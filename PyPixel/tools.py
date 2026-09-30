"""Инструменты: кирка, топор, меч. Всё программно."""
import pygame

PICKAXE = "pickaxe"
AXE = "axe"
SWORD = "sword"

# ---------- Спрайты 10x10 ----------
PICKAXE_SPRITE = [
    ".MMMMMMMM.",
    "M.M....M.M",
    "M........M",
    "....BB....",
    "....BB....",
    "....BB....",
    "....BB....",
    "....BB....",
    "....BB....",
    "....BB....",
]

AXE_SPRITE = [
    "..AAAA....",
    ".AAAAAA...",
    "AAAA.BB...",
    "AA...BB...",
    ".....BB...",
    ".....BB...",
    ".....BB...",
    ".....BB...",
    ".....BB...",
    ".....BB...",
]

SWORD_SPRITE = [
    ".......SS.",
    "......SSS.",
    ".....SSS..",
    "....SSS...",
    "...SSS....",
    "..SSS.....",
    ".GGGG.....",
    ".BB.......",
    ".BB.......",
    ".B........",
]

TOOL_PALETTES = {
    PICKAXE: {"M": (200, 210, 220), "B": (120, 80, 50)},
    AXE:     {"A": (180, 190, 200), "B": (120, 80, 50)},
    SWORD:   {"S": (220, 230, 245), "G": (240, 200, 80), "B": (120, 80, 50)},
}

TOOL_SPRITES = {
    PICKAXE: PICKAXE_SPRITE,
    AXE: AXE_SPRITE,
    SWORD: SWORD_SPRITE,
}

TOOLS = {
    PICKAXE: {
        "name": "Кирка",
        "speed": 3.5,         # ускорение против соответствующих блоков
        "damage": 1,
        "range": 6,           # радиус копания (в тайлах)
    },
    AXE: {
        "name": "Топор",
        "speed": 5.0,
        "damage": 1,
        "range": 5,
    },
    SWORD: {
        "name": "Меч",
        "speed": 1.0,
        "damage": 3,          # урон по врагам
        "range": 5,
        "attack_range_px": 90,
    },
}


_cache = {}

def get_tool_sprite(tool_id, size=32):
    """Возвращает Surface с иконкой инструмента (кешируется)."""
    key = (tool_id, size)
    if key in _cache:
        return _cache[key]
    pattern = TOOL_SPRITES.get(tool_id)
    palette = TOOL_PALETTES.get(tool_id)
    if not pattern:
        return None
    h = len(pattern)
    w = len(pattern[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            col = palette.get(ch)
            if col is not None:
                surf.set_at((x, y), col)
    scaled = pygame.transform.scale(surf, (size, size))
    _cache[key] = scaled
    return scaled


def draw_tool_icon(surface, rect, tool_id):
    """Рисует иконку инструмента в прямоугольнике."""
    sprite = get_tool_sprite(tool_id, min(rect.w, rect.h))
    if sprite:
        r = sprite.get_rect(center=rect.center)
        surface.blit(sprite, r)
