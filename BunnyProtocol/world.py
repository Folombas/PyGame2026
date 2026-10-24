"""Процедурная серверная — комнаты, коридоры, серверные стойки."""
import random
from settings import *


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def rect(self):
        return pygame_rect(self.x, self.y, self.w, self.h)


def pygame_rect(x, y, w, h):
    import pygame
    return pygame.Rect(x, y, w, h)


class World:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.rng = random.Random(self.seed)
        # 0 = стена, 1 = пол, 2 = сервер (блокирует зрение)
        self.tiles = [[0 for _ in range(MAP_W)] for _ in range(MAP_H)]
        self.rooms = []
        self.servers = []  # список Rect серверных стоек
        self._generate()

    def _generate(self):
        # BSP-лайт: случайные комнаты + коридоры
        max_rooms = 9
        attempts = 0
        while len(self.rooms) < max_rooms and attempts < 100:
            attempts += 1
            w = self.rng.randint(6, 11)
            h = self.rng.randint(5, 9)
            x = self.rng.randint(2, MAP_W - w - 2)
            y = self.rng.randint(2, MAP_H - h - 2)
            new = Room(x, y, w, h)
            if any(self._overlap(new, r) for r in self.rooms):
                continue
            self._carve(new)
            if self.rooms:
                self._connect(self.rooms[-1].center, new.center)
            self.rooms.append(new)

        # Ставим серверные стойки (2-4 в каждой комнате, кроме стартовой)
        for i, r in enumerate(self.rooms):
            if i == 0:
                continue  # старт пустой
            n_servers = self.rng.randint(1, 4)
            for _ in range(n_servers):
                sx = r.x + self.rng.randint(1, max(1, r.w - 3))
                sy = r.y + self.rng.randint(1, max(1, r.h - 3))
                if self.tiles[sy][sx] == 1:
                    self.tiles[sy][sx] = 2
                    self.servers.append(pygame_rect(
                        sx * TILE, sy * TILE, TILE, TILE))

    def _overlap(self, a, b, pad=1):
        return not (
            a.x + a.w + pad < b.x or b.x + b.w + pad < a.x or
            a.y + a.h + pad < b.y or b.y + b.h + pad < a.y
        )

    def _carve(self, room):
        for y in range(room.y, room.y + room.h):
            for x in range(room.x, room.x + room.w):
                self.tiles[y][x] = 1

    def _connect(self, a, b):
        ax, ay = a
        bx, by = b
        if self.rng.random() < 0.5:
            for x in range(min(ax, bx), max(ax, bx) + 1):
                if 0 <= ay < MAP_H:
                    self.tiles[ay][x] = 1
            for y in range(min(ay, by), max(ay, by) + 1):
                if 0 <= y < MAP_H:
                    self.tiles[y][bx] = 1
        else:
            for y in range(min(ay, by), max(ay, by) + 1):
                if 0 <= y < MAP_H:
                    self.tiles[y][ax] = 1
            for x in range(min(ax, bx), max(ax, bx) + 1):
                if 0 <= ay < MAP_H:
                    self.tiles[by][x] = 1

    def spawn_point(self):
        c = self.rooms[0].center
        return c[0] * TILE + TILE // 2, c[1] * TILE + TILE // 2

    def exit_point(self):
        c = self.rooms[-1].center
        return c[0] * TILE + TILE // 2, c[1] * TILE + TILE // 2

    def free_cells(self):
        cells = []
        for y in range(MAP_H):
            for x in range(MAP_W):
                if self.tiles[y][x] == 1:
                    cells.append((x * TILE + TILE // 2, y * TILE + TILE // 2))
        return cells

    def is_wall(self, px, py):
        """Проверка точки: стена ли?"""
        tx, ty = int(px) // TILE, int(py) // TILE
        if not (0 <= tx < MAP_W and 0 <= ty < MAP_H):
            return True
        return self.tiles[ty][tx] == 0

    def is_blocking(self, px, py):
        """Стена или сервер — блокирует движение и зрение."""
        tx, ty = int(px) // TILE, int(py) // TILE
        if not (0 <= tx < MAP_W and 0 <= ty < MAP_H):
            return True
        return self.tiles[ty][tx] in (0, 2)

    def raycast_block(self, x1, y1, x2, y2):
        """Есть ли препятствие между точками? Простой DDA."""
        import math
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            return False
        steps = int(dist / 8)
        for i in range(1, steps):
            t = i / steps
            px = x1 + dx * t
            py = y1 + dy * t
            if self.is_blocking(px, py):
                return True
        return False
