"""Launcher — rofi/wofi-style overlay (Super+D)."""
import pygame
from theme import *
from settings import WIDTH, HEIGHT


class Launcher:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font = font_small
        self.open = False
        self.query = ""
        self.selected = 0
        self.tick = 0

        # (name, app_id, icon, category)
        self.items = [
            ("Терминал",       "terminal",   ">_", "SYSTEM"),
            ("REAL BASH",      "_realbash",  "🔥", "SYSTEM"),
            ("Web Server",     "_webserver", "🌐", "SYSTEM"),
            ("Проводник",      "files",      "📁", "SYSTEM"),
            ("BunnyNet",       "browser",    "🌐", "NET"),
            ("Карта",          "map",        "🗺", "NET"),
            ("Блокнот",        "notepad",    "📝", "TOOLS"),
            ("Калькулятор",    "calc",       "🔢", "TOOLS"),
            ("Game Hub",       "hub",        "🎮", "GAMES"),
            ("Змейка",         "_snake",     "🐍", "GAMES"),
            ("Тетрис",         "_tetris",    "🧱", "GAMES"),
            ("2048",           "_2048",      "🔢", "GAMES"),
            ("Персонализация", "wallpapers", "🎨", "APPEARANCE"),
        ]

    def show(self):
        self.open = True
        self.query = ""
        self.selected = 0
        self.tick = 0

    def hide(self):
        self.open = False
        self.query = ""

    def filtered(self):
        if not self.query:
            return self.items
        q = self.query.lower()
        return [it for it in self.items if q in it[0].lower()]

    def handle_event(self, e):
        if not self.open:
            return None
        if e.type != pygame.KEYDOWN:
            return None
        if e.key == pygame.K_ESCAPE:
            self.hide()
            return None
        if e.key == pygame.K_DOWN:
            items = self.filtered()
            if items:
                self.selected = (self.selected + 1) % len(items)
            return None
        if e.key == pygame.K_UP:
            items = self.filtered()
            if items:
                self.selected = (self.selected - 1) % len(items)
            return None
        if e.key == pygame.K_RETURN:
            items = self.filtered()
            if items and 0 <= self.selected < len(items):
                entry = items[self.selected]
                app_id = entry[1]
                self.hide()
                return app_id
            return None
        if e.key == pygame.K_BACKSPACE:
            self.query = self.query[:-1]
            self.selected = 0
            return None
        else:
            if e.unicode and e.unicode.isprintable():
                self.query += e.unicode
                self.selected = 0
        return None

    def update(self, dt):
        self.tick += 1

    def draw(self, screen):
        if not self.open:
            return

        # Затемнение
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))

        # Панель
        panel_w = 600
        items = self.filtered()
        panel_h = 100 + min(len(items), 8) * 50
        panel = pygame.Rect(
            WIDTH // 2 - panel_w // 2,
            HEIGHT // 2 - panel_h // 2,
            panel_w, panel_h,
        )

        # Фон панели
        bg = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
        bg.fill((16, 16, 26, 240))
        screen.blit(bg, panel.topleft)

        # Неоновая рамка
        draw_gradient_border(screen, panel, GRAD_ACTIVE, width=3, radius=12)
        neon_glow(screen, panel, NEON_CYAN, radius=20, intensity=1.0)

        # Поле ввода
        input_rect = pygame.Rect(panel.x + 20, panel.y + 20, panel.w - 40, 50)
        pygame.draw.rect(screen, (8, 8, 14), input_rect, border_radius=8)
        pygame.draw.rect(screen, NEON_CYAN, input_rect, 2, border_radius=8)

        # Текст или placeholder
        if self.query:
            txt = self.font_big.render(self.query, True, TEXT)
        else:
            txt = self.font_big.render("Найди приложение...", True, TEXT_DIM)
        screen.blit(txt, (input_rect.x + 15, input_rect.centery - txt.get_height() // 2))

        # Курсор
        if (self.tick // 30) % 2 == 0:
            cx = input_rect.x + 15 + txt.get_width() + 3
            pygame.draw.rect(screen, NEON_CYAN,
                             (cx, input_rect.centery - 12, 3, 24))

        # Список
        y = panel.y + 90
        for i, entry in enumerate(items[:8]):
            name, app_id, icon = entry[0], entry[1], entry[2]
            row = pygame.Rect(panel.x + 20, y, panel.w - 40, 44)
            if i == self.selected:
                # Подсветка
                for xx in range(row.w):
                    t = xx / row.w
                    c = blend(NEON_CYAN, NEON_PURPLE, t)
                    pygame.draw.line(screen, c, (row.x + xx, row.y),
                                     (row.x + xx, row.bottom))
                text_col = (10, 10, 20)
            else:
                text_col = TEXT

            # Иконка + текст
            it = self.font.render(icon, True, text_col)
            screen.blit(it, (row.x + 10, row.centery - it.get_height() // 2))
            nt = self.font.render(name, True, text_col)
            screen.blit(nt, (row.x + 50, row.centery - nt.get_height() // 2))

            # Хоткей справа
            if i == self.selected:
                hint = self.font.render("ENTER", True, text_col)
                screen.blit(hint, (row.right - hint.get_width() - 10,
                                   row.centery - hint.get_height() // 2))

            y += 50

        # Подсказка внизу
        hint = self.font.render("↑↓ выбрать  ENTER запустить  ESC закрыть",
                                 True, TEXT_DIM)
        screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                            panel.bottom - 20))
