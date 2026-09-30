"""Сглаженный рельеф: рисуем поверхность как многоугольник, а не колонны."""
import pygame
from world import surface_y, is_cave, COLUMN_W


GROUND_COLOR = (120, 80, 50)
GROUND_DARK = (75, 50, 30)
GRASS_COLOR = (85, 175, 75)
GRASS_DARK = (55, 140, 55)
STONE_COLOR = (90, 80, 75)
CAVE_BG = (28, 16, 12)


def draw_terrain_polygon(screen, camera):
    """Рисует поверхность земли как сглаженный многоугольник."""
    ox = camera.offset_x
    oy = camera.offset_y
    step = 16   # меньший шаг — глаже

    # Сэмплируем точки поверхности слева и справа от экрана
    x_start = int(ox) - step
    x_end = int(ox) + camera.view_width + step

    points = []
    x = x_start
    while x <= x_end:
        sy = surface_y(x)
        sx = x - ox
        sy_screen = sy - oy
        points.append((sx, sy_screen))
        x += step

    if not points:
        return

    # Замкнутый многоугольник: сверху по поверхности, снизу — до конца экрана
    poly = points + [(x_end - ox, camera.view_height + 50),
                     (x_start - ox, camera.view_height + 50)]

    # Тело земли
    pygame.draw.polygon(screen, GROUND_COLOR, poly)

    # Трава — тонкая полоска поверх поверхности
    grass_thickness = 8
    grass_poly = points + [(x, y + grass_thickness) for x, y in reversed(points)]
    pygame.draw.polygon(screen, GRASS_COLOR, grass_poly)

    # Тёмная линия между травой и землёй
    pygame.draw.lines(screen, GROUND_DARK, False,
                      [(x, y + grass_thickness) for x, y in points], 2)


def draw_surface_details(screen, camera):
    """Травинки и мелкие камни на поверхности."""
    ox = camera.offset_x
    oy = camera.offset_y
    from world import _hash
    step = 8
    x_start = int(ox) - step
    x_end = int(ox) + camera.view_width + step
    x = (x_start // step) * step
    while x <= x_end:
        if _hash(x // step, 0, 100) > 0.7:
            sy = surface_y(x)
            sx = x - ox
            sy_screen = sy - oy
            # травинка
            h = 4 + int(_hash(x // step, 1, 100) * 4)
            pygame.draw.line(screen, GRASS_DARK,
                             (sx, sy_screen), (sx, sy_screen - h), 1)
        x += step
