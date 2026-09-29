"""Яблоня с яблоками, которые можно собирать."""
import pygame


class AppleTree:
    TRUNK_COLOR = (110, 70, 40)
    TRUNK_DARK = (75, 45, 25)
    CROWN_DARK = (40, 100, 50)
    CROWN_MAIN = (65, 150, 75)
    CROWN_LIGHT = (105, 190, 105)
    APPLE_COLOR = (220, 50, 60)
    APPLE_SHINE = (255, 150, 150)
    LEAF_COLOR = (100, 200, 100)

    # (offset_x, offset_y) относительно основания ствола.
    # отрицательный offset_y = выше земли
    DEFAULT_APPLES = [
        (-35, -75),
        (-50, -95),
        (-25, -110),
        (5, -115),
        (30, -110),
        (48, -95),
        (25, -75),
    ]

    def __init__(self, base_x, base_y):
        self.base_x = base_x
        self.base_y = base_y
        self.apples = [(ax, ay, False) for ax, ay in self.DEFAULT_APPLES]

    def apple_world_rects(self):
        """Список (index, world_rect) для несобранных яблок."""
        result = []
        for i, (ax, ay, collected) in enumerate(self.apples):
            if not collected:
                r = pygame.Rect(
                    self.base_x + ax - 6,
                    self.base_y + ay - 6,
                    12, 12
                )
                result.append((i, r))
        return result

    def collect(self, index):
        ax, ay, _ = self.apples[index]
        self.apples[index] = (ax, ay, True)

    def draw(self, surface, offset_x=0):
        x = self.base_x - offset_x
        y = self.base_y

        # ствол
        pygame.draw.rect(surface, self.TRUNK_COLOR, (x - 7, y - 55, 14, 55))
        pygame.draw.rect(surface, self.TRUNK_DARK, (x + 1, y - 55, 6, 55))

        # ветки
        pygame.draw.rect(surface, self.TRUNK_COLOR, (x - 22, y - 75, 22, 6))
        pygame.draw.rect(surface, self.TRUNK_COLOR, (x, y - 88, 22, 6))

        # крона — задний тёмный слой
        crown_cx = x
        crown_cy = y - 95
        pygame.draw.circle(surface, self.CROWN_DARK, (crown_cx - 22, crown_cy + 4), 28)
        pygame.draw.circle(surface, self.CROWN_DARK, (crown_cx + 22, crown_cy + 4), 28)
        pygame.draw.circle(surface, self.CROWN_DARK, (crown_cx, crown_cy - 14), 31)

        # основной слой
        pygame.draw.circle(surface, self.CROWN_MAIN, (crown_cx - 20, crown_cy), 25)
        pygame.draw.circle(surface, self.CROWN_MAIN, (crown_cx + 20, crown_cy), 25)
        pygame.draw.circle(surface, self.CROWN_MAIN, (crown_cx, crown_cy - 16), 27)

        # светлые блики
        pygame.draw.circle(surface, self.CROWN_LIGHT, (crown_cx - 15, crown_cy - 22), 9)
        pygame.draw.circle(surface, self.CROWN_LIGHT, (crown_cx + 17, crown_cy - 10), 7)

        # яблоки
        for ax, ay, collected in self.apples:
            if collected:
                continue
            apx = x + ax
            apy = y + ay
            pygame.draw.circle(surface, self.APPLE_COLOR, (apx, apy), 5)
            pygame.draw.rect(surface, self.APPLE_SHINE, (apx - 2, apy - 2, 2, 2))
            pygame.draw.rect(surface, self.LEAF_COLOR, (apx, apy - 8, 3, 3))
