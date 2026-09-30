"""Биомы мира."""
from settings import BIOME_BOUNDS


BIOMES = {
    "snow_peaks": {
        "name": "Снежные вершины",
        "bg": (215, 225, 240),
        "bg_dark": (150, 170, 200),
        "platform": (240, 245, 250),
        "accent": (200, 220, 235),
    },
    "mountains": {
        "name": "Горы",
        "bg": (95, 105, 135),
        "bg_dark": (60, 70, 100),
        "platform": (120, 110, 100),
        "accent": (160, 140, 125),
    },
    "hills": {
        "name": "Холмы",
        "bg": (70, 80, 110),
        "bg_dark": (45, 55, 85),
        "platform": (110, 85, 55),
        "accent": (150, 115, 75),
    },
    "forest": {
        "name": "Лес",
        "bg": (18, 16, 30),
        "bg_dark": (8, 8, 18),
        "platform": (90, 75, 120),
        "accent": (140, 120, 170),
    },
    "caves": {
        "name": "Пещеры",
        "bg": (38, 22, 28),
        "bg_dark": (20, 10, 15),
        "platform": (115, 60, 50),
        "accent": (160, 95, 75),
    },
    "deep_caves": {
        "name": "Глубокие пещеры",
        "bg": (15, 10, 25),
        "bg_dark": (3, 3, 12),
        "platform": (70, 50, 80),
        "accent": (110, 75, 120),
    },
}


def get_biome(world_y):
    """Возвращает ключ биома для мировой Y-координаты."""
    for y_min, y_max, key in BIOME_BOUNDS:
        if y_min <= world_y < y_max:
            return key
    return "forest"


def get_biome_color(world_y):
    return BIOMES[get_biome(world_y)]
