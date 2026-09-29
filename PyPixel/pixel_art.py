"""Программный пиксель-арт: строим спрайты из текстовых матриц.

Символ в матрице = пиксель:
  '.' — прозрачный
  остальные — смотрятся в палитре
"""
import pygame


# ---------- ПАЛИТРЫ ----------
PLAYER_PALETTE = {
    "G": (120, 200, 120),   # тело
    "B": (30, 30, 40),      # глаза
}

ENEMY_PALETTE = {
    "R": (230, 90, 90),
    "B": (30, 30, 40),
}


# ---------- ИГРОК (8x8, scale 4 = 32x32) ----------
PLAYER_IDLE = [
    "..GGGG..",
    ".GGGGGG.",
    "G.B..B.G",
    "GGGGGGGG",
    "GGGGGGGG",
    ".G.GG.G.",
    ".G....G.",
    ".G....G.",
]

PLAYER_WALK_1 = [
    "..GGGG..",
    ".GGGGGG.",
    "G.B..B.G",
    "GGGGGGGG",
    "GGGGGGGG",
    ".G.GG.G.",
    "G......G",
    ".G....G.",
]

PLAYER_WALK_2 = [
    "..GGGG..",
    ".GGGGGG.",
    "G.B..B.G",
    "GGGGGGGG",
    "GGGGGGGG",
    ".G.GG.G.",
    ".G....G.",
    "G......G",
]

PLAYER_JUMP = [
    "..GGGG..",
    ".GGGGGG.",
    "G.B..B.G",
    "GGGGGGGG",
    "GGGGGGGG",
    "G.GGGG.G",
    "..G..G..",
    "........",
]

PLAYER_SPRITES = {
    "idle":   PLAYER_IDLE,
    "walk_1": PLAYER_WALK_1,
    "walk_2": PLAYER_WALK_2,
    "jump":   PLAYER_JUMP,
}


# ---------- ВРАГ (7x7, scale 4 = 28x28) ----------
ENEMY_WALK_1 = [
    ".RRRRR.",
    "RRRRRRR",
    "R.B.B.R",
    "RRRRRRR",
    "R.R.R.R",
    ".RRRRR.",
    ".......",
]

ENEMY_WALK_2 = [
    ".RRRRR.",
    "RRRRRRR",
    "R.B.B.R",
    "RRRRRRR",
    ".R.R.R.",
    "R.....R",
    ".......",
]

ENEMY_SPRITES = {
    "walk_1": ENEMY_WALK_1,
    "walk_2": ENEMY_WALK_2,
}


# ---------- ФУНКЦИЯ СБОРКИ ----------
def build_sprite(pattern, palette, scale=4, flip_x=False):
    """Превращает матрицу символов в pygame.Surface нужного размера."""
    h = len(pattern)
    w = len(pattern[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color is not None:
                surf.set_at((x, y), color)
    if flip_x:
        surf = pygame.transform.flip(surf, True, False)
    return pygame.transform.scale(surf, (w * scale, h * scale))
