"""Процедурные обои для экрана входа BunnyOS."""
import pygame
import random
import math
from settings import WIDTH, HEIGHT


def generate_login_bg():
    """Возвращает Surface с красивым фоном для логина.
    Стиль: тёмный киберпанк с сеткой перспективы и светящимися точками."""
    surf = pygame.Surface((WIDTH, HEIGHT))

    # === 1. Градиент (тёмно-синий → почти чёрный) ===
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8 + 15 * t)
        g = int(15 + 25 * t)
        b = int(35 + 50 * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))

    # === 2. Туманности (размытые цветные пятна) ===
    rng = random.Random(42)
    for _ in range(6):
        cx = rng.randint(0, WIDTH)
        cy = rng.randint(0, HEIGHT)
        r = rng.randint(180, 320)
        hue = rng.choice([
            (60, 100, 200),   # синий
            (100, 60, 180),   # фиолетовый
            (40, 120, 180),   # голубой
        ])
        nebula = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(10):
            rr = r - i * 20
            if rr <= 0:
                continue
            a = 6 + i * 2
            pygame.draw.circle(nebula, (*hue, a), (r, r), rr)
        surf.blit(nebula, (cx - r, cy - r))

    # === 3. Сетка перспективы (снизу) ===
    horizon_y = int(HEIGHT * 0.65)
    # Горизонтальные линии
    for i in range(20):
        t = i / 20
        y = horizon_y + int((HEIGHT - horizon_y) * (t ** 1.5))
        a = int(60 * (1 - t * 0.4))
        line = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        line.fill((80, 140, 220, a))
        surf.blit(line, (0, y))
    # Вертикальные линии (сходятся к центру горизонта)
    cx = WIDTH // 2
    for i in range(-16, 17):
        x_bottom = cx + i * (WIDTH // 12)
        a = 45
        line = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(line, (80, 140, 220, a),
                         (cx, horizon_y), (x_bottom, HEIGHT), 1)
        surf.blit(line, (0, 0))

    # === 4. Свечение на горизонте ===
    for i in range(60):
        a = int(50 * (1 - i / 60))
        y1 = horizon_y - i
        y2 = horizon_y + i
        if y1 >= 0:
            line = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            line.fill((120, 180, 255, a))
            surf.blit(line, (0, y1))
        if y2 < HEIGHT:
            line = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            line.fill((120, 180, 255, int(a * 0.6)))
            surf.blit(line, (0, y2))

    # === 5. Звёзды наверху ===
    for _ in range(80):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, horizon_y - 20)
        size = rng.choice([1, 1, 1, 2])
        a = rng.randint(100, 255)
        star = pygame.Surface((size, size), pygame.SRCALPHA)
        star.fill((a, a, 255, a))
        surf.blit(star, (x, y))

    # === 6. Виньетка (тёмные края) ===
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(80):
        a = int(120 * (i / 80) ** 2)
        pygame.draw.rect(vignette, (0, 0, 0, a),
                         (i, i, WIDTH - i * 2, HEIGHT - i * 2), 1)
    surf.blit(vignette, (0, 0))

    return surf


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    bg = generate_login_bg()
    pygame.image.save(bg, "assets/wallpapers/login_procedural.png")
    print("✓ Сохранено: assets/wallpapers/login_procedural.png")
