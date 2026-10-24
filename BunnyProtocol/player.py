"""Игрок — зайка-хакер."""
import pygame
import math
from settings import *


class Player:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.radius = PLAYER_RADIUS
        self.facing = 0.0  # угол в радианах
        self.running = False
        self.bob = 0.0
        self.keys_collected = 0

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def try_move(self, dx, dy, world):
        """Двигает с проверкой коллизий по осям."""
        # Проверка по X
        nx = self.x + dx
        if not self._collide(nx, self.y, world):
            self.x = nx
        # Проверка по Y
        ny = self.y + dy
        if not self._collide(self.x, ny, world):
            self.y = ny

    def _collide(self, x, y, world):
        r = self.radius
        # Проверяем 4 точки вокруг радиуса
        for px, py in [(x - r, y), (x + r, y), (x, y - r), (x, y + r)]:
            if world.is_blocking(px, py):
                return True
        return False

    def update(self, dt, keys, world):
        # Направление
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        # Нормализация диагонали
        if dx != 0 and dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length

        self.running = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        speed = PLAYER_SPEED * (1.6 if self.running else 1.0)

        if dx != 0 or dy != 0:
            self.facing = math.atan2(dy, dx)
            self.bob += dt * 10
        else:
            self.bob *= 0.9

        self.try_move(dx * speed * dt, dy * speed * dt, world)

    def draw(self, screen, cam_x, cam_y):
        # Тень
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        shadow = pygame.Surface((self.radius * 2 + 4, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 100),
                           (0, 0, self.radius * 2 + 4, 8))
        screen.blit(shadow, (sx - self.radius - 2, sy + self.radius - 2))

        # Тело (с лёгким bob)
        bob_offset = int(abs(math.sin(self.bob)) * 2)
        r = self.radius

        # Белый круг
        pygame.draw.circle(screen, PLAYER, (sx, sy - bob_offset), r)
        # Обводка
        pygame.draw.circle(screen, PLAYER_ACCENT, (sx, sy - bob_offset), r, 2)

        # Уши — по направлению движения
        ang = self.facing
        # Уши перпендикулярны направлению
        for side in (-1, 1):
            perp = ang + side * 0.7
            ux = sx + int(math.cos(perp) * r * 0.9)
            uy = sy - bob_offset + int(math.sin(perp) * r * 0.9)
            pygame.draw.circle(screen, PLAYER, (ux, uy), 5)
            pygame.draw.circle(screen, PLAYER_ACCENT, (ux, uy), 5, 1)
            # Внутренняя розовая
            pygame.draw.circle(screen, (240, 150, 170), (ux, uy), 2)

        # Глаза — по направлению
        fx = math.cos(ang) * 4
        fy = math.sin(ang) * 4
        # Левый и правый глаз
        for side in (-1, 1):
            perp = ang + side * math.pi / 2
            ex = sx + int(math.cos(perp) * 4 + fx * 0.5)
            ey = sy - bob_offset + int(math.sin(perp) * 4 + fy * 0.5)
            pygame.draw.circle(screen, (30, 25, 35), (ex, ey), 2)
