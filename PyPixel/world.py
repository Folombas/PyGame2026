"""Мир: чистая тайловая система с ленивой генерацией."""
import pygame
from blocks import (TILE_SIZE, AIR, DIRT, GRASS, STONE, COPPER, IRON, GOLD, SAND,
                    draw_block)
from enemy import Enemy
from collectible import Pixel
from tree import AppleTree
from medkit import Medkit

SURFACE_Y = 1200
DEATH_Y = SURFACE_Y + 1800


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
    base = SURFACE_Y
    base += int((_smooth1d(x, 350, 1) - 0.5) * 60)
    base += int((_smooth1d(x, 140, 2) - 0.5) * 25)
    m = _smooth1d(x, 800, 10)
    if m > 0.65:
        peak_t = (m - 0.65) / 0.35
        base -= int(peak_t * peak_t * 750)
    return base


def _gen_tile(tx, ty):
    wx = tx * TILE_SIZE + TILE_SIZE // 2
    wy = ty * TILE_SIZE + TILE_SIZE // 2
    sy = surface_y(wx)

    if wy < sy:
        return AIR

    depth = wy - sy

    # Пещеры ниже поверхности
    if depth > TILE_SIZE * 4:
        cv = _hash(tx // 2, ty // 2, 5) * 0.6 + _hash(tx, ty, 6) * 0.4
        df = min(0.25, depth / 3000.0)
        if cv > 0.62 - df:
            return AIR

    if depth < TILE_SIZE:
        return SAND if sy < 700 else GRASS
    if depth < TILE_SIZE * 4:
        return DIRT

    if depth > TILE_SIZE * 8:
        r = _hash(tx, ty, 42)
        if r > 0.985: return GOLD
        if r > 0.955: return IRON
        if r > 0.91: return COPPER

    return STONE


class Tile:
    """Обёртка тайла для коллизий."""
    __slots__ = ("rect", "block_type")
    def __init__(self, tx, ty, bt):
        self.rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.block_type = bt


class World:
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.mods = {}
        self.enemies = []
        self.pixels = []
        self.trees = []
        self.medkits = []
        self.spawned = set()
        self._last_chunk = None

    def get_block(self, tx, ty):
        if (tx, ty) in self.mods:
            return self.mods[(tx, ty)]
        return _gen_tile(tx, ty)

    def dig(self, tx, ty):
        bt = self.get_block(tx, ty)
        if bt == AIR:
            return None
        self.mods[(tx, ty)] = AIR
        return bt

    def place(self, tx, ty, bt):
        if self.get_block(tx, ty) != AIR:
            return False
        self.mods[(tx, ty)] = bt
        return True

    def solid_rect_check(self, px, py, w, h):
        tx0 = px // TILE_SIZE
        ty0 = py // TILE_SIZE
        tx1 = (px + w - 1) // TILE_SIZE
        ty1 = (py + h - 1) // TILE_SIZE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if self.get_block(tx, ty) != AIR:
                    return True
        return False

    def visible_tiles(self, camera):
        ox, oy = camera.ox, camera.oy
        tx0 = max(-500, ox // TILE_SIZE - 1)
        ty0 = max(-500, oy // TILE_SIZE - 1)
        tx1 = (ox + camera.view_width) // TILE_SIZE + 1
        ty1 = (oy + camera.view_height) // TILE_SIZE + 1
        out = []
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                bt = self.get_block(tx, ty)
                if bt != AIR:
                    out.append(Tile(tx, ty, bt))
        return out

    def update(self, camera):
        cx = int(camera.offset_x + camera.view_width // 2) // 512
        cy = int(camera.offset_y + camera.view_height // 2) // 512
        if (cx, cy) != self._last_chunk:
            self._last_chunk = (cx, cy)
            for dx in range(-3, 4):
                for dy in range(-2, 3):
                    self._spawn(cx + dx, cy + dy)
            # деспавн
            px = camera.offset_x + camera.view_width // 2
            py = camera.offset_y + camera.view_height // 2
            d = 2500
            self.enemies = [e for e in self.enemies if abs(e.rect.centerx - px) < d]
            self.trees = [t for t in self.trees if abs(t.base_x - px) < d]
            self.medkits = [m for m in self.medkits if m.alive and abs(m.rect.centerx - px) < d]

        # враги обновляются в main loop

    def _spawn(self, cx, cy):
        key = (cx, cy)
        if key in self.spawned:
            return
        self.spawned.add(key)
        x0 = cx * 512
        y0 = cy * 512
        x1 = x0 + 512
        y1 = y0 + 512

        # Деревья
        step = 250
        sx = (x0 // step) * step
        for tx in range(sx, x1 + step, step):
            if _hash(tx // step, 0, 20) > 0.55:
                sy = surface_y(tx)
                if y0 - 200 <= sy <= y1 + 200:
                    self.trees.append(AppleTree(tx, sy))

        # Враги
        dens = self.difficulty.get("enemy_density", 0.4)
        step = 260
        sx = (x0 // step) * step
        for ex in range(sx, x1 + step, step):
            if _hash(ex // step, 0, 30) < dens:
                sy = surface_y(ex)
                if y0 - 28 <= sy - 28 <= y1:
                    self.enemies.append(Enemy(ex, sy - 28))

        # Яблоки в воздухе
        step = 200
        sx = (x0 // step) * step
        for px_ in range(sx, x1 + step, step):
            if _hash(px_ // step, cy, 50) > 0.7:
                sy = surface_y(px_)
                py_ = sy - 100 - int(_hash(px_ // step, 1, 50) * 150)
                if y0 - 20 <= py_ <= y1:
                    self.pixels.append(Pixel(px_, py_))

        # Аптечки
        step = 600
        sx = (x0 // step) * step
        for mx in range(sx, x1 + step, step):
            if _hash(mx // step, 0, 40) > 0.6:
                sy = surface_y(mx)
                if y0 - 40 <= sy - 40 <= y1:
                    self.medkits.append(Medkit(mx, sy - 40))

    def draw_tiles(self, surface, camera):
        for t in self.visible_tiles(camera):
            r = pygame.Rect(t.rect.x - camera.ox, t.rect.y - camera.oy,
                            TILE_SIZE, TILE_SIZE)
            draw_block(surface, r, t.block_type)

    def draw_trees(self, surface, cam):
        for t in self.trees:
            t.draw(surface, cam.ox, cam.oy)

    def draw_entities(self, surface, cam):
        for m in self.medkits:
            m.draw(surface, cam.ox, cam.oy)
        for p in self.pixels:
            p.draw(surface, cam.ox, cam.oy)
        for e in self.enemies:
            e.draw(surface, cam.ox, cam.oy)

    def collect(self):
        """Совместимость со старым API."""
        return [], self.enemies, self.pixels, self.trees, self.medkits


# --- оставляем вспомогательные функции для совместимости ---
def get_ambient_temp(world_y):
    if world_y < SURFACE_Y:
        alt = SURFACE_Y - world_y
        return max(0.0, 100.0 - alt * 0.1)
    depth = world_y - SURFACE_Y
    t = min(1.0, depth / 1500.0)
    return 70.0 + t * 25.0


def weather_zone(world_y):
    if world_y < 200: return "freezing"
    if world_y < 500: return "snow"
    if world_y < 800: return "cold"
    if world_y < SURFACE_Y: return "mild"
    if world_y < SURFACE_Y + 400: return "cave_warm"
    return "cave_hot"
