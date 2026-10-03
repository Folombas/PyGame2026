"""BunnyOS — ядро Carrot Linux в обличье Windows 10."""
import math
import pygame
from settings import WIDTH, HEIGHT
import os_sounds


def _clamp(t):
    return tuple(max(0, min(255, int(x))) for x in t)


# Win10 цвета
TASKBAR = (28, 28, 28)
TASKBAR_HOVER = (55, 55, 55)
WIN_BG = (243, 243, 243)
WIN_TITLE = (255, 255, 255)
WIN_TITLE_TEXT = (30, 30, 30)
WIN_BORDER = (200, 200, 200)
ACCENT = (0, 120, 215)
BTN = (225, 225, 225)
BTN_HOVER = (200, 220, 240)
BTN_PRESS = (150, 190, 230)
CLOSE_HOVER = (232, 17, 35)
DESKTOP_BG = (0, 120, 215)

DESKTOP_ICONS = [
    {"id": "mycomputer", "name": "Мой кролик", "icon": "🖥"},
    {"id": "browser",    "name": "Интернет",   "icon": "🌐"},
    {"id": "map",        "name": "Карта",      "icon": "🗺"},
    {"id": "notes",      "name": "Заметки",    "icon": "📝"},
    {"id": "calc",       "name": "Калькулятор","icon": "🔢"},
]


class Window:
    TITLE_H = 32

    def __init__(self, wtype, x, y, w=580, h=400, title="Окно"):
        self.wtype = wtype
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.minimized = False

    def on_titlebar(self, mx, my):
        return (self.rect.x <= mx < self.rect.right and
                self.rect.y <= my < self.rect.y + self.TITLE_H)

    def on_close(self, mx, my):
        cx = self.rect.right - 22
        cy = self.rect.y + self.TITLE_H // 2
        return (cx - 14 <= mx <= cx + 14 and cy - 14 <= my <= cy + 14)

    def on_minimize(self, mx, my):
        cx = self.rect.right - 68
        cy = self.rect.y + self.TITLE_H // 2
        return (cx - 14 <= mx <= cx + 14 and cy - 14 <= my <= cy + 14)


