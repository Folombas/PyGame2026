import math, random
import pygame
from settings import *
import i18n as locale

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
daily_anim = 0.0

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


def draw_achievement_icon(surf, x, y, size, unlocked, color=GOLD):
    """Рисует неоновую иконку достижения."""
    rect = pygame.Rect(x, y, size, size)
    # Фон
    pygame.draw.rect(surf, (22, 20, 40), rect, border_radius=8)
    # Рамка
    pygame.draw.rect(surf, color if unlocked else (80, 80, 100), rect, 2, border_radius=8)
    # Звёздочка внутри
    cx, cy = x + size // 2, y + size // 2
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = size // 3 if i % 2 == 0 else size // 6
        points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    pygame.draw.polygon(surf, color if unlocked else (100, 100, 120), points)
    if not unlocked:
        # Затемнение
        pygame.draw.rect(surf, (0, 0, 0, 100), rect, border_radius=8)


def draw_daily_icon(surf, x, y, size, quest_type, done, color=ACCENT):
    """Рисует иконку для ежедневного задания."""
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(surf, (22, 20, 40), rect, border_radius=6)
    pygame.draw.rect(surf, color if done else (80, 80, 100), rect, 2, border_radius=6)
    # Простые символы для типов
    cx, cy = x + size // 2, y + size // 2
    if quest_type == 'lines':
        # Полоски
        for i in range(3):
            pygame.draw.line(surf, color if done else (100, 100, 120), (cx - 10, cy - 8 + i*8), (cx + 10, cy - 8 + i*8), 2)
    elif quest_type == 'score':
        # Звезда
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = 10 if i % 2 == 0 else 5
            points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
        pygame.draw.polygon(surf, color if done else (100, 100, 120), points)
    elif quest_type == 'time':
        # Часы
        pygame.draw.circle(surf, color if done else (100, 100, 120), (cx, cy), 10, 2)
        pygame.draw.line(surf, color if done else (100, 100, 120), (cx, cy), (cx, cy - 8), 2)
        pygame.draw.line(surf, color if done else (100, 100, 120), (cx, cy), (cx + 6, cy), 2)

# ---------- Экранные оверлеи и панели ----------



