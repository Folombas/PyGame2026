"""Asteroids — космический шутер в стиле BunnyOS."""
import pygame
import random
import sys
import math
import records


WIDTH, HEIGHT = 900, 700
FPS = 60

C_BG = (8, 10, 20)
C_TEXT = (220, 230, 245)
C_TEXT_DIM = (120, 140, 170)
C_SHIP = (100, 200, 255)
C_BULLET = (255, 240, 100)
C_ASTEROID = (180, 170, 140)
C_ACCENT = (100, 180, 255)

SHIP_SIZE = 14
SHIP_TURN = 4.0
SHIP_THRUST = 300
SHIP_FRICTION = 0.99
MAX_SPEED = 400

BULLET_SPEED = 550
BULLET_LIFE = 1.2

AST_RADII = [50, 30, 18]
AST_SPEEDS = [60, 90, 120]

VOLUME_MASTER = 0.25


class Ship:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = self.vy = 0
        self.angle = -90  # смотрит вверх
        self.alive = True
        self.invuln = 2.0  # секунд неуязвимости
        self.thrusting = False

    def update(self, dt, keys):
        if not self.alive:
            return
        if self.invuln > 0:
            self.invuln -= dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= SHIP_TURN
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += SHIP_TURN
        self.thrusting = False
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            rad = math.radians(self.angle)
            self.vx += math.cos(rad) * SHIP_THRUST * dt
            self.vy += math.sin(rad) * SHIP_THRUST * dt
            self.thrusting = True
        # трение
        self.vx *= SHIP_FRICTION
        self.vy *= SHIP_FRICTION
        # макс скорость
        sp = math.hypot(self.vx, self.vy)
        if sp > MAX_SPEED:
            self.vx = self.vx / sp * MAX_SPEED
            self.vy = self.vy / sp * MAX_SPEED
        self.x += self.vx * dt
        self.y += self.vy * dt
        # wrap
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, scr):
        if not self.alive:
            return
        # мигание при неуязвимости
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            return
        rad = math.radians(self.angle)
        # треугольник
        p1 = (self.x + math.cos(rad) * SHIP_SIZE,
              self.y + math.sin(rad) * SHIP_SIZE)
        p2 = (self.x + math.cos(rad + 2.5) * SHIP_SIZE * 0.9,
              self.y + math.sin(rad + 2.5) * SHIP_SIZE * 0.9)
        p3 = (self.x + math.cos(rad - 2.5) * SHIP_SIZE * 0.9,
              self.y + math.sin(rad - 2.5) * SHIP_SIZE * 0.9)
        pygame.draw.polygon(scr, C_SHIP, [p1, p2, p3])
        pygame.draw.polygon(scr, (200, 240, 255), [p1, p2, p3], 2)
        # выхлоп
        if self.thrusting:
            px = self.x - math.cos(rad) * SHIP_SIZE * 1.2
            py = self.y - math.sin(rad) * SHIP_SIZE * 1.2
            pygame.draw.circle(scr, (255, 180, 80), (int(px), int(py)), 5)
            pygame.draw.circle(scr, (255, 240, 140), (int(px), int(py)), 2)

    def get_poly(self):
        rad = math.radians(self.angle)
        return [
            (self.x + math.cos(rad) * SHIP_SIZE,
             self.y + math.sin(rad) * SHIP_SIZE),
            (self.x + math.cos(rad + 2.5) * SHIP_SIZE * 0.9,
             self.y + math.sin(rad + 2.5) * SHIP_SIZE * 0.9),
            (self.x + math.cos(rad - 2.5) * SHIP_SIZE * 0.9,
             self.y + math.sin(rad - 2.5) * SHIP_SIZE * 0.9),
        ]


class Bullet:
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        rad = math.radians(angle)
        self.vx = math.cos(rad) * BULLET_SPEED
        self.vy = math.sin(rad) * BULLET_SPEED
        self.life = BULLET_LIFE

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x %= WIDTH
        self.y %= HEIGHT
        self.life -= dt

    def draw(self, scr):
        pygame.draw.circle(scr, C_BULLET, (int(self.x), int(self.y)), 3)


class Asteroid:
    def __init__(self, x, y, size_idx):
        self.x, self.y = x, y
        self.size_idx = size_idx
        self.radius = AST_RADII[size_idx]
        angle = random.uniform(0, math.tau)
        speed = AST_SPEEDS[size_idx]
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        # полигон (случайной формы)
        self.poly = []
        n = random.randint(8, 12)
        for i in range(n):
            a = i * math.tau / n
            r = self.radius * random.uniform(0.8, 1.2)
            self.poly.append((math.cos(a) * r, math.sin(a) * r))

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, scr):
        points = [(self.x + dx, self.y + dy) for dx, dy in self.poly]
        pygame.draw.polygon(scr, C_ASTEROID, points)
        pygame.draw.polygon(scr, (120, 110, 90), points, 2)

    def hit(self, x, y, r=5):
        return math.hypot(self.x - x, self.y - y) < self.radius + r
