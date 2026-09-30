"""Бесконечный процедурный мир: горы, пещеры с входами, погодные зоны."""
import pygame
from blocks import TILE_SIZE, AIR, DIRT, GRASS, STONE, COPPER, IRON, GOLD, SAND
from platform import Platform
from enemy import Enemy
from collectible import Pixel
from tree import AppleTree
from medkit import Medkit


CHUNK_SIZE = 400
SURFACE_Y = 1200          # базовый уровень земли
GROUND_DEPTH = 600
COLUMN_W = 32
DEATH_Y = SURFACE_Y + 1800

# Высотные зоны (по мировой Y)
TEMP_ZONES = [
    (0,     200,  "freezing"),   # ледяные вершины
    (200,   500,  "snow"),       # снега
    (500,   800,  "cold"),       # холодные горы
    (800,   SURFACE_Y, "mild"),  # умеренно
    (SURFACE_Y, SURFACE_Y + 400, "cave_warm"),  # пещеры тёплые
    (SURFACE_Y + 400, 99999, "cave_hot"),       # глубоко — жарко
]


def weather_zone(world_y):
    for y_min, y_max, key in TEMP_ZONES:
        if y_min <= world_y < y_max:
            return key
    return "mild"


def get_ambient_temp(world_y):
    """Температура среды в мировой точке (0..100)."""
    if world_y < SURFACE_Y:
        # Над землёй: 100 у поверхности → 0 на 1000px вверх
        altitude = (SURFACE_Y - world_y)
        return max(0.0, 100.0 - altitude * 0.1)
    else:
        # Под землёй: тёплые пещеры (70), глубже — жарче (до 95)
        depth = world_y - SURFACE_Y
        t = min(1.0, depth / 1500.0)
        return 70.0 + t * 25.0


def _hash(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 1274126177) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFFFF) / 0xFFFFFFFF


def _smooth1d(x, scale, seed=0):
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
    """Рельеф: холмы + редкие горы с пиками."""
    # Базовые холмы
    base = SURFACE_Y
    base += int((_smooth1d(x, 350, 1) - 0.5) * 60)
    base += int((_smooth1d(x, 140, 2) - 0.5) * 25)

    # Горы: горный шум, редкие высокие пики
    m = _smooth1d(x, 800, 10)
    if m > 0.65:
        peak_t = (m - 0.65) / 0.35  # 0..1
        peak_h = peak_t * peak_t * 750  # до 750 px вверх
        base -= int(peak_h)
    return base


def is_cave_entrance(x, y):
    """Вертикальный вход-шахта на поверхности."""
    sy = surface_y(x)
    col = x // 24
    if _hash(col, 0, 77) > 0.94:
        if sy + 5 < y < sy + 300:
            return True
    return False


