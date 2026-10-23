"""Keybindings overlay — Omarchy-style cheatsheet."""
import pygame
from theme import *


class KeybindsOverlay:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font = font_small
        self.open = False
        self.tick = 0

        self.groups = [
            ("ОКНА", [
                ("Super+Enter", "Открыть терминал"),
                ("Super+Q",     "Закрыть окно"),
                ("Super+T",     "Toggle tiling/floating"),
                ("Super+D",     "Launcher (fuzzy search)"),
            ]),
            ("НАВИГАЦИЯ", [
                ("Super+H/J/K/L", "Фокус влево/вниз/вверх/вправо"),
                ("Super+1..9",    "Переключить рабочий стол"),
            ]),
            ("ПРИЛОЖЕНИЯ", [
                ("Super+B",     "REAL BASH (pty+bwrap)"),
                ("Ctrl+Alt+T",  "Терминал"),
                ("Ctrl+Alt+B",  "REAL BASH"),
                ("F12",         "Скриншот в ~/bunny_sandbox/"),
                ("Ctrl+L",      "Заблокировать экран"),
            ]),
            ("FALLBACK", [
                ("Ctrl+Shift+*", "Если Super перехвачен системой"),
            ]),
        ]

    def toggle(self):
        self.open = not self.open
        self.tick = 0

    def handle_event(self, e):
        if not self.open:
            return False
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_F1, pygame.K_h):
                self.open = False
                return True
        return True

    def update(self, dt):
        self.tick += 1

    def draw(self, screen):
        if not self.open:
            return
        W, H = screen.get_size()
        # Затемнение
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))

        # Панель
        pw = 700
        ph = 560
        panel = pygame.Rect(W // 2 - pw // 2, H // 2 - ph // 2, pw, ph)

        # Фон
        bg = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
        bg.fill((16, 16, 24, 240))
        screen.blit(bg, panel.topleft)
        draw_gradient_border(screen, panel, GRAD_ACTIVE, 3, 16)
        neon_glow(screen, panel, NEON_CYAN, 24, 0.6)

        # Заголовок
        title = self.font_big.render("⌨ KEYBINDINGS", True, NEON_CYAN)
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 20))

        # Подзаголовок
        sub = self.font.render("Omarchy / Hyprland-style", True, TEXT_DIM)
        screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 70))

        # Группы в 2 колонки
        y_base = panel.y + 110
        col_w = panel.w // 2 - 20
        for gi, (group, binds) in enumerate(self.groups):
            col = gi % 2
            row = gi // 2
            x = panel.x + 20 + col * (col_w + 20)
            y = y_base + row * 220

            # Заголовок группы
            gt = self.font.render(group, True, NEON_PURPLE)
            screen.blit(gt, (x, y))
            pygame.draw.line(screen, NEON_PURPLE, (x, y + 24), (x + col_w, y + 24), 1)

            # Записи
            yy = y + 34
            for key, action in binds:
                k = self.font.render(key, True, NEON_CYAN)
                screen.blit(k, (x, yy))
                a = self.font.render(action, True, TEXT)
                screen.blit(a, (x + 160, yy))
                yy += 28

        # Подсказка
        hint = self.font.render("Esc / F1 / H — закрыть", True, TEXT_DIM)
        screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 30))
