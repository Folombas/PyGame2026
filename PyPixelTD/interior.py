"""Интерьер дома (комната внутри)."""
import pygame
from settings import *


class Interior:
    """Отдельный маленький мир — комната."""
    def __init__(self, house_index=0, seed=0):
        self.w = INTERIOR_W
        self.h = INTERIOR_H
        self.house_index = house_index
        # Всё пол, стены по краям
        self.tiles = [[0 for _ in range(self.w)] for _ in range(self.h)]
        # Стены
        for x in range(self.w):
            self.tiles[0][x] = 1
            self.tiles[self.h - 1][x] = 1
        for y in range(self.h):
            self.tiles[y][0] = 1
            self.tiles[y][self.w - 1] = 1
        # Дверь выхода внизу (центр)
        self.exit_tx = self.w // 2
        self.exit_ty = self.h - 1
        self.tiles[self.exit_ty][self.exit_tx] = 2  # дверь
        # Мебель — стол, кровать, ковёр
        self._place_furniture()
        self.cam_offset_x = 0
        self.cam_offset_y = 0

    def _place_furniture(self):
        # Кровать в левом верхнем углу
        self.bed = pygame.Rect(2 * TILE, 2 * TILE, 2 * TILE, 3 * TILE // 2)
        # Стол в центре
        self.table = pygame.Rect((self.w // 2 - 1) * TILE, 3 * TILE, TILE, TILE)
        # Ковёр в центре
        self.rug = pygame.Rect(3 * TILE, 5 * TILE, 4 * TILE, 3 * TILE)
        # Свеча на столе
        self.candle = (self.table.centerx, self.table.top - 4)

    def is_solid(self, tx, ty):
        if tx < 0 or tx >= self.w or ty < 0 or ty >= self.h:
            return True
        t = self.tiles[ty][tx]
        return t == 1  # только стены

    def is_exit(self, tx, ty):
        return (tx == self.exit_tx and ty == self.exit_ty)

    def tile_at(self, tx, ty):
        if tx < 0 or tx >= self.w or ty < 0 or ty >= self.h:
            return 1
        return self.tiles[ty][tx]

    def can_walk(self, px, py, pw, ph):
        """px, py — локальные координаты в комнате."""
        # границы комнаты
        if px < TILE or py < TILE: return False
        if px + pw > (self.w - 1) * TILE: return False
        if py + ph > (self.h - 1) * TILE:
            # Разрешаем пройти в дверь
            tx0 = px // TILE; tx1 = (px + pw - 1) // TILE
            for tx in range(tx0, tx1 + 1):
                if tx == self.exit_tx:
                    # только дверь пускает вниз
                    return True
            return False

        tx0 = px // TILE; ty0 = py // TILE
        tx1 = (px + pw - 1) // TILE; ty1 = (py + ph - 1) // TILE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if self.is_solid(tx, ty):
                    return False
        return True

    def draw(self, screen, cam_x, cam_y):
        for ty in range(self.h):
            for tx in range(self.w):
                t = self.tiles[ty][tx]
                sx = tx * TILE - cam_x
                sy = ty * TILE - cam_y
                if t == 1:
                    # стена
                    pygame.draw.rect(screen, WALL_INTERIOR, (sx, sy, TILE, TILE))
                    pygame.draw.rect(screen, (50, 40, 35), (sx, sy, TILE, TILE), 2)
                elif t == 2:
                    # дверь
                    pygame.draw.rect(screen, DOOR_OPEN, (sx, sy, TILE, TILE))
                    pygame.draw.rect(screen, (60, 35, 20), (sx, sy, TILE, TILE), 2)
                    pygame.draw.rect(screen, (255, 220, 120), (sx + 4, sy + 4, TILE - 8, 4))
                else:
                    # пол
                    pygame.draw.rect(screen, FLOOR_WOOD, (sx, sy, TILE, TILE))
                    pygame.draw.line(screen, FLOOR_WOOD_D, (sx, sy + TILE // 2), (sx + TILE, sy + TILE // 2), 1)
                    pygame.draw.line(screen, FLOOR_WOOD_D, (sx, sy), (sx, sy + TILE), 1)

        # Ковёр
        r = self.rug
        pygame.draw.rect(screen, (140, 60, 80), (r.x - cam_x, r.y - cam_y, r.w, r.h))
        pygame.draw.rect(screen, (180, 90, 110), (r.x - cam_x + 4, r.y - cam_y + 4, r.w - 8, r.h - 8), 2)

        # Кровать
        b = self.bed
        pygame.draw.rect(screen, (130, 60, 60), (b.x - cam_x, b.y - cam_y, b.w, b.h))
        pygame.draw.rect(screen, (200, 200, 220), (b.x - cam_x + 4, b.y - cam_y + 4, b.w - 8, b.h // 2 - 4))
        pygame.draw.rect(screen, (60, 40, 40), (b.x - cam_x, b.y - cam_y, b.w, b.h), 2)

        # Стол
        t = self.table
        pygame.draw.rect(screen, (120, 75, 50), (t.x - cam_x, t.y - cam_y, t.w, t.h))
        pygame.draw.rect(screen, (80, 45, 25), (t.x - cam_x, t.y - cam_y, t.w, t.h), 2)

        # Свеча
        cx = self.candle[0] - cam_x
        cy = self.candle[1] - cam_y
        pygame.draw.rect(screen, (240, 240, 200), (cx - 2, cy, 4, 8))
        # Пламя с пульсацией
        import math
        pulse = abs(math.sin(pygame.time.get_ticks() / 300.0))
        pygame.draw.circle(screen, (255, 180, 60), (cx, cy - 2), int(3 + pulse * 2))
        pygame.draw.circle(screen, (255, 240, 140), (cx, cy - 2), int(1 + pulse))

        # Выход — подсказка
        font = pygame.font.SysFont("monospace", 12, bold=True)
        hint = font.render("Выход (S у двери)", True, (220, 220, 200))
        screen.blit(hint, ((self.exit_tx * TILE) - cam_x - 20, (self.exit_ty * TILE) - cam_y + 34))
