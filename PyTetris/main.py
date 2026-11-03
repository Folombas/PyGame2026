import sys, pygame, random
import settings as S
from game import Game
from effects import Effects, apply_bloom, FloatingText, Shockwave
from meta import (load_meta, save_meta, load_scores, save_score,
                  ACHIEVEMENTS, check_run, on_line_clear,
                  update_persistent, get_daily_quests, get_weekly_quests,
                  update_daily, check_streak, claim_quest_reward,
                  daily_progress, weekly_progress)
import ui
import audio
import i18n as locale
from graphics import BlockRenderer

pygame.init()
pygame.display.set_caption("PyTetris — Neon Edition")
screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
clock = pygame.time.Clock()

# Состояния
MENU, PLAY, PAUSE, OVER, SCORES, ACHS, DAILY, SETTINGS, COLLECTION, SHOP, CALENDAR, PROFILE = range(12)
state = MENU
transition_alpha = 0
fade_speed = 15
flash_timer = 0
is_new_high = False
muted = False
is_fullscreen = False
KONAMI_SEQ = [pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_b, pygame.K_a]
konami_progress = 0

game = Game()
fx = Effects()
stars = ui.Starfield(S.WIDTH, S.HEIGHT, n=80)
meta = load_meta()
locale.LANG = meta.get('lang', 'en')
_streak_updated = check_streak(meta)
run_time = 0.0
last_unlock = None
last_unlock_t = 0
last_card_unlock = None
last_card_t = 0
pack_reveal = None
pack_reveal_t = 0
pack_reveal_duration = 1200
renderer = BlockRenderer()

# Координаты
board_x = 30
board_y = 80
sidebar_x = board_x + S.BOARD_W + 30

# UI
menu_buttons = []
volume_slider = None
sfx_slider = None
ghost_toggle = None
shake_toggle = None
speed_slider = None
grid_toggle = None


def _handle_quest_click(mx, my):
    from meta import claim_quest_reward, get_daily_quests, get_weekly_quests
    # Daily block: rect (WIDTH//2 - 320, 100, 640, 260); buttons at rect.right - 90, y + 5
    rect_x = S.WIDTH // 2 - 320
    rect_y = 100
    for i, q in enumerate(get_daily_quests()):
        bx = rect_x + 640 - 90
        by = rect_y + 45 + i * 70 + 5
        if bx <= mx <= bx + 70 and by <= my <= by + 32:
            res = claim_quest_reward(meta, q['type'], 'daily')
            if res:
                audio.play('levelup')
                return
    # Weekly block: rect (WIDTH//2 - 320, 375, 640, 210)
    wrex_y = 430
    for i, q in enumerate(get_weekly_quests()):
        bx = rect_x + 640 - 90
        by = wrex_y + 45 + i * 70 + 5
        if bx <= mx <= bx + 70 and by <= my <= by + 32:
            res = claim_quest_reward(meta, q['type'], 'weekly')
            if res:
                audio.play('levelup')
                return



