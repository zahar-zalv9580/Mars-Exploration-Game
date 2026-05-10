"""
Save/Load system — JSON format.
Save file: saves/savegame.json
"""
from __future__ import annotations
import json
import os
from dataclasses import asdict

SAVE_DIR  = "saves"
SAVE_FILE = "saves/savegame.json"
SAVE_VERSION = 1


def _ensure_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_exists() -> bool:
    return os.path.isfile(SAVE_FILE)


def save_game(game) -> bool:
    """Зберігає стан гри. Повертає True при успіху."""
    try:
        _ensure_dir()
        from systems.resources import Resource
        from entities.building import BuildingState

        data = {
            "version": SAVE_VERSION,

            # День
            "day":         game.day.day,
            "time_in_day": game.day.time_in_day,

            # Ровер
            "rover": {
                "x": game.rover.x,
                "y": game.rover.y,
            },

            # Ресурси
            "resources": {
                r.value: game.resources.amount(r)
                for r in Resource
            },
            "storage_count": game.resources._storage_count,

            # Популяція
            "population": {
                "population":     game.population.population,
                "capacity":       game.population.capacity,
                "habitat_count":  game.population._habitat_count,
            },

            # Будівлі
            "buildings": [
                {
                    "type":  b.type.value,
                    "tx":    b.tx,
                    "ty":    b.ty,
                    "state": b.state.name,
                    "hp":    b.hp,
                }
                for b in game.buildings._buildings.values()
            ],

            # Blueprint inventory
            "blueprints": dict(game.buildings.blueprint_inv._items),

            # Фабрика
            "factory": {
                "queue":   game.factory._queue,
                "current": game.factory._current,
                "timer":   game.factory._timer,
            },

            # Лабораторія / лор
            "lab": {
                "discovered":  list(game.lab._discovered),
                "queue":       game.lab._queue,
                "current":     game.lab._current,
                "timer":       game.lab._timer,
                "fragments":   game.lab.fragments,
            },
            "fragments": [
                {"tx": f.tx, "ty": f.ty, "rarity": f.rarity.value}
                for f in game.fragments._fragments
            ],

            # Exploration — зберігаємо стан кожного тайлу
            "exploration": [
                [int(game.world.grid[ty][tx].explore)
                 for tx in range(game.world.width)]
                for ty in range(game.world.height)
            ],
        }

        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True

    except Exception as e:
        print(f"[Save] ERROR: {e}")
        return False


def load_game(game) -> bool:
    """Завантажує стан гри. Повертає True при успіху."""
    if not save_exists():
        return False
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("version", 0) != SAVE_VERSION:
            print("[Load] Version mismatch — cannot load.")
            return False

        from systems.resources import Resource
        from entities.building import BuildingType, BuildingState, Building
        from world.tile import TileExploreState

        # День
        game.day.day         = data["day"]
        game.day.time_in_day = data["time_in_day"]

        # Ровер
        game.rover.x = data["rover"]["x"]
        game.rover.y = data["rover"]["y"]

        # Ресурси
        for r in Resource:
            val = data["resources"].get(r.value, 0.0)
            game.resources.set(r, val)
        game.resources._storage_count = data.get("storage_count", 0)
        game.resources._recalc_capacity()

        # Популяція
        pop_data = data["population"]
        game.population.population    = pop_data["population"]
        game.population.capacity      = pop_data["capacity"]
        game.population._habitat_count = pop_data["habitat_count"]

        # Будівлі
        game.buildings._buildings.clear()
        for bd in data["buildings"]:
            bt    = BuildingType(bd["type"])
            state = BuildingState[bd["state"]]
            b     = Building(type=bt, tx=bd["tx"], ty=bd["ty"])
            b.state = state
            b.hp    = bd.get("hp", 100.0)
            game.buildings._buildings[(bd["tx"], bd["ty"])] = b
            game.world.grid[bd["ty"]][bd["tx"]].building = bd["type"]

        # Blueprints
        game.buildings.blueprint_inv._items = data.get("blueprints", {})

        # Фабрика
        fac = data.get("factory", {})
        game.factory._queue   = fac.get("queue", [])
        game.factory._current = fac.get("current")
        game.factory._timer   = fac.get("timer", 0.0)
        game.factory._busy    = game.factory._current is not None

        # Лабораторія
        lab = data.get("lab", {})
        game.lab._discovered = set(lab.get("discovered", []))
        game.lab._queue      = lab.get("queue", [])
        game.lab._current    = lab.get("current")
        game.lab._timer      = lab.get("timer", 0.0)
        game.lab._busy       = game.lab._current is not None
        game.lab.fragments   = lab.get("fragments", {})

        frag_data = data.get("fragments", [])
        from systems.lore import SignalFragment, FragmentRarity
        game.fragments._fragments = [
            SignalFragment(
                tx=f.get("tx", 0),
                ty=f.get("ty", 0),
                rarity=FragmentRarity(f.get("rarity", "common"))
            )
            for f in frag_data
            if isinstance(f, dict) and "tx" in f and "ty" in f and "rarity" in f
        ]

        # Exploration
        exp_data = data.get("exploration", [])
        for ty, row in enumerate(exp_data):
            for tx, val in enumerate(row):
                tile = game.world.get_tile(tx, ty)
                if tile:
                    tile.explore = TileExploreState(val)

        # Оновлюємо fog
        for ty in range(game.world.height):
            for tx in range(game.world.width):
                game.world.mark_dirty(tx, ty)

        # Камера на ровера
        game.camera.update(game.rover.x, game.rover.y, game.world)

        print(f"[Load] Loaded — Day {game.day.day}")
        return True

    except Exception as e:
        print(f"[Load] ERROR: {e}")
        import traceback; traceback.print_exc()
        return False


def delete_save():
    if save_exists():
        os.remove(SAVE_FILE)
