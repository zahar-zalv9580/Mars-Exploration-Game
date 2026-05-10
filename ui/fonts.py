"""Централізоване завантаження шрифтів. Імпортуй звідси скрізь."""
import pygame

FONT_PATH = "assets/fonts/Minecraft_1_1.ttf"

_cache: dict[tuple[str, int, bool], pygame.font.Font] = {}


def get(size: int, bold: bool = False) -> pygame.font.Font:
    key = (FONT_PATH, size, bold)
    if key not in _cache:
        try:
            f = pygame.font.Font(FONT_PATH, size)
        except Exception:
            f = pygame.font.SysFont("consolas", size, bold=bold)
        _cache[key] = f
    return _cache[key]


def clear_cache():
    _cache.clear()
