import pygame
from world.tile import Tile
from ui.resource_panel import ResourcePanel
from ui.inventory import Inventory
from entities.building import BuildingType, BUILDING_DEFS
from systems.resources import ResourceSystem, Resource
from ui.population_panel import PopulationPanel
from ui.hud import HUD
from systems.population import PopulationManager
from systems.day_cycle import DayCycle

# Іконки ресурсів клітинки
TILE_RES_COLORS: dict[str, tuple[int,int,int]] = {
    "energy":  (255, 220, 50),
    "iron":    (180, 130, 90),
    "water":   (80,  160, 220),
    "silicon": (140, 200, 140),
    "fuel":    (220, 120, 50),
    "uranium": (130, 220, 100),
}


class UI:
    def __init__(self, screen: pygame.Surface):
        self.screen         = screen
        self.tile_info        = TileInfoPanel()
        self.resource_panel   = ResourcePanel()
        self.population_panel = PopulationPanel()
        self.inventory        = Inventory()
        self.hud              = HUD()

    def load_icons(self, icons):
        self.inventory.load_icons(icons)

    def handle_key(self, key: int, bp_inv=None):
        return self.inventory.handle_key(key, bp_inv) if bp_inv else None

    def handle_click(self, mx: int, my: int, world, camera, bp_inv=None) -> str:
        sw, sh = self.screen.get_size()
        bt = self.inventory.handle_click(mx, my, sw, sh, bp_inv or __import__('systems.factory', fromlist=['BlueprintInventory']).BlueprintInventory())
        if bt is not None:
            return 'inventory'
        tx, ty = world.screen_to_tile(mx, my, camera)
        tile   = world.get_tile(tx, ty)
        if tile and tile.is_explored:   # тільки досліджені
            self.tile_info.toggle(tile, tx, ty)
            return 'world'
        return None

    def render(self, res: ResourceSystem, pop: PopulationManager | None = None,
               bp_inv=None, day: DayCycle | None = None, crisis=None):
        if day:
            self.hud.render(self.screen, day, crisis)
        self.resource_panel.render(self.screen, res)
        # Population panel — нижче resource panel
        res_panel_h = 10 + 14 + len(list(__import__('systems.resources', fromlist=['Resource']).Resource)) * 40 + 10
        if pop is not None:
            self.population_panel.render(self.screen, pop, 56 + res_panel_h + 8)
        self.tile_info.render(self.screen)
        self.inventory.render(self.screen, bp_inv or __import__('systems.factory', fromlist=['BlueprintInventory']).BlueprintInventory())
        self._render_hints()

    def _render_hints(self):
        from ui import fonts
        font = fonts.get(10)
        hint = font.render(
            "1-9: build  |  E: inventory  |  Q: scan  |  F: factory  |  H: overlay  |  ESC: cancel",
            True, (100, 100, 90)
        )
        self.screen.blit(hint, (10, 28))


# ── Tile Info Panel ──────────────────────────────────────────────────────────

