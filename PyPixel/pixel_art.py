"""Программный пиксель-арт: строим спрайты из текстовых матриц.

Символы:
  '.' — прозрачный
  'K' — контур (тёмный)
  'G' — тело игрока
  'R' — тело врага
  'B' — зрачок глаза
"""
import pygame


# ---------- ПАЛИТРЫ ----------
PLAYER_PALETTE = {
    "G": (120, 200, 120),   # тело
    "B": (30, 30, 40),      # зрачки
    "K": (40, 80, 50),      # контур (тёмно-зелёный)
}

ENEMY_PALETTE = {
    "R": (230, 90, 90),
    "B": (30, 30, 40),
    "K": (110, 40, 45),     # контур (тёмно-красный)
}


# ---------- ИГРОК (10x10, scale=3 = 30x30) ----------
PLAYER_IDLE = [
    "..KKKKKK..",
    ".KGGGGGGK.",
    "KGGGGGGGGK",
    "KG.BB.BBGK",
    "KGGGGGGGGK",
    ".KGGGGGGK.",
    "..KKKKKK..",
    "..KGGGGK..",
    "..KG..GK..",
    "..KK..KK..",
]

PLAYER_WALK_1 = [
    "..KKKKKK..",
    ".KGGGGGGK.",
    "KGGGGGGGGK",
    "KG.BB.BBGK",
    "KGGGGGGGGK",
    ".KGGGGGGK.",
    "..KKKKKK..",
    "..KGGGGK..",
    ".KG....GK.",
    ".KK....KK.",
]

PLAYER_WALK_2 = [
    "..KKKKKK..",
    ".KGGGGGGK.",
    "KGGGGGGGGK",
    "KG.BB.BBGK",
    "KGGGGGGGGK",
    ".KGGGGGGK.",
    "..KKKKKK..",
    "..KGGGGK..",
    "..KG..GK..",
    "..KK..KK..",
]

PLAYER_JUMP = [
    "..KKKKKK..",
    ".KGGGGGGK.",
    "KGGGGGGGGK",
    "KG.BB.BBGK",
    "KGGGGGGGGK",
    "KKGGGGGGKK",
    "..KKKKKK..",
    "..KGGGGK..",
    ".KG....GK.",
    ".KK....KK.",
]

PLAYER_SPRITES = {
    "idle":   PLAYER_IDLE,
    "walk_1": PLAYER_WALK_1,
    "walk_2": PLAYER_WALK_2,
    "jump":   PLAYER_JUMP,
}


# ---------- ВРАГ (10x10, scale=3 = 30x30) ----------
ENEMY_WALK_1 = [
    ".KKKKKKKK.",
    "KRRRRRRRRK",
    "KR.BB.BBRK",
    "KRRRRRRRRK",
    "KRRKKKKRRK",
    "KRRRRRRRRK",
    ".KKKKKKKK.",
    "..KRRRRK..",
    ".KR....RK.",
    ".KK....KK.",
]

ENEMY_WALK_2 = [
    ".KKKKKKKK.",
    "KRRRRRRRRK",
    "KR.BB.BBRK",
    "KRRRRRRRRK",
    "KRRKKKKRRK",
    "KRRRRRRRRK",
    ".KKKKKKKK.",
    "..KRRRRK..",
    "..KR..RK..",
    "..KK..KK..",
]

ENEMY_SPRITES = {
    "walk_1": ENEMY_WALK_1,
    "walk_2": ENEMY_WALK_2,
}


# ---------- ФУНКЦИЯ СБОРКИ ----------
def build_sprite(pattern, palette, scale=3, flip_x=False):
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
