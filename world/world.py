import pygame
from PIL import Image
from world.tile import Tile, HeightLevel, HEIGHT_BRIGHTNESS, TileExploreState, BIOME_BASE_COLOR
from world import generator
from core.camera import Camera

FOG_COLOR       = (0, 0, 0)
EXPLORED_DIM    = (0, 0, 0, 110)   # напівпрозоре затемнення для explored


class World:
    TILE_SIZE = 64

    def __init__(
        self,
        width:  int = 128,
        height: int = 64,
        height_path: str = "assets/maps/height.png",
        biome_path:  str = "assets/maps/biome.png",
        map_path:    str = "assets/maps/map.png",
        seed: int | None = None,
    ):
        self.width  = width
        self.height = height
        self.grid   = generator.generate(
            width, height, height_path, biome_path, map_path, seed
        )
        self.show_overlay = False
        self.overlay_mode = 0   # 0: none, 1: height, 2: biome, 3: resources
        self._dirty: set[tuple[int,int]] = set()   # тайли що змінили стан

        map_w = width  * self.TILE_SIZE
        map_h = height * self.TILE_SIZE

        print(f"Змінюємо розмір карти до {map_w}x{map_h}...")
        pil_map = Image.open(map_path).convert("RGB").resize(
            (map_w, map_h), Image.LANCZOS
        )
        self._map_surface = pygame.image.fromstring(
            pil_map.tobytes(), (map_w, map_h), "RGB"
        ).convert()
        print("Карта готова.")

        self._grid_overlay     = self._bake_grid()
        self._height_overlay   = self._bake_height_overlay()
        self._fog_surface      = self._bake_fog()   # повністю чорний fog
        self._biome_overlay    = self._bake_biome_overlay()


    def _bake_grid(self) -> pygame.Surface:
        ts   = self.TILE_SIZE
        surf = pygame.Surface((self.width * ts, self.height * ts), pygame.SRCALPHA)
        for ty in range(self.height):
            for tx in range(self.width):
                rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
                pygame.draw.rect(surf, (0, 0, 0, 55), rect, 1)
        return surf

    def _bake_height_overlay(self) -> pygame.Surface:
        ts   = self.TILE_SIZE
        surf = pygame.Surface((self.width * ts, self.height * ts), pygame.SRCALPHA)
        for ty, row in enumerate(self.grid):
            for tx, tile in enumerate(row):
                rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
                b    = HEIGHT_BRIGHTNESS[tile.height]
                if b < 1.0:
                    pygame.draw.rect(surf, (0, 0, 0, int((1-b)*160)), rect)
                elif b > 1.0:
                    pygame.draw.rect(surf, (255, 220, 180, int((b-1)*130)), rect)
                if tile.height == HeightLevel.MOUNTAINS:
                    pygame.draw.rect(surf, (0, 0, 0, 120), rect)
                    pygame.draw.line(surf, (0, 0, 0, 180),
                                     rect.topleft, rect.bottomright, 2)
                    pygame.draw.line(surf, (0, 0, 0, 180),
                                     rect.topright, rect.bottomleft, 2)
        return surf

    def _bake_biome_overlay(self) -> pygame.Surface:
        ts = self.TILE_SIZE
        surf = pygame.Surface((self.width * ts, self.height * ts), pygame.SRCALPHA)
        for ty, row in enumerate(self.grid):
            for tx, tile in enumerate(row):
                rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
                color = BIOME_BASE_COLOR.get(tile.biome, (100,100,100))
                # напівпрозорий прямокутник кольору біому
                pygame.draw.rect(surf, (*color, 140), rect)
        return surf

    

    def _bake_fog(self) -> pygame.Surface:
        ts   = self.TILE_SIZE
        surf = pygame.Surface((self.width * ts, self.height * ts), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 255))
        return surf


    def mark_dirty(self, tx: int, ty: int):
        self._dirty.add((tx, ty))

    def _update_fog_patches(self):
        if not self._dirty:
            return
        ts = self.TILE_SIZE
        for (tx, ty) in self._dirty:
            tile = self.get_tile(tx, ty)
            if tile is None:
                continue
            rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
            if tile.is_scanned:
                # Повністю прозорий - fog знятий
                self._fog_surface.fill((0, 0, 0, 0), rect)
            elif tile.is_explored:
                # Напівпрозорий туман
                self._fog_surface.fill(EXPLORED_DIM, rect)
            else:
                # Чорний fog
                self._fog_surface.fill((0, 0, 0, 255), rect)
        self._dirty.clear()


    def cycle_overlay(self):
        self.overlay_mode = (self.overlay_mode + 1) % 4

    def render(self, screen: pygame.Surface, camera: Camera):
        self._update_fog_patches()
        src = pygame.Rect(int(camera.x), int(camera.y),
                          camera.screen_w, camera.screen_h)
        screen.blit(self._map_surface, (0, 0), src)

        # Циклічні оверлеї
        if self.overlay_mode == 1:   # height
            screen.blit(self._height_overlay, (0, 0), src)
        elif self.overlay_mode == 2: # biome
            screen.blit(self._biome_overlay, (0, 0), src)
        elif self.overlay_mode == 3:    # resources (динамічний, тільки скановані)
            self._render_resource_overlay(screen, camera)

        screen.blit(self._grid_overlay, (0, 0), src)
        screen.blit(self._fog_surface,  (0, 0), src)
    def _render_resource_overlay(self, screen: pygame.Surface, camera: Camera):
        ts = self.TILE_SIZE
        res_colors = {
            "iron":    (180, 130, 90),
            "water":   (80,  160, 220),
            "silicon": (140, 200, 140),
            "fuel":    (220, 120, 50),
            "uranium": (130, 220, 100),
        }

        # Визначаємо тайли, які потрапляють у видиму область камери
        start_tx = max(0, int(camera.x // ts))
        start_ty = max(0, int(camera.y // ts))
        end_tx   = min(self.width,  int((camera.x + camera.screen_w) // ts) + 1)
        end_ty   = min(self.height, int((camera.y + camera.screen_h) // ts) + 1)

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                tile = self.get_tile(tx, ty)
                # Пропускаємо не скановані та None
                if not tile or not tile.is_scanned:
                    continue

                wx, wy = tx * ts, ty * ts
                if not camera.is_visible(wx, wy, ts):
                    continue

                sx, sy = camera.apply(wx, wy)
                cx = sx + ts // 2
                cy = sy + ts // 2

                for res_name, richness in tile.resources.as_dict().items():
                    color  = res_colors.get(res_name, (200, 200, 200))
                    radius = 4 + richness * 2          # більший кружечок для багатших ресурсів
                    pygame.draw.circle(screen, (*color, 180), (cx, cy), radius)
    def get_tile(self, tx: int, ty: int) -> Tile | None:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
        return None

    def get_tile_at_world(self, wx: float, wy: float) -> Tile | None:
        return self.get_tile(int(wx // self.TILE_SIZE), int(wy // self.TILE_SIZE))

    def screen_to_tile(self, sx: int, sy: int, camera: Camera) -> tuple[int, int]:
        return (int((sx + camera.x) // self.TILE_SIZE),
                int((sy + camera.y) // self.TILE_SIZE))