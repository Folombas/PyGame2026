"""World — тайловый мир 32×32 с процедурной генерацией.

Единая система координат:
  • Всё в ТАЙЛАХ (tx, ty). Пиксели = tx * TILE.
  • surface_ty(tx) — Y ВЕРХНЕГО твёрдого тайла в колонке.
  • Пещеры генерируются ТОЛЬКО глубоко (depth >= 8), чтобы поверхность была плотной.
"""
import pygame
from blocks import (
    TILE_SIZE, AIR, DIRT, GRASS, STONE, COPPER, IRON, GOLD, SAND, WATER,
    draw_block,
)
from water import WaterSim, draw_water_block
from enemy import Enemy
from collectible import Pixel
from tree import AppleTree
from medkit import Medkit

TILE = TILE_SIZE
SURFACE_TY = 40                # базовый уровень поверхности (в тайлах)
SEA_TY = 43                    # уровень моря — ниже этой линии низины заполняются водой
DEATH_TY = SURFACE_TY + 55     # ниже — смерть (в тайлах)


# ============ ШУМЫ ============
def _h(x, y, seed=0):
    n = (int(x) * 374761393 + int(y) * 668265263 + int(seed) * 1274126177) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFFFF) / 0xFFFFFFFF


def _s1d(x, scale, seed=0):
    xf = x / scale
    x0 = int(xf)
    if xf < 0:
        x0 -= 1
    t = xf - x0
    t = t * t * (3 - 2 * t)
    a = _h(x0, 0, seed)
    b = _h(x0 + 1, 0, seed)
    return a * (1 - t) + b * t


def _s2d(x, y, scale, seed=0):
    xf = x / scale
    yf = y / scale
    x0 = int(xf); y0 = int(yf)
    if xf < 0: x0 -= 1
    if yf < 0: y0 -= 1
    tx = xf - x0; ty = yf - y0
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    a = _h(x0,     y0,     seed)
    b = _h(x0 + 1, y0,     seed)
    c = _h(x0,     y0 + 1, seed)
    d = _h(x0 + 1, y0 + 1, seed)
    ab = a + (b - a) * tx
    cd = c + (d - c) * tx
    return ab + (cd - ab) * ty


# ============ ГЕНЕРАЦИЯ ============
def surface_ty(tx):
    """Y ВЕРХНЕГО твёрдого тайла в колонке tx (в тайлах)."""
    base = SURFACE_TY
    base += int((_s1d(tx, 12, 1) - 0.5) * 3)   # холмы ±3 тайла
    base += int((_s1d(tx, 5, 2) - 0.5) * 1.5)  # мелкие кочки
    # горы — редкие высокие пики
    m = _s1d(tx, 25, 10)
    if m > 0.68:
        t = (m - 0.68) / 0.32
        base -= int(t * t * 22)     # до 22 тайлов вверх (704 px)
    return base


def gen_tile(tx, ty):
    st = surface_ty(tx)
    if ty < st:
        # Низина ниже уровня моря → вода
        if ty >= SEA_TY:
            return WATER
        return AIR
    depth = ty - st

    if depth == 0:
        return SAND if st < 20 else GRASS
    if depth < 4:
        return DIRT

    # пещеры — только с depth >= 8
    if depth >= 8:
        cave = (_s2d(tx, ty, 8, 5) * 0.55
                + _s2d(tx, ty, 4, 6) * 0.45)
        # чем глубже, тем больше пустот
        bias = min(0.22, (depth - 8) / 60.0)
        if cave > 0.62 - bias:
            return AIR

    # руды на глубине
    if depth >= 10:
        r = _h(tx, ty, 42)
        if r > 0.988: return GOLD
        if r > 0.965: return IRON
        if r > 0.925: return COPPER

    return STONE


