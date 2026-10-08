"""Стильные экраны загрузки и логина BunnyOS (без пиксель-арта)."""
import math
import random
import pygame
from settings import WIDTH, HEIGHT


# ==================== BOOT ====================
class BootScreen:
    """Тёмный минималистичный экран загрузки."""

    DURATION = 3.0   # секунд

    def __init__(self):
        self.timer = 0.0
        self.done = False
        self.particles = self._make_particles(80)
        self.font_title = pygame.font.Font(None, 72)
        self.font_sub = pygame.font.Font(None, 22)
        self.font_small = pygame.font.Font(None, 18)
        self._bg_cache = None

    def _make_particles(self, n):
        rng = random.Random(42)
        return [
            {
                "x": rng.uniform(0, WIDTH),
                "y": rng.uniform(0, HEIGHT),
                "vy": rng.uniform(5, 25),
                "r": rng.uniform(0.5, 1.8),
                "a": rng.randint(40, 160),
            }
            for _ in range(n)
        ]

    def _make_bg(self):
        """Кэшируем градиент."""
        s = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            # Тёмно-синий → почти чёрный
            r = int(15 + 10 * (1 - t))
            g = int(20 + 20 * (1 - t))
            b = int(40 + 30 * (1 - t))
            pygame.draw.line(s, (r, g, b), (0, y), (WIDTH, y))
        return s

    def update(self, dt):
        self.timer += dt
        # Двигаем частицы вверх
        for p in self.particles:
            p["y"] -= p["vy"] * dt
            if p["y"] < -5:
                p["y"] = HEIGHT + 5
                p["x"] = random.uniform(0, WIDTH)
        if self.timer >= self.DURATION:
            self.done = True

    def draw(self, scr):
        # Фон
        if self._bg_cache is None:
            self._bg_cache = self._make_bg()
        scr.blit(self._bg_cache, (0, 0))

        # Частицы (летят вверх — «данные»)
        for p in self.particles:
            col = (100, 180, 255, p["a"])
            surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, col, (2, 2), int(p["r"]))
            scr.blit(surf, (int(p["x"]), int(p["y"])))

        # Логотип — тонкое кольцо + буква B
        cx, cy = WIDTH // 2, HEIGHT // 2 - 60
        pulse = math.sin(self.timer * 2) * 0.1 + 1.0
        r = int(38 * pulse)

        # Внешнее свечение
        for i in range(6):
            glow_r = r + i * 8
            a = max(0, 40 - i * 6)
            glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 160, 255, a), (glow_r, glow_r), glow_r)
            scr.blit(glow, (cx - glow_r, cy - glow_r))

        # Кольцо
        pygame.draw.circle(scr, (60, 120, 200), (cx, cy), r, 2)
        pygame.draw.circle(scr, (140, 200, 255), (cx, cy), r - 4, 1)

        # Буква B внутри
        fb = pygame.font.Font(None, 56)
        lt = fb.render("B", True, (200, 225, 255))
        scr.blit(lt, (cx - lt.get_width() // 2, cy - lt.get_height() // 2))

        # Название
        title = self.font_title.render("BunnyOS", True, (230, 240, 255))
        scr.blit(title, (WIDTH // 2 - title.get_width() // 2, cy + 70))

        sub = self.font_sub.render("1.0 LTS  ·  Carrot Kernel", True, (120, 150, 190))
        scr.blit(sub, (WIDTH // 2 - sub.get_width() // 2, cy + 130))

        # Прогресс-бар
        prog = min(1.0, self.timer / self.DURATION)
        bw, bh = 320, 3
        bx, by = WIDTH // 2 - bw // 2, HEIGHT - 100
        # Фон полосы
        pygame.draw.rect(scr, (30, 45, 70), (bx, by, bw, bh), border_radius=2)
        # Заполнение
        fill_w = int(bw * prog)
        if fill_w > 0:
            pygame.draw.rect(scr, (100, 170, 255),
                             (bx, by, fill_w, bh), border_radius=2)

        # Проценты
        pct = self.font_small.render(f"{int(prog * 100)}%", True, (140, 170, 210))
        scr.blit(pct, (bx + bw + 12, by - 6))

        # Статус-текст
        status = self._status(prog)
        st = self.font_small.render(status, True, (110, 140, 180))
        scr.blit(st, (bx, by + 18))

        # Версия в углу
        v = self.font_small.render("build 2026.10", True, (60, 80, 110))
        scr.blit(v, (20, HEIGHT - 24))

    def _status(self, p):
        if p < 0.15: return "Initializing kernel modules..."
        if p < 0.30: return "Mounting filesystems..."
        if p < 0.45: return "Starting system services..."
        if p < 0.60: return "Loading window manager..."
        if p < 0.75: return "Initializing user session..."
        if p < 0.90: return "Starting desktop environment..."
        return "Ready"


# ==================== LOGIN ====================
class LoginScreen:
    """Экран входа в систему."""

    def __init__(self):
        self.timer = 0.0
        self.done = False
        self.font_name = pygame.font.Font(None, 48)
        self.font_hint = pygame.font.Font(None, 22)
        self.font_sub = pygame.font.Font(None, 18)
        self._bg_cache = None
        self.password = ""
        self.show_hint = False

    def _make_bg(self):
        """Размытый тёмный фон — как заблюренный рабочий стол."""
        s = pygame.Surface((WIDTH, HEIGHT))
        rng = random.Random(7)
        # Базовый тёмный фон
        for y in range(HEIGHT):
            t = y / HEIGHT
            col = (int(20 + 30 * t), int(30 + 40 * t), int(55 + 50 * t))
            pygame.draw.line(s, col, (0, y), (WIDTH, y))
        # Крупные размытые пятна
        for _ in range(15):
            x = rng.randint(0, WIDTH)
            y = rng.randint(0, HEIGHT)
            r = rng.randint(120, 260)
            col = (
                rng.randint(30, 80),
                rng.randint(50, 120),
                rng.randint(100, 180),
            )
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            # Много кругов с прозрачностью для «размытия»
            for i in range(8):
                rr = r - i * 15
                if rr > 0:
                    a = 10 + i * 3
                    pygame.draw.circle(surf, (*col, a), (r, r), rr)
            s.blit(surf, (x - r, y - r))
        # Затемнение
        dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 80))
        s.blit(dark, (0, 0))
        return s

    def update(self, dt):
        self.timer += dt

    def handle_event(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.done = True

    def draw(self, scr):
        if self._bg_cache is None:
            self._bg_cache = self._make_bg()
        scr.blit(self._bg_cache, (0, 0))

        cx, cy = WIDTH // 2, HEIGHT // 2 - 40

        # Аватар — круг с монограммой "Z"
        r = 60
        # Свечение
        for i in range(5):
            rr = r + 4 + i * 6
            a = max(0, 30 - i * 6)
            glow = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (100, 160, 220, a), (rr, rr), rr)
            scr.blit(glow, (cx - rr, cy - rr))
        # Круг
        pygame.draw.circle(scr, (45, 65, 95), (cx, cy), r)
        pygame.draw.circle(scr, (140, 180, 230), (cx, cy), r, 2)

        # Монограмма
        mono = pygame.font.Font(None, 84)
        mt = mono.render("Z", True, (200, 220, 245))
        scr.blit(mt, (cx - mt.get_width() // 2, cy - mt.get_height() // 2 + 4))

        # Имя
        name = self.font_name.render("Зайка", True, (230, 240, 250))
        scr.blit(name, (cx - name.get_width() // 2, cy + r + 25))

        # Подпись
        sub = self.font_sub.render("zayka@bunnyos", True, (130, 155, 190))
        scr.blit(sub, (cx - sub.get_width() // 2, cy + r + 70))

        # Пульсирующая подсказка
        alpha = int(128 + 127 * math.sin(self.timer * 3))
        hint = self.font_hint.render("Нажми любую клавишу или кликни", True, (200, 220, 245))
        hint_surf = pygame.Surface(hint.get_size(), pygame.SRCALPHA)
        hint_surf.blit(hint, (0, 0))
        hint_surf.set_alpha(alpha)
        scr.blit(hint_surf, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 120))

        # Версия
        v = self.font_sub.render("BunnyOS 1.0 LTS  ·  Carrot Linux", True, (80, 100, 130))
        scr.blit(v, (WIDTH // 2 - v.get_width() // 2, HEIGHT - 50))
