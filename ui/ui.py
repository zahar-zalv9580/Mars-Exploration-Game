import pygame
from world.tile import Tile


class UI:
    """Головний UI менеджер. Збирає всі елементи інтерфейсу."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.tile_info = TileInfoPanel()

    def handle_click(self, mx: int, my: int, world, camera) -> bool:
        """Обробляє клік миші. Повертає True якщо клік поглинув UI."""
        tx, ty = world.screen_to_tile(mx, my, camera)
        tile   = world.get_tile(tx, ty)
        if tile:
            self.tile_info.toggle(tile, tx, ty)
            return True
        return False

    def render(self):
        self.tile_info.render(self.screen)
        self._render_hints()

    def _render_hints(self):
        font = pygame.font.SysFont("consolas", 13)
        hint = font.render("LMB: tile info  |  ESC: pause", True, (100, 100, 90))
        self.screen.blit(hint, (10, 28))


# ---------------------------------------------------------------------------

class TileInfoPanel:
    WIDTH   = 260
    HEIGHT  = 140
    MARGIN  = 12
    PADDING = 10

    BG_COLOR     = (15, 8, 4, 210)
    BORDER_COLOR = (180, 80, 30)
    TITLE_COLOR  = (255, 160, 60)
    TEXT_COLOR   = (210, 190, 170)
    COORD_COLOR  = (140, 200, 140)

    def __init__(self):
        self._tile: Tile | None = None
        self._tx = 0
        self._ty = 0
        self._visible    = False
        self._font_title = pygame.font.SysFont("consolas", 14, bold=True)
        self._font_text  = pygame.font.SysFont("consolas", 13)

    def show(self, tile: Tile, tx: int, ty: int):
        self._tile    = tile
        self._tx      = tx
        self._ty      = ty
        self._visible = True

    def hide(self):
        self._visible = False

    def toggle(self, tile: Tile, tx: int, ty: int):
        if self._visible and self._tx == tx and self._ty == ty:
            self.hide()
        else:
            self.show(tile, tx, ty)

    def render(self, screen: pygame.Surface):
        if not self._visible or self._tile is None:
            return

        sw, sh = screen.get_size()
        x = sw - self.WIDTH  - self.MARGIN
        y = sh - self.HEIGHT - self.MARGIN

        panel = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        panel.fill(self.BG_COLOR)
        screen.blit(panel, (x, y))
        pygame.draw.rect(screen, self.BORDER_COLOR,
                         pygame.Rect(x, y, self.WIDTH, self.HEIGHT), 2)

        color_rect = pygame.Rect(x + self.PADDING, y + self.PADDING, 12, 12)
        pygame.draw.rect(screen, self._tile.map_color or self._tile.color, color_rect)
        pygame.draw.rect(screen, self.BORDER_COLOR, color_rect, 1)

        tile_id = self._ty * 128 + self._tx

        lines = [
            ("TILE INFO",                                   self.TITLE_COLOR, self._font_title, 28),
            (f"Biome:  {self._tile.biome_name}",            self.TEXT_COLOR,  self._font_text,  46),
            (f"Height: {self._tile.height_name}",           self.TEXT_COLOR,  self._font_text,  64),
            (f"Coords: ({self._tx}, {self._ty})",           self.COORD_COLOR, self._font_text,  82),
            (f"ID:     {tile_id}",                          self.COORD_COLOR, self._font_text, 100),
            (f"Speed:  x{self._tile.speed_modifier:.2f}  "
             f"Pass: {'Yes' if self._tile.passable else 'NO'}",
             self.TEXT_COLOR, self._font_text, 118),
        ]

        for text, color, font, offset_y in lines:
            surf = font.render(text, True, color)
            screen.blit(surf, (x + self.PADDING, y + offset_y))
