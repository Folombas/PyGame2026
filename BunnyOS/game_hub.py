"""Game Hub — крутой лаунчер игр BunnyOS."""
import os
import sys
import json
import math
import random
import subprocess
import pygame
from settings import WIDTH, HEIGHT, TASKBAR_H


# === НАСТРОЙКИ ===
FPS = 60
HUB_W = WIDTH
HUB_H = HEIGHT - TASKBAR_H

# === ЦВЕТА ===
C_BG1        = (12, 16, 28)
C_BG2        = (28, 20, 50)
C_CARD       = (25, 30, 50)
C_CARD_HOVER = (40, 50, 80)
C_CARD_ACTIVE= (60, 80, 130)
C_BORDER     = (60, 80, 130)
C_BORDER_HI  = (100, 180, 255)
C_TEXT       = (230, 240, 255)
C_TEXT_DIM   = (130, 150, 180)
C_ACCENT     = (100, 180, 255)
C_GOLD       = (255, 200, 80)

# Папка для рекордов
SCORES_PATH = os.path.expanduser("~/.bunny_games/highscores.json")

# === ОПИСАНИЯ ИГР ===
GAMES = [
    {
        "id": "snake",
        "name": "Змейка",
        "desc": "Классика. Собирай яблоки, не кусай хвост.",
        "file": "snake.py",
        "color": (60, 220, 100),
        "preview": "snake",
    },
    {
        "id": "tetris",
        "name": "Тетрис",
        "desc": "7 фигур, 4 линии, комбо-эффекты.",
        "file": "tetris.py",
        "color": (200, 120, 240),
        "preview": "tetris",
    },
    {
        "id": "2048",
        "name": "2048",
        "desc": "Соединяй плитки. Дойди до 2048!",
        "file": "game2048.py",
        "color": (240, 200, 80),
        "preview": "2048",
    },
    {
        "id": "pong",
        "name": "Понг",
        "desc": "Против ИИ. До 7 очков.",
        "file": "pong.py",
        "color": (255, 130, 100),
        "preview": "pong",
    },
]


