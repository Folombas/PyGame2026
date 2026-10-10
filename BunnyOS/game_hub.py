"""Game Hub — лаунчер игр BunnyOS в стиле ретро-консоли."""
import os
import sys
import json
import math
import random
import subprocess
import pygame
from settings import WIDTH, HEIGHT, TASKBAR_H


FPS = 60
HUB_W = WIDTH
HUB_H = HEIGHT - TASKBAR_H

# === ЦВЕТА (ретро-консоль) ===
C_BG_TOP    = (8, 10, 20)
C_BG_BOT    = (20, 12, 35)
C_CARD      = (18, 22, 38)
C_CARD_SEL  = (28, 36, 60)
C_BORDER    = (60, 80, 120)
C_BORDER_HI = (255, 220, 100)
C_TEXT      = (230, 240, 255)
C_TEXT_DIM  = (110, 130, 160)
C_ACCENT    = (100, 180, 255)
C_GOLD      = (255, 220, 100)
C_GRID      = (25, 35, 55)

SCORES_PATH = os.path.expanduser("~/.bunny_games/highscores.json")
FONT_PATH = "assets/fonts/PressStart2P.ttf"
FONT_DESC = "assets/fonts/VT323.ttf"


GAMES = [
    {"id": "snake",  "name": "SNAKE",  "desc": "Collect apples. Don't bite yourself.",
     "file": "snake.py",    "color": (80, 220, 120), "icon": "terminal"},
    {"id": "tetris", "name": "TETRIS", "desc": "7 pieces. 4 lines. Combos x2 x3 x4.",
     "file": "tetris.py",   "color": (200, 120, 240), "icon": "tetris"},
    {"id": "2048",   "name": "2048",   "desc": "Merge tiles. Reach 2048!",
     "file": "game2048.py", "color": (240, 200, 80), "icon": "calculator"},
    {"id": "pong",   "name": "PONG",   "desc": "Play vs AI. First to 7.",
     "file": "pong.py",     "color": (255, 130, 100), "icon": "browser"},
]