class Toggle:
    def __init__(self, x, y, w, h, initial=False, callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.state = initial
        self.callback = callback
        self.anim = 1.0 if initial else 0.0
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                if self.callback:
                    self.callback(self.state)

    def update(self, dt):
        target = 1.0 if self.state else 0.0
        self.anim += (target - self.anim) * min(1.0, dt / 80.0)

    def draw(self, surf):
        color = ACCENT if self.state else (60, 60, 80)
        if self.hovered:
            color = tuple(min(255, c + 30) for c in color)
        
        pygame.draw.rect(surf, color, self.rect, border_radius=self.rect.h // 2)
        
        # Кружочек
        r = self.rect.h - 8
        cx = self.rect.x + 4 + int(self.anim * (self.rect.w - r - 8)) + r // 2
        cy = self.rect.centery
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r // 2)

class Slider:
    def __init__(self, x, y, w, h, val=0.5, callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.val = val
        self.callback = callback
        self.dragging = False
        self.update_handle()

    def update_handle(self):
        self.handle_rect = pygame.Rect(self.rect.x + int(self.val * self.rect.w) - 8, self.rect.y - 6, 16, self.rect.h + 12)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_val(event.pos[0])

    def _update_val(self, mx):
        self.val = max(0.0, min(1.0, (mx - self.rect.x) / self.rect.w))
        self.update_handle()
        if self.callback:
            self.callback(self.val)

    def draw(self, surf):
        pygame.draw.rect(surf, (40, 36, 70), self.rect, border_radius=5)
        fill_w = int(self.val * self.rect.w)
        if fill_w > 0:
            pygame.draw.rect(surf, ACCENT, (self.rect.x, self.rect.y, fill_w, self.rect.h), border_radius=5)
        pygame.draw.rect(surf, TEXT, self.handle_rect, border_radius=8)
        pygame.draw.rect(surf, ACCENT, self.handle_rect, 2, border_radius=8)

class VolumeSlider:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.val = 0.4
        self.dragging = False
        self.update_handle()

    def update_handle(self):
        self.handle_rect = pygame.Rect(self.rect.x + int(self.val * self.rect.w) - 8, self.rect.y - 6, 16, self.rect.h + 12)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_val(event.pos[0])

    def _update_val(self, mx):
        self.val = max(0.0, min(1.0, (mx - self.rect.x) / self.rect.w))
        self.update_handle()

    def draw(self, surf):
        # Текст
        vol_text = F_SMALL.render(f"VOL: {int(self.val * 100)}%", True, MUTED)
        surf.blit(vol_text, (self.rect.centerx - vol_text.get_width()//2, self.rect.y - 25))
        
        # Дорожка
        pygame.draw.rect(surf, (40, 36, 70), self.rect, border_radius=5)
        # Заполнение
        fill_w = int(self.val * self.rect.w)
        if fill_w > 0:
            pygame.draw.rect(surf, ACCENT, (self.rect.x, self.rect.y, fill_w, self.rect.h), border_radius=5)
        # Ползунок
        pygame.draw.rect(surf, TEXT, self.handle_rect, border_radius=8)
        pygame.draw.rect(surf, ACCENT, self.handle_rect, 2, border_radius=8)


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

def draw_grid_bg(surf, board_x, board_y, t=0):
    offset = int(math.sin(t / 500.0) * 10)
    col = (26 + offset, 22 + offset, 44 + offset)
    for y in range(ROWS):
        for x in range(COLS):
            pygame.draw.rect(surf, col,
                             (board_x + x*CELL, board_y + y*CELL, CELL, CELL), 1)

def draw_cell(surf, px, py, color, glow=0.0, ghost=False, size=CELL):
    r = pygame.Rect(px + 1, py + 1, size - 2, size - 2)
    if ghost:
        pygame.draw.rect(surf, color, r, 1, border_radius=4)
        return
    if glow > 0.05:
        g = pygame.Surface((size + 8, size + 8), pygame.SRCALPHA)
        for i in range(4, 0, -1):
            a = int(60 * glow * (5 - i) / 4)
            pygame.draw.rect(g, (*color, a), (4 - i, 4 - i, size + 2*i, size + 2*i),
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
                draw_cell(surf, ox + x*cell, oy + y*cell, color, size=cell)

def draw_text_center(surf, text, y, font, color=TEXT):
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(WIDTH // 2, y)))

def draw_menu(surf, buttons, t, stars, meta=None):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    stars.draw(surf)
    draw_title(surf, "PYTETRIS", 110, t)
    s = F_MED.render("★ Neon Edition ★", True, ACCENT)
    surf.blit(s, s.get_rect(center=(WIDTH // 2, 180)))
    if meta:
        total = meta.get('total_lines', 0)
        best = meta.get('best_score', 0)
        stat = F_SMALL.render(f"{locale.t('total_lines')}: {total}   |   {locale.t('best_score')}: {best}", True, MUTED)
        surf.blit(stat, stat.get_rect(center=(WIDTH // 2, 148)))
    # Панель для кнопок
    panel_rect = pygame.Rect(WIDTH // 2 - 150, 185, 300, 400)
    pygame.draw.rect(surf, (12, 10, 24, 200), panel_rect, border_radius=20)
    pygame.draw.rect(surf, ACCENT, panel_rect, 1, border_radius=20)

    for b in buttons:
        b.draw(surf)

def draw_pause(surf):
    draw_overlay(surf, 170)
    draw_text_center(surf, locale.t("paused"), HEIGHT // 2 - 40, F_TITLE, ACCENT)


def draw_leaderboard(surf, scores, best):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "LEADERBOARD", 90, pygame.time.get_ticks())
    rect = pygame.Rect(WIDTH // 2 - 240, 170, 480, 470)
    panel(surf, rect, accent=GOLD)
    if not scores:
        s = F_MED.render("No scores yet — play to set one!", True, MUTED)
        surf.blit(s, s.get_rect(center=(rect.centerx, rect.centery)))
        return
    # Пытаемся загрузить медали из assets/medals
    medal_imgs = []
    try:
        for name in ("medal_gold.png", "medal_silver.png", "medal_bronze.png"):
            img = pygame.image.load(f"assets/medals/{name}").convert_alpha()
            img = pygame.transform.scale(img, (24, 24))
            medal_imgs.append(img)
    except:
        medal_imgs = []

    for i, sc in enumerate(scores[:10]):
        y = rect.y + 80 + i * 38
        color = GOLD if i == 0 else TEXT
        if i < 3:
            if len(medal_imgs) == 3:
                surf.blit(medal_imgs[i], (rect.x + 30, y))
            else:
                pygame.draw.circle(surf, (255, 215, 0) if i==0 else (192,192,192) if i==1 else (205,127,50), (rect.x + 50, y + 14), 12)
        rank = F_MED.render(f"{i+1:>2}.", True, color)
        surf.blit(rank, (rect.x + 80, y))
        num = F_MED.render(f"{sc}", True, color)
        surf.blit(num, (rect.x + 140, y))
    if best:
        s = F_SMALL.render(f"Personal best: {best}", True, ACCENT)
        surf.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

def draw_achievements(surf, meta, ach_list):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, locale.t("ach"), 70, pygame.time.get_ticks())
    unlocked = meta.get('unlocked', {})
    rect = pygame.Rect(0, 0, 560, 520)
    rect.center = (WIDTH // 2, HEIGHT // 2 + 20)
    panel(surf, rect, accent=ACCENT2)
    for i, a in enumerate(ach_list):
        y = rect.y + 40 + i * 60
        done = a['id'] in unlocked
        color = ACCENT if done else MUTED
        draw_achievement_icon(surf, rect.x + 20, y, 40, done)
        name = F_MED.render(locale.t(a['name_key']), True, color)
        surf.blit(name, (rect.x + 80, y + 2))
        desc = F_SMALL.render(locale.t(a['desc_key']), True, (180, 180, 220) if done else (110, 110, 140))
        surf.blit(desc, (rect.x + 80, y + 26))

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
        draw_daily_icon(surf, rect.x + 30, y, 36, q['type'], done)
        bar = pygame.Rect(rect.x + 80, y + 35, rect.w - 140, 18)
        pygame.draw.rect(surf, (40, 36, 70), bar, border_radius=9)
        global daily_anim
        target_fill = min(1.0, cur / tgt) if tgt else 0
        daily_anim += (target_fill - daily_anim) * 0.1
        if daily_anim > 0.01:
            fw = int(bar.w * daily_anim)
            pygame.draw.rect(surf, ACCENT if not done else GOLD,
                             (bar.x, bar.y, fw, bar.h), border_radius=9)
        pygame.draw.rect(surf, ACCENT, bar, 2, border_radius=9)
        title = F_MED.render(q['desc'], True, TEXT)
        surf.blit(title, (rect.x + 80, y))
        stat = F_SMALL.render(
            f"{cur:.0f} / {tgt}" if q['type'] != 'time'
            else f"{int(cur)}s / {tgt}s",
            True, GOLD if done else MUTED)
        surf.blit(stat, (rect.right - 40 - stat.get_width(), y + 2))



def draw_collection(surf, meta):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, locale.t("collection"), 70, pygame.time.get_ticks())
    rect = pygame.Rect(WIDTH // 2 - 280, 140, 560, 420)
    panel(surf, rect, accent=GOLD)
    level = meta.get('player_level', 1)
    unlocked_count = min(5, level - 1)  # Например, 5 карточек
    for i in range(5):
        x = rect.x + 40 + (i % 3) * 180
        y = rect.y + 50 + (i // 3) * 180
        card_rect = pygame.Rect(x, y, 140, 160)
        if i < unlocked_count:
            # Рисуем карточку (упрощённо)
            pygame.draw.rect(surf, (30, 30, 60), card_rect, border_radius=10)
            pygame.draw.rect(surf, GOLD, card_rect, 2, border_radius=10)
            txt = F_SMALL.render(f"Card {i+1}", True, TEXT)
            surf.blit(txt, txt.get_rect(center=(card_rect.centerx, card_rect.centery)))
        else:
            pygame.draw.rect(surf, (20, 20, 40), card_rect, border_radius=10)
            pygame.draw.rect(surf, (60, 60, 80), card_rect, 2, border_radius=10)
            lock = F_H2.render("?", True, MUTED)
            surf.blit(lock, lock.get_rect(center=card_rect.center))

def draw_settings(surf, music_slider, sfx_slider, ghost_toggle, shake_toggle, speed_slider, grid_toggle, back_btn):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, locale.t("settings"), 70, pygame.time.get_ticks())
    rect = pygame.Rect(WIDTH // 2 - 240, 140, 480, 400)
    panel(surf, rect, accent=ACCENT)
    
    y = rect.y + 40
    # Музыка
    m_txt = F_MED.render(locale.t("music"), True, TEXT)
    surf.blit(m_txt, (rect.x + 40, y))
    music_slider.rect.x = rect.x + 200
    music_slider.update_handle()
    music_slider.draw(surf)
    y += 60
    
    # Звуки
    s_txt = F_MED.render(locale.t("sfx"), True, TEXT)
    surf.blit(s_txt, (rect.x + 40, y))
    sfx_slider.rect.x = rect.x + 200
    sfx_slider.update_handle()
    sfx_slider.draw(surf)
    y += 80
    
    # Призрак
    g_txt = F_MED.render(locale.t("ghost"), True, TEXT)
    surf.blit(g_txt, (rect.x + 40, y))
    ghost_toggle.rect.x = rect.right - 100
    ghost_toggle.rect.y = y - 5
    ghost_toggle.draw(surf)
    y += 60
    
    # Тряска
    sh_txt = F_MED.render(locale.t("shake"), True, TEXT)
    surf.blit(sh_txt, (rect.x + 40, y))
    shake_toggle.rect.x = rect.right - 100
    shake_toggle.rect.y = y - 5
    shake_toggle.draw(surf)
    y += 60

    # Скорость падения
    sp_txt = F_MED.render("Speed", True, TEXT)
    surf.blit(sp_txt, (rect.x + 40, y))
    if speed_slider:
        speed_slider.rect.x = rect.x + 200
        speed_slider.update_handle()
        speed_slider.draw(surf)
    y += 60

    # Сетка
    gr_txt = F_MED.render("Grid", True, TEXT)
    surf.blit(gr_txt, (rect.x + 40, y))
    if grid_toggle:
        grid_toggle.rect.x = rect.right - 100
        grid_toggle.rect.y = y - 5
        grid_toggle.draw(surf)

    # Кнопка назад
    back_btn.draw(surf)

def draw_hud(surf, game, sidebar_x, t):
    # Score / level / lines
    draw_text_center  # silence lint
    x = sidebar_x
    y = 40
    labels = [(locale.t("score"), str(game.score), ACCENT),
              (locale.t("level"), str(game.level), ACCENT2),
              (locale.t("lines"), str(game.lines), GOLD)]
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
    lab = F_SMALL.render(locale.t("next"), True, MUTED)
    surf.blit(lab, (x + 12, y + 12))
    draw_piece_mini(surf, game.next.shape, game.next.color,
                    nb.centerx, nb.centery + 10, cell=20)
    if getattr(game, 'b2b', False):
        b = F_SMALL.render("B2B", True, GOLD)
        surf.blit(b, (x, y + 260))
    # Combo
    if game.combo > 1:
        c = F_H2.render(f"COMBO x{game.combo}", True, GOLD)
        surf.blit(c, c.get_rect(midtop=(x + 100, HEIGHT - 110)))
    # HOLD
    hb = pygame.Rect(x, y + 145, 200, 105)
    pygame.draw.rect(surf, (22, 20, 40), hb, border_radius=12)
    pygame.draw.rect(surf, GOLD, hb, 2, border_radius=12)
    hl = F_SMALL.render(locale.t("hold") + " (C)", True, MUTED)
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
