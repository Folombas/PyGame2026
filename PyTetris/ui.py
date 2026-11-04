from cards import RARITY_COLORS
import math
import math, random
import pygame
from settings import *
import math
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

MEDAL_COLORS = [None, (120,80,40), (205,127,50), (192,192,192), (255,215,0), (180,230,255)]

def draw_medal(surf, x, y, size, tier):
    """tier: 0=empty, 1=bronze, 2=silver, 3=gold"""
    rect = pygame.Rect(x, y, size, size)
    if tier == 0:
        pygame.draw.circle(surf, (60, 60, 80), rect.center, size // 2, 2)
    else:
        pygame.draw.circle(surf, MEDAL_COLORS[tier], rect.center, size // 2)
        pygame.draw.circle(surf, (255, 255, 255), rect.center, size // 2, 2)
        # star
        cx, cy = rect.center
        pts = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            r = size // 3 if i % 2 == 0 else size // 6
            pts.append((cx + r * math.cos(ang), cy - r * math.sin(ang)))
        pygame.draw.polygon(surf, (30, 20, 10), pts)


def draw_card_icon(surf, x, y, w, h, rarity, unlocked, label=""):
    """Draws a card icon with rarity color."""
    col = RARITY_COLORS[rarity] if unlocked else (60, 60, 80)
    pygame.draw.rect(surf, (20, 18, 35), (x, y, w, h), border_radius=8)
    pygame.draw.rect(surf, col, (x, y, w, h), 2, border_radius=8)
    if unlocked:
        inner = pygame.Rect(x + 6, y + 6, w - 12, h - 12)
        pygame.draw.rect(surf, col, inner, 1, border_radius=5)
        if label:
            txt = F_SMALL.render(label, True, col)
            surf.blit(txt, txt.get_rect(center=(x + w // 2, y + h - 16)))
    else:
        lock = F_H2.render("?", True, (80, 80, 100))
        surf.blit(lock, lock.get_rect(center=(x + w // 2, y + h // 2)))


def draw_progress_bar(surf, x, y, w, h, frac, color):
    pygame.draw.rect(surf, (30, 28, 50), (x, y, w, h), border_radius=h // 2)
    if frac > 0:
        fw = max(1, int(w * min(1.0, frac)))
        pygame.draw.rect(surf, color, (x, y, fw, h), border_radius=h // 2)


def load_skin(name):
    try:
        img = pygame.image.load(f"assets/ui/{name}").convert_alpha()
        return img
    except:
        return None

# Загружаем скины
btn_skin = load_skin("neon_ui_basic.png")

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
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse)
        if self.hovered and not was_hovered:
            try:
                import audio
                audio.play('menu')
            except:
                pass
        target = 1.0 if self.hovered else 0.0
        self.pulse += (target - self.pulse) * min(1.0, dt / 80.0)

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
    def update(self, dt, speed_mult=1.0):
        f = (dt / 16.67) * speed_mult
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
    wave = math.sin(t / 400) * 4
    base_font = F_TITLE
    main_surf = base_font.render(text, True, TEXT)
    
    # Если текст слишком длинный (например, "ДОСТИЖЕНИЯ"), уменьшаем его
    if main_surf.get_width() > WIDTH - 40:
        scale = (WIDTH - 40) / main_surf.get_width()
        new_w = int(main_surf.get_width() * scale)
        new_h = int(main_surf.get_height() * scale)
        main_surf = pygame.transform.smoothscale(main_surf, (new_w, new_h))
    
    glow_base = base_font.render(text, True, ACCENT2)
    if glow_base.get_width() > WIDTH - 40:
        glow_base = pygame.transform.smoothscale(glow_base, main_surf.get_size())
    
    for i, a in [(6, 25), (3, 45), (1, 90)]:
        s = glow_base.copy()
        s.set_alpha(a)
        surf.blit(s, s.get_rect(center=(WIDTH // 2 + i, y + wave)))
        
    surf.blit(main_surf, main_surf.get_rect(center=(WIDTH // 2, y + wave)))
    
    acc_base = base_font.render(text, True, ACCENT)
    if acc_base.get_width() > WIDTH - 40:
        acc_base = pygame.transform.smoothscale(acc_base, main_surf.get_size())
    for i, a in [(3, 60), (1, 120)]:
        s = acc_base.copy()
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



def draw_gradient_panel(surf, rect, color1, color2):
    for i in range(rect.h):
        t = i / rect.h
        col = (
            int(color1[0] * (1 - t) + color2[0] * t),
            int(color1[1] * (1 - t) + color2[1] * t),
            int(color1[2] * (1 - t) + color2[2] * t),
        )
        pygame.draw.line(surf, col, (rect.x, rect.y + i), (rect.right, rect.y + i))

def draw_overlay(surf, alpha=190):
    o = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    o.fill((0, 0, 0, alpha))
    surf.blit(o, (0, 0))

def panel(surf, rect, title=None, accent=ACCENT):
    draw_gradient_panel(surf, rect, (22, 20, 40), (10, 8, 24))
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
    # Пульсация с использованием синуса
    pulse = math.sin(t / 300.0) * 15
    col = (int(26 + pulse), int(22 + pulse), int(44 + pulse * 1.5))
    for y in range(ROWS):
        for x in range(COLS):
            pygame.draw.rect(surf, col,
                             (board_x + x*CELL, board_y + y*CELL, CELL, CELL), 1)

def draw_cell(surf, px, py, color, glow=0.0, ghost=False, size=CELL):
    r = pygame.Rect(px + 1, py + 1, size - 2, size - 2)
    if ghost:
        # Пунктирная рамка
        for i in range(0, size, 6):
            pygame.draw.line(surf, color, (px + 1, py + i), (px + 1 + min(3, size - i), py + i), 2)
            pygame.draw.line(surf, color, (px + size - 2, py + i), (px + size - 2 - min(3, size - i), py + i), 2)
            pygame.draw.line(surf, color, (px + i, py + 1), (px + i, py + 1 + min(3, size - i)), 2)
            pygame.draw.line(surf, color, (px + i, py + size - 2), (px + i, py + size - 2 - min(3, size - i)), 2)
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
    shadow = font.render(text, True, (0, 0, 0))
    surf.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 2, y + 2)))
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(WIDTH // 2, y)))

def draw_menu(surf, buttons, t, stars, meta=None):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    stars.draw(surf)
    draw_title(surf, "PYTETRIS", 80, t)
    
    s = F_MED.render("★ Neon Edition ★", True, ACCENT)
    surf.blit(s, s.get_rect(center=(WIDTH // 2, 140)))
    
    if meta:
        medals = sum(1 for a in __import__('meta').ACHIEVEMENTS if meta['medals'].get(a['id'], 0) > 0)
        cards = len(meta.get('cards', []))
        from cards import CARDS
        mc = F_SMALL.render(f"🏅 {medals}/10    🃏 {cards}/{len(CARDS)}", True, GOLD)
        surf.blit(mc, mc.get_rect(center=(WIDTH // 2, 165)))
        total = meta.get('total_lines', 0)
        best = meta.get('best_score', 0)
        stat = F_SMALL.render(f"{locale.t('total_lines')}: {total}  |  {locale.t('best_score')}: {best}", True, MUTED)
        surf.blit(stat, stat.get_rect(center=(WIDTH // 2, 170)))

    # Панель под кнопки
    panel_rect = pygame.Rect(WIDTH // 2 - 160, 190, 320, 420)
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
    # mode records
    mode_stats = meta.get('mode_scores', {}) if 'meta' in dir() else {}
    try:
        import inspect
        frame = inspect.currentframe()
    except Exception:
        pass


def draw_achievements(surf, meta, ach_list):
    from meta import get_medal_tier, get_progress, get_achievement_points, get_global_rank
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    ap = get_achievement_points(meta)
    rank = get_global_rank(meta)
    draw_title(surf, locale.t("ach"), 30, pygame.time.get_ticks())
    header = F_SMALL.render(f"{locale.t('ap')}: {ap}   |   {locale.t('rank')}: {rank}/10", True, GOLD)
    surf.blit(header, header.get_rect(center=(WIDTH // 2, 75)))

    rect = pygame.Rect(WIDTH // 2 - 320, 100, 640, 580)
    panel(surf, rect, accent=ACCENT2)

    # Группируем по категориям
    cats = ['progress', 'skill', 'endurance', 'mastery']
    y_cursor = rect.y + 15
    for cat in cats:
        cat_ach = [a for a in ach_list if a.get('cat') == cat and (not a.get('hidden') or get_medal_tier(meta, a) > 0)]
        if not cat_ach: continue
        cat_label = F_SMALL.render(f"── {cat.upper()} ──", True, ACCENT)
        surf.blit(cat_label, (rect.x + 15, y_cursor))
        y_cursor += 22
        for a in cat_ach:
            tier = get_medal_tier(meta, a)
            cur, nxt, cur_tier = get_progress(meta, a)
            # 5 mini medals
            for t in range(1, 6):
                draw_medal(surf, rect.x + 15 + (t - 1) * 14, y_cursor + 4, 12, t if tier >= t else 0)
            color = ACCENT if tier > 0 else MUTED
            name = F_SMALL.render(locale.t(a['name_key']), True, color)
            surf.blit(name, (rect.x + 95, y_cursor))
            # progress bar
            if cur_tier < 5:
                frac = cur / nxt if nxt else 0
                draw_progress_bar(surf, rect.x + 320, y_cursor + 8, 250, 8, frac, MEDAL_COLORS[min(5, cur_tier + 1)] or (100,100,120))
                stat = F_TINY.render(f"{int(cur)}/{nxt}", True, MUTED)
                surf.blit(stat, (rect.x + 610 - stat.get_width(), y_cursor - 2))
            else:
                stat = F_TINY.render("MAX", True, GOLD)
                surf.blit(stat, (rect.x + 610 - stat.get_width(), y_cursor))
            y_cursor += 28
        y_cursor += 6
        if y_cursor > rect.bottom - 30: break

def draw_dailies(surf, meta, quests, weeklies=None):
    from meta import daily_progress, weekly_progress, get_streak_multiplier
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    streak = meta.get('daily_streak', 0)
    mult = get_streak_multiplier(meta)
    draw_title(surf, locale.t("daily"), 25, pygame.time.get_ticks())
    if streak > 0:
        s_lab = F_H2.render(f"🔥 {streak}  ({locale.t('streak_multiplier', n=mult)})", True, GOLD)
        surf.blit(s_lab, s_lab.get_rect(center=(WIDTH // 2, 68)))

    # DAILY block
    rect = pygame.Rect(WIDTH // 2 - 320, 100, 640, 260)
    panel(surf, rect, accent=ACCENT)
    dlabel = F_H2.render(locale.t("daily").upper(), True, ACCENT)
    surf.blit(dlabel, (rect.x + 15, rect.y + 8))
    p = daily_progress(meta)
    for i, q in enumerate(quests):
        y = rect.y + 45 + i * 70
        cur = p.get(q['type'], 0)
        tgt = q['target']
        done = cur >= tgt
        claimed = q['id'] in p.get('done', [])
        # icon
        draw_daily_icon(surf, rect.x + 20, y, 36, q['type'], done)
        # desc
        desc = F_MED.render(q['desc'], True, TEXT)
        surf.blit(desc, (rect.x + 70, y))
        # bar
        bar = pygame.Rect(rect.x + 70, y + 30, 380, 14)
        frac = min(1.0, cur / tgt) if tgt else 0
        draw_progress_bar(surf, bar.x, bar.y, bar.w, bar.h, frac, ACCENT if not done else GOLD)
        stat = F_SMALL.render(f"{int(cur)}/{tgt}", True, GOLD if done else MUTED)
        surf.blit(stat, (bar.right + 10, bar.y - 4))
        # claim button
        if done and not claimed:
            cb = pygame.Rect(rect.right - 90, y + 5, 70, 32)
            pygame.draw.rect(surf, GOLD, cb, border_radius=6)
            ct = F_SMALL.render(locale.t("claim"), True, (20, 20, 20))
            surf.blit(ct, ct.get_rect(center=cb.center))
        elif claimed:
            ct = F_SMALL.render(f"✓ {locale.t('claimed')}", True, ACCENT)
            surf.blit(ct, (rect.right - 130, y + 12))

    # WILDCARD block
    try:
        from meta import get_wildcard, wildcard_progress
        wc = get_wildcard()
        wcp = wildcard_progress(meta)
        wc_rect = pygame.Rect(WIDTH // 2 - 320, 360, 640, 60)
        panel(surf, wc_rect, accent=GOLD)
        wc_icon = F_H2.render("🌟", True, GOLD)
        surf.blit(wc_icon, (wc_rect.x + 12, wc_rect.y + 12))
        wc_lbl = F_SMALL.render("WILDCARD", True, GOLD)
        surf.blit(wc_lbl, (wc_rect.x + 55, wc_rect.y + 8))
        wc_desc = F_SMALL.render(locale.t(wc['desc_key']) if locale.t(wc['desc_key']) != wc['desc_key'] else wc['desc_key'], True, TEXT)
        surf.blit(wc_desc, (wc_rect.x + 55, wc_rect.y + 28))
        wc_bar = pygame.Rect(wc_rect.x + 380, wc_rect.y + 22, 180, 14)
        frac = min(1.0, wcp['cur'] / wc['target'])
        draw_progress_bar(surf, wc_bar.x, wc_bar.y, wc_bar.w, wc_bar.h, frac, GOLD if wcp['done'] else ACCENT)
        wc_stat = F_TINY.render(f"{wcp['cur']}/{wc['target']}", True, GOLD if wcp['done'] else MUTED)
        surf.blit(wc_stat, (wc_bar.right + 8, wc_bar.y - 2))
    except Exception:
        pass

    # WEEKLY block
    if weeklies:
        wrect = pygame.Rect(WIDTH // 2 - 320, 430, 640, 210)
        panel(surf, wrect, accent=ACCENT2)
        wlabel = F_H2.render(locale.t("weekly").upper(), True, ACCENT2)
        surf.blit(wlabel, (wrect.x + 15, wrect.y + 8))
        wp = weekly_progress(meta)
        for i, q in enumerate(weeklies):
            y = wrect.y + 45 + i * 70
            cur = wp.get(q['type'], 0)
            tgt = q['target']
            done = cur >= tgt
            claimed = q['id'] in wp.get('done', [])
            desc = F_MED.render(q['desc'], True, TEXT)
            surf.blit(desc, (wrect.x + 20, y))
            bar = pygame.Rect(wrect.x + 20, y + 30, 480, 14)
            frac = min(1.0, cur / tgt) if tgt else 0
            draw_progress_bar(surf, bar.x, bar.y, bar.w, bar.h, frac, ACCENT2 if not done else GOLD)
            stat = F_SMALL.render(f"{int(cur)}/{tgt}", True, GOLD if done else MUTED)
            surf.blit(stat, (bar.right + 10, bar.y - 4))
            if done and not claimed:
                cb = pygame.Rect(wrect.right - 90, y + 5, 70, 32)
                pygame.draw.rect(surf, GOLD, cb, border_radius=6)
                ct = F_SMALL.render(locale.t("claim"), True, (20, 20, 20))
                surf.blit(ct, ct.get_rect(center=cb.center))
            elif claimed:
                ct = F_SMALL.render(f"✓ {locale.t('claimed')}", True, ACCENT2)
                surf.blit(ct, (wrect.right - 130, y + 12))

def draw_collection(surf, meta):
    from cards import CARDS, get_cards_by_category, get_card_level, get_card_dups_to_next, RARITY_COLORS, CATEGORIES
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    owned = meta.get('cards', {})
    packs = meta.get('unopened_packs', 0)
    draw_title(surf, f"{locale.t('cards')}  {len(owned)}/{len(CARDS)}", 25, pygame.time.get_ticks())
    if packs > 0:
        pk = F_H2.render(f"📦 {packs} {locale.t('packs')}", True, GOLD)
        surf.blit(pk, pk.get_rect(midtop=(WIDTH // 2, 70)))

    cols, cw, ch, pad = 5, 100, 120, 10
    start_y = 120
    cat_labels = {'beasts': 'cat_beasts', 'lands': 'cat_lands', 'artifacts': 'cat_artifacts',
                  'signs': 'cat_signs', 'heroes': 'cat_heroes'}
    for ci, cat in enumerate(CATEGORIES):
        cat_cards = get_cards_by_category(cat)
        if not cat_cards: continue
        label = F_SMALL.render(locale.t(cat_labels[cat]), True, ACCENT)
        surf.blit(label, (60, start_y))
        total_w = cols * cw + (cols - 1) * pad
        sx = (WIDTH - total_w) // 2
        for i, card in enumerate(cat_cards[:5]):
            x = sx + i * (cw + pad)
            y = start_y + 18
            lvl = get_card_level(meta, card['id'])
            unlocked = lvl > 0
            draw_card_icon(surf, x, y, cw, ch, card['rarity'], unlocked)
            if unlocked:
                nm = F_TINY.render(locale.t(card['name_key']), True, RARITY_COLORS[card['rarity']])
                surf.blit(nm, nm.get_rect(center=(x + cw // 2, y + 20)))
                lv = F_TINY.render(locale.t('card_level', n=lvl), True, GOLD if lvl >= 3 else MUTED)
                surf.blit(lv, lv.get_rect(center=(x + cw // 2, y + ch - 20)))
            else:
                val = meta['stats'].get(card['stat'], 0)
                prog = f"{min(val, card['threshold'])}/{card['threshold']}"
                ptxt = F_TINY.render(prog, True, (100, 100, 120))
                surf.blit(ptxt, ptxt.get_rect(center=(x + cw // 2, y + ch - 20)))
        start_y += ch + 30

    hint = F_TINY.render("ESC — назад", True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 15)))

def draw_settings(surf, music_slider, sfx_slider, ghost_toggle, shake_toggle, speed_slider, grid_toggle, back_btn):
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, locale.t("settings"), 60, pygame.time.get_ticks())
    rect = pygame.Rect(WIDTH // 2 - 250, 130, 500, 440)
    panel(surf, rect, accent=ACCENT)
    
    y = rect.y + 40
    # Музыка
    surf.blit(F_MED.render(locale.t("music"), True, TEXT), (rect.x + 40, y))
    if music_slider:
        music_slider.rect.x = rect.x + 240
        music_slider.rect.y = y + 8
        music_slider.update_handle()
        music_slider.draw(surf)
    y += 60
    
    # Звуки
    surf.blit(F_MED.render(locale.t("sfx"), True, TEXT), (rect.x + 40, y))
    if sfx_slider:
        sfx_slider.rect.x = rect.x + 240
        sfx_slider.rect.y = y + 8
        sfx_slider.update_handle()
        sfx_slider.draw(surf)
    y += 70
    
    # Призрак
    surf.blit(F_MED.render(locale.t("ghost"), True, TEXT), (rect.x + 40, y))
    if ghost_toggle:
        ghost_toggle.rect.x = rect.right - 100
        ghost_toggle.rect.y = y
        ghost_toggle.draw(surf)
    y += 60
    
    # Тряска
    surf.blit(F_MED.render(locale.t("shake"), True, TEXT), (rect.x + 40, y))
    if shake_toggle:
        shake_toggle.rect.x = rect.right - 100
        shake_toggle.rect.y = y
        shake_toggle.draw(surf)
    y += 70
    
    # Скорость
    surf.blit(F_MED.render("Скорость", True, TEXT), (rect.x + 40, y))
    if speed_slider:
        speed_slider.rect.x = rect.x + 240
        speed_slider.rect.y = y + 8
        speed_slider.update_handle()
        speed_slider.draw(surf)
    y += 60
    
    # Сетка
    surf.blit(F_MED.render("Сетка", True, TEXT), (rect.x + 40, y))
    if grid_toggle:
        grid_toggle.rect.x = rect.right - 100
        grid_toggle.rect.y = y
        grid_toggle.draw(surf)
    
    # Кнопка назад
    back_btn.rect.y = HEIGHT - 60
    back_btn.draw(surf)
def draw_hud(surf, game, sidebar_x, t, meta):
    x = sidebar_x
    y = 40
    if getattr(game, 'mode', 'classic') == 'survival':
        labels = [(locale.t("score"), str(game.score), ACCENT),
                  (locale.t("lines"), str(game.lines), GOLD),
                  ("GARBAGE", f"{int(game.garbage_timer/1000)}s", S.DANGER)]
    elif getattr(game, 'mode', 'classic') == 'sprint':
        labels = [(locale.t("time"), f"{game.elapsed_time/1000:.1f}s", ACCENT),
                  (locale.t("goal"), f"{game.lines}/40", GOLD)]
    else:
        labels = [(locale.t("score"), str(game.score), ACCENT),
                  (locale.t("level"), str(game.level), ACCENT2),
                  (locale.t("lines"), str(game.lines), GOLD)]
    for label, val, col in labels:
        l = F_SMALL.render(label, True, MUTED)
        surf.blit(l, (x, y))
        v = F_H2.render(val, True, col)
        # Обводка для цифр
        v_outline = F_H2.render(val, True, (0, 0, 0))
        surf.blit(v_outline, (x - 1, y + 18 - 1))
        surf.blit(v_outline, (x + 1, y + 18 + 1))
        surf.blit(v, (x, y + 18))
        y += 70

    player_level = meta.get('player_level', 1)
    xp = meta.get('xp', 0)
    xp_needed = meta.get('xp_needed', 100)
    rank_lab = F_SMALL.render(locale.t("rank"), True, MUTED)
    surf.blit(rank_lab, (x, y))
    rank_val = F_H2.render(str(player_level), True, ACCENT)
    surf.blit(rank_val, (x, y + 18))
    
    bar_x = x + 50
    bar_y = y + 25
    bar_w, bar_h = 140, 12
    pygame.draw.rect(surf, (40, 36, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
    fill = min(1.0, xp / xp_needed) if xp_needed else 0
    if fill > 0:
        pygame.draw.rect(surf, ACCENT, (bar_x, bar_y, int(bar_w * fill), bar_h), border_radius=6)
    xp_txt = F_TINY.render(f"{xp}/{xp_needed}", True, MUTED)
    surf.blit(xp_txt, (bar_x + bar_w + 5, bar_y - 2))
    y += 60

    # Next (3 pieces)
    nb = pygame.Rect(x, y, 200, 230)
    pygame.draw.rect(surf, (22, 20, 40), nb, border_radius=12)
    pygame.draw.rect(surf, ACCENT2, nb, 2, border_radius=12)
    lab = F_SMALL.render(locale.t("next"), True, MUTED)
    surf.blit(lab, (x + 12, y + 12))
    
    for i, piece in enumerate(game.next_queue):
        draw_piece_mini(surf, piece.shape, piece.color,
                        nb.centerx, nb.y + 60 + i * 60, cell=18)
    
    y += 245
    
    # HOLD
    hb = pygame.Rect(x, y, 200, 90)
    pygame.draw.rect(surf, (22, 20, 40), hb, border_radius=12)
    pygame.draw.rect(surf, GOLD, hb, 2, border_radius=12)
    hl = F_SMALL.render(locale.t("hold") + " (C)", True, MUTED)
    surf.blit(hl, (x + 12, y + 6))
    if game.hold:
        hc = COLORS[game.hold]
        hs = SHAPES[game.hold]
        dim = game.hold_used
        col = tuple(c // 2 for c in hc) if dim else hc
        draw_piece_mini(surf, hs, col, hb.centerx, hb.centery + 5, cell=20)

    if game.combo > 1:
        c = F_H2.render(f"COMBO x{game.combo}", True, GOLD)
        surf.blit(c, c.get_rect(midtop=(x + 100, HEIGHT - 80)))
    
    hint = F_TINY.render(locale.t("controls"), True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20)))


def draw_stats(surf, meta):
    from meta import get_achievement_points, get_global_rank, get_ap_bonus
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "STATS", 40, pygame.time.get_ticks())
    rect = pygame.Rect(WIDTH // 2 - 280, 100, 560, 480)
    panel(surf, rect, accent=ACCENT)
    stats = meta['stats']
    ap = get_achievement_points(meta)
    rank = get_global_rank(meta)
    _, ap_mult = get_ap_bonus(meta)
    lines = [
        ("Total lines", stats.get('total_lines', 0)),
        ("Best score", stats.get('best_score', 0)),
        ("Best level", stats.get('best_level', 1)),
        ("Max combo", stats.get('max_combo', 0)),
        ("Tetrises", stats.get('tetris_count', 0)),
        ("B2B count", stats.get('b2b_count', 0)),
        ("Holds used", stats.get('hold_uses', 0)),
        ("Sprint wins", stats.get('sprint_wins', 0)),
        ("Zen games", stats.get('zen_games', 0)),
        ("Longest run", f"{stats.get('longest_run', 0)}s"),
        ("Playtime", f"{int(meta.get('total_playtime', 0))}s"),
        ("Achievement Points", f"{ap}  (Rank {rank}/10)"),
        ("Score bonus", f"+{int((ap_mult - 1) * 100)}%"),
    ]
    ms = meta.get('mode_scores', {})
    for mode, score in ms.items():
        if score > 0:
            lines.append((f"Mode Best: {mode}", f"{score}"))
    for i, (label, val) in enumerate(lines):
        y = rect.y + 30 + i * 28
        l = F_SMALL.render(label, True, MUTED)
        surf.blit(l, (rect.x + 30, y))
        v = F_SMALL.render(str(val), True, TEXT)
        surf.blit(v, (rect.right - 30 - v.get_width(), y))
    hint = F_TINY.render("ESC — назад", True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 15)))


def draw_shop(surf, meta, t):
    from shop import PACK_PRICES
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "SHOP", 40, t)
    coins = meta.get('coins', 0)
    cl = F_H2.render(f"🪙 {coins}", True, GOLD)
    surf.blit(cl, cl.get_rect(midtop=(WIDTH // 2, 78)))

    items = [
        ('standard', 'STANDARD PACK', '1 random card', ACCENT),
        ('premium', 'PREMIUM PACK', 'Guaranteed Rare+', ACCENT2),
        ('legendary', 'LEGENDARY PACK', 'Legendary boosted x5', GOLD),
    ]
    y = 130
    for kind, title, desc, col in items:
        rect = pygame.Rect(WIDTH // 2 - 250, y, 500, 90)
        affordable = meta.get('coins', 0) >= PACK_PRICES[kind]
        pygame.draw.rect(surf, (22, 20, 40), rect, border_radius=12)
        pygame.draw.rect(surf, col if affordable else (80, 80, 100), rect, 2, border_radius=12)
        tt = F_H2.render(title, True, col if affordable else (120, 120, 140))
        surf.blit(tt, (rect.x + 20, rect.y + 12))
        dd = F_SMALL.render(desc, True, MUTED)
        surf.blit(dd, (rect.x + 20, rect.y + 50))
        # price
        pr = F_H2.render(f"🪙 {PACK_PRICES[kind]}", True, GOLD if affordable else (100, 100, 120))
        surf.blit(pr, (rect.right - 20 - pr.get_width(), rect.y + 32))
        y += 105

    hint = F_TINY.render("ЛКМ — купить   ESC — назад", True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 15)))


def draw_calendar(surf, meta, t):
    from meta import get_daily_calendar, LOGIN_REWARDS
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "DAILY REWARDS", 40, t)
    cal = get_daily_calendar(meta)
    cols = 7
    cw, ch, pad = 70, 100, 10
    total_w = cols * cw + (cols - 1) * pad
    sx = (WIDTH - total_w) // 2
    sy = 130
    for i, r in enumerate(cal):
        x = sx + i * (cw + pad)
        y = sy
        rect = pygame.Rect(x, y, cw, ch)
        if r['claimed']:
            bg = (30, 50, 30)
            border = (60, 200, 80)
        elif r['current']:
            bg = (50, 40, 20)
            border = GOLD
        else:
            bg = (22, 20, 40)
            border = (80, 80, 100)
        pygame.draw.rect(surf, bg, rect, border_radius=8)
        pygame.draw.rect(surf, border, rect, 2, border_radius=8)
        # day number
        dn = F_H2.render(f"D{r['day']}", True, border)
        surf.blit(dn, dn.get_rect(midtop=(x + cw // 2, y + 8)))
        # reward
        if r['coins'] > 0:
            ct = F_SMALL.render(f"🪙{r['coins']}", True, GOLD)
            surf.blit(ct, ct.get_rect(center=(x + cw // 2, y + 55)))
        if r['packs'] > 0:
            pt = F_SMALL.render(f"📦{r['packs']}", True, ACCENT2)
            surf.blit(pt, pt.get_rect(center=(x + cw // 2, y + 75)))
        if r['claimed']:
            ck = F_H2.render("✓", True, (60, 200, 80))
            surf.blit(ck, ck.get_rect(center=(x + cw // 2, y + 90)))

    # Claim button
    cur = next((r for r in cal if r['current']), None)
    if cur:
        btn = pygame.Rect(WIDTH // 2 - 120, sy + ch + 40, 240, 55)
        pygame.draw.rect(surf, GOLD, btn, border_radius=10)
        bt = F_H2.render("CLAIM TODAY", True, (20, 20, 20))
        surf.blit(bt, bt.get_rect(center=btn.center))

    hint = F_TINY.render("ESC — назад", True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 15)))


def draw_profile(surf, meta, t):
    from meta import get_player_title, get_achievement_points, get_global_rank
    import i18n as locale
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, "PROFILE", 40, t)
    # Avatar circle
    cx, cy = WIDTH // 2, 140
    pygame.draw.circle(surf, (30, 28, 55), (cx, cy), 55)
    pygame.draw.circle(surf, ACCENT, (cx, cy), 55, 3)
    # Initial letter
    init = F_TITLE.render("P", True, ACCENT)
    surf.blit(init, init.get_rect(center=(cx, cy)))

    ap = get_achievement_points(meta)
    rank = get_global_rank(meta)
    title_en, title_ru, title_col = get_player_title(meta, locale.LANG)
    tt = F_H1.render(title_ru if locale.LANG == 'ru' else title_en, True, title_col)
    surf.blit(tt, tt.get_rect(midtop=(WIDTH // 2, 205)))

    # Stats grid
    rect = pygame.Rect(WIDTH // 2 - 280, 265, 560, 300)
    panel(surf, rect, accent=ACCENT2)
    rows = [
        ("AP", f"{ap}"),
        ("Global Rank", f"{rank}/10"),
        ("Player Level", f"{meta.get('player_level', 1)}"),
        ("XP", f"{meta.get('xp', 0)}/{meta.get('xp_needed', 100)}"),
        ("Coins", f"{meta.get('coins', 0)}"),
        ("Total Lines", f"{meta.get('stats', {}).get('total_lines', 0)}"),
        ("Best Score", f"{meta.get('stats', {}).get('best_score', 0)}"),
        ("Streak", f"{meta.get('daily_streak', 0)} days"),
        ("Cards", f"{len(meta.get('cards', {}))}/20"),
        ("Sets", f"{len(meta.get('completed_sets', []))}/5"),
    ]
    for i, (label, val) in enumerate(rows):
        y = rect.y + 20 + i * 28
        l = F_SMALL.render(label, True, MUTED)
        surf.blit(l, (rect.x + 25, y))
        v = F_SMALL.render(val, True, TEXT)
        surf.blit(v, (rect.right - 25 - v.get_width(), y))

    hint = F_TINY.render("ESC — назад", True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 15)))


def draw_animated_flame(surf, x, y, t, streak):
    """Animated flame that grows with streak."""
    if streak <= 0: return
    phase = (t / 200.0) % 1.0
    base_size = min(1.0 + streak * 0.15, 2.0)
    for i, col in enumerate([(255, 100, 30), (255, 160, 60), (255, 220, 100)]):
        wobble = math.sin(t / 100.0 + i) * 3
        size = int(20 * base_size - i * 4)
        alpha = 180 - i * 40
        flame = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(flame, (*col, alpha), (size, size), size)
        surf.blit(flame, (x + wobble - size, y - size + phase * 10))


def draw_coin_hud(surf, meta, t):
    """Coins displayed in top-right corner."""
    coins = meta.get('coins', 0)
    packs = meta.get('unopened_packs', 0)
    txt = F_H2.render(f"🪙 {coins}", True, GOLD)
    surf.blit(txt, (WIDTH - txt.get_width() - 20, 15))
    if packs > 0:
        ptxt = F_SMALL.render(f"📦 {packs}", True, ACCENT2)
        surf.blit(ptxt, (WIDTH - ptxt.get_width() - 20, 45))


def draw_peek_next(surf, game, x, y, t=0):
    """Compact floating 'next piece' preview in top-right corner."""
    if not getattr(game, 'next_queue', None):
        return
    piece = game.next_queue[0]
    w, h = 74, 74

    # Pulsing border on every swap
    pulse = 0.0
    if hasattr(game, 'peek_flash_until') and t < getattr(game, 'peek_flash_until', 0):
        rem = (game.peek_flash_until - t) / 300.0
        pulse = max(0.0, min(1.0, rem))

    border_col = ACCENT2
    if pulse > 0:
        border_col = (
            int(ACCENT2[0] + (255 - ACCENT2[0]) * pulse),
            int(ACCENT2[1] + (255 - ACCENT2[1]) * pulse),
            int(ACCENT2[2] + (255 - ACCENT2[2]) * pulse),
        )

    # subtle glow behind
    if pulse > 0.05:
        glow = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
        for i in range(6, 0, -1):
            a = int(70 * pulse * (7 - i) / 6)
            pygame.draw.rect(glow, (*border_col, a),
                             (8 - i, 8 - i, w + 2*i, h + 2*i),
                             border_radius=12 + i)
        surf.blit(glow, (x - 8, y - 8))

    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, (22, 20, 40), rect, border_radius=10)
    pygame.draw.rect(surf, border_col, rect, 2, border_radius=10)

    lbl = F_TINY.render("NEXT", True, MUTED)
    surf.blit(lbl, lbl.get_rect(midtop=(rect.centerx, rect.y + 3)))

    cell = 13
    sw = len(piece.shape[0]) * cell
    sh = len(piece.shape) * cell
    ox = rect.centerx - sw // 2
    oy = rect.y + 18 + (h - 24 - sh) // 2
    for yy, row in enumerate(piece.shape):
        for xx, v in enumerate(row):
            if v:
                c = pygame.Rect(ox + xx*cell, oy + yy*cell, cell - 1, cell - 1)
                pygame.draw.rect(surf, piece.color, c, border_radius=2)
                hi = tuple(min(255, k + 50) for k in piece.color)
                pygame.draw.rect(surf, hi, c, 1, border_radius=2)
