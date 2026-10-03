"""BunnyOS — в стиле Windows XP (на базе Linux-ядра Carrot)."""
import math
import pygame
from settings import WIDTH, HEIGHT
import os_sounds


# Цвета XP Luna
XP_BLUE = (30, 80, 160)
XP_BLUE_LIGHT = (90, 145, 220)
XP_BLUE_DARK = (15, 45, 100)
XP_BG = (88, 130, 180)
XP_TASKBAR = (36, 90, 170)
XP_TASKBAR_LIGHT = (70, 130, 210)
XP_START = (75, 155, 75)       # зелёная кнопка Пуск
XP_START_LIGHT = (120, 200, 110)
XP_WINDOW_BG = (240, 235, 220)
XP_WINDOW_BORDER = (30, 80, 160)
XP_TITLE = (60, 110, 190)
XP_TEXT = (20, 20, 40)

DESKTOP_ICONS = [
    {"id": "mycomputer", "name": "Мой кролик", "icon": "🖥", "color": (120, 160, 220)},
    {"id": "browser",    "name": "Интернет",   "icon": "🌐", "color": (80, 160, 220)},
    {"id": "map",        "name": "Карта",      "icon": "🗺", "color": (150, 200, 120)},
    {"id": "notes",      "name": "Заметки",    "icon": "📝", "color": (240, 200, 100)},
    {"id": "calc",       "name": "Калькулятор","icon": "🔢", "color": (200, 130, 200)},
]


def draw_xp_button(screen, rect, label, font, hovered=False, pressed=False, base_col=None):
    """Кнопка в стиле XP — с градиентом и рамкой."""
    base = base_col or (230, 230, 240)
    if pressed:
        top = tuple(max(0, c - 30) for c in base)
        bot = base
    else:
        top = base
        bot = tuple(max(0, c - 30) for c in base)

    # Градиент
    for y in range(rect.h):
        t = y / rect.h
        col = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        pygame.draw.line(screen, col, (rect.x, rect.y + y), (rect.right, rect.y + y))
    # Внешняя тёмная рамка
    pygame.draw.rect(screen, (60, 80, 120), rect, 1)
    # Внутренняя светлая
    pygame.draw.line(screen, (255, 255, 255), (rect.x + 1, rect.y + 1),
                     (rect.right - 2, rect.y + 1))
    pygame.draw.line(screen, (255, 255, 255), (rect.x + 1, rect.y + 1),
                     (rect.x + 1, rect.bottom - 2))
    # Текст
    txt = font.render(label, True, XP_TEXT)
    screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                      rect.centery - txt.get_height() // 2))


class Window:
    def __init__(self, wtype, x, y, w=580, h=400, title="Окно"):
        self.wtype = wtype
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.minimized = False

    def contains_titlebar(self, mx, my):
        return (self.rect.x <= mx < self.rect.right and
                self.rect.y <= my < self.rect.y + 26)

    def contains_close(self, mx, my):
        cx = self.rect.right - 18
        cy = self.rect.y + 13
        return (cx - 9 <= mx <= cx + 9 and cy - 9 <= my <= cy + 9)

    def contains_minimize(self, mx, my):
        cx = self.rect.right - 44
        cy = self.rect.y + 13
        return (cx - 9 <= mx <= cx + 9 and cy - 9 <= my <= cy + 9)


