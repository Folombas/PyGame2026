"""Камера, следующая за игроком."""
import pygame


class Camera:
    def __init__(self, view_width: int, world_width: int):
        self.offset_x = 0.0
        self.view_width = view_width
        self.world_width = world_width
        # «Мёртвая зона» — где игрок может ходить, не двигая камеру
        self.dead_zone = 120

    def update(self, target_rect: pygame.Rect) -> None:
        # Куда камера хотела бы смотреть
        # Хотим, чтобы игрок был в центре мёртвой зоны
        target_center = target_rect.centerx - self.view_width / 2

        # Если игрок вышел за пределы мёртвой зоны — двигаем
        diff = target_center - self.offset_x
        if abs(diff) > self.dead_zone:
            # мягкое следование
            if diff > 0:
                target_center = self.offset_x + diff - self.dead_zone
            else:
                target_center = self.offset_x + diff + self.dead_zone

        # Плавная интерполяция
        self.offset_x += (target_center - self.offset_x) * 0.15

        # Ограничения мира
        self.offset_x = max(0, min(self.offset_x, self.world_width - self.view_width))

    @property
    def ox(self) -> int:
        """Целочисленный сдвиг для отрисовки (без джиттера)."""
        return int(self.offset_x)

