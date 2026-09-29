"""Яблоня с яблоками, которые можно собирать. Пиксель-арт."""
import pygame


# ---------- Спрайт дерева (матрица символов) ----------
# '.' — прозрачный, 'K' — контур ствола, 'T' — ствол, 'C' — крона,
# 'D' — тёмная крона, 'L' — светлая крона
TREE_SPRITE = [
    "....DDDDDDDDDDDD....",
    "..DDCCCCCCCCCCCCDD..",
    ".DCCCCCCCCCCCCCCCCD.",
    "DCCCCCCCCCCCCCCCCCCD",
    "DCCLLCCCCCCCCLLCCCCD",
    "DCCCCCCCCCCCCCCCCCCD",
    "DCCCCCCCCCCCCCCCCCCD",
    ".DCCCCCCCCCCCCCCCCD.",
    "..DDCCCCCCCCCCCCDD..",
    "....DDDDCCCCDDDD....",
    ".........TT.........",
    ".........TT.........",
    ".........TT.........",
    ".........TT.........",
    ".........TT.........",
    "........KTTK........",
]

PALETTE = {
    "T": (110, 70, 40),      # ствол
    "K": (75, 45, 25),       # тёмный ствол
    "C": (65, 150, 75),      # крона
    "D": (40, 100, 50),      # тёмная крона (контур)
    "L": (105, 190, 105),    # светлый блик
}

SCALE = 8
APPLE_RADIUS = 9


class AppleTree:
    # Относительно (base_x, base_y) — базовая точка внизу ствола
    DEFAULT_APPLES = [
        (-52, -95),
        (-30, -118),
        (-8,  -100),
        (14,  -118),
        (36,  -95),
        (55,  -115),
        (0,   -140),
    ]

    _cached_sprite = None

    @classmethod
    def _get_sprite(cls):
        if cls._cached_sprite is not None:
            return cls._cached_sprite
        h = len(TREE_SPRITE)
        w = len(TREE_SPRITE[0])
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y, row in enumerate(TREE_SPRITE):
            for x, ch in enumerate(row):
                color = PALETTE.get(ch)
                if color is not None:
                    surf.set_at((x, y), color)
        cls._cached_sprite = pygame.transform.scale(surf, (w * SCALE, h * SCALE))
        return cls._cached_sprite

    def __init__(self, base_x, base_y):
        self.base_x = base_x
        self.base_y = base_y
        self.apples = [(ax, ay, False) for ax, ay in self.DEFAULT_APPLES]

    def apple_world_rects(self):
        result = []
        for i, (ax, ay, collected) in enumerate(self.apples):
            if not collected:
                r = pygame.Rect(
                    self.base_x + ax - APPLE_RADIUS,
                    self.base_y + ay - APPLE_RADIUS,
                    APPLE_RADIUS * 2,
                    APPLE_RADIUS * 2,
                )
                result.append((i, r))
        return result

    def collect(self, index):
        ax, ay, _ = self.apples[index]
        self.apples[index] = (ax, ay, True)

    def draw(self, surface, offset_x=0):
        sprite = self._get_sprite()
        r = sprite.get_rect()
        r.midbottom = (self.base_x - offset_x, self.base_y)
        surface.blit(sprite, r)

        # яблоки — поверх спрайта
        for ax, ay, collected in self.apples:
            if collected:
                continue
            apx = self.base_x + ax - offset_x
            apy = self.base_y + ay
            # тень / контур
            pygame.draw.circle(surface, (140, 30, 40), (apx, apy), APPLE_RADIUS)
            # тело
            pygame.draw.circle(surface, (220, 50, 60), (apx, apy), APPLE_RADIUS - 1)
            # блик
            pygame.draw.rect(surface, (255, 180, 180), (apx - 3, apy - 3, 2, 2))
            # листик
            pygame.draw.rect(surface, (100, 200, 100), (apx + 2, apy - APPLE_RADIUS - 2, 3, 3))