class GameHub:
    def __init__(self):
        self.screen = pygame.display.set_mode((HUB_W, HUB_H))
        pygame.display.set_caption("Game Hub — BunnyOS")

        # === Шрифты ===
        if os.path.exists(FONT_PATH):
            self.f_title = pygame.font.Font(FONT_PATH, 32)
            self.f_card = pygame.font.Font(FONT_PATH, 14)
            self.f_small = pygame.font.Font(FONT_PATH, 10)
            self.font_ok = True
        else:
            self.f_title = pygame.font.Font(None, 56)
            self.f_card = pygame.font.Font(None, 28)
            self.f_small = pygame.font.Font(None, 18)
            self.font_ok = False

        if os.path.exists(FONT_DESC):
            self.f_desc = pygame.font.Font(FONT_DESC, 24)
        else:
            self.f_desc = pygame.font.Font(None, 20)

        self.clock = pygame.time.Clock()
        self.selected = 0
        self.tick = 0
        self.scores = self._load_scores()
        self.card_anims = [0.0 for _ in GAMES]
        self.hover_anims = [0.0 for _ in GAMES]
        self.stars = self._make_stars(80)
        self.bg_cache = None

        # Иконки игр — из retro pack
        self.icons = {}
        try:
            from ui import load_icon
            for g in GAMES:
                img = load_icon(g["icon"], 96)
                self.icons[g["id"]] = img
        except Exception:
            pass

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
             "r": rng.uniform(0.5, 1.8), "a": rng.randint(40, 180),
             "speed": rng.uniform(0.2, 0.8), "col": rng.choice([
                 (180, 200, 255), (255, 220, 180), (200, 180, 255)])}
            for _ in range(n)
        ]

    def _make_bg(self):
        s = pygame.Surface((HUB_W, HUB_H))
        for y in range(HUB_H):
            t = y / HUB_H
            r = int(C_BG_TOP[0] * (1 - t) + C_BG_BOT[0] * t)
            g = int(C_BG_TOP[1] * (1 - t) + C_BG_BOT[1] * t)
            b = int(C_BG_TOP[2] * (1 - t) + C_BG_BOT[2] * t)
            pygame.draw.line(s, (r, g, b), (0, y), (HUB_W, y))

        # Сетка перспективы (ретро-стиль)
        horizon = HUB_H // 2
        # Горизонтальные линии
        for i in range(20):
            t = i / 20
            y = horizon + int((HUB_H - horizon) * t * t)
            a = int(60 * (1 - t * 0.5))
            pygame.draw.line(s, (*C_GRID, a), (0, y), (HUB_W, y))

        # Вертикальные линии (сходятся к центру горизонта)
        cx = HUB_W // 2
        for i in range(-10, 11):
            x_bottom = cx + i * (HUB_W // 10)
            pygame.draw.line(s, C_GRID, (cx, horizon), (x_bottom, HUB_H))

        # Свечение горизонта
        glow = pygame.Surface((HUB_W, 100), pygame.SRCALPHA)
        for i in range(50):
            a = int(80 * (1 - i / 50))
            pygame.draw.line(glow, (*C_ACCENT, a), (0, 50 - i), (HUB_W, 50 - i))
            pygame.draw.line(glow, (*C_ACCENT, a), (0, 50 + i), (HUB_W, 50 + i))
        s.blit(glow, (0, horizon - 50))

        return s

    def _card_rect(self, i):
        card_w, card_h = 400, 250
        gap_x, gap_y = 40, 30
        total_w = card_w * 2 + gap_x
        x0 = (HUB_W - total_w) // 2
        y0 = 150
        col = i % 2
        row = i // 2
        return pygame.Rect(
            x0 + col * (card_w + gap_x),
            y0 + row * (card_h + gap_y),
            card_w, card_h,
        )

    def _draw_grid_bg(self, scr, rect):
        """Сетка на фоне карточки."""
        for x in range(rect.x, rect.right, 20):
            pygame.draw.line(scr, (30, 40, 60),
                             (x, rect.y), (x, rect.bottom))
        for y in range(rect.y, rect.bottom, 20):
            pygame.draw.line(scr, (30, 40, 60),
                             (rect.x, y), (rect.right, y))

    def _draw_preview(self, scr, kind, rect, color, hover):
        inner = rect.inflate(-20, -20)
        # Фон
        pygame.draw.rect(scr, (8, 10, 18), inner, border_radius=6)
        # Сетка
        self._draw_grid_bg(scr, inner)

        cx, cy = inner.centerx, inner.centery

        if kind == "snake":
            cell = 18
            start_x = cx - 3 * cell
            start_y = cy - cell // 2
            for i in range(5):
                col = color if i > 0 else (255, 255, 255)
                pygame.draw.rect(scr, col,
                                 (start_x + i * cell, start_y, cell - 2, cell - 2),
                                 border_radius=2)
            # Яблоко
            pygame.draw.circle(scr, (255, 60, 100), (cx + 90, cy - 30), 10)
            pygame.draw.circle(scr, (255, 120, 140), (cx + 90, cy - 30), 10, 2)

        elif kind == "tetris":
            block = 22
            base_x = cx - 3 * block
            base_y = cy + 25
            colors = [(80, 220, 240), (250, 220, 80), (190, 100, 240),
                      (100, 230, 120), (240, 90, 110), (80, 130, 250)]
            for x in range(6):
                col = colors[x % len(colors)]
                pygame.draw.rect(scr, col,
                                 (base_x + x * block, base_y, block - 2, block - 2),
                                 border_radius=3)
            # Падающая фигура
            falling_x = cx - 2 * block
            falling_y = cy - 45
            for dx in (-1, 0, 1):
                pygame.draw.rect(scr, colors[2],
                                 (falling_x + dx * block, falling_y,
                                  block - 2, block - 2),
                                 border_radius=3)
            pygame.draw.rect(scr, colors[2],
                             (falling_x, falling_y - block, block - 2, block - 2),
                             border_radius=3)

        elif kind == "2048":
            cell = 52
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
            pygame.draw.rect(scr, (100, 200, 255),
                             (cx - 110, cy - 30, 8, 60), border_radius=3)
            pygame.draw.rect(scr, (255, 130, 100),
                             (cx + 102, cy - 20, 8, 60), border_radius=3)
            pygame.draw.circle(scr, (240, 240, 220), (cx, cy), 8)
            for i in range(3):
                a = 120 - i * 40
                s = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(s, (240, 240, 220, a), (5, 5), 5 - i)
                scr.blit(s, (cx - 20 - i * 8, cy - 5))

        # Цветное свечение внутри при hover
        if hover > 0.01:
            glow = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
            glow.fill((*color, int(40 * hover)))
            scr.blit(glow, inner.topleft, special_flags=pygame.BLEND_RGBA_ADD)

    def _launch(self, game):
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
                for i in range(len(GAMES)):
                    if self._card_rect(i).collidepoint(mx, my):
                        self.selected = i
                        break
        return True

    def _update(self, dt):
        self.tick += 1
        for i in range(len(GAMES)):
            self.card_anims[i] = min(1.0, self.card_anims[i] + dt * 1.8)
        for i in range(len(GAMES)):
            target = 1.0 if i == self.selected else 0.0
            self.hover_anims[i] += (target - self.hover_anims[i]) * dt * 10
        # Звёзды
        for s in self.stars:
            s["y"] += s["speed"]
            if s["y"] > HUB_H:
                s["y"] = -2
                s["x"] = random.uniform(0, HUB_W)

    def _draw(self):
        if self.bg_cache is None:
            self.bg_cache = self._make_bg()
        self.screen.blit(self.bg_cache, (0, 0))

        # Звёзды
        for s in self.stars:
            surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*s["col"], s["a"]), (2, 2), int(s["r"]))
            self.screen.blit(surf, (s["x"], s["y"]))

        # Заголовок
        title = self.f_title.render("GAME HUB", True, C_GOLD)
        # Двойной контур для ретро-эффекта
        title_shadow = self.f_title.render("GAME HUB", True, (100, 60, 20))
        tx = HUB_W // 2 - title.get_width() // 2
        self.screen.blit(title_shadow, (tx + 3, 36))
        self.screen.blit(title, (tx, 33))

        # Мигающий подзаголовок
        if (self.tick // 30) % 2 == 0:
            sub = self.f_small.render("* BUNNYOS ARCADE COLLECTION *", True, C_ACCENT)
            self.screen.blit(sub, (HUB_W // 2 - sub.get_width() // 2, 100))

        # Карточки
        for i, g in enumerate(GAMES):
            self._draw_card(i, g)

        # Подсказки
        hint = self.f_small.render(
            "ARROWS/WASD=MOVE   ENTER=PLAY   ESC=EXIT",
            True, C_TEXT_DIM
        )
        self.screen.blit(hint, (HUB_W // 2 - hint.get_width() // 2, HUB_H - 25))

        # CRT-эффект (сканлайны)
        self._draw_scanlines()

        pygame.display.flip()

    def _draw_scanlines(self):
        """Тонкие горизонтальные полосы для CRT-эффекта."""
        scanline = pygame.Surface((HUB_W, HUB_H), pygame.SRCALPHA)
        for y in range(0, HUB_H, 3):
            pygame.draw.line(scanline, (0, 0, 0, 30), (0, y), (HUB_W, y))
        self.screen.blit(scanline, (0, 0))

    def _draw_card(self, i, g):
        base_rect = self._card_rect(i)
        anim = self.card_anims[i]
        hover = self.hover_anims[i]
        active = (i == self.selected)

        offset_y = int((1 - anim) * 80)
        rect = base_rect.move(0, offset_y)

        scale = 1.0 + hover * 0.04
        if scale != 1.0:
            new_w = int(rect.w * scale)
            new_h = int(rect.h * scale)
            rect = pygame.Rect(0, 0, new_w, new_h)
            rect.center = base_rect.center
            rect.y += offset_y

        # Тень
        shadow = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120),
                         (10, 10, rect.w, rect.h), border_radius=8)
        self.screen.blit(shadow, (rect.x - 10, rect.y - 10))

        # Фон карточки
        card_col = C_CARD_SEL if active else C_CARD
        pygame.draw.rect(self.screen, card_col, rect, border_radius=8)

        # Свечение вокруг активной карточки (пульсирующее)
        if active:
            pulse = 0.5 + 0.5 * math.sin(self.tick * 0.12)
            glow = pygame.Surface((rect.w + 40, rect.h + 40), pygame.SRCALPHA)
            for r in range(6):
                a = int(60 * pulse) - r * 8
                if a > 0:
                    pygame.draw.rect(glow, (*g["color"], a),
                                     (20 - r * 3, 20 - r * 3,
                                      rect.w + r * 6, rect.h + r * 6),
                                     border_radius=10 + r * 3, width=2)
            self.screen.blit(glow, (rect.x - 20, rect.y - 20))

        # Рамка карточки — пиксельный стиль
        border_col = C_BORDER_HI if active else C_BORDER
        border_w = 3 if active else 2
        # Уголки (пиксель-арт стиль)
        pygame.draw.rect(self.screen, border_col, rect, border_w, border_radius=8)

        # Угловые акценты (как у пиксельной рамки)
        cl = 12  # длина уголка
        th = 4   # толщина
        for (ax, ay, dx, dy) in [
            (rect.x, rect.y, 1, 1),
            (rect.right - cl, rect.y, 1, 1),
            (rect.x, rect.bottom - cl, 1, 1),
            (rect.right - cl, rect.bottom - cl, 1, 1),
        ]:
            # Горизонтальная полоска уголка
            pygame.draw.rect(self.screen, g["color"],
                             (ax, ay if dy == 1 else rect.bottom - th,
                              cl, th))
            # Вертикальная полоска уголка
            pygame.draw.rect(self.screen, g["color"],
                             (ax if dx == 1 else rect.right - th, ay,
                              th, cl))

        # Иконка игры — слева сверху
        icon_x = rect.x + 20
        icon_y = rect.y + 15
        icon_img = self.icons.get(g["id"])
        if icon_img:
            # Рамка вокруг иконки
            icon_bg = pygame.Rect(icon_x - 4, icon_y - 4, 64, 64)
            pygame.draw.rect(self.screen, (30, 38, 58), icon_bg, border_radius=6)
            pygame.draw.rect(self.screen, g["color"], icon_bg, 2, border_radius=6)
            small_icon = pygame.transform.scale(icon_img, (56, 56))
            self.screen.blit(small_icon, (icon_x, icon_y))

        # Название игры — справа от иконки
        name = self.f_card.render(g["name"], True, g["color"])
        self.screen.blit(name, (icon_x + 75, icon_y + 8))

        # Рекорд под названием
        if g["id"] in self.scores:
            rec = self.f_small.render(f"HI: {self.scores[g['id']]}", True, C_GOLD)
            self.screen.blit(rec, (icon_x + 75, icon_y + 32))

        # Превью под названием
        preview_rect = pygame.Rect(rect.x + 20, rect.y + 100,
                                    rect.w - 40, 130)
        self._draw_preview(self.screen, g["id"], preview_rect, g["color"], hover)

        # Описание внизу
        desc = self.f_desc.render(g["desc"], True, C_TEXT_DIM)
        self.screen.blit(desc, (rect.x + 20, rect.bottom - 28))

        # Стрелка-курсор справа (мигающая)
        if active and (self.tick // 15) % 2 == 0:
            ax = rect.right - 22
            ay = rect.centery
            pts = [(ax, ay - 8), (ax + 8, ay), (ax, ay + 8)]
            pygame.draw.polygon(self.screen, C_BORDER_HI, pts)

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
