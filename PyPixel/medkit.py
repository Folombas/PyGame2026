"""Аптечка — восстанавливает HP при подборе."""
import pygame


# Матрица спрайта: '.' — прозрачный, 'W' — белая коробка, 'R' — красный крест,
# 'K' — тёмный контур
MEDKIT_SPRITE = [
    ".KKKKKK.",
    "KRRWWRRK",
    "KRRWWRRK",
    "KRWWWWRK",
    "KRWWWWRK",
    "KRRWWRRK",
    "KRRWWRRK",
    ".KKKKKK.",
]

PALETTE = {
    "K": (110, 20, 30),      # тёмно-красный контур
    "W": (250, 250, 250),    # белый крест
    "R": (220, 50, 60),      # красная коробка
}

SCALE = 4
HEAL_AMOUNT = 30


class Medkit:
    _cached_sprite = None

    @classmethod
    def _get_sprite(cls):
        if cls._cached_sprite is not None:
            return cls._cached_sprite
        h = len(MEDKIT_SPRITE)
        w = len(MEDKIT_SPRITE[0])
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y, row in enumerate(MEDKIT_SPRITE):
            for x, ch in enumerate(row):
                color = PALETTE.get(ch)
                if color is not None:
                    surf.set_at((x, y), color)
        cls._cached_sprite = pygame.transform.scale(surf, (w * SCALE, h * SCALE))
        return cls._cached_sprite

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 8 * SCALE, 8 * SCALE)
        self.alive = True

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.alive:
            return
        sprite = self._get_sprite()
        r = sprite.get_rect()
        r.topleft = (self.rect.x - offset_x, self.rect.y - offset_y)
        surface.blit(sprite, r)
