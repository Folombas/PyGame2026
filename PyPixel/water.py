import pygame
"""Простая симуляция воды: клеточный автомат на тайлах."""
import random
from blocks import TILE_SIZE, AIR, WATER


class WaterSim:
    """Простой автомат: вода стекает вниз, растекается в стороны.

    Обновляем каждые N кадров, обрабатываем bottom-up чтобы не телепортировать.
    """
    def __init__(self):
        self.tick = 0
        self.INTERVAL = 4       # каждые 4 кадра
        self.FLOW_SPEED = 0.5   # вероятность растечься (0..1)

    def update(self, world, camera):
        self.tick += 1
        if self.tick % self.INTERVAL != 0:
            return

        ox = camera.ox
        oy = camera.oy
        tx0 = max(-1000, ox // TILE_SIZE - 1)
        ty0 = max(-1000, oy // TILE_SIZE - 1)
        tx1 = (ox + camera.view_width) // TILE_SIZE + 1
        ty1 = (oy + camera.view_height) // TILE_SIZE + 1

        # Собираем активные клетки с водой
        to_process = []
        for ty in range(ty1, ty0 - 1, -1):        # bottom-up
            for tx in range(tx0, tx1 + 1):
                if world.get_block(tx, ty) == WATER:
                    to_process.append((tx, ty))

        moved = set()
        for tx, ty in to_process:
            if (tx, ty) in moved:
                continue

            # 1) вниз
            if world.get_block(tx, ty + 1) == AIR:
                world.mods[(tx, ty + 1)] = WATER
                world.mods[(tx, ty)] = AIR
                moved.add((tx, ty + 1))
                continue

            # 2) в стороны — рандомно, чтобы не было смещения
            dirs = [-1, 1]
            random.shuffle(dirs)
            for dx in dirs:
                if random.random() > self.FLOW_SPEED:
                    continue
                if world.get_block(tx + dx, ty) == AIR:
                    # только если под "целью" есть вода или блок (не парит)
                    below = world.get_block(tx + dx, ty + 1)
                    if below != AIR:  # ставим на опору
                        world.mods[(tx + dx, ty)] = WATER
                        world.mods[(tx, ty)] = AIR
                        moved.add((tx + dx, ty))
                        break

    def player_in_water(self, world, rect):
        """True если прямоугольник игрока пересекается с водой."""
        tx0 = rect.left // TILE_SIZE
        ty0 = rect.top // TILE_SIZE
        tx1 = (rect.right - 1) // TILE_SIZE
        ty1 = (rect.bottom - 1) // TILE_SIZE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if world.get_block(tx, ty) == WATER:
                    return True
        return False


# ---- отрисовка воды с волнами ----
_wave_offset = 0.0

def draw_water_block(surface, rect, is_surface, t=0.0):
    """Синяя полупрозрачная вода. Волны если это поверхность."""
    import math
    x, y, w, h = rect.x, rect.y, rect.w, rect.h

    # тело воды — синий, слегка прозрачный
    body = (30, 90, 150)
    pygame_surf = surface
    pygame.draw.rect(pygame_surf, body, rect)

    # поверхностная рябь — если над водой воздух
    if is_surface:
        # двойная волна
        for offset, col, thick in [(0, (60, 140, 200), 2), (3, (150, 230, 255), 2)]:
            points = []
            for i in range(0, w + 1, 3):
                wy = y + 2 + offset + int(math.sin((x + i) * 0.20 + t * 1.5) * 2.5)
                points.append((x + i, wy))
            if len(points) >= 2:
                pygame.draw.lines(pygame_surf, col, False, points, thick)
        # блики
        for i in range(0, w, 8):
            bx = x + i + int((t * 30) % 8)
            by = y + 4 + int(math.sin((x + i) * 0.2 + t) * 2)
            pygame.draw.rect(pygame_surf, (200, 240, 255), (bx, by, 3, 1))

    # лёгкий светлый блик в середине
    pygame.draw.rect(pygame_surf, (50, 130, 190), (x, y + h // 2, w, 2))

