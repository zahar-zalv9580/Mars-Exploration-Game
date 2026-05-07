from dataclasses import dataclass, field
from enum import IntEnum


class Biome(IntEnum):
    BRIGHT_LANDS     = 0
    DARK_LANDS       = 1
    CRATER_FIELDS    = 2
    VOLCANIC_PLATEAU = 3
    POLAR_CAPS       = 4
    VALLES_MARINERIS = 5


class HeightLevel(IntEnum):
    DEEP_LOWLANDS = 0
    LOWLANDS      = 1
    PLAINS        = 2
    HIGH_PLAINS   = 3
    HIGHLANDS     = 4
    PLATEAUS      = 5
    MOUNTAINS     = 6


BIOME_NAMES = {
    Biome.BRIGHT_LANDS:      "Bright Lands",
    Biome.DARK_LANDS:        "Dark Lands",
    Biome.CRATER_FIELDS:     "Crater Fields",
    Biome.VOLCANIC_PLATEAU:  "Volcanic Plateau",
    Biome.POLAR_CAPS:        "Polar Caps",
    Biome.VALLES_MARINERIS:  "Valles Marineris",
}

HEIGHT_NAMES = {
    HeightLevel.DEEP_LOWLANDS: "Deep Lowlands",
    HeightLevel.LOWLANDS:      "Lowlands",
    HeightLevel.PLAINS:        "Plains",
    HeightLevel.HIGH_PLAINS:   "High Plains",
    HeightLevel.HIGHLANDS:     "Highlands",
    HeightLevel.PLATEAUS:      "Plateaus",
    HeightLevel.MOUNTAINS:     "Mountains",
}

# Базовий колір з map.png — але як fallback якщо map не завантажено
BIOME_BASE_COLOR: dict[Biome, tuple[int,int,int]] = {
    Biome.BRIGHT_LANDS:      (180, 90,  50),
    Biome.DARK_LANDS:        (60,  35,  25),
    Biome.CRATER_FIELDS:     (130, 70,  45),
    Biome.VOLCANIC_PLATEAU:  (100, 50,  25),
    Biome.POLAR_CAPS:        (220, 210, 205),
    Biome.VALLES_MARINERIS:  (80,  45,  30),
}

HEIGHT_BRIGHTNESS: dict[HeightLevel, float] = {
    HeightLevel.DEEP_LOWLANDS: 0.55,
    HeightLevel.LOWLANDS:      0.70,
    HeightLevel.PLAINS:        0.90,
    HeightLevel.HIGH_PLAINS:   1.00,
    HeightLevel.HIGHLANDS:     1.12,
    HeightLevel.PLATEAUS:      1.22,
    HeightLevel.MOUNTAINS:     1.40,
}

HEIGHT_SPEED_MOD: dict[HeightLevel, float] = {
    HeightLevel.DEEP_LOWLANDS: 0.65,
    HeightLevel.LOWLANDS:      0.82,
    HeightLevel.PLAINS:        1.00,
    HeightLevel.HIGH_PLAINS:   0.95,
    HeightLevel.HIGHLANDS:     0.82,
    HeightLevel.PLATEAUS:      0.88,
    HeightLevel.MOUNTAINS:     0.00,
}


def _blend(color: tuple[int,int,int], factor: float) -> tuple[int,int,int]:
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


@dataclass
class Tile:
    biome:    Biome       = Biome.BRIGHT_LANDS
    height:   HeightLevel = HeightLevel.PLAINS
    building: str | None  = None
    explored: bool        = False
    map_color: tuple[int,int,int] | None = None   # колір з map.png

    _color: tuple[int,int,int] = field(init=False, repr=False)

    def __post_init__(self):
        self._color = self._compute_color()

    def _compute_color(self) -> tuple[int,int,int]:
        base   = self.map_color if self.map_color else BIOME_BASE_COLOR[self.biome]
        factor = HEIGHT_BRIGHTNESS[self.height]
        return _blend(base, factor)

    @property
    def color(self) -> tuple[int,int,int]:
        return self._color

    @property
    def speed_modifier(self) -> float:
        return HEIGHT_SPEED_MOD[self.height]

    @property
    def passable(self) -> bool:
        return self.height != HeightLevel.MOUNTAINS

    @property
    def biome_name(self) -> str:
        return BIOME_NAMES[self.biome]

    @property
    def height_name(self) -> str:
        return HEIGHT_NAMES[self.height]
