"""Блок платформы/земли."""
import pygame
from blocks import AIR, STONE, draw_block, draw_dig_progress


class Platform:
    def __init__(self, x, y, w, h=20, block_type=STONE):
        self.rect = pygame.Rect(x, y, w, h)
        self.block_type = block_type

    def draw(self, surface, offset_x=0, offset_y=0):
        r = self.rect
        if r.right - offset_x < 0 or r.left - offset_x > surface.get_width():
            return
        if r.bottom - offset_y < 0 or r.top - offset_y > surface.get_height():
            return
        draw_block(surface, r, self.block_type, (offset_x, offset_y))
