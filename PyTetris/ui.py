import settings as S
from cards import RARITY_COLORS
import math
import math, random
import pygame
from settings import *
import math
import i18n as locale

pygame.font.init()
def _font(size, bold=False):
    import os
    import settings as S
    # Try Roboto first, then Russo_One, then SysFont
    candidates = [
        S.FONT_BOLD if bold else S.FONT_REGULAR,
        "assets/Russo_One.ttf",
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            font = pygame.font.Font(path, size)
            # Validate by rendering test char
            _test = font.render("A", True, (255, 255, 255))
            if _test.get_width() > 0:
                return font
        except Exception:
            continue
    # SysFont fallback
    for name in ('Roboto', 'Inter', 'DejaVu Sans', 'Arial'):
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


def vertical_gradient(surf, top, bottom):
    h = surf.get_height()
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (surf.get_width(), y))


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

def draw_playfield_frame(surf, board_x, board_y, t=0):
    pygame.draw.rect(surf, (40, 36, 70),
                     (board_x - 4, board_y - 4, BOARD_W + 8, BOARD_H + 8),
                     border_radius=10)
    # Animated gradient border — pulses between cyan and pink
    phase = (t % 3000) / 3000.0
    if phase < 0.5:
        k = phase / 0.5
        col = (int(ACCENT[0] * (1-k) + ACCENT2[0] * k),
               int(ACCENT[1] * (1-k) + ACCENT2[1] * k),
               int(ACCENT[2] * (1-k) + ACCENT2[2] * k))
    else:
        k = (phase - 0.5) / 0.5
        col = (int(ACCENT2[0] * (1-k) + ACCENT[0] * k),
               int(ACCENT2[1] * (1-k) + ACCENT[1] * k),
               int(ACCENT2[2] * (1-k) + ACCENT[2] * k))
    pygame.draw.rect(surf, col,
                     (board_x - 4, board_y - 4, BOARD_W + 8, BOARD_H + 8),
                     2, border_radius=10)
    # Corner highlights
    for cx, cy in [(board_x - 4, board_y - 4),
                    (board_x + BOARD_W + 4, board_y - 4),
                    (board_x - 4, board_y + BOARD_H + 4),
                    (board_x + BOARD_W + 4, board_y + BOARD_H + 4)]:
        pygame.draw.circle(surf, col, (cx, cy), 4)

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
    # Размытие + затемнение
    try:
        blurred = pygame.transform.gaussian_blur(surf, 6)
        surf.blit(blurred, (0, 0))
    except Exception:
        pass
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    draw_text_center(surf, "PAUSED", HEIGHT // 2 - 40, F_TITLE, ACCENT)
    hint = F_SMALL.render("ESC — продолжить   |   Q — в меню", True, MUTED)
    surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

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
    dlabel = F_H2.render(locale.t("daily"), True, ACCENT)
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
        wc_lbl = F_SMALL.render(locale.t("wildcard"), True, GOLD)
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
        wlabel = F_H2.render(locale.t("weekly"), True, ACCENT2)
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
    draw_title(surf, f"{locale.t('collection_title')}  {len(owned)}/{len(CARDS)}", 25, pygame.time.get_ticks())
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
    """Компактный HUD — только самое нужное."""
    x = sidebar_x
    y = 30

    # SCORE — большой
    l = F_TINY.render(locale.t("score"), True, MUTED)
    surf.blit(l, (x, y))
    v = F_H1.render(str(game.score), True, ACCENT)
    surf.blit(v, (x, y + 14))
    y += 14 + 55

    # LEVEL + LINES в строку
    ll = F_TINY.render(locale.t("level"), True, MUTED)
    surf.blit(ll, (x, y))
    lv = F_TINY.render(locale.t("lines"), True, MUTED)
    surf.blit(lv, (x + 80, y))
    v1 = F_H2.render(str(game.level), True, ACCENT2)
    surf.blit(v1, (x, y + 14))
    v2 = F_H2.render(str(game.lines), True, GOLD)
    surf.blit(v2, (x + 80, y + 14))
    y += 14 + 42 + 10

    # NEXT
    nb = pygame.Rect(x, y, 200, 90)
    pygame.draw.rect(surf, (22, 20, 40), nb, border_radius=10)
    pygame.draw.rect(surf, ACCENT2, nb, 2, border_radius=10)
    lab = F_TINY.render(locale.t("next"), True, MUTED)
    surf.blit(lab, (nb.x + 8, nb.y + 6))
    if hasattr(game, 'next_queue') and game.next_queue:
        p = game.next_queue[0]
        draw_piece_mini(surf, p.shape, p.color, nb.centerx, nb.centery + 12, cell=16)
    y += 90 + 10

    # HOLD
    hb = pygame.Rect(x, y, 200, 80)
    pygame.draw.rect(surf, (22, 20, 40), hb, border_radius=10)
    pygame.draw.rect(surf, GOLD, hb, 2, border_radius=10)
    lab = F_TINY.render(locale.t("hold") + " (C)", True, MUTED)
    surf.blit(lab, (hb.x + 8, hb.y + 6))
    if game.hold:
        hc = COLORS[game.hold]
        hs = SHAPES[game.hold]
        dim = game.hold_used
        col = tuple(c // 2 for c in hc) if dim else hc
        draw_piece_mini(surf, hs, col, hb.centerx, hb.centery + 10, cell=16)
    y += 80 + 12

    # Streak + Coins (компактно в одну строку)
    bits = []
    streak = meta.get('daily_streak', 0) if meta else 0
    coins = meta.get('coins', 0) if meta else 0
    if streak > 0: bits.append(f"🔥{streak}d")
    if coins > 0: bits.append(f"🪙{coins}")
    if bits:
        info = F_TINY.render("  ".join(bits), True, GOLD)
        surf.blit(info, (x, y))
        y += 18

    # COMBO внизу
    if game.combo > 1:
        c = F_H2.render(f"COMBO x{game.combo}", True, GOLD)
        surf.blit(c, c.get_rect(midtop=(x + 100, HEIGHT - 80)))

    # Controls hint
    hint = F_TINY.render(locale.t("controls"), True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 8)))

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


