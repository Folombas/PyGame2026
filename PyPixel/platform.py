"""Платформа — статичный прямоугольник, с которым сталкивается игрок."""
import pygame
from biomes import get_biome_color


class Platform:
    def __init__(self, x: int, y: int, w: int, h: int = 20):
        self.rect = pygame.Rect(x, y, w, h)
        biome = get_biome_color(y + h // 2)
        self.color = biome["platform"]
        self.accent = biome["accent"]

    def draw(self, surface, offset_x=0, offset_y=0):
        r = self.rect.move(-offset_x, -offset_y)
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, self.accent, (r.x, r.y, r.w, 3))
