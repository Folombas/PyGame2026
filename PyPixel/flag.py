"""Флаг — цель уровня."""
import pygame
from settings import FLAG_COLOR, FLAG_POLE_COLOR


class Flag:
    def __init__(self, x: int, y: int, pole_h: int = 120):
        self.base_x = x
        self.base_y = y
        self.pole_h = pole_h
        # зона касания — прямоугольник вокруг шеста
        self.rect = pygame.Rect(x - 4, y - pole_h, 32, pole_h)
        self.flag_offset = 0.0   # 0 = сверху, 1 = внизу
        self.lowered = False

    def lower(self) -> None:
        self.lowered = True

    def animate(self, dt: float) -> None:
        if self.lowered and self.flag_offset < 1.0:
            self.flag_offset = min(1.0, self.flag_offset + 1.6 * dt)

    def draw(self, surface, offset_x=0, offset_y=0):
        x = self.base_x - offset_x
        yy = self.base_y - offset_y
        # шест
        pygame.draw.rect(
            surface, FLAG_POLE_COLOR,
            (x + 10, yy - self.pole_h, 4, self.pole_h)
        )
        # шарик наверху
        pygame.draw.rect(surface, FLAG_POLE_COLOR, (x + 6, yy - self.pole_h - 6, 12, 6))

        # флажок — треугольник, опускается по мере animate()
        travel = max(0, self.pole_h - 36)
        flag_top = yy - self.pole_h + 12 + self.flag_offset * travel
        pygame.draw.polygon(surface, FLAG_COLOR, [
            (x + 14, flag_top),
            (x + 44, flag_top + 11),
            (x + 14, flag_top + 22),
        ])
