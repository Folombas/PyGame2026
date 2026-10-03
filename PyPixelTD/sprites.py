"""Программные спрайты для top-down."""
import pygame


# Игрок — 10x14 в 4 направлениях, 2 кадра анимации
PLAYER_DOWN_1 = [
    "..KKKK..",
    ".KHHHHK.",
    "KHSSSSHK",
    "KHSSSSHK",
    ".KSSSSK.",
    "..BBBB..",
    ".BBBBBB.",
    ".BBBBBB.",
    ".B.BB.B.",
    ".B.BB.B.",
    ".B.BB.B.",
    ".K.KK.K.",
    ".K.KK.K.",
    "..K..K..",
]
PLAYER_DOWN_2 = [
    "..KKKK..",
    ".KHHHHK.",
    "KHSSSSHK",
    "KHSSSSHK",
    ".KSSSSK.",
    "..BBBB..",
    ".BBBBBB.",
    ".BBBBBB.",
    ".B.BB.B.",
    "B..BB..B",
    "B..BB..B",
    ".K.KK.K.",
    "..K..K..",
    "........",
]
PLAYER_UP_1 = [
    "..KKKK..",
    ".KHHHHK.",
    "KHHHHHHK",
    "KHHHHHHK",
    ".KHHHHK.",
    "..BBBB..",
    ".BBBBBB.",
    ".BBBBBB.",
    ".B.BB.B.",
    ".B.BB.B.",
    ".B.BB.B.",
    ".K.KK.K.",
    ".K.KK.K.",
    "..K..K..",
]
PLAYER_UP_2 = [
    "..KKKK..",
    ".KHHHHK.",
    "KHHHHHHK",
    "KHHHHHHK",
    ".KHHHHK.",
    "..BBBB..",
    ".BBBBBB.",
    ".BBBBBB.",
    ".B.BB.B.",
    "B..BB..B",
    "B..BB..B",
    ".K.KK.K.",
    "..K..K..",
    "........",
]
PLAYER_LEFT_1 = [
    "..KKK...",
    ".KHHHK..",
    "KHSSSHK.",
    "KHSSSHK.",
    ".KSSSK..",
    "..BBB...",
    ".BBBB...",
    ".BBBB...",
    ".BB.B...",
    ".BB.B...",
    ".B..B...",
    ".K..K...",
    "K...K...",
    "K...K...",
]
PLAYER_LEFT_2 = [
    "..KKK...",
    ".KHHHK..",
    "KHSSSHK.",
    "KHSSSHK.",
    ".KSSSK..",
    "..BBB...",
    ".BBBB...",
    ".BBBB...",
    ".BB.B...",
    "B...B...",
    "B...B...",
    ".K..K...",
    "K...K...",
    "........",
]
PLAYER_RIGHT_1 = [
    "...KKK..",
    "..KHHHK.",
    ".KHSSSHK",
    ".KHSSSHK",
    "..KSSSK.",
    "...BBB..",
    "...BBBB.",
    "...BBBB.",
    "...B.BB.",
    "...B.BB.",
    "...B..B.",
    "...K..K.",
    "...K...K",
    "...K...K",
]
PLAYER_RIGHT_2 = [
    "...KKK..",
    "..KHHHK.",
    ".KHSSSHK",
    ".KHSSSHK",
    "..KSSSK.",
    "...BBB..",
    "...BBBB.",
    "...BBBB.",
    "...B.BB.",
    "...B...B",
    "...B...B",
    "...K..K.",
    "...K...K",
    "........",
]

# K=контур, H=волосы, S=кожа, B=тело(синий)
PLAYER_PALETTE = {
    "K": (25, 20, 35),
    "H": (100, 60, 40),
    "S": (240, 200, 170),
    "B": (70, 120, 200),
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


PLAYER_SPRITES = {
    "down":  [PLAYER_DOWN_1, PLAYER_DOWN_2],
    "up":    [PLAYER_UP_1, PLAYER_UP_2],
    "left":  [PLAYER_LEFT_1, PLAYER_LEFT_2],
    "right": [PLAYER_RIGHT_1, PLAYER_RIGHT_2],
}

# Собираем кеш
_sprite_cache = {}
def get_player_sprite(direction, frame):
    key = (direction, frame)
    if key in _sprite_cache:
        return _sprite_cache[key]
    pattern = PLAYER_SPRITES[direction][frame]
    sprite = build_sprite(pattern, PLAYER_PALETTE, scale=2)
    _sprite_cache[key] = sprite
    return sprite


# NPC — простой человечек
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
    "up": [
        "..KKKK..",
        ".KHHHHK.",
        "KHHHHHHK",
        ".KHHHHK.",
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
    if key in _sprite_cache:
        return _sprite_cache[key]
    palette = {
        "K": (25, 20, 35),
        "H": NPC_HAIR,
        "S": NPC_SKIN,
        "B": shirt_color,
    }
    pattern = NPC_PATTERNS.get(direction, NPC_PATTERNS["down"])
    sprite = build_sprite(pattern, palette, scale=2)
    _sprite_cache[key] = sprite
    return sprite
