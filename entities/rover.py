import pygame
import math
from core.camera import Camera


class Rover:
    ACCELERATION = 400.0
    MAX_SPEED    = 220.0
    FRICTION     = 0.88
    SIZE         = 20

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0

    def update(self, dt: float, keys, world):
        dx = dy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
            self.angle = math.degrees(math.atan2(dy, dx)) + 90

        tile = world.get_tile_at_world(self.x, self.y)
        speed_mod = tile.speed_modifier if tile else 1.0

        self.vx += dx * self.ACCELERATION * speed_mod * dt
        self.vy += dy * self.ACCELERATION * speed_mod * dt

        speed = math.hypot(self.vx, self.vy)
        max_s = self.MAX_SPEED * speed_mod
        if speed > max_s and speed > 0:
            self.vx = self.vx / speed * max_s
            self.vy = self.vy / speed * max_s

        self.vx *= self.FRICTION
        self.vy *= self.FRICTION

        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt

        if self._can_move_to(new_x, new_y, world):
            self.x = new_x
            self.y = new_y
        else:
            self.vx = 0
            self.vy = 0

        map_w = world.width * world.TILE_SIZE
        map_h = world.height * world.TILE_SIZE
        self.x = max(self.SIZE, min(self.x, map_w - self.SIZE))
        self.y = max(self.SIZE, min(self.y, map_h - self.SIZE))

    def _can_move_to(self, x: float, y: float, world) -> bool:
        tile = world.get_tile_at_world(x, y)
        return tile is not None and tile.passable

    def render(self, screen: pygame.Surface, camera: Camera):
        sx, sy = camera.apply(self.x, self.y)
        pygame.draw.circle(screen, (220, 180, 60), (sx, sy), self.SIZE)
        pygame.draw.circle(screen, (255, 220, 80), (sx, sy), self.SIZE - 4)
        rad = math.radians(self.angle - 90)
        tip_x = sx + math.cos(rad) * (self.SIZE + 6)
        tip_y = sy + math.sin(rad) * (self.SIZE + 6)
        pygame.draw.line(screen, (255, 80, 30), (sx, sy), (int(tip_x), int(tip_y)), 3)
