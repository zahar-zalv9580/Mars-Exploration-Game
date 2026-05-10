"""
HUD — верхня панель гри.
Показує: день, фазу, таймер дня, попередження, лог подій.
"""
from __future__ import annotations
import pygame
import math
from ui import fonts
from systems.day_cycle import DayCycle

# Кольори фаз
PHASE_COLORS = {
    "EARLY":    (100, 180, 100),
    "EARLY+":   (140, 200, 80),
    "MID":      (220, 180, 50),
    "LATE":     (220, 130, 40),
    "CRITICAL": (220, 60,  40),
    "FINAL":    (180, 30,  30),
}

LOG_MAX     = 5      # скільки рядків логу видно
LOG_FADE    = 6.0    # секунд до зникнення повідомлення


class HUD:
    BG          = (8, 4, 2, 200)
    BORDER      = (120, 55, 20)
    TEXT        = (210, 190, 160)
    DIM         = (100, 80,  60)
    ALERT       = (220, 60,  40)
    GOLD        = (255, 200, 50)

    def __init__(self):
        self._log: list[tuple[str, float]] = []   # (msg, age)
        self._blink = 0.0

    def push_message(self, msg: str):
        self._log.insert(0, (msg, 0.0))
        if len(self._log) > LOG_MAX:
            self._log.pop()

    def update(self, dt: float):
        self._blink += dt
        self._log = [(m, age + dt) for m, age in self._log]
        self._log = [(m, age) for m, age in self._log if age < LOG_FADE]

    def render(self, screen: pygame.Surface, day: DayCycle, crisis=None):
        sw, _ = screen.get_size()
        self._render_top_bar(screen, day, sw, crisis)
        self._render_log(screen, day)

    # ---------------------------------------------------------------- top bar

    def _render_top_bar(self, screen: pygame.Surface, day: DayCycle, sw: int, crisis=None):
        BAR_H = 44
        bg = pygame.Surface((sw, BAR_H), pygame.SRCALPHA)
        bg.fill(self.BG)
        screen.blit(bg, (0, 0))
        pygame.draw.line(screen, self.BORDER, (0, BAR_H), (sw, BAR_H), 1)

        phase_color = PHASE_COLORS.get(day.phase, self.TEXT)
        cx = sw // 2

        # ── День (центр) ──────────────────────────────────────────────────
        day_str = f"DAY {day.day}"
        day_surf = fonts.get(20, bold=True).render(day_str, True, self.GOLD)
        screen.blit(day_surf, (cx - day_surf.get_width() // 2, 6))

        # ── Прогрес дня (під написом) ─────────────────────────────────────
        bar_w = 120
        bar_x = cx - bar_w // 2
        bar_y = 30
        pygame.draw.rect(screen, (30, 15, 5),
                         pygame.Rect(bar_x, bar_y, bar_w, 6))
        pygame.draw.rect(screen, self.GOLD,
                         pygame.Rect(bar_x, bar_y,
                                     int(bar_w * day.progress), 6))
        pygame.draw.rect(screen, self.BORDER,
                         pygame.Rect(bar_x, bar_y, bar_w, 6), 1)

        # Таймер до наступного дня
        timer = fonts.get(9).render(day.time_in_day_str, True, self.DIM)
        screen.blit(timer, (cx - timer.get_width() // 2, 38))

        # ── Фаза (ліво від дня) ───────────────────────────────────────────
        phase_surf = fonts.get(12, bold=True).render(
            day.phase, True, phase_color
        )
        screen.blit(phase_surf, (cx - 160 - phase_surf.get_width(), 8))

        label_surf = fonts.get(9).render(day.phase_label, True, self.DIM)
        screen.blit(label_surf, (cx - 160 - label_surf.get_width(), 24))

        # ── Залишилось днів (право від дня) ──────────────────────────────
        left_str = f"{30 - day.day} ДНІВ ЗАЛИШИЛОСЬ" if day.day < 30 else "ОСТАННІЙ ДЕНЬ"
        left_color = self.ALERT if day.day >= 25 else self.TEXT
        left_surf = fonts.get(12, bold=True).render(left_str, True, left_color)
        screen.blit(left_surf, (cx + 170, 8))

        # Загальний прогрес гри
        total_bar_w = 80
        total_prog  = (day.day - 1) / 29
        pygame.draw.rect(screen, (30, 15, 5),
                         pygame.Rect(cx + 170, 26, total_bar_w, 5))
        pygame.draw.rect(screen, left_color,
                         pygame.Rect(cx + 170, 26,
                                     int(total_bar_w * total_prog), 5))
        pygame.draw.rect(screen, self.BORDER,
                         pygame.Rect(cx + 170, 26, total_bar_w, 5), 1)

        # ── Іконка погоди (ліво вгорі) ──────────────────────────────────────
        if crisis is not None:
            icon = crisis.weather_icon
            icon_surf = fonts.get(20).render(icon, True, (220, 180, 80))
            screen.blit(icon_surf, (10, 8))

        # ── CRITICAL alert (день 25+) ─────────────────────────────────────
        if day.is_critical:
            blink = math.sin(self._blink * 4) > 0
            if blink:
                alert = fonts.get(11, bold=True).render(
                    "// ПКО ПРИБЛИЖАЄТЬСЯ //", True, self.ALERT
                )
                screen.blit(alert, (cx + 170, 34))

    # ---------------------------------------------------------------- log

    def _render_log(self, screen: pygame.Surface, day: DayCycle):
        if not self._log:
            return
        sw, sh = screen.get_size()
        x  = 10
        y  = 52   # під top bar

        for msg, age in self._log:
            alpha = max(0, int(255 * (1.0 - age / LOG_FADE)))
            color = (*self._msg_color(msg), alpha) if alpha > 0 else None
            if not color:
                continue
            surf = fonts.get(10).render(msg, True, color[:3])
            surf.set_alpha(alpha)
            screen.blit(surf, (x, y))
            y += 16

    def _msg_color(self, msg: str) -> tuple[int,int,int]:
        m = msg.upper()
        if "ALERT" in m or "CRITICAL" in m or "PCO" in m:
            return (220, 60, 40)
        if "WARNING" in m or "ERROR" in m:
            return (220, 180, 40)
        if "COLONIST" in m:
            return (180, 120, 80)
        return (160, 200, 160)