class GameHub:
    def __init__(self):
        self.screen = pygame.display.set_mode((HUB_W, HUB_H))
        pygame.display.set_caption("Game Hub — BunnyOS")
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.Font(None, 64)
        self.font_card = pygame.font.Font(None, 36)
        self.font_desc = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 18)
        self.font_big = pygame.font.Font(None, 48)

        self.selected = 0
        self.tick = 0
        self.scores = self._load_scores()

        # Анимации карточек
        self.card_anims = [0.0 for _ in GAMES]  # 0..1 — плавное появление
        self.hover_anims = [0.0 for _ in GAMES]
        self.stars = self._make_stars(60)
        self.bg_cache = None

    # ---------- УТИЛИТЫ ----------
    def _load_scores(self):
        if not os.path.exists(SCORES_PATH):
            return {}
        try:
            with open(SCORES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _make_stars(self, n):
        rng = random.Random(42)
        return [
            {"x": rng.uniform(0, HUB_W), "y": rng.uniform(0, HUB_H),
             "r": rng.uniform(0.5, 2.0), "a": rng.randint(40, 150),
             "speed": rng.uniform(0.1, 0.5)}
            for _ in range(n)
        ]

    def _make_bg(self):
        """Тёмный градиент с "туманностью"."""
        s = pygame.Surface((HUB_W, HUB_H))
        for y in range(HUB_H):
            t = y / HUB_H
            r = int(C_BG1[0] * (1 - t) + C_BG2[0] * t)
            g = int(C_BG1[1] * (1 - t) + C_BG2[1] * t)
            b = int(C_BG1[2] * (1 - t) + C_BG2[2] * t)
            pygame.draw.line(s, (r, g, b), (0, y), (HUB_W, y))
        # Пятна туманности
        rng = random.Random(7)
        for _ in range(8):
            x = rng.randint(100, HUB_W - 100)
            y = rng.randint(100, HUB_H - 100)
            r = rng.randint(120, 240)
            col = (
                rng.randint(40, 100),
                rng.randint(30, 80),
                rng.randint(100, 180),
            )
            nebula = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            for i in range(10):
                rr = r - i * 12
                if rr > 0:
                    pygame.draw.circle(nebula, (*col, 8), (r, r), rr)
            s.blit(nebula, (x - r, y - r))
        return s

    # ---------- КООРДИНАТЫ КАРТОЧЕК ----------
    def _card_rect(self, i):
        # Сетка 2×2, центрирована
        card_w, card_h = 400, 240
        gap_x, gap_y = 40, 30
        total_w = card_w * 2 + gap_x
        total_h = card_h * 2 + gap_y
        x0 = (HUB_W - total_w) // 2
        y0 = 130  # отступ от заголовка
        col = i % 2
        row = i // 2
        return pygame.Rect(
            x0 + col * (card_w + gap_x),
            y0 + row * (card_h + gap_y),
            card_w, card_h,
        )

    # ---------- ПРЕВЬЮ (процедурное) ----------
    def _draw_preview(self, scr, kind, rect, color, hover):
        """Рисует маленькое превью игры."""
        # Фон — тёмный скруглённый
        inner = rect.inflate(-20, -20)
        pygame.draw.rect(scr, (10, 14, 22), inner, border_radius=8)

        cx, cy = inner.centerx, inner.centery

        if kind == "snake":
            # Змейка: маленькие квадратики
            cell = 16
            start_x = cx - 3 * cell
            start_y = cy - cell // 2
            for i in range(5):
                c = color if i > 0 else (255, 255, 255)
                r = 3 if i == 0 else 2
                pygame.draw.rect(scr, c,
                                 (start_x + i * cell, start_y, cell - 2, cell - 2),
                                 border_radius=r)
            # Яблоко
            pygame.draw.circle(scr, (255, 60, 100),
                               (cx + 90, cy - 30), 8)
            pygame.draw.circle(scr, (255, 120, 140),
                               (cx + 90, cy - 30), 8, 2)

        elif kind == "tetris":
            # Тетрис: полоски из цветных блоков
            block = 20
            base_x = cx - 3 * block
            base_y = cy + 20
            colors = [(80, 220, 240), (250, 220, 80), (190, 100, 240),
                      (100, 230, 120), (240, 90, 110), (80, 130, 250)]
            for x in range(6):
                col = colors[x % len(colors)]
                pygame.draw.rect(scr, col,
                                 (base_x + x * block, base_y, block - 2, block - 2),
                                 border_radius=3)
            # Падающая фигура сверху
            falling_x = cx - 2 * block
            falling_y = cy - 40
            for dx in (-1, 0, 1):
                pygame.draw.rect(scr, colors[2],
                                 (falling_x + dx * block, falling_y,
                                  block - 2, block - 2),
                                 border_radius=3)
            pygame.draw.rect(scr, colors[2],
                             (falling_x, falling_y - block, block - 2, block - 2),
                             border_radius=3)

        elif kind == "2048":
            # 2048: 4 плитки с числами
            cell = 50
            gap = 6
            nums = [2, 4, 8, 16]
            colors_2048 = [(238, 228, 218), (237, 224, 200),
                           (242, 177, 121), (245, 149, 99)]
            start_x = cx - cell - gap // 2
            start_y = cy - cell - gap // 2
            for i, num in enumerate(nums):
                r = i // 2
                c = i % 2
                x = start_x + c * (cell + gap)
                y = start_y + r * (cell + gap)
                pygame.draw.rect(scr, colors_2048[i], (x, y, cell, cell),
                                 border_radius=6)
                txt_col = (60, 60, 60) if num < 100 else (255, 255, 255)
                f = pygame.font.Font(None, 28)
                t = f.render(str(num), True, txt_col)
                scr.blit(t, (x + cell // 2 - t.get_width() // 2,
                             y + cell // 2 - t.get_height() // 2))

        elif kind == "pong":
            # Понг: две ракетки и мяч
            pygame.draw.rect(scr, (100, 200, 255),
                             (cx - 100, cy - 30, 8, 60), border_radius=3)
            pygame.draw.rect(scr, (255, 130, 100),
                             (cx + 92, cy - 20, 8, 60), border_radius=3)
            # Мяч
            pygame.draw.circle(scr, (240, 240, 220), (cx, cy), 8)
            # Шлейф
            for i in range(3):
                a = 120 - i * 40
                s = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(s, (240, 240, 220, a), (5, 5), 5 - i)
                scr.blit(s, (cx - 20 - i * 8, cy - 5))

        # Свечение при hover
        if hover > 0.01:
            glow = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
            glow.fill((*C_BORDER_HI, int(30 * hover)))
            scr.blit(glow, inner.topleft)

    # ---------- ЛОГИКА ----------
    def _launch(self, game):
        """Запускает игру во внешнем процессе."""
        script = os.path.join(os.path.dirname(__file__), game["file"])
        try:
            subprocess.Popen([sys.executable, script])
            print(f"[Hub] Запуск: {game['name']}")
        except Exception as e:
            print(f"[Hub] Ошибка: {e}")

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected = (self.selected - 1) % len(GAMES)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected = (self.selected + 1) % len(GAMES)
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.selected = (self.selected - 2) % len(GAMES)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected = (self.selected + 2) % len(GAMES)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._launch(GAMES[self.selected])
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                for i, g in enumerate(GAMES):
                    if self._card_rect(i).collidepoint(mx, my):
                        self.selected = i
                        self._launch(g)
                        break
            if e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                for i, g in enumerate(GAMES):
                    if self._card_rect(i).collidepoint(mx, my):
                        self.selected = i
                        break
        return True

    def _update(self, dt):
        self.tick += 1
        # Плавное появление
        for i in range(len(GAMES)):
            self.card_anims[i] = min(1.0, self.card_anims[i] + dt * 1.5)
        # Hover анимации
        for i in range(len(GAMES)):
            target = 1.0 if i == self.selected else 0.0
            self.hover_anims[i] += (target - self.hover_anims[i]) * dt * 8

    # ---------- ОТРИСОВКА ----------
    def _draw(self):
        # Фон
        if self.bg_cache is None:
            self.bg_cache = self._make_bg()
        self.screen.blit(self.bg_cache, (0, 0))

        # Звёзды с параллаксом
        for s in self.stars:
            s["y"] += s["speed"] * 0.3
            if s["y"] > HUB_H:
                s["y"] = 0
                s["x"] = random.uniform(0, HUB_W)
            surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 200, 255, s["a"]),
                               (2, 2), int(s["r"]))
            self.screen.blit(surf, (s["x"], s["y"]))

        # Заголовок
        title = self.font_title.render("Game Hub", True, C_TEXT)
        self.screen.blit(title, (HUB_W // 2 - title.get_width() // 2, 30))
        # Подзаголовок с акцентом
        sub = self.font_small.render("BunnyOS · Games Collection", True, C_TEXT_DIM)
        self.screen.blit(sub, (HUB_W // 2 - sub.get_width() // 2, 92))

        # Декоративная линия под заголовком
        line_y = 118
        line_w = 300 + int(20 * math.sin(self.tick * 0.05))
        line_x = HUB_W // 2 - line_w // 2
        pygame.draw.line(self.screen, C_ACCENT,
                         (line_x, line_y), (line_x + line_w, line_y), 2)

        # Карточки
        for i, g in enumerate(GAMES):
            self._draw_card(i, g)

        # Подсказка внизу
        hint = self.font_small.render(
            "Стрелки / WASD — навигация    Enter — играть    Esc — выход",
            True, C_TEXT_DIM
        )
        self.screen.blit(hint, (HUB_W // 2 - hint.get_width() // 2, HUB_H - 30))

        pygame.display.flip()

    def _draw_card(self, i, g):
        base_rect = self._card_rect(i)
        anim = self.card_anims[i]
        hover = self.hover_anims[i]
        active = (i == self.selected)

        # Появление — сдвиг снизу + прозрачность
        offset_y = int((1 - anim) * 60)
        rect = base_rect.move(0, offset_y)

        # Масштабирование при активной
        scale = 1.0 + hover * 0.03
        if scale != 1.0:
            new_w = int(rect.w * scale)
            new_h = int(rect.h * scale)
            rect = pygame.Rect(0, 0, new_w, new_h)
            rect.center = base_rect.center
            rect.y += offset_y

        # Тень
        shadow = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 100),
                         (10, 10, rect.w, rect.h), border_radius=16)
        self.screen.blit(shadow, (rect.x - 10, rect.y - 10))

        # Фон карточки
        if active:
            card_col = C_CARD_ACTIVE
        else:
            card_col = C_CARD

        pygame.draw.rect(self.screen, card_col, rect, border_radius=16)

        # Свечение при активной (пульсация)
        if active:
            pulse = 0.6 + 0.4 * math.sin(self.tick * 0.1)
            glow = pygame.Surface((rect.w + 40, rect.h + 40), pygame.SRCALPHA)
            for r in range(4):
                a = int(40 * pulse) - r * 8
                if a > 0:
                    pygame.draw.rect(glow, (*g["color"], a),
                                     (20 - r * 4, 20 - r * 4,
                                      rect.w + r * 8, rect.h + r * 8),
                                     border_radius=20 + r * 4)
            self.screen.blit(glow, (rect.x - 20, rect.y - 20))

        # Рамка
        border_col = C_BORDER_HI if active else C_BORDER
        border_w = 3 if active else 2
        pygame.draw.rect(self.screen, border_col, rect, border_w, border_radius=16)

        # Превью
        preview_rect = pygame.Rect(rect.x + 20, rect.y + 20,
                                   rect.w - 40, 120)
        self._draw_preview(self.screen, g["preview"], preview_rect,
                           g["color"], hover)

        # Название
        name = self.font_card.render(g["name"], True, C_TEXT)
        self.screen.blit(name, (rect.x + 20, rect.y + 155))

        # Описание
        desc = self.font_desc.render(g["desc"], True, C_TEXT_DIM)
        self.screen.blit(desc, (rect.x + 20, rect.y + 195))

        # Рекорд (если есть)
        if g["id"] in self.scores:
            score = self.scores[g["id"]]
            rec = self.font_small.render(f"Рекорд: {score}", True, C_GOLD)
            self.screen.blit(rec, (rect.right - rec.get_width() - 20, rect.y + 200))

        # Стрелка при активной
        if active:
            arrow_x = rect.right - 30
            arrow_y = rect.y + 30
            arrow_off = int(4 * math.sin(self.tick * 0.15))
            pts = [
                (arrow_x + arrow_off, arrow_y),
                (arrow_x + arrow_off + 10, arrow_y + 8),
                (arrow_x + arrow_off, arrow_y + 16),
            ]
            pygame.draw.polygon(self.screen, g["color"], pts)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            if not self._handle_events():
                break
            self._update(dt)
            self._draw()
        return True


if __name__ == "__main__":
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    GameHub().run()
    pygame.quit()
    sys.exit(0)
