"""Стрелы."""
import math
import pygame
from blocks import TILE_SIZE, AIR


ARROW_SPRITE = [
    "..SSS.",
    ".SSSS.",
    "SSSSS.",
    ".SSS..",
    "..F...",
    "..F...",
]
ARROW_PALETTE = {"S": (220, 230, 240), "F": (240, 200, 80)}
ARROW_SCALE = 3

_cache = {}

def _build_base():
    h = len(ARROW_SPRITE); w = len(ARROW_SPRITE[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(ARROW_SPRITE):
        for x, ch in enumerate(row):
            c = ARROW_PALETTE.get(ch)
            if c: surf.set_at((x, y), c)
    return pygame.transform.scale(surf, (w * ARROW_SCALE, h * ARROW_SCALE))

def get_arrow_sprite(angle_deg):
    key = int(angle_deg / 15) * 15
    if key in _cache: return _cache[key]
    sprite = pygame.transform.rotate(_build_base(), key)
    _cache[key] = sprite
    return sprite


class Arrow:
    def __init__(self, x, y, vx, vy, damage=2):
        self.x = float(x); self.y = float(y)
        self.vx = vx; self.vy = vy
        self.alive = True
        self.damage = damage
        self.lifetime = 200
        self.angle = math.degrees(math.atan2(-vy, vx)) - 90

    def update(self, world, enemies):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            return None
        tx = int(self.x) // TILE_SIZE
        ty = int(self.y) // TILE_SIZE
        if world.get_block(tx, ty) != AIR:
            self.alive = False
            return None
        for e in enemies:
            if not e.alive:
                continue
            if e.rect.collidepoint(self.x, self.y):
                self.alive = False
                return e
        return None

    def draw(self, surface, offset_x, offset_y):
        if not self.alive:
            return
        sprite = get_arrow_sprite(self.angle)
        r = sprite.get_rect(center=(int(self.x) - offset_x, int(self.y) - offset_y))
        surface.blit(sprite, r)
