"""Мини-ОС внутри игры: рабочий стол, окна, курсор, интернет, карта."""
import math
import pygame
from settings import WIDTH, HEIGHT


# Цвета темы
DESK_BG = (30, 40, 70)
DESK_GRID = (40, 52, 88)
WIN_BG = (240, 240, 245)
WIN_BORDER = (80, 90, 130)
WIN_TITLE = (60, 80, 140)
WIN_TITLE_TEXT = (255, 255, 255)
TASKBAR = (35, 45, 75)
TASKBAR_TEXT = (220, 220, 240)
ICON_BG = (70, 100, 170)
ICON_HOVER = (100, 140, 220)
CURSOR_COL = (255, 255, 255)
CURSOR_BORDER = (30, 30, 30)

DESKTOP_ICONS = [
    {"id": "browser", "name": "Интернет", "icon": "🌐", "color": (80, 160, 220)},
    {"id": "map",     "name": "Карта",     "icon": "🗺", "color": (150, 200, 120)},
    {"id": "notes",   "name": "Заметки",   "icon": "📝", "color": (240, 200, 100)},
    {"id": "calc",    "name": "Калькулятор", "icon": "🔢", "color": (200, 130, 200)},
    {"id": "trash",   "name": "Корзина",   "icon": "🗑", "color": (140, 140, 140)},
]


class Window:
    def __init__(self, wtype, x, y, w=560, h=380, title="Окно"):
        self.wtype = wtype
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.close_hover = False

    def contains_titlebar(self, mx, my):
        return (self.rect.x <= mx < self.rect.right and
                self.rect.y <= my < self.rect.y + 26)

    def contains_close(self, mx, my):
        cx = self.rect.right - 18
        cy = self.rect.y + 13
        return (cx - 8 <= mx <= cx + 8 and cy - 8 <= my <= cy + 8)


