"""Переиспользуемые UI-компоненты в Material Design."""
import pygame
import theme
from theme import (
    MD_PRIMARY, MD_SURFACE, MD_SURFACE_HI, MD_ON_SURFACE, MD_ON_BG,
    MD_MUTED, MD_GOLD, MD_SUCCESS, MD_ERROR, MD_SECONDARY, WIDTH,
)


class Button:
    def __init__(self, label, rect, on_click, accent=MD_PRIMARY):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.on_click = on_click
        self.accent = accent
        self.hovered = False
        self.pressed = False
        self.press_anim = 0.0
        self.hover_anim = 0.0
        self.enabled = True

    def update(self, dt, mouse):
        self.hovered = self.enabled and self.rect.collidepoint(mouse)
        target_h = 1.0 if self.hovered else 0.0
        self.hover_anim += (target_h - self.hover_anim) * min(1.0, dt / 80)
        target_p = 1.0 if self.pressed else 0.0
        self.press_anim += (target_p - self.press_anim) * min(1.0, dt / 40)

    def handle(self, e):
        if not self.enabled:
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.pressed = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.pressed and self.rect.collidepoint(e.pos):
                if self.on_click:
                    self.on_click()
            self.pressed = False

    def draw(self, surf):
        offset = int(3 * self.press_anim)
        rect = self.rect.move(0, offset)
        if self.press_anim < 0.8:
            sh = pygame.Surface((rect.w + 10, rect.h + 10), pygame.SRCALPHA)
            alpha = int(80 * (1 - self.press_anim))
            pygame.draw.rect(sh, (0, 0, 0, alpha), (5, 5, rect.w, rect.h), border_radius=12)
            surf.blit(sh, (rect.x - 5, rect.y - 5))
        if not self.enabled:
            bg = (25, 25, 32)
        elif self.press_anim > 0.5:
            bg = (20, 20, 28)
        elif self.hover_anim > 0.3:
            bg = MD_SURFACE_HI
        else:
            bg = MD_SURFACE
        pygame.draw.rect(surf, bg, rect, border_radius=12)
        if not self.enabled:
            border = (60, 60, 75)
        elif self.hover_anim > 0.3:
            border = self.accent
        else:
            border = (60, 60, 75)
        pygame.draw.rect(surf, border, rect, 2, border_radius=12)
        col = self.accent if (self.hover_anim > 0.5 and self.enabled) else MD_ON_SURFACE
        if not self.enabled:
            col = MD_MUTED
        f = theme.font(22, bold=True)
        txt = f.render(self.label, True, col)
        surf.blit(txt, txt.get_rect(center=rect.center))


def draw_text_centered(surf, text, y, size, color=MD_ON_BG, bold=False):
    f = theme.font(size, bold=bold)
    s = f.render(text, True, color)
    surf.blit(s, s.get_rect(center=(WIDTH // 2, y)))


def draw_text_left(surf, text, x, y, size, color=MD_ON_BG, bold=False):
    f = theme.font(size, bold=bold)
    surf.blit(f.render(text, True, color), (x, y))


def panel(surf, rect, accent=MD_PRIMARY, fill=MD_SURFACE):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, fill, rect, border_radius=16)
    pygame.draw.rect(surf, accent, rect, 2, border_radius=16)


def progress_bar(surf, rect, frac, color=MD_PRIMARY):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, (40, 40, 55), rect, border_radius=rect.h // 2)
    if frac > 0:
        fill_w = max(1, int(rect.w * min(1.0, frac)))
        pygame.draw.rect(surf, color, (rect.x, rect.y, fill_w, rect.h),
                         border_radius=rect.h // 2)


# ─── Геймификация ──────────────────────────────────────────

def draw_hearts(surf, x, y, hearts, max_hearts, size=20):
    """Рисует сердечки (полные/пустые)."""
    for i in range(max_hearts):
        cx = x + i * (size + 6)
        cy = y
        full = i < hearts
        color = (220, 40, 80) if full else (60, 40, 50)
        # Сердечко как два круга + треугольник
        r = size // 3
        pygame.draw.circle(surf, color, (cx + r, cy), r)
        pygame.draw.circle(surf, color, (cx + size - r, cy), r)
        pygame.draw.polygon(surf, color, [
            (cx, cy + r),
            (cx + size, cy + r),
            (cx + size // 2, cy + size),
        ])


def draw_xp_bar(surf, x, y, w, h, cur, total, color=MD_PRIMARY):
    """XP-бар с подписью."""
    f = theme.font(14)
    label = f.render(f"XP {cur} / {total}", True, MD_MUTED)
    surf.blit(label, (x, y - 18))
    frac = cur / total if total else 0
    progress_bar(surf, (x, y, w, h), frac, color)


def draw_streak_badge(surf, x, y, days):
    """Огонёк + число дней подряд."""
    f = theme.font(22, bold=True)
    # Огонёк (треугольник + полукруг)
    pygame.draw.polygon(surf, (255, 140, 40), [
        (x, y + 14), (x + 10, y), (x + 20, y + 14),
    ])
    pygame.draw.circle(surf, (255, 200, 80), (x + 10, y + 14), 6)
    txt = f.render(str(days), True, MD_GOLD)
    surf.blit(txt, (x + 26, y))


def draw_daily_quests(surf, x, y, w, done, target):
    """Карточка ежедневного квеста."""
    h = 70
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, MD_SURFACE, rect, border_radius=12)
    complete = done >= target
    border = MD_GOLD if complete else MD_PRIMARY
    pygame.draw.rect(surf, border, rect, 2, border_radius=12)
    # Заголовок
    f1 = theme.font(18, bold=True)
    title = "Ежедневный челлендж"
    surf.blit(f1.render(title, True, MD_ON_SURFACE), (x + 14, y + 8))
    # Прогресс
    f2 = theme.font(14)
    label = f2.render(f"Правильных: {done} / {target}", True, MD_MUTED)
    surf.blit(label, (x + 14, y + 34))
    progress_bar(surf, (x + 14, y + 52, w - 28, 8),
                 min(1.0, done / target) if target else 0,
                 MD_GOLD if complete else MD_PRIMARY)
