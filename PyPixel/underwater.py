"""Подводный мир: рыбы-враги, водоросли, кораллы, пузырьки."""
import math
import random
import pygame
from blocks import TILE_SIZE, WATER, AIR


# ---------- РЫБА (враг) ----------
class Fish:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 24, 16)
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = random.choice([-1.4, -1.0, 1.0, 1.4])
        self.alive = True
        self.timer = random.uniform(0, 6.28)
        self.range = random.randint(80, 200)

    def update(self, world):
        if not self.alive:
            return
        self.timer += 0.05
        self.rect.x += int(self.vel_x)
        # разворот если отплыл от spawn
        if abs(self.rect.centerx - self.spawn_x) > self.range:
            self.vel_x = -self.vel_x
        # вверх-вниз плавно
        self.rect.y = self.spawn_y + int(math.sin(self.timer) * 8)
        # если впереди не вода — разворот
        tx = (self.rect.centerx + (10 if self.vel_x > 0 else -10)) // TILE_SIZE
        ty = self.rect.centery // TILE_SIZE
        if world.get_block(tx, ty) != WATER:
            self.vel_x = -self.vel_x

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.alive:
            return
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.rect.w, self.rect.h
        facing_right = self.vel_x > 0

        body_col = (240, 120, 80)
        fin_col = (200, 80, 60)

        # тело — овал
        pygame.draw.ellipse(surface, body_col, (x, y + 2, w - 6, h - 4))
        # хвост
        if facing_right:
            pygame.draw.polygon(surface, fin_col, [
                (x, y + h // 2), (x - 6, y + 2), (x - 6, y + h - 2)])
            eye_x = x + w - 8
        else:
            pygame.draw.polygon(surface, fin_col, [
                (x + w - 4, y + h // 2), (x + w + 2, y + 2), (x + w + 2, y + h - 2)])
            eye_x = x + 4
        # глаз
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + h // 2), 3)
        pygame.draw.circle(surface, (20, 20, 20), (eye_x, y + h // 2), 2)


# ---------- ВОДОРОСЛИ ----------
class Seaweed:
    def __init__(self, x, y, height=None):
        self.x = x
        self.y = y
        self.height = height or random.randint(20, 56)
        self.timer = random.uniform(0, 6.28)
        self.segments = max(3, self.height // 8)

    def update(self):
        self.timer += 0.04

    def draw(self, surface, offset_x=0, offset_y=0):
        sx = self.x - offset_x
        sy = self.y - offset_y
        col = (40, 160, 90)
        col2 = (70, 200, 120)
        seg_h = self.height / self.segments
        for i in range(self.segments):
            t = i / self.segments
            sway = math.sin(self.timer + i * 0.5) * (2 + t * 4)
            px = sx + sway
            py = sy - i * seg_h
            pygame.draw.circle(surface, col, (int(px), int(py)), 3)
            pygame.draw.circle(surface, col2, (int(px) - 1, int(py) - 1), 1)


# ---------- КОРАЛЛ ----------
class Coral:
    PALETTES = [
        ((240, 100, 160), (255, 160, 200)),
        ((255, 180, 80), (255, 220, 140)),
        ((160, 100, 240), (200, 160, 255)),
        ((240, 90, 90), (255, 140, 140)),
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.col, self.col2 = random.choice(self.PALETTES)
        self.branches = []
        for _ in range(random.randint(2, 4)):
            angle = random.uniform(-0.9, 0.9)
            length = random.randint(10, 22)
            self.branches.append((angle, length))
        self.timer = random.uniform(0, 6.28)

    def update(self):
        self.timer += 0.03

    def draw(self, surface, offset_x=0, offset_y=0):
        sx = self.x - offset_x
        sy = self.y - offset_y
        # ствол
        pygame.draw.rect(surface, self.col, (sx - 2, sy - 10, 4, 12))
        # ветки
        for ang, ln in self.branches:
            ex = sx + int(math.sin(ang) * ln)
            ey = sy - 10 - int(math.cos(ang) * ln * 0.8)
            pygame.draw.line(surface, self.col, (sx, sy - 8), (ex, ey), 3)
            pygame.draw.circle(surface, self.col2, (ex, ey), 3)
        # мягкое свечение
        glow_a = 60 + int(40 * math.sin(self.timer))
        glow = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.col2, glow_a), (15, 15), 12)
        surface.blit(glow, (sx - 15, sy - 20))


# ---------- ПУЗЫРЬКИ (частицы от игрока) ----------
class Bubble:
    def __init__(self, x, y):
        self.x = float(x) + random.uniform(-6, 6)
        self.y = float(y)
        self.vy = -random.uniform(0.6, 1.4)
        self.vx = random.uniform(-0.3, 0.3)
        self.life = random.randint(40, 90)
        self.r = random.randint(2, 4)

    def update(self):
        self.y += self.vy
        self.x += self.vx
        self.life -= 1
        return self.life > 0

    def draw(self, surface, offset_x=0, offset_y=0):
        sx = int(self.x - offset_x)
        sy = int(self.y - offset_y)
        pygame.draw.circle(surface, (200, 230, 255), (sx, sy), self.r)
        pygame.draw.circle(surface, (255, 255, 255), (sx - 1, sy - 1), max(1, self.r - 2))
