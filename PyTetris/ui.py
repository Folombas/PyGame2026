import math, random
import pygame
from settings import *

pygame.font.init()
def _font(size, bold=False):
    # Пытаемся загрузить Russo One из assets
    import os
    font_path = os.path.join('assets', 'Russo_One.ttf')
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            pass
    for name in ('Inter', 'Segoe UI', 'DejaVu Sans', 'Arial'):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

F_TITLE  = _font(72, bold=True)
F_H1     = _font(44, bold=True)
F_H2     = _font(30, bold=True)
F_MED    = _font(22)
F_SMALL  = _font(17)
F_TINY   = _font(14)

class Button:
    def __init__(self, label, cx, cy, w, h, on_click, accent=ACCENT):
        self.label = label
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)
        self.on_click = on_click
        self.accent = accent
        self.hovered = False
        self.pressed = False
        self.pulse = 0.0

    def update(self, dt, mouse):
        self.hovered = self.rect.collidepoint(mouse)
        target = 1.0 if self.hovered else 0.0
        self.pulse += (target - self.pulse) * min(1.0, dt / 120.0)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
            self.pressed = False

    def draw(self, surf):
        p = self.pulse
        base = (30, 28, 60)
        col = tuple(int(base[i] + (self.accent[i] - base[i]) * (0.35 + 0.35 * p)) for i in range(3))
        rect = self.rect.copy()
        if self.pressed:
            rect = rect.inflate(-4, -4)
        # glow
        if p > 0.05:
            glow = pygame.Surface((rect.w + 24, rect.h + 24), pygame.SRCALPHA)
            for i in range(10, 0, -1):
                a = int(28 * p * (11 - i) / 10)
                pygame.draw.rect(glow, (*self.accent, a),
                                 (12 - i, 12 - i, rect.w + 2*i, rect.h + 2*i),
                                 border_radius=14 + i)
            surf.blit(glow, (rect.x - 12, rect.y - 12))
        pygame.draw.rect(surf, col, rect, border_radius=12)
        pygame.draw.rect(surf, self.accent, rect, 2, border_radius=12)
        txt = F_H2.render(self.label, True, TEXT)
        surf.blit(txt, txt.get_rect(center=rect.center))

def vertical_gradient(surf, top, bottom):
    h = surf.get_height()
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (surf.get_width(), y))

class Starfield:
    def __init__(self, w, h, n=60):
        self.w, self.h = w, h
        self.stars = [[random.uniform(0, w), random.uniform(0, h),
                       random.uniform(0.2, 1.6)] for _ in range(n)]
    def update(self, dt):
        f = dt / 16.67
        for s in self.stars:
            s[1] += s[2] * f
            if s[1] > self.h:
                s[0] = random.uniform(0, self.w)
                s[1] = -2
    def draw(self, surf):
        for x, y, sp in self.stars:
            a = int(120 + 100 * min(1.0, sp))
            pygame.draw.circle(surf, (a, a, min(255, a + 40)), (int(x), int(y)), 1)

