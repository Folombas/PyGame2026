"""Бесконечный процедурно генерируемый мир. Без уровней, без границ."""
import pygame
from platform import Platform
from enemy import Enemy
from collectible import Pixel
from tree import AppleTree
from medkit import Medkit


CHUNK_SIZE = 400
SURFACE_Y = 1200          # средний уровень земли
GROUND_DEPTH = 600        # насколько глубоко под землёй генерировать породу
COLUMN_W = 32             # ширина столбца земли
DEATH_Y = SURFACE_Y + 1800  # глубже — смерть от падения в бездну


def _hash(x, y, seed=0):
    """Детерминированный хеш 0..1 (одинаковый для одинаковых координат)."""
    n = (x * 374761393 + y * 668265263 + seed * 1274126177) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFFFF) / 0xFFFFFFFF


def _smooth1d(x, scale, seed=0):
    """Сглаженный 1D шум (для высоты поверхности)."""
    xf = x / scale
    x0 = int(xf)
    if xf < 0:
        x0 -= 1
    t = xf - x0
    t = t * t * (3 - 2 * t)
    a = _hash(x0, 0, seed)
    b = _hash(x0 + 1, 0, seed)
    return a * (1 - t) + b * t


def surface_y(x):
    """Мировой Y поверхности для столбца X (плавно колеблется ±120px)."""
    n = ((_smooth1d(x, 350, 1) - 0.5) * 130
         + (_smooth1d(x, 140, 2) - 0.5) * 50
         + (_smooth1d(x, 60, 3) - 0.5) * 20)
    return SURFACE_Y + int(n)


def is_cave(x, y):
    """True — если в этой мировой точке пустота (пещера)."""
    sy = surface_y(x)
    if y < sy + 90:
        return False   # верхний слой земли всегда сплошной
    v = (_hash(x // 25, y // 25, 5) * 0.5
         + _hash(x // 50, y // 50, 6) * 0.5)
    # Чем глубже — тем больше пустот
    depth_factor = min(0.25, (y - sy) / 3000.0)
    return v > 0.60 - depth_factor


class Chunk:
    """Один чанк мира 400x400 px. Генерируется один раз, кешируется."""

    def __init__(self, cx, cy, difficulty):
        self.cx = cx
        self.cy = cy
        self.difficulty = difficulty
        self.platforms = []
        self.enemies = []
        self.pixels = []
        self.trees = []
        self.medkits = []
        self._generate()

    def _generate(self):
        x0 = self.cx * CHUNK_SIZE
        y0 = self.cy * CHUNK_SIZE
        x1 = x0 + CHUNK_SIZE
        y1 = y0 + CHUNK_SIZE

        # ----- Земля: столбцы твёрдой породы -----
        col_start = (x0 // COLUMN_W - 1) * COLUMN_W
        for col_x in range(col_start, x1 + COLUMN_W, COLUMN_W):
            sy = surface_y(col_x)
            ground_end = sy + GROUND_DEPTH
            gy = sy
            while gy < ground_end:
                if gy + COLUMN_W < y0:
                    gy += COLUMN_W
                    continue
                if gy > y1:
                    break
                if not is_cave(col_x, gy + COLUMN_W // 2):
                    self.platforms.append(Platform(col_x, gy, COLUMN_W + 1, COLUMN_W))
                gy += COLUMN_W

        # ----- Висячие платформы в воздухе -----
        step = 240
        start = (x0 // step) * step
        for px in range(start, x1 + step, step):
            if _hash(px // step, self.cy, 10) > 0.5:
                sy = surface_y(px)
                height = 120 + int(_hash(px // step, 1, 10) * 220)
                py = sy - height
                if y0 - 20 <= py <= y1:
                    w = 100 + int(_hash(px // step, 2, 10) * 100)
                    self.platforms.append(Platform(px, py, w, 20))
                    if _hash(px // step, 3, 10) > 0.35:
                        self.pixels.append(Pixel(px + w // 2 - 7, py - 22))

        # ----- Деревья на поверхности -----
        step = 350
        start = (x0 // step) * step
        for tx in range(start, x1 + step, step):
            if _hash(tx // step, 0, 20) > 0.5:
                sy = surface_y(tx)
                if y0 - 200 <= sy <= y1 + 200:
                    self.trees.append(AppleTree(tx, sy))

        # ----- Враги -----
        density = self.difficulty.get("enemy_density", 0.4)
        step = 300
        start = (x0 // step) * step
        for ex in range(start, x1 + step, step):
            if _hash(ex // step, 0, 30) < density:
                sy = surface_y(ex)
                if y0 - 28 <= sy - 28 <= y1:
                    self.enemies.append(Enemy(ex, sy - 28))

        # ----- Аптечки -----
        step = 600
        start = (x0 // step) * step
        for mx in range(start, x1 + step, step):
            if _hash(mx // step, 0, 40) > 0.55:
                sy = surface_y(mx)
                if y0 - 40 <= sy - 40 <= y1:
                    self.medkits.append(Medkit(mx, sy - 40))


class World:
    """Хранилище чанков, генерирует по мере движения."""

    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.chunks = {}

    def _get_chunk(self, cx, cy):
        key = (cx, cy)
        if key not in self.chunks:
            self.chunks[key] = Chunk(cx, cy, self.difficulty)
        return self.chunks[key]

    def update(self, camera):
        """Подгружает видимые чанки, выгружает далёкие."""
        cx0 = int((camera.offset_x - CHUNK_SIZE) // CHUNK_SIZE)
        cx1 = int((camera.offset_x + camera.view_width + CHUNK_SIZE) // CHUNK_SIZE)
        cy0 = int((camera.offset_y - CHUNK_SIZE) // CHUNK_SIZE)
        cy1 = int((camera.offset_y + camera.view_height + CHUNK_SIZE) // CHUNK_SIZE)

        active = set()
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                self._get_chunk(cx, cy)
                active.add((cx, cy))

        # Выгружаем очень далёкие чанки (экономия памяти)
        for key in list(self.chunks.keys()):
            cx, cy = key
            if abs(cx - cx0) > 5 or abs(cy - cy0) > 5:
                del self.chunks[key]

    def collect(self):
        """Собирает все объекты из всех загруженных чанков."""
        platforms, enemies, pixels, trees, medkits = [], [], [], [], []
        for ch in self.chunks.values():
            platforms.extend(ch.platforms)
            enemies.extend(ch.enemies)
            pixels.extend(ch.pixels)
            trees.extend(ch.trees)
            medkits.extend(ch.medkits)
        return platforms, enemies, pixels, trees, medkits
