"""Генератор процедурных обоев для BunnyOS."""
import math
import random
import pygame
from settings import WIDTH, HEIGHT


def _gradient(surf, top, bottom):
    for y in range(HEIGHT):
        t = y / HEIGHT
        col = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (WIDTH, y))


def _stars(surf, n=120, seed=42):
    rng = random.Random(seed)
    for _ in range(n):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT // 2)
        s = rng.choice([1, 1, 2])
        a = rng.randint(100, 255)
        col = (a, a, min(255, a + 30))
        pygame.draw.rect(surf, col, (x, y, s, s))


def _moon(surf, cx, cy, r=50):
    pygame.draw.circle(surf, (245, 245, 220), (cx, cy), r)
    pygame.draw.circle(surf, (230, 230, 200), (cx + 8, cy - 5), r - 15)


def _rabbit_silhouette(surf, cx, cy, scale=3):
    """Пиксельный зайка-силуэт."""
    c = (20, 20, 30)
    # тело
    pygame.draw.rect(surf, c, (cx - 15 * scale, cy - 5 * scale, 30 * scale, 25 * scale))
    # голова
    pygame.draw.rect(surf, c, (cx - 12 * scale, cy - 15 * scale, 24 * scale, 15 * scale))
    # уши
    pygame.draw.rect(surf, c, (cx - 10 * scale, cy - 38 * scale, 6 * scale, 25 * scale))
    pygame.draw.rect(surf, c, (cx + 4 * scale, cy - 38 * scale, 6 * scale, 25 * scale))


def wp_night():
    """1. Ночное небо с зайкой."""
    s = pygame.Surface((WIDTH, HEIGHT))
    _gradient(s, (10, 15, 40), (30, 40, 80))
    _stars(s, 150, 1)
    _moon(s, WIDTH - 200, 150, 60)
    # Холмы
    for x in range(0, WIDTH, 40):
        y = HEIGHT - 180 - int(40 * math.sin(x * 0.01))
        pygame.draw.rect(s, (20, 30, 50), (x, y, 40, HEIGHT - y))
    _rabbit_silhouette(s, 300, HEIGHT - 220, 3)
    return s


def wp_sunset():
    """2. Закат."""
    s = pygame.Surface((WIDTH, HEIGHT))
    _gradient(s, (255, 120, 80), (80, 30, 90))
    # Солнце
    pygame.draw.circle(s, (255, 220, 120), (WIDTH // 2, HEIGHT - 200), 90)
    pygame.draw.circle(s, (255, 240, 180), (WIDTH // 2, HEIGHT - 200), 60)
    # Море
    pygame.draw.rect(s, (40, 20, 60), (0, HEIGHT - 180, WIDTH, 180))
    # Отражение
    for i in range(20):
        y = HEIGHT - 170 + i * 9
        w = 100 - i * 4
        pygame.draw.rect(s, (255, 180, 100, 100), (WIDTH // 2 - w // 2, y, w, 3))
    return s


def wp_forest():
    """3. Лес."""
    s = pygame.Surface((WIDTH, HEIGHT))
    _gradient(s, (140, 200, 130), (40, 90, 50))
    # Деревья
    rng = random.Random(7)
    for _ in range(30):
        x = rng.randint(0, WIDTH)
        y = rng.randint(HEIGHT - 300, HEIGHT - 60)
        h = rng.randint(80, 180)
        # Ствол
        pygame.draw.rect(s, (80, 50, 30), (x - 4, y, 8, h))
        # Кроны
        for k in range(3):
            r = 40 - k * 8
            pygame.draw.circle(s, (30 + k * 15, 100 + k * 20, 40),
                                (x, y - k * 30), r)
    return s


def wp_space():
    """4. Космос."""
    import random as _r
    rng = _r.Random(99)
    s = pygame.Surface((WIDTH, HEIGHT))
    _gradient(s, (5, 5, 20), (30, 10, 50))
    _stars(s, 250, 3)
    # Планета
    pygame.draw.circle(s, (180, 90, 140), (WIDTH - 300, HEIGHT - 250), 130)
    pygame.draw.circle(s, (120, 60, 100), (WIDTH - 300, HEIGHT - 250), 130, 4)
    # Кольцо
    pygame.draw.ellipse(s, (220, 180, 220),
                        (WIDTH - 470, HEIGHT - 290, 340, 80), 4)
    # Туманность
    for _ in range(60):
        x = rng.randint(100, WIDTH - 100)
        y = rng.randint(100, HEIGHT - 100)
        pygame.draw.circle(s, (60, 30, 90), (x, y), rng.randint(5, 20))
    return s


def wp_ocean():
    """5. Океан."""
    s = pygame.Surface((WIDTH, HEIGHT))
    _gradient(s, (140, 220, 240), (20, 80, 140))
    # Волны
    for row in range(15):
        y = HEIGHT - 300 + row * 20
        for x in range(0, WIDTH, 20):
            offset = int(10 * math.sin((x + row * 30) * 0.01))
            pygame.draw.circle(s, (200, 240, 255, 100), (x, y + offset), 3)
    # Солнце
    pygame.draw.circle(s, (255, 250, 200), (200, 150), 60)
    return s


def wp_retrowave():
    """6. Ретро-волна."""
    s = pygame.Surface((WIDTH, HEIGHT))
    _gradient(s, (40, 10, 60), (200, 40, 120))
    # Солнце с полосками
    pygame.draw.circle(s, (255, 200, 100), (WIDTH // 2, HEIGHT // 2 - 100), 100)
    for i in range(6):
        y = HEIGHT // 2 - 160 + i * 25
        pygame.draw.rect(s, (40, 10, 60), (WIDTH // 2 - 120, y, 240, 8))
    # Сетка
    for x in range(0, WIDTH, 60):
        pygame.draw.line(s, (255, 100, 200), (WIDTH // 2, HEIGHT // 2), (x, HEIGHT), 1)
    for i in range(15):
        y = HEIGHT // 2 + i * 20
        if y < HEIGHT:
            pygame.draw.line(s, (255, 100, 200), (0, y), (WIDTH, y), 1)
    return s


GENERATORS = [
    ("Ночное небо", "night",     wp_night),
    ("Закат",       "sunset",    wp_sunset),
    ("Лес",         "forest",    wp_forest),
    ("Космос",      "space",     wp_space),
    ("Океан",       "ocean",     wp_ocean),
    ("Ретро-волна", "retrowave", wp_retrowave),
]


def generate_all(out_dir="assets/wallpapers"):
    """Генерирует все обои и сохраняет в out_dir."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    for name, fname, fn in GENERATORS:
        surf = fn()
        path = os.path.join(out_dir, f"gen_{fname}.png")
        pygame.image.save(surf, path)
        print(f"  ✓ {path}")
    return len(GENERATORS)
