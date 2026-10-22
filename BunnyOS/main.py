"""BunnyOS — симулятор Unix-подобной ОС на PyGame."""
import os
import sys
import time
import pygame
import web_server
import screenshot
from settings import *
from boot_style import BootScreen, LoginScreen
from lock_screen import LockScreen
from real_bash import RealBashUI
from tiler import Tiler
from waybar import Waybar
from launcher import Launcher
from fs import VirtualFS, Shell
from ui import (Window, TerminalApp, FilesApp, NotepadApp,
                CalculatorApp, AboutApp, WallpapersApp, load_icon)
from browser import BrowserApp


APPS = {
    "terminal": (TerminalApp, "Терминал — zayka@bunnyos", (150, 90, 700, 480)),
    "browser":  (BrowserApp,  "BunnyNet — браузер",       (120, 70, 820, 540)),
    "files":    (FilesApp,    "Проводник",                 (220, 130, 600, 420)),
    "notepad":  (NotepadApp,  "Блокнот",                   (260, 110, 640, 480)),
    "calc":     (CalculatorApp, "Калькулятор",             (400, 180, 300, 400)),
    "about":    (AboutApp,    "О BunnyOS",                 (350, 170, 480, 300)),
    "wallpapers": (WallpapersApp, "Персонализация",        (200, 100, 740, 520)),
}


