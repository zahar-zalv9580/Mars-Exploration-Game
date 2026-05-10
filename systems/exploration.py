# Система дослідження. Відповідає за відкриття нових tiles навколо ровера та сканування конкретних tiles.
from world.world import World
from world.tile import TileExploreState

EXPLORE_RADIUS = 3


class ExplorationSystem:
    def __init__(self, world: World):
        self._world = world

    def explore_around(self, rover_tx: int, rover_ty: int):
        # Відкриває tiles в радіусі EXPLORE_RADIUS навколо ровера
        for dy in range(-EXPLORE_RADIUS, EXPLORE_RADIUS + 1):
            for dx in range(-EXPLORE_RADIUS, EXPLORE_RADIUS + 1):
                tile = self._world.get_tile(rover_tx + dx, rover_ty + dy)
                if tile and tile.is_unexplored:
                    tile.explore_tile()
                    # Помічаємо surface як брудний
                    self._world.mark_dirty(rover_tx + dx, rover_ty + dy)

    def scan_tile(self, tx: int, ty: int) -> bool:
        tile = self._world.get_tile(tx, ty)
        if tile and tile.is_explored:
            was_scanned = tile.is_scanned
            tile.scan_tile()
            if not was_scanned:
                self._world.mark_dirty(tx, ty)
            return True
        return False
