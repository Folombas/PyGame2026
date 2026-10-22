"""Cyberpunk Hyprland-inspired theme."""

# === Базовые цвета ===
BG_DEEP     = (8, 8, 14)
BG_PANEL    = (14, 14, 22)
BG_HOVER    = (24, 24, 36)
BORDER      = (40, 40, 60)
TEXT        = (220, 220, 240)
TEXT_DIM    = (110, 110, 140)

# === Неоновые акценты (Hyprland style) ===
NEON_CYAN   = (0, 255, 220)
NEON_PINK   = (255, 0, 180)
NEON_PURPLE = (180, 80, 255)
NEON_YELLOW = (255, 220, 80)
NEON_RED    = (255, 60, 80)

# === Градиенты для бордеров ===
GRAD_ACTIVE = [(0, 255, 220), (120, 200, 255), (180, 80, 255)]
GRAD_WARN   = [(255, 200, 80), (255, 100, 80)]

# === Размеры ===
WAYBAR_H     = 44
BORDER_W     = 3
ROUND_RADIUS = 10

# === Шрифты ===
FONT_PIXEL   = "assets/fonts/VT323.ttf"
FONT_SIZE_SMALL = 18
FONT_SIZE_NORMAL = 22
FONT_SIZE_LARGE = 32

# === Рабочие столы ===
WORKSPACES = 9

# === Анимации ===
ANIM_DURATION = 0.2
GLOW_PULSE    = 0.15


def blend(c1, c2, t):
    """Линейный блендинг двух цветов."""
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


def gradient_h(c, w):
    """Возвращает список цветов горизонтального градиента."""
    n = len(c)
    if n < 2:
        return [c[0]] * w
    out = []
    for x in range(w):
        pos = x / max(1, w - 1) * (n - 1)
        i = int(pos)
        t = pos - i
        if i >= n - 1:
            out.append(c[-1])
        else:
            out.append(blend(c[i], c[i + 1], t))
    return out


def neon_glow(surface, rect, color, radius=12, intensity=1.0):
    """Рисует мягкое свечение вокруг прямоугольника."""
    import pygame
    glow = pygame.Surface((rect.w + radius * 2, rect.h + radius * 2), pygame.SRCALPHA)
    for i in range(radius, 0, -2):
        a = int(intensity * 30 * (i / radius))
        pygame.draw.rect(glow, (*color, a),
                         (radius - i, radius - i, rect.w + i * 2, rect.h + i * 2),
                         border_radius=8)
    surface.blit(glow, (rect.x - radius, rect.y - radius))


def draw_gradient_border(screen, rect, colors, width=3, radius=8):
    """Градиентный бордер."""
    import pygame
    # Верхняя половина
    w = rect.w
    for x in range(w):
        pos = x / max(1, w - 1) * (len(colors) - 1)
        i = int(pos)
        t = pos - i
        c = colors[min(i + 1, len(colors) - 1)] if t > 0 else colors[i]
        if t > 0:
            c = blend(colors[i], colors[min(i+1, len(colors)-1)], t)
        # Верх
        pygame.draw.line(screen, c, (rect.x + x, rect.y), (rect.x + x, rect.y + width - 1))
        # Низ
        pygame.draw.line(screen, c,
                         (rect.x + x, rect.bottom - width),
                         (rect.x + x, rect.bottom - 1))
    # Левая и правая
    for y in range(rect.h):
        pos = y / max(1, rect.h - 1) * (len(colors) - 1)
        i = int(pos)
        t = pos - i
        if t > 0:
            c = blend(colors[i], colors[min(i+1, len(colors)-1)], t)
        else:
            c = colors[i]
        pygame.draw.line(screen, c, (rect.x, rect.y + y), (rect.x + width - 1, rect.y + y))
        pygame.draw.line(screen, c,
                         (rect.right - width, rect.y + y),
                         (rect.right - 1, rect.y + y))
