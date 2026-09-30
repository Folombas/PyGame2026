"""Биомы мира — естественные, реалистичные цвета."""
from settings import BIOME_BOUNDS


BIOMES = {
    "snow_peaks": {
        "name": "Снежные вершины",
        "bg_top": (185, 210, 235),     # холодное небо
        "bg_bot": (225, 235, 245),
        "platform_top": (250, 252, 255),  # снег
        "platform_body": (130, 140, 155),  # камень
        "platform_edge": (90, 100, 115),
    },
    "mountains": {
        "name": "Горы",
        "bg_top": (125, 175, 220),     # синее небо
        "bg_bot": (185, 215, 235),
        "platform_top": (145, 140, 130),   # серый камень
        "platform_body": (105, 95, 85),
        "platform_edge": (60, 55, 50),
    },
    "hills": {
        "name": "Холмы",
        "bg_top": (110, 170, 220),     # синее небо
        "bg_bot": (170, 205, 230),
        "platform_top": (110, 190, 90),    # светло-зелёная трава
        "platform_body": (120, 85, 55),    # коричневая земля
        "platform_edge": (75, 50, 30),
    },
    "forest": {
        "name": "Луг",
        "bg_top": (100, 170, 230),     # классическое синее небо
        "bg_bot": (165, 210, 235),
        "platform_top": (85, 175, 75),     # трава
        "platform_body": (120, 80, 50),    # земля
        "platform_edge": (70, 45, 25),
    },
    "caves": {
        "name": "Пещеры",
        "bg_top": (45, 30, 35),
        "bg_bot": (25, 15, 20),
        "platform_top": (130, 100, 85),
        "platform_body": (85, 60, 50),
        "platform_edge": (45, 30, 25),
    },
    "deep_caves": {
        "name": "Глубокие пещеры",
        "bg_top": (20, 15, 30),
        "bg_bot": (8, 5, 15),
        "platform_top": (80, 65, 90),
        "platform_body": (50, 40, 60),
        "platform_edge": (25, 20, 35),
    },
}


def get_biome(world_y):
    for y_min, y_max, key in BIOME_BOUNDS:
        if y_min <= world_y < y_max:
            return key
    return "forest"


def get_biome_color(world_y):
    return BIOMES[get_biome(world_y)]
