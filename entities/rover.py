import pygame
import math
from core.camera import Camera

# Модифікатори швидкості по висоті (нижче = швидше)
HEIGHT_SPEED_MOD = {
    0: 1.30,   # DEEP_LOWLANDS
    1: 1.15,   # LOWLANDS
    2: 1.00,   # PLAINS
    3: 0.95,   # HIGH_PLAINS
    4: 0.82,   # HIGHLANDS
    5: 0.88,   # PLATEAUS
    6: 0.00,   # MOUNTAINS — непрохідно
}


class Rover:
    MAX_SPEED    = 320.0    # пікселів/с
    ACCELERATION = 900.0    # пікселів/с²
    FRICTION     = 0.82     # множник за кадр
    SIZE         = 24       # радіус для колізій

    def __init__(self, x: float, y: float):
        self.x   = x
        self.y   = y
        self.vx  = 0.0
        self.vy  = 0.0
        self.angle = 0.0
        self.speed_mod_external = 1.0   # від кризи (буря)      # градуси для повороту спрайту
        self._texture: pygame.Surface | None = None
        self._tex_orig: pygame.Surface | None = None  # оригінал для повороту

    def load_texture(self, path: str = "assets/textures/rover.png"):
        try:
            img = pygame.image.load(path).convert_alpha()
            self._tex_orig = pygame.transform.scale(img, (self.SIZE * 2, self.SIZE * 2))
            self._texture  = self._tex_orig
        except Exception as e:
            print(f"[Rover] texture load failed: {e}")

    # ---------------------------------------------------------------- update

    def update(self, dt: float, keys, world):
        # Вектор введення
        dx = dy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        # Нормалізація діагоналі
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
            # Кут повороту спрайту (0° = вгору)
            self.angle = math.degrees(math.atan2(dx, -dy))

        # Модифікатор швидкості з тайлу
        tile = world.get_tile_at_world(self.x, self.y)
        if tile:
            speed_mod = HEIGHT_SPEED_MOD.get(int(tile.height), 1.0)
        else:
            speed_mod = 1.0

        effective_max = self.MAX_SPEED * speed_mod * self.speed_mod_external

        # Прискорення
        self.vx += dx * self.ACCELERATION * dt
        self.vy += dy * self.ACCELERATION * dt

        # Обмеження швидкості
        speed = math.hypot(self.vx, self.vy)
        if speed > effective_max and speed > 0:
            self.vx = self.vx / speed * effective_max
            self.vy = self.vy / speed * effective_max

        # Тертя (менше тертя = чіткіший рух)
        self.vx *= self.FRICTION
        self.vy *= self.FRICTION

        # Спроба руху
        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt

        # Колізія по осях окремо — не застрягаємо в кутах
        if self._can_move_to(new_x, self.y, world):
            self.x = new_x
        else:
            self.vx = 0

        if self._can_move_to(self.x, new_y, world):
            self.y = new_y
        else:
            self.vy = 0

        # Обмеження по краях карти
        hw = world.width  * world.TILE_SIZE
        hh = world.height * world.TILE_SIZE
        self.x = max(self.SIZE, min(self.x, hw - self.SIZE))
        self.y = max(self.SIZE, min(self.y, hh - self.SIZE))

    def _can_move_to(self, x: float, y: float, world) -> bool:
        tile = world.get_tile_at_world(x, y)
        return tile is not None and tile.passable

    # ---------------------------------------------------------------- render

    def render(self, screen: pygame.Surface, camera: Camera):
        sx, sy = camera.apply(self.x, self.y)

        if self._tex_orig is not None:
            # Повертаємо оригінал (щоб не деградував від повторних поворотів)
            rotated = pygame.transform.rotate(self._tex_orig, -self.angle)
            rect    = rotated.get_rect(center=(sx, sy))
            screen.blit(rotated, rect)
        else:
            # Fallback — коло
            pygame.draw.circle(screen, (220, 180, 60), (sx, sy), self.SIZE)
            pygame.draw.circle(screen, (255, 220, 80), (sx, sy), self.SIZE - 4)
            rad   = math.radians(self.angle - 90)
            tip_x = sx + math.cos(rad) * (self.SIZE + 6)
            tip_y = sy + math.sin(rad) * (self.SIZE + 6)
            pygame.draw.line(screen, (255, 80, 30),
                             (sx, sy), (int(tip_x), int(tip_y)), 3)
