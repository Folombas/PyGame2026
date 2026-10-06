"""BunnyOS — симулятор Unix-подобной ОС на PyGame."""
import sys
import time
import pygame
from settings import *
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
        self.font_bold = pygame.font.Font(None, 20)
        self.font_huge = pygame.font.Font(None, 72)

        self.fs = VirtualFS()
        self.shell = Shell(self.fs)

        self.state = "boot"
        self.running = True
        self.timer = 0.0
        self.windows = []
        self.active_win = None
        self.start_open = False

        # Обои
        self.wallpaper = None
        self.wallpaper_surf = None
        self._load_wallpaper()

    # ---------- EVENTS ----------
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
            return
        if self.state == "boot":
            if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                self.state = "login"
                self.timer = 0
            return
        if self.state == "login":
            if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                self.state = "desktop"
                self.open_app("terminal")
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
                items = list(APPS.keys())
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
                for w in self.windows:
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

    def _window_result(self, w, res):
        if res == "close":
            if w in self.windows:
                self.windows.remove(w)
            if self.active_win == w:
                self.active_win = None
        elif res == "minimize":
            w.minimized = True
        elif res == "maximize":
            w.toggle_max()
        elif res == "focus":
            self.focus(w)

    def _desktop_icon_click(self, mx, my):
        icons = list(APPS.keys())
        x0, y0 = 20, 20
        for i, app_id in enumerate(icons):
            ir = pygame.Rect(x0, y0 + i * 90, 80, 80)
            if ir.collidepoint(mx, my):
                self.open_app(app_id)
                return True
        return False

    def focus(self, w):
        if self.active_win and self.active_win != w:
            self.active_win.active = False
        self.active_win = w
        w.active = True
        if w in self.windows:
            self.windows.remove(w)
            self.windows.append(w)

    def open_app(self, app_id):
        if app_id not in APPS:
            return
        for w in self.windows:
            if getattr(w.app, "app_id", None) == app_id:
                w.minimized = False
                self.focus(w)
                return
        cls, title, (x, y, ww, wh) = APPS[app_id]
        app = cls(self)
        w = Window(x, y, ww, wh, title, app)
        self.windows.append(w)
        self.focus(w)

    # ---------- UPDATE ----------
    def update(self, dt):
        self.timer += dt
        if self.state == "boot" and self.timer > 2.5:
            self.state = "login"
            self.timer = 0

    # ---------- DRAW ----------
    def draw(self):
        if self.state == "boot":
            self.draw_boot()
        elif self.state == "login":
            self.draw_login()
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
        for w in self.windows:
            w.draw(self.screen, self.font_bold)
        # Taskbar
        self._draw_taskbar()
        if self.start_open:
            self._draw_start_menu()

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
        for w in self.windows:
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
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    BunnyOS().run()
