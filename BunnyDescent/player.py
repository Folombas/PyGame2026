"""Игрок — зайка-хакер."""
import pygame
from settings import *


class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = PLAYER_HP
        self.max_hp = PLAYER_HP
        self.mp = PLAYER_MP
        self.max_mp = PLAYER_MP
        self.xp = 0
        self.level = 1
        self.attack = 3
        self.defense = 1
        # Анимация движения
        self.move_cooldown = 0.0
        self.bob_timer = 0.0
        self.facing = (0, 1)  # вниз

    def try_move(self, dx, dy, dungeon):
        if self.move_cooldown > 0:
            return False
        nx, ny = self.x + dx, self.y + dy
        if dungeon.is_walkable(nx, ny):
            self.x, self.y = nx, ny
            self.facing = (dx, dy)
            self.move_cooldown = PLAYER_SPEED
            self.bob_timer = 0.2
            return True
        return False

    def update(self, dt):
        if self.move_cooldown > 0:
            self.move_cooldown -= dt
        if self.bob_timer > 0:
            self.bob_timer -= dt

    def draw(self, scr, cam_x, cam_y):
        px = self.x * TILE - cam_x + TILE // 2
        py = self.y * TILE - cam_y + TILE // 2
        # bob
        if self.bob_timer > 0:
            py -= int(abs(self.bob_timer) * 6)
        # Тень
        pygame.draw.ellipse(scr, (0, 0, 0, 80),
                            (px - 12, py + 8, 24, 8))
        # Тело — круг
        pygame.draw.circle(scr, (240, 240, 250), (px, py), 13)
        pygame.draw.circle(scr, (100, 140, 200), (px, py), 13, 2)
        # Уши
        pygame.draw.ellipse(scr, (240, 240, 250), (px - 8, py - 22, 7, 14))
        pygame.draw.ellipse(scr, (240, 240, 250), (px + 1, py - 22, 7, 14))
        pygame.draw.ellipse(scr, (240, 150, 170), (px - 6, py - 20, 3, 10))
        pygame.draw.ellipse(scr, (240, 150, 170), (px + 3, py - 20, 3, 10))
        # Глаза (по направлению)
        fx, fy = self.facing
        ox = fx * 3
        oy = fy * 2
        pygame.draw.circle(scr, (30, 25, 35), (px - 4 + ox, py - 2 + oy), 2)
        pygame.draw.circle(scr, (30, 25, 35), (px + 4 + ox, py - 2 + oy), 2)
        # Нос
        pygame.draw.circle(scr, (240, 150, 170), (px, py + 3), 2)
