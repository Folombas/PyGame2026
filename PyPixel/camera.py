"""Бесконечная камера без границ."""
from settings import HEIGHT


class Camera:
    def __init__(self, view_width):
        self.view_width = view_width
        self.view_height = HEIGHT
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.dead_zone_x = 100
        self.dead_zone_y = 60

    def update(self, target_rect):
        # X
        tx = target_rect.centerx - self.view_width / 2
        dx = tx - self.offset_x
        if abs(dx) > self.dead_zone_x:
            if dx > 0:
                tx = self.offset_x + dx - self.dead_zone_x
            else:
                tx = self.offset_x + dx + self.dead_zone_x
        self.offset_x += (tx - self.offset_x) * 0.15

        # Y
        ty = target_rect.centery - self.view_height / 2
        dy = ty - self.offset_y
        if abs(dy) > self.dead_zone_y:
            if dy > 0:
                ty = self.offset_y + dy - self.dead_zone_y
            else:
                ty = self.offset_y + dy + self.dead_zone_y
        self.offset_y += (ty - self.offset_y) * 0.12

    @property
    def ox(self): return int(self.offset_x)

    @property
    def oy(self): return int(self.offset_y)