def draw_shop(surf, meta, t):
    from shop import PACK_PRICES
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, locale.t("shop_title"), 40, t)
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
    draw_title(surf, locale.t("calendar_title"), 40, t)
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
            bg, border = (30, 50, 30), (60, 200, 80)
        elif r['current']:
            bg, border = (50, 40, 20), GOLD
        else:
            bg, border = (22, 20, 40), (80, 80, 100)
        pygame.draw.rect(surf, bg, rect, border_radius=8)
        pygame.draw.rect(surf, border, rect, 2, border_radius=8)
        dn = F_H2.render(f"Д{r['day']}", True, border)
        surf.blit(dn, dn.get_rect(midtop=(x + cw // 2, y + 8)))
        if r['coins'] > 0:
            ct = F_SMALL.render(f"🪙{r['coins']}", True, GOLD)
            surf.blit(ct, ct.get_rect(center=(x + cw // 2, y + 55)))
        if r['packs'] > 0:
            pt = F_SMALL.render(f"📦{r['packs']}", True, ACCENT2)
            surf.blit(pt, pt.get_rect(center=(x + cw // 2, y + 75)))
        if r['claimed']:
            ck = F_H2.render("✓", True, (60, 200, 80))
            surf.blit(ck, ck.get_rect(center=(x + cw // 2, y + 90)))

    # Кнопка CLAIM — точная позиция совпадает с hitbox в main.py
    cur = next((r for r in cal if r['current']), None)
    if cur:
        btn = pygame.Rect(WIDTH // 2 - 120, 270, 240, 55)
        pygame.draw.rect(surf, GOLD, btn, border_radius=10)
        pygame.draw.rect(surf, (255, 255, 200), btn, 2, border_radius=10)
        bt = F_H2.render("ЗАБРАТЬ", True, (20, 20, 20))
        surf.blit(bt, bt.get_rect(center=btn.center))

def draw_profile(surf, meta, t):
    from meta import get_player_title, get_achievement_points, get_global_rank
    import i18n as locale
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_title(surf, locale.t("profile_title"), 40, t)
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


def draw_weekly(surf, meta, weeklies):
    from meta import weekly_progress
    vertical_gradient(surf, (18, 12, 40), (6, 4, 16))
    draw_section_title(surf, locale.t("weekly_quests_title"), "🔥", 60, ACCENT2)
    rect = pygame.Rect(WIDTH // 2 - 320, 130, 640, 420)
    panel(surf, rect, accent=ACCENT2)
    wp = weekly_progress(meta)
    for i, q in enumerate(weeklies):
        y = rect.y + 40 + i * 130
        cur = wp.get(q['type'], 0)
        tgt = q['target']
        done = cur >= tgt
        claimed = q['id'] in wp.get('done', [])

        # Иконка слева
        icon_color = GOLD if done else ACCENT2
        pygame.draw.circle(surf, icon_color, (rect.x + 50, y + 35), 22, 2)
        icon_text = '✓' if done else '!'
        it = F_H2.render(icon_text, True, icon_color)
        surf.blit(it, it.get_rect(center=(rect.x + 50, y + 35)))

        desc = F_MED.render(q['desc'], True, TEXT)
        surf.blit(desc, (rect.x + 90, y))

        # Прогресс-бар
        bar = pygame.Rect(rect.x + 90, y + 35, 400, 16)
        draw_progress_bar(surf, bar.x, bar.y, bar.w, bar.h,
                         (cur / tgt) if tgt else 0,
                         GOLD if done else ACCENT2)
        stat = F_SMALL.render(f"{int(cur)}/{tgt}", True, GOLD if done else MUTED)
        surf.blit(stat, (bar.right + 15, bar.y - 2))

        # Награды
        rew = F_SMALL.render(f"+{q['reward_xp']} XP  +{q['reward_packs']} 📦", True, GOLD)
        surf.blit(rew, (rect.x + 90, y + 60))

        # Claim
        if done and not claimed:
            cb = pygame.Rect(rect.right - 130, y + 20, 110, 40)
            pygame.draw.rect(surf, GOLD, cb, border_radius=8)
            ct = F_SMALL.render("ЗАБРАТЬ", True, (20, 20, 20))
            surf.blit(ct, ct.get_rect(center=cb.center))
        elif claimed:
            ct = F_SMALL.render("✓ ПОЛУЧЕНО", True, ACCENT)
            surf.blit(ct, (rect.right - 160, y + 30))

def draw_big_achievement_popup(surf, ach_id, meta, elapsed, duration=2500):
    """Draw centered achievement popup with medal icon."""
    if elapsed > duration:
        return
    fade = max(0.0, 1.0 - elapsed / duration)
    scale_in = min(1.0, elapsed / 250.0)
    # overlay
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, int(120 * fade)))
    surf.blit(ov, (0, 0))
    # panel
    pw, ph = 480, 180
    px = WIDTH // 2 - pw // 2
    py = HEIGHT // 2 - ph // 2
    panel_rect = pygame.Rect(px, py, pw, ph)
    pygame.draw.rect(surf, (22, 20, 40), panel_rect, border_radius=16)
    # tier color border
    tier = meta.get('medals', {}).get(ach_id, 1)
    border = MEDAL_COLORS[tier] if tier < len(MEDAL_COLORS) else GOLD
    pygame.draw.rect(surf, border, panel_rect, 3, border_radius=16)
    # medal icon big
    draw_medal(surf, px + 20, py + 20, 60, tier)
    # title
    title = F_H2.render("🏆 ACHIEVEMENT!", True, border)
    surf.blit(title, (px + 100, py + 20))
    # name
    from meta import ACHIEVEMENTS
    name_key = next((a['name_key'] for a in ACHIEVEMENTS if a['id'] == ach_id), ach_id)
    nm = F_H1.render(locale.t(name_key), True, TEXT)
    surf.blit(nm, (px + 100, py + 60))
    # tier label
    tier_names = ["", "Bronze", "Silver", "Gold", "Platinum", "Mythic"]
    lbl = F_MED.render(f"Tier: {tier_names[tier] if tier < len(tier_names) else 'Unknown'}", True, border)
    surf.blit(lbl, (px + 100, py + 120))
    # hint
    hint = F_TINY.render("Click to dismiss", True, MUTED)
    surf.blit(hint, hint.get_rect(midbottom=(WIDTH // 2, py + ph - 12)))


def draw_minimap(surf, game, x, y, w=10, h=200):
    """Вертикальная полоска: заполненность по столбцам."""
    pygame.draw.rect(surf, (30, 28, 50), (x, y, w, h), border_radius=4)
    if not game.grid:
        return
    for col in range(10):
        filled = sum(1 for row in range(20) if game.grid[row][col] is not None)
        ratio = filled / 20.0
        bh = int(h * ratio)
        if bh > 0:
            color = ACCENT
            if ratio > 0.7: color = GOLD
            if ratio > 0.9: color = DANGER
            pygame.draw.rect(surf, color, (x, y + h - bh, w, bh), border_radius=4)


def draw_tooltip(surf, text, mouse_x, mouse_y):
    """Плавающий тултип над курсором."""
    if not text:
        return
    font = F_TINY
    txt_surf = font.render(text, True, (240, 240, 255))
    pad = 6
    w = txt_surf.get_width() + pad * 2
    h = txt_surf.get_height() + pad * 2
    tx = mouse_x + 15
    ty = mouse_y + 15
    if tx + w > WIDTH: tx = mouse_x - w - 10
    if ty + h > HEIGHT: ty = mouse_y - h - 10
    pygame.draw.rect(surf, (15, 13, 25), (tx, ty, w, h), border_radius=6)
    pygame.draw.rect(surf, ACCENT, (tx, ty, w, h), 1, border_radius=6)
    surf.blit(txt_surf, (tx + pad, ty + pad))


def draw_section_title(surf, text, icon_char, y, color=ACCENT):
    """Красивый заголовок с иконкой слева."""
    # Большой заголовок
    title = F_H1.render(text, True, color)
    icon = F_H1.render(icon_char, True, color)
    total_w = icon.get_width() + 15 + title.get_width()
    x0 = WIDTH // 2 - total_w // 2
    surf.blit(icon, (x0, y - title.get_height() // 2))
    surf.blit(title, (x0 + icon.get_width() + 15, y - title.get_height() // 2))
    # Декоративные линии по бокам
    line_y = y + title.get_height() // 2 + 8
    pygame.draw.line(surf, color, (WIDTH // 2 - 220, line_y), (WIDTH // 2 - total_w // 2 - 20, line_y), 1)
    pygame.draw.line(surf, color, (WIDTH // 2 + total_w // 2 + 20, line_y), (WIDTH // 2 + 220, line_y), 1)


def draw_living_grid(surf, board_x, board_y, t=0, game=None):
    """ЖИВАЯ СЕТКА — неоновая мембрана с волнами и пульсом под бит."""
    import math
    level = getattr(game, 'level', 1) if game else 1
    
    # Сдвиг оттенка с уровнем (всего 10 уровней → постепенный сдвиг в тёплый)
    hue_offset = (level - 1) * 4
    
    # Пульс под "бит" 128 BPM (468мс на удар)
    beat_phase = (t % 468) / 468.0
    pulse = max(0, 1.0 - beat_phase * 3)
    
    # Базовый цвет + пульс
    r = 26 + hue_offset + pulse * 35
    g = 22 + pulse * 25
    b = 44 + pulse * 60
    col = (int(max(0, min(255, r))), int(max(0, min(255, g))), int(max(0, min(255, b))))
    
    # Амплитуда волны
    amp = 1.2 + pulse * 1.8
    
    # Вертикальные линии с волной
    for x in range(COLS + 1):
        px = board_x + x * CELL
        w_top = math.sin(t / 800 + x * 0.35) * amp
        w_bot = math.sin(t / 800 + x * 0.35 + 2.0) * amp
        pygame.draw.line(surf, col,
                        (px + w_top, board_y),
                        (px + w_bot, board_y + BOARD_H), 1)
    
    # Горизонтальные линии с волной
    for y in range(ROWS + 1):
        py = board_y + y * CELL
        w_l = math.cos(t / 800 + y * 0.35) * amp
        w_r = math.cos(t / 800 + y * 0.35 + 2.0) * amp
        pygame.draw.line(surf, col,
                        (board_x + w_l, py),
                        (board_x + BOARD_W + w_r, py), 1)
    



def draw_clear_rays(surf, board_x, board_y, rows, t=0):
    """Волны от очищенных линий — расходятся в обе стороны."""
    import math
    for row in rows:
        cy = board_y + row * CELL + CELL // 2
        # Горизонтальная волна от центра
        phase = (t / 300.0) % 1.0
        for offset in range(0, BOARD_W // 2, 8):
            alpha = int(180 * (1 - phase))
            if alpha <= 0:
                continue
            # Левая волна
            x_l = board_x + BOARD_W // 2 - offset - int(phase * 100)
            if board_x <= x_l:
                ray = pygame.Surface((6, 3), pygame.SRCALPHA)
                ray.fill((255, 255, 200, alpha))
                surf.blit(ray, (x_l, cy - 1))
            # Правая волна
            x_r = board_x + BOARD_W // 2 + offset + int(phase * 100)
            if x_r <= board_x + BOARD_W:
                ray = pygame.Surface((6, 3), pygame.SRCALPHA)
                ray.fill((255, 255, 200, alpha))
                surf.blit(ray, (x_r, cy - 1))
