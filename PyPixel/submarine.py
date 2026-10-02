"""Батискаф — подводный транспорт с фонарём, светит вокруг."""
import math
import pygame


class Submarine:
    W, H = 80, 44

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.W, self.H)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.bob_timer = 0.0
        self.has_pilot = False

    def update(self, world, keys=None):
        self.bob_timer += 0.05
        if self.has_pilot and keys:
            ax = 0
            ay = 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:   ax -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  ax += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]:     ay -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:   ay += 1
            # ускорение
            self.vel_x += ax * 0.35
            self.vel_y += ay * 0.35
            self.vel_x = max(-4.5, min(4.5, self.vel_x))
            self.vel_y = max(-4.0, min(4.0, self.vel_y))
        else:
            # свободно дрейфует
            self.vel_x *= 0.95
            self.vel_y *= 0.95

        # сопротивление воды
        self.vel_x *= 0.92
        self.vel_y *= 0.92

        # движение с проверкой воды
        nx = self.rect.x + int(self.vel_x)
        ny = self.rect.y + int(self.vel_y)
        tx = (nx + self.rect.w // 2) // 32
        ty = (ny + self.rect.h // 2) // 32
        from blocks import WATER
        if world.get_block(tx, ty) == WATER:
            self.rect.x = nx
            self.rect.y = ny
        else:
            self.vel_x = -self.vel_x * 0.3
            self.vel_y = -self.vel_y * 0.3

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        bob = int(math.sin(self.bob_timer) * 2)
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y + bob
        w, h = self.W, self.H

        # главный корпус — овал
        pygame.draw.ellipse(surface, (200, 180, 60), (x + 4, y + 6, w - 8, h - 12))
        pygame.draw.ellipse(surface, (140, 120, 40), (x + 4, y + 6, w - 8, h - 12), 2)

        # верхняя башня
        pygame.draw.ellipse(surface, (220, 200, 80), (x + w // 2 - 14, y - 4, 28, 16))
        pygame.draw.ellipse(surface, (140, 120, 40), (x + w // 2 - 14, y - 4, 28, 16), 2)
        # перископ
        pygame.draw.rect(surface, (60, 60, 70), (x + w // 2 - 2, y - 16, 4, 14))
        pygame.draw.rect(surface, (60, 60, 70), (x + w // 2 - 2, y - 18, 12, 4))

        # носовой прожектор
        pygame.draw.circle(surface, (255, 240, 150), (x + w - 6, y + h // 2), 6)
        pygame.draw.circle(surface, (255, 200, 60), (x + w - 6, y + h // 2), 6, 2)

        # иллюминаторы
        for i in range(3):
            cx = x + 20 + i * 16
            cy = y + h // 2
            pygame.draw.circle(surface, (30, 60, 100), (cx, cy), 6)
            pygame.draw.circle(surface, (100, 180, 240), (cx, cy), 6, 2)
            # отблеск
            pygame.draw.arc(surface, (200, 230, 255), (cx - 4, cy - 4, 8, 8),
                            math.pi, math.pi * 2, 2)

        # винт сзади
        blade_t = math.sin(self.bob_timer * 8) * 8
        pygame.draw.ellipse(surface, (100, 100, 110),
                            (x - 8, y + h // 2 - 6 + blade_t, 8, 12))
        # киль
        pygame.draw.rect(surface, (140, 120, 40), (x + 6, y + h - 6, w - 12, 4))

    def get_light(self):
        """Возвращает позицию прожектора для освещения."""
        return (self.rect.right, self.rect.centery, 300)


def _make_pilot(self, player):
    """Посадить игрока в батискаф."""
    self.has_pilot = True
    player.in_submarine = self


def _eject_pilot(self, player):
    """Высадить игрока."""
    self.has_pilot = False
    player.in_submarine = None
    # выкидываем игрока наверх
    player.rect.midbottom = (self.rect.centerx, self.rect.top - 4)


Submarine.set_pilot = _make_pilot
Submarine.eject = _eject_pilot
