"""Камера, следующая за игроком по X и Y."""
import pygame
from settings import HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, SURFACE_Y


class Camera:
    def __init__(self, view_width, world_width):
        self.view_width = view_width
        self.view_height = HEIGHT
        self.world_width = world_width
        self.world_height = WORLD_HEIGHT
        # Стартуем камеру так, чтобы центр смотрел на уровень земли
        self.offset_x = 0.0
        self.offset_y = float(SURFACE_Y - self.view_height // 2)
        self.dead_zone_x = 120
        self.dead_zone_y = 80

    def update(self, target_rect):
        # --- X ---
        target_x = target_rect.centerx - self.view_width / 2
        diff_x = target_x - self.offset_x
        if abs(diff_x) > self.dead_zone_x:
            if diff_x > 0:
                target_x = self.offset_x + diff_x - self.dead_zone_x
            else:
                target_x = self.offset_x + diff_x + self.dead_zone_x
        self.offset_x += (target_x - self.offset_x) * 0.15
        self.offset_x = max(0, min(self.offset_x, self.world_width - self.view_width))

        # --- Y ---
        target_y = target_rect.centery - self.view_height / 2
        diff_y = target_y - self.offset_y
        if abs(diff_y) > self.dead_zone_y:
            if diff_y > 0:
                target_y = self.offset_y + diff_y - self.dead_zone_y
            else:
                target_y = self.offset_y + diff_y + self.dead_zone_y
        self.offset_y += (target_y - self.offset_y) * 0.12
        self.offset_y = max(0, min(self.offset_y, self.world_height - self.view_height))

    @property
    def ox(self):
        return int(self.offset_x)

    @property
    def oy(self):
        return int(self.offset_y)