class MiniPC:
    def __init__(self, font_small, font_big, world_map_surface=None):
        self.font_small = font_small
        self.font_big = font_big
        self.world_map_surface = world_map_surface
        self.cursor_x = WIDTH // 2
        self.cursor_y = HEIGHT // 2
        self.cursor_speed = 12
        self.windows = []
        self.icon_rects = []
        self.browser_page = "home"
        self.browser_url = "bunny://home"
        self.notes_text = ("Привет, я Зайка!\n\n"
                           "BunnyOS · ядро Carrot Linux 5.15\n"
                           "(UI в стиле Windows 10)\n\n"
                           "Заметки:\n"
                           "- Полить морковь и капусту\n"
                           "- Проверить грядки\n"
                           "- Изучить восточное озеро")
        self.toast = None
        self.toast_timer = 0
        self.desk_anim = 0.0
        self.start_open = False
        self.start_pressed = 0        # таймер нажатия
        self.active_idx = -1
        # Калькулятор — единый дисплей с полной строкой
        self.calc_expr = ""           # "2 - 1 = 1"
        self.calc_tokens = []         # ["2", "-", "1"]
        self.calc_current = "0"
        self.calc_after_eq = False

    # ============= ОКНА =============
    def toggle_window(self, wtype):
        for w in self.windows:
            if w.wtype == wtype:
                w.minimized = False
                self.windows.remove(w)
                self.windows.append(w)
                self.active_idx = len(self.windows) - 1
                return
        titles = {"mycomputer": "Мой кролик",
                  "browser": "BunnyNet Explorer",
                  "map": "Карта мира",
                  "notes": "Заметки — Блокнот",
                  "calc": "Калькулятор"}
        x = 180 + len(self.windows) * 30
        y = 80 + len(self.windows) * 30
        w = Window(wtype, x, y, title=titles.get(wtype, wtype))
        if wtype == "map": w.rect.w, w.rect.h = 720, 500
        if wtype == "calc": w.rect.w, w.rect.h = 340, 500
        if wtype == "notes": w.rect.w, w.rect.h = 500, 400
        self.windows.append(w)
        self.active_idx = len(self.windows) - 1

    def close_window(self, w):
        if w in self.windows:
            self.windows.remove(w)
            if self.active_idx >= len(self.windows):
                self.active_idx = len(self.windows) - 1

    def handle_key(self, key):
        """Клавиши в PC. Возвращает 'shutdown' или None."""
        if key == pygame.K_UP and self.windows:
            self.active_idx = (self.active_idx - 1) % len(self.windows)
            os_sounds.play("click")
        elif key == pygame.K_DOWN and self.windows:
            self.active_idx = (self.active_idx + 1) % len(self.windows)
            os_sounds.play("click")
        elif key in (pygame.K_RETURN, pygame.K_SPACE) and self.windows:
            w = self.windows[self.active_idx]
            w.minimized = not w.minimized
            os_sounds.play("click")
        return None

    def update(self, keys, dt):
        self.desk_anim += dt
        if self.start_pressed > 0:
            self.start_pressed -= 1
        # WASD курсор
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.cursor_x -= self.cursor_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.cursor_x += self.cursor_speed
        if keys[pygame.K_w]:  self.cursor_y -= self.cursor_speed
        if keys[pygame.K_s]:  self.cursor_y += self.cursor_speed
        self.cursor_x = max(0, min(WIDTH - 1, self.cursor_x))
        self.cursor_y = max(0, min(HEIGHT - 1, self.cursor_y))
        # мышь
        mx, my = pygame.mouse.get_pos()
        if abs(mx - self.cursor_x) > 40 or abs(my - self.cursor_y) > 40:
            self.cursor_x, self.cursor_y = mx, my
        if self.toast_timer > 0:
            self.toast_timer -= 1

    # ============= КЛИКИ =============
    def handle_click(self, mx, my, button=1):
        # Кнопка Пуск
        start_rect = pygame.Rect(6, HEIGHT - 44, 56, 44)
        if start_rect.collidepoint(mx, my):
            self.start_open = not self.start_open
            self.start_pressed = 10
            os_sounds.play("click")
            return

        # Меню Пуск
        if self.start_open:
            menu = pygame.Rect(6, HEIGHT - 400, 260, 356)
            if menu.collidepoint(mx, my):
                items = [("Мой кролик", "mycomputer"),
                         ("Интернет", "browser"),
                         ("Карта", "map"),
                         ("Заметки", "notes"),
                         ("Калькулятор", "calc"),
                         ("", None),
                         ("Выключить ПК", "shutdown")]
                for i, (name, wid) in enumerate(items):
                    iy = menu.y + 50 + i * 40
                    r = pygame.Rect(menu.x + 4, iy, menu.w - 8, 36)
                    if r.collidepoint(mx, my) and wid:
                        if wid == "shutdown":
                            self.start_open = False
                            os_sounds.play("shutdown")
                            return "shutdown"
                        self.toggle_window(wid)
                        self.start_open = False
                        return
                return
            else:
                self.start_open = False
                return

        # Панель задач — окна
        tx = 70
        for i, w in enumerate(self.windows):
            short = w.title.split("—")[0].strip()[:14]
            txt = self.font_small.render(short, True, (255, 255, 255))
            bw = max(150, txt.get_width() + 32)
            r = pygame.Rect(tx, HEIGHT - 44, bw, 44)
            if r.collidepoint(mx, my):
                self.active_idx = i
                w.minimized = not w.minimized
                os_sounds.play("click")
                return
            tx += bw + 4

        # Окна
        for w in reversed(self.windows):
            if w.minimized: continue
            if w.on_close(mx, my):
                self.close_window(w); os_sounds.play("click"); return
            if w.on_minimize(mx, my):
                w.minimized = True; os_sounds.play("click"); return
            if w.on_titlebar(mx, my):
                w.dragging = True
                w.drag_offset = (mx - w.rect.x, my - w.rect.y)
                self.windows.remove(w); self.windows.append(w)
                self.active_idx = len(self.windows) - 1
                return
            if w.rect.collidepoint(mx, my):
                self.windows.remove(w); self.windows.append(w)
                self.active_idx = len(self.windows) - 1
                self._window_click(w, mx, my)
                return

        # Иконки
        for r, ic in self.icon_rects:
            if r.collidepoint(mx, my):
                self.toggle_window(ic["id"]); return

    def mouse_up(self):
        for w in self.windows:
            w.dragging = False

    def mouse_motion(self, mx, my):
        for w in self.windows:
            if w.dragging:
                w.rect.x = mx - w.drag_offset[0]
                w.rect.y = my - w.drag_offset[1]

    def _window_click(self, w, mx, my):
        if w.wtype == "browser":
            rel_y = my - w.rect.y
            if 36 < rel_y < 66:
                pages = ["home", "news", "game", "shop", "map"]
                for i, p in enumerate(pages):
                    bx = w.rect.x + 10 + i * 94
                    if bx <= mx < bx + 90:
                        self.browser_page = p
                        self.browser_url = f"bunny://{p}"
                        return
        elif w.wtype == "calc":
            for label, r in self._calc_buttons(w):
                if r.collidepoint(mx, my):
                    self._calc_press(label)
                    os_sounds.play("click")
                    return

    # ============= КАЛЬКУЛЯТОР =============
    def _calc_buttons(self, w):
        r = w.rect
        disp_h = 110
        gx = r.x + 12
        gy = r.y + w.TITLE_H + disp_h + 12
        gap = 6
        bw = (r.w - 24 - 3 * gap) // 4
        bh = 56
        layout = [
            ["C", "←", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["±", "0", ".", "="],
        ]
        out = []
        for i, row in enumerate(layout):
            for j, lbl in enumerate(row):
                out.append((lbl, pygame.Rect(gx + j * (bw + gap),
                                              gy + i * (bh + gap),
                                              bw, bh)))
        return out

    def _calc_press(self, lbl):
        if lbl == "C":
            self.calc_tokens = []
            self.calc_current = "0"
            self.calc_after_eq = False
            self.calc_expr = ""
            return
        if lbl == "←":
            if self.calc_after_eq:
                self.calc_tokens = []; self.calc_current = "0"
                self.calc_after_eq = False; self.calc_expr = ""
                return
            if len(self.calc_current) > 1:
                self.calc_current = self.calc_current[:-1]
            else:
                self.calc_current = "0"
            return
        if lbl == "±":
            if self.calc_current.startswith("-"):
                self.calc_current = self.calc_current[1:]
            elif self.calc_current != "0":
                self.calc_current = "-" + self.calc_current
            return
        if lbl == "%":
            try:
                v = float(self.calc_current) / 100
                self.calc_current = self._fmt(v)
            except ValueError:
                pass
            return
        if lbl in ("+", "-", "*", "/"):
            if self.calc_after_eq:
                self.calc_tokens = [self.calc_current, lbl]
                self.calc_current = "0"
                self.calc_after_eq = False
                return
            # если уже нажали число и оператор — фиксируем
            if not self.calc_tokens or self.calc_tokens[-1] in ("+", "-", "*", "/"):
                # предыдущее число = текущее
                if self.calc_tokens:
                    self.calc_tokens[-1] = lbl
                else:
                    self.calc_tokens = [self.calc_current, lbl]
                self.calc_current = "0"
                return
            self.calc_tokens.append(self.calc_current)
            self.calc_tokens.append(lbl)
            self.calc_current = "0"
            return
        if lbl == "=":
            if not self.calc_tokens:
                self.calc_expr = f"{self.calc_current} ="
                return
            # собираем выражение
            full = self.calc_tokens + [self.calc_current]
            expr_str = " ".join(full)
            try:
                result = self._eval(full)
                self.calc_expr = f"{expr_str} = {self._fmt(result)}"
                self.calc_current = self._fmt(result)
            except (ValueError, ZeroDivisionError):
                self.calc_expr = f"{expr_str} = Ошибка"
                os_sounds.play("error")
            self.calc_tokens = []
            self.calc_after_eq = True
            return
        if lbl == ".":
            if self.calc_after_eq:
                self.calc_current = "0."
                self.calc_after_eq = False
                self.calc_tokens = []
                self.calc_expr = ""
                return
            if "." not in self.calc_current:
                self.calc_current += "."
            return
        # цифра
        if self.calc_after_eq:
            self.calc_current = lbl
            self.calc_after_eq = False
            self.calc_tokens = []
            self.calc_expr = ""
            return
        if self.calc_current == "0":
            self.calc_current = lbl
        else:
            self.calc_current += lbl

    def _eval(self, tokens):
        """Токены вида [число, оп, число, оп, ...]"""
        vals = [float(t) for t in tokens[0::2]]
        ops = tokens[1::2]
        stack_vals = [vals[0]]
        stack_ops = []
        for i, op in enumerate(ops):
            v = vals[i + 1] if i + 1 < len(vals) else 0
            if op in ("*", "/"):
                if op == "*":
                    stack_vals[-1] *= v
                else:
                    if v == 0: raise ZeroDivisionError()
                    stack_vals[-1] /= v
            else:
                stack_ops.append(op)
                stack_vals.append(v)
        res = stack_vals[0]
        for i, op in enumerate(stack_ops):
            v = stack_vals[i + 1]
            res = res + v if op == "+" else res - v
        return res

    def _fmt(self, v):
        if abs(v - int(v)) < 1e-9:
            return str(int(v))
        return f"{v:.6f}".rstrip("0").rstrip(".")

    # ============= DRAW =============
    def draw(self, screen):
        # Фон — синий Win10
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(0 + 20 * t)
            g = int(100 + 40 * t)
            b = int(180 + 50 * t)
            screen.fill((r, g, b), (0, y, WIDTH, 1))

        # Декор — круги
        for cx, cy, cr in [(180, 280, 160), (900, 180, 200), (520, 480, 150)]:
            s = pygame.Surface((cr * 2, cr * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, 20), (cr, cr), cr)
            screen.blit(s, (cx - cr, cy - cr))

        # Иконки
        self.icon_rects = []
        mx, my = self.cursor_x, self.cursor_y
        for i, ic in enumerate(DESKTOP_ICONS):
            r = pygame.Rect(30, 30 + i * 110, 100, 100)
            self.icon_rects.append((r, ic))
            if r.collidepoint(mx, my):
                bg = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                bg.fill((255, 255, 255, 50))
                screen.blit(bg, r.topleft)
                pygame.draw.rect(screen, (255, 255, 255), r, 1)
            sym = self.font_big.render(ic["icon"], True, (255, 255, 255))
            screen.blit(sym, (r.centerx - sym.get_width() // 2, r.y + 14))
            sh = self.font_small.render(ic["name"], True, (0, 0, 0))
            nm = self.font_small.render(ic["name"], True, (255, 255, 255))
            nx = r.centerx - nm.get_width() // 2
            ny = r.bottom - 24
            screen.blit(sh, (nx + 1, ny + 1))
            screen.blit(nm, (nx, ny))

        # Окна
        for i, w in enumerate(self.windows):
            if not w.minimized:
                self._draw_window(screen, w, i == self.active_idx)

        # Меню Пуск
        if self.start_open:
            self._draw_start_menu(screen)

        # Taskbar
        self._draw_taskbar(screen)

        # Toast
        if self.toast and self.toast_timer > 0:
            t = self.font_small.render(self.toast, True, (255, 255, 255))
            bg = pygame.Surface((t.get_width() + 20, 30), pygame.SRCALPHA)
            bg.fill((40, 60, 100, 230))
            pygame.draw.rect(bg, (100, 160, 240), (0, 0, bg.get_width(), 30), 2)
            screen.blit(bg, (WIDTH - bg.get_width() - 20, 20))
            screen.blit(t, (WIDTH - bg.get_width() - 10, 26))

        # Курсор
        self._draw_cursor(screen)

    def _draw_taskbar(self, screen):
        tb = pygame.Rect(0, HEIGHT - 44, WIDTH, 44)
        pygame.draw.rect(screen, TASKBAR, tb)

        # Кнопка Пуск
        sr = pygame.Rect(6, HEIGHT - 44, 56, 44)
        hover = sr.collidepoint(self.cursor_x, self.cursor_y)
        # Нажатие — визуально сдвигаем и темним
        pressed = self.start_pressed > 0
        if pressed:
            pygame.draw.rect(screen, (70, 70, 70), sr)
        elif hover or self.start_open:
            pygame.draw.rect(screen, TASKBAR_HOVER, sr)
        # 4 квадрата Win10
        offset = 2 if pressed else 0
        qx = sr.x + 20
        qy = sr.y + 14 + offset
        for dx, dy in [(0, 0), (9, 0), (0, 9), (9, 9)]:
            pygame.draw.rect(screen, (255, 255, 255), (qx + dx, qy + dy, 7, 7))

        # Окна — на панели задач
        tx = 70
        for i, w in enumerate(self.windows):
            short = w.title.split("—")[0].strip()[:14]
            txt = self.font_small.render(short, True, (255, 255, 255))
            bw = max(150, txt.get_width() + 32)
            r = pygame.Rect(tx, HEIGHT - 44, bw, 44)
            is_active = (i == self.active_idx) and not w.minimized
            # Подсветка выбранного стрелками
            if is_active:
                pygame.draw.rect(screen, (60, 90, 130), r)
            elif r.collidepoint(self.cursor_x, self.cursor_y):
                pygame.draw.rect(screen, TASKBAR_HOVER, r)
            # Полоска снизу — Win10 индикатор активного
            if not w.minimized:
                pygame.draw.rect(screen, ACCENT, (r.x + 20, r.bottom - 3, r.w - 40, 3))
            screen.blit(txt, (r.x + 16, r.y + 12))
            tx += bw + 4

        # Трей — часы
        t = pygame.time.get_ticks() // 1000
        hh = (t // 3600 + 9) % 24
        mm = (t // 60) % 60
        clock = self.font_small.render(f"{hh:02d}:{mm:02d}", True, (255, 255, 255))
        date = self.font_small.render("03.10.2026", True, (200, 200, 200))
        screen.blit(clock, (WIDTH - clock.get_width() - 14, HEIGHT - 34))
        screen.blit(date, (WIDTH - 100, HEIGHT - 16))

    def _draw_start_menu(self, screen):
        menu = pygame.Rect(6, HEIGHT - 400, 260, 356)
        shadow = pygame.Surface((menu.w + 8, menu.h + 8), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 100))
        screen.blit(shadow, (menu.x + 4, menu.y + 4))
        pygame.draw.rect(screen, WIN_BG, menu)
        pygame.draw.rect(screen, WIN_BORDER, menu, 1)

        # Заголовок с аватаром
        head = pygame.Rect(menu.x, menu.y, menu.w, 52)
        pygame.draw.rect(screen, ACCENT, head)
        pygame.draw.circle(screen, (255, 245, 235), (menu.x + 28, menu.y + 26), 18)
        pygame.draw.circle(screen, (30, 25, 35), (menu.x + 22, menu.y + 22), 3)
        pygame.draw.circle(screen, (30, 25, 35), (menu.x + 34, menu.y + 22), 3)
        pygame.draw.circle(screen, (240, 150, 170), (menu.x + 28, menu.y + 30), 3)
        name = self.font_big.render("Зайка", True, (255, 255, 255))
        screen.blit(name, (menu.x + 60, menu.y + 16))

        items = [("Мой кролик", "mycomputer"),
                 ("Интернет", "browser"),
                 ("Карта", "map"),
                 ("Заметки", "notes"),
                 ("Калькулятор", "calc")]
        mx, my = self.cursor_x, self.cursor_y
        for i, (name, wid) in enumerate(items):
            iy = menu.y + 58 + i * 40
            r = pygame.Rect(menu.x + 4, iy, menu.w - 8, 36)
            if r.collidepoint(mx, my):
                pygame.draw.rect(screen, BTN_HOVER, r)
            icon = DESKTOP_ICONS[i]["icon"]
            ic = self.font_small.render(icon, True, (30, 30, 30))
            screen.blit(ic, (r.x + 8, r.y + 8))
            t = self.font_small.render(name, True, (30, 30, 30))
            screen.blit(t, (r.x + 36, r.y + 10))

        # Разделитель + Выключение
        div_y = menu.y + 58 + len(items) * 40 + 6
        pygame.draw.line(screen, (200, 200, 200), (menu.x + 8, div_y),
                         (menu.right - 8, div_y), 1)
        sr = pygame.Rect(menu.x + 4, div_y + 6, menu.w - 8, 36)
        hov = sr.collidepoint(mx, my)
        if hov:
            pygame.draw.rect(screen, (240, 220, 220), sr)
        ic = self.font_small.render("⏻", True, (180, 40, 40))
        screen.blit(ic, (sr.x + 8, sr.y + 8))
        t = self.font_small.render("Выключить ПК", True, (180, 40, 40))
        screen.blit(t, (sr.x + 36, sr.y + 10))

    def _draw_cursor(self, screen):
        x, y = int(self.cursor_x), int(self.cursor_y)
        pts_o = [(0,0),(0,16),(4,12),(7,17),(10,16),(7,11),(12,11)]
        pts_i = [(2,2),(2,13),(5,10),(8,15),(9,15),(6,10),(10,10)]
        pygame.draw.polygon(screen, (0, 0, 0), [(x+dx, y+dy) for dx, dy in pts_o])
        pygame.draw.polygon(screen, (255, 255, 255), [(x+dx, y+dy) for dx, dy in pts_i])

    def _draw_window(self, screen, w, active):
        sh = pygame.Surface((w.rect.w + 8, w.rect.h + 8), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 90))
        screen.blit(sh, (w.rect.x + 4, w.rect.y + 4))
        pygame.draw.rect(screen, WIN_BG, w.rect)
        border = ACCENT if active else WIN_BORDER
        pygame.draw.rect(screen, border, w.rect, 1)

        # Title bar — Win10 светлая полоса
        tb = pygame.Rect(w.rect.x, w.rect.y, w.rect.w, w.TITLE_H)
        pygame.draw.rect(screen, WIN_TITLE, tb)
        pygame.draw.line(screen, WIN_BORDER, (tb.x, tb.bottom), (tb.right, tb.bottom), 1)
        title = self.font_small.render(w.title, True, WIN_TITLE_TEXT)
        screen.blit(title, (tb.x + 12, tb.y + 8))

        # Кнопка close (Win10 стиль)
        cx = w.rect.right - 22
        cy = w.rect.y + 16
        hov = w.on_close(self.cursor_x, self.cursor_y)
        if hov:
            pygame.draw.rect(screen, CLOSE_HOVER, (cx - 22, w.rect.y, 22, w.TITLE_H))
            col = (255, 255, 255)
        else:
            col = (30, 30, 30)
        pygame.draw.line(screen, col, (cx - 5, cy - 5), (cx + 5, cy + 5), 2)
        pygame.draw.line(screen, col, (cx - 5, cy + 5), (cx + 5, cy - 5), 2)

        # Minimize
        mx_ = w.rect.right - 68
        my_ = w.rect.y + 16
        hov_m = w.on_minimize(self.cursor_x, self.cursor_y)
        if hov_m:
            pygame.draw.rect(screen, (230, 230, 230), (mx_ - 22, w.rect.y, 22, w.TITLE_H))
        pygame.draw.line(screen, (30, 30, 30), (mx_ - 5, my_ + 4), (mx_ + 5, my_ + 4), 2)

        # Содержимое
        cr = pygame.Rect(w.rect.x + 4, w.rect.y + w.TITLE_H + 2,
                          w.rect.w - 8, w.rect.h - w.TITLE_H - 6)
        if w.wtype == "browser": self._draw_browser(screen, cr)
        elif w.wtype == "map": self._draw_map_content(screen, cr)
        elif w.wtype == "notes": self._draw_notes(screen, cr)
        elif w.wtype == "calc": self._draw_calc(screen, cr, w)
        elif w.wtype == "mycomputer": self._draw_mycomputer(screen, cr)

    def _draw_browser(self, screen, r):
        nav = pygame.Rect(r.x, r.y, r.w, 30)
        pygame.draw.rect(screen, (240, 240, 240), nav)
        pages = [("Дом", "home"), ("Новости", "news"), ("Игра", "game"),
                 ("Магазин", "shop"), ("Карта", "map")]
        for i, (name, pid) in enumerate(pages):
            bx = nav.x + 10 + i * 94
            br = pygame.Rect(bx, nav.y + 4, 90, 22)
            active = self.browser_page == pid
            bg = (200, 220, 240) if active else (250, 250, 250)
            pygame.draw.rect(screen, bg, br)
            pygame.draw.rect(screen, (180, 180, 180), br, 1)
            t = self.font_small.render(name, True, (30, 30, 30))
            screen.blit(t, (br.centerx - t.get_width() // 2, br.y + 3))

        url_r = pygame.Rect(r.x + 4, nav.bottom + 4, r.w - 8, 24)
        pygame.draw.rect(screen, (255, 255, 255), url_r)
        pygame.draw.rect(screen, (200, 200, 200), url_r, 1)
        t = self.font_small.render(self.browser_url, True, (40, 40, 70))
        screen.blit(t, (url_r.x + 6, url_r.y + 5))

        cont = pygame.Rect(r.x + 4, url_r.bottom + 4, r.w - 8,
                           r.h - (url_r.bottom - r.y) - 6)
        pygame.draw.rect(screen, (255, 255, 255), cont)
        pygame.draw.rect(screen, (200, 200, 200), cont, 1)
        self._browser_content(screen, cont)

    def _browser_content(self, screen, r):
        p = self.browser_page
        if p == "home":
            t = self.font_big.render("BunnyNet · Добро пожаловать!", True, ACCENT)
            screen.blit(t, (r.x + 20, r.y + 20))
            for i, line in enumerate(["Здесь всё о морковке и приключениях.",
                                      "Вкладки: Новости, Игра, Магазин, Карта."]):
                s = self.font_small.render(line, True, (60, 60, 80))
                screen.blit(s, (r.x + 20, r.y + 60 + i * 22))
        elif p == "news":
            t = self.font_small.render("Новости Морковного Края", True, (140, 60, 80))
            screen.blit(t, (r.x + 20, r.y + 20))
            news = ["· Открыт новый колодец в деревне!",
                    "· Урожай капусты в этом году — рекордный.",
                    "· Замечена тень у восточного озера...",
                    "· BunnyOS 1.1 — с мышками-помощниками!"]
            for i, l in enumerate(news):
                s = self.font_small.render(l, True, (60, 60, 80))
                screen.blit(s, (r.x + 20, r.y + 50 + i * 22))
        elif p == "game":
            t = self.font_big.render("Игра: Прыгни Выше!", True, (140, 80, 160))
            screen.blit(t, (r.x + 20, r.y + 20))
            for i in range(6):
                x = r.x + 50 + i * 70
                y = r.y + 130 + int(math.sin(self.desk_anim * 3 + i) * 12)
                pygame.draw.circle(screen, (250, 240, 220), (x, y), 16)
                pygame.draw.circle(screen, (30, 25, 35), (x, y), 16, 2)
                pygame.draw.circle(screen, (240, 150, 170), (x - 5, y - 18), 5)
                pygame.draw.circle(screen, (240, 150, 170), (x + 5, y - 18), 5)
        elif p == "shop":
            t = self.font_small.render("Магазин Семян", True, (100, 130, 60))
            screen.blit(t, (r.x + 20, r.y + 20))
            items = [("Семена моркови — 5🪙", (240, 130, 60)),
                     ("Семена капусты — 8🪙", (140, 200, 120)),
                     ("Удобрение — 10🪙", (140, 90, 50)),
                     ("Лейка — 25🪙", (100, 160, 220))]
            for i, (n, c) in enumerate(items):
                y = r.y + 50 + i * 30
                pygame.draw.rect(screen, c, (r.x + 20, y, 20, 20))
                t = self.font_small.render(n, True, (60, 60, 80))
                screen.blit(t, (r.x + 50, y + 3))
        elif p == "map":
            self._draw_map_content(screen, r)

    def _draw_map_content(self, screen, r):
        if self.world_map_surface is None:
            return
        img = pygame.transform.smoothscale(self.world_map_surface,
                                           (r.w - 20, r.h - 20))
        screen.blit(img, (r.x + 10, r.y + 10))

    def _draw_notes(self, screen, r):
        pygame.draw.rect(screen, (255, 250, 220), r)
        lines = self.notes_text.split("\n")
        for i, l in enumerate(lines):
            t = self.font_small.render(l, True, (40, 40, 40))
            screen.blit(t, (r.x + 12, r.y + 8 + i * 22))

    def _draw_calc(self, screen, r, w):
        pygame.draw.rect(screen, (235, 235, 240), r)
        # Единый дисплей — показываем полную строку
        disp = pygame.Rect(r.x + 12, r.y + 12, r.w - 24, 96)
        pygame.draw.rect(screen, (255, 255, 255), disp)
        pygame.draw.rect(screen, (200, 200, 200), disp, 1)

        # Основная строка — вся формула
        display_text = self.calc_expr if self.calc_expr else self.calc_current
        # Автоматически уменьшаем шрифт если не влезает
        font = self.font_big
        txt = font.render(display_text, True, (30, 30, 30))
        while txt.get_width() > disp.w - 16 and font.get_height() > 10:
            font = pygame.font.SysFont("monospace", font.get_height() - 2, bold=True)
            txt = font.render(display_text, True, (30, 30, 30))
        # Выравнивание справа
        screen.blit(txt, (disp.right - txt.get_width() - 8,
                          disp.centery - txt.get_height() // 2))

        # Кнопки
        mx, my = self.cursor_x, self.cursor_y
        for lbl, br in self._calc_buttons(w):
            hov = br.collidepoint(mx, my)
            if lbl in ("=",):
                base = ACCENT
                tc = (255, 255, 255)
            elif lbl in ("C", "←"):
                base = (220, 120, 120)
                tc = (255, 255, 255)
            elif lbl in ("+", "-", "*", "/", "%", "±"):
                base = (200, 220, 240)
                tc = (20, 40, 80)
            else:
                base = (250, 250, 255)
                tc = (30, 30, 30)
            if hov:
                base = _clamp(tuple(c + 20 for c in base))
            pygame.draw.rect(screen, base, br)
            pygame.draw.rect(screen, (160, 160, 170), br, 1)
            t = self.font_big.render(lbl, True, tc)
            screen.blit(t, (br.centerx - t.get_width() // 2,
                            br.centery - t.get_height() // 2))

    def _draw_mycomputer(self, screen, r):
        pygame.draw.rect(screen, (255, 255, 255), r)
        t = self.font_big.render("Мой кролик", True, ACCENT)
        screen.blit(t, (r.x + 14, r.y + 10))
        disks = [("💾 BunnyOS (C:)", "13.7 ГБ свободно"),
                 ("🌿 Морковный (D:)", "48.2 ГБ свободно"),
                 ("📀 CD — Урожай 2026", "пустой")]
        for i, (n, info) in enumerate(disks):
            y = r.y + 60 + i * 70
            ic = pygame.Rect(r.x + 14, y, 50, 50)
            pygame.draw.rect(screen, ACCENT, ic)
            pygame.draw.rect(screen, (40, 80, 140), ic, 2)
            a = self.font_small.render(n, True, (20, 30, 60))
            screen.blit(a, (r.x + 80, y + 6))
            b = self.font_small.render(info, True, (100, 100, 120))
            screen.blit(b, (r.x + 80, y + 28))