class MiniPC:
    def __init__(self, font_small, font_big, world_map_surface=None):
        self.font_small = font_small
        self.font_big = font_big
        self.world_map_surface = world_map_surface
        self.cursor_x = WIDTH // 2
        self.cursor_y = HEIGHT // 2
        self.cursor_speed = 10
        self.windows = []
        self.icon_rects = []
        self.browser_page = "home"
        self.browser_url = "bunny://home"
        self.notes_text = "Привет, я Зайка!\n\nЗаметки BunnyOS:\n- Покормить грядки\n- Собрать морковку\n- Проверить восточное озеро\n- Сделать резервную копию"
        self.toast = None
        self.toast_timer = 0
        self.desk_anim = 0.0
        self.start_menu_open = False
        self.clock_timer = 0
        # Калькулятор
        self.calc_display = "0"
        self.calc_prev = None
        self.calc_op = None
        self.calc_new = False

    def toggle_window(self, wtype):
        for w in self.windows:
            if w.wtype == wtype:
                self.windows.remove(w)
                self.windows.append(w)
                if w.minimized:
                    w.minimized = False
                return
        titles = {
            "mycomputer": "Мой кролик",
            "browser": "🌐 Интернет — BunnyNet Explorer",
            "map": "🗺 Карта мира",
            "notes": "📝 Заметки",
            "calc": "Калькулятор",
        }
        x = 180 + len(self.windows) * 30
        y = 90 + len(self.windows) * 30
        w = Window(wtype, x, y, title=titles.get(wtype, wtype))
        if wtype == "map":
            w.rect.w = 720
            w.rect.h = 500
        if wtype == "calc":
            w.rect.w = 320
            w.rect.h = 440
        if wtype == "notes":
            w.rect.w = 500
            w.rect.h = 400
        self.windows.append(w)

    def close_window(self, w):
        if w in self.windows:
            self.windows.remove(w)

    def minimize_window(self, w):
        w.minimized = True

    def update(self, keys, dt):
        self.desk_anim += dt
        self.clock_timer += 1

        # Курсор
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

        # Реальная мышь
        mx, my = pygame.mouse.get_pos()
        if abs(mx - self.cursor_x) > 40 or abs(my - self.cursor_y) > 40:
            self.cursor_x, self.cursor_y = mx, my

        if self.toast_timer > 0:
            self.toast_timer -= 1

    def handle_click(self, mx, my, button=1):
        # Кнопка Пуск?
        start_rect = pygame.Rect(6, HEIGHT - 40, 110, 34)
        if start_rect.collidepoint(mx, my):
            self.start_menu_open = not self.start_menu_open
            os_sounds.play("click")
            return

        # Если меню Пуск открыто — проверяем его
        if self.start_menu_open:
            menu_rect = pygame.Rect(6, HEIGHT - 300, 240, 260)
            if menu_rect.collidepoint(mx, my):
                # Пункты меню
                items = [
                    ("Мой кролик", "mycomputer"),
                    ("Интернет", "browser"),
                    ("Карта", "map"),
                    ("Заметки", "notes"),
                    ("Калькулятор", "calc"),
                    ("", None),
                    ("Выключить ПК", "shutdown"),
                ]
                for i, (name, wid) in enumerate(items):
                    iy = menu_rect.y + 10 + i * 32
                    item_rect = pygame.Rect(menu_rect.x + 4, iy, menu_rect.w - 8, 30)
                    if item_rect.collidepoint(mx, my) and wid:
                        if wid == "shutdown":
                            self.start_menu_open = False
                            os_sounds.play("shutdown")
                            return "shutdown"
                        self.toggle_window(wid)
                        self.start_menu_open = False
                        os_sounds.play("click")
                        return
                return
            else:
                self.start_menu_open = False
                return

        # Проверяем окна
        for w in reversed(self.windows):
            if w.minimized:
                continue
            if w.contains_close(mx, my):
                self.close_window(w)
                os_sounds.play("click")
                return
            if w.contains_minimize(mx, my):
                self.minimize_window(w)
                os_sounds.play("click")
                return
            if w.contains_titlebar(mx, my):
                w.dragging = True
                w.drag_offset = (mx - w.rect.x, my - w.rect.y)
                self.windows.remove(w)
                self.windows.append(w)
                return
            if w.rect.collidepoint(mx, my):
                self.windows.remove(w)
                self.windows.append(w)
                self._handle_window_click(w, mx, my)
                return

        # Иконки
        for r, icon in self.icon_rects:
            if r.collidepoint(mx, my):
                self.toggle_window(icon["id"])
                os_sounds.play("click")
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
            rel_y = my - w.rect.y
            if 30 < rel_y < 60:
                pages = ["home", "news", "game", "shop", "map"]
                btn_w = 90
                for i, p in enumerate(pages):
                    bx = w.rect.x + 10 + i * (btn_w + 4)
                    if bx <= mx < bx + btn_w:
                        self.browser_page = p
                        self.browser_url = f"bunny://{p}"
                        os_sounds.play("click")
                        return
        elif w.wtype == "calc":
            self._handle_calc_click(w, mx, my)

    def _handle_calc_click(self, w, mx, my):
        """Обработка кнопок калькулятора."""
        # Позиции кнопок
        buttons = self._calc_buttons(w)
        for (label, rect) in buttons:
            if rect.collidepoint(mx, my):
                self._calc_press(label)
                os_sounds.play("click")
                return

    def _calc_buttons(self, w):
        """Возвращает список (label, rect) для кнопок калькулятора."""
        r = w.rect
        # display сверху
        disp_h = 60
        # сетка 4x5 под дисплеем
        grid_x = r.x + 10
        grid_y = r.y + 30 + disp_h + 10
        bw = (r.w - 20 - 3 * 6) // 4
        bh = 50
        gap = 6
        layout = [
            ["C", "←", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["±", "0", ".", "="],
        ]
        result = []
        for row_i, row in enumerate(layout):
            for col_i, label in enumerate(row):
                bx = grid_x + col_i * (bw + gap)
                by = grid_y + row_i * (bh + gap)
                result.append((label, pygame.Rect(bx, by, bw, bh)))
        return result

    def _calc_press(self, label):
        """Логика калькулятора."""
        if label == "C":
            self.calc_display = "0"
            self.calc_prev = None
            self.calc_op = None
            self.calc_new = False
        elif label == "←":
            if len(self.calc_display) > 1:
                self.calc_display = self.calc_display[:-1]
            else:
                self.calc_display = "0"
        elif label == "±":
            if self.calc_display.startswith("-"):
                self.calc_display = self.calc_display[1:]
            elif self.calc_display != "0":
                self.calc_display = "-" + self.calc_display
        elif label == "%":
            try:
                self.calc_display = str(float(self.calc_display) / 100)
                if self.calc_display.endswith(".0"):
                    self.calc_display = self.calc_display[:-2]
            except ValueError:
                pass
        elif label in ("+", "-", "*", "/"):
            try:
                cur = float(self.calc_display)
                if self.calc_op and self.calc_prev is not None:
                    result = self._apply_op(self.calc_prev, cur, self.calc_op)
                    self.calc_display = self._fmt(result)
                    self.calc_prev = result
                else:
                    self.calc_prev = cur
                self.calc_op = label
                self.calc_new = True
            except ValueError:
                pass
        elif label == "=":
            if self.calc_op and self.calc_prev is not None:
                try:
                    cur = float(self.calc_display)
                    result = self._apply_op(self.calc_prev, cur, self.calc_op)
                    self.calc_display = self._fmt(result)
                    self.calc_prev = None
                    self.calc_op = None
                    self.calc_new = True
                except (ValueError, ZeroDivisionError):
                    self.calc_display = "Ошибка"
                    os_sounds.play("error")
        elif label == ".":
            if "." not in self.calc_display:
                self.calc_display += "."
        else:  # цифра
            if self.calc_new:
                self.calc_display = label
                self.calc_new = False
            else:
                if self.calc_display == "0":
                    self.calc_display = label
                else:
                    self.calc_display += label

    def _apply_op(self, a, b, op):
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/":
            if b == 0:
                raise ZeroDivisionError()
            return a / b
        return b

    def _fmt(self, v):
        if abs(v - int(v)) < 1e-9:
            return str(int(v))
        return f"{v:.6f}".rstrip("0").rstrip(".")

    def draw(self, screen):
        # ==== Рабочий стол — луг + небо как обои XP ====
        # Небо сверху
        for y in range(HEIGHT):
            t = y / HEIGHT
            if t < 0.55:
                r = int(80 + 80 * t)
                g = int(140 + 60 * t)
                b = int(200 + 40 * t)
            else:
                t2 = (t - 0.55) / 0.45
                r = int(120 - 40 * t2)
                g = int(180 - 60 * t2)
                b = int(80 - 40 * t2)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # Холмы
        hills = [(0, HEIGHT - 200, 300), (300, HEIGHT - 230, 400),
                 (700, HEIGHT - 210, 350), (WIDTH - 200, HEIGHT - 190, 300)]
        for hx, hy, hw in hills:
            pygame.draw.ellipse(screen, (110, 170, 90),
                                (hx - hw // 2, hy, hw, HEIGHT - hy + 50))

        # Иконки
        self.icon_rects = []
        for i, icon in enumerate(DESKTOP_ICONS):
            x = 30
            y = 30 + i * 110
            r = pygame.Rect(x, y, 100, 100)
            self.icon_rects.append((r, icon))

            mx, my = self.cursor_x, self.cursor_y
            hover = r.collidepoint(mx, my)

            # Иконка
            if hover:
                pygame.draw.rect(screen, (100, 150, 220), r, 2)
                bg = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                bg.fill((255, 255, 255, 40))
                screen.blit(bg, r.topleft)
            # Символ
            sym = self.font_big.render(icon["icon"], True, (255, 255, 255))
            screen.blit(sym, (r.centerx - sym.get_width() // 2, r.y + 18))
            # Имя — с тенью для читаемости
            sh = self.font_small.render(icon["name"], True, (0, 0, 0))
            nm = self.font_small.render(icon["name"], True, (255, 255, 255))
            nx = r.centerx - nm.get_width() // 2
            ny = r.bottom - 24
            screen.blit(sh, (nx + 1, ny + 1))
            screen.blit(nm, (nx, ny))

        # Окна
        for w in self.windows:
            if not w.minimized:
                self._draw_window(screen, w)

        # Меню Пуск
        if self.start_menu_open:
            self._draw_start_menu(screen)

        # Панель задач
        self._draw_taskbar(screen)

        # Toast
        if self.toast and self.toast_timer > 0:
            txt = self.font_small.render(self.toast, True, (255, 255, 255))
            bg = pygame.Surface((txt.get_width() + 20, 30), pygame.SRCALPHA)
            bg.fill((40, 60, 100, 230))
            pygame.draw.rect(bg, (100, 160, 240), (0, 0, bg.get_width(), 30), 2)
            screen.blit(bg, (WIDTH - bg.get_width() - 20, 20))
            screen.blit(txt, (WIDTH - bg.get_width() - 10, 26))

        # Курсор
        self._draw_cursor(screen)

    def _draw_taskbar(self, screen):
        # Панель
        tb = pygame.Rect(0, HEIGHT - 40, WIDTH, 40)
        # Градиент
        for y in range(tb.h):
            t = y / tb.h
            col = tuple(int(XP_TASKBAR[i] * (1 - t * 0.4) + XP_TASKBAR_LIGHT[i] * t * 0.4)
                        for i in range(3))
            pygame.draw.line(screen, col, (0, tb.y + y), (WIDTH, tb.y + y))
        pygame.draw.line(screen, XP_TASKBAR_LIGHT, (0, tb.y), (WIDTH, tb.y), 2)
        pygame.draw.line(screen, XP_BLUE_DARK, (0, tb.bottom - 1), (WIDTH, tb.bottom - 1), 1)

        # Кнопка Пуск — зелёная
        start_rect = pygame.Rect(6, HEIGHT - 36, 110, 32)
        # Градиент зелёный
        for y in range(start_rect.h):
            t = y / start_rect.h
            col = tuple(int(XP_START[i] * (1 - t) + XP_START_LIGHT[i] * t) for i in range(3))
            pygame.draw.line(screen, col, (start_rect.x, start_rect.y + y),
                             (start_rect.right, start_rect.y + y))
        pygame.draw.rect(screen, (40, 100, 50), start_rect, 2)
        # Флаг + текст
        pygame.draw.rect(screen, (255, 220, 80), (start_rect.x + 8, start_rect.y + 10, 14, 12))
        txt = self.font_big.render("Пуск", True, (255, 255, 255))
        screen.blit(txt, (start_rect.x + 30, start_rect.y + 4))

        # Кнопки открытых окон (задачи)
        tx = start_rect.right + 8
        for w in self.windows:
            short = w.title.split("—")[0].strip()[:14]
            txt = self.font_small.render(short, True, (255, 255, 255))
            bw = max(120, txt.get_width() + 24)
            btn = pygame.Rect(tx, HEIGHT - 36, bw, 32)
            if w.minimized:
                bg_col = (50, 100, 180)
            else:
                bg_col = (80, 140, 220)
            for y in range(btn.h):
                t = y / btn.h
                col = tuple(int(bg_col[i] * (1 - t * 0.3)) for i in range(3))
                pygame.draw.line(screen, col, (btn.x, btn.y + y), (btn.right, btn.y + y))
            pygame.draw.rect(screen, XP_BLUE_DARK, btn, 1)
            screen.blit(txt, (btn.x + 12, btn.y + 8))
            tx += bw + 4

        # Системный трей справа — часы
        tray_w = 160
        tray_rect = pygame.Rect(WIDTH - tray_w, HEIGHT - 38, tray_w - 4, 36)
        for y in range(tray_rect.h):
            t = y / tray_rect.h
            col = tuple(int(XP_BLUE_DARK[i] * (1 - t * 0.5) + XP_TASKBAR_LIGHT[i] * t * 0.4)
                        for i in range(3))
            pygame.draw.line(screen, col, (tray_rect.x, tray_rect.y + y),
                             (tray_rect.right, tray_rect.y + y))
        pygame.draw.rect(screen, XP_BLUE_DARK, tray_rect, 1)
        # Иконки трея
        pygame.draw.rect(screen, (100, 200, 100), (tray_rect.x + 8, tray_rect.y + 12, 12, 12))
        pygame.draw.rect(screen, (220, 180, 80), (tray_rect.x + 26, tray_rect.y + 12, 12, 12))
        # Часы
        t = pygame.time.get_ticks() // 1000
        hh = (t // 3600 + 9) % 24
        mm = (t // 60) % 60
        clock = self.font_small.render(f"{hh:02d}:{mm:02d}", True, (255, 255, 255))
        screen.blit(clock, (tray_rect.right - clock.get_width() - 10, tray_rect.y + 10))

    def _draw_start_menu(self, screen):
        menu = pygame.Rect(6, HEIGHT - 320, 260, 280)
        # Тень
        shadow = pygame.Surface((menu.w + 6, menu.h + 6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 100))
        screen.blit(shadow, (menu.x + 3, menu.y + 3))

        # Верхняя часть — заголовок с именем
        header = pygame.Rect(menu.x, menu.y, menu.w, 60)
        for y in range(header.h):
            t = y / header.h
            col = tuple(int(XP_BLUE[i] * (1 - t * 0.3) + XP_BLUE_LIGHT[i] * t * 0.5)
                        for i in range(3))
            pygame.draw.line(screen, col, (header.x, header.y + y), (header.right, header.y + y))
        pygame.draw.rect(screen, XP_BLUE_DARK, header, 2)
        # Аватар
        pygame.draw.circle(screen, (255, 245, 235), (menu.x + 30, menu.y + 30), 20)
        pygame.draw.circle(screen, (240, 150, 170), (menu.x + 30, menu.y + 30), 20, 2)
        pygame.draw.circle(screen, (30, 25, 35), (menu.x + 24, menu.y + 26), 3)
        pygame.draw.circle(screen, (30, 25, 35), (menu.x + 36, menu.y + 26), 3)
        name = self.font_big.render("Зайка", True, (255, 255, 255))
        screen.blit(name, (menu.x + 60, menu.y + 18))

        # Нижняя часть — пункты
        body = pygame.Rect(menu.x, header.bottom, menu.w, menu.h - header.h)
        pygame.draw.rect(screen, (240, 240, 250), body)

        items = [
            ("Мой кролик", "mycomputer"),
            ("Интернет", "browser"),
            ("Карта", "map"),
            ("Заметки", "notes"),
            ("Калькулятор", "calc"),
        ]
        for i, (name, wid) in enumerate(items):
            iy = body.y + 8 + i * 32
            item_rect = pygame.Rect(body.x + 4, iy, body.w - 8, 30)
            mx, my = self.cursor_x, self.cursor_y
            if item_rect.collidepoint(mx, my):
                pygame.draw.rect(screen, (100, 160, 220), item_rect)
                txt_col = (255, 255, 255)
            else:
                txt_col = (20, 20, 40)
            icon = DESKTOP_ICONS[i]["icon"] if i < len(DESKTOP_ICONS) else "•"
            ic = self.font_small.render(icon, True, txt_col)
            screen.blit(ic, (item_rect.x + 8, item_rect.y + 6))
            t = self.font_small.render(name, True, txt_col)
            screen.blit(t, (item_rect.x + 32, item_rect.y + 8))

        # Разделитель + Выключение
        div_y = body.y + 8 + len(items) * 32 + 4
        pygame.draw.line(screen, (150, 150, 170), (body.x + 8, div_y), (body.right - 8, div_y), 1)

        shutdown_rect = pygame.Rect(body.x + 4, div_y + 4, body.w - 8, 32)
        mx, my = self.cursor_x, self.cursor_y
        if shutdown_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, (220, 80, 80), shutdown_rect)
            col = (255, 255, 255)
        else:
            col = (180, 40, 40)
        off = self.font_small.render("⏻  Выключить ПК", True, col)
        screen.blit(off, (shutdown_rect.x + 8, shutdown_rect.y + 8))

    def _draw_cursor(self, screen):
        x, y = int(self.cursor_x), int(self.cursor_y)
        # XP-курсор — белая стрелка с чёрным контуром
        pts_outer = [(0,0),(0,16),(4,12),(7,17),(10,16),(7,11),(12,11)]
        pts_inner = [(2,2),(2,13),(5,10),(8,15),(9,15),(6,10),(10,10)]
        pygame.draw.polygon(screen, (0, 0, 0), [(x+dx, y+dy) for dx, dy in pts_outer])
        pygame.draw.polygon(screen, (255, 255, 255), [(x+dx, y+dy) for dx, dy in pts_inner])

    def _draw_window(self, screen, w):
        # Тень
        shadow = pygame.Surface((w.rect.w + 8, w.rect.h + 8), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 80))
        screen.blit(shadow, (w.rect.x + 4, w.rect.y + 4))

        # Тело
        pygame.draw.rect(screen, XP_WINDOW_BG, w.rect)
        pygame.draw.rect(screen, XP_WINDOW_BORDER, w.rect, 2)

        # Заголовок XP — синий градиент
        title_rect = pygame.Rect(w.rect.x, w.rect.y, w.rect.w, 26)
        for y in range(title_rect.h):
            t = y / title_rect.h
            col = tuple(int(XP_TITLE[i] * (1 - t * 0.3) + XP_BLUE_LIGHT[i] * t * 0.6)
                        for i in range(3))
            pygame.draw.line(screen, col, (title_rect.x, title_rect.y + y),
                             (title_rect.right, title_rect.y + y))
        pygame.draw.rect(screen, XP_BLUE_DARK, title_rect, 1)

        title = self.font_small.render(w.title, True, (255, 255, 255))
        screen.blit(title, (title_rect.x + 8, title_rect.y + 6))

        # Кнопка закрытия (красная)
        cx = w.rect.right - 18
        cy = w.rect.y + 13
        hover = w.contains_close(self.cursor_x, self.cursor_y)
        col = (240, 90, 90) if hover else (200, 50, 50)
        close_rect = pygame.Rect(cx - 9, cy - 9, 18, 18)
        for y in range(close_rect.h):
            t = y / close_rect.h
            c = tuple(int(col[i] * (1 - t * 0.3) + 255 * t * 0.2) for i in range(3))
            pygame.draw.line(screen, c, (close_rect.x, close_rect.y + y),
                             (close_rect.right, close_rect.y + y))
        pygame.draw.rect(screen, (80, 20, 20), close_rect, 1)
        pygame.draw.line(screen, (255, 255, 255), (cx - 5, cy - 5), (cx + 5, cy + 5), 2)
        pygame.draw.line(screen, (255, 255, 255), (cx - 5, cy + 5), (cx + 5, cy - 5), 2)

        # Кнопка minimize (синяя)
        mx_ = w.rect.right - 44
        my_ = w.rect.y + 13
        hover_m = w.contains_minimize(self.cursor_x, self.cursor_y)
        col_m = (90, 140, 220) if hover_m else (60, 100, 180)
        min_rect = pygame.Rect(mx_ - 9, my_ - 9, 18, 18)
        for y in range(min_rect.h):
            t = y / min_rect.h
            c = tuple(int(col_m[i] * (1 - t * 0.3) + 255 * t * 0.2) for i in range(3))
            pygame.draw.line(screen, c, (min_rect.x, min_rect.y + y),
                             (min_rect.right, min_rect.y + y))
        pygame.draw.rect(screen, (30, 60, 120), min_rect, 1)
        pygame.draw.line(screen, (255, 255, 255), (mx_ - 5, my_ + 4), (mx_ + 5, my_ + 4), 2)

        # Содержимое
        content_rect = pygame.Rect(w.rect.x + 4, w.rect.y + 30,
                                    w.rect.w - 8, w.rect.h - 34)
        if w.wtype == "browser":
            self._draw_browser(screen, content_rect)
        elif w.wtype == "map":
            self._draw_map_content(screen, content_rect)
        elif w.wtype == "notes":
            self._draw_notes(screen, content_rect)
        elif w.wtype == "calc":
            self._draw_calc(screen, content_rect, w)
        elif w.wtype == "mycomputer":
            self._draw_mycomputer(screen, content_rect)

    def _draw_browser(self, screen, r):
        nav = pygame.Rect(r.x, r.y, r.w, 30)
        pygame.draw.rect(screen, (220, 225, 235), nav)
        pages = [("Дом", "home"), ("Новости", "news"), ("Игра", "game"),
                 ("Магазин", "shop"), ("Карта", "map")]
        btn_w = 90
        for i, (name, pid) in enumerate(pages):
            bx = nav.x + 10 + i * (btn_w + 4)
            by = nav.y + 4
            btn_rect = pygame.Rect(bx, by, btn_w, 22)
            active = (self.browser_page == pid)
            col_base = (200, 220, 255) if active else (235, 235, 245)
            draw_xp_button(screen, btn_rect, name, self.font_small,
                           hovered=False, base_col=col_base)

        url_rect = pygame.Rect(r.x + 4, nav.bottom + 4, r.w - 8, 24)
        pygame.draw.rect(screen, (255, 255, 255), url_rect)
        pygame.draw.rect(screen, (100, 110, 140), url_rect, 1)
        url_txt = self.font_small.render(self.browser_url, True, (40, 40, 70))
        screen.blit(url_txt, (url_rect.x + 6, url_rect.y + 5))

        cont = pygame.Rect(r.x + 4, url_rect.bottom + 4, r.w - 8, r.h - (url_rect.bottom - r.y) - 8)
        pygame.draw.rect(screen, (255, 255, 255), cont)
        pygame.draw.rect(screen, (100, 110, 140), cont, 1)
        self._draw_browser_content(screen, cont)

    def _draw_browser_content(self, screen, r):
        p = self.browser_page
        if p == "home":
            title = self.font_big.render("🐰 Добро пожаловать в BunnyNet!", True, (40, 80, 150))
            screen.blit(title, (r.x + 20, r.y + 20))
            lines = [
                "Здесь ты найдёшь всё о морковке и приключениях.",
                "",
                "Вкладки: Новости, Игра, Магазин, Карта.",
                "Нажми любую — и погнали!",
            ]
            for i, line in enumerate(lines):
                t = self.font_small.render(line, True, (40, 50, 80))
                screen.blit(t, (r.x + 20, r.y + 60 + i * 22))
        elif p == "news":
            title = self.font_small.render("📰 Новости Морковного Края", True, (140, 60, 80))
            screen.blit(title, (r.x + 20, r.y + 20))
            news = [
                "• В деревне открыт новый колодец!",
                "• Урожай морковки — рекордный!",
                "• Замечена странная тень у восточного озера...",
                "• Торговец снизил цены на удобрения.",
                "• BunnyOS 1.1 скоро — с мышками-помощниками!",
            ]
            for i, line in enumerate(news):
                t = self.font_small.render(line, True, (60, 60, 80))
                screen.blit(t, (r.x + 20, r.y + 50 + i * 22))
        elif p == "game":
            title = self.font_big.render("🎮 Игра: Прыгни Выше!", True, (140, 80, 160))
            screen.blit(title, (r.x + 20, r.y + 20))
            t = self.font_small.render("(Здесь могла быть мини-игра)", True, (100, 100, 120))
            screen.blit(t, (r.x + 20, r.y + 60))
            for i in range(6):
                x = r.x + 40 + i * 60
                y = r.y + 130 + int(math.sin(self.desk_anim * 3 + i) * 12)
                pygame.draw.circle(screen, (250, 240, 220), (x, y), 16)
                pygame.draw.circle(screen, (30, 25, 35), (x, y), 16, 2)
                pygame.draw.circle(screen, (240, 150, 170), (x - 5, y - 18), 5)
                pygame.draw.circle(screen, (240, 150, 170), (x + 5, y - 18), 5)
                pygame.draw.circle(screen, (30, 25, 35), (x - 5, y - 2), 2)
                pygame.draw.circle(screen, (30, 25, 35), (x + 5, y - 2), 2)
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
        if self.world_map_surface is None:
            t = self.font_small.render("Карта недоступна", True, (100, 100, 120))
            screen.blit(t, (r.x + 20, r.y + 20))
            return
        map_img = pygame.transform.smoothscale(
            self.world_map_surface, (r.w - 20, r.h - 20))
        screen.blit(map_img, (r.x + 10, r.y + 10))

    def _draw_notes(self, screen, r):
        pygame.draw.rect(screen, (255, 250, 220), r)
        pygame.draw.rect(screen, (200, 180, 130), r, 2)
        for i in range(1, 15):
            y = r.y + i * 22
            pygame.draw.line(screen, (220, 210, 180), (r.x, y), (r.right, y), 1)
        lines = self.notes_text.split("\n")
        for i, line in enumerate(lines):
            t = self.font_small.render(line, True, (60, 50, 40))
            screen.blit(t, (r.x + 12, r.y + 8 + i * 22))

    def _draw_calc(self, screen, r, w):
        # Фон
        pygame.draw.rect(screen, (235, 235, 240), r)
        # Дисплей
        disp = pygame.Rect(r.x + 10, r.y + 10, r.w - 20, 60)
        for y in range(disp.h):
            t = y / disp.h
            col = (int(240 - 20 * t), int(250 - 20 * t), int(220 - 20 * t))
            pygame.draw.line(screen, col, (disp.x, disp.y + y), (disp.right, disp.y + y))
        pygame.draw.rect(screen, (60, 80, 60), disp, 2)
        # Текст дисплея — выравнивание вправо
        val = self.calc_display
        if len(val) > 14:
            val = val[:14] + "…"
        t = self.font_big.render(val, True, (30, 60, 30))
        screen.blit(t, (disp.right - t.get_width() - 10, disp.y + 14))

        # Кнопки — с нажатием и hover
        mx, my = self.cursor_x, self.cursor_y
        buttons = self._calc_buttons(w)
        for label, brect in buttons:
            hover = brect.collidepoint(mx, my)
            if label in ("=",):
                base = (100, 160, 220)
                txt_col = (255, 255, 255)
            elif label in ("C", "←"):
                base = (220, 120, 120)
                txt_col = (255, 255, 255)
            elif label in ("+", "-", "*", "/"):
                base = (180, 200, 220)
                txt_col = (20, 40, 80)
            else:
                base = (245, 245, 250)
                txt_col = (20, 30, 60)
            if hover:
                base = tuple(min(255, c + 20) for c in base)
            # Рисуем кнопку
            for y in range(brect.h):
                tt = y / brect.h
                col = tuple(int(base[i] * (1 - tt * 0.15) + 255 * tt * 0.1)
                            for i in range(3))
                pygame.draw.line(screen, col, (brect.x, brect.y + y),
                                 (brect.right, brect.y + y))
            pygame.draw.rect(screen, (80, 90, 120), brect, 1)
            pygame.draw.line(screen, (255, 255, 255), (brect.x + 1, brect.y + 1),
                             (brect.right - 2, brect.y + 1))
            txt = self.font_big.render(label, True, txt_col)
            screen.blit(txt, (brect.centerx - txt.get_width() // 2,
                              brect.centery - txt.get_height() // 2))

    def _draw_mycomputer(self, screen, r):
        pygame.draw.rect(screen, (255, 255, 255), r)
        pygame.draw.rect(screen, (100, 110, 140), r, 1)
        title = self.font_big.render("Мой кролик", True, (40, 80, 150))
        screen.blit(title, (r.x + 14, r.y + 10))
        # Диски
        disks = [
            ("💾 BunnyOS (C:)", "13.7 ГБ свободно"),
            ("🌿 Морковный диск (D:)", "48.2 ГБ свободно"),
            ("📀 CD — Урожай 2026", "пустой"),
        ]
        for i, (name, info) in enumerate(disks):
            y = r.y + 60 + i * 70
            icon_rect = pygame.Rect(r.x + 14, y, 50, 50)
            pygame.draw.rect(screen, (120, 160, 220), icon_rect)
            pygame.draw.rect(screen, (40, 80, 140), icon_rect, 2)
            t = self.font_small.render(name, True, (20, 30, 60))
            screen.blit(t, (r.x + 80, y + 6))
            t2 = self.font_small.render(info, True, (100, 100, 120))
            screen.blit(t2, (r.x + 80, y + 28))
