"""Процедурная генерация подземелья (BSP-дерево)."""
import random
from settings import MAP_W, MAP_H


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other, pad=1):
        return not (
            self.x + self.w + pad < other.x or
            other.x + other.w + pad < self.x or
            self.y + self.h + pad < other.y or
            other.y + other.h + pad < self.y
        )


class Dungeon:
    def __init__(self, level=1, seed=None):
        self.level = level
        self.seed = seed or random.randint(0, 999999)
        rng = random.Random(self.seed)
        self.rng = rng

        # 0 = стена, 1 = пол, 2 = дверь, 3 = лестница вниз
        self.tiles = [[0 for _ in range(MAP_W)] for _ in range(MAP_H)]
        self.rooms = []
        self._generate()

    def _generate(self):
        # Пытаемся сгенерировать 8-14 комнат
        max_rooms = self.rng.randint(8, 14) + self.level
        attempts = 0
        while len(self.rooms) < max_rooms and attempts < 200:
            attempts += 1
            w = self.rng.randint(5, 10)
            h = self.rng.randint(4, 8)
            x = self.rng.randint(2, MAP_W - w - 2)
            y = self.rng.randint(2, MAP_H - h - 2)
            new_room = Room(x, y, w, h)
            # Проверка пересечений
            if any(new_room.intersects(r) for r in self.rooms):
                continue
            self._carve_room(new_room)
            if self.rooms:
                # Соединяем с предыдущей
                self._connect(new_room.center, self.rooms[-1].center)
            self.rooms.append(new_room)

        # Лестница вниз — в последней комнате
        if self.rooms:
            sx, sy = self.rooms[-1].center
            self.tiles[sy][sx] = 3

    def _carve_room(self, room):
        for y in range(room.y, room.y + room.h):
            for x in range(room.x, room.x + room.w):
                self.tiles[y][x] = 1

    def _connect(self, a, b):
        ax, ay = a
        bx, by = b
        # L-образный коридор
        if self.rng.random() < 0.5:
            for x in range(min(ax, bx), max(ax, bx) + 1):
                self.tiles[ay][x] = 1
            for y in range(min(ay, by), max(ay, by) + 1):
                self.tiles[y][bx] = 1
        else:
            for y in range(min(ay, by), max(ay, by) + 1):
                self.tiles[y][ax] = 1
            for x in range(min(ax, bx), max(ax, bx) + 1):
                self.tiles[by][x] = 1

    def spawn_pos(self):
        """Стартовая позиция — центр первой комнаты."""
        return self.rooms[0].center

    def exit_pos(self):
        """Позиция лестницы вниз."""
        for y in range(MAP_H):
            for x in range(MAP_W):
                if self.tiles[y][x] == 3:
                    return (x, y)
        return None

    def is_walkable(self, x, y):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            return self.tiles[y][x] in (1, 2, 3)
        return False

    def free_cells(self, exclude=()):
        """Свободные клетки для спавна врагов/предметов."""
        cells = []
        for y in range(MAP_H):
            for x in range(MAP_W):
                if self.tiles[y][x] == 1 and (x, y) not in exclude:
                    cells.append((x, y))
        return cells
