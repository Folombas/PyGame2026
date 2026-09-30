"""Бесконечная камера — без ограничений мира."""
from settings import HEIGHT


class Camera:
    def __init__(self, view_width):
        self.view_width = view_width
        self.view_height = HEIGHT
        self.offset_x = 0.0
        self.offset_y = 0.0
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

        # --- Y ---
        target_y = target_rect.centery - self.view_height / 2
        diff_y = target_y - self.offset_y
        if abs(diff_y) > self.dead_zone_y:
            if diff_y > 0:
                target_y = self.offset_y + diff_y - self.dead_zone_y
            else:
                target_y = self.offset_y + diff_y + self.dead_zone_y
        self.offset_y += (target_y - self.offset_y) * 0.12

    @property
    def ox(self):
        return int(self.offset_x)

    @property
    def oy(self):
        return int(self.offset_y)