# ============ МИР ============
class World:
    DAY_LENGTH = 30.0        # секунд на полный цикл

    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.mods = {}          # (tx,ty) -> block_type
        self.trees = []
        self.enemies = []
        self.pixels = []
        self.medkits = []
        self.arrows = []
        self._spawned = set()
        self._last_chunk = None
        self.time_of_day = 0.78   # старт — утро
        self.torches = []         # [(wx, wy), ...] — для света
        self.water_sim = WaterSim()

    def tick_time(self, dt):
        self.time_of_day = (self.time_of_day + dt / self.DAY_LENGTH) % 1.0

    def get_light_sources(self, camera):
        """Возвращает список (wx, wy, radius_px) видимых источников."""
        sources = []
        # факелы в модах
        for (tx, ty), bt in self.mods.items():
            if bt == 13:  # TORCH
                wx = tx * TILE + TILE // 2
                wy = ty * TILE + TILE // 2
                # отсев
                if (abs(wx - (camera.offset_x + camera.view_width // 2)) < 900 and
                        abs(wy - (camera.offset_y + camera.view_height // 2)) < 700):
                    sources.append((wx, wy, 180))
        return sources

    # --- доступ к блокам ---
    def get_block(self, tx, ty):
        if (tx, ty) in self.mods:
            return self.mods[(tx, ty)]
        return gen_tile(tx, ty)

    def is_solid(self, tx, ty):
        bt = self.get_block(tx, ty)
        return bt != AIR and bt != WATER

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
        tx0 = int(px) // TILE
        ty0 = int(py) // TILE
        tx1 = int(px + w - 1) // TILE
        ty1 = int(py + h - 1) // TILE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if self.is_solid(tx, ty):
                    return True
        return False

    # --- чанки (спавн сущностей) ---
    def update(self, camera):
        # вода — до всего
        self.water_sim.update(self, camera)
        cx = int(camera.offset_x + camera.view_width // 2) // 512
        cy = int(camera.offset_y + camera.view_height // 2) // 512
        if (cx, cy) == self._last_chunk:
            return
        self._last_chunk = (cx, cy)

        for dx in range(-2, 3):
            for dy in range(-2, 3):
                self._spawn(cx + dx, cy + dy)

        # деспавн
        px = camera.offset_x + camera.view_width // 2
        py = camera.offset_y + camera.view_height // 2
        d = 2200
        self.enemies = [e for e in self.enemies
                        if abs(e.rect.centerx - px) < d and abs(e.rect.centery - py) < d]
        self.trees = [t for t in self.trees if abs(t.base_x - px) < d]
        self.medkits = [m for m in self.medkits
                        if m.alive and abs(m.rect.centerx - px) < d]
        self.pixels = [p for p in self.pixels
                       if p.alive and abs(p.rect.centerx - px) < d]

    def _spawn(self, cx, cy):
        key = (cx, cy)
        if key in self._spawned:
            return
        self._spawned.add(key)
        x0 = cx * 512; x1 = x0 + 512
        y0 = cy * 512; y1 = y0 + 512

        # --- деревья на поверхности ---
        step = 180
        sx = (x0 // step) * step
        for wx in range(sx, x1 + step, step):
            if _h(wx // step, 0, 20) > 0.55:
                tx = wx // TILE
                sty = surface_ty(tx)
                py = sty * TILE
                if y0 - 250 < py < y1 + 250:
                    self.trees.append(AppleTree(wx, py))

        # --- враги на поверхности ---
        dens = self.difficulty.get("enemy_density", 0.4)
        step = 280
        sx = (x0 // step) * step
        for wx in range(sx, x1 + step, step):
            if _h(wx // step, 0, 30) < dens:
                tx = wx // TILE
                sty = surface_ty(tx)
                py = (sty - 1) * TILE
                if y0 - 40 < py < y1 + 40:
                    self.enemies.append(Enemy(wx, py))

        # --- пиксели-очки ---
        step = 200
        sx = (x0 // step) * step
        for wx in range(sx, x1 + step, step):
            if _h(wx // step, cy, 50) > 0.72:
                tx = wx // TILE
                sty = surface_ty(tx)
                py = sty * TILE - 100 - int(_h(wx // step, 1, 50) * 140)
                if y0 - 20 < py < y1:
                    self.pixels.append(Pixel(wx, py))

        # --- аптечки ---
        step = 500
        sx = (x0 // step) * step
        for wx in range(sx, x1 + step, step):
            if _h(wx // step, 0, 40) > 0.65:
                tx = wx // TILE
                sty = surface_ty(tx)
                py = (sty - 1) * TILE - 6
                if y0 - 40 < py < y1:
                    self.medkits.append(Medkit(wx, py))

    # --- отрисовка ---
    def draw_tiles(self, screen, camera):
        ox, oy = camera.ox, camera.oy
        tx0 = ox // TILE - 1
        ty0 = oy // TILE - 1
        tx1 = (ox + camera.view_width) // TILE + 1
        ty1 = (oy + camera.view_height) // TILE + 1
        t = pygame.time.get_ticks() / 1000.0
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                bt = self.get_block(tx, ty)
                if bt == AIR:
                    continue
                r = pygame.Rect(tx * TILE - ox, ty * TILE - oy, TILE, TILE)
                if bt == WATER:
                    is_surface = (self.get_block(tx, ty - 1) == AIR)
                    draw_water_block(screen, r, is_surface, t)
                else:
                    draw_block(screen, r, bt)

    def draw_entities(self, screen, camera):
        for t in self.trees:
            t.draw(screen, camera.ox, camera.oy)
        for m in self.medkits:
            m.draw(screen, camera.ox, camera.oy)
        for p in self.pixels:
            p.draw(screen, camera.ox, camera.oy)
        for e in self.enemies:
            e.draw(screen, camera.ox, camera.oy)
        for a in self.arrows:
            a.draw(screen, camera.ox, camera.oy)

    def collect(self):
        return [], self.enemies, self.pixels, self.trees, self.medkits


# ============ УТИЛИТЫ ДЛЯ MAIN ============
def get_ambient_temp(world_y):
    sy = SURFACE_TY * TILE
    if world_y < sy:
        alt = sy - world_y
        return max(0.0, 100.0 - alt * 0.1)
    depth = world_y - sy
    t = min(1.0, depth / 1500.0)
    return 70.0 + t * 25.0


def weather_zone(world_y):
    sy = SURFACE_TY * TILE
    if world_y < sy - 900: return "freezing"
    if world_y < sy - 600: return "snow"
    if world_y < sy - 300: return "cold"
    if world_y < sy:       return "mild"
    if world_y < sy + 400: return "cave_warm"
    return "cave_hot"


# Совместимость
SURFACE_Y = SURFACE_TY * TILE
DEATH_Y = DEATH_TY * TILE