def draw_title(surf, text, y, t):
    """Animated glowing title."""
    wave = math.sin(t / 400) * 4
    glow = F_TITLE.render(text, True, ACCENT2)
    for i, a in [(6, 25), (3, 45), (1, 90)]:
        s = F_TITLE.render(text, True, (*ACCENT2, a))
        s.set_alpha(a)
        surf.blit(s, s.get_rect(center=(WIDTH // 2 + i, y + wave)))
    main = F_TITLE.render(text, True, TEXT)
    surf.blit(main, main.get_rect(center=(WIDTH // 2, y + wave)))
    for i, a in [(3, 60), (1, 120)]:
        s = F_TITLE.render(text, True, ACCENT)
        s.set_alpha(a)
        surf.blit(s, s.get_rect(center=(WIDTH // 2 - i, y + wave)))

# ---------- Экранные оверлеи и панели ----------

def draw_overlay(surf, alpha=190):
    o = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    o.fill((0, 0, 0, alpha))
    surf.blit(o, (0, 0))

def panel(surf, rect, title=None, accent=ACCENT):
    pygame.draw.rect(surf, (22, 20, 40), rect, border_radius=16)
    pygame.draw.rect(surf, accent, rect, 2, border_radius=16)
    if title:
        t = F_H1.render(title, True, accent)
        surf.blit(t, t.get_rect(midtop=(rect.centerx, rect.y + 14)))

def draw_playfield_frame(surf, board_x, board_y):
    pygame.draw.rect(surf, (40, 36, 70),
                     (board_x - 4, board_y - 4, BOARD_W + 8, BOARD_H + 8),
                     border_radius=10)
    pygame.draw.rect(surf, ACCENT,
                     (board_x - 4, board_y - 4, BOARD_W + 8, BOARD_H + 8),
                     2, border_radius=10)

def draw_grid_bg(surf, board_x, board_y):
    for y in range(ROWS):
        for x in range(COLS):
            pygame.draw.rect(surf, GRID,
                             (board_x + x*CELL, board_y + y*CELL, CELL, CELL), 1)

def draw_cell(surf, px, py, color, glow=0.0, ghost=False):
    r = pygame.Rect(px + 1, py + 1, CELL - 2, CELL - 2)
    if ghost:
        pygame.draw.rect(surf, (*color, ), r, 1, border_radius=4)
        return
    if glow > 0.05:
        g = pygame.Surface((CELL + 8, CELL + 8), pygame.SRCALPHA)
        for i in range(4, 0, -1):
            a = int(60 * glow * (5 - i) / 4)
            pygame.draw.rect(g, (*color, a), (4 - i, 4 - i, CELL + 2*i, CELL + 2*i),
                             border_radius=4 + i)
        surf.blit(g, (px - 4, py - 4))
    pygame.draw.rect(surf, color, r, border_radius=4)
    hi = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surf, hi, r, 1, border_radius=4)

def draw_piece_mini(surf, shape, color, cx, cy, cell=22):
    w = len(shape[0]); h = len(shape)
    ox = cx - w * cell // 2
    oy = cy - h * cell // 2
    for y, row in enumerate(shape):
        for x, v in enumerate(row):
            if v:
                draw_cell(surf, ox + x*cell, oy + y*cell, color)

def draw_text_center(surf, text, y, font, color=TEXT):
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(WIDTH // 2, y)))

def draw_menu(surf, buttons, t, stars):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    stars.draw(surf)
    draw_title(surf, "PYTETRIS", 110, t)
    s = F_MED.render("★ Neon Edition ★", True, ACCENT)
    surf.blit(s, s.get_rect(center=(WIDTH // 2, 180)))
    for b in buttons:
        b.draw(surf)

def draw_pause(surf):
    draw_overlay(surf, 170)
    draw_text_center(surf, "PAUSED", HEIGHT // 2 - 40, F_TITLE, ACCENT)
    draw_text_center(surf, "ESC — resume   |   Q — quit to menu",
                     HEIGHT // 2 + 40, F_MED, MUTED)

def draw_leaderboard(surf, scores, best):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "LEADERBOARD", 90, pygame.time.get_ticks())
    rect = pygame.Rect(WIDTH // 2 - 220, 170, 440, 470)
    panel(surf, rect, accent=GOLD)
    if not scores:
        s = F_MED.render("No scores yet — play to set one!", True, MUTED)
        surf.blit(s, s.get_rect(center=(rect.centerx, rect.centery)))
        return
    for i, sc in enumerate(scores[:10]):
        y = rect.y + 80 + i * 36
        color = GOLD if i == 0 else TEXT
        rank = F_MED.render(f"{i+1:>2}.", True, color)
        surf.blit(rank, (rect.x + 40, y))
        num = F_MED.render(f"{sc}", True, color)
        surf.blit(num, (rect.x + 100, y))
    if best:
        s = F_SMALL.render(f"Personal best: {best}", True, ACCENT)
        surf.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

def draw_achievements(surf, meta, ach_list):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "ACHIEVEMENTS", 70, pygame.time.get_ticks())
    unlocked = meta.get('unlocked', {})
    rect = pygame.Rect(WIDTH // 2 - 280, 140, 560, 520)
    panel(surf, rect, accent=ACCENT2)
    for i, a in enumerate(ach_list):
        y = rect.y + 40 + i * 48
        done = a['id'] in unlocked
        color = ACCENT if done else MUTED
        mark = "★" if done else "☆"
        m = F_MED.render(mark, True, color)
        surf.blit(m, (rect.x + 20, y))
        name = F_MED.render(a['name'], True, color)
        surf.blit(name, (rect.x + 60, y))
        desc = F_SMALL.render(a['desc'], True, (180, 180, 220) if done else (110, 110, 140))
        surf.blit(desc, (rect.x + 60, y + 24))

def draw_dailies(surf, meta, quests):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "DAILY QUESTS", 70, pygame.time.get_ticks())
    rect = pygame.Rect(WIDTH // 2 - 280, 160, 560, 420)
    panel(surf, rect, accent=ACCENT)
    p = meta.get('dailies', {}).get(__import__('meta').today_key(),
                                     {'lines': 0, 'score': 0, 'time': 0})
    for i, q in enumerate(quests):
        y = rect.y + 50 + i * 120
        cur = p.get(q['type'], 0)
        tgt = q['target']
        done = cur >= tgt
        bar = pygame.Rect(rect.x + 30, y + 60, rect.w - 60, 18)
        pygame.draw.rect(surf, (40, 36, 70), bar, border_radius=9)
        fill = min(1.0, cur / tgt) if tgt else 0
        if fill > 0:
            fw = int(bar.w * fill)
            pygame.draw.rect(surf, ACCENT if not done else GOLD,
                             (bar.x, bar.y, fw, bar.h), border_radius=9)
        pygame.draw.rect(surf, ACCENT, bar, 2, border_radius=9)
        title = F_H2.render(q['desc'], True, TEXT)
        surf.blit(title, (rect.x + 30, y))
        stat = F_SMALL.render(
            f"{cur:.0f} / {tgt}" if q['type'] != 'time'
            else f"{int(cur)}s / {tgt}s",
            True, GOLD if done else MUTED)
        surf.blit(stat, (rect.right - 30 - stat.get_width(), y + 2))

def draw_hud(surf, game, sidebar_x, t):
    # Score / level / lines
    draw_text_center  # silence lint
    x = sidebar_x
    y = 40
    labels = [("SCORE", str(game.score), ACCENT),
              ("LEVEL", str(game.level), ACCENT2),
              ("LINES", str(game.lines), GOLD)]
    for label, val, col in labels:
        l = F_SMALL.render(label, True, MUTED)
        surf.blit(l, (x, y))
        v = F_H2.render(val, True, col)
        surf.blit(v, (x, y + 18))
        y += 78
    # Next
    nb = pygame.Rect(x, y + 6, 200, 130)
    pygame.draw.rect(surf, (22, 20, 40), nb, border_radius=12)
    pygame.draw.rect(surf, ACCENT2, nb, 2, border_radius=12)
    lab = F_SMALL.render("NEXT", True, MUTED)
    surf.blit(lab, (x + 12, y + 12))
    draw_piece_mini(surf, game.next.shape, game.next.color,
                    nb.centerx, nb.centery + 10, cell=20)
    # Combo
    if game.combo > 1:
        c = F_H2.render(f"COMBO x{game.combo}", True, GOLD)
        surf.blit(c, c.get_rect(midtop=(x + 100, HEIGHT - 110)))
    # HOLD
    hb = pygame.Rect(x, y + 145, 200, 105)
    pygame.draw.rect(surf, (22, 20, 40), hb, border_radius=12)
    pygame.draw.rect(surf, GOLD, hb, 2, border_radius=12)
    hl = F_SMALL.render("HOLD (C)", True, MUTED)
    surf.blit(hl, (x + 12, y + 150))
    if game.hold:
        hc = COLORS[game.hold]
        hs = SHAPES[game.hold]
        dim = game.hold_used
        col = tuple(c // 2 for c in hc) if dim else hc
        draw_piece_mini(surf, hs, col, hb.centerx, hb.centery + 12, cell=20)
    # Controls hint
    hint = F_TINY.render("← → move  ↑ rotate  ↓ soft  SPACE hard  C hold  P pause",
                         True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 8)))
