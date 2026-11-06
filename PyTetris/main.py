import math
import sys, pygame, random
import settings as S
from game import Game
from effects import Effects, apply_bloom, FloatingText, Shockwave
from meta import (load_meta, save_meta, load_scores, save_score,
                  ACHIEVEMENTS, check_run, on_line_clear,
                  update_persistent, get_daily_quests, get_weekly_quests,
                  update_daily, check_streak, claim_quest_reward,
                  daily_progress, weekly_progress, get_ap_bonus,
                  award_run_coins, award_coins, get_streak_multiplier,
                  get_achievement_points, get_global_rank)
import ui
import audio
import i18n as locale
from graphics import BlockRenderer

try:
    import cards as C
except Exception:
    C = None
try:
    import shop as Shop
except Exception:
    Shop = None
try:
    from seasons import get_season_info
except Exception:
    def get_season_info(): return None
try:
    from meta import claim_login
except Exception:
    claim_login = lambda m: None

pygame.init()
pygame.display.set_caption("PyTetris — Neon Edition")
import os
os.environ['SDL_VIDEO_CENTERED'] = '1'  # центрируем окно на экране
screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
is_fullscreen = False
debug_overlay = False
window_scale = 1.0
das_timer = 0
das_direction = 0
DAS_DELAY = 160
DAS_REPEAT = 40
clock = pygame.time.Clock()

MENU, PLAY, PAUSE, OVER, SCORES, ACHS, DAILY, SETTINGS, COLLECTION, SHOP, CALENDAR, PROFILE, WEEKLY = range(13)
state = MENU
transition_alpha = 0
fade_speed = 15
flash_timer = 0
is_new_high = False
muted = False
is_fullscreen = True
pack_reveal = None
pack_reveal_t = 0
last_unlock = None
last_unlock_t = 0
last_card_unlock = None
last_card_t = 0
danger_pulse = 0
danger_beep_timer = 0
combo_display = 0
combo_display_t = 0
last_milestone = 0
milestone_toast = None
milestone_toast_t = 0
levelup_toast = None
levelup_toast_t = 0
focus_lost = False
time_scale = 1.0
trail_timer = 0

KONAMI_SEQ = [pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN,
              pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT,
              pygame.K_b, pygame.K_a]
konami_progress = 0

game = Game()
fx = Effects()
stars = ui.Starfield(S.WIDTH, S.HEIGHT, n=80)
meta = load_meta()
locale.LANG = meta.get('lang', 'en')
check_streak(meta)

# === Подэкраны и их навигация ===
SUBMENU_STATES = [SCORES, ACHS, DAILY, COLLECTION, SHOP, CALENDAR, PROFILE, WEEKLY]

def submenu_prev():
    idx = SUBMENU_STATES.index(state)
    set_state(SUBMENU_STATES[(idx - 1) % len(SUBMENU_STATES)])

def submenu_next():
    idx = SUBMENU_STATES.index(state)
    set_state(SUBMENU_STATES[(idx + 1) % len(SUBMENU_STATES)])

run_time = 0.0
renderer = BlockRenderer()

board_x = 30
board_y = 80
sidebar_x = board_x + S.BOARD_W + 30

menu_buttons = []
volume_slider = None
sfx_slider = None
ghost_toggle = None
shake_toggle = None
speed_slider = None
grid_toggle = None


def toggle_fullscreen():
    global is_fullscreen, screen
    is_fullscreen = not is_fullscreen
    try:
        if is_fullscreen:
            screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        else:
            screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
        # пересоздать фиксированные поверхности если были
    except Exception as e:
        print(f"⚠️ toggle_fullscreen: {e}")
        is_fullscreen = False
        try:
            screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
        except Exception:
            pass


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
    meta['lang'] = 'ru' if locale.LANG == 'en' else 'en'
    locale.LANG = meta['lang']
    save_meta(meta)
    rebuild_menu()


def quit_game():
    pygame.quit()
    sys.exit()