def is_cave(x, y):
    """True — пустота (пещера или вход)."""
    sy = surface_y(x)
    if y < sy + 60:
        return is_cave_entrance(x, y)

    v = (_hash(x // 25, y // 25, 5) * 0.5
         + _hash(x // 50, y // 50, 6) * 0.5)
    depth_factor = min(0.30, (y - sy) / 3000.0)
    return v > 0.60 - depth_factor




def block_at(x, y):
    """Тип блока в мировой точке (x, y)."""
    sy = surface_y(x)
    if y < sy:
        return AIR
    # верхний слой — трава
    if y < sy + TILE_SIZE:
        return GRASS if sy > 700 else SAND
    # следующие 4 тайла — земля
    if y < sy + TILE_SIZE * 5:
        return DIRT
    # дальше — камень с рудой
    depth = (y - sy) // TILE_SIZE
    h = _hash(x // TILE_SIZE, y // TILE_SIZE, 42)
    if depth > 6:
        if h > 0.985:
            return GOLD
        if h > 0.955:
            return IRON
        if h > 0.90:
            return COPPER
    return STONE


class Chunk:
    def __init__(self, cx, cy, difficulty, modifications=None):
        self.cx = cx
        self.cy = cy
        self.difficulty = difficulty
        self.modifications = modifications or {}
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
                tx = col_x // TILE_SIZE
                ty = gy // TILE_SIZE
                # игрок изменял этот тайл?
                if (tx, ty) in self.modifications:
                    mod = self.modifications[(tx, ty)]
                    if mod is not None:
                        p = Platform(col_x, gy, COLUMN_W + 1, COLUMN_W, block_type=mod)
                        self.platforms.append(p)
                elif not is_cave(col_x, gy + COLUMN_W // 2):
                    bt = block_at(col_x, gy + COLUMN_W // 2)
                    if bt != AIR:
                        p = Platform(col_x, gy, COLUMN_W + 1, COLUMN_W, block_type=bt)
                        self.platforms.append(p)
                gy += COLUMN_W

        # Висячие платформы в воздухе (только над землёй)
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

        # Деревья (только в умеренной зоне, Y > 700)
        step = 350
        start = (x0 // step) * step
        for tx in range(start, x1 + step, step):
            if _hash(tx // step, 0, 20) > 0.5:
                sy = surface_y(tx)
                if sy < 700:
                    continue  # выше снеговой линии деревьев нет
                if y0 - 200 <= sy <= y1 + 200:
                    self.trees.append(AppleTree(tx, sy))

        # Враги
        density = self.difficulty.get("enemy_density", 0.4)
        step = 300
        start = (x0 // step) * step
        for ex in range(start, x1 + step, step):
            if _hash(ex // step, 0, 30) < density:
                sy = surface_y(ex)
                if y0 - 28 <= sy - 28 <= y1:
                    self.enemies.append(Enemy(ex, sy - 28))

        # Аптечки
        step = 600
        start = (x0 // step) * step
        for mx in range(start, x1 + step, step):
            if _hash(mx // step, 0, 40) > 0.55:
                sy = surface_y(mx)
                if y0 - 40 <= sy - 40 <= y1:
                    self.medkits.append(Medkit(mx, sy - 40))


class World:
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.chunks = {}
        self.modifications = {}   # (tx, ty) -> block_type или None

    def _get_chunk(self, cx, cy):
        key = (cx, cy)
        if key not in self.chunks:
            self.chunks[key] = Chunk(cx, cy, self.difficulty, self.modifications)
        return self.chunks[key]


    def world_to_tile(self, wx, wy):
        return (wx // TILE_SIZE, wy // TILE_SIZE)

    def get_block_type(self, wx, wy):
        """Тип блока в мировой точке. None — если пустота."""
        tx, ty = self.world_to_tile(wx, wy)
        if (tx, ty) in self.modifications:
            return self.modifications[(tx, ty)]
        # если не модифицирован — смотрим сгенерированный чанк
        cx = tx * TILE_SIZE // CHUNK_SIZE
        cy = ty * TILE_SIZE // CHUNK_SIZE
        ch = self._get_chunk(cx, cy)
        for p in ch.platforms:
            if p.rect.x <= wx < p.rect.right and p.rect.y <= wy < p.rect.bottom:
                return getattr(p, "block_type", STONE)
        return None

    def dig(self, wx, wy):
        """Убирает блок. Возвращает его тип или None."""
        tx, ty = self.world_to_tile(wx, wy)
        bt = self.get_block_type(wx, wy)
        if bt is None or bt == AIR:
            return None
        # удаляем из чанка
        cx = tx * TILE_SIZE // CHUNK_SIZE
        cy = ty * TILE_SIZE // CHUNK_SIZE
        ch = self._get_chunk(cx, cy)
        r = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        ch.platforms = [p for p in ch.platforms if not (p.rect.x == r.x and p.rect.y == r.y)]
        # запоминаем изменение
        self.modifications[(tx, ty)] = None
        return bt

    def place(self, wx, wy, block_type):
        """Ставит блок. Возвращает True при успехе."""
        tx, ty = self.world_to_tile(wx, wy)
        if self.get_block_type(wx, wy) is not None:
            return False
        cx = tx * TILE_SIZE // CHUNK_SIZE
        cy = ty * TILE_SIZE // CHUNK_SIZE
        ch = self._get_chunk(cx, cy)
        p = Platform(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE + 1, TILE_SIZE, block_type=block_type)
        ch.platforms.append(p)
        self.modifications[(tx, ty)] = block_type
        return True

    def update(self, camera):
        cx0 = int((camera.offset_x - CHUNK_SIZE) // CHUNK_SIZE)
        cx1 = int((camera.offset_x + camera.view_width + CHUNK_SIZE) // CHUNK_SIZE)
        cy0 = int((camera.offset_y - CHUNK_SIZE) // CHUNK_SIZE)
        cy1 = int((camera.offset_y + camera.view_height + CHUNK_SIZE) // CHUNK_SIZE)

        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                self._get_chunk(cx, cy)

        for key in list(self.chunks.keys()):
            cx, cy = key
            if abs(cx - cx0) > 5 or abs(cy - cy0) > 5:
                del self.chunks[key]

    def collect(self):
        platforms, enemies, pixels, trees, medkits = [], [], [], [], []
        for ch in self.chunks.values():
            platforms.extend(ch.platforms)
            enemies.extend(ch.enemies)
            pixels.extend(ch.pixels)
            trees.extend(ch.trees)
            medkits.extend(ch.medkits)
        return platforms, enemies, pixels, trees, medkits
