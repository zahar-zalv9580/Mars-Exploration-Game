import random
from PIL import Image
from world.tile import Tile, Biome, HeightLevel
from world.tile_resources_gen import generate_tile_resources

HEIGHT_COLOR_MAP: dict[tuple[int,int,int], HeightLevel] = {
    (0,   0,   255): HeightLevel.DEEP_LOWLANDS,
    (0,   255, 255): HeightLevel.LOWLANDS,
    (0,   255, 0):   HeightLevel.PLAINS,
    (255, 255, 0):   HeightLevel.HIGH_PLAINS,
    (255, 0,   0):   HeightLevel.HIGHLANDS,
    (255, 0,   255): HeightLevel.PLATEAUS,
    (255, 255, 255): HeightLevel.MOUNTAINS,
}

BIOME_COLOR_MAP: dict[tuple[int,int,int], Biome] = {
    (255, 255, 255): Biome.POLAR_CAPS,
    (0,   0,   0):   Biome.DARK_LANDS,
    (127, 127, 127): Biome.CRATER_FIELDS,
    (0,   255, 0):   Biome.BRIGHT_LANDS,
    (255, 0,   0):   Biome.VOLCANIC_PLATEAU,
    (0,   0,   255): Biome.VALLES_MARINERIS,
}


def _nearest_color(pixel, color_map):
    best_key, best_dist = None, float("inf")
    r, g, b = pixel[0], pixel[1], pixel[2]
    for (cr, cg, cb), value in color_map.items():
        d = (r-cr)**2 + (g-cg)**2 + (b-cb)**2
        if d < best_dist:
            best_dist, best_key = d, value
    return best_key


def generate(
    width: int, height: int,
    height_path: str = "assets/maps/height.png",
    biome_path:  str = "assets/maps/biome.png",
    map_path:    str = "assets/maps/map.png",
    seed: int | None = None,
) -> list[list[Tile]]:
    rng = random.Random(seed)

    h_img = Image.open(height_path).convert("RGB").resize((width, height), Image.NEAREST)
    b_img = Image.open(biome_path).convert("RGB").resize((width, height), Image.NEAREST)
    m_img = Image.open(map_path).convert("RGB").resize((width, height), Image.LANCZOS)

    h_px, b_px, m_px = h_img.load(), b_img.load(), m_img.load()

    grid: list[list[Tile]] = []
    for ty in range(height):
        row: list[Tile] = []
        for tx in range(width):
            hlevel    = _nearest_color(h_px[tx, ty], HEIGHT_COLOR_MAP)
            biome     = _nearest_color(b_px[tx, ty], BIOME_COLOR_MAP)
            map_color = m_px[tx, ty][:3]
            tile = Tile(biome=biome, height=hlevel, map_color=map_color)
            generate_tile_resources(tile, rng)
            row.append(tile)
        grid.append(row)

    return grid
