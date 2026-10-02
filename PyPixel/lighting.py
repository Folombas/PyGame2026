"""Освещение: маска света, мягкие градиенты, кеш."""
import pygame
from settings import WIDTH, HEIGHT


class LightMask:
    """Наложение света поверх экрана через BLEND_RGBA_MIN.

    Принцип:
      • Маска = Surface(WIDTH, HEIGHT), залит alpha=darkness.
      • Источники света blit'ят круги с alpha=0 (прозрачно) в центре → darkness к краю.
      • BLEND_RGBA_MIN берёт min alpha для каждого пикселя — свет "вычитает" темноту.
    """
    def __init__(self):
        self.surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._grad_cache = {}

    def _make_gradient(self, radius):
        """Мягкий круг света: центр alpha=0, край alpha=255."""
        key = radius
        if key in self._grad_cache:
            return self._grad_cache[key]
        size = radius * 2
        grad = pygame.Surface((size, size), pygame.SRCALPHA)
        steps = 28
        for i in range(steps, 0, -1):
            r = int(radius * i / steps)
            # alpha: 0 у центра, 255 у края (квадратичный спад для мягкости)
            t = i / steps
            alpha = int(255 * (t ** 1.6))
            pygame.draw.circle(grad, (0, 0, 0, alpha), (radius, radius), r)
        self._grad_cache[key] = grad
        return grad

    def render(self, screen, camera, sources, ambient_dark):
        """sources = [(world_x, world_y, radius_px), ...]
        ambient_dark = 0..255 — общая темнота.
        """
        if ambient_dark <= 4:
            return  # светло — не затемняем

        # Заливаем маску тьмой
        self.surf.fill((0, 0, 0, ambient_dark))

        # Вырезаем свет от источников
        for wx, wy, r in sources:
            if r <= 0:
                continue
            sx = int(wx - camera.ox - r)
            sy = int(wy - camera.oy - r)
            # быстрый отсев
            if sx + r * 2 < 0 or sx > WIDTH or sy + r * 2 < 0 or sy > HEIGHT:
                continue
            grad = self._make_gradient(r)
            self.surf.blit(grad, (sx, sy), special_flags=pygame.BLEND_RGBA_MIN)

        # Накладываем на экран
        screen.blit(self.surf, (0, 0))


# --- утилита: уровень тьмы по времени суток ---
def ambient_from_time(time_of_day):
    """time_of_day = 0..1. 0=полночь, 0.5=полдень."""
    import math
    s = math.sin(time_of_day * math.tau - math.pi / 2) * 0.5 + 0.5
    # макс тёмность 140 (было 220) — ночью всё ещё видно силуэты
    return int(140 * (1 - s) ** 1.5)


def sky_colors_from_time(time_of_day):
    """Возвращает (top_color, bot_color) для неба. Натуральные переходы."""
    stops = [
        (0.00, (15, 18, 45),   (35, 40, 70)),      # глубокая ночь
        (0.18, (30, 35, 65),   (90, 70, 110)),     # поздняя ночь
        (0.24, (90, 60, 100),  (240, 130, 90)),    # предрассвет
        (0.28, (170, 120, 130),(255, 180, 130)),   # рассвет
        (0.33, (120, 170, 220),(230, 200, 180)),   # раннее утро
        (0.45, (100, 160, 220),(200, 225, 245)),   # утро
        (0.50, (95, 155, 225), (195, 225, 250)),   # полдень
        (0.60, (110, 165, 220),(220, 220, 210)),   # после полудня
        (0.72, (200, 140, 130),(255, 190, 140)),   # закат
        (0.78, (150, 90, 120), (240, 130, 110)),   # поздний закат
        (0.85, (50, 40, 85),   (110, 70, 100)),    # сумерки
        (0.92, (25, 25, 55),   (55, 50, 80)),      # ранняя ночь
        (1.00, (15, 18, 45),   (35, 40, 70)),      # глубокая ночь (как 0)
    ]
    t = time_of_day % 1.0
    for i in range(len(stops) - 1):
        t0, top0, bot0 = stops[i]
        t1, top1, bot1 = stops[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            top = tuple(int(top0[j] * (1 - u) + top1[j] * u) for j in range(3))
            bot = tuple(int(bot0[j] * (1 - u) + bot1[j] * u) for j in range(3))
            return top, bot
    return stops[0][1], stops[0][2]