class BunnyOS:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("BunnyOS 1.0 LTS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 16)
        self.font_bold = pygame.font.Font(None, 20)
        self.font_huge = pygame.font.Font(None, 72)
        self.font_big = pygame.font.Font(None, 36)
        self.waybar = Waybar(self.font_small, self.font_bold)
        self.launcher = Launcher(self.font_big, self.font_small)

        self.fs = VirtualFS()
        self.shell = Shell(self.fs)

        # Веб-сервер (Фейнман-режим: загляни из браузера!)
        self.web_started = False
        try:
            web_server.start(self.shell)
            self.web_started = True
        except Exception as e:
            print(f"[OS] web server не стартовал: {e}")

        self.state = "boot"
        self.running = True
        self.timer = 0.0
        self.boot_screen = BootScreen()
        self.real_bash = None  # создастся при первом вызове
        self.login_screen = LoginScreen()
        self.windows = []
        # === Tiling WM ===
        self.tiler = Tiler()
        self._super_held = False
        # Создастся после шрифтов — временно None
        self.waybar = None
        self.tiling = True
        self.workspaces = [[] for _ in range(9)]
        self.current_ws = 0
        self.active_win = None
        self.start_open = False
        # === UI / effects ===
        self.toast = ""
        self.toast_timer = 0
        self._weather_cache = None
        self._weather_timer = 0
        # Embedded-игры
        self.active_game = None
        self.game_surface = None
        self.game_size = (0, 0)
        self._saved_caption = ""

        # Обои
        self.wallpaper = None
        self.wallpaper_surf = None
        self._load_wallpaper()

    # ---------- EVENTS ----------
    def handle_event(self, e):
        # Отслеживаем Super (Win) отдельно — SDL не даёт его в mods
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_LMETA, pygame.K_RMETA):
            self._super_held = True
            return
        if e.type == pygame.KEYUP and e.key in (pygame.K_LMETA, pygame.K_RMETA):
            self._super_held = False
            return
        # Launcher — перехватывает всё если открыт
        if self.launcher and self.launcher.open:
            action = self.launcher.handle_event(e)
            if action:
                if action == "_realbash":
                    if self.real_bash is None:
                        from real_bash import RealBashUI
                        self.real_bash = RealBashUI(self.font_small)
                    self.real_bash.open_ui()
                    self.state = "real_bash"
                elif action == "_webserver":
                    self.toast = "Web: http://localhost:8000"
                    self.toast_timer = 120
                else:
                    self.open_app(action)
            return
        if e.type == pygame.QUIT:
            self.running = False
            return
        if self.state == "real_bash":
            if self.real_bash:
                self.real_bash.handle_event(e)
                if not self.real_bash.open:
                    self.state = "desktop"
            return

        # Ctrl+Alt+T — открыть Терминал
        if (self.state == "desktop" and e.type == pygame.KEYDOWN
                and e.key == pygame.K_t
                and (pygame.key.get_mods() & pygame.KMOD_CTRL)
                and (pygame.key.get_mods() & pygame.KMOD_ALT)):
            self.open_app("terminal")
            return

        # === SUPER (Hyprland-style) хоткеи ===
        if self.state == "desktop" and e.type == pygame.KEYDOWN:
            # Super: либо отдельный флаг, либо Ctrl+Shift (fallback)
            mods = pygame.key.get_mods()
            super_held = (self._super_held
                          or ((mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT)))

            if super_held:
                # Super+Enter → терминал
                if e.key == pygame.K_RETURN:
                    self.open_app("terminal")
                    return
                # Super+B → real bash
                if e.key == pygame.K_b:
                    if self.real_bash is None:
                        from real_bash import RealBashUI
                        self.real_bash = RealBashUI(self.font_small)
                    self.real_bash.open_ui()
                    self.state = "real_bash"
                    return
                # Super+D → launcher
                if e.key == pygame.K_d:
                    self.launcher.show()
                    return
                # Super+Q → закрыть активное окно
                if e.key == pygame.K_q:
                    if self.active_win:
                        self._window_result(self.active_win, "close")
                    return
                # Super+1..9 → workspace
                if pygame.K_1 <= e.key <= pygame.K_9:
                    ws = e.key - pygame.K_1
                    if ws < 9:
                        self.current_ws = ws
                        self.active_win = None
                        if self.tiling:
                            self.tiler.apply(self.current_windows())
                        return
                # Super+H/J/K/L → навигация
                if e.key == pygame.K_h:
                    self._focus_dir(-1, 0)
                    return
                if e.key == pygame.K_l:
                    self._focus_dir(1, 0)
                    return
                if e.key == pygame.K_k:
                    self._focus_dir(0, -1)
                    return
                if e.key == pygame.K_j:
                    self._focus_dir(0, 1)
                    return
                # Super+T → toggle tiling/floating
                if e.key == pygame.K_t:
                    self.tiling = not self.tiling
                    self.toast = f"Tiling: {'ON' if self.tiling else 'OFF'}"
                    self.toast_timer = 90
                    if self.tiling:
                        self.tiler.apply(self.current_windows())
                    return

        # Ctrl+L — блокировка
        if (self.state == "desktop" and e.type == pygame.KEYDOWN
                and e.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL)):
            self.lock_screen.show()
            self.state = "locked"
            return

        # Ctrl+Alt+B — REAL BASH
        if (self.state == "desktop" and e.type == pygame.KEYDOWN
                and e.key == pygame.K_b
                and (pygame.key.get_mods() & pygame.KMOD_CTRL)
                and (pygame.key.get_mods() & pygame.KMOD_ALT)):
            if self.real_bash is None:
                self.real_bash = RealBashUI(self.font_small)
            self.real_bash.open_ui()
            self.state = "real_bash"
            return

        # F12 — скриншот
        if self.state == "desktop" and e.type == pygame.KEYDOWN and e.key == pygame.K_F12:
            path = screenshot.take_screenshot(self.screen)
            if path:
                self.toast = f"📸 {path.split('/')[-1]}"
                self.toast_timer = 120
            return

        if self.state == "boot":
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.boot_screen.done = True
            return
        if self.state == "login":
            self.login_screen.handle_event(e)
            return
        # desktop
        self.handle_desktop_event(e)

    def handle_desktop_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.start_open = False
            return

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx, my = e.pos
            # Start button
            sb = pygame.Rect(0, HEIGHT - TASKBAR_H, 60, TASKBAR_H)
            if sb.collidepoint(mx, my):
                self.start_open = not self.start_open
                return
            # Start menu items
            if self.start_open:
                items = list(APPS.keys()) + ["realbash"]
                menu_h = 40 + len(items) * 36
                menu_y = HEIGHT - TASKBAR_H - menu_h
                for i, app_id in enumerate(items):
                    iy = menu_y + 40 + i * 36
                    ir = pygame.Rect(0, iy, 260, 32)
                    if ir.collidepoint(mx, my):
                        self.start_open = False
                        self.open_app(app_id)
                        return
                # Клик вне
                if my < menu_y or mx > 260:
                    self.start_open = False
            # Taskbar windows
            if my >= HEIGHT - TASKBAR_H and mx > 60:
                x = 64
                for w in self.current_windows():
                    wr = pygame.Rect(x, HEIGHT - TASKBAR_H, 140, TASKBAR_H)
                    if wr.collidepoint(mx, my):
                        if w.minimized:
                            w.minimized = False
                            self.focus(w)
                        elif w == self.active_win:
                            w.minimized = True
                        else:
                            self.focus(w)
                        return
                    x += 144
                return
            # Desktop icons
            if self._desktop_icon_click(mx, my):
                return
            # Window hit
            for w in reversed(self.windows):
                if w.minimized:
                    continue
                if w.rect.collidepoint(mx, my):
                    self.focus(w)
                    res = w.handle_event(e)
                    self._window_result(w, res)
                    return
            return

        # Прочие события — активному окну
        if self.active_win:
            res = self.active_win.handle_event(e)
            self._window_result(self.active_win, res)

    def current_windows(self):
        return self.workspaces[self.current_ws]

    def _focus_dir(self, dx, dy):
        """Направленная навигация (HJKL)."""
        ws = self.current_windows()
        if len(ws) < 2 or not self.active_win:
            return
        cur = self.active_win
        cx, cy = cur.rect.centerx, cur.rect.centery
        best = None
        best_score = 1e9
        for w in ws:
            if w is cur:
                continue
            wx, wy = w.rect.centerx, w.rect.centery
            # Разница по нужной оси + штраф за перпендикуляр
            if dx != 0:
                dist = (wx - cx) * dx
                perp = abs(wy - cy)
            else:
                dist = (wy - cy) * dy
                perp = abs(wx - cx)
            if dist > 0:
                score = dist + perp * 2
                if score < best_score:
                    best_score = score
                    best = w
        if best:
            self.focus(best)

    def _window_result(self, w, res):
        if res == "close":
            if w in self.current_windows():
                self.current_windows().remove(w)
            if self.active_win == w:
                self.active_win = None
        elif res == "minimize":
            w.minimized = True
        elif res == "maximize":
            w.toggle_max()
        elif res == "focus":
            self.focus(w)

    def _desktop_icon_click(self, mx, my):
        # Иконки на рабочем столе (включая игры)
        desktop_icons = list(APPS.keys()) + ["snake"]
        x0, y0 = 20, 20
        for i, app_id in enumerate(desktop_icons):
            ir = pygame.Rect(x0, y0 + i * 90, 80, 80)
            if ir.collidepoint(mx, my):
                if app_id == "snake":
                    self.launch_snake()
                else:
                    self.open_app(app_id)
                return True
        return False

    def launch_game(self, game_id):
        """Запускает игру ВНУТРИ BunnyOS (без отдельного окна)."""
        GAME_INFO = {
            "snake":  ("snake",    "SnakeGame"),
            "tetris": ("tetris",   "TetrisGame"),
            "2048":   ("game2048", "Game2048"),
            "pong":   ("pong",     "PongGame"),
            "breakout": ("breakout", "BreakoutGame"),
            "asteroids": ("asteroids", "AsteroidsGame"),
        }
        if game_id not in GAME_INFO:
            print(f"[OS] Игра '{game_id}' не найдена")
            return
        module_name, class_name = GAME_INFO[game_id]
        try:
            mod = __import__(module_name)
            cls = getattr(mod, class_name)
            gw = getattr(mod, "WIDTH", 800)
            gh = getattr(mod, "HEIGHT", 600)
            self.game_size = (gw, gh)
            self.game_surface = pygame.Surface((gw, gh)).convert()
            self._saved_caption = pygame.display.get_caption()[0]
            self.active_game = cls(screen=self.game_surface)
            self.state = "game"
            print(f"[OS] {game_id} запущена в BunnyOS (embedded)")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[OS] Ошибка запуска {game_id}: {e}")
            self.active_game = None

    def launch_snake(self):
        self.launch_game("snake")

    def focus(self, w):
        if self.active_win and self.active_win != w:
            self.active_win.active = False
        self.active_win = w
        w.active = True
        ws = self.workspaces[self.current_ws]
        if w in ws:
            ws.remove(w)
            ws.append(w)
        if self.tiling:
            self.tiler.apply(ws)

    def _load_wallpaper(self):
        """Загружает первый доступный wallpaper из папки."""
        import os as _os
        d = "assets/wallpapers"
        if not _os.path.exists(d):
            return
        files = sorted([f for f in _os.listdir(d)
                        if f.lower().endswith((".jpg", ".jpeg", ".png"))])
        if not files:
            return
        self.set_wallpaper(_os.path.join(d, files[0]))

    def set_wallpaper(self, path):
        """Устанавливает обои и кэширует отмасштабированную версию."""
        self.wallpaper = path
        try:
            img = pygame.image.load(path).convert()
            self.wallpaper_surf = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
            
        except Exception as e:
            print(f"[wallpaper] ошибка: {e}")
            self.wallpaper_surf = None

    def open_app(self, app_id):
        if app_id not in APPS:
            return
        # Ищем на ВСЕХ рабочих столах
        for ws_list in self.workspaces:
            for w in ws_list:
                if getattr(w.app, "app_id", None) == app_id:
                    w.minimized = False
                    # Переключаемся на тот workspace
                    idx = self.workspaces.index(ws_list)
                    self.current_ws = idx
                    self.focus(w)
                    return
        cls, title, (x, y, ww, wh) = APPS[app_id]
        app = cls(self)
        w = Window(x, y, ww, wh, title, app)
        self.workspaces[self.current_ws].append(w)
        self.focus(w)
        if self.tiling:
            self.tiler.apply(self.workspaces[self.current_ws])

    # ---------- UPDATE ----------
    def update(self, dt):
        self.timer += dt
        if getattr(self, "toast_timer", 0) > 0:
            self.toast_timer -= 1
        # Погода — раз в 300 кадров (~5 сек для симуляции)
        if not hasattr(self, "_weather_timer"):
            self._weather_timer = 0
        if not hasattr(self, "_weather_cache"):
            self._weather_cache = None
        self._weather_timer += 1
        if self._weather_timer > 300 or self._weather_cache is None:
            self._weather_timer = 0
            self._update_weather()
        if self.state == "real_bash" and self.real_bash:
            self.real_bash.update(dt)
        if self.state == "locked":
            self.lock_screen.update(dt)
        if self.state == "desktop" and self.waybar:
            self.waybar.update(dt)
        if self.launcher and self.launcher.open:
            self.launcher.update(dt)
        if self.state == "boot":
            self.boot_screen.update(dt)
            if self.boot_screen.done:
                self.state = "login"
                self.timer = 0
        elif self.state == "login":
            self.login_screen.update(dt)
            if self.login_screen.done:
                self.state = "desktop"
                self.open_app("terminal")

    # ---------- DRAW ----------

    def _update_weather(self):
        """Погода из loadavg."""
        try:
            import real_sys, re as _re
            load = real_sys.uptime_str()
            mm = _re.search(r'load average: ([\d.]+)', load)
            la = float(mm.group(1)) if mm else 0.0
            if la < 0.5:
                w = ("☀ Ясно", (255, 220, 100))
            elif la < 1.5:
                w = ("⛅ Облачно", (200, 200, 220))
            elif la < 3.0:
                w = ("🌧 Дождь", (120, 160, 220))
            else:
                w = ("🌩 Гроза", (180, 100, 180))
            self._weather_cache = (w[0], w[1], f"load {la:.2f}")
        except Exception:
            self._weather_cache = ("☀ Ясно", (255, 220, 100), "load 0.00")

    def draw(self):
        if self.state == "locked":
            self.lock_screen.draw(self.screen)
            pygame.display.flip()
            return

        if self.state == "real_bash" and self.real_bash:
            self.real_bash.draw(self.screen)
            pygame.display.flip()
            return
        if self.state == "boot":
            self.boot_screen.draw(self.screen)
        elif self.state == "login":
            self.login_screen.draw(self.screen)
        else:
            self.draw_desktop()
        pygame.display.flip()

    def draw_boot(self):
        self.screen.fill((8, 15, 30))
        cx, cy = WIDTH // 2, HEIGHT // 2 - 40
        # Свечение
        for r in range(80, 30, -10):
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 180, 255, 20), (r, r), r)
            self.screen.blit(s, (cx - r, cy - r))
        # Зайка
        pygame.draw.circle(self.screen, (255, 245, 235), (cx, cy), 50)
        pygame.draw.circle(self.screen, (150, 200, 255), (cx, cy), 50, 2)
        for dx in (-15, 15):
            pygame.draw.ellipse(self.screen, (255, 245, 235),
                                (cx + dx - 8, cy - 80, 16, 40))
            pygame.draw.ellipse(self.screen, (240, 150, 170),
                                (cx + dx - 4, cy - 76, 8, 30))
        pygame.draw.circle(self.screen, (30, 25, 35), (cx - 15, cy - 5), 5)
        pygame.draw.circle(self.screen, (30, 25, 35), (cx + 15, cy - 5), 5)
        pygame.draw.circle(self.screen, (240, 150, 170), (cx, cy + 8), 4)

        t = self.font_huge.render("BunnyOS", True, (255, 255, 255))
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, cy + 80))

        # Progress bar
        prog = min(1.0, self.timer / 2.5)
        bw, bh = 300, 5
        bx, by = WIDTH // 2 - bw // 2, HEIGHT - 140
        pygame.draw.rect(self.screen, (30, 40, 60), (bx, by, bw, bh))
        pygame.draw.rect(self.screen, (150, 200, 255), (bx, by, int(bw * prog), bh))
        dots = "." * ((int(self.timer * 3)) % 4)
        s = self.font.render(f"Loading{dots}", True, (180, 200, 230))
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, by + 20))

    def draw_login(self):
        self.screen.fill((0, 100, 180))
        cx, cy = WIDTH // 2, HEIGHT // 2 - 80
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 70)
        pygame.draw.circle(self.screen, (200, 220, 240), (cx, cy), 70, 3)
        # Ушки
        pygame.draw.ellipse(self.screen, (255, 245, 235), (cx - 22, cy - 90, 16, 42))
        pygame.draw.ellipse(self.screen, (255, 245, 235), (cx + 6, cy - 90, 16, 42))
        pygame.draw.ellipse(self.screen, (240, 150, 170), (cx - 18, cy - 84, 8, 32))
        pygame.draw.ellipse(self.screen, (240, 150, 170), (cx + 10, cy - 84, 8, 32))
        # Глаза
        pygame.draw.circle(self.screen, (30, 25, 35), (cx - 20, cy - 5), 6)
        pygame.draw.circle(self.screen, (30, 25, 35), (cx + 20, cy - 5), 6)
        pygame.draw.circle(self.screen, (240, 150, 170), (cx, cy + 15), 5)

        name = self.font_huge.render("Зайка", True, (255, 255, 255))
        self.screen.blit(name, (WIDTH // 2 - name.get_width() // 2, cy + 90))
        hint = self.font.render("Press any key or click to log in",
                                True, (200, 220, 255))
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 100))

    def draw_desktop(self):
        # Обои — картинка или градиент
        if self.wallpaper_surf:
            self.screen.blit(self.wallpaper_surf, (0, 0))
        else:
            for y in range(HEIGHT):
                t = y / HEIGHT
                col = (int(0 + 25 * t), int(70 + 70 * t), int(160 + 60 * t))
                pygame.draw.line(self.screen, col, (0, y), (WIDTH, y))
        # Лёгкое затемнение внизу для taskbar
        self._draw_desktop_icons()
        # Окна
        for w in self.current_windows():
            w.draw(self.screen, self.font_bold)
        # === WAYBAR ===
        if self.waybar:
            self.waybar.draw(self.screen, self.current_ws, 9, self.workspaces)

        # Погодный виджет (правый верх)
        if getattr(self, "_weather_cache", None):
            text, color, sub = self._weather_cache
            w_panel = pygame.Rect(WIDTH - 200, 20, 180, 80)
            panel_surf = pygame.Surface((w_panel.w, w_panel.h), pygame.SRCALPHA)
            panel_surf.fill((20, 30, 50, 180))
            pygame.draw.rect(panel_surf, (*color, 200),
                             (0, 0, w_panel.w, w_panel.h), 2, border_radius=10)
            self.screen.blit(panel_surf, w_panel.topleft)
            wt = self.font_bold.render(text, True, color) if hasattr(self, 'font_bold') else self.font.render(text, True, color)
            self.screen.blit(wt, (w_panel.x + 12, w_panel.y + 12))
            st = self.font.render(sub, True, (150, 170, 200))
            self.screen.blit(st, (w_panel.x + 12, w_panel.y + 48))

        # Toast (уведомление)
        if getattr(self, "toast_timer", 0) > 0 and getattr(self, "toast", ""):
            # Плавное появление/исчезновение
            alpha = 255
            if self.toast_timer < 20:
                alpha = int(255 * (self.toast_timer / 20))
            elif self.toast_timer > 100:
                alpha = int(255 * ((120 - self.toast_timer) / 20))

            t = self.font.render(self.toast, True, (255, 255, 255))
            pad = 16
            box = pygame.Surface((t.get_width() + pad * 2, t.get_height() + pad), pygame.SRCALPHA)
            box.fill((40, 60, 100, int(alpha * 0.95)))
            pygame.draw.rect(box, (100, 180, 255, alpha),
                             (0, 0, box.get_width(), box.get_height()), 2, border_radius=8)
            bx = WIDTH - box.get_width() - 20
            by = HEIGHT - TASKBAR_H - box.get_height() - 20
            self.screen.blit(box, (bx, by))
            # Текст с alpha
            t.set_alpha(alpha)
            self.screen.blit(t, (bx + pad, by + pad // 2))

        # Taskbar — только в floating режиме
        if not self.tiling:
            self._draw_taskbar()
        if self.start_open:
            self._draw_start_menu()

        # Launcher — поверх всего
        if self.launcher and self.launcher.open:
            self.launcher.draw(self.screen)

    def _draw_desktop_icons(self):
        icons = [
            ("terminal", "Терминал",    "terminal"),
            ("browser",  "BunnyNet",    "browser"),
            ("files",    "Проводник",   "folder"),
            ("notepad",  "Блокнот",     "notepad"),
            ("calc",     "Калькулятор", "calculator"),
            ("about",    "О системе",   "info"),
            ("wallpapers", "Персонализация", "computer"),
        ]
        mx, my = pygame.mouse.get_pos()
        x0, y0 = 20, 20
        for i, (app_id, label, icon_name) in enumerate(icons):
            y = y0 + i * 90
            box = pygame.Rect(x0 + 16, y + 8, 48, 48)
            hover = box.collidepoint(mx, my) or pygame.Rect(x0, y, 80, 80).collidepoint(mx, my)
            
            # Пытаемся загрузить иконку
            img = load_icon(icon_name, 48)
            if img:
                self.screen.blit(img, (box.x, box.y))
            else:
                # Фоллбэк - процедурная отрисовка
                col = (60, 130, 200) if not hover else (90, 160, 230)
                pygame.draw.rect(self.screen, col, box, border_radius=6)
                pygame.draw.rect(self.screen, (200, 220, 240), box, 1, border_radius=6)
                g = self.font_bold.render(app_id[:2].upper(), True, (255, 255, 255))
                self.screen.blit(g, (box.centerx - g.get_width() // 2,
                                     box.centery - g.get_height() // 2))
            
            # Тень и название
            lbl = self.font.render(label, True, (255, 255, 255))
            sh = self.font.render(label, True, (0, 0, 0))
            lx = x0 + 40 - lbl.get_width() // 2
            ly = y + 62
            self.screen.blit(sh, (lx + 1, ly + 1))
            self.screen.blit(lbl, (lx, ly))

    def _draw_taskbar(self):
        bar = pygame.Rect(0, HEIGHT - TASKBAR_H, WIDTH, TASKBAR_H)
        pygame.draw.rect(self.screen, C_TASKBAR, bar)

        mx, my = pygame.mouse.get_pos()
        sb = pygame.Rect(0, HEIGHT - TASKBAR_H, 60, TASKBAR_H)
        hover = sb.collidepoint(mx, my) or self.start_open
        if hover:
            pygame.draw.rect(self.screen, C_TASKBAR_HOVER, sb)
        # Логотип — 4 квадрата
        cx, cy = sb.centerx, sb.centery
        s = 6
        pygame.draw.rect(self.screen, C_ACCENT, (cx - s - 2, cy - s - 2, s, s))
        pygame.draw.rect(self.screen, C_ACCENT, (cx + 2, cy - s - 2, s, s))
        pygame.draw.rect(self.screen, C_ACCENT, (cx - s - 2, cy + 2, s, s))
        pygame.draw.rect(self.screen, C_ACCENT, (cx + 2, cy + 2, s, s))

        # Окна
        x = 64
        for w in self.current_windows():
            wr = pygame.Rect(x, HEIGHT - TASKBAR_H, 140, TASKBAR_H)
            active = w == self.active_win and not w.minimized
            hov = wr.collidepoint(mx, my)
            if active:
                col = C_TASKBAR_ACTIVE
            elif hov:
                col = C_TASKBAR_HOVER
            else:
                col = C_TASKBAR
            pygame.draw.rect(self.screen, col, wr)
            if active:
                pygame.draw.rect(self.screen, C_ACCENT,
                                 (wr.x + 30, wr.bottom - 2, wr.w - 60, 2))
            t = self.font.render(w.title[:16], True, (220, 220, 220))
            self.screen.blit(t, (wr.x + 8, wr.centery - t.get_height() // 2))
            x += 144

        # Индикатор веб-сервера
        if getattr(self, "web_started", False):
            import web_server
            if web_server._running:
                icon_x = WIDTH - 160
                icon_y = HEIGHT - TASKBAR_H + 12
                # Зелёная точка
                pygame.draw.circle(self.screen, (100, 240, 120), (icon_x, icon_y + 8), 5)
                # Иконка "WEB" — используем self.font
                wt = self.font.render("WEB", True, (140, 220, 140))
                self.screen.blit(wt, (icon_x + 10, icon_y + 2))

        # Часы
        ct = time.strftime("%H:%M")
        dt = time.strftime("%d.%m.%Y")
        tt = self.font.render(ct, True, (230, 230, 230))
        dd = self.font.render(dt, True, (170, 170, 170))
        self.screen.blit(tt, (WIDTH - 90, HEIGHT - TASKBAR_H + 4))
        self.screen.blit(dd, (WIDTH - 90, HEIGHT - TASKBAR_H + 20))

    def _draw_start_menu(self):
        items = list(APPS.keys())
        labels = {
            "terminal": ">_  Терминал",
            "browser":  "WWW BunnyNet",
            "files":    "[]  Проводник",
            "notepad":  "#   Блокнот",
            "calc":     "+-  Калькулятор",
            "about":    "i   О системе",
            "wallpapers": "[]  Персонализация",
        }
        menu_h = 40 + len(items) * 36
        menu_y = HEIGHT - TASKBAR_H - menu_h
        menu = pygame.Rect(0, menu_y, 260, menu_h)
        surf = pygame.Surface((menu.w, menu.h), pygame.SRCALPHA)
        surf.fill((28, 28, 28, 240))
        self.screen.blit(surf, menu.topleft)
        pygame.draw.rect(self.screen, (60, 60, 60), menu, 1)

        title = self.font_bold.render("BunnyOS 1.0", True, (255, 255, 255))
        self.screen.blit(title, (menu.x + 16, menu.y + 10))

        mx, my = pygame.mouse.get_pos()
        for i, app_id in enumerate(items):
            iy = menu.y + 40 + i * 36
            ir = pygame.Rect(menu.x + 4, iy, menu.w - 8, 32)
            if ir.collidepoint(mx, my):
                pygame.draw.rect(self.screen, (60, 60, 60), ir)
            t = self.font.render(labels[app_id], True, (230, 230, 230))
            self.screen.blit(t, (ir.x + 12, ir.y + 8))

    # ---------- MAIN LOOP ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            # === Проверяем запрос на REAL BASH ===
            if self.state == "desktop":
                import os
                req = os.path.expanduser("~/.bunny_realbash_request")
                if os.path.exists(req):
                    try:
                        os.remove(req)
                    except Exception:
                        pass
                    if self.real_bash is None:
                        self.real_bash = RealBashUI(self.font_small)
                    self.real_bash.terminal.sandbox = (mode != "raw")
                    self.real_bash.open_ui()
                    self.state = "real_bash"
                    continue

            # === Проверяем запрос из Hub на запуск игры ===
            import os
            req_path = os.path.expanduser("~/.bunny_launch_request")
            if os.path.exists(req_path):
                try:
                    with open(req_path, "r") as f:
                        game_id = f.read().strip()
                    os.remove(req_path)
                    self.launch_game(game_id)
                except Exception as e:
                    print(f"[OS] Ошибка обработки запроса: {e}")
                    try:
                        os.remove(req_path)
                    except Exception:
                        pass

            # === Если запущена игра — она управляет всем ===
            if self.state == "game" and self.active_game is not None:
                events = pygame.event.get()
                if not self.active_game._handle_events(events):
                    # Игра просит выход
                    self.active_game = None
                    self.game_surface = None
                    self.state = "desktop"
                    # Возвращаем имя окна BunnyOS
                    pygame.display.set_caption("BunnyOS 1.0 LTS")
                    continue
                self.active_game._update(dt)
                self.active_game._draw()
                # Центрируем игру на экране BunnyOS
                self.screen.fill((10, 12, 20))
                gw, gh = self.game_size
                gx = (WIDTH - gw) // 2
                gy = (HEIGHT - gh) // 2
                self.screen.blit(self.game_surface, (gx, gy))
                # Рамка вокруг игры
                pygame.draw.rect(self.screen, (80, 100, 140),
                                 (gx - 2, gy - 2, gw + 4, gh + 4), 2)
                pygame.display.flip()
                if hasattr(self, "web_started") and self.web_started:
                    self._web_tick = getattr(self, "_web_tick", 0) + 1
                    if self._web_tick % 10 == 0:
                        web_server._update_frame(self.screen)
                continue

            # === Обычный цикл BunnyOS ===
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
            # Обновляем кадр для веб-сервера (раз в 10 кадров)
            if hasattr(self, "web_started") and self.web_started:
                self._web_tick = getattr(self, "_web_tick", 0) + 1
                if self._web_tick % 10 == 0:
                    web_server._update_frame(self.screen)
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    BunnyOS().run()
