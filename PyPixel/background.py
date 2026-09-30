"""Многослойный фон с глубиной и туманом."""
import pygame
from settings import WIDTH, HEIGHT


def draw_sky_gradient(screen, camera):
    """Небо с градиентом — цвет зависит от глубины камеры."""
    oy = camera.offset_y
    from world import SURFACE_Y
    ground_y = SURFACE_Y - oy

    sky_top = (70, 130, 200)
    sky_bot = (170, 210, 240)
    cave_top = (48, 32, 28)
    cave_bot = (5, 3, 8)

    for y_screen in range(HEIGHT):
        if y_screen < ground_y:
            t = min(1.0, max(0.0, (ground_y - y_screen) / 600.0))
            col = (
                int(sky_bot[0] * (1 - t) + sky_top[0] * t),
                int(sky_bot[1] * (1 - t) + sky_top[1] * t),
                int(sky_bot[2] * (1 - t) + sky_top[2] * t),
            )
        else:
            t = min(1.0, (y_screen - ground_y) / 800.0)
            col = (
                int(cave_top[0] * (1 - t) + cave_bot[0] * t),
                int(cave_top[1] * (1 - t) + cave_bot[1] * t),
                int(cave_top[2] * (1 - t) + cave_bot[2] * t),
            )
        pygame.draw.line(screen, col, (0, y_screen), (WIDTH, y_screen))


def draw_mountains(screen, camera):
    """3 слоя гор с разными оттенками + туман."""
    oy = camera.offset_y
    ox = camera.offset_x
    from world import SURFACE_Y
    ground_y = SURFACE_Y - oy

    if ground_y < -300 or ground_y > HEIGHT + 300:
        return

    layers = [
        # (параллакс, цвет, высота, ширина волны, spacing)
        (0.10, (155, 185, 215), 100, 500, 450),
        (0.25, (125, 160, 200), 160, 380, 380),
        (0.40, (95, 130, 180), 220, 280, 320),
        (0.55, (70, 100, 155), 280, 220, 260),
    ]

    for parallax, color, height, wave, spacing in layers:
        shift = int(ox * parallax) % spacing
        cx = -shift - spacing
        points = []
        while cx <= WIDTH + spacing:
            # Каждая гора — треугольник с сглаженными краями
            peak_x = cx + spacing // 2
            peak_y = ground_y - height
            points.append((cx, ground_y + 5))
            points.append((peak_x, peak_y))
            cx += spacing
        points.append((WIDTH + spacing, ground_y + 5))
        # Заливаем как полигон
        if len(points) >= 3:
            pygame.draw.polygon(screen, color, points)


def draw_fog_between_layers(screen, camera, strength=0.15):
    """Полупрозрачный туман для глубины."""
    if strength <= 0:
        return
    oy = camera.offset_y
    from world import SURFACE_Y
    ground_y = SURFACE_Y - oy
    if ground_y < 0 or ground_y > HEIGHT:
        return
    fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    alpha = int(strength * 255)
    fog.fill((200, 215, 235, alpha))
    screen.blit(fog, (0, 0))