class MiniPC:
    """Эмуляция рабочего стола с иконками, окнами, курсором."""

    def __init__(self, font_small, font_big, world_map_surface=None):
        self.font_small = font_small
        self.font_big = font_big
        self.world_map_surface = world_map_surface
        # Курсор
        self.cursor_x = WIDTH // 2
        self.cursor_y = HEIGHT // 2
        self.cursor_speed = 8
        # Окна
        self.windows = []
        # Иконки на рабочем столе
        self.icon_rects = []
        # Браузер — состояние
        self.browser_page = "home"  # home | news | game | shop | map
        self.browser_input_focus = False
        self.browser_url = "bunny://home"
        # Заметки — текст
        self.notes_text = "Привет, я Зайка!\n\nТут можно писать заметки.\n\n- Покормить грядки\n- Собрать морковку\n- Поиграть в игру"
        # Лог
        self.toast = None
        self.toast_timer = 0
        self.desk_anim = 0.0

    def toggle_window(self, wtype):
        # Если уже открыто — наверх
        for w in self.windows:
            if w.wtype == wtype:
                self.windows.remove(w)
                self.windows.append(w)
                return
        # Иначе открываем новое
        titles = {
            "browser": "🌐 Интернет",
            "map": "🗺 Карта мира",
            "notes": "📝 Заметки",
            "calc": "🔢 Калькулятор",
            "trash": "🗑 Корзина",
        }
        x = 160 + len(self.windows) * 30
        y = 100 + len(self.windows) * 30
        w = Window(wtype, x, y, title=titles.get(wtype, wtype))
        if wtype == "map":
            w.rect.w = 720
            w.rect.h = 480
        self.windows.append(w)

    def close_window(self, w):
        if w in self.windows:
            self.windows.remove(w)

    def update(self, keys, dt):
        self.desk_anim += dt
        # Курсор клавиатурой
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.cursor_x -= self.cursor_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.cursor_x += self.cursor_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.cursor_y -= self.cursor_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.cursor_y += self.cursor_speed
        self.cursor_x = max(0, min(WIDTH - 1, self.cursor_x))
        self.cursor_y = max(0, min(HEIGHT - 1, self.cursor_y))
        # Синхронизируем с реальной мышью, если она двигается
        mx, my = pygame.mouse.get_pos()
        if abs(mx - self.cursor_x) > 40 or abs(my - self.cursor_y) > 40:
            self.cursor_x, self.cursor_y = mx, my

        if self.toast_timer > 0:
            self.toast_timer -= 1

    def handle_click(self, mx, my, button=1):
        # 1. Проверяем окна (сверху вниз)
        for w in reversed(self.windows):
            if w.contains_close(mx, my):
                self.close_window(w)
                return
            if w.contains_titlebar(mx, my):
                # начинаем drag
                w.dragging = True
                w.drag_offset = (mx - w.rect.x, my - w.rect.y)
                # наверх
                self.windows.remove(w)
                self.windows.append(w)
                return
            # Клик внутри окна
            if w.rect.collidepoint(mx, my):
                self.windows.remove(w)
                self.windows.append(w)
                # Спец-обработка
                self._handle_window_click(w, mx, my)
                return
        # 2. Проверяем иконки
        for r, icon in self.icon_rects:
            if r.collidepoint(mx, my):
                self.toggle_window(icon["id"])
                self.toast = f"Открыто: {icon['name']}"
                self.toast_timer = 90
                return

    def handle_mouse_up(self):
        for w in self.windows:
            w.dragging = False

    def handle_mouse_motion(self, mx, my):
        for w in self.windows:
            if w.dragging:
                w.rect.x = mx - w.drag_offset[0]
                w.rect.y = my - w.drag_offset[1]

    def _handle_window_click(self, w, mx, my):
        if w.wtype == "browser":
            # Кнопки навигации
            rel_y = my - w.rect.y
            if 30 < rel_y < 60:
                # Проверяем кнопки
                pages = ["home", "news", "game", "shop", "map"]
                btn_w = 80
                for i, p in enumerate(pages):
                    bx = w.rect.x + 10 + i * (btn_w + 4)
                    if bx <= mx < bx + btn_w:
                        self.browser_page = p
                        self.browser_url = f"bunny://{p}"
                        return
        elif w.wtype == "trash":
            self.toast = "Корзина пуста. Зайка — чистюля!"
            self.toast_timer = 90

    def draw(self, screen):
        # Фон — сине-фиолетовый градиент
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(30 + 40 * t)
            g = int(40 + 30 * t)
            b = int(70 + 60 * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # Сетка
        for gx in range(0, WIDTH, 40):
            pygame.draw.line(screen, DESK_GRID, (gx, 0), (gx, HEIGHT - 40), 1)
        for gy in range(0, HEIGHT - 40, 40):
            pygame.draw.line(screen, DESK_GRID, (0, gy), (WIDTH, gy), 1)

        # Иконки на рабочем столе
        self.icon_rects = []
        for i, icon in enumerate(DESKTOP_ICONS):
            col = i // 6
            row = i % 6
            x = 30 + col * 130
            y = 30 + row * 110
            r = pygame.Rect(x, y, 90, 90)
            self.icon_rects.append((r, icon))

            mx, my = self.cursor_x, self.cursor_y
            hovered = r.collidepoint(mx, my)
            bg = ICON_HOVER if hovered else ICON_BG
            pygame.draw.rect(screen, bg, r)
            pygame.draw.rect(screen, (30, 30, 40), r, 2)
            # Символ
            sym = self.font_big.render(icon["icon"], True, (255, 255, 255))
            screen.blit(sym, (r.centerx - sym.get_width() // 2, r.y + 12))
            # Название
            name = self.font_small.render(icon["name"], True, (240, 240, 250))
            screen.blit(name, (r.centerx - name.get_width() // 2, r.bottom - 22))

        # Окна
        for w in self.windows:
            self._draw_window(screen, w)

        # Taskbar
        pygame.draw.rect(screen, TASKBAR, (0, HEIGHT - 40, WIDTH, 40))
        pygame.draw.line(screen, (70, 90, 140), (0, HEIGHT - 40), (WIDTH, HEIGHT - 40), 2)
        # Логотип
        logo = self.font_big.render("🐰 Зайка-OS", True, (255, 240, 180))
        screen.blit(logo, (14, HEIGHT - 34))
        # Время
        t = pygame.time.get_ticks() // 1000
        hh = (t // 3600) % 24
        mm = (t // 60) % 60
        clock = self.font_small.render(f"{hh:02d}:{mm:02d}   Esc — выключить ПК",
                                        True, TASKBAR_TEXT)
        screen.blit(clock, (WIDTH - clock.get_width() - 16, HEIGHT - 28))

        # Toast
        if self.toast and self.toast_timer > 0:
            txt = self.font_small.render(self.toast, True, (255, 255, 255))
            bg = pygame.Surface((txt.get_width() + 20, 30), pygame.SRCALPHA)
            bg.fill((40, 60, 100, 230))
            pygame.draw.rect(bg, (100, 160, 240), (0, 0, bg.get_width(), 30), 2)
            screen.blit(bg, (WIDTH - bg.get_width() - 20, 20))
            screen.blit(txt, (WIDTH - bg.get_width() - 10, 26))

        # Пиксельный курсор — рисуем поверх всего
        self._draw_cursor(screen)

    def _draw_cursor(self, screen):
        x, y = int(self.cursor_x), int(self.cursor_y)
        # Стрелка курсора — 12x16 пикселей
        cursor_pixels = [
            (0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9),(0,10),(0,11),(0,12),(0,13),(0,14),(0,15),
            (1,0),(2,1),(3,2),(4,3),(5,4),(6,5),(7,6),(8,7),(9,8),(7,10),(8,10),(9,10),(10,10),(11,10),
            (1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),
            (9,9),(9,10),(9,11),(9,12),(10,9),(10,10),(10,11),(10,12),(11,9),(11,10),(12,10),(12,11),
        ]
        for dx, dy in cursor_pixels:
            pygame.draw.rect(screen, CURSOR_BORDER, (x + dx, y + dy, 3, 3))
            pygame.draw.rect(screen, CURSOR_COL, (x + dx + 1, y + dy + 1, 1, 1))

    def _draw_window(self, screen, w):
        # Тень
        shadow = pygame.Surface((w.rect.w + 8, w.rect.h + 8), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 80))
        screen.blit(shadow, (w.rect.x + 4, w.rect.y + 4))

        # Тело
        pygame.draw.rect(screen, WIN_BG, w.rect)
        pygame.draw.rect(screen, WIN_BORDER, w.rect, 2)

        # Заголовок
        title_rect = pygame.Rect(w.rect.x, w.rect.y, w.rect.w, 26)
        pygame.draw.rect(screen, WIN_TITLE, title_rect)
        title = self.font_small.render(w.title, True, WIN_TITLE_TEXT)
        screen.blit(title, (title_rect.x + 8, title_rect.y + 6))

        # Кнопка закрытия
        cx = w.rect.right - 18
        cy = w.rect.y + 13
        hover = w.contains_close(self.cursor_x, self.cursor_y)
        col = (240, 90, 90) if hover else (200, 70, 70)
        pygame.draw.rect(screen, col, (cx - 8, cy - 8, 16, 16))
        pygame.draw.rect(screen, (40, 20, 20), (cx - 8, cy - 8, 16, 16), 1)
        # Крестик
        pygame.draw.line(screen, (255, 240, 240), (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
        pygame.draw.line(screen, (255, 240, 240), (cx - 4, cy + 4), (cx + 4, cy - 4), 2)

        # Содержимое окна
        content_rect = pygame.Rect(w.rect.x + 4, w.rect.y + 30,
                                    w.rect.w - 8, w.rect.h - 34)
        if w.wtype == "browser":
            self._draw_browser(screen, content_rect)
        elif w.wtype == "map":
            self._draw_map(screen, content_rect)
        elif w.wtype == "notes":
            self._draw_notes(screen, content_rect)
        elif w.wtype == "calc":
            self._draw_calc(screen, content_rect)
        elif w.wtype == "trash":
            self._draw_trash(screen, content_rect)

    def _draw_browser(self, screen, r):
        # Панель навигации
        nav = pygame.Rect(r.x, r.y, r.w, 30)
        pygame.draw.rect(screen, (200, 210, 225), nav)
        pages = [("Дом", "home"), ("Новости", "news"), ("Игра", "game"),
                 ("Магазин", "shop"), ("Карта", "map")]
        btn_w = 80
        for i, (name, pid) in enumerate(pages):
            bx = nav.x + 10 + i * (btn_w + 4)
            by = nav.y + 4
            btn_rect = pygame.Rect(bx, by, btn_w, 22)
            active = (self.browser_page == pid)
            col = (100, 150, 220) if active else (180, 190, 205)
            pygame.draw.rect(screen, col, btn_rect)
            pygame.draw.rect(screen, (80, 90, 110), btn_rect, 1)
            txt = self.font_small.render(name, True, (255, 255, 255) if active else (40, 40, 60))
            screen.blit(txt, (btn_rect.centerx - txt.get_width() // 2,
                              btn_rect.y + 4))

        # Адресная строка
        url_rect = pygame.Rect(r.x + 4, nav.bottom + 4, r.w - 8, 24)
        pygame.draw.rect(screen, (250, 250, 255), url_rect)
        pygame.draw.rect(screen, (150, 160, 180), url_rect, 1)
        url_txt = self.font_small.render(self.browser_url, True, (40, 40, 70))
        screen.blit(url_txt, (url_rect.x + 6, url_rect.y + 5))

        # Контент страницы
        cont = pygame.Rect(r.x + 4, url_rect.bottom + 4, r.w - 8, r.h - (url_rect.bottom - r.y) - 8)
        pygame.draw.rect(screen, (250, 250, 255), cont)
        pygame.draw.rect(screen, (150, 160, 180), cont, 1)
        self._draw_browser_content(screen, cont)

    def _draw_browser_content(self, screen, r):
        p = self.browser_page
        if p == "home":
            title = self.font_big.render("🐰 Добро пожаловать в BunnyNet!", True, (60, 80, 140))
            screen.blit(title, (r.x + 20, r.y + 20))
            lines = [
                "Здесь ты найдёшь всё о морковке и приключениях.",
                "",
                "Слева — вкладки: Новости, Игра, Магазин, Карта.",
                "Нажми на любую — и погнали!",
            ]
            for i, line in enumerate(lines):
                t = self.font_small.render(line, True, (40, 50, 80))
                screen.blit(t, (r.x + 20, r.y + 60 + i * 22))
        elif p == "news":
            title = self.font_small.render("📰 Новости Морковного Края", True, (140, 60, 80))
            screen.blit(title, (r.x + 20, r.y + 20))
            news = [
                "• В деревне открыт новый колодец!",
                "• Урожай морковки в этом году — рекордный.",
                "• Замечена странная тень у восточного озера...",
                "• Торговец снизил цены на удобрения.",
            ]
            for i, line in enumerate(news):
                t = self.font_small.render(line, True, (60, 60, 80))
                screen.blit(t, (r.x + 20, r.y + 50 + i * 22))
        elif p == "game":
            title = self.font_big.render("🎮 Игра: Прыгни Выше!", True, (140, 80, 160))
            screen.blit(title, (r.x + 20, r.y + 20))
            t = self.font_small.render("(Здесь могла быть мини-игра)", True, (100, 100, 120))
            screen.blit(t, (r.x + 20, r.y + 60))
            # Зайка
            for i in range(6):
                x = r.x + 40 + i * 60
                y = r.y + 120 + int(math.sin(self.desk_anim * 3 + i) * 12)
                pygame.draw.circle(screen, (250, 240, 220), (x, y), 14)
                pygame.draw.circle(screen, (30, 25, 35), (x, y), 14, 2)
                pygame.draw.circle(screen, (240, 150, 170), (x - 4, y - 16), 4)
                pygame.draw.circle(screen, (240, 150, 170), (x + 4, y - 16), 4)
                pygame.draw.circle(screen, (30, 25, 35), (x - 4, y - 2), 2)
                pygame.draw.circle(screen, (30, 25, 35), (x + 4, y - 2), 2)
        elif p == "shop":
            title = self.font_small.render("🛒 Магазин Семян", True, (100, 130, 60))
            screen.blit(title, (r.x + 20, r.y + 20))
            items = [
                ("Семена морковки — 5🪙", (240, 130, 60)),
                ("Удобрение — 10🪙", (140, 90, 50)),
                ("Лейка — 25🪙", (100, 160, 220)),
                ("Забор — 15🪙", (180, 130, 90)),
            ]
            for i, (name, col) in enumerate(items):
                y = r.y + 50 + i * 30
                pygame.draw.rect(screen, col, (r.x + 20, y, 20, 20))
                t = self.font_small.render(name, True, (60, 60, 80))
                screen.blit(t, (r.x + 50, y + 3))
        elif p == "map":
            self._draw_map_content(screen, r)

    def _draw_map_content(self, screen, r):
        """Карта внутри браузера."""
        if self.world_map_surface is None:
            t = self.font_small.render("Карта недоступна", True, (100, 100, 120))
            screen.blit(t, (r.x + 20, r.y + 20))
            return
        # Масштабируем карту под контент
        map_img = pygame.transform.smoothscale(
            self.world_map_surface, (r.w - 20, r.h - 20))
        screen.blit(map_img, (r.x + 10, r.y + 10))

    def _draw_map(self, screen, r):
        """Отдельное окно карты."""
        self._draw_map_content(screen, r)

    def _draw_notes(self, screen, r):
        # Заголовок как лист блокнота
        pygame.draw.rect(screen, (255, 250, 220), r)
        pygame.draw.rect(screen, (200, 180, 130), r, 2)
        # Пунктирные линии
        for i in range(1, 15):
            y = r.y + i * 22
            pygame.draw.line(screen, (220, 210, 180), (r.x, y), (r.right, y), 1)
        # Текст
        lines = self.notes_text.split("\n")
        for i, line in enumerate(lines):
            t = self.font_small.render(line, True, (60, 50, 40))
            screen.blit(t, (r.x + 12, r.y + 8 + i * 22))

    def _draw_calc(self, screen, r):
        pygame.draw.rect(screen, (200, 200, 210), r)
        # Дисплей
        disp = pygame.Rect(r.x + 10, r.y + 10, r.w - 20, 50)
        pygame.draw.rect(screen, (240, 250, 220), disp)
        pygame.draw.rect(screen, (60, 80, 60), disp, 2)
        t = self.font_big.render("0", True, (40, 60, 40))
        screen.blit(t, (disp.right - t.get_width() - 10, disp.y + 10))
        # Кнопки
        labels = [["7","8","9","/"],["4","5","6","*"],["1","2","3","-"],["C","0","=","+"]]
        bw, bh = 60, 40
        gap = 8
        start_x = r.x + 10
        start_y = disp.bottom + 10
        for row_i, row in enumerate(labels):
            for col_i, label in enumerate(row):
                bx = start_x + col_i * (bw + gap)
                by = start_y + row_i * (bh + gap)
                pygame.draw.rect(screen, (240, 240, 245), (bx, by, bw, bh))
                pygame.draw.rect(screen, (100, 100, 120), (bx, by, bw, bh), 2)
                t = self.font_small.render(label, True, (30, 30, 50))
                screen.blit(t, (bx + bw // 2 - t.get_width() // 2,
                                by + bh // 2 - t.get_height() // 2))

    def _draw_trash(self, screen, r):
        pygame.draw.rect(screen, (245, 245, 250), r)
        pygame.draw.rect(screen, (180, 180, 190), r, 2)
        t = self.font_small.render("Корзина пуста.", True, (120, 120, 140))
        screen.blit(t, (r.x + 20, r.y + 20))
        t2 = self.font_small.render("Зайка — аккуратный!", True, (120, 120, 140))
        screen.blit(t2, (r.x + 20, r.y + 44))
