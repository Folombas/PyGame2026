"""Интерьер дома зайки: кровать, диван, стол с ПК, стул, цветок."""
import pygame
from radio import Radio
from settings import *


class Interior:
    def __init__(self, house_index=0):
        self.w = 16
        self.h = 12
        self.house_index = house_index
        self.tiles = [[0 for _ in range(self.w)] for _ in range(self.h)]
        # Стены по краям
        for x in range(self.w):
            self.tiles[0][x] = 1
            self.tiles[self.h - 1][x] = 1
        for y in range(self.h):
            self.tiles[y][0] = 1
            self.tiles[y][self.w - 1] = 1
        # Дверь снизу по центру
        self.exit_tx = self.w // 2
        self.exit_ty = self.h - 1
        self.tiles[self.exit_ty][self.exit_tx] = 2

        # ---- МЕБЕЛЬ (компактно) ----
        # Кровать — левый верх
        self.bed = pygame.Rect(1 * TILE, 1 * TILE, 3 * TILE, 2 * TILE)
        # Диван — правый верх
        self.sofa = pygame.Rect(11 * TILE, 1 * TILE, 4 * TILE, TILE + 8)
        # Тумбочка рядом с диваном (слева от дивана)
        self.nightstand = pygame.Rect(9 * TILE, 1 * TILE, 2 * TILE, TILE + 8)
        # Радио на тумбочке
        self.radio = Radio(10 * TILE, 2 * TILE + 8)
        # Стол с ПК — центр-низ
        self.desk = pygame.Rect(7 * TILE, 8 * TILE, 3 * TILE, TILE + 8)
        # Стул перед столом
        self.chair = pygame.Rect(8 * TILE, 10 * TILE + 4, TILE, TILE - 4)
        # Монитор на столе
        self.monitor = pygame.Rect(7 * TILE - 4, self.desk.y - 26, TILE + 12, 28)
        # Цветок — правый низ
        self.flower_pos = (14 * TILE, 9 * TILE + 16)
        # Ковёр — центр
        self.rug = pygame.Rect(5 * TILE, 4 * TILE, 6 * TILE, 3 * TILE)
        # Коврик у кровати
        self.rug2 = pygame.Rect(1 * TILE, 4 * TILE, 3 * TILE, 2 * TILE)

        self.pc_on = False
        self.pc_boot_timer = 0
        self.sitting = False


    def is_solid(self, tx, ty):
        if tx < 0 or tx >= self.w or ty < 0 or ty >= self.h:
            return True
        return self.tiles[ty][tx] == 1

    def is_exit(self, tx, ty):
        return tx == self.exit_tx and ty == self.exit_ty

    def tile_at(self, tx, ty):
        if tx < 0 or tx >= self.w or ty < 0 or ty >= self.h:
            return 1
        return self.tiles[ty][tx]

    def can_walk(self, px, py, pw, ph):
        if px < TILE or py < TILE: return False
        if px + pw > (self.w - 1) * TILE: return False
        if py + ph > (self.h - 1) * TILE:
            tx0 = px // TILE; tx1 = (px + pw - 1) // TILE
            for tx in range(tx0, tx1 + 1):
                if tx == self.exit_tx:
                    return True
            return False
        tx0 = px // TILE; ty0 = py // TILE
        tx1 = (px + pw - 1) // TILE; ty1 = (py + ph - 1) // TILE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if self.is_solid(tx, ty):
                    return False
        return True

    def chair_rect(self):
        return self.chair.inflate(20, 20)

    def update(self, dt):
        if self.pc_boot_timer > 0:
            self.pc_boot_timer -= dt * 60
        if hasattr(self, "radio"):
            self.radio.update()

    def draw(self, screen, cam_x, cam_y, font_small=None):
        # ---- Тайлы ----
        for ty in range(self.h):
            for tx in range(self.w):
                t = self.tiles[ty][tx]
                sx = tx * TILE - cam_x
                sy = ty * TILE - cam_y
                if t == 1:
                    # стена — обои
                    pygame.draw.rect(screen, (140, 100, 130), (sx, sy, TILE, TILE))
                    pygame.draw.rect(screen, (90, 60, 90), (sx, sy, TILE, TILE), 2)
                    # полоски
                    pygame.draw.line(screen, (110, 75, 105), (sx + 8, sy), (sx + 8, sy + TILE), 1)
                    pygame.draw.line(screen, (110, 75, 105), (sx + 22, sy), (sx + 22, sy + TILE), 1)
                elif t == 2:
                    # дверь
                    pygame.draw.rect(screen, DOOR_OPEN, (sx, sy, TILE, TILE))
                    pygame.draw.rect(screen, (60, 35, 20), (sx, sy, TILE, TILE), 2)
                    pygame.draw.rect(screen, (255, 220, 120), (sx + 4, sy + 4, TILE - 8, 4))
                else:
                    # пол — деревянные доски
                    pygame.draw.rect(screen, FLOOR_WOOD, (sx, sy, TILE, TILE))
                    pygame.draw.line(screen, FLOOR_WOOD_D,
                                     (sx, sy + TILE // 2), (sx + TILE, sy + TILE // 2), 1)
                    pygame.draw.line(screen, FLOOR_WOOD_D, (sx, sy), (sx, sy + TILE), 1)

        # ---- Ковёр главный ----
        r = self.rug
        pygame.draw.rect(screen, (150, 60, 80), (r.x - cam_x, r.y - cam_y, r.w, r.h))
        pygame.draw.rect(screen, (200, 90, 110), (r.x - cam_x + 6, r.y - cam_y + 6, r.w - 12, r.h - 12), 2)
        pygame.draw.rect(screen, (170, 70, 90), (r.x - cam_x + 14, r.y - cam_y + 14, r.w - 28, r.h - 28), 2)
        # Второй коврик
        r2 = self.rug2
        pygame.draw.rect(screen, (60, 120, 100), (r2.x - cam_x, r2.y - cam_y, r2.w, r2.h))
        pygame.draw.rect(screen, (100, 180, 150), (r2.x - cam_x + 4, r2.y - cam_y + 4, r2.w - 8, r2.h - 8), 2)

        # ---- Кровать ----
        b = self.bed
        pygame.draw.rect(screen, (110, 55, 55), (b.x - cam_x, b.y - cam_y, b.w, b.h))
        pygame.draw.rect(screen, (60, 35, 35), (b.x - cam_x, b.y - cam_y, b.w, b.h), 2)
        # Матрас
        pygame.draw.rect(screen, (240, 240, 250),
                         (b.x - cam_x + 4, b.y - cam_y + 4, b.w - 8, b.h - 20))
        # Подушка
        pygame.draw.ellipse(screen, (255, 255, 255),
                            (b.x - cam_x + 8, b.y - cam_y + 6, b.w - 16, 16))
        # Одеяло
        pygame.draw.rect(screen, (100, 160, 220),
                         (b.x - cam_x + 4, b.y - cam_y + 26, b.w - 8, b.h - 30))
        # Полоски одеяла
        for i in range(3):
            yy = b.y - cam_y + 34 + i * 8
            pygame.draw.line(screen, (70, 130, 190),
                             (b.x - cam_x + 6, yy), (b.x - cam_x + b.w - 6, yy), 1)

        # ---- Диван ----
        s = self.sofa
        # Спинка
        pygame.draw.rect(screen, (140, 70, 60), (s.x - cam_x, s.y - cam_y, s.w, 14))
        # Сидение
        pygame.draw.rect(screen, (170, 90, 80),
                         (s.x - cam_x, s.y - cam_y + 10, s.w, s.h - 10))
        pygame.draw.rect(screen, (80, 40, 35), (s.x - cam_x, s.y - cam_y, s.w, s.h), 2)
        # Подушки
        for i in range(2):
            px = s.x - cam_x + 6 + i * (s.w // 2)
            pygame.draw.rect(screen, (200, 120, 110), (px, s.y - cam_y + 4, s.w // 2 - 10, 12))
            pygame.draw.rect(screen, (80, 40, 35), (px, s.y - cam_y + 4, s.w // 2 - 10, 12), 1)

        # ---- Тумбочка ----
        ns = self.nightstand
        # Тень
        pygame.draw.ellipse(screen, (0, 0, 0, 80),
                            (ns.x - cam_x + 4, ns.bottom - cam_y - 4, ns.w - 8, 6))
        # Корпус
        pygame.draw.rect(screen, (130, 85, 50),
                         (ns.x - cam_x, ns.y - cam_y, ns.w, ns.h))
        pygame.draw.rect(screen, (60, 40, 25),
                         (ns.x - cam_x, ns.y - cam_y, ns.w, ns.h), 2)
        # Верхняя крышка
        pygame.draw.rect(screen, (170, 120, 75),
                         (ns.x - cam_x, ns.y - cam_y, ns.w, 6))
        pygame.draw.rect(screen, (60, 40, 25),
                         (ns.x - cam_x, ns.y - cam_y, ns.w, 6), 1)
        # Ручка
        pygame.draw.rect(screen, (200, 180, 120),
                         (ns.centerx - cam_x - 6, ns.centery - cam_y + 4, 12, 3))
        # Ящик
        pygame.draw.rect(screen, (100, 60, 35),
                         (ns.x - cam_x + 4, ns.y - cam_y + 16, ns.w - 8, ns.h - 26))
        pygame.draw.rect(screen, (60, 40, 25),
                         (ns.x - cam_x + 4, ns.y - cam_y + 16, ns.w - 8, ns.h - 26), 1)

        # ---- Радиоприёмник ----
        self.radio.draw(screen, cam_x, cam_y)

        # ---- Стол ----
        d = self.desk
        pygame.draw.rect(screen, (130, 80, 50), (d.x - cam_x, d.y - cam_y, d.w, d.h))
        pygame.draw.rect(screen, (80, 45, 25), (d.x - cam_x, d.y - cam_y, d.w, d.h), 2)
        # Ножки
        for lx in (d.x + 4, d.x + d.w - 10):
            pygame.draw.rect(screen, (80, 45, 25), (lx - cam_x, d.y - cam_y + d.h - 4, 6, 8))

        # ---- Монитор ----
        m = self.monitor
        # Подставка
        pygame.draw.rect(screen, (30, 30, 40), (m.centerx - cam_x - 4, m.bottom - cam_y, 8, 6))
        pygame.draw.rect(screen, (30, 30, 40), (m.centerx - cam_x - 10, m.bottom - cam_y - 2, 20, 4))
        # Корпус монитора
        pygame.draw.rect(screen, (40, 40, 50), (m.x - cam_x, m.y - cam_y, m.w, m.h))
        pygame.draw.rect(screen, (60, 60, 75), (m.x - cam_x, m.y - cam_y, m.w, m.h), 2)
        # Экран
        screen_rect = pygame.Rect(m.x - cam_x + 3, m.y - cam_y + 3, m.w - 6, m.h - 8)
        if self.pc_on:
            # Синее свечение
            glow = pygame.Surface((m.w + 30, m.h + 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 140, 220, 80), (glow.get_width() // 2, glow.get_height() // 2), 30)
            screen.blit(glow, (m.x - cam_x - 15, m.y - cam_y - 15))
            # Синий экран
            pygame.draw.rect(screen, (40, 100, 180), screen_rect)
            # Иконка зайки на экране
            pygame.draw.circle(screen, (250, 240, 220),
                               (screen_rect.centerx, screen_rect.centery), 4)
            pygame.draw.circle(screen, (240, 150, 170),
                               (screen_rect.centerx - 2, screen_rect.centery - 4), 1)
            pygame.draw.circle(screen, (240, 150, 170),
                               (screen_rect.centerx + 2, screen_rect.centery - 4), 1)
        else:
            # Чёрный экран
            pygame.draw.rect(screen, (10, 10, 15), screen_rect)
            # Блик
            pygame.draw.line(screen, (30, 30, 40), (screen_rect.x + 4, screen_rect.y + 4),
                             (screen_rect.x + 12, screen_rect.y + 12), 1)

        # ---- Стул ----
        c = self.chair
        # Сидение
        pygame.draw.rect(screen, (100, 60, 40), (c.x - cam_x, c.y - cam_y + 8, c.w, c.h - 8))
        pygame.draw.rect(screen, (60, 35, 20), (c.x - cam_x, c.y - cam_y + 8, c.w, c.h - 8), 2)
        # Спинка
        pygame.draw.rect(screen, (100, 60, 40), (c.x - cam_x, c.y - cam_y, c.w, 10))
        pygame.draw.rect(screen, (60, 35, 20), (c.x - cam_x, c.y - cam_y, c.w, 10), 2)

        # ---- Цветок ----
        fx, fy = self.flower_pos
        fx -= cam_x
        fy -= cam_y
        # Горшок
        pygame.draw.polygon(screen, (180, 90, 60), [
            (fx - 10, fy + 8), (fx + 10, fy + 8), (fx + 8, fy + 22), (fx - 8, fy + 22)])
        pygame.draw.polygon(screen, (120, 60, 40), [
            (fx - 10, fy + 8), (fx + 10, fy + 8), (fx + 8, fy + 22), (fx - 8, fy + 22)], 2)
        # Земля
        pygame.draw.rect(screen, (80, 50, 30), (fx - 8, fy + 6, 16, 4))
        # Стебель
        pygame.draw.line(screen, (60, 140, 70), (fx, fy + 8), (fx, fy - 14), 2)
        # Листья
        pygame.draw.ellipse(screen, (80, 180, 90), (fx - 12, fy - 6, 10, 6))
        pygame.draw.ellipse(screen, (80, 180, 90), (fx + 2, fy - 10, 10, 6))
        # Цветок
        import math
        pulse = math.sin(pygame.time.get_ticks() / 500.0) * 0.2 + 1
        for ang in range(0, 360, 60):
            r = math.radians(ang)
            hx = fx + math.cos(r) * 6 * pulse
            hy = fy - 14 + math.sin(r) * 6 * pulse
            pygame.draw.circle(screen, (240, 120, 160), (int(hx), int(hy)), 4)
        pygame.draw.circle(screen, (250, 220, 80), (fx, fy - 14), 4)

        # ---- Подсказка "Стол с ПК" ----
        if font_small:
            if self.sitting and not self.pc_on:
                hint = font_small.render("E — включить ПК", True, (255, 240, 120))
            elif self.sitting and self.pc_on:
                hint = font_small.render("E — выключить ПК", True, (255, 200, 100))
            else:
                hint = None
            if hint:
                bx = self.monitor.centerx - cam_x - hint.get_width() // 2
                by = self.monitor.y - cam_y - 20
                bg = pygame.Surface((hint.get_width() + 10, hint.get_height() + 4), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 180))
                screen.blit(bg, (bx - 5, by - 2))
                screen.blit(hint, (bx, by))
