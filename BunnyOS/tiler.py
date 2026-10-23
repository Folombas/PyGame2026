"""Tiling window manager — master/stack layout."""
import pygame
from theme import WAYBAR_H, BORDER_W
from settings import WIDTH, HEIGHT


MASTER_RATIO = 0.62   # 62% ширины — мастер
GAP = 6               # зазор между окнами


class Tiler:
    """Простой BSP тайлер (master + stack)."""

    def __init__(self):
        self.master_ratio = MASTER_RATIO
        self.gap = GAP

    def screen_area(self):
        """Область для тайлинга (без waybar сверху и небольшого отступа)."""
        return pygame.Rect(
            self.gap,
            WAYBAR_H + self.gap,
            WIDTH - self.gap * 2,
            HEIGHT - WAYBAR_H - self.gap * 2,
        )

    def layout(self, windows):
        """Возвращает [(window, pygame.Rect), ...] — раскладку."""
        if not windows:
            return []
        area = self.screen_area()
        n = len(windows)

        # 1 окно — на весь экран
        if n == 1:
            return [(windows[0], area.copy())]

        # 2+ — master слева, stack справа
        master_w = int(area.w * self.master_ratio) - self.gap // 2
        stack_x = area.x + master_w + self.gap
        stack_w = area.w - master_w - self.gap

        result = [(windows[0], pygame.Rect(area.x, area.y, master_w, area.h))]

        stack = windows[1:]
        if stack:
            count = len(stack)
            stack_h_total = area.h - (count - 1) * self.gap
            base_h = stack_h_total // count
            extra = stack_h_total - base_h * count  # остаток в первый
            y = area.y
            for i, w in enumerate(stack):
                h = base_h + (extra if i == 0 else 0)
                result.append((w, pygame.Rect(stack_x, y, stack_w, h)))
                y += h + self.gap

        return result

    def apply(self, windows):
        """Применяет раскладку (анимированно через target_rect)."""
        for w, rect in self.layout(windows):
            if hasattr(w, 'target_rect'):
                w.target_rect = rect
            else:
                w.rect = rect
            w.maximized = False
            w.minimized = False
