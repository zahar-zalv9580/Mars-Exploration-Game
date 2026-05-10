import pygame
from ui import fonts
from systems.resources import ResourceSystem, Resource

RESOURCE_STYLE: dict[Resource, dict] = {
    Resource.ENERGY:  {"label": "Енергія",  "color": (255, 220, 50)},
    Resource.IRON:    {"label": "Залізо",    "color": (180, 130, 90)},
    Resource.WATER:   {"label": "Вода",   "color": (80,  160, 220)},
    Resource.SILICON: {"label": "Силікон", "color": (140, 200, 140)},
    Resource.FUEL:    {"label": "Паливо",    "color": (220, 120, 50)},
    Resource.URANIUM: {"label": "Уран", "color": (130, 220, 100)},
    Resource.FOOD:    {"label": "Їжа",    "color": (180, 220, 80)},
}

PANEL_WIDTH  = 220
ROW_HEIGHT   = 40
PADDING      = 10
MARGIN_TOP   = 56
BAR_H        = 7
WARN_RATIO   = 0.20
CRIT_RATIO   = 0.08


class ResourcePanel:
    BG_COLOR     = (12, 6, 3, 200)
    BORDER_COLOR = (120, 55, 20)
    BAR_BG       = (35, 18, 8)
    TEXT_COLOR   = (210, 190, 160)
    WARN_COLOR   = (220, 180, 30)
    CRIT_COLOR   = (220, 60,  40)

    def render(self, screen: pygame.Surface, res: ResourceSystem):
        sw, _ = screen.get_size()
        panel_h = PADDING + 14 + len(Resource) * ROW_HEIGHT + PADDING
        x = sw - PANEL_WIDTH - 8
        y = MARGIN_TOP

        bg = pygame.Surface((PANEL_WIDTH, panel_h), pygame.SRCALPHA)
        bg.fill(self.BG_COLOR)
        screen.blit(bg, (x, y))
        pygame.draw.rect(screen, self.BORDER_COLOR,
                         pygame.Rect(x, y, PANEL_WIDTH, panel_h), 1)

        title = fonts.get(11, bold=True).render("Ресурси", True, (180, 80, 30))
        screen.blit(title, (x + PADDING, y + 4))

        for i, r in enumerate(Resource):
            self._render_row(screen, res, r, x,
                             y + PADDING + 14 + i * ROW_HEIGHT)

    def _render_row(self, screen, res, r, px, py):
        style   = RESOURCE_STYLE[r]
        color   = style["color"]
        ratio   = res.ratio(r)
        amount  = res.amount(r)
        cap     = res.capacity(r)
        delta   = res.delta(r)

        # Колір залежно від рівня
        if ratio < CRIT_RATIO:
            label_color = self.CRIT_COLOR
        elif ratio < WARN_RATIO:
            label_color = self.WARN_COLOR
        else:
            label_color = color

        # Назва
        lbl = fonts.get(11, bold=True).render(style["label"], True, label_color)
        screen.blit(lbl, (px + PADDING, py + 2))

        # Значення + дельта
        delta_str = ""
        if abs(delta) > 0.01:
            sign = "+" if delta > 0 else ""
            delta_color = (100, 220, 100) if delta > 0 else (220, 100, 100)
            d_surf = fonts.get(10).render(
                f"{sign}{delta:.1f}/s", True, delta_color
            )
            screen.blit(d_surf, (px + PANEL_WIDTH - d_surf.get_width() - PADDING, py + 2))

        val = fonts.get(10).render(
            f"{int(amount)}/{int(cap)}", True, self.TEXT_COLOR
        )
        # Якщо є дельта - зсуваємо вліво
        val_x = px + PANEL_WIDTH - val.get_width() - PADDING
        if abs(delta) > 0.01:
            val_x -= (d_surf.get_width() + 4)
        screen.blit(val, (val_x, py + 2))

        # Бар
        bar_x = px + PADDING
        bar_y = py + ROW_HEIGHT - BAR_H - 4
        bar_w = PANEL_WIDTH - PADDING * 2
        pygame.draw.rect(screen, self.BAR_BG,
                         pygame.Rect(bar_x, bar_y, bar_w, BAR_H))
        fill_w = max(0, int(bar_w * ratio))
        if fill_w > 0:
            bar_color = (self.CRIT_COLOR if ratio < CRIT_RATIO
                         else self.WARN_COLOR if ratio < WARN_RATIO
                         else color)
            pygame.draw.rect(screen, bar_color,
                             pygame.Rect(bar_x, bar_y, fill_w, BAR_H))
        pygame.draw.rect(screen, self.BORDER_COLOR,
                         pygame.Rect(bar_x, bar_y, bar_w, BAR_H), 1)
