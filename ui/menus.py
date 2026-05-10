"""
Всі екрани гри:
  MainMenu, PauseMenu, GameOverScreen, EndingScreen
Кожен має:
  .handle_event(event) -> str | None   (назва дії)
  .update(dt)
  .render(screen)
"""
from __future__ import annotations
import pygame
import random
import math
from ui import fonts


# ── Загальні кольори ────────────────────────────────────────────────────────
C_BG        = (5,  3,  2)
C_RED       = (200, 50,  30)
C_ORANGE    = (220, 130, 40)
C_GOLD      = (255, 200, 50)
C_TEXT      = (210, 190, 160)
C_DIM       = (100, 80,  60)
C_GLITCH_R  = (220, 30,  30)
C_GLITCH_B  = (30,  80, 220)


# ── Частинки для головного меню ─────────────────────────────────────────────
class _Particle:
    def __init__(self, sw: int, sh: int):
        self.reset(sw, sh)

    def reset(self, sw: int, sh: int):
        self.x  = random.uniform(0, sw)
        self.y  = random.uniform(0, sh)
        self.vx = random.uniform(-12, 12)
        self.vy = random.uniform(-20, -4)
        self.r  = random.uniform(1, 3)
        self.alpha = random.randint(60, 180)
        self.life  = random.uniform(2.0, 6.0)
        self.age   = 0.0
        self._sw, self._sh = sw, sh

    def update(self, dt: float):
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.age += dt
        if self.age >= self.life or self.y < -10:
            self.reset(self._sw, self._sh)
            self.y = self._sh + 5

    def render(self, surf: pygame.Surface):
        a = int(self.alpha * max(0, 1 - self.age / self.life))
        if a <= 0:
            return
        s = pygame.Surface((int(self.r * 2 + 1),) * 2, pygame.SRCALPHA)
        pygame.draw.circle(s, (*C_ORANGE, a), (int(self.r), int(self.r)), int(self.r))
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))