def draw_pack_reveal(surf, t):
    global pack_reveal, pack_reveal_t
    if not pack_reveal: return
    elapsed = t - pack_reveal_t
    if elapsed > pack_reveal_duration:
        pack_reveal = None
        return
    from cards import get_card_by_id, RARITY_COLORS
    if 'levelup' in pack_reveal:
        # Level up celebration
        frac = elapsed / pack_reveal_duration
        overlay = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * (1 - abs(frac - 0.5) * 2))))
        surf.blit(overlay, (0, 0))
        scale = 1.0 + 0.2 * (1 - frac)
        txt = ui.F_TITLE.render(f"LEVEL UP! {pack_reveal['levelup']}", True, S.GOLD)
        sw, sh = int(txt.get_width() * scale), int(txt.get_height() * scale)
        txt = pygame.transform.smoothscale(txt, (sw, sh))
        surf.blit(txt, txt.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 2)))
        sub = ui.F_H2.render("+1 pack", True, S.ACCENT)
        surf.blit(sub, sub.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 2 + 80)))
        return
    frac = elapsed / pack_reveal_duration
    card = get_card_by_id(pack_reveal['card_id'])
    if not card: return
    # Overlay
    overlay = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(180 * (1 - abs(frac - 0.5) * 2))))
    surf.blit(overlay, (0, 0))
    # Scale from 0 to 1.2 to 1.0
    if frac < 0.3:
        scale = frac / 0.3 * 1.2
    elif frac < 0.5:
        scale = 1.2 - (frac - 0.3) / 0.2 * 0.2
    else:
        scale = 1.0
    w, h = int(240 * scale), int(320 * scale)
    cx, cy = S.WIDTH // 2, S.HEIGHT // 2
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    col = RARITY_COLORS[card['rarity']]
    if pack_reveal.get('foil'):
        # prismatic border
        for i in range(6):
            c = [(255, 100, 100), (255, 200, 100), (200, 255, 100),
                 (100, 255, 200), (100, 200, 255), (200, 100, 255)][i]
            pygame.draw.rect(surf, c, rect.inflate(2*i, 2*i), 2, border_radius=10)
    pygame.draw.rect(surf, (20, 18, 35), rect, border_radius=10)
    pygame.draw.rect(surf, col, rect, 3, border_radius=10)
    if pack_reveal.get('foil'):
        txt = ui.F_H2.render("✨ FOIL ✨", True, (255, 255, 200))
        surf.blit(txt, txt.get_rect(center=(cx, rect.y - 25)))
    name = ui.F_H1.render(locale.t(card['name_key']), True, col)
    surf.blit(name, name.get_rect(center=(cx, cy)))
    if pack_reveal.get('duplicate'):
        dup = ui.F_MED.render(f"+1 duplicate (Lv.{pack_reveal.get('new_level', 1)})", True, S.MUTED)
        surf.blit(dup, dup.get_rect(center=(cx, cy + 50)))
    if pack_reveal.get('new_sets'):
        for i, sname in enumerate(pack_reveal['new_sets']):
            st = ui.F_H2.render(f"🏆 SET COMPLETE: {sname.upper()}!", True, S.GOLD)
            surf.blit(st, st.get_rect(center=(cx, rect.bottom + 40 + i * 30)))

def draw_crt_effect(surf):
    lines = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
    for y in range(0, S.HEIGHT, 4):
        pygame.draw.line(lines, (0, 0, 0, 40), (0, y), (S.WIDTH, y), 2)
    surf.blit(lines, (0, 0))

def toggle_fullscreen():
    global is_fullscreen, screen
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    else:
        screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))

def set_state(s):
    global state, transition_alpha
    state = s
    audio.play('menu')
    if s in (PLAY, PAUSE):
        audio.play_music()
    else:
        audio.stop_music()
    transition_alpha = 255

def toggle_lang():
    global meta
    meta['lang'] = 'ru' if locale.LANG == 'en' else 'en'
    locale.LANG = meta['lang']
    save_meta(meta)
    rebuild_menu()

