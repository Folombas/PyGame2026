"""Декоративная поверхность: травинки, без заливки (блоки теперь главные)."""
import pygame
from world import surface_y


def draw_terrain_polygon(screen, camera):
    """Тонкая зелёная кромка поверх блоков — визуальный акцент."""
    ox = camera.offset_x
    oy = camera.offset_y
    step = 8

    x_start = int(ox) - step
    x_end = int(ox) + camera.view_width + step

    points = []
    x = x_start
    while x <= x_end:
        sy = surface_y(x)
        points.append((x - ox, sy - oy))
        x += step

    if len(points) < 2:
        return

    # Только тонкая травяная полоска (5px) — блоки под ней всё равно видны
    grass_poly = points + [(px, py + 5) for px, py in reversed(points)]
    pygame.draw.polygon(screen, (85, 175, 75), grass_poly)
    # тёмная линия снизу полоски
    pygame.draw.lines(screen, (55, 140, 55), False,
                      [(px, py + 5) for px, py in points], 1)


def draw_surface_details(screen, camera):
    """Травинки, торчащие над поверхностью."""
    from world import _hash
    ox = camera.offset_x
    oy = camera.offset_y
    step = 8
    x_start = int(ox) - step
    x_end = int(ox) + camera.view_width + step
    x = (x_start // step) * step
    while x <= x_end:
        if _hash(x // step, 0, 100) > 0.7:
            sy = surface_y(x)
            sx = x - ox
            sy_screen = sy - oy
            h = 4 + int(_hash(x // step, 1, 100) * 4)
            pygame.draw.line(screen, (55, 140, 55),
                             (sx, sy_screen), (sx, sy_screen - h), 1)
        x += step
