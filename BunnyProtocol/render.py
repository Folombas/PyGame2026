"""Рендер мира — тайлы, серверы, камера."""
import pygame
from settings import *


class Camera:
    def __init__(self, world_w, world_h):
        self.x = 0.0
        self.y = 0.0
        self.world_w = world_w
        self.world_h = world_h

    def follow(self, px, py):
        target_x = px - WIDTH / 2
        target_y = py - HEIGHT / 2
        self.x += (target_x - self.x) * 0.15
        self.y += (target_y - self.y) * 0.15
        # Границы
        self.x = max(0, min(self.world_w * TILE - WIDTH, self.x))
        self.y = max(0, min(self.world_h * TILE - HEIGHT, self.y))


def draw_world(screen, world, cam):
    cam_x = int(cam.x)
    cam_y = int(cam.y)
    tx0 = max(0, cam_x // TILE)
    ty0 = max(0, cam_y // TILE)
    tx1 = min(MAP_W, (cam_x + WIDTH) // TILE + 2)
    ty1 = min(MAP_H, (cam_y + HEIGHT) // TILE + 2)

    for ty in range(ty0, ty1):
        for tx in range(tx0, tx1):
            t = world.tiles[ty][tx]
            px = tx * TILE - cam_x
            py = ty * TILE - cam_y
            if t == 0:
                # Стена
                pygame.draw.rect(screen, WALL, (px, py, TILE, TILE))
                pygame.draw.rect(screen, WALL_TOP, (px, py, TILE, 4))
            elif t == 1:
                # Пол (шахматный)
                c = FLOOR if (tx + ty) % 2 == 0 else FLOOR_ALT
                pygame.draw.rect(screen, c, (px, py, TILE, TILE))
            elif t == 2:
                # Серверная стойка
                pygame.draw.rect(screen, FLOOR, (px, py, TILE, TILE))
                pygame.draw.rect(screen, SERVER,
                                 (px + 2, py + 2, TILE - 4, TILE - 4),
                                 border_radius=3)
                # LED-полоска
                pygame.draw.rect(screen, SERVER_ON,
                                 (px + 6, py + 6, TILE - 12, 3))
                # Вентиляционные щели
                for i in range(3):
                    ly = py + 14 + i * 5
                    pygame.draw.line(screen, (20, 25, 40),
                                     (px + 6, ly), (px + TILE - 6, ly), 1)


def draw_fov_cone(screen, x, y, angle_deg, dist, half_angle_deg, cam_x, cam_y):
    """Рисует конус зрения врага."""
    import math
    cx = x - cam_x
    cy = y - cam_y
    a1 = math.radians(angle_deg - half_angle_deg)
    a2 = math.radians(angle_deg + half_angle_deg)
    points = [(cx, cy)]
    # Аппроксимация дуги
    steps = 12
    for i in range(steps + 1):
        t = i / steps
        a = a1 + (a2 - a1) * t
        points.append((cx + math.cos(a) * dist, cy + math.sin(a) * dist))
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(surf, ENEMY_FOV, points)
    screen.blit(surf, (0, 0))