class TileInfoPanel:
    WIDTH   = 270
    PADDING = 10
    MARGIN  = 12

    BG_COLOR     = (15, 8, 4, 210)
    BORDER_COLOR = (180, 80, 30)
    TITLE_COLOR  = (255, 160, 60)
    TEXT_COLOR   = (210, 190, 170)
    COORD_COLOR  = (140, 200, 140)
    SCAN_COLOR   = (100, 180, 255)
    RICHNESS_COLOR = (255, 220, 80)

    def __init__(self):
        self._tile: Tile | None = None
        self._tx = 0
        self._ty = 0
        self._visible = False

    def show(self, tile: Tile, tx: int, ty: int):
        self._tile, self._tx, self._ty, self._visible = tile, tx, ty, True

    def hide(self):
        self._visible = False

    def toggle(self, tile: Tile, tx: int, ty: int):
        if self._visible and self._tx == tx and self._ty == ty:
            self.hide()
        else:
            self.show(tile, tx, ty)

    def _building_type_from_value(self, value: str) -> BuildingType | None:
        for bt in BuildingType:
            if bt.value == value:
                return bt
        return None

    def _expected_output_lines(self, tile: Tile) -> list[tuple[str, tuple[int,int,int]]]:
        if not tile.building:
            return []

        bt = self._building_type_from_value(tile.building)
        if bt is None:
            return []

        rates: dict[Resource, float] = {}

        defn = BUILDING_DEFS[bt]
        for res, rate in defn.produces.items():
            rates[res] = rates.get(res, 0.0) + rate

        if bt == BuildingType.SOLAR:
            rates[Resource.ENERGY] = rates.get(Resource.ENERGY, 0.0) + ResourceSystem.solar_output(
                tile.solar_modifier, 1.0
            )
        elif bt == BuildingType.EXTRACTOR:
            for tile_res_name, richness in tile.resources.as_dict().items():
                out_resource, out_amount = ResourceSystem.extractor_output(
                    tile_res_name, richness, 1.0
                )
                rates[out_resource] = rates.get(out_resource, 0.0) + out_amount

        lines: list[tuple[str, tuple[int,int,int]]] = []
        for res in Resource:
            amount = rates.get(res, 0.0)
            if amount <= 0:
                continue
            color = TILE_RES_COLORS.get(res.value, self.TEXT_COLOR)
            lines.append((f"+{amount:.1f}/s {res.value.capitalize()}", color))
        return lines

    def render(self, screen: pygame.Surface):
        if not self._visible or self._tile is None:
            return

        from ui import fonts
        font_title = fonts.get(12, bold=True)
        font_text  = fonts.get(11)

        tile = self._tile
        show_resources = tile.is_scanned
        res_dict = tile.resources.as_dict() if show_resources else {}
        output_lines = self._expected_output_lines(tile)

        # Розраховуємо висоту панелі динамічно
        base_lines = 6   # title + biome + height + coords + id + speed
        res_lines  = len(res_dict) if show_resources else 1  # 1 = "Not scanned"
        building_lines = 0
        if tile.building:
            building_lines = 2 + max(1, len(output_lines))

        total_h = self.PADDING + base_lines * 18 + 8 + res_lines * 18
        if building_lines:
            total_h += 10 + building_lines * 18
        total_h += self.PADDING

        sw, sh = screen.get_size()
        x = sw - self.WIDTH - self.MARGIN
        y = sh - total_h - self.MARGIN - 90   # вище інвентарю

        # Фон
        panel = pygame.Surface((self.WIDTH, total_h), pygame.SRCALPHA)
        panel.fill(self.BG_COLOR)
        screen.blit(panel, (x, y))
        pygame.draw.rect(screen, self.BORDER_COLOR,
                         pygame.Rect(x, y, self.WIDTH, total_h), 2)

        # Кольоровий квадрат біому
        color_rect = pygame.Rect(x + self.PADDING, y + self.PADDING, 10, 10)
        pygame.draw.rect(screen, tile.map_color or tile.color, color_rect)
        pygame.draw.rect(screen, self.BORDER_COLOR, color_rect, 1)

        tile_id = self._ty * 128 + self._tx
        cy = y + self.PADDING

        def draw_line(text, color, bold=False):
            nonlocal cy
            f = font_title if bold else font_text
            s = f.render(text, True, color)
            screen.blit(s, (x + self.PADDING, cy))
            cy += 18

        draw_line("Інформація про клітинку", self.TITLE_COLOR, bold=True)
        draw_line(f"Біом:  {tile.biome_name}",  self.TEXT_COLOR)
        draw_line(f"Висота: {tile.height_name}", self.TEXT_COLOR)
        draw_line(f"Координати: ({self._tx}, {self._ty})", self.COORD_COLOR)
        draw_line(f"ID:     {tile_id}",           self.COORD_COLOR)
        draw_line(
            f"Швидкість: x{tile.speed_modifier:.2f}  "
            f"Прохідність: {'Так' if tile.passable else 'Ні'}",
            self.TEXT_COLOR
        )

        # Роздільник
        cy += 4
        pygame.draw.line(screen, self.BORDER_COLOR,
                         (x + self.PADDING, cy),
                         (x + self.WIDTH - self.PADDING, cy), 1)
        cy += 6

        if show_resources:
            if not res_dict:
                draw_line("Без ресурсів", self.TEXT_COLOR)
            else:
                for res_name, richness in res_dict.items():
                    color = TILE_RES_COLORS.get(res_name, self.TEXT_COLOR)
                    stars = "*" * richness + "-" * (3 - richness)
                    draw_line(
                        f"{res_name.capitalize():10s} {stars}",
                        color
                    )
        else:
            draw_line("[ Не відскановано - натисніть Q ]", self.SCAN_COLOR)

        if tile.building:
            cy += 4
            pygame.draw.line(screen, self.BORDER_COLOR,
                             (x + self.PADDING, cy),
                             (x + self.WIDTH - self.PADDING, cy), 1)
            cy += 6

            bt = self._building_type_from_value(tile.building)
            building_label = BUILDING_DEFS[bt].label if bt else tile.building
            draw_line(f"Будівля: {building_label}", self.TEXT_COLOR)
            draw_line("Очікуваний вихід:", self.TITLE_COLOR)

            if output_lines:
                for text, color in output_lines:
                    draw_line(text, color)
            else:
                draw_line("Без +вихід/с", self.TEXT_COLOR)
