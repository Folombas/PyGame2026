import math, random
import pygame
from settings import *

pygame.font.init()
def _font(size, bold=False):
    for name in ('Inter', 'Segoe UI', 'DejaVu Sans', 'Arial'):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

F_TITLE  = _font(72, bold=True)
F_H1     = _font(44, bold=True)
F_H2     = _font(30, bold=True)
F_MED    = _font(22)
F_SMALL  = _font(17)
F_TINY   = _font(14)

class Button:
    def __init__(self, label, cx, cy, w, h, on_click, accent=ACCENT):
        self.label = label
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)
        self.on_click = on_click
        self.accent = accent
        self.hovered = False
        self.pressed = False
        self.pulse = 0.0

    def update(self, dt, mouse):
        self.hovered = self.rect.collidepoint(mouse)
        target = 1.0 if self.hovered else 0.0
        self.pulse += (target - self.pulse) * min(1.0, dt / 120.0)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
            self.pressed = False

    def draw(self, surf):
        p = self.pulse
        base = (30, 28, 60)
        col = tuple(int(base[i] + (self.accent[i] - base[i]) * (0.35 + 0.35 * p)) for i in range(3))
        rect = self.rect.copy()
        if self.pressed:
            rect = rect.inflate(-4, -4)
        # glow
        if p > 0.05:
            glow = pygame.Surface((rect.w + 24, rect.h + 24), pygame.SRCALPHA)
            for i in range(10, 0, -1):
                a = int(28 * p * (11 - i) / 10)
                pygame.draw.rect(glow, (*self.accent, a),
                                 (12 - i, 12 - i, rect.w + 2*i, rect.h + 2*i),
                                 border_radius=14 + i)
            surf.blit(glow, (rect.x - 12, rect.y - 12))
        pygame.draw.rect(surf, col, rect, border_radius=12)
        pygame.draw.rect(surf, self.accent, rect, 2, border_radius=12)
        txt = F_H2.render(self.label, True, TEXT)
        surf.blit(txt, txt.get_rect(center=rect.center))

def vertical_gradient(surf, top, bottom):
    h = surf.get_height()
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (surf.get_width(), y))

class Starfield:
    def __init__(self, w, h, n=60):
        self.w, self.h = w, h
        self.stars = [[random.uniform(0, w), random.uniform(0, h),
                       random.uniform(0.2, 1.6)] for _ in range(n)]
    def update(self, dt):
        f = dt / 16.67
        for s in self.stars:
            s[1] += s[2] * f
            if s[1] > self.h:
                s[0] = random.uniform(0, self.w)
                s[1] = -2
    def draw(self, surf):
        for x, y, sp in self.stars:
            a = int(120 + 100 * min(1.0, sp))
            pygame.draw.circle(surf, (a, a, min(255, a + 40)), (int(x), int(y)), 1)

def draw_title(surf, text, y, t):
    """Animated glowing title."""
    wave = math.sin(t / 400) * 4
    glow = F_TITLE.render(text, True, ACCENT2)
    for i, a in [(6, 25), (3, 45), (1, 90)]:
        s = F_TITLE.render(text, True, (*ACCENT2, a))
        s.set_alpha(a)
        surf.blit(s, s.get_rect(center=(WIDTH // 2 + i, y + wave)))
    main = F_TITLE.render(text, True, TEXT)
    surf.blit(main, main.get_rect(center=(WIDTH // 2, y + wave)))
    for i, a in [(3, 60), (1, 120)]:
        s = F_TITLE.render(text, True, ACCENT)
        s.set_alpha(a)
        surf.blit(s, s.get_rect(center=(WIDTH // 2 - i, y + wave)))
