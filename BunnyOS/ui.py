"""UI: окно + приложения BunnyOS."""
import os
import pygame
from settings import *

# ===================== ICONS =====================
ICON_CACHE = {}

def _find_icon(name):
    """Ищет иконку по имени в разных наборах."""
    # Варианты путей: pixel/png/name.png, retro/name.png, retro/name.PNG
    paths = [
        f"assets/icons/retro/sliced/{name}.png",
        f"assets/icons/retro/{name}.png",
        f"assets/icons/pixel/png/{name}.png",
        f"assets/icons/kenney/{name}.png",
        f"assets/icons/win10/{name}.png",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    # Пробуем найти файл, который содержит имя (например, "folder" в "folder_32.png")
    for root, dirs, files in os.walk("assets/icons"):
        for f in files:
            if f.lower().endswith(('.png', '.PNG')) and name.lower() in f.lower():
                return os.path.join(root, f)
    return None

def load_icon(name, size=None):
    """Загружает иконку по имени, кэширует и опционально масштабирует."""
    key = (name, size)
    if key in ICON_CACHE:
        return ICON_CACHE[key]
    path = _find_icon(name)
    if not path:
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, (size, size))
        ICON_CACHE[key] = img
        return img
    except:
        return None




# ===================== WINDOW =====================
class Window:
    def __init__(self, x, y, w, h, title, app=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.app = app
        self.active = False
        self.minimized = False
        self.dragging = False
        self.drag_off = (0, 0)
        self.maximized = False
        self._saved_rect = None
        # === Анимация ===
        self.open_progress = 0.0
        self.target_rect = self.rect.copy()  # куда двигаемся (tiling)

    def titlebar(self):
        return pygame.Rect(self.rect.x, self.rect.y, self.rect.w, TITLEBAR_H)

    def content(self):
        return pygame.Rect(self.rect.x, self.rect.y + TITLEBAR_H,
                            self.rect.w, self.rect.h - TITLEBAR_H)

    def btn_close(self):
        return pygame.Rect(self.rect.right - 46, self.rect.y, 46, TITLEBAR_H)

    def btn_max(self):
        return pygame.Rect(self.rect.right - 92, self.rect.y, 46, TITLEBAR_H)

    def btn_min(self):
        return pygame.Rect(self.rect.right - 138, self.rect.y, 46, TITLEBAR_H)

    def draw(self, scr, font):
        if self.minimized:
            return
        # Анимация открытия
        if self.open_progress < 1.0:
            self.open_progress = min(1.0, self.open_progress + 0.12)
        # Плавный переход к target_rect (tiling)
        if self.rect != self.target_rect:
            lerp = 0.25
            self.rect.x += int((self.target_rect.x - self.rect.x) * lerp)
            self.rect.y += int((self.target_rect.y - self.rect.y) * lerp)
            self.rect.w += int((self.target_rect.w - self.rect.w) * lerp)
            self.rect.h += int((self.target_rect.h - self.rect.h) * lerp)
            # Если близко — фиксируем
            if abs(self.rect.x - self.target_rect.x) < 2 and abs(self.rect.y - self.target_rect.y) < 2:
                self.rect = self.target_rect.copy()
        slide_y = int((1 - self.open_progress) * 30)
        # Сохраняем оригинальный rect для отрисовки
        orig_y = self.rect.y
        self.rect.y += slide_y
        # Тень
        sh = pygame.Surface((self.rect.w + 10, self.rect.h + 10), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 80), (4, 4, self.rect.w, self.rect.h))
        scr.blit(sh, (self.rect.x - 2, self.rect.y - 2))
        # Фон окна
        pygame.draw.rect(scr, C_WINDOW_BG, self.rect)
        pygame.draw.rect(scr, C_WINDOW_BORDER, self.rect, 1)
        # Титул
        tb_col = C_TITLEBAR_ACTIVE if self.active else C_TITLEBAR
        pygame.draw.rect(scr, tb_col, self.titlebar())
        pygame.draw.line(scr, (220, 220, 220),
                         (self.rect.x, self.rect.y + TITLEBAR_H),
                         (self.rect.right, self.rect.y + TITLEBAR_H))
        # Заголовок
        tc = C_TITLE_TEXT if self.active else C_TITLE_TEXT_DIM
        t = font.render(self.title, True, tc)
        scr.blit(t, (self.rect.x + 12, self.rect.y + 8))

        mx, my = pygame.mouse.get_pos()
        # Close
        cb = self.btn_close()
        if self.active and cb.collidepoint(mx, my):
            pygame.draw.rect(scr, C_CLOSE_BTN_HOVER, cb)
        elif self.active:
            pygame.draw.rect(scr, C_CLOSE_BTN, cb)
        cc = (255, 255, 255) if self.active else (150, 150, 150)
        cx, cy = cb.centerx, cb.centery
        pygame.draw.line(scr, cc, (cx - 5, cy - 5), (cx + 5, cy + 5), 2)
        pygame.draw.line(scr, cc, (cx - 5, cy + 5), (cx + 5, cy - 5), 2)
        # Max
        mb = self.btn_max()
        if self.active and mb.collidepoint(mx, my):
            pygame.draw.rect(scr, C_BTN_HOVER, mb)
        pygame.draw.rect(scr, tc, (mb.centerx - 5, mb.centery - 5, 10, 10), 1)
        # Min
        mn = self.btn_min()
        if self.active and mn.collidepoint(mx, my):
            pygame.draw.rect(scr, C_BTN_HOVER, mn)
        pygame.draw.line(scr, tc, (mn.centerx - 5, mn.centery + 3),
                         (mn.centerx + 5, mn.centery + 3), 2)

        # Контент
        if self.app:
            self.app.draw(scr, self.content(), font)

        # Dimming для неактивных окон
        if not self.active:
            dim = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            dim.fill((10, 10, 18, 110))
            scr.blit(dim, self.rect.topleft)

        # Восстанавливаем y
        self.rect.y = orig_y

    def handle_event(self, event):
        if self.minimized:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.btn_close().collidepoint(mx, my):
                return "close"
            if self.btn_max().collidepoint(mx, my):
                return "maximize"
            if self.btn_min().collidepoint(mx, my):
                return "minimize"
            if self.titlebar().collidepoint(mx, my):
                self.dragging = True
                self.drag_off = (mx - self.rect.x, my - self.rect.y)
                return "focus"
            if self.content().collidepoint(mx, my) and self.app:
                self.app.handle_event(event, self.content())
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.rect.x = event.pos[0] - self.drag_off[0]
            self.rect.y = event.pos[1] - self.drag_off[1]
            self.rect.x = max(-self.rect.w + 100, min(self.rect.x, WIDTH - 100))
            self.rect.y = max(0, min(self.rect.y, HEIGHT - TASKBAR_H - 40))
        elif event.type == pygame.KEYDOWN and self.app:
            self.app.handle_event(event, self.content())
        return None

    def toggle_max(self):
        if self.maximized:
            self.rect = self._saved_rect
            self.maximized = False
        else:
            self._saved_rect = self.rect.copy()
            self.rect = pygame.Rect(0, 0, WIDTH, HEIGHT - TASKBAR_H)
            self.maximized = True