def rebuild_menu():
    global menu_buttons, volume_slider, sfx_slider, ghost_toggle, shake_toggle, speed_slider, grid_toggle
    menu_buttons = [
        ui.Button(locale.t("play"),    S.WIDTH // 2, 180, 240, 36, lambda: start_game(False, "classic")),
        ui.Button(locale.t("sprint"),  S.WIDTH // 2, 225, 240, 36, lambda: start_game(False, "sprint"), accent=S.GOLD),
        ui.Button(locale.t("survival"),S.WIDTH // 2, 270, 240, 36, lambda: start_game(False, "survival"), accent=S.DANGER),
        ui.Button(locale.t("zen"),     S.WIDTH // 2, 315, 240, 36, lambda: start_game(True, "classic"), accent=S.ACCENT2),
        ui.Button(locale.t("lb"),      S.WIDTH // 2, 360, 240, 36, lambda: set_state(SCORES), accent=S.GOLD),
        ui.Button(locale.t("ach"),     S.WIDTH // 2, 405, 240, 30, lambda: set_state(ACHS), accent=S.ACCENT2),
        ui.Button("👤 PROFILE",       S.WIDTH // 2, 440, 240, 26, lambda: set_state(PROFILE), accent=S.ACCENT2),
        ui.Button(locale.t("daily"),   S.WIDTH // 2, 470, 240, 26, lambda: set_state(DAILY), accent=S.ACCENT),
        ui.Button("🎁 CALENDAR",       S.WIDTH // 2, 500, 240, 26, lambda: set_state(CALENDAR), accent=S.GOLD),
        ui.Button("🛒 SHOP",         S.WIDTH // 2, 530, 240, 26, lambda: set_state(SHOP), accent=S.GOLD),
        ui.Button(locale.t("settings"),S.WIDTH // 2, 560, 240, 24, lambda: set_state(SETTINGS), accent=S.ACCENT),
        ui.Button(locale.t("lang"),    S.WIDTH // 2, 588, 240, 24, toggle_lang, accent=S.ACCENT2),
        ui.Button(locale.t("quit"),    S.WIDTH // 2, 616, 240, 24, quit_game, accent=S.DANGER),
    ]
    if volume_slider is None:
        volume_slider = ui.Slider(S.WIDTH // 2 - 100, 640, 200, 10, 0.4)
        sfx_slider = ui.Slider(S.WIDTH // 2 - 100, 300, 200, 10, 0.6)
        ghost_toggle = ui.Toggle(S.WIDTH // 2 + 50, 360, 60, 26, True)
        shake_toggle = ui.Toggle(S.WIDTH // 2 + 50, 420, 60, 26, True)
        speed_slider = ui.Slider(S.WIDTH // 2 - 100, 480, 200, 10, 0.5)
        grid_toggle = ui.Toggle(S.WIDTH // 2 + 50, 540, 60, 26, True)

def start_game(zen=False, mode='classic'):
    global run_time
    game.reset(zen=zen, mode=mode)
    run_time = 0.0
    set_state(PLAY)

def back_to_menu():
    set_state(MENU)

def quit_game():
    pygame.quit()
    sys.exit()

# --- КОЛЛБЕКИ ИГРЫ ---
def cb_move():    audio.play('move')
def cb_rotate():  audio.play('rotate')

def cb_lock():
    audio.play('lock')
    for gx, gy in game.current.cells():
        if gy >= 0:
            fx.burst(board_x + gx * S.CELL + S.CELL / 2, 
                     board_y + gy * S.CELL + S.CELL / 2, 
                     game.current.color, count=6)
    fx.kick(3.0)
    if getattr(game.current, 'powerup', None):
        global flash_timer
        flash_timer = 150
        audio.play('powerup')

def cb_levelup(lvl):
    global flash_timer
    audio.play('levelup')
    fx.kick(9.0)
    flash_timer = 500
    for _y in range(0, S.ROWS, 2):
        colors = list(S.COLORS.values())
        fx.burst_row(board_y + _y * S.CELL, board_x, S.CELL, S.COLS, colors)

def cb_clear(rows, count):
    audio.play('tetris' if count == 4 else 'clear')
    for y in rows:
        colors = list(S.COLORS.values())
        fx.burst_row(board_y + y * S.CELL, board_x, S.CELL, S.COLS, colors)
    fx.kick(6.0 if count < 4 else 12.0)
    
    if rows:
        cy = board_y + (sum(rows) / len(rows)) * S.CELL + S.CELL / 2
        fx.waves.append(Shockwave(board_x + S.BOARD_W / 2, cy, S.ACCENT, max_radius=150, life=30))
        txt = "TETRIS!" if count == 4 else f"+{count * 100}"
        col = S.GOLD if count == 4 else S.TEXT
        fx.texts.append(FloatingText(board_x + S.BOARD_W / 2, cy, txt, col, life=60))
        if count == 4: audio.play('combo')
        if game.combo > 1:
            txt = f"COMBO x{game.combo}"
            fx.texts.append(FloatingText(board_x + S.BOARD_W / 2, cy - 40, txt, S.ACCENT2, life=80))
    
    global meta, last_unlock, last_unlock_t
    # AP bonus
    from meta import get_ap_bonus
    _, ap_mult = get_ap_bonus(meta)
    if ap_mult > 1.0:
        game.score += int(count * 100 * game.level * (ap_mult - 1.0))
    from meta import award_coins
    award_coins(meta, count * 3, 'line_clear')
    meta['stats']['total_lines'] += count
    if count == 4:
        meta['stats']['tetris_count'] += 1
    meta['stats']['max_combo'] = max(meta['stats']['max_combo'], game.combo)
    save_meta(meta)
    from meta import get_streak_multiplier as _gsm
    streak_xp_mult = _gsm(meta)
    meta['xp'] = meta.get('xp', 0) + int(count * 10 * streak_xp_mult)
    while meta['xp'] >= meta.get('xp_needed', 100):
        meta['xp'] -= meta['xp_needed']
        meta['player_level'] = meta.get('player_level', 1) + 1
        meta['xp_needed'] = int(meta['xp_needed'] * 1.5)
        audio.play('levelup')
        fx.kick(9.0)
    old_level = meta.get('player_level', 1)
    # ... xp logic above
    save_meta(meta)
    if meta.get('player_level', 1) > old_level:
        # Level up celebration
        global pack_reveal, pack_reveal_t
        import cards as C
        meta['unopened_packs'] = meta.get('unopened_packs', 0) + 1
        save_meta(meta)
        audio.play('levelup')
        fx.kick(12.0)
        # Use pack_reveal as celebration overlay
        pack_reveal = {'card_id': None, 'levelup': meta['player_level']}
        pack_reveal_t = pygame.time.get_ticks()

    res = on_line_clear(meta, count)
    if res:
        last_unlock = res
        last_unlock_t = pygame.time.get_ticks()

def cb_gameover():
    audio.play('gameover')

def cb_win():
    audio.play('levelup')

game.on_move = cb_move
game.on_rotate = cb_rotate
game.on_lock = cb_lock
game.on_clear = cb_clear
game.on_levelup = cb_levelup
game.on_gameover = cb_gameover
game.on_win = cb_win

settings_back = ui.Button(locale.t("back"), S.WIDTH // 2, S.HEIGHT - 60, 200, 45, lambda: set_state(MENU))

pause_buttons = [
    ui.Button(locale.t("resume"), S.WIDTH // 2, S.HEIGHT // 2 + 40, 240, 54, lambda: set_state(PLAY)),
    ui.Button(locale.t("menu"),   S.WIDTH // 2, S.HEIGHT // 2 + 110, 240, 54, lambda: set_state(MENU), accent=S.ACCENT2)
]

over_buttons = [
    ui.Button(locale.t("restart"), S.WIDTH // 2, S.HEIGHT // 2 + 90, 240, 60, lambda: start_game(False, game.mode)),
    ui.Button(locale.t("menu"),    S.WIDTH // 2, S.HEIGHT // 2 + 170, 240, 60, back_to_menu, accent=S.ACCENT2),
]

rebuild_menu()

# --- ОБРАБОТКА СОБЫТИЙ ---
def handle_events():
    global state, muted
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
            toggle_fullscreen()
        global konami_progress
        if e.type == pygame.KEYDOWN:
            if e.key == KONAMI_SEQ[konami_progress]:
                konami_progress += 1
                if konami_progress == len(KONAMI_SEQ):
                    konami_progress = 0
                    meta['unopened_packs'] = meta.get('unopened_packs', 0) + 5
                    meta['coins'] = meta.get('coins', 0) + 1000
                    save_meta(meta)
                    audio.play('set_complete')
                    print("🎉 KONAMI CODE! +5 паков, +1000 монет")
            else:
                konami_progress = 0
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F5:
            from meta import export_save
            fname = export_save(meta)
            print(f'✅ Сохранено в {fname}')
            audio.play('levelup')
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F9:
            from meta import import_save
            try:
                data = import_save()
                meta.update(data)
                print('✅ Загружено')
                audio.play('levelup')
            except Exception as ex:
                print(f'⚠️ {ex}')
        if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
            muted = not muted
            audio.toggle_mute(muted)

        if state == MENU:
            for b in menu_buttons: b.handle(e)
            if volume_slider: volume_slider.handle_event(e)
        elif state == PLAY:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE or e.key == pygame.K_p: set_state(PAUSE)
                elif e.key == pygame.K_LEFT:  game.move(-1)
                elif e.key == pygame.K_RIGHT: game.move(1)
                elif e.key == pygame.K_DOWN:  game.soft_drop()
                elif e.key == pygame.K_UP:    game.rotate(1)
                elif e.key == pygame.K_z:     game.rotate(-1)
                elif e.key == pygame.K_SPACE:
                    old_y = game.current.y
                    game.hard_drop()
                    for gx, gy in game.current.cells():
                        if gy >= 0:
                            fx.burst(board_x + gx * S.CELL + S.CELL/2, board_y + old_y * S.CELL, (255, 255, 255), count=3)
                elif e.key == pygame.K_c:
                    if game.hold_piece(): audio.play('rotate')
        elif state == PAUSE:
            for b in pause_buttons: b.handle(e)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE or e.key == pygame.K_p: set_state(PLAY)
                elif e.key == pygame.K_q: set_state(MENU)
        elif state == OVER:
            for b in over_buttons: b.handle(e)
        elif state == SHOP:
            ui.draw_shop(screen, meta, t)
    elif state == CALENDAR:
        ui.draw_calendar(screen, meta, t)
    elif state == PROFILE:
        ui.draw_profile(screen, meta, t)
    elif state == SETTINGS:
            settings_back.handle(e)
            if sfx_slider: sfx_slider.handle_event(e)
            if ghost_toggle: ghost_toggle.handle_event(e)
            if shake_toggle: shake_toggle.handle_event(e)
            if speed_slider: speed_slider.handle_event(e)
            if grid_toggle: grid_toggle.handle_event(e)
        elif state in (SCORES, ACHS, DAILY, COLLECTION, PROFILE):
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                set_state(MENU)
            if state == COLLECTION and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                import cards as C
                global pack_reveal, pack_reveal_t
                res = C.open_pack(meta)
                if res:
                    pack_reveal = res
                    pack_reveal_t = pygame.time.get_ticks()
                    audio.play('pack_open')
                    fx.kick(6.0)
                    if res.get('foil'): audio.play('foil_chime')
                    if res.get('new_sets'): audio.play('set_complete')
            if state == DAILY and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                # Проверяем клики по Claim-кнопкам
                _handle_quest_click(mx, my)

# --- ОТРИСОВКА ---
def draw_playfield_target(surf):
    ui.draw_playfield_frame(surf, board_x, board_y)
    if getattr(game, 'show_grid', True):
        ui.draw_grid_bg(surf, board_x, board_y, pygame.time.get_ticks())
    for y in range(S.ROWS):
        for x in range(S.COLS):
            col = game.grid[y][x]
            if col:
                flash = y in game.clearing
                if flash:
                    flash_surf = pygame.Surface((S.CELL, S.CELL), pygame.SRCALPHA)
                    alpha = min(255, max(0, int((game.clear_timer / 220.0) * 255)))
                    flash_surf.fill((255, 255, 255, alpha))
                    surf.blit(flash_surf, (board_x + x*S.CELL, board_y + y*S.CELL))
                else:
                    kind = next((k for k, v in S.COLORS.items() if v == col), "I")
                    renderer.draw_block(surf, board_x + x*S.CELL, board_y + y*S.CELL, kind)
                    if (x, y) in game.powerup_grid:
                        ptype = game.powerup_grid[(x, y)]
                        icon = {"bomb": "B", "freeze": "F", "clear": "C"}[ptype]
                        itxt = ui.F_TINY.render(icon, True, (255, 255, 255))
                        surf.blit(itxt, (board_x + x*S.CELL + 8, board_y + y*S.CELL + 8))
                        
    if not game.game_over and not game.clearing and game.show_ghost:
        gy = game.ghost_y()
        p = game.current
        for xx, yy in p.cells():
            dy = gy - p.y
            ui.draw_cell(surf, board_x + xx*S.CELL, board_y + (yy+dy)*S.CELL,
                         p.color, ghost=True)
        for xx, yy in p.cells():
            if yy >= 0:
                renderer.draw_block(surf, board_x + xx*S.CELL, board_y + yy*S.CELL, p.kind)

def draw_game(t, dt):
    screen.fill(S.BG)
    ox, oy = fx.offset()
    if ox or oy:
        tmp = pygame.Surface((S.WIDTH, S.HEIGHT))
        tmp.fill(S.BG)
        draw_playfield_target(tmp)
        ui.draw_hud(tmp, game, sidebar_x, t, meta)
        fx.draw(tmp, font=ui.F_H2)
        screen.fill(S.BG)
        screen.blit(tmp, (ox, oy))
    else:
        draw_playfield_target(screen)
        ui.draw_hud(screen, game, sidebar_x, t, meta)
        fx.draw(screen, font=ui.F_H2)
        
    if muted:
        m = ui.F_SMALL.render("MUTED", True, S.DANGER)
        screen.blit(m, (S.WIDTH - 70, 10))
        
    if flash_timer > 0:
        fl = pygame.Surface((S.WIDTH, S.HEIGHT))
        fl.fill((255, 255, 255))
        fl.set_alpha(int(200 * (flash_timer / 500.0)))
        screen.blit(fl, (0, 0))
    
    apply_bloom(screen)
    draw_crt_effect(screen)

def handle_game_over():
    global meta, state, last_unlock, last_unlock_t, is_new_high
    is_new_high = game.score > meta.get('best_score', 0)
    if is_new_high:
        for _ in range(10):
            fx.burst(S.WIDTH//2 + random.randint(-150, 150), S.HEIGHT//2 - 100, S.GOLD, count=15)
    save_score(game.score)
    global last_card_unlock, last_card_t
    new_medals, new_cards = check_run(meta, game, run_time)
    if new_medals:
        last_unlock = new_medals[0]
        last_unlock_t = pygame.time.get_ticks()
        audio.play('medal_shine')
        fx.kick(8.0)
    if new_cards:
        last_card_unlock = new_cards[0]
        last_card_t = pygame.time.get_ticks()
        audio.play('powerup')
    set_state(OVER)

def draw_over():
    screen.fill(S.BG)
    draw_playfield_target(screen)
    ui.draw_overlay(screen, 200)
    
    shadow = ui.F_TITLE.render(locale.t("game_over"), True, (0,0,0))
    screen.blit(shadow, shadow.get_rect(center=(S.WIDTH // 2 + 4, S.HEIGHT // 2 - 120 + 4)))
    
    if getattr(game, 'win', False):
        ui.draw_text_center(screen, locale.t("win"), S.HEIGHT // 2 - 120, ui.F_TITLE, S.GOLD)
    else:
        ui.draw_text_center(screen, locale.t("game_over"), S.HEIGHT // 2 - 120, ui.F_TITLE, S.DANGER)
        
    if is_new_high:
        h = ui.F_H1.render(locale.t("new_high"), True, S.GOLD)
        screen.blit(h, h.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 2 - 200)))
        
    ui.draw_text_center(screen, f"{locale.t('score')}: {game.score}   {locale.t('lines')}: {game.lines}   {locale.t('level')}: {game.level}",
                        S.HEIGHT // 2 - 30, ui.F_H2, S.TEXT)
    for b in over_buttons: b.draw(screen)

# --- ГЛАВНЫЙ ЦИКЛ ---
running = True
while running:
    dt = clock.tick(S.FPS)
    t = pygame.time.get_ticks()
    mouse = pygame.mouse.get_pos()

    handle_events()

    if transition_alpha > 0:
        transition_alpha = max(0, transition_alpha - fade_speed)
    if flash_timer > 0:
        flash_timer -= dt

    if volume_slider: pygame.mixer.music.set_volume(volume_slider.val)
    if sfx_slider: audio.set_sfx_volume(sfx_slider.val)
    if shake_toggle: fx.enable_shake = shake_toggle.state
    if ghost_toggle: game.show_ghost = ghost_toggle.state
    if speed_slider: game.fall_speed_mult = max(0.1, speed_slider.val * 2.0)
    if grid_toggle: game.show_grid = grid_toggle.state

    if state == MENU:
        for b in menu_buttons: b.update(dt, mouse)
        ui.draw_menu(screen, menu_buttons, t, stars, meta)
        if volume_slider: volume_slider.draw(screen)
        stars.update(dt)
        apply_bloom(screen)
    elif state == PLAY:
        if game.game_over:
            handle_game_over()
        elif game.win:
            handle_game_over()
        else:
            game.update(dt)
            run_time += dt / 1000.0
            update_daily(meta, lines=0, score=game.score, dt=dt / 1000.0)
        draw_game(t, dt)
        fx.update(dt)
    elif state == PAUSE:
        draw_game(t, dt)
        ui.draw_pause(screen)
        for b in pause_buttons: b.update(dt, mouse)
        for b in pause_buttons: b.draw(screen)
        fx.update(dt)
    elif state == OVER:
        for b in over_buttons: b.update(dt, mouse)
        draw_over()
        fx.update(dt)
    elif state == COLLECTION:
        ui.draw_collection(screen, meta)
    elif state == SCORES:
        ui.draw_leaderboard(screen, load_scores(), meta.get('best_score', 0))
    elif state == ACHS:
        ui.draw_achievements(screen, meta, ACHIEVEMENTS)
    elif state == DAILY:
        ui.draw_dailies(screen, meta, get_daily_quests(), get_weekly_quests())
    elif state == SHOP:
        ui.draw_shop(screen, meta, t)
    elif state == CALENDAR:
        ui.draw_calendar(screen, meta, t)
    elif state == PROFILE:
        ui.draw_profile(screen, meta, t)
    elif state == SETTINGS:
        settings_back.update(dt, mouse)
        for obj in (sfx_slider, ghost_toggle, shake_toggle, speed_slider, grid_toggle):
            if obj and hasattr(obj, 'update'): obj.update(dt)
        ui.draw_settings(screen, volume_slider, sfx_slider, ghost_toggle, shake_toggle, speed_slider, grid_toggle, settings_back)

    if last_unlock and t - last_unlock_t < 3000:
        elapsed = t - last_unlock_t
        fade = max(0.0, 1.0 - elapsed / 3000.0)
        # slide-in effect
        slide = min(1.0, elapsed / 300.0)
        y_pos = int(20 + (1 - slide) * -100)
        name = next((a['name_key'] for a in ACHIEVEMENTS if a['id'] == last_unlock), last_unlock)
        tier = meta['medals'].get(last_unlock, 1)
        # background box
        box_w, box_h = 500, 70
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((20, 18, 40, int(220 * fade)))
        pygame.draw.rect(box, ui.MEDAL_COLORS[tier] or S.GOLD, (0, 0, box_w, box_h), 2, border_radius=8)
        screen.blit(box, (S.WIDTH // 2 - box_w // 2, y_pos))
        # text
        toast = ui.F_H2.render(f"★ {locale.t(name)}", True, ui.MEDAL_COLORS[tier] or S.GOLD)
        toast.set_alpha(int(255 * fade))
        screen.blit(toast, toast.get_rect(center=(S.WIDTH // 2, y_pos + box_h // 2)))
    elif last_unlock:
        last_unlock = None

    if last_card_unlock and t - last_card_t < 3000:
        from cards import get_card_by_id, RARITY_COLORS
        card = get_card_by_id(last_card_unlock)
        if card:
            fade = max(0.0, 1.0 - (t - last_card_t) / 3000.0)
            rarity_col = RARITY_COLORS[card['rarity']]
            toast = ui.F_H2.render(f"★ {locale.t(card['name_key'])}", True, rarity_col)
            toast.set_alpha(int(255 * fade))
            screen.blit(toast, toast.get_rect(midtop=(S.WIDTH // 2, 50)))
    elif last_card_unlock:
        last_card_unlock = None

    draw_pack_reveal(screen, t)

    if transition_alpha > 0:
        fs = pygame.Surface((S.WIDTH, S.HEIGHT))
        fs.fill((0, 0, 0))
        fs.set_alpha(transition_alpha)
        screen.blit(fs, (0, 0))

    pygame.display.flip()

pygame.quit()
sys.exit()
