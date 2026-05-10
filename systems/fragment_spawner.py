"""
Spawns signal fragments on the map at game start.
Rover can collect them by pressing E near them.
"""
from __future__ import annotations
import random
from systems.lore import SignalFragment, FragmentRarity, roll_fragment_rarity
from world.world import World
from world.tile import TileExploreState

FRAGMENT_COUNT = 18   # скільки фрагментів на карті
COLLECT_RADIUS = 1    # тайлів від ровера


class FragmentSpawner:
    def __init__(self, world: World, seed: int | None = None):
        self._rng = random.Random(seed)
        self._fragments: list[SignalFragment] = []
        self._spawn(world)

    def _spawn(self, world: World):
        placed = 0
        attempts = 0
        while placed < FRAGMENT_COUNT and attempts < 2000:
            attempts += 1
            tx = self._rng.randint(5, world.width  - 5)
            ty = self._rng.randint(5, world.height - 5)
            tile = world.get_tile(tx, ty)
            if tile and tile.passable:
                rarity = roll_fragment_rarity(self._rng)
                self._fragments.append(
                    SignalFragment(tx=tx, ty=ty, rarity=rarity)
                )
                placed += 1

    def try_collect(self, rover_tx: int, rover_ty: int) -> SignalFragment | None:
        """Збирає найближчий фрагмент якщо ровер поруч."""
        for frag in self._fragments:
            dist = max(abs(frag.tx - rover_tx), abs(frag.ty - rover_ty))
            if dist <= COLLECT_RADIUS:
                self._fragments.remove(frag)
                return frag
        return None

    def nearby_fragment(self, rover_tx: int, rover_ty: int) -> SignalFragment | None:
        """Повертає фрагмент поруч (для підказки E)."""
        for frag in self._fragments:
            if not frag:
                continue
            dist = max(abs(frag.tx - rover_tx), abs(frag.ty - rover_ty))
            if dist <= COLLECT_RADIUS:
                return frag
        return None

    def render(self, screen, camera, world):
        import pygame
        from ui import fonts
        ts = world.TILE_SIZE
        for frag in self._fragments:
            tile = world.get_tile(frag.tx, frag.ty)
            if not tile or not tile.is_explored:
                continue
            wx, wy = frag.tx * ts, frag.ty * ts
            if not camera.is_visible(wx, wy, ts):
                continue
            sx, sy = camera.apply(wx, wy)
            cx, cy = sx + ts // 2, sy + ts // 2

            # Пульсуюче кільце
            import math, pygame
            pulse = abs(math.sin(pygame.time.get_ticks() / 400))
            r = int(8 + 4 * pulse)
            s = pygame.Surface((r*2+2,)*2, pygame.SRCALPHA)
            pygame.draw.circle(s, (*frag.color, int(180 * pulse)),
                               (r+1, r+1), r, 2)
            screen.blit(s, (cx - r - 1, cy - r - 1))

            # Іконка
            pygame.draw.circle(screen, frag.color, (cx, cy), 5)
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy), 5, 1)
