"""Top-down мир: тайлы, дома, деревня."""
import pygame
import assets
from animals import Animal
from settings import *


# Типы тайлов
T_GRASS = 0
T_PATH = 1
T_WATER = 2
T_STONE = 3
T_TREE = 4
T_FLOWER = 5
T_GARDEN_CARROT = 6   # грядка с морковью
T_GARDEN_CABBAGE = 7  # грядка с капустой

SOLID = {T_WATER, T_TREE}


class House:
    """Дом на карте. w_tiles x h_tiles тайлов."""
    def __init__(self, tx, ty, w_tiles=4, h_tiles=3):
        self.tx = tx
        self.ty = ty
        self.w = w_tiles
        self.h = h_tiles
        # дверь — центральный тайл нижней стены
        self.door_tx = tx + w_tiles // 2
        self.door_ty = ty + h_tiles - 1

    def rect_px(self):
        return pygame.Rect(self.tx * TILE, self.ty * TILE,
                           self.w * TILE, self.h * TILE)

    def door_rect_px(self):
        return pygame.Rect(self.door_tx * TILE, self.door_ty * TILE,
                           TILE, TILE)

    def draw(self, surface, offset_x, offset_y):
        x = self.tx * TILE - offset_x
        y = self.ty * TILE - offset_y
        w = self.w * TILE
        h = self.h * TILE

        # Стены
        pygame.draw.rect(surface, HOUSE_WALL, (x, y + h // 3, w, h - h // 3))
        pygame.draw.rect(surface, HOUSE_WALL_D, (x, y + h // 3, w, h - h // 3), 2)
        # Двери
        door_x = self.door_tx * TILE - offset_x
        door_y = self.door_ty * TILE - offset_y
        pygame.draw.rect(surface, DOOR, (door_x + 4, door_y + 6, TILE - 8, TILE - 6))
        pygame.draw.rect(surface, (60, 35, 20), (door_x + 4, door_y + 6, TILE - 8, TILE - 6), 1)
        # Ручка
        pygame.draw.circle(surface, (220, 180, 80), (door_x + TILE - 10, door_y + TILE // 2), 2)

        # Крыша
        pygame.draw.rect(surface, HOUSE_ROOF, (x - 4, y, w + 8, h // 3 + 4))
        pygame.draw.rect(surface, HOUSE_ROOF_D, (x - 4, y, w + 8, h // 3 + 4), 2)
        # Линии черепицы
        for i in range(4):
            ly = y + 6 + i * 8
            pygame.draw.line(surface, HOUSE_ROOF_D, (x - 4, ly), (x + w + 4, ly), 1)

        # Окна
        win_pos = [(x + 10, y + h // 3 + 8), (x + w - 30, y + h // 3 + 8)]
        for wx, wy in win_pos:
            pygame.draw.rect(surface, (80, 50, 30), (wx - 2, wy - 2, 24, 24))
            pygame.draw.rect(surface, WINDOW, (wx, wy, 20, 20))
            pygame.draw.line(surface, (80, 50, 30), (wx + 10, wy), (wx + 10, wy + 20), 1)
            pygame.draw.line(surface, (80, 50, 30), (wx, wy + 10), (wx + 20, wy + 10), 1)


class Villager:
    """NPC на карте."""
    NAMES = ["Фермер", "Кузнец", "Торговец", "Старейшина", "Пастух"]
    SHIRTS = [(200, 80, 80), (80, 160, 200), (200, 180, 80), (140, 90, 200), (100, 200, 120)]

    def __init__(self, tx, ty, idx=0):
        self.tx = tx
        self.ty = ty
        self.name = self.NAMES[idx % len(self.NAMES)]
        self.shirt = self.SHIRTS[idx % len(self.SHIRTS)]
        self.direction = "down"
        self.talking_timer = 0
        self.saying = None

    def rect_px(self):
        return pygame.Rect(self.tx * TILE + 6, self.ty * TILE + 4, 20, 28)

    def draw(self, surface, offset_x, offset_y, font=None):
        from sprites import get_npc_sprite
        sprite = get_npc_sprite(self.shirt, self.direction)
        sx = self.tx * TILE - offset_x + (TILE - sprite.get_width()) // 2
        sy = self.ty * TILE - offset_y + (TILE - sprite.get_height()) // 2
        surface.blit(sprite, (sx, sy))

        # Имя
        if font:
            name_surf = font.render(self.name, True, (255, 240, 180))
            bg = pygame.Surface((name_surf.get_width() + 6, name_surf.get_height() + 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            nx = self.tx * TILE + TILE // 2 - bg.get_width() // 2 - offset_x
            ny = self.ty * TILE - bg.get_height() - 4 - offset_y
            surface.blit(bg, (nx, ny))
            surface.blit(name_surf, (nx + 3, ny + 1))

        # Речь
        if self.saying and font:
            txt = font.render(self.saying, True, (255, 255, 255))
            bw = txt.get_width() + 12; bh = txt.get_height() + 8
            bx = self.tx * TILE + TILE // 2 - bw // 2 - offset_x
            by = self.ty * TILE - bh - 24 - offset_y
            pygame.draw.rect(surface, (30, 25, 50), (bx, by, bw, bh))
            pygame.draw.rect(surface, (200, 200, 220), (bx, by, bw, bh), 2)
            surface.blit(txt, (bx + 6, by + 4))

    def say(self, text, frames=180):
        self.saying = text
        self.talking_timer = frames

    def update(self):
        if self.talking_timer > 0:
            self.talking_timer -= 1
            if self.talking_timer <= 0:
                self.saying = None


class World:
    """Фиксированный top-down мир."""
    def __init__(self):
        self.w = WORLD_W
        self.h = WORLD_H
        # Карта: 2D массив тайлов
        self.tiles = [[T_GRASS for _ in range(self.w)] for _ in range(self.h)]
        self.houses = []
        self.villagers = []
        self.animals = []
        self._build()

    def _build(self):
        # Тропинка от спавна через деревню
        for x in range(15, 45):
            self.tiles[22][x] = T_PATH
            self.tiles[23][x] = T_PATH
        # Поперечная тропа к домам
        for y in range(18, 24):
            for x in [18, 24, 30, 36]:
                self.tiles[y][x] = T_PATH

        # Немного цветов и разнообразия
        import random
        random.seed(42)
        for _ in range(60):
            x = random.randint(2, self.w - 3)
            y = random.randint(2, self.h - 3)
            if self.tiles[y][x] == T_GRASS:
                self.tiles[y][x] = T_FLOWER

        # Деревья вокруг
        for _ in range(120):
            x = random.randint(1, self.w - 2)
            y = random.randint(1, self.h - 2)
            # не рядом со спавном, не на тропе
            if abs(x - 15) < 4 and abs(y - 22) < 4: continue
            if self.tiles[y][x] in (T_PATH, T_FLOWER):
                continue
            self.tiles[y][x] = T_TREE

        # Вода — пруд слева
        for y in range(10, 18):
            for x in range(3, 10):
                self.tiles[y][x] = T_WATER

        # Вода — озеро справа от деревни
        for y in range(25, 33):
            for x in range(42, 52):
                self.tiles[y][x] = T_WATER

        # Камень — немного
        for _ in range(30):
            x = random.randint(2, self.w - 3)
            y = random.randint(2, self.h - 3)
            if self.tiles[y][x] == T_GRASS:
                self.tiles[y][x] = T_STONE

        # ОДИН домик Зайки
        self.houses.append(House(16, 18, 4, 3))

        # Грядки рядом (слева от дома, компактный огород)
        # Морковь — верхний блок
        for gy in range(17, 19):
            for gx in range(10, 14):
                self.tiles[gy][gx] = T_GARDEN_CARROT
        # Капуста — прямо под морковью
        for gy in range(19, 21):
            for gx in range(10, 14):
                self.tiles[gy][gx] = T_GARDEN_CABBAGE

        # Жители — только парочка (прохожие)


        # Животные на лугу — коровы и куры
        self.animals.append(Animal(6, 22, "cow"))
        self.animals.append(Animal(9, 24, "cow"))
        self.animals.append(Animal(3, 25, "cow"))
        self.animals.append(Animal(11, 22, "chicken"))
        self.animals.append(Animal(13, 24, "chicken"))
        self.animals.append(Animal(7, 26, "chicken"))

    # ---- Доступ ----
    def tile_at(self, tx, ty):
        if tx < 0 or tx >= self.w or ty < 0 or ty >= self.h:
            return T_STONE  # стены мира
        return self.tiles[ty][tx]

    def is_solid(self, tx, ty):
        return self.tile_at(tx, ty) in SOLID

    def house_at(self, tx, ty):
        """Если в этом тайле дом — вернуть объект."""
        for h in self.houses:
            if h.tx <= tx < h.tx + h.w and h.ty <= ty < h.ty + h.h:
                return h
        return None

    def can_walk(self, px, py, pw, ph):
        """Может ли игрок с прямоугольником (px,py,pw,ph) стоять тут."""
        tx0 = px // TILE; ty0 = py // TILE
        tx1 = (px + pw - 1) // TILE; ty1 = (py + ph - 1) // TILE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if self.is_solid(tx, ty):
                    return False
                # дом — тоже solid (кроме двери)
                h = self.house_at(tx, ty)
                if h:
                    if tx == h.door_tx and ty == h.door_ty:
                        continue
                    return False
        return True

    # ---- Отрисовка ----
    _real_tiles = {}

    @classmethod
    def next_grass_candidate(cls):
        cls._grass_candidate = (getattr(cls, "_grass_candidate", 0) + 1) % 15
        cls._real_tiles.clear()
        return cls._grass_candidate    # сбросить кеш при перезапуске

    _big_tree_cache = None

    def _get_big_tree(self):
        """Возвращает большое дерево (собранное из 2×2 блока nature.png)."""
        if World._big_tree_cache is not None:
            return World._big_tree_cache

        sheet = assets.load_image("tilesets/nature.png")
        if sheet is None:
            World._big_tree_cache = None
            return None

        # Дерево в nature.png — типично 3×4 тайла (48×64)
        # Попробуем взять область в левом верхнем углу
        big = pygame.Surface((48, 64), pygame.SRCALPHA)
        big.blit(sheet, (0, 0), pygame.Rect(0, 0, 48, 64))
        tree = pygame.transform.scale(big, (96, 128))
        World._big_tree_cache = tree
        return tree

    def _get_real_tile(self, t):
        """Возвращает Surface тайла из assets/ или None."""
        if t in World._real_tiles:
            return World._real_tiles[t]

        # Карта: тип_тайла → (имя_листа, col, row)
        # Фиксированные координаты (из превью)
        coords_set = {
            "grass": (3, 11),   # зелёная трава
            "path":  (3, 1),    # песчаная тропинка
            "water": (18, 4),   # чистая вода из water.png
            "tree":  (2, 2),    # дерево из nature.png (кандидат)
        }
        mapping = {
            T_GRASS: ("floor", coords_set["grass"][0], coords_set["grass"][1]),
            T_PATH:  ("floor", coords_set["path"][0],  coords_set["path"][1]),
            T_WATER: ("water", coords_set["water"][0], coords_set["water"][1]),
        }
        coords = mapping.get(t)
        if coords is None:
            World._real_tiles[t] = None
            return None

        sheet_name, tx, ty = coords
        cache_key = f"_sheet_{sheet_name}"
        if not hasattr(World, cache_key):
            setattr(World, cache_key,
                    assets.load_image(f"tilesets/{sheet_name}.png"))
        sheet = getattr(World, cache_key)
        if sheet is None:
            World._real_tiles[t] = None
            return None

        tile = assets.extract_tile(sheet, tx, ty, 16, 16, scale=2)
        World._real_tiles[t] = tile
        return tile

    def update_animals(self):
        for a in self.animals:
            a.update()

    def draw_animals(self, screen, cam, font_small=None):
        for a in self.animals:
            a.draw(screen, cam.x, cam.y, font_small)

    def draw(self, screen, cam):
        tx0 = max(0, cam.x // TILE - 1)
        ty0 = max(0, cam.y // TILE - 1)
        tx1 = min(self.w, (cam.x + WIDTH) // TILE + 2)
        ty1 = min(self.h, (cam.y + HEIGHT) // TILE + 2)

        for ty in range(ty0, ty1):
            for tx in range(tx0, tx1):
                t = self.tiles[ty][tx]
                sx = tx * TILE - cam.x
                sy = ty * TILE - cam.y
                r = (sx, sy, TILE, TILE)

                # === Пробуем реальный тайл из assets/ ===
                real = self._get_real_tile(t)
                if real is not None:
                    screen.blit(real, (sx, sy))
                    continue

                # Fallback — процедурные тайлы
                if t == T_GRASS:
                    pygame.draw.rect(screen, GRASS, r)
                    # блик
                    pygame.draw.rect(screen, GRASS_L, (sx + 6, sy + 6, 3, 3))
                    pygame.draw.rect(screen, GRASS_D, (sx + 20, sy + 22, 3, 3))
                elif t == T_PATH:
                    pygame.draw.rect(screen, PATH, r)
                    pygame.draw.rect(screen, PATH_D, (sx, sy + 14, TILE, 2))
                elif t == T_WATER:
                    pygame.draw.rect(screen, WATER, r)
                    # волны
                    import math
                    t2 = pygame.time.get_ticks() / 800.0
                    wy = sy + 8 + int(math.sin(tx * 0.5 + t2) * 2)
                    pygame.draw.line(screen, WATER_L, (sx + 4, wy), (sx + TILE - 4, wy), 2)
                elif t == T_STONE:
                    pygame.draw.rect(screen, STONE, r)
                    pygame.draw.rect(screen, (90, 90, 100), (sx + 4, sy + 4, TILE - 8, TILE - 8), 2)
                elif t == T_FLOWER:
                    pygame.draw.rect(screen, GRASS, r)
                    pygame.draw.circle(screen, (240, 180, 200), (sx + TILE // 2, sy + TILE // 2), 4)
                    pygame.draw.circle(screen, (255, 220, 100), (sx + TILE // 2, sy + TILE // 2), 2)
                elif t == T_TREE:
                    pygame.draw.rect(screen, GRASS, r)
                    pygame.draw.ellipse(screen, GRASS_D,
                                        (sx + 4, sy + TILE - 8, TILE - 8, 6))
                    pygame.draw.rect(screen, TREE_TRUNK, (sx + TILE // 2 - 3, sy + TILE - 12, 6, 10))
                    pygame.draw.circle(screen, TREE_LEAF_D, (sx + TILE // 2, sy + TILE // 2 - 2), 12)
                    pygame.draw.circle(screen, TREE_LEAF, (sx + TILE // 2 - 3, sy + TILE // 2 - 4), 9)
                    pygame.draw.circle(screen, (75, 165, 95), (sx + TILE // 2 + 3, sy + TILE // 2 - 6), 6)
                elif t == T_GARDEN_CARROT:
                    # грядка — вспаханная земля + морковка
                    pygame.draw.rect(screen, (110, 75, 50), r)
                    pygame.draw.rect(screen, (80, 55, 35), (sx, sy, TILE, 4))
                    # борозды
                    pygame.draw.line(screen, (70, 45, 30),
                                     (sx, sy + 12), (sx + TILE, sy + 12), 1)
                    pygame.draw.line(screen, (70, 45, 30),
                                     (sx, sy + 22), (sx + TILE, sy + 22), 1)
                    # морковь — зелёные ростки
                    cx = sx + TILE // 2
                    for dx, dy in [(-5, -3), (5, -3), (0, -8), (-3, -10), (3, -10)]:
                        pygame.draw.line(screen, (70, 180, 80),
                                         (cx, sy + 20), (cx + dx, sy + 20 + dy), 2)
                    # оранжевая верхушка морковки виднеется
                    pygame.draw.circle(screen, (240, 130, 50), (cx, sy + 24), 3)
                elif t == T_GARDEN_CABBAGE:
                    # грядка с капустой
                    pygame.draw.rect(screen, (110, 75, 50), r)
                    pygame.draw.rect(screen, (80, 55, 35), (sx, sy, TILE, 4))
                    pygame.draw.line(screen, (70, 45, 30),
                                     (sx, sy + 12), (sx + TILE, sy + 12), 1)
                    pygame.draw.line(screen, (70, 45, 30),
                                     (sx, sy + 22), (sx + TILE, sy + 22), 1)
                    # капуста — круглый зелёный кочан
                    cx = sx + TILE // 2
                    cy = sy + TILE // 2 + 4
                    pygame.draw.circle(screen, (110, 180, 90), (cx, cy), 10)
                    pygame.draw.circle(screen, (150, 210, 120), (cx - 2, cy - 2), 7)
                    pygame.draw.circle(screen, (80, 140, 70), (cx, cy), 10, 1)
                    # прожилки
                    pygame.draw.arc(screen, (80, 140, 70),
                                    (cx - 10, cy - 10, 20, 20),
                                    0.3, 2.8, 1)

        # Дома поверх тайлов
        for h in self.houses:
            h.draw(screen, cam.x, cam.y)

    def draw_villagers(self, screen, cam, font):
        for v in self.villagers:
            v.draw(screen, cam.x, cam.y, font)


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def follow(self, rect, world_w_px, world_h_px):
        tx = rect.centerx - WIDTH // 2
        ty = rect.centery - HEIGHT // 2
        self.x = max(0, min(tx, world_w_px - WIDTH))
        self.y = max(0, min(ty, world_h_px - HEIGHT))
