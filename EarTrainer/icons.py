"""Векторные иконки — работают без emoji-шрифтов на любой системе."""
import pygame


def draw_speaker(surf, cx, cy, size, color):
    """Динамик — строго внутри квадрата size x size вокруг центра."""
    s = size // 2
    # Корпус (прямоугольник)
    bw = s // 2
    pygame.draw.rect(surf, color, (cx - s, cy - bw, bw, bw * 2), 2)
    # Треугольник-раструб
    pygame.draw.polygon(surf, color, [
        (cx - s + bw, cy - bw),
        (cx - s + bw + s // 2, cy - s * 2 // 3),
        (cx - s + bw + s // 2, cy + s * 2 // 3),
        (cx - s + bw, cy + bw),
    ], 2)
    # Волны — 2 дуги, строго в правой половине
    for r in (s // 3, s * 2 // 3):
        rect = pygame.Rect(cx + s // 4 - r, cy - r, r * 2, r * 2)
        try:
            pygame.draw.arc(surf, color, rect, -0.7, 0.7, 2)
        except Exception:
            pass


def draw_arrow_left(surf, x, y, size, color):
    s = size // 2
    pygame.draw.line(surf, color, (x + s, y - s), (x - s, y), 3)
    pygame.draw.line(surf, color, (x - s, y), (x + s, y + s), 3)
    pygame.draw.line(surf, color, (x - s, y), (x + s, y), 3)


def draw_arrow_right(surf, x, y, size, color):
    s = size // 2
    pygame.draw.line(surf, color, (x - s, y - s), (x + s, y), 3)
    pygame.draw.line(surf, color, (x + s, y), (x - s, y + s), 3)
    pygame.draw.line(surf, color, (x + s, y), (x - s, y), 3)


def draw_check(surf, x, y, size, color):
    s = size // 2
    pts = [
        (x - s, y),
        (x - s // 3, y + s * 2 // 3),
        (x + s, y - s * 2 // 3),
    ]
    pygame.draw.lines(surf, color, False, pts, 3)


def draw_cross(surf, x, y, size, color):
    s = size // 2
    pygame.draw.line(surf, color, (x - s, y - s), (x + s, y + s), 3)
    pygame.draw.line(surf, color, (x - s, y + s), (x + s, y - s), 3)


def draw_music_note(surf, x, y, size, color):
    s = size // 2
    # Головка
    pygame.draw.circle(surf, color, (x - s // 3, y + s * 2 // 3), max(2, s // 3))
    # Штиль
    pygame.draw.line(surf, color, (x, y + s // 2), (x, y - s), 3)
    # Флажок
    pygame.draw.line(surf, color, (x, y - s), (x + s // 2, y - s // 3), 3)


def draw_bar_chart(surf, x, y, size, color):
    s = size // 2
    # 3 столбика разной высоты
    pygame.draw.rect(surf, color, (x - s, y + s // 3, s * 2 // 3, s * 2 // 3), 2)
    pygame.draw.rect(surf, color, (x - s // 4, y - s // 3, s * 2 // 3, s * 2 // 3), 2)
    pygame.draw.rect(surf, color, (x + s // 2, y - s, s * 2 // 3, s * 2 // 3), 2)


def draw_hearts_icon(surf, x, y, size, color):
    """Маленькое сердечко для туториала."""
    pygame.draw.circle(surf, color, (x - size // 4, y - size // 4), size // 4)
    pygame.draw.circle(surf, color, (x + size // 4, y - size // 4), size // 4)
    pygame.draw.polygon(surf, color, [
        (x - size // 2, y - size // 4),
        (x + size // 2, y - size // 4),
        (x, y + size // 2),
    ])


def draw_star(surf, x, y, size, color):
    """Звезда для туториала."""
    import math
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        r = size // 2 if i % 2 == 0 else size // 4
        pts.append((x + r * math.cos(ang), y - r * math.sin(ang)))
    pygame.draw.polygon(surf, color, pts)
