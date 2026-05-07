import pygame
from PIL import Image
from world.tile import Tile, HeightLevel, HEIGHT_BRIGHTNESS
from world import generator
from core.camera import Camera


class World:
    TILE_SIZE = 64

    def __init__(
        self,
        width:  int = 128,
        height: int = 64,
        height_path: str = "assets/maps/height.png",
        biome_path:  str = "assets/maps/biome.png",
        map_path:    str = "assets/maps/map.png",
    ):
        self.width  = width
        self.height = height
        self.grid   = generator.generate(width, height, height_path, biome_path, map_path)

        self.show_overlay = False   # H — перемикач

        map_w = width  * self.TILE_SIZE
        map_h = height * self.TILE_SIZE

        print(f"Scaling map.png to {map_w}x{map_h}...")
        pil_map = Image.open(map_path).convert("RGB").resize((map_w, map_h), Image.LANCZOS)
        raw = pil_map.tobytes()
        self._map_surface = pygame.image.fromstring(raw, (map_w, map_h), "RGB").convert()
        print("Map surface ready.")

        self._grid_overlay    = self._bake_grid()
        self._height_overlay  = self._bake_height_overlay()

    # ------------------------------------------------------------------ baking

    def _bake_grid(self) -> pygame.Surface:
        """Тільки сітка — завжди видима."""
        ts   = self.TILE_SIZE
        surf = pygame.Surface((self.width * ts, self.height * ts), pygame.SRCALPHA)
        for ty, row in enumerate(self.grid):
            for tx, tile in enumerate(row):
                rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
                pygame.draw.rect(surf, (0, 0, 0, 55), rect, 1)
        return surf

    def _bake_height_overlay(self) -> pygame.Surface:
        """Затемнення/освітлення + гори — вмикається клавішею H."""
        ts   = self.TILE_SIZE
        surf = pygame.Surface((self.width * ts, self.height * ts), pygame.SRCALPHA)
        for ty, row in enumerate(self.grid):
            for tx, tile in enumerate(row):
                rect       = pygame.Rect(tx * ts, ty * ts, ts, ts)
                brightness = HEIGHT_BRIGHTNESS[tile.height]

                if brightness < 1.0:
                    alpha = int((1.0 - brightness) * 160)
                    pygame.draw.rect(surf, (0, 0, 0, alpha), rect)
                elif brightness > 1.0:
                    alpha = int((brightness - 1.0) * 130)
                    pygame.draw.rect(surf, (255, 220, 180, alpha), rect)

                if tile.height == HeightLevel.MOUNTAINS:
                    pygame.draw.rect(surf, (0, 0, 0, 120), rect)
                    pygame.draw.line(surf, (0, 0, 0, 180),
                                     rect.topleft, rect.bottomright, 2)
                    pygame.draw.line(surf, (0, 0, 0, 180),
                                     rect.topright, rect.bottomleft, 2)
        return surf

    # ------------------------------------------------------------------ public

    def toggle_overlay(self):
        self.show_overlay = not self.show_overlay

    def render(self, screen: pygame.Surface, camera: Camera):
        src = pygame.Rect(int(camera.x), int(camera.y), camera.screen_w, camera.screen_h)
        screen.blit(self._map_surface, (0, 0), src)
        if self.show_overlay:
            screen.blit(self._height_overlay, (0, 0), src)
        screen.blit(self._grid_overlay, (0, 0), src)

    def get_tile(self, tx: int, ty: int) -> Tile | None:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
        return None

    def get_tile_at_world(self, wx: float, wy: float) -> Tile | None:
        return self.get_tile(int(wx // self.TILE_SIZE), int(wy // self.TILE_SIZE))

    def screen_to_tile(self, sx: int, sy: int, camera: Camera) -> tuple[int, int]:
        wx = sx + camera.x
        wy = sy + camera.y
        return int(wx // self.TILE_SIZE), int(wy // self.TILE_SIZE)