# ── Кнопка ──────────────────────────────────────────────────────────────────
class _Button:
    W, H = 280, 40
    C_IDLE   = (30, 15, 8)
    C_HOVER  = (60, 30, 10)
    C_BORDER = (140, 60, 20)
    C_HOVER_BORDER = (220, 130, 40)

    def __init__(self, label: str, action: str, cx: int, cy: int):
        self.label  = label
        self.action = action
        self.rect   = pygame.Rect(cx - self.W // 2, cy - self.H // 2, self.W, self.H)
        self._hover = False

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.action
        return None

    def render(self, screen: pygame.Surface):
        bg  = self.C_HOVER  if self._hover else self.C_IDLE
        brd = self.C_HOVER_BORDER if self._hover else self.C_BORDER
        pygame.draw.rect(screen, bg,  self.rect)
        pygame.draw.rect(screen, brd, self.rect, 1)
        font = fonts.get(14)
        txt  = font.render(self.label, True,
                           C_GOLD if self._hover else C_TEXT)
        screen.blit(txt, txt.get_rect(center=self.rect.center))


# ── Glitch-ефект ─────────────────────────────────────────────────────────────
class _GlitchFx:
    def __init__(self):
        self._timer    = 0.0
        self._interval = random.uniform(2.0, 5.0)
        self._active   = False
        self._duration = 0.0
        self._lines: list[tuple[int,int,int]] = []   # y, h, shift

    def update(self, dt: float):
        self._timer += dt
        if not self._active and self._timer >= self._interval:
            self._active   = True
            self._duration = random.uniform(0.08, 0.22)
            self._timer    = 0.0
            self._interval = random.uniform(1.5, 5.0)
            self._lines    = [
                (random.randint(0, 600), random.randint(2, 12),
                 random.randint(-30, 30))
                for _ in range(random.randint(3, 8))
            ]
        if self._active:
            self._duration -= dt
            if self._duration <= 0:
                self._active = False

    def render(self, screen: pygame.Surface):
        if not self._active:
            return
        sw, sh = screen.get_size()
        for y, h, shift in self._lines:
            if y + h > sh:
                continue
            strip = screen.subsurface(pygame.Rect(0, y, sw, h)).copy()
            # Червоний і синій зсув
            r_surf = pygame.Surface((sw, h), pygame.SRCALPHA)
            r_surf.blit(strip, (0, 0))
            r_surf.fill((255, 0, 0, 60), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(r_surf, (shift, y))
            screen.blit(strip,  (-shift // 2, y))


# ═══════════════════════════════════════════════════════════════════════════
# ГОЛОВНЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════════════════
class MainMenu:
    TITLE    = "MARS: R-ARK PROTOCOL"
    SUBTITLE = "// RED ARKORP COLONIZATION UNIT //"

    def __init__(self, screen: pygame.Surface, has_save: bool = False):
        sw, sh = screen.get_size()
        self._sw, self._sh = sw, sh
        self._glitch  = _GlitchFx()
        self._particles = [_Particle(sw, sh) for _ in range(80)]
        self._time    = 0.0

        cy_start = sh // 2 + 20
        self._buttons: list[_Button] = []
        if has_save:
            self._buttons.append(_Button("CONTINUE",     "continue",  sw // 2, cy_start))
            cy_start += 52
        self._buttons.append(_Button("NEW GAME",     "new_game",  sw // 2, cy_start))
        cy_start += 52
        self._buttons.append(_Button("EXIT",         "exit",      sw // 2, cy_start))

    def handle_event(self, event: pygame.event.Event) -> str | None:
        for btn in self._buttons:
            result = btn.handle_event(event)
            if result:
                return result
        return None

    def update(self, dt: float):
        self._time += dt
        self._glitch.update(dt)
        for p in self._particles:
            p.update(dt)

    def render(self, screen: pygame.Surface):
        screen.fill(C_BG)

        # Частинки
        for p in self._particles:
            p.render(screen)

        # Горизонтальні лінії (атмосфера)
        for i in range(0, self._sh, 60):
            alpha = int(20 + 10 * math.sin(self._time * 0.5 + i * 0.05))
            s = pygame.Surface((self._sw, 1), pygame.SRCALPHA)
            s.fill((180, 80, 30, alpha))
            screen.blit(s, (0, i))

        # Заголовок
        title_font = fonts.get(28)
        title = title_font.render(self.TITLE, True, C_GOLD)
        tx = self._sw // 2 - title.get_width() // 2
        ty = self._sh // 2 - 160
        # Glitch-тінь
        shadow_r = title_font.render(self.TITLE, True, (*C_GLITCH_R, 120))
        shadow_b = title_font.render(self.TITLE, True, (*C_GLITCH_B, 120))
        screen.blit(shadow_r, (tx + 3, ty))
        screen.blit(shadow_b, (tx - 3, ty))
        screen.blit(title, (tx, ty))

        # Підзаголовок
        sub_font = fonts.get(10)
        sub = sub_font.render(self.SUBTITLE, True, C_DIM)
        screen.blit(sub, (self._sw // 2 - sub.get_width() // 2, ty + 44))

        # Роздільник
        pygame.draw.line(screen, C_RED,
                         (self._sw // 2 - 140, ty + 64),
                         (self._sw // 2 + 140, ty + 64), 1)

        for btn in self._buttons:
            btn.render(screen)

        # Версія
        ver = fonts.get(9).render("v0.1-hackathon", True, C_DIM)
        screen.blit(ver, (10, self._sh - 20))

        self._glitch.render(screen)


# ═══════════════════════════════════════════════════════════════════════════
# ПАУЗА
# ═══════════════════════════════════════════════════════════════════════════
class PauseMenu:
    def __init__(self, screen: pygame.Surface):
        sw, sh = screen.get_size()
        cy = sh // 2 + 10
        self._buttons = [
            _Button("RESUME",    "resume",    sw // 2, cy),
            _Button("SAVE GAME", "save",      sw // 2, cy + 52),
            _Button("MAIN MENU", "main_menu", sw // 2, cy + 104),
            _Button("EXIT",      "exit",      sw // 2, cy + 156),
        ]

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "resume"
        for btn in self._buttons:
            r = btn.handle_event(event)
            if r:
                return r
        return None

    def update(self, dt: float):
        pass

    def render(self, screen: pygame.Surface):
        # Напівпрозорий overlay поверх гри
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))

        sw, sh = screen.get_size()

        # Панель
        pw, ph = 340, 330
        px, py = sw // 2 - pw // 2, sh // 2 - ph // 2 - 20
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((10, 5, 2, 220))
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, C_RED, pygame.Rect(px, py, pw, ph), 1)

        title = fonts.get(22).render("// PAUSED //", True, C_ORANGE)
        screen.blit(title, (sw // 2 - title.get_width() // 2, py + 20))
        pygame.draw.line(screen, C_RED,
                         (px + 20, py + 54), (px + pw - 20, py + 54), 1)

        for btn in self._buttons:
            btn.render(screen)


# ═══════════════════════════════════════════════════════════════════════════
# GAME OVER
# ═══════════════════════════════════════════════════════════════════════════
class GameOverScreen:
    REASONS = {
        "energy": "ENERGY COLLAPSE",
        "food":   "FOOD SHORTAGE",
        "hub":    "HUB DESTROYED",
    }

    def __init__(self, screen: pygame.Surface, reason: str = "hub"):
        sw, sh = screen.get_size()
        self._reason  = self.REASONS.get(reason, "SYSTEM FAILURE")
        self._glitch  = _GlitchFx()
        self._time    = 0.0
        cy = sh // 2 + 60
        self._buttons = [
            _Button("PLAY AGAIN", "new_game",  sw // 2, cy),
            _Button("MAIN MENU",  "main_menu", sw // 2, cy + 52),
        ]

    def handle_event(self, event: pygame.event.Event) -> str | None:
        for btn in self._buttons:
            r = btn.handle_event(event)
            if r:
                return r
        return None

    def update(self, dt: float):
        self._time += dt
        self._glitch.update(dt)

    def render(self, screen: pygame.Surface):
        # Темно-червоне затемнення
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((40, 0, 0, 200))
        screen.blit(ov, (0, 0))

        sw, sh = screen.get_size()

        flicker = abs(math.sin(self._time * 8)) > 0.3
        color = C_GLITCH_R if flicker else C_RED

        title = fonts.get(32).render("CORRECTION EXECUTED", True, color)
        screen.blit(title, (sw // 2 - title.get_width() // 2, sh // 2 - 140))

        sub = fonts.get(14).render(self._reason, True, C_ORANGE)
        screen.blit(sub, (sw // 2 - sub.get_width() // 2, sh // 2 - 80))

        msg = fonts.get(10).render(
            "// PLANETARY CORRECTION OBJECT HAS REACHED MARS //",
            True, C_DIM
        )
        screen.blit(msg, (sw // 2 - msg.get_width() // 2, sh // 2 - 40))

        for btn in self._buttons:
            btn.render(screen)

        self._glitch.render(screen)


# ═══════════════════════════════════════════════════════════════════════════
# ENDING SCREEN
# ═══════════════════════════════════════════════════════════════════════════
ENDING_DATA = {
    "good": {
        "title":   "SIGNAL HIDDEN",
        "color":   (80, 220, 120),
        "lines": [
            "The Signal Jammer activated.",
            "The colony vanished from Observer sensors.",
            "Mars goes silent.",
            "Humanity survives.",
        ],
    },
    "bad": {
        "title":   "CORRECTION EXECUTED",
        "color":   C_GLITCH_R,
        "lines": [
            "The Planetary Correction Object entered orbit.",
            "The signal was never hidden.",
            "Mars, like Earth, falls silent.",
        ],
    },
    "secret": {
        "title":   "R-ARK OVERRIDE",
        "color":   C_GOLD,
        "lines": [
            "All lore logs recovered.",
            "The R-ARK-NET corruption identified.",
            "Signal rerouted. Observers... confused.",
            "The colony broadcasts a new frequency.",
            "Unknown response incoming.",
        ],
    },
}


class EndingScreen:
    def __init__(self, screen: pygame.Surface, ending: str = "good",
                 discovered_logs: list[str] | None = None):
        sw, sh = screen.get_size()
        self._data    = ENDING_DATA.get(ending, ENDING_DATA["good"])
        self._glitch  = _GlitchFx()
        self._time    = 0.0
        self._particles = [_Particle(sw, sh) for _ in range(40)]
        self._archive_ids = discovered_logs or []
        self._archive_index = 0
        self._mode = "main"

        cy = sh // 2 + 160
        self._buttons = [
            _Button("PLAY AGAIN", "new_game",  sw // 2, cy),
            _Button("MAIN MENU",  "main_menu", sw // 2, cy + 52),
        ]
        if self._archive_ids:
            self._buttons.append(
                _Button("VIEW ARCHIVE", "archive", sw // 2, cy + 104)
            )

        self._archive_buttons = [
            _Button("BACK", "back", sw // 2, sh - 80)
        ]

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self._mode == "archive":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self._archive_index = max(0, self._archive_index - 1)
                    return None
                if event.key == pygame.K_RIGHT:
                    self._archive_index = min(
                        len(self._archive_ids) - 1, self._archive_index + 1
                    )
                    return None
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self._mode = "main"
                    return None
            for btn in self._archive_buttons:
                r = btn.handle_event(event)
                if r == "back":
                    self._mode = "main"
                    return None
            return None

        for btn in self._buttons:
            r = btn.handle_event(event)
            if r == "archive":
                self._mode = "archive"
                self._archive_index = 0
                return None
            if r:
                return r
        return None

    def update(self, dt: float):
        self._time += dt
        self._glitch.update(dt)
        for p in self._particles:
            p.update(dt)

    def render(self, screen: pygame.Surface):
        screen.fill(C_BG)
        for p in self._particles:
            p.render(screen)

        sw, sh = screen.get_size()
        color  = self._data["color"]

        if self._mode == "archive":
            self._render_archive(screen, sw, sh)
            return

        # Заголовок
        title = fonts.get(26).render(self._data["title"], True, color)
        ty    = sh // 2 - 180
        # Glitch-тінь
        sh_r  = fonts.get(26).render(self._data["title"], True, (*C_GLITCH_R, 80))
        screen.blit(sh_r, (sw // 2 - title.get_width() // 2 + 4, ty + 2))
        screen.blit(title, (sw // 2 - title.get_width() // 2, ty))

        pygame.draw.line(screen, color,
                         (sw // 2 - 160, ty + 42),
                         (sw // 2 + 160, ty + 42), 1)

        # Текст
        line_font = fonts.get(11)
        for i, line in enumerate(self._data["lines"]):
            # Рядки з'являються поступово
            visible = self._time > i * 1.2
            if not visible:
                continue
            alpha = min(255, int((self._time - i * 1.2) * 200))
            surf  = line_font.render(line, True, C_TEXT)
            surf.set_alpha(alpha)
            screen.blit(surf, (sw // 2 - surf.get_width() // 2, ty + 60 + i * 26))

        for btn in self._buttons:
            btn.render(screen)

        self._glitch.render(screen)

    def _render_archive(self, screen: pygame.Surface, sw: int, sh: int):
        from systems.lore import LOG_BY_ID

        title = fonts.get(24, bold=True).render("ARCHIVE VIEWER", True, C_GOLD)
        screen.blit(title, (sw // 2 - title.get_width() // 2, 48))

        if not self._archive_ids:
            hint = fonts.get(14).render("No logs discovered.", True, C_TEXT)
            screen.blit(hint, (sw // 2 - hint.get_width() // 2, sh // 2))
        else:
            log_id = self._archive_ids[self._archive_index]
            log = LOG_BY_ID.get(log_id)
            if log:
                header = fonts.get(16, bold=True).render(log.title, True, C_TEXT)
                screen.blit(header, (sw // 2 - header.get_width() // 2, 110))
                meta = fonts.get(11).render(
                    f"{log.date} — {log.category.name}", True, C_DIM
                )
                screen.blit(meta, (sw // 2 - meta.get_width() // 2, 140))
                for i, line in enumerate(log.text):
                    text_surf = fonts.get(12).render(line, True, C_TEXT)
                    screen.blit(text_surf, (120, 180 + i * 24))
            nav = fonts.get(11).render(
                f"< LEFT   [{self._archive_index + 1}/{len(self._archive_ids)}]   RIGHT >",
                True, C_DIM
            )
            screen.blit(nav, (sw // 2 - nav.get_width() // 2, sh - 120))

        for btn in self._archive_buttons:
            btn.render(screen)
