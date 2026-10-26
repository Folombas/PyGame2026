import pygame
from settings import CELL, COLORS

class BlockRenderer:
    def __init__(self):
        self.sprites = {}
        for kind, color in COLORS.items():
            surf = pygame.Surface((CELL - 2, CELL - 2), pygame.SRCALPHA)
            # Градиент (сверху темнее, снизу светлее)
            for y in range(CELL - 2):
                t = y / max(1, CELL - 3)
                r = int(color[0] * (0.5 + 0.5 * t))
                g = int(color[1] * (0.5 + 0.5 * t))
                b = int(color[2] * (0.5 + 0.5 * t))
                pygame.draw.line(surf, (r, g, b), (0, y), (CELL - 2, y))
            
            # Внутренний блик (эффект стекла)
            pygame.draw.rect(surf, (255, 255, 255, 120), (2, 2, CELL - 6, CELL - 6), 1, border_radius=3)
            # Внешняя неоновая рамка
            pygame.draw.rect(surf, (255, 255, 255, 220), (0, 0, CELL - 2, CELL - 2), 1, border_radius=4)
            self.sprites[kind] = surf

    def draw_block(self, surf, x, y, kind, glow=0.0):
        sprite = self.sprites.get(kind)
        if sprite:
            surf.blit(sprite, (x + 1, y + 1))
        else:
            color = COLORS.get(kind, (255, 255, 255))
            rect = pygame.Rect(x + 1, y + 1, CELL - 2, CELL - 2)
            pygame.draw.rect(surf, color, rect, border_radius=4)
