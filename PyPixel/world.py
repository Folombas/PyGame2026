"""World — фиксированный (скриптованный) мир. Без генерации.

Карта 300x120 тайлов. Всё расставлено вручную по "сценарию".
"""
import math
import pygame
from blocks import (
    TILE_SIZE, AIR, DIRT, GRASS, STONE, COPPER, IRON, GOLD, SAND,
    WATER, SNOW, TORCH, draw_block,
)
from water import WaterSim, draw_water_block
from enemy import Enemy
from collectible import Pixel
from tree import AppleTree
from medkit import Medkit
from chest import Chest
from underwater import Fish, Seaweed, Coral, Turtle, Seahorse, Shark
from ocean import SunkenShip, TempleRuin, PoseidonStatue, Whale, BigShark, Column

TILE = TILE_SIZE
SURFACE_TY = 40                # базовый уровень поверхности
SEA_TY = 38                    # уровень моря
SNOW_LINE_TY = 25              # выше — снег
WORLD_TX = 300                 # ширина мира в тайлах
WORLD_TY = 120                 # высота мира в тайлах
DEATH_TY = 118

WORLD_Y_LAVA = 110


# ============= ГЛАВНАЯ КАРТА (фиксированный рельеф) =============
# Список (start_tx, end_tx, surface_ty) — ступенчатый рельеф
# Всё что между start и end — одна высота
RELIEF = [
    # горы — вверху, с пиками
    (0, 15, 40),     # предгорье
    (15, 25, 30),    # нижние склоны
    (25, 32, 22),    # снежная вершина
    (32, 40, 30),    # обратно вниз
    (40, 50, 40),    # базовый уровень

    # лес
    (50, 70, 40),
    (70, 80, 42),    # чуть ниже — низинка

    # луг (ровный)
    (80, 110, 40),

    # озеро — большая плоская низина
    (110, 150, 55),  # уровень дна озера

    # океан — ГЛУБОКАЯ впадина
    (150, 230, 130), # дно океана (в 3 раза ниже базового!)

    # пляж — поднимается
    (230, 250, 50),

    # восточные холмы
    (250, 270, 40),
    (270, 285, 32),
    (285, 300, 40),
]


def surface_ty(tx):
    """Фиксированная высота поверхности для колонки tx."""
    if tx < 0:
        return SURFACE_TY
    if tx >= WORLD_TX:
        return SURFACE_TY
    for start, end, ty in RELIEF:
        if start <= tx < end:
            return ty
    return SURFACE_TY


def _smooth_surface(tx):
    """Сглаженная версия — интерполяция между колоннами рельефа."""
    # берём surface_ty для tx и усредняем с соседями
    a = surface_ty(tx - 1)
    b = surface_ty(tx)
    c = surface_ty(tx + 1)
    return int((a + b * 2 + c) / 4)


def gen_tile(tx, ty):
    """Тип тайла в (tx, ty). Фиксированная логика."""
    if tx < 0 or tx >= WORLD_TX or ty < 0 or ty >= WORLD_TY:
        return AIR
    st = _smooth_surface(tx)

    if ty < st:
        # Над поверхностью — воздух или вода (в низинах)
        if st > SEA_TY and ty >= SEA_TY:
            return WATER
        return AIR

    depth = ty - st

    # снег на горных вершинах
    if st <= SNOW_LINE_TY and depth < 4:
        return SNOW
    # песок на пляжах (у океана)
    if 230 <= tx < 250 and depth < 3:
        return SAND
    # трава везде остальное
    if depth == 0:
        return GRASS
    if depth < 4:
        return DIRT

    # пещеры — фиксированная сетка
    if depth >= 10:
        # простое детерминированное "псевдо-random" от координат
        n = ((tx * 73 + ty * 131) ^ (tx * ty)) & 0xFF
        if n < 15:  # ~6% блоков — воздух
            return AIR

    # руды
    if depth >= 12:
        n = (tx * 374761393 + ty * 668265263) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        n = n ^ (n >> 16)
        r = (n & 0xFFFFFFFF) / 0xFFFFFFFF
        if r > 0.985: return GOLD
        if r > 0.965: return IRON
        if r > 0.925: return COPPER

    return STONE


