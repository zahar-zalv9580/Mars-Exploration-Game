from asyncio import events
import pygame
import random
import math
from systems import crisis
from systems.crisis import Modifiers, CrisisManager, EventType


class DustParticle:
    def __init__(self, sw: int, sh: int):
        self.sw, self.sh = sw, sh
        self.reset()

    def reset(self):
        self.x   = random.uniform(-100, self.sw + 100)
        self.y   = random.uniform(-20,  self.sh + 20)
        self.vx  = random.uniform(80, 200)
        self.vy  = random.uniform(-10, 20)
        self.r   = random.uniform(1, 4)
        self.alpha = random.randint(40, 140)

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x > self.sw + 120:
            self.reset()
            self.x = -100

    def render(self, surf: pygame.Surface, intensity: float):
        a = int(self.alpha * intensity)
        if a <= 0:
            return
        s = pygame.Surface((int(self.r*2+1),)*2, pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 140, 60, a),
                           (int(self.r), int(self.r)), int(self.r))
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))


class WeatherFX:
    PARTICLE_COUNT = 120

    def __init__(self, screen: pygame.Surface):
        sw, sh = screen.get_size()
        self._sw, self._sh = sw, sh
        self._dust = [DustParticle(sw, sh) for _ in range(self.PARTICLE_COUNT)]
        self._glitch_timer = 0.0
        self._glitch_active = False
        self._glitch_lines: list[tuple] = []
        self._time = 0.0

    def update(self, dt: float, crisis: CrisisManager):
        self._time += dt

        # Dust particles — тільки якщо є буря або orbital shadow
        has_dust = (crisis.has_dust_storm or
                    any(ev.type == EventType.ORBITAL_SHADOW
                        for ev in crisis.active_events))
        if has_dust:
            for p in self._dust:
                p.update(dt)

        # Glitch
        self._glitch_timer -= dt
        if self._glitch_timer <= 0:
            self._glitch_timer = random.uniform(0.5, 3.0)
            self._glitch_active = random.random() < 0.4
            if self._glitch_active:
                self._glitch_lines = [
                    (random.randint(0, self._sh),
                     random.randint(2, 10),
                     random.randint(-25, 25))
                    for _ in range(random.randint(2, 6))
                ]

    def render(self, screen: pygame.Surface,
               mods: Modifiers, crisis: CrisisManager):
        # Screen overlay
        if mods.screen_overlay and mods.overlay_alpha > 0:
            ov = pygame.Surface((self._sw, self._sh), pygame.SRCALPHA)
            ov.fill((*mods.screen_overlay, int(mods.overlay_alpha)))
            screen.blit(ov, (0, 0))

        # Dust particles
        has_dust = crisis.has_dust_storm
        if has_dust:
            dust_intensity = max(
                ev.severity * math.sin(math.pi * ev.progress)
                for ev in crisis.active_events
                if ev.type == EventType.DUST_STORM
            ) if crisis.active_events else 0
            for p in self._dust:
                p.render(screen, dust_intensity)

        # Glitch lines
        if mods.signal_glitch and self._glitch_active:
            for y, h, shift in self._glitch_lines:
                if y + h > self._sh or y < 0:
                    continue
                try:
                    strip = screen.subsurface(
                        pygame.Rect(0, y, self._sw, h)
                    ).copy()
                    r_ov = pygame.Surface((self._sw, h), pygame.SRCALPHA)
                    r_ov.blit(strip, (0, 0))
                    r_ov.fill((255, 0, 0, 50),
                               special_flags=pygame.BLEND_RGBA_MULT)
                    screen.blit(r_ov, (shift, y))
                    screen.blit(strip, (-shift // 2, y))
                except Exception:
                    pass

        # Weather widget — правий верхній кут (під HUD)
        self._render_weather_widget(screen, crisis)

    def _render_weather_widget(self, screen: pygame.Surface, crisis: CrisisManager):
        events = crisis.active_events
        if not events:
            return

        from ui import fonts
        # Правий нижній кут, щоб не заважати панелям ресурсів і популяції
        x = self._sw - 10
        y = self._sh - 140

        for ev in events[:3]:
            # Додаємо іконку до назви
            display_text = f"{ev.icon} {ev.label}"
            # Вимірюємо ширину тексту
            label_surf = fonts.get(10, bold=True).render(display_text, True, ev.color)
            w = max(140, label_surf.get_width() + 24)  # динамічна ширина
            h = 28

            # Фон
            bg = pygame.Surface((w, h), pygame.SRCALPHA)
            bg.fill((10, 5, 2, 220))   # трохи щільніший фон
            screen.blit(bg, (x - w, y))
            pygame.draw.rect(screen, ev.color,
                             pygame.Rect(x - w, y, w, h), 1)

            # Текст з іконкою
            label = fonts.get(10, bold=True).render(
                display_text, True, ev.color
            )
            screen.blit(label, (x - w + 6, y + 6))

            # Прогрес-бар тривалості
            bar_w = w - 12
            pygame.draw.rect(screen, (30, 15, 5),
                             pygame.Rect(x - w + 6, y + h - 5, bar_w, 3))
            fill = int(bar_w * (1.0 - ev.progress))
            if fill > 0:
                pygame.draw.rect(screen, ev.color,
                                 pygame.Rect(x - w + 6, y + h - 5, fill, 3))
            y += h + 4
