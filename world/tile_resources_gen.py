import random
from world.tile import Tile, Biome, HeightLevel, TileResources

# ── Шанси появи ресурсу на клітинці (0.0-1.0) per biome ────────────────────
# Формат: {Resource: {Biome: chance}}
SPAWN_CHANCE: dict[str, dict[Biome, float]] = {
    "iron": {
        Biome.BRIGHT_LANDS:      0.30,
        Biome.DARK_LANDS:        0.55,
        Biome.CRATER_FIELDS:     0.45,
        Biome.VOLCANIC_PLATEAU:  0.25,
        Biome.POLAR_CAPS:        0.10,
        Biome.VALLES_MARINERIS:  0.20,
    },
    "water": {
        Biome.BRIGHT_LANDS:      0.10,
        Biome.DARK_LANDS:        0.05,
        Biome.CRATER_FIELDS:     0.15,
        Biome.VOLCANIC_PLATEAU:  0.05,
        Biome.POLAR_CAPS:        0.65,
        Biome.VALLES_MARINERIS:  0.25,
    },
    "silicon": {
        Biome.BRIGHT_LANDS:      0.15,
        Biome.DARK_LANDS:        0.10,
        Biome.CRATER_FIELDS:     0.20,
        Biome.VOLCANIC_PLATEAU:  0.50,
        Biome.POLAR_CAPS:        0.05,
        Biome.VALLES_MARINERIS:  0.10,
    },
    "fuel": {
        Biome.BRIGHT_LANDS:      0.08,
        Biome.DARK_LANDS:        0.12,
        Biome.CRATER_FIELDS:     0.10,
        Biome.VOLCANIC_PLATEAU:  0.20,
        Biome.POLAR_CAPS:        0.05,
        Biome.VALLES_MARINERIS:  0.08,
    },
    "uranium": {
        Biome.BRIGHT_LANDS:      0.03,
        Biome.DARK_LANDS:        0.05,
        Biome.CRATER_FIELDS:     0.06,
        Biome.VOLCANIC_PLATEAU:  0.08,
        Biome.POLAR_CAPS:        0.01,
        Biome.VALLES_MARINERIS:  0.04,
    },
}

# Модифікатор шансу по висоті
HEIGHT_SPAWN_MOD: dict[HeightLevel, float] = {
    HeightLevel.DEEP_LOWLANDS: 1.20,
    HeightLevel.LOWLANDS:      1.10,
    HeightLevel.PLAINS:        1.00,
    HeightLevel.HIGH_PLAINS:   0.95,
    HeightLevel.HIGHLANDS:     0.90,
    HeightLevel.PLATEAUS:      1.15,   # плато — гарне для silicon
    HeightLevel.MOUNTAINS:     0.00,   # немає ресурсів
}

# Шанси richness (1, 2, 3) per resource
# uranium завжди x1
RICHNESS_CHANCES: dict[str, list[float]] = {
    # [шанс x1, шанс x2, шанс x3]
    "iron":    [0.55, 0.30, 0.15],
    "water":   [0.60, 0.30, 0.10],
    "silicon": [0.60, 0.30, 0.10],
    "fuel":    [0.70, 0.25, 0.05],
    "uranium": [1.00, 0.00, 0.00],
}


def _roll_richness(resource: str, rng: random.Random) -> int:
    chances = RICHNESS_CHANCES[resource]
    r = rng.random()
    if r < chances[0]:
        return 1
    elif r < chances[0] + chances[1]:
        return 2
    return 3


def generate_tile_resources(tile: Tile, rng: random.Random):
    height_mod = HEIGHT_SPAWN_MOD.get(tile.height, 0.0)
    if height_mod == 0.0:
        return   # гори - без ресурсів

    res = TileResources()
    for resource, biome_chances in SPAWN_CHANCE.items():
        base_chance = biome_chances.get(tile.biome, 0.0)
        final_chance = base_chance * height_mod
        if rng.random() < final_chance:
            richness = _roll_richness(resource, rng)
            setattr(res, resource, richness)

    tile.resources = res
