"""Tokyo Night + cyberpunk Hyprland-inspired theme (Omarchy-style)."""

# === Базовые (Tokyo Night) ===
BG_DEEP     = (16, 16, 24)
BG_PANEL    = (26, 27, 38)
BG_HOVER    = (36, 40, 59)
BG_INACTIVE = (22, 22, 30)
BORDER      = (59, 66, 97)
TEXT        = (192, 202, 245)
TEXT_DIM    = (86, 95, 137)

# === Неон (Tokyo Night accents) ===
NEON_CYAN   = (125, 207, 255)
NEON_PINK   = (255, 0, 124)
NEON_PURPLE = (187, 154, 247)
NEON_YELLOW = (224, 175, 104)
NEON_RED    = (247, 118, 142)
NEON_GREEN  = (158, 206, 106)

# === Градиенты ===
GRAD_ACTIVE = [NEON_CYAN, NEON_PURPLE, NEON_PINK]
GRAD_WARN   = [NEON_YELLOW, NEON_RED]

# === Размеры ===
WAYBAR_H     = 44
BORDER_W     = 3
ROUND_RADIUS = 10
GAP          = 6

# === Шрифты ===
FONT_PIXEL = "assets/fonts/VT323.ttf"
FONT_SIZE_SMALL  = 18
FONT_SIZE_NORMAL = 22
FONT_SIZE_LARGE  = 32

# === Workspaces ===
WORKSPACES = 9

# === Анимации ===
ANIM_DURATION = 0.18


def blend(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


def gradient_h(colors, w):
    n = len(colors)
    if n < 2:
        return [colors[0]] * w
    out = []
    for x in range(w):
        pos = x / max(1, w - 1) * (n - 1)
        i = int(pos)
        t = pos - i
        if i >= n - 1:
            out.append(colors[-1])
        else:
            out.append(blend(colors[i], colors[i + 1], t))
    return out


def neon_glow(surface, rect, color, radius=12, intensity=1.0):
    import pygame
    glow = pygame.Surface((rect.w + radius * 2, rect.h + radius * 2), pygame.SRCALPHA)
    for i in range(radius, 0, -2):
        a = int(intensity * 30 * (i / radius))
        pygame.draw.rect(glow, (*color, a),
                         (radius - i, radius - i, rect.w + i * 2, rect.h + i * 2),
                         border_radius=8)
    surface.blit(glow, (rect.x - radius, rect.y - radius))


def draw_gradient_border(screen, rect, colors, width=3, radius=8):
    import pygame
    w = rect.w
    for x in range(w):
        pos = x / max(1, w - 1) * (len(colors) - 1)
        i = int(pos)
        t = pos - i
        if t > 0 and i < len(colors) - 1:
            c = blend(colors[i], colors[i + 1], t)
        else:
            c = colors[i]
        pygame.draw.line(screen, c, (rect.x + x, rect.y), (rect.x + x, rect.y + width - 1))
        pygame.draw.line(screen, c, (rect.x + x, rect.bottom - width),
                         (rect.x + x, rect.bottom - 1))
    for y in range(rect.h):
        pos = y / max(1, rect.h - 1) * (len(colors) - 1)
        i = int(pos)
        t = pos - i
        if t > 0 and i < len(colors) - 1:
            c = blend(colors[i], colors[i + 1], t)
        else:
            c = colors[i]
        pygame.draw.line(screen, c, (rect.x, rect.y + y), (rect.x + width - 1, rect.y + y))
        pygame.draw.line(screen, c, (rect.right - width, rect.y + y),
                         (rect.right - 1, rect.y + y))
