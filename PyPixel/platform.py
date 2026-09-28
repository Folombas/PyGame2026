"""Платформа — статичный прямоугольник, с которым сталкивается игрок."""
import pygame
from settings import PLATFORM_COLOR


class Platform:
    def __init__(self, x: int, y: int, w: int, h: int = 20):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface: pygame.Surface, offset_x: int = 0) -> None:
        r = self.rect.move(-offset_x, 0)
        pygame.draw.rect(surface, PLATFORM_COLOR, r)
        pygame.draw.rect(
            surface, (140, 120, 170),
            (r.x, r.y, r.w, 3)
        )