# ===================== APPS =====================
class TerminalApp:
    app_id = "terminal"
    def __init__(self, os_ref):
        self.os = os_ref
        self.lines = [
            "BunnyOS 1.0 LTS — Carrot Linux 5.15",
            "Type 'help' to see commands.",
            "",
        ]
        self.input = ""
        self.tick = 0
        # История листания (по стрелкам ↑↓)
        self.hist_idx = -1
        self.saved_input = ""
        # Размер шрифта (Ctrl+= / Ctrl+-)
        self.font_size = 16
        self.MIN_FONT = 10
        self.MAX_FONT = 32
        self.DEFAULT_FONT = 16

    def handle_event(self, event, rect):
        if event.type != pygame.KEYDOWN:
            return
        mods = pygame.key.get_mods()

        # --- Ctrl-комбинации ---
        if mods & pygame.KMOD_CTRL:
            if event.key == pygame.K_l:
                self.lines = []
                return
            if event.key == pygame.K_u:
                self.input = ""
                self.hist_idx = -1
                return
            if event.key == pygame.K_c:
                self.input = ""
                self.hist_idx = -1
                self.lines.append(f"{self.os.shell.prompt()} ^C")
                return
            # === Ctrl+= или Ctrl++ : увеличить шрифт ===
            if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.font_size = min(self.MAX_FONT, self.font_size + 2)
                print(f"[term] Шрифт: {self.font_size}")
                return
            # === Ctrl+- : уменьшить шрифт ===
            if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.font_size = max(self.MIN_FONT, self.font_size - 2)
                print(f"[term] Шрифт: {self.font_size}")
                return
            # === Ctrl+0 : сброс шрифта ===
            if event.key in (pygame.K_0, pygame.K_KP0):
                self.font_size = self.DEFAULT_FONT
                print(f"[term] Шрифт: {self.font_size}")
                return

        # --- Enter ---
        if event.key == pygame.K_RETURN:
            cmd = self.input
            self.lines.append(f"{self.os.shell.prompt()} {cmd}")
            self.input = ""
            self.hist_idx = -1          # сброс листания
            self.saved_input = ""
            out = self.os.shell.run(cmd)
            if out and out == ["__CLEAR__"]:
                self.lines = []
            else:
                self.lines.extend(out)
            self.lines.append("")

        # --- Backspace ---
        elif event.key == pygame.K_BACKSPACE:
            self.input = self.input[:-1]

        # --- Стрелка ВВЕРХ — предыдущая команда ---
        elif event.key == pygame.K_UP:
            hist = self.os.shell.history
            if not hist:
                return
            if self.hist_idx == -1:
                # Начинаем листать — запоминаем что было введено
                self.saved_input = self.input
                self.hist_idx = len(hist) - 1
            else:
                self.hist_idx = max(0, self.hist_idx - 1)
            self.input = hist[self.hist_idx]

        # --- Стрелка ВНИЗ — следующая команда (или возврат к исходному) ---
        elif event.key == pygame.K_DOWN:
            hist = self.os.shell.history
            if not hist or self.hist_idx == -1:
                return
            if self.hist_idx >= len(hist) - 1:
                # Дошли до конца — восстанавливаем исходный ввод
                self.hist_idx = -1
                self.input = self.saved_input
                self.saved_input = ""
            else:
                self.hist_idx += 1
                self.input = hist[self.hist_idx]

        # --- Tab — автодополнение ---
        elif event.key == pygame.K_TAB:
            known = ["help","ls","cd","pwd","cat","echo","clear","history",
                     "neofetch","tree","mkdir","touch","rm","grep","head",
                     "tail","wc","man","ps","whoami","hostname","uname",
                     "date","uptime","sudo","exit","snake","games"]
            cur = self.input.split()[-1] if self.input else ""
            matches = [c for c in known if c.startswith(cur)]
            if len(matches) == 1:
                parts = self.input.rsplit(" ", 1)
                self.input = (parts[0] + " " + matches[0]) if len(parts) > 1 else matches[0]
            elif len(matches) > 1:
                self.lines.append(" ".join(matches))

        # --- Обычный ввод ---
        else:
            if event.unicode and event.unicode.isprintable():
                self.input += event.unicode
                # Сброс листания при ручном вводе (но текст сохраняем)
                self.hist_idx = -1

    def draw(self, scr, rect, font):
        pygame.draw.rect(scr, C_TERMINAL_BG, rect)
        mono = pygame.font.Font(None, self.font_size)
        lh = self.font_size + 2   # межстрочный интервал зависит от размера
        n = max(1, (rect.h - 40) // lh)
        visible = self.lines[-n:]
        y = rect.y + 8
        for line in visible:
            col = C_TERMINAL_TEXT
            if line.startswith("bash:"):
                col = (255, 120, 120)
            elif line.startswith("BunnyOS") or "LTS" in line:
                col = (120, 220, 255)
            t = mono.render(line, True, col)
            scr.blit(t, (rect.x + 8, y))
            y += lh
        # Prompt
        p = f"{self.os.shell.prompt()} "
        pt = mono.render(p, True, C_TERMINAL_PROMPT)
        scr.blit(pt, (rect.x + 8, y))
        it = mono.render(self.input, True, C_TERMINAL_TEXT)
        scr.blit(it, (rect.x + 8 + pt.get_width(), y))
        # Курсор
        self.tick += 1
        if (self.tick // 30) % 2 == 0:
            cx = rect.x + 8 + pt.get_width() + it.get_width() + 2
            pygame.draw.rect(scr, C_TERMINAL_TEXT, (cx, y + 3, 8, 14))


class FilesApp:
    app_id = "files"
    def __init__(self, os_ref):
        self.os = os_ref
        self.path = "/home/zayka"
        self.entries = []
        self.selected = -1
        self.search = ""
        self.search_focus = False
        self.refresh()

    def refresh(self):
        # Реальная ФС для /home и /etc
        if self.path in ("/home", "/etc", "/usr", "/var", "/opt", "/tmp",
                          "/home/sasha", "/root"):
            import os as _os
            self.entries = []
            try:
                for name in sorted(_os.listdir(self.path)):
                    full = _os.path.join(self.path, name)
                    is_dir = _os.path.isdir(full)
                    self.entries.append((name, is_dir, "REAL"))
            except Exception:
                pass
            self.selected = -1
            return
        # Виртуальная ФС
        r = self.os.fs.ls(self.path)
        self.entries = []
        if r:
            d, f = r
            self.entries = [(x, True, "VIRT") for x in d] + [(x, False, "VIRT") for x in f]
        self.selected = -1

    def handle_event(self, event, rect):
        # Поиск — клавиатура
        if event.type == pygame.KEYDOWN and self.search_focus:
            if event.key == pygame.K_ESCAPE:
                self.search_focus = False
                self.search = ""
            elif event.key == pygame.K_BACKSPACE:
                self.search = self.search[:-1]
            elif event.key == pygame.K_RETURN:
                self.search_focus = False
            elif event.unicode and event.unicode.isprintable():
                self.search += event.unicode
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        # Клик по полю поиска
        search_rect = pygame.Rect(rect.x + 76, rect.y + 6, rect.w - 90, 22)
        if search_rect.collidepoint(event.pos):
            self.search_focus = True
            return
        self.search_focus = False
        mx, my = event.pos
        # Кнопка "up"
        up = pygame.Rect(rect.x + 6, rect.y + 6, 60, 22)
        if up.collidepoint(mx, my):
            if self.path != "/":
                self.path = "/".join(self.path.rstrip("/").split("/")[:-1]) or "/"
                self.refresh()
            return
        # Клик по файлу
        y0 = rect.y + 40
        for i, entry in enumerate(self.entries):
            name, is_d = entry[0], entry[1]
            ey = y0 + i * 26
            if rect.x + 6 <= mx <= rect.right - 6 and ey <= my <= ey + 24:
                self.selected = i
                if is_d:
                    self.path = (self.path.rstrip("/") + "/" + name)
                    self.refresh()
                return

    def draw(self, scr, rect, font):
        pygame.draw.rect(scr, (250, 250, 250), rect)
        # Top bar
        top = pygame.Rect(rect.x, rect.y, rect.w, 32)
        pygame.draw.rect(scr, (235, 235, 235), top)
        pygame.draw.line(scr, (200, 200, 200), (rect.x, rect.y + 32),
                         (rect.right, rect.y + 32))
        up = pygame.Rect(rect.x + 6, rect.y + 6, 60, 22)
        pygame.draw.rect(scr, (220, 220, 220), up)
        pygame.draw.rect(scr, (160, 160, 160), up, 1)
        t = font.render("↑", True, (0, 0, 0))
        scr.blit(t, (up.centerx - t.get_width() // 2, up.centery - t.get_height() // 2))
        p = font.render(self.path, True, (0, 0, 0))
        scr.blit(p, (rect.x + 76, rect.y + 10))

        # Поле поиска
        search_rect = pygame.Rect(rect.x + 76, rect.y + 6, rect.w - 90, 22)
        pygame.draw.rect(scr, (255, 255, 255), search_rect)
        border_col = (0, 120, 215) if self.search_focus else (180, 180, 180)
        pygame.draw.rect(scr, border_col, search_rect, 2)
        if self.search:
            st = font.render(self.search, True, (0, 0, 0))
            scr.blit(st, (search_rect.x + 5, search_rect.y + 5))
        elif not self.search_focus:
            placeholder = font.render("Поиск...", True, (170, 170, 170))
            scr.blit(placeholder, (search_rect.x + 5, search_rect.y + 5))

        # List (с фильтром)
        y0 = rect.y + 40
        filtered = [e for e in self.entries
                    if self.search.lower() in e[0].lower()] if self.search else self.entries
        for i, entry in enumerate(filtered):
            name, is_d = entry[0], entry[1]
            src_type = entry[2] if len(entry) > 2 else "VIRT"
            ey = y0 + i * 26
            if i == self.selected:
                pygame.draw.rect(scr, (0, 120, 215, 80),
                                 (rect.x + 6, ey, rect.w - 12, 24))
            icon = "[D]" if is_d else "[F]"
            col = (0, 80, 160) if is_d else (60, 60, 60)
            t = font.render(f"{icon}  {name}", True, col)
            scr.blit(t, (rect.x + 12, ey + 5))
            # Бейдж REAL
            if src_type == "REAL":
                badge = font.render("REAL", True, (200, 120, 50))
                scr.blit(badge, (rect.right - 50, ey + 5))


class NotepadApp:
    app_id = "notepad"
    def __init__(self, os_ref):
        self.os = os_ref
        self.text = ""
        self.file_path = None
        self.status = "New file · Ctrl+S = save to /home/zayka/note.txt"
        self.cursor_tick = 0

    def handle_event(self, event, rect):
        if event.type != pygame.KEYDOWN:
            return
        mods = pygame.key.get_mods()
        if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
            self.file_path = "/home/zayka/note.txt"
            self.os.fs.write(self.file_path, self.text)
            self.status = f"Saved: {self.file_path}"
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key == pygame.K_RETURN:
            self.text += "\n"
        elif event.key == pygame.K_TAB:
            self.text += "    "
        else:
            if event.unicode and event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, scr, rect, font):
        pygame.draw.rect(scr, (255, 255, 255), rect)
        mono = pygame.font.Font(None, 18)
        y = rect.y + 8
        for line in self.text.split("\n"):
            t = mono.render(line, True, (0, 0, 0))
            scr.blit(t, (rect.x + 8, y))
            y += 18
        # Статус
        st = pygame.font.Font(None, 16).render(self.status, True, (100, 100, 100))
        scr.blit(st, (rect.x + 8, rect.bottom - 20))


class CalculatorApp:
    app_id = "calc"
    def __init__(self, os_ref):
        self.os = os_ref
        self.expr = ""
        self.display = "0"

    def _btn_layout(self, rect):
        sx, sy = rect.x + 10, rect.y + 80
        bw, bh, gap = 60, 50, 4
        labels = [
            ["C", "(", ")", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", ".", "=", ""],
        ]
        rects = []
        for r, row in enumerate(labels):
            for c, lab in enumerate(row):
                if not lab:
                    continue
                bx = sx + c * (bw + gap)
                by = sy + r * (bh + gap)
                rects.append((lab, pygame.Rect(bx, by, bw, bh)))
        return rects

    def _press(self, lab):
        if lab == "C":
            self.expr = ""
            self.display = "0"
        elif lab == "=":
            try:
                v = eval(self.expr, {"__builtins__": None}, {})
                self.display = str(v)
                self.expr = str(v)
            except Exception:
                self.display = "Error"
                self.expr = ""
        else:
            self.expr += lab
            self.display = self.expr

    def handle_event(self, event, rect):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for lab, br in self._btn_layout(rect):
                if br.collidepoint(event.pos):
                    self._press(lab)
                    return
        if event.type == pygame.KEYDOWN:
            if event.unicode in "0123456789.+-*/()":
                self._press(event.unicode)
            elif event.key == pygame.K_RETURN:
                self._press("=")
            elif event.key == pygame.K_BACKSPACE:
                self.expr = self.expr[:-1]
                self.display = self.expr or "0"

    def draw(self, scr, rect, font):
        pygame.draw.rect(scr, (240, 240, 240), rect)
        disp = pygame.Rect(rect.x + 10, rect.y + 10, rect.w - 20, 60)
        pygame.draw.rect(scr, (255, 255, 255), disp)
        pygame.draw.rect(scr, (180, 180, 180), disp, 2)
        big = pygame.font.Font(None, 36)
        t = big.render(self.display[:18], True, (0, 0, 0))
        scr.blit(t, (disp.right - t.get_width() - 8, disp.y + 14))

        mx, my = pygame.mouse.get_pos()
        for lab, br in self._btn_layout(rect):
            hover = br.collidepoint(mx, my)
            col = (200, 220, 240) if hover else (220, 220, 220)
            pygame.draw.rect(scr, col, br)
            pygame.draw.rect(scr, (150, 150, 150), br, 1)
            t = font.render(lab, True, (0, 0, 0))
            scr.blit(t, (br.centerx - t.get_width() // 2,
                         br.centery - t.get_height() // 2))


class AboutApp:
    app_id = "about"
    def __init__(self, os_ref):
        self.os = os_ref

    def handle_event(self, event, rect):
        pass

    def draw(self, scr, rect, font):
        pygame.draw.rect(scr, (255, 255, 255), rect)
        big = pygame.font.Font(None, 42)
        t = big.render("BunnyOS 1.0 LTS", True, (0, 100, 200))
        scr.blit(t, (rect.x + 20, rect.y + 20))
        lines = [
            "",
            "Kernel:      Carrot 5.15",
            "Shell:       bunny-sh 1.0",
            "Desktop:     Luna",
            "User:        zayka",
            "",
            "(c) 2026 Bunny Inc.",
        ]
        y = rect.y + 90
        for line in lines:
            tt = font.render(line, True, (40, 40, 40))
            scr.blit(tt, (rect.x + 20, y))
            y += 24

# ===================== WALLPAPERS APP =====================
class WallpapersApp:
    """Персонализация — выбор обоев из assets/wallpapers/."""
    app_id = "wallpapers"

    def __init__(self, os_ref):
        self.os = os_ref
        self.wallpapers = []       # список путей
        self.thumbs = {}           # path → маленькая версия
        self.selected = None
        self.status = ""
        self._load_list()

    def _load_list(self):
        """Загружает ВСЕ обои из assets/wallpapers/ (включая подпапки)."""
        import wallpapers_gen
        self.wallpapers = wallpapers_gen.get_all_wallpapers()
        self.thumbs = {}
        for p in self.wallpapers:
            try:
                img = pygame.image.load(p).convert()
                # Пропорционально уменьшаем до ширины 240px
                w, h = img.get_size()
                new_w = 240
                new_h = int(h * new_w / w)
                thumb = pygame.transform.smoothscale(img, (new_w, new_h))
                self.thumbs[p] = thumb
            except Exception:
                pass
        print(f"[Personalization] Загружено обоев: {len(self.wallpapers)}")

    def handle_event(self, event, rect):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Кнопка "Обновить из интернета"
            upd = pygame.Rect(rect.right - 220, rect.y + 12, 200, 32)
            if upd.collidepoint(mx, my):
                self._download_new()
                return
            # Клик по обоям (сетка 3 колонки)
            cols = 3
            cell_w = (rect.w - 40) // cols
            cell_h = 135 + 30
            for i, p in enumerate(self.wallpapers):
                r = i // cols
                c = i % cols
                x = rect.x + 12 + c * cell_w
                y = rect.y + 60 + r * cell_h
                if pygame.Rect(x, y, cell_w - 12, cell_h - 12).collidepoint(mx, my):
                    self.os.set_wallpaper(p)
                    self.selected = p
                    self.status = f"Применено: {os.path.basename(p)}"
                    return

    def _download_new(self):
        """Генерирует новые процедурные обои."""
        try:
            import random as _r
            import wallpapers_gen
            self.status = "Генерация новых обоев..."
            
            # Выбираем случайный тип и генерируем с новым сидом
            name, fname, fn = _r.choice(wallpapers_gen.GENERATORS)
            surf = fn()
            
            # Сохраняем под уникальным именем
            seed = _r.randint(1, 999999)
            out = f"assets/wallpapers/gen_{fname}_{seed}.png"
            pygame.image.save(surf, out)
            
            # Обновляем список
            self._load_list()
            self.status = f"✓ Сгенерированы обои: {name}"
        except Exception as e:
            self.status = f"✗ {type(e).__name__}: {str(e)[:50]}"

    def draw(self, scr, rect, font):
        pygame.draw.rect(scr, (250, 250, 252), rect)
        # Заголовок
        title = pygame.font.Font(None, 28).render("Персонализация — Обои", True, (30, 30, 40))
        scr.blit(title, (rect.x + 16, rect.y + 12))
        # Кнопка "Сгенерировать"
        mx, my = pygame.mouse.get_pos()
        upd = pygame.Rect(rect.right - 220, rect.y + 12, 200, 32)
        hover = upd.collidepoint(mx, my)
        col = (0, 130, 220) if hover else (0, 110, 200)
        pygame.draw.rect(scr, col, upd, border_radius=6)
        tt = font.render("Сгенерировать новые", True, (255, 255, 255))
        scr.blit(tt, (upd.centerx - tt.get_width() // 2, upd.centery - tt.get_height() // 2))

        # Галерея
        cols = 3
        cell_w = (rect.w - 40) // cols
        cell_h = 135 + 30
        y_start = rect.y + 60
        for i, p in enumerate(self.wallpapers):
            r = i // cols
            c = i % cols
            x = rect.x + 12 + c * cell_w
            y = y_start + r * cell_h
            box = pygame.Rect(x, y, cell_w - 12, cell_h - 12)
            # Подсветка выбранного
            is_sel = (p == self.os.wallpaper)
            hov = box.collidepoint(mx, my)
            if is_sel:
                pygame.draw.rect(scr, (0, 120, 215), box, 3)
            elif hov:
                pygame.draw.rect(scr, (100, 160, 220), box, 2)
            else:
                pygame.draw.rect(scr, (200, 200, 200), box, 1)
            # Превью
            thumb = self.thumbs.get(p)
            if thumb:
                scr.blit(thumb, (box.x + 2, box.y + 2))
            # Имя файла
            name = os.path.basename(p)
            nt = pygame.font.Font(None, 14).render(name[:28], True, (60, 60, 60))
            scr.blit(nt, (box.x + 4, box.bottom - 18))

        # Статус
        if self.status:
            st = font.render(self.status, True, (0, 100, 0))
            scr.blit(st, (rect.x + 16, rect.bottom - 24))
