"""Враги — баги, вирусы, firewalls."""
import pygame
import random
import math
from settings import *


class Enemy:
    def __init__(self, x, y, kind="bug"):
        self.x, self.y = x, y
        self.kind = kind
        self.move_cooldown = 0.0
        self.hit_flash = 0.0

        # Характеристики по типу
        if kind == "bug":
            self.display_name = "Искра"
            self.hp = 5
            self.max_hp = 5
            self.attack = 2
            self.color = (200, 60, 80)
            self.speed = 0.6
            self.xp_reward = 5
        elif kind == "virus":
            self.display_name = "Вихрь"
            self.hp = 8
            self.max_hp = 8
            self.attack = 3
            self.color = (180, 80, 220)
            self.speed = 0.5
            self.xp_reward = 10
        elif kind == "firewall":
            self.display_name = "Страж"
            self.hp = 15
            self.max_hp = 15
            self.attack = 5
            self.color = (220, 140, 60)
            self.speed = 0.8
            self.xp_reward = 20
        elif kind == "boss":
            self.display_name = "Хранитель"
            self.hp = 40
            self.max_hp = 40
            self.attack = 8
            self.color = (255, 40, 60)
            self.speed = 0.4
            self.xp_reward = 100

    def dist(self, other):
        return math.hypot(self.x - other[0], self.y - other[1])

    def update(self, dt, player, dungeon, other_enemies):
        if self.move_cooldown > 0:
            self.move_cooldown -= dt
            return
        if self.hit_flash > 0:
            self.hit_flash -= dt

        # Если игрок рядом — атака
        dist = self.dist((player.x, player.y))
        if dist < 1.1:
            # Атака
            player.hp -= self.attack
            self.move_cooldown = 0.9
            return

        # Преследование если игрок близко (8 клеток)
        if dist < 8:
            dx = player.x - self.x
            dy = player.y - self.y
            # Простая навигация: сначала по большой оси
            if abs(dx) > abs(dy):
                nx, ny = self.x + (1 if dx > 0 else -1), self.y
            else:
                nx, ny = self.x, self.y + (1 if dy > 0 else -1)
            # Проверка коллизий
            if dungeon.is_walkable(nx, ny) and not any(
                    e.x == nx and e.y == ny and e is not self for e in other_enemies):
                self.x, self.y = nx, ny
            self.move_cooldown = self.speed
        else:
            # Случайное блуждание
            if random.random() < 0.3:
                dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                nx, ny = self.x + dx, self.y + dy
                if dungeon.is_walkable(nx, ny) and not any(
                        e.x == nx and e.y == ny and e is not self for e in other_enemies):
                    self.x, self.y = nx, ny
            self.move_cooldown = 1.2

    def draw(self, scr, cam_x, cam_y):
        px = self.x * TILE - cam_x + TILE // 2
        py = self.y * TILE - cam_y + TILE // 2

        # Тень
        pygame.draw.ellipse(scr, (0, 0, 0, 80),
                            (px - 10, py + 6, 20, 6))

        color = self.color
        if self.hit_flash > 0:
            color = (255, 255, 255)

        # Тело
        if self.kind == "bug":
            # Овальный баг
            pygame.draw.ellipse(scr, color, (px - 12, py - 8, 24, 16))
            # Глаза
            pygame.draw.circle(scr, (30, 20, 25), (px - 4, py - 2), 2)
            pygame.draw.circle(scr, (30, 20, 25), (px + 4, py - 2), 2)
            # Усики
            pygame.draw.line(scr, color, (px - 4, py - 8), (px - 8, py - 14), 2)
            pygame.draw.line(scr, color, (px + 4, py - 8), (px + 8, py - 14), 2)
        elif self.kind == "virus":
            # Треугольник
            pygame.draw.polygon(scr, color, [
                (px, py - 12), (px - 12, py + 8), (px + 12, py + 8)])
            pygame.draw.polygon(scr, (255, 255, 255, 200), [
                (px, py - 12), (px - 12, py + 8), (px + 12, py + 8)], 2)
        elif self.kind == "firewall":
            # Квадрат с огнём
            pygame.draw.rect(scr, color, (px - 11, py - 11, 22, 22))
            pygame.draw.rect(scr, (255, 255, 255, 180),
                             (px - 11, py - 11, 22, 22), 2)
            # Пламя
            pygame.draw.polygon(scr, (255, 200, 80), [
                (px - 4, py - 6), (px, py - 14), (px + 4, py - 6)])
        else:  # boss
            pygame.draw.circle(scr, color, (px, py), 16)
            pygame.draw.circle(scr, (255, 255, 255, 200), (px, py), 16, 2)
            pygame.draw.circle(scr, (60, 20, 30), (px - 5, py - 3), 3)
            pygame.draw.circle(scr, (60, 20, 30), (px + 5, py - 3), 3)
            # HP бар над боссом
            bar_w = 30
            hp_pct = self.hp / self.max_hp
            pygame.draw.rect(scr, (40, 20, 20), (px - bar_w//2, py - 26, bar_w, 4))
            pygame.draw.rect(scr, (255, 60, 80), (px - bar_w//2, py - 26, int(bar_w * hp_pct), 4))

    def alive(self):
        return self.hp > 0