# ============= МИР =============
class World:
    DAY_LENGTH = 120.0

    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.mods = {}
        self.trees = []
        self.enemies = []
        self.pixels = []
        self.medkits = []
        self.arrows = []
        self.chests = []
        self.fishes = []
        self.seaweeds = []
        self.corals = []
        self.turtles = []
        self.seahorses = []
        self.sharks = []
        self.ships = []
        self.temples = []
        self.poseidons = []
        self.big_sharks = []
        self.whales = []
        self.time_of_day = 0.30
        self.water_sim = WaterSim()
        self._populate()

    def tick_time(self, dt):
        self.time_of_day = (self.time_of_day + dt / self.DAY_LENGTH) % 1.0

    # ============= РАССТАНОВКА ОБЪЕКТОВ (как декорации) =============
    def _populate(self):
        # --- ДЕРЕВЬЯ в лесу и на лугу ---
        tree_positions = [
            # лес
            (52, 38), (58, 39), (64, 40), (70, 38), (76, 39),
            # луг
            (85, 40), (95, 40), (105, 40),
            # восточные холмы
            (255, 40), (262, 41), (275, 33), (288, 41),
            # предгорье
            (5, 40), (10, 40),
        ]
        for tx, ty in tree_positions:
            st = _smooth_surface(tx)
            if st < ty:  # дерево выше поверхности — ок
                py = st * TILE if st == ty else _smooth_surface(tx) * TILE
            py = _smooth_surface(tx) * TILE
            self.trees.append(AppleTree(tx * TILE, py))

        # --- ВРАГИ на поверхности ---
        enemy_positions = [
            (60, 39), (75, 39), (90, 40), (100, 40),
            (255, 39), (265, 39), (280, 32),
            (10, 40), (20, 40),
        ]
        for tx, ty in enemy_positions:
            st = _smooth_surface(tx)
            py = (st - 1) * TILE
            self.enemies.append(Enemy(tx * TILE, py))

        # --- ПИКСЕЛИ (сборные очки) ---
        pixel_positions = [
            (30, 20), (35, 25),  # у вершин
            (55, 30), (65, 32), (80, 35),  # лес
            (120, 45), (130, 48),  # озеро
            (200, 60), (210, 70),  # под водой в океане
            (240, 45), (250, 42),
        ]
        for tx, ty in pixel_positions:
            self.pixels.append(Pixel(tx * TILE, ty * TILE))

        # --- АПТЕЧКИ ---
        medkit_positions = [
            (45, 39), (95, 39), (240, 49),
        ]
        for tx, ty in medkit_positions:
            self.medkits.append(Medkit(tx * TILE, ty * TILE))

        # --- СУНДУКИ (в пещерах, ниже поверхности) ---
        chest_positions = [
            # в горах глубже
            (20, 60), (28, 55), (35, 65),
            # под лесом
            (60, 70), (75, 75),
            # под лугом
            (90, 65), (100, 80),
            # под океаном — клады на дне
            (180, 128), (200, 130), (220, 125),
        ]
        for tx, ty in chest_positions:
            self.chests.append(Chest(tx * TILE, ty * TILE))

        # --- РЫБЫ в озере и океане ---
        fish_positions = [
            # озеро
            (115, 50, "red"), (125, 48, "yellow"), (135, 52, "blue"),
            (120, 45, "glow"), (130, 50, "red"), (140, 47, "yellow"),
            # океан — много разных на разных глубинах
            (160, 60, "blue"), (170, 70, "glow"), (180, 80, "red"),
            (190, 90, "yellow"), (200, 100, "blue"), (210, 110, "glow"),
            (175, 55, "red"), (195, 65, "yellow"), (215, 75, "blue"),
            (165, 100, "glow"), (185, 105, "red"), (205, 95, "yellow"),
            (220, 85, "blue"), (225, 115, "glow"),
        ]
        for tx, ty, kind in fish_positions:
            self.fishes.append(Fish(tx * TILE, ty * TILE, kind))

        # --- ВОДОРОСЛИ ---
        seaweed_positions = [
            (115, 54), (120, 54), (130, 54), (140, 54),  # озеро дно
            (155, 129), (165, 129), (175, 129), (185, 129),  # океан дно
            (195, 129), (205, 129), (215, 129), (225, 129),
        ]
        for tx, ty in seaweed_positions:
            self.seaweeds.append(Seaweed(tx * TILE, ty * TILE - 4))

        # --- КОРАЛЛЫ ---
        coral_positions = [
            (160, 129), (172, 129), (188, 129), (202, 129), (218, 129),
            (155, 128), (200, 128), (225, 128),
        ]
        for tx, ty in coral_positions:
            self.corals.append(Coral(tx * TILE, ty * TILE - 4))

        # --- ЧЕРЕПАХИ ---
        turtle_positions = [
            (170, 80), (195, 95), (215, 70),
        ]
        for tx, ty in turtle_positions:
            self.turtles.append(Turtle(tx * TILE, ty * TILE))

        # --- МОРСКИЕ КОНЬКИ ---
        seahorse_positions = [
            (150, 120), (175, 122), (200, 125), (220, 122),
        ]
        for tx, ty in seahorse_positions:
            self.seahorses.append(Seahorse(tx * TILE, ty * TILE))

        # --- АКУЛЫ (маленькие, обычные) ---
        shark_positions = [
            (185, 90), (210, 105),
        ]
        for tx, ty in shark_positions:
            self.sharks.append(Shark(tx * TILE - 10, ty * TILE))

        # --- ЗАТОНУВШИЕ КОРАБЛИ (в океане на дне) ---
        # Дно океана около y=129 тайлов
        ship_positions = [
            (165, 128, False),
            (195, 127, True),
            (220, 129, False),
        ]
        for tx, ty, flip in ship_positions:
            self.ships.append(SunkenShip(tx * TILE - 70, ty * TILE - 60))

        # --- РУИНЫ ХРАМОВ АТЛАНТИДЫ ---
        temple_positions = [
            (175, 130),   # большой храм
            (205, 130),   # второй храм
            (155, 130),   # маленький
        ]
        for tx, ty in temple_positions:
            self.temples.append(TempleRuin(tx * TILE, ty * TILE))

        # --- СТАТУЯ ПОСЕЙДОНА (главная достопримечательность) ---
        self.poseidons.append(PoseidonStatue(190 * TILE, 130 * TILE))

        # --- БОЛЬШИЕ АКУЛЫ (патрулируют глубокий океан) ---
        big_shark_positions = [
            (170, 100), (200, 85), (215, 110),
        ]
        for tx, ty in big_shark_positions:
            self.big_sharks.append(BigShark(tx * TILE, ty * TILE))

        # --- КИТЫ (в толще воды океана) ---
        whale_positions = [
            (170, 70), (200, 90), (225, 80),
        ]
        for tx, ty in whale_positions:
            self.whales.append(Whale(tx * TILE, ty * TILE))

    # ============= ДОСТУП К БЛОКАМ =============
    def get_block(self, tx, ty):
        if (tx, ty) in self.mods:
            return self.mods[(tx, ty)]
        return gen_tile(tx, ty)

    def is_solid(self, tx, ty):
        bt = self.get_block(tx, ty)
        return bt != AIR and bt != WATER

    def dig(self, tx, ty):
        bt = self.get_block(tx, ty)
        if bt == AIR or bt == WATER:
            return None
        self.mods[(tx, ty)] = AIR
        return bt

    def place(self, tx, ty, bt):
        cur = self.get_block(tx, ty)
        if cur != AIR and cur != WATER:
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

    # ============= chop_tree =============
    def chop_tree(self, wx, wy, radius_px=150):
        best_i = -1
        best_d = radius_px * radius_px
        for i, t in enumerate(self.trees):
            cx = t.base_x
            cy = t.base_y - 50
            d = (cx - wx) ** 2 + (cy - wy) ** 2
            if d < best_d:
                best_d = d
                best_i = i
        if best_i >= 0:
            t = self.trees.pop(best_i)
            return (t.base_x, t.base_y - 50)
        return None

    # ============= light =============
    def get_light_sources(self, camera):
        sources = []
        cx = camera.offset_x + camera.view_width // 2
        cy = camera.offset_y + camera.view_height // 2
        for (tx, ty), bt in self.mods.items():
            if bt == TORCH:
                wx = tx * TILE + TILE // 2
                wy = ty * TILE + TILE // 2
                if abs(wx - cx) < 900 and abs(wy - cy) < 700:
                    sources.append((wx, wy, 260))
        return sources

    # ============= update =============
    def update(self, camera):
        self.water_sim.update(self, camera)
        for f in self.fishes:
            f.update(self)
        for t in self.turtles:
            t.update(self)
        for s in self.seahorses:
            s.update(self)
        for s in self.seaweeds:
            s.update()
        for c in self.corals:
            c.update()
        for sh in self.sharks:
            if hasattr(self, "_player_ref"):
                sh.update(self, self._player_ref)
        for b in self.big_sharks:
            if hasattr(self, "_player_ref"):
                b.update(self, self._player_ref)
        for w in self.whales:
            w.update(self)
        for s in self.ships:
            s.update(self)
        for t in self.temples:
            t.update(self)
        for p in self.poseidons:
            p.update(self)
        for e in self.enemies:
            e.update(self)

    # ============= DRAW =============
    def draw_tiles(self, screen, camera):
        ox, oy = camera.ox, camera.oy
        tx0 = max(0, ox // TILE - 1)
        ty0 = max(0, oy // TILE - 1)
        tx1 = min(WORLD_TX, (ox + camera.view_width) // TILE + 1)
        ty1 = min(WORLD_TY, (oy + camera.view_height) // TILE + 1)
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

    def draw_underwater(self, screen, camera):
        for s in self.ships:
            s.draw(screen, camera.ox, camera.oy, self)
        for t in self.temples:
            t.draw(screen, camera.ox, camera.oy, self)
        for p in self.poseidons:
            p.draw(screen, camera.ox, camera.oy, self)
        for s in self.seaweeds:
            s.draw(screen, camera.ox, camera.oy, self)
        for c in self.corals:
            c.draw(screen, camera.ox, camera.oy, self)
        for t in self.turtles:
            t.draw(screen, camera.ox, camera.oy, self)
        for s in self.seahorses:
            s.draw(screen, camera.ox, camera.oy, self)

    def draw_entities(self, screen, camera):
        for w in self.whales:
            w.draw(screen, camera.ox, camera.oy, self)
        for f in self.fishes:
            f.draw(screen, camera.ox, camera.oy, self)
        for sh in self.sharks:
            sh.draw(screen, camera.ox, camera.oy, self)
        for b in self.big_sharks:
            b.draw(screen, camera.ox, camera.oy, self)
        for c in self.chests:
            c.draw(screen, camera.ox, camera.oy)

    def draw_trees(self, screen, camera):
        for t in self.trees:
            t.draw(screen, camera.ox, camera.oy)

    def draw_all_entities(self, screen, camera):
        """Деревья + враги + аптечки + пиксели — единый вызов."""
        for t in self.trees:
            t.draw(screen, camera.ox, camera.oy)
        for m in self.medkits:
            m.draw(screen, camera.ox, camera.oy)
        for p in self.pixels:
            p.draw(screen, camera.ox, camera.oy)
        for e in self.enemies:
            e.draw(screen, camera.ox, camera.oy)

    def collect(self):
        return [], self.enemies, self.pixels, self.trees, self.medkits


# ============= УТИЛИТЫ =============
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
    return "deep_ocean"


SURFACE_Y = SURFACE_TY * TILE
DEATH_Y = DEATH_TY * TILE
