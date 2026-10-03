"""Программные спрайты: зайка."""
import pygame


# ============== ЗАЙКА 10x14 ==============
# K=контур, W=белый мех, P=розовый (уши/нос), E=глаз, B=жилетка

RABBIT_DOWN_1 = [
    ".K.K.K.K.",
    ".KWKWKWK.",
    ".KWKWKWK.",
    ".KWWWWWK.",
    "KWWWWWWWK",
    "KWPWWWPWK",
    "KWWEEWWWK",
    "KWWWWWWWK",
    ".KBBBBBK.",
    ".KBBBBBK.",
    ".KBBBBBK.",
    ".K.KK.K..",
    ".K.KK.K..",
    "..K..K...",
]
RABBIT_DOWN_2 = [
    ".K.K.K.K.",
    ".KWKWKWK.",
    ".KWKWKWK.",
    ".KWWWWWK.",
    "KWWWWWWWK",
    "KWPWWWPWK",
    "KWWEEWWWK",
    "KWWWWWWWK",
    ".KBBBBBK.",
    ".KBBBBBK.",
    "B.KBBBK.B",
    "B.K.KK.KB",
    "..K.KK.K.",
    "..K..K...",
]
RABBIT_UP_1 = [
    ".K.K.K.K.",
    ".KWKWKWK.",
    ".KWKWKWK.",
    ".KWWWWWK.",
    "KWWWWWWWK",
    "KWWWWWWWK",
    "KWWWWWWWK",
    "KWWWWWWWK",
    ".KBBBBBK.",
    ".KBBBBBK.",
    ".KBBBBBK.",
    ".K.KK.K..",
    ".K.KK.K..",
    "..K..K...",
]
RABBIT_UP_2 = [
    ".K.K.K.K.",
    ".KWKWKWK.",
    ".KWKWKWK.",
    ".KWWWWWK.",
    "KWWWWWWWK",
    "KWWWWWWWK",
    "KWWWWWWWK",
    "KWWWWWWWK",
    ".KBBBBBK.",
    ".KBBBBBK.",
    "B.KBBBK.B",
    "B.K.KK.KB",
    "..K.KK.K.",
    "..K..K...",
]
RABBIT_LEFT_1 = [
    ".K.K.K...",
    ".KWKWK...",
    ".KWKWK...",
    ".KWWWK...",
    "KWWWWK...",
    "KWPWWK...",
    "KWWEWK...",
    "KWWWWK...",
    ".KBBBK...",
    ".KBBBK...",
    ".KBBBK...",
    ".K.KK.K..",
    ".K.KK.K..",
    "..K..K...",
]
RABBIT_LEFT_2 = [
    ".K.K.K...",
    ".KWKWK...",
    ".KWKWK...",
    ".KWWWK...",
    "KWWWWK...",
    "KWPWWK...",
    "KWWEWK...",
    "KWWWWK...",
    ".KBBBK...",
    "B.KBBK.B.",
    "..K.KK.K.",
    "..K.KK.K.",
    ".K..K.K..",
    "..K..K...",
]
RABBIT_RIGHT_1 = [
    "...K.K.K.",
    "...KWKWK.",
    "...KWKWK.",
    "...KWWWK.",
    "...KWWWWK",
    "...KWWPWK",
    "...KWEWWK",
    "...KWWWWK",
    "...KBBBK.",
    "...KBBBK.",
    "...KBBBK.",
    "..K.KK.K.",
    "..K.KK.K.",
    "...K..K..",
]
RABBIT_RIGHT_2 = [
    "...K.K.K.",
    "...KWKWK.",
    "...KWKWK.",
    "...KWWWK.",
    "...KWWWWK",
    "...KWWPWK",
    "...KWEWWK",
    "...KWWWWK",
    "...KBBBK.",
    ".B.KBBK.B",
    ".K.KK.K..",
    ".K.KK.K..",
    "..K.K.K..",
    "...K..K..",
]

RABBIT_PALETTE = {
    "K": (30, 25, 35),       # контур
    "W": (250, 245, 235),    # мех
    "P": (240, 150, 170),    # розовый (уши, нос)
    "E": (30, 25, 35),       # глаз
    "B": (100, 160, 220),    # жилетка
}


def build_sprite(pattern, palette, scale=2):
    h = len(pattern); w = len(pattern[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            c = palette.get(ch)
            if c:
                surf.set_at((x, y), c)
    return pygame.transform.scale(surf, (w * scale, h * scale))


RABBIT_SPRITES = {
    "down":  [RABBIT_DOWN_1, RABBIT_DOWN_2],
    "up":    [RABBIT_UP_1, RABBIT_UP_2],
    "left":  [RABBIT_LEFT_1, RABBIT_LEFT_2],
    "right": [RABBIT_RIGHT_1, RABBIT_RIGHT_2],
}

_cache = {}

def get_player_sprite(direction, frame):
    key = (direction, frame)
    if key in _cache:
        return _cache[key]
    pattern = RABBIT_SPRITES[direction][frame]
    sprite = build_sprite(pattern, RABBIT_PALETTE, scale=3)
    _cache[key] = sprite
    return sprite


# ============== NPC ==============
NPC_PATTERNS = {
    "down": [
        "..KKKK..",
        ".KHHHHK.",
        "KHSSSSHK",
        ".KSSSSK.",
        "..BBBB..",
        ".BBBBBB.",
        ".BBBBBB.",
        ".B.BB.B.",
        ".K.KK.K.",
        "..K..K..",
    ],
}
NPC_SKIN = (240, 200, 170)
NPC_HAIR = (60, 40, 30)

def get_npc_sprite(shirt_color, direction="down"):
    key = (shirt_color, direction)
    if key in _cache:
        return _cache[key]
    palette = {"K": (25, 20, 35), "H": NPC_HAIR, "S": NPC_SKIN, "B": shirt_color}
    pattern = NPC_PATTERNS.get(direction, NPC_PATTERNS["down"])
    sprite = build_sprite(pattern, palette, scale=3)
    _cache[key] = sprite
    return sprite
