"""Платформа: трава сверху, земля снизу."""
import pygame
from biomes import get_biome_color


class Platform:
    def __init__(self, x, y, w, h=20):
        self.rect = pygame.Rect(x, y, w, h)
        biome = get_biome_color(y + h // 2)
        self.color_top = biome["platform_top"]
        self.color_body = biome["platform_body"]
        self.color_edge = biome["platform_edge"]

    def draw(self, surface, offset_x=0, offset_y=0):
        r = self.rect.move(-offset_x, -offset_y)

        # не рисуем если вне экрана (оптимизация)
        if r.right < 0 or r.left > surface.get_width():
            return
        if r.bottom < 0 or r.top > surface.get_height():
            return

        # тело платформы (земля)
        pygame.draw.rect(surface, self.color_body, r)

        # травяная кромка сверху (5 px)
        grass_h = min(5, r.h)
        grass = pygame.Rect(r.x, r.y, r.w, grass_h)
        pygame.draw.rect(surface, self.color_top, grass)

        # тёмная линия между травой и землёй
        if r.h > grass_h:
            line = pygame.Rect(r.x, r.y + grass_h, r.w, 2)
            pygame.draw.rect(surface, self.color_edge, line)

        # контур снизу
        pygame.draw.rect(surface, self.color_edge, (r.x, r.bottom - 2, r.w, 2))

        # крапинки в земле для текстуры
        if r.h >= 20 and r.w >= 40:
            step = 24
            for xx in range(r.x + 8, r.right - 8, step):
                for yy in range(r.y + grass_h + 6, r.bottom - 6, 8):
                    darker = tuple(max(0, c - 25) for c in self.color_body)
                    pygame.draw.rect(surface, darker, (xx, yy, 3, 3))
