"""Платформа — статичный прямоугольник, с которым сталкивается игрок."""
import pygame
from settings import PLATFORM_COLOR


class Platform:
    def __init__(self, x: int, y: int, w: int, h: int = 20):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PLATFORM_COLOR, self.rect)
        # тонкая подсветка сверху — чтобы визуально читалось
        pygame.draw.rect(
            surface, (140, 120, 170),
            (self.rect.x, self.rect.y, self.rect.w, 3)
        )
