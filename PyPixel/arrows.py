"""Стрелы — летят по направлению к курсору, ранят врагов."""
import math
import pygame

ARROW_SPRITE = [
    "..SSS.",
    ".SSSS.",
    "SSSSS.",
    ".SSS..",
    "..F...",
    "..F...",
]

ARROW_PALETTE = {
    "S": (220, 230, 240),   # серебристый наконечник
    "F": (240, 200, 80),    # золотое оперение
}

ARROW_SCALE = 3
ARROW_SIZE = 6 * ARROW_SCALE  # 18

_cache = {}


def _build_base():
    h = len(ARROW_SPRITE)
    w = len(ARROW_SPRITE[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(ARROW_SPRITE):
        for x, ch in enumerate(row):
            col = ARROW_PALETTE.get(ch)
            if col is not None:
                surf.set_at((x, y), col)
    return pygame.transform.scale(surf, (w * ARROW_SCALE, h * ARROW_SCALE))


def get_arrow_sprite(angle_deg):
    """Кешируем по углу, округлённому до 15°."""
    key = int(angle_deg / 15) * 15
    if key in _cache:
        return _cache[key]
    sprite = pygame.transform.rotate(_build_base(), key)
    _cache[key] = sprite
    return sprite


class Arrow:
    def __init__(self, x, y, vx, vy, damage=2):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.alive = True
        self.damage = damage
        self.lifetime = 200
        # угол спрайта — вверх по умолчанию, поэтому -90
        self.angle = math.degrees(math.atan2(-vy, vx)) - 90

    def update(self, platforms, enemies):
        """Возвращает врага при попадании, иначе None."""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12      # гравитация
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            return None

        # стены
        for p in platforms:
            if p.rect.collidepoint(self.x, self.y):
                self.alive = False
                return None

        # враги
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
