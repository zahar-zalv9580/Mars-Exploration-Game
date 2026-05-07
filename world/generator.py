from PIL import Image
from world.tile import Tile, Biome, HeightLevel

# --- Таблиці кольорів з PNG ---

# height.png: RGB -> HeightLevel
HEIGHT_COLOR_MAP: dict[tuple[int,int,int], HeightLevel] = {
    (0,   0,   255): HeightLevel.DEEP_LOWLANDS,
    (0,   255, 255): HeightLevel.LOWLANDS,
    (0,   255, 0):   HeightLevel.PLAINS,
    (255, 255, 0):   HeightLevel.HIGH_PLAINS,
    (255, 0,   0):   HeightLevel.HIGHLANDS,
    (255, 0,   255): HeightLevel.PLATEAUS,
    (255, 255, 255): HeightLevel.MOUNTAINS,
}

# biome.png: RGB -> Biome
BIOME_COLOR_MAP: dict[tuple[int,int,int], Biome] = {
    (255, 255, 255): Biome.POLAR_CAPS,
    (0,   0,   0):   Biome.DARK_LANDS,
    (127, 127, 127): Biome.CRATER_FIELDS,
    (0,   255, 0):   Biome.BRIGHT_LANDS,
    (255, 0,   0):   Biome.VOLCANIC_PLATEAU,
    (0,   0,   255): Biome.VALLES_MARINERIS,
}


def _nearest_color(pixel: tuple, color_map: dict) -> any:
    """Знаходить найближчий колір у таблиці (захист від anti-aliasing)."""
    best_key = None
    best_dist = float("inf")
    r, g, b = pixel[0], pixel[1], pixel[2]
    for (cr, cg, cb), value in color_map.items():
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if dist < best_dist:
            best_dist = dist
            best_key = value
    return best_key


def generate(
    width: int,
    height: int,
    height_path: str = "assets/maps/height.png",
    biome_path:  str = "assets/maps/biome.png",
    map_path:    str = "assets/maps/map.png",
) -> list[list[Tile]]:
    """
    Читає height.png, biome.png і map.png і будує сітку тайлів.
    Розміри PNG мають бути width x height пікселів (128x64).
    map.png залишається оригінальною текстурою (без масштабування).
    """
    h_img  = Image.open(height_path).convert("RGB").resize((width, height), Image.NEAREST)
    b_img  = Image.open(biome_path).convert("RGB").resize((width, height), Image.NEAREST)
    m_img  = Image.open(map_path).convert("RGB")  # Оригінальна текстура без масштабування

    h_px = h_img.load()
    b_px = b_img.load()

    grid: list[list[Tile]] = []
    for ty in range(height):
        row: list[Tile] = []
        for tx in range(width):
            hlevel    = _nearest_color(h_px[tx, ty], HEIGHT_COLOR_MAP)
            biome     = _nearest_color(b_px[tx, ty], BIOME_COLOR_MAP)

            row.append(Tile(
                biome=biome,
                height=hlevel,
            ))
        grid.append(row)

    return grid