def rebuild_menu():
    global menu_buttons, volume_slider, sfx_slider, ghost_toggle, shake_toggle, speed_slider, grid_toggle
    menu_buttons = [
        ui.Button(locale.t("play"),    S.WIDTH // 2, 175, 240, 30, lambda: start_game(False, "classic")),
        ui.Button(locale.t("sprint"),  S.WIDTH // 2, 210, 240, 30, lambda: start_game(False, "sprint"), accent=S.GOLD),
        ui.Button(locale.t("survival"),S.WIDTH // 2, 245, 240, 30, lambda: start_game(False, "survival"), accent=S.DANGER),
        ui.Button(locale.t("zen"),     S.WIDTH // 2, 280, 240, 30, lambda: start_game(True, "classic"), accent=S.ACCENT2),
        ui.Button(locale.t("lb"),      S.WIDTH // 2, 315, 240, 30, lambda: set_state(SCORES), accent=S.GOLD),
        ui.Button(locale.t("ach"),     S.WIDTH // 2, 350, 240, 28, lambda: set_state(ACHS), accent=S.ACCENT2),
        ui.Button("👤 PROFILE",        S.WIDTH // 2, 383, 240, 26, lambda: set_state(PROFILE), accent=S.ACCENT2),
        ui.Button(locale.t("daily"),   S.WIDTH // 2, 414, 240, 26, lambda: set_state(DAILY), accent=S.ACCENT),
        ui.Button("📅 WEEKLY",          S.WIDTH // 2, 445, 240, 22, lambda: set_state(WEEKLY), accent=S.ACCENT),
        ui.Button("🎁 CALENDAR",       S.WIDTH // 2, 470, 240, 22, lambda: set_state(CALENDAR), accent=S.GOLD),
        ui.Button("🛒 SHOP",           S.WIDTH // 2, 495, 240, 22, lambda: set_state(SHOP), accent=S.GOLD),
        ui.Button("🎴 CARDS",          S.WIDTH // 2, 520, 240, 22, lambda: set_state(COLLECTION), accent=S.ACCENT2),
        ui.Button(locale.t("settings"),S.WIDTH // 2, 545, 240, 20, lambda: set_state(SETTINGS), accent=S.ACCENT),
        ui.Button(locale.t("lang"),    S.WIDTH // 2, 568, 240, 20, toggle_lang, accent=S.ACCENT2),
        ui.Button(locale.t("quit"),    S.WIDTH // 2, 591, 240, 20, quit_game, accent=S.DANGER),
    ]
    if volume_slider is None:
        volume_slider = ui.Slider(S.WIDTH // 2 - 100, 640, 200, 10, 0.4)
        sfx_slider = ui.Slider(S.WIDTH // 2 - 100, 300, 200, 10, 0.6)
        ghost_toggle = ui.Toggle(S.WIDTH // 2 + 50, 360, 60, 26, True)
        shake_toggle = ui.Toggle(S.WIDTH // 2 + 50, 420, 60, 26, True)
        speed_slider = ui.Slider(S.WIDTH // 2 - 100, 480, 200, 10, 0.5)
        grid_toggle = ui.Toggle(S.WIDTH // 2 + 50, 540, 60, 26, True)


def start_game(zen=False, mode='classic'):
    global run_time, last_milestone, combo_display, combo_display_t, milestone_toast, milestone_toast_t
    game.reset(zen=zen, mode=mode)
    run_time = 0.0
    last_milestone = 0
    combo_display = 0
    combo_display_t = 0
    milestone_toast = None
    milestone_toast_t = 0
    set_state(PLAY)


def back_to_menu():
    set_state(MENU)


# Callbacks
def cb_move():
    audio.play('move')


def cb_rotate():
    audio.play('rotate')


def cb_lock():
    audio.play('lock')
    game.peek_flash_until = pygame.time.get_ticks() + 300
    for gx, gy in game.current.cells():
        if gy >= 0:
            fx.burst(board_x + gx * S.CELL + S.CELL / 2,
                     board_y + gy * S.CELL + S.CELL / 2,
                     game.current.color, count=4)
    fx.kick(2.5)


def cb_levelup(lvl):
    global flash_timer, levelup_toast, levelup_toast_t
    levelup_toast = lvl
    levelup_toast_t = pygame.time.get_ticks()
    audio.play('levelup')
    fx.kick(12.0)
    flash_timer = 500
    for _y in range(0, S.ROWS, 2):
        colors = list(S.COLORS.values())
        fx.burst_row(board_y + _y * S.CELL, board_x, S.CELL, S.COLS, colors)
    # Fireworks from 4 corners + center
    import math
    cx, cy = S.WIDTH // 2, S.HEIGHT // 2
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        px = cx + math.cos(rad) * 200
        py = cy + math.sin(rad) * 150
        for _ in range(15):
            fx.burst(px, py, S.GOLD, count=1)
    for _ in range(20):
        fx.burst(cx, cy, S.ACCENT, count=1)


def cb_clear(rows, count):
    global last_unlock, last_unlock_t, combo_display, combo_display_t, last_milestone, milestone_toast, milestone_toast_t
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
        if count == 4:
            audio.play('combo')
            global flash_timer
            flash_timer = 250
        if game.combo > 1:
            combo_display = game.combo
            combo_display_t = pygame.time.get_ticks()
            if game.combo <= 2: audio.play('combo_low')
            elif game.combo <= 4: audio.play('combo_mid')
            else: audio.play('combo_hi')

    # Live stats
    meta['stats']['total_lines'] += count
    if count == 4:
        meta['stats']['tetris_count'] += 1
    meta['stats']['max_combo'] = max(meta['stats']['max_combo'], game.combo)
    save_meta(meta)

    # XP (with streak multiplier)
    streak_xp = get_streak_multiplier(meta)
    combo_mult = 1.0 + max(0, game.combo - 1) * 0.25  # +25% per combo step
    meta['xp'] = meta.get('xp', 0) + int(count * 10 * streak_xp * combo_mult)

    # AP bonus coins
    _, ap_mult = get_ap_bonus(meta)
    coins_earned = int(count * 3 * ap_mult * streak_xp)
    award_coins(meta, coins_earned, 'line_clear')

    # Level up player
    while meta['xp'] >= meta.get('xp_needed', 100):
        meta['xp'] -= meta['xp_needed']
        meta['player_level'] = meta.get('player_level', 1) + 1
        meta['xp_needed'] = int(meta['xp_needed'] * 1.5)
        audio.play('levelup')
        fx.kick(9.0)
        meta['unopened_packs'] = meta.get('unopened_packs', 0) + 1

    save_meta(meta)

    # Milestone check
    milestone = (game.score // 1000) * 1000
    if milestone > last_milestone and milestone > 0:
        last_milestone = milestone
        meta['coins'] = meta.get('coins', 0) + 100
        save_meta(meta)
        global milestone_toast, milestone_toast_t
        milestone_toast = milestone
        milestone_toast_t = pygame.time.get_ticks()
        audio.play('milestone')

    # Perfect clear bonus
    if game.perfect_clear:
        game.perfect_clear = False
        meta['stats']['perfect_clears'] = meta.get('perfect_clears', 0) if 'perfect_clears' in meta.get('stats', {}) else 0
        meta['stats']['perfect_clears'] = meta['stats'].get('perfect_clears', 0) + 1
        meta['coins'] = meta.get('coins', 0) + 500
        meta['unopened_packs'] = meta.get('unopened_packs', 0) + 1
        save_meta(meta)
        audio.play('pc')
        fx.kick(15.0)
        for _ in range(20):
            fx.burst(S.WIDTH // 2 + random.randint(-200, 200),
                     S.HEIGHT // 2 + random.randint(-100, 100),
                     S.GOLD, count=10)
        fx.texts.append(FloatingText(board_x + S.BOARD_W / 2, board_y + 200,
                                     "PERFECT CLEAR!", S.GOLD, life=120))

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
    ui.Button(locale.t("menu"),   S.WIDTH // 2, S.HEIGHT // 2 + 110, 240, 54, lambda: set_state(MENU), accent=S.ACCENT2),
]
over_buttons = [
    ui.Button(locale.t("restart"), S.WIDTH // 2, S.HEIGHT // 2 + 90, 240, 60, lambda: start_game(False, game.mode)),
    ui.Button(locale.t("menu"),    S.WIDTH // 2, S.HEIGHT // 2 + 170, 240, 60, back_to_menu, accent=S.ACCENT2),
]

# === Навигационные кнопки для всех подэкранов ===
nav_buttons = [
    ui.Button("НАЗАД",  S.WIDTH // 2 - 280, S.HEIGHT - 50, 200, 48,
              submenu_prev, accent=S.ACCENT, icon='left'),
    ui.Button("В МЕНЮ", S.WIDTH // 2,       S.HEIGHT - 50, 200, 48,
              lambda: set_state(MENU), accent=S.ACCENT2, icon='home'),
    ui.Button("ДАЛЕЕ",  S.WIDTH // 2 + 280, S.HEIGHT - 50, 200, 48,
              submenu_next, accent=S.GOLD, icon='right'),
]


rebuild_menu()


def _handle_quest_click(mx, my):
    rect_x = S.WIDTH // 2 - 320
    for i, q in enumerate(get_daily_quests()):
        bx, by = rect_x + 640 - 90, 100 + 45 + i * 70 + 5
        if bx <= mx <= bx + 70 and by <= my <= by + 32:
            if claim_quest_reward(meta, q['type'], 'daily'):
                audio.play('levelup')
                return
    for i, q in enumerate(get_weekly_quests()):
        bx, by = rect_x + 640 - 90, 430 + 45 + i * 70 + 5
        if bx <= mx <= bx + 70 and by <= my <= by + 32:
            if claim_quest_reward(meta, q['type'], 'weekly'):
                audio.play('levelup')
                return


def handle_events():
    global state, muted, konami_progress, pack_reveal, pack_reveal_t, focus_lost
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if e.type == pygame.WINDOWFOCUSLOST and state == PLAY:
            set_state(PAUSE)
            print('⏸ Авто-пауза (потеря фокуса)')
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_F4:
                global window_scale, screen
                window_scale = 0.75 if window_scale == 1.0 else 1.0
                try:
                    w2, h2 = int(S.WIDTH * window_scale), int(S.HEIGHT * window_scale)
                    screen = pygame.display.set_mode((w2, h2))
                except Exception:
                    pass
            elif e.key == pygame.K_F3:
                global debug_overlay
                debug_overlay = not debug_overlay
            elif e.key == pygame.K_F11:
                toggle_fullscreen()
            elif e.key == pygame.K_F5:
                from meta import export_save
                print(f"✅ Сохранено: {export_save(meta)}")
                audio.play('levelup')
            elif e.key == pygame.K_F9:
                from meta import import_save
                try:
                    meta.update(import_save())
                    print("✅ Загружено")
                    audio.play('levelup')
                except Exception as ex:
                    print(f"⚠️ {ex}")
            elif e.key == pygame.K_m:
                muted = not muted
                audio.toggle_mute(muted)
            else:
                if konami_progress < len(KONAMI_SEQ) and e.key == KONAMI_SEQ[konami_progress]:
                    konami_progress += 1
                    if konami_progress == len(KONAMI_SEQ):
                        konami_progress = 0
                        meta['unopened_packs'] = meta.get('unopened_packs', 0) + 5
                        meta['coins'] = meta.get('coins', 0) + 1000
                        save_meta(meta)
                        audio.play('set_complete') if 'set_complete' in dir(audio) else audio.play('levelup')
                        print("🎉 KONAMI CODE!")
                else:
                    konami_progress = 0

        if state == MENU:
            for b in menu_buttons: b.handle(e)
            if volume_slider: volume_slider.handle_event(e)
        elif state == PLAY:
            global das_timer, das_direction
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_p): set_state(PAUSE)
                elif e.key == pygame.K_LEFT:
                    game.move(-1)
                    das_direction = -1
                    das_timer = 0
                elif e.key == pygame.K_RIGHT:
                    game.move(1)
                    das_direction = 1
                    das_timer = 0
                elif e.key == pygame.K_DOWN:  game.soft_drop()
                elif e.key == pygame.K_UP:    game.rotate(1)
                elif e.key == pygame.K_z:     game.rotate(-1)
                elif e.key == pygame.K_SPACE:
                    old_y = game.current.y
                    height = game.ghost_y() - old_y
                    game.hard_drop()
                    fx.kick(min(10.0, 3.0 + height * 0.5))
                    for gx, gy in game.current.cells():
                        if gy >= 0:
                            fx.burst(board_x + gx * S.CELL + S.CELL/2,
                                     board_y + old_y * S.CELL, (255, 255, 255), count=3)
                elif e.key == pygame.K_c:
                    if game.hold_piece(): audio.play('rotate')
            elif e.type == pygame.KEYUP:
                if e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    das_direction = 0
        elif state == PAUSE:
            for b in pause_buttons: b.handle(e)
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_p): set_state(PLAY)
                elif e.key == pygame.K_q: set_state(MENU)
        elif state == OVER:
            for b in over_buttons: b.handle(e)
        elif state == SHOP:
            for b in nav_buttons: b.handle(e)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                set_state(MENU)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and Shop:
                mx, my = e.pos
                for i, kind in enumerate(['standard', 'premium', 'legendary']):
                    yr = 130 + i * 105
                    if S.WIDTH // 2 - 250 <= mx <= S.WIDTH // 2 + 250 and yr <= my <= yr + 90:
                        if Shop.buy_pack(meta, kind):
                            audio.play('pack_open')
                            fx.kick(6.0)
                        break
        elif state == CALENDAR:
            for b in nav_buttons: b.handle(e)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                set_state(MENU)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                bx, by = S.WIDTH // 2 - 120, 270
                if bx <= e.pos[0] <= bx + 240 and by <= e.pos[1] <= by + 55:
                    if claim_login(meta):
                        audio.play('levelup')
                        fx.kick(6.0)
        elif state == PROFILE:
            for b in nav_buttons: b.handle(e)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                set_state(MENU)
        elif state == SETTINGS:
            settings_back.handle(e)
            if sfx_slider: sfx_slider.handle_event(e)
            if ghost_toggle: ghost_toggle.handle_event(e)
            if shake_toggle: shake_toggle.handle_event(e)
            if speed_slider: speed_slider.handle_event(e)
            if grid_toggle: grid_toggle.handle_event(e)
        elif state in (SCORES, ACHS, DAILY, COLLECTION, WEEKLY):
            for b in nav_buttons: b.handle(e)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                set_state(MENU)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                set_state(MENU)
            if state == COLLECTION and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and C:
                res = C.open_pack(meta)
                if res:
                    pack_reveal = res
                    pack_reveal_t = pygame.time.get_ticks()
                    audio.play('pack_open')
                    fx.kick(6.0)
            if state == DAILY and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                _handle_quest_click(e.pos[0], e.pos[1])


def draw_crt_effect(surf):
    lines = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
    for y in range(0, S.HEIGHT, 4):
        pygame.draw.line(lines, (0, 0, 0, 30), (0, y), (S.WIDTH, y), 2)
    surf.blit(lines, (0, 0))


def draw_danger_zone(surf, t):
    filled = sum(1 for row in game.grid if any(cell is not None for cell in row))
    if filled < 14:
        return
    pulse = abs((t % 800) - 400) / 400.0
    alpha = int(80 + 100 * pulse)
    col = (255, 40, 40, alpha)
    overlay = pygame.Surface((S.BOARD_W, S.CELL * 3), pygame.SRCALPHA)
    overlay.fill(col)
    surf.blit(overlay, (board_x, board_y))


def draw_playfield(surf, t):
    ui.draw_playfield_frame(surf, board_x, board_y, t)
    if getattr(game, 'show_grid', True):
        ui.draw_grid_bg(surf, board_x, board_y, t)
    draw_danger_zone(surf, t)
    for y in range(S.ROWS):
        for x in range(S.COLS):
            col = game.grid[y][x]
            if col:
                if y in game.clearing:
                    alpha = min(255, max(0, int((game.clear_timer / 220.0) * 255)))
                    flash = pygame.Surface((S.CELL, S.CELL), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, alpha))
                    surf.blit(flash, (board_x + x*S.CELL, board_y + y*S.CELL))
                else:
                    kind = next((k for k, v in S.COLORS.items() if v == col), "I")
                    renderer.draw_block(surf, board_x + x*S.CELL, board_y + y*S.CELL, kind)
    if not game.game_over and not game.clearing and game.show_ghost:
        gy = game.ghost_y()
        p = game.current
        for xx, yy in p.cells():
            dy = gy - p.y
            ui.draw_cell(surf, board_x + xx*S.CELL, board_y + (yy+dy)*S.CELL, p.color, ghost=True)
        for xx, yy in p.cells():
            if yy >= 0:
                renderer.draw_block(surf, board_x + xx*S.CELL, board_y + yy*S.CELL, p.kind)


def draw_combo_hud(surf, t):
    if combo_display >= 2 and t - combo_display_t < 2000:
        elapsed = t - combo_display_t
        alpha = max(0, 255 - int(elapsed / 2000 * 255))
        scale = 1.0 + min(0.5, elapsed / 400.0)
        size = int(40 * scale)
        try:
            font = ui.F_TITLE if size > 50 else ui.F_H1
            txt = font.render(f"COMBO x{combo_display}", True, S.GOLD)
            txt.set_alpha(alpha)
            surf.blit(txt, txt.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 2 - 100)))
        except Exception:
            pass


def draw_game(t, dt):
    screen.fill(S.BG)
    stars.draw(screen)
    stars.update(dt, 0.3)
    ox, oy = fx.offset()
    if ox or oy:
        tmp = pygame.Surface((S.WIDTH, S.HEIGHT))
        tmp.fill(S.BG)
        draw_playfield(tmp, t)
        ui.draw_hud(tmp, game, sidebar_x, t, meta)
        fx.draw(tmp, font=ui.F_H2)
        screen.fill(S.BG)
        screen.blit(tmp, (ox, oy))
    else:
        draw_playfield(screen, t)
        ui.draw_hud(screen, game, sidebar_x, t, meta)
        fx.draw(screen, font=ui.F_H2)
    draw_combo_hud(screen, t)
    ui.draw_coin_hud(screen, meta, t)
    # Floating next-piece peek (top-right corner)
    ui.draw_peek_next(screen, game, S.WIDTH - 88, 75, t)
    if muted:
        m = ui.F_SMALL.render("MUTED", True, S.DANGER)
        screen.blit(m, (S.WIDTH - 70, 10))
    if flash_timer > 0:
        fl = pygame.Surface((S.WIDTH, S.HEIGHT))
        fl.fill((255, 255, 255))
        fl.set_alpha(int(180 * (flash_timer / 500.0)))
        screen.blit(fl, (0, 0))
    apply_bloom(screen)
    draw_crt_effect(screen)


def handle_game_over():
    global is_new_high, last_unlock, last_unlock_t, last_card_unlock, last_card_t
    is_new_high = game.score > meta.get('best_score', 0)
    if is_new_high:
        for _ in range(10):
            fx.burst(S.WIDTH//2 + random.randint(-150, 150), S.HEIGHT//2 - 100, S.GOLD, count=15)
    save_score(game.score)
    award_run_coins(meta, game.score, game.lines)
    new_medals, new_cards = check_run(meta, game, run_time)
    if new_medals:
        last_unlock = new_medals[0]
        last_unlock_t = pygame.time.get_ticks()
        audio.play('levelup')
    if new_cards:
        last_card_unlock = new_cards[0]
        last_card_t = pygame.time.get_ticks()
    set_state(OVER)


def draw_over():
    screen.fill(S.BG)
    draw_playfield(screen, pygame.time.get_ticks())
    ui.draw_overlay(screen, 200)
    if getattr(game, 'win', False):
        ui.draw_text_center(screen, locale.t("win"), S.HEIGHT // 2 - 120, ui.F_TITLE, S.GOLD)
    else:
        ui.draw_text_center(screen, locale.t("game_over"), S.HEIGHT // 2 - 120, ui.F_TITLE, S.DANGER)
    if is_new_high:
        h = ui.F_H1.render(locale.t("new_high"), True, S.GOLD)
        screen.blit(h, h.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 2 - 200)))
    ui.draw_text_center(screen,
                        f"{locale.t('score')}: {game.score}   {locale.t('lines')}: {game.lines}   {locale.t('level')}: {game.level}",
                        S.HEIGHT // 2 - 30, ui.F_H2, S.TEXT)
    for b in over_buttons: b.draw(screen)


def draw_pack_reveal(surf, t):
    global pack_reveal
    if not pack_reveal: return
    elapsed = t - pack_reveal_t
    duration = 1800
    if elapsed > duration:
        pack_reveal = None
        return
    frac = min(1.0, elapsed / duration)
    overlay = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(180 * (1 - abs(frac - 0.5) * 2))))
    surf.blit(overlay, (0, 0))
    if 'card_id' not in pack_reveal: return
    if not C: return
    card = C.get_card_by_id(pack_reveal['card_id'])
    if not card: return
    cx, cy = S.WIDTH // 2, S.HEIGHT // 2
    base_w, base_h = 200, 280

    # Flip animation: first 40% = flip in (scale_x 0 -> 1), then show
    if frac < 0.4:
        flip = frac / 0.4
        scale_x = flip
        scale_y = 1.0
        reveal = False
    else:
        flip = (frac - 0.4) / 0.6
        # slight bounce
        bounce = 1.0 + 0.05 * math.sin(flip * math.pi * 2)
        scale_x = bounce
        scale_y = bounce
        reveal = True

    w, h = int(base_w * scale_x), int(base_h * scale_y)
    if w < 4: w = 4
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    col = C.RARITY_COLORS[card['rarity']]

    # Card back (while flipping)
    if not reveal:
        pygame.draw.rect(surf, (30, 28, 55), rect, border_radius=10)
        pygame.draw.rect(surf, col, rect, 3, border_radius=10)
        q = ui.F_TITLE.render("?", True, col)
        if w > 60:
            surf.blit(q, q.get_rect(center=rect.center))
        return

    # Foil prismatic border
    if pack_reveal.get('foil'):
        for i in range(6):
            c = [(255,100,100),(255,200,100),(200,255,100),(100,255,200),(100,200,255),(200,100,255)][i]
            pygame.draw.rect(surf, c, rect.inflate(2*i, 2*i), 2, border_radius=10)
    pygame.draw.rect(surf, (20, 18, 35), rect, border_radius=10)
    pygame.draw.rect(surf, col, rect, 3, border_radius=10)
    if w > 100:
        name = ui.F_H1.render(locale.t(card['name_key']), True, col)
        surf.blit(name, name.get_rect(center=(cx, cy)))
        if pack_reveal.get('duplicate'):
            dup = ui.F_MED.render(f"+1 dup (Lv.{pack_reveal.get('new_level', 1)})", True, S.MUTED)
            surf.blit(dup, dup.get_rect(center=(cx, cy + 50)))


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

    if volume_slider:
        base_vol = volume_slider.val
        if state == PLAY and not game.game_over:
            # music swells with level (up to +30%)
            boost = min(0.3, (game.level - 1) * 0.05)
            pygame.mixer.music.set_volume(min(1.0, base_vol * (1.0 + boost)))
        else:
            pygame.mixer.music.set_volume(base_vol)
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
        if game.game_over or game.win:
            handle_game_over()
        else:
            # Slow-motion during line clear
            if game.clearing:
                time_scale = 0.3
            else:
                target = 1.0
                time_scale += (target - time_scale) * min(1.0, dt / 80.0)
            game.update(dt * time_scale)
            # Trail particles behind falling piece
            trail_timer += dt
            if trail_timer > 60 and not game.game_over and not game.clearing:
                trail_timer = 0
                for gx, gy in game.current.cells():
                    if gy >= 0:
                        fx.burst(board_x + gx * S.CELL + S.CELL/2,
                                 board_y + gy * S.CELL + S.CELL/2,
                                 game.current.color, count=1)
            run_time += dt / 1000.0
            update_daily(meta, lines=0, score=game.score, dt=dt / 1000.0)
        draw_game(t, dt)
        fx.update(dt)
        # Danger beep when stack is high
        filled = sum(1 for row in game.grid if any(c is not None for c in row))
        if filled >= 15 and not game.game_over:
            danger_beep_timer += dt
            if danger_beep_timer > 700:
                danger_beep_timer = 0
                audio.play('danger')
        else:
            danger_beep_timer = 0
    elif state == PAUSE:
        draw_game(t, dt)
        ui.draw_pause(screen)
        # Show focus hint if window is unfocused
        try:
            if not pygame.display.get_active():
                hint = ui.F_SMALL.render('(Окно не в фокусе)', True, S.MUTED)
                screen.blit(hint, hint.get_rect(center=(S.WIDTH // 2, S.HEIGHT - 100)))
        except Exception:
            pass
        for b in pause_buttons: b.update(dt, mouse)
        for b in pause_buttons: b.draw(screen)
    elif state == OVER:
        for b in over_buttons: b.update(dt, mouse)
        draw_over()
        fx.update(dt)
    elif state == SCORES:
        ui.draw_leaderboard(screen, load_scores(), meta.get('best_score', 0))
    elif state == ACHS:
        ui.draw_achievements(screen, meta, ACHIEVEMENTS)
    elif state == DAILY:
        ui.draw_dailies(screen, meta, get_daily_quests(), get_weekly_quests())
    elif state == WEEKLY:
        ui.draw_weekly(screen, meta, get_weekly_quests())
    elif state == SETTINGS:
        settings_back.update(dt, mouse)
        for obj in (sfx_slider, ghost_toggle, shake_toggle, speed_slider, grid_toggle):
            if obj and hasattr(obj, 'update'): obj.update(dt)
        ui.draw_settings(screen, volume_slider, sfx_slider, ghost_toggle, shake_toggle,
                        speed_slider, grid_toggle, settings_back)
    elif state == COLLECTION:
        ui.draw_collection(screen, meta)
    elif state == SHOP:
        ui.draw_shop(screen, meta, t)
    elif state == CALENDAR:
        ui.draw_calendar(screen, meta, t)
    elif state == PROFILE:
        ui.draw_profile(screen, meta, t)

    if last_unlock and t - last_unlock_t < 2500:
        ui.draw_big_achievement_popup(screen, last_unlock, meta, t - last_unlock_t)
    elif last_unlock:
        last_unlock = None

    if last_card_unlock and t - last_card_t < 3000:
        fade = max(0.0, 1.0 - (t - last_card_t) / 3000.0)
        if C:
            card = C.get_card_by_id(last_card_unlock)
            if card:
                toast = ui.F_H2.render(f"🃏 {locale.t(card['name_key'])}", True, C.RARITY_COLORS[card['rarity']])
                toast.set_alpha(int(255 * fade))
                screen.blit(toast, toast.get_rect(midtop=(S.WIDTH // 2, 50)))
    elif last_card_unlock:
        last_card_unlock = None

    if levelup_toast and t - levelup_toast_t < 2200:
        elapsed = t - levelup_toast_t
        fade = max(0.0, 1.0 - elapsed / 2200.0)
        # Slide-in from top
        slide = min(1.0, elapsed / 400.0)
        y_pos = int(-100 + slide * 120)
        scale = 1.0 + min(0.4, elapsed / 500.0)
        size = int(80 * scale)
        try:
            font = pygame.font.SysFont('Arial', size, bold=True)
            shadow = font.render("LEVEL UP!", True, (0, 0, 0))
            txt = font.render("LEVEL UP!", True, S.GOLD)
            shadow.set_alpha(int(255 * fade))
            txt.set_alpha(int(255 * fade))
            surf = screen
            surf.blit(shadow, shadow.get_rect(center=(S.WIDTH // 2 + 4, y_pos + 4)))
            surf.blit(txt, txt.get_rect(center=(S.WIDTH // 2, y_pos)))
            # Level number
            lv = ui.F_TITLE.render(f"→ {levelup_toast}", True, S.ACCENT)
            lv.set_alpha(int(255 * fade))
            surf.blit(lv, lv.get_rect(center=(S.WIDTH // 2, y_pos + 70)))
        except Exception:
            pass
    elif levelup_toast:
        levelup_toast = None

    if milestone_toast and t - milestone_toast_t < 2000:
        fade = max(0.0, 1.0 - (t - milestone_toast_t) / 2000.0)
        elapsed = t - milestone_toast_t
        scale = 1.0 + min(0.3, elapsed / 800.0)
        size = int(60 * scale)
        font = ui.F_TITLE if size > 60 else ui.F_H1
        txt = font.render(f"🎉 {milestone_toast}", True, S.GOLD)
        txt.set_alpha(int(255 * fade))
        screen.blit(txt, txt.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 3)))
    elif milestone_toast:
        milestone_toast = None

    # Отрисовка кнопок навигации на всех подэкранах
    if state in SUBMENU_STATES:
        for b in nav_buttons:
            b.update(dt, mouse)
            b.draw(screen)

    draw_pack_reveal(screen, t)

    if transition_alpha > 0:
        fs = pygame.Surface((S.WIDTH, S.HEIGHT))
        fs.fill((0, 0, 0))
        fs.set_alpha(transition_alpha)
        screen.blit(fs, (0, 0))

    if combo_display >= 2 and t - combo_display_t < 1500:
        elapsed = t - combo_display_t
        alpha = max(0, 255 - int(elapsed / 1500 * 255))
        scale = 1.0 + min(0.6, elapsed / 300.0)
        size = int(48 * scale)
        try:
            font = pygame.font.SysFont('Arial', size, bold=True)
            txt = font.render(f"COMBO x{combo_display}", True, S.GOLD)
            txt.set_alpha(alpha)
            screen.blit(txt, txt.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 2 - 100)))
        except Exception:
            pass

    if debug_overlay:
        fps = clock.get_fps()
        dbg = ui.F_TINY.render(f"FPS: {fps:.0f}  t={t}  state={state}", True, (0, 255, 0))
        screen.blit(dbg, (5, 5))

    pygame.display.flip()

pygame.quit()
sys.exit()
