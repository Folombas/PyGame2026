"""Пиксель — собираемый предмет, +1 очко."""
import pygame
from settings import PIXEL_COLOR


class Pixel:
    def __init__(self, x: int, y: int, size: int = 14):
        self.rect = pygame.Rect(x, y, size, size)
        self.alive = True

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.alive:
            return
        r = self.rect.move(-offset_x, -offset_y)
        # чуть побольше для «свечения»
        glow = r.inflate(4, 4)
        pygame.draw.rect(surface, (120, 100, 40), glow)
        pygame.draw.rect(surface, PIXEL_COLOR, r)
