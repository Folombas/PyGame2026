import sys, pygame
import settings as S
from game import Game
from effects import Effects
from meta import (load_meta, save_meta, load_scores, save_score,
                  ACHIEVEMENTS, check_run, on_line_clear,
                  update_persistent, get_daily_quests, update_daily)
import ui
import audio
from graphics import BlockRenderer
import easypygamewidgets as epw

pygame.init()
pygame.display.set_caption("PyTetris — Neon Edition")
screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
epw.link_pygame_window(screen)
clock = pygame.time.Clock()

# Состояния
MENU, PLAY, PAUSE, OVER, SCORES, ACHS, DAILY = range(7)
state = MENU
transition_alpha = 0
fade_speed = 15
flash_timer = 0
is_new_high = False
muted = False

game = Game()
fx = Effects()
stars = ui.Starfield(S.WIDTH, S.HEIGHT, n=80)
meta = load_meta()
run_time = 0.0
last_unlock = None
last_unlock_t = 0

renderer = BlockRenderer()

# Координаты
board_x = 20
board_y = 20
sidebar_x = board_x + S.BOARD_W + 30

def set_state(s):
    global state, transition_alpha
    state = s
    audio.play('menu')
    if s in (PLAY, PAUSE):
        audio.play_music()
    else:
        audio.stop_music()
    transition_alpha = 255

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

def cb_levelup(lvl):
    global flash_timer
    audio.play('levelup')
    fx.kick(9.0)
    flash_timer = 300
    for _y in range(0, S.ROWS, 4):
        colors = list(S.COLORS.values())
        fx.burst_row(board_y + _y * S.CELL, board_x, S.CELL, S.COLS, colors)

def cb_clear(rows, count):
    audio.play('tetris' if count == 4 else 'clear')
    for y in rows:
        colors = list(S.COLORS.values())
        fx.burst_row(board_y + y * S.CELL, board_x, S.CELL, S.COLS, colors)
    fx.kick(6.0 if count < 4 else 12.0)
    global meta, last_unlock, last_unlock_t
    res = on_line_clear(meta, count)
    if res:
        last_unlock = res
        last_unlock_t = pygame.time.get_ticks()

def cb_gameover():
    audio.play('gameover')

game.on_move = cb_move
game.on_rotate = cb_rotate
game.on_lock = cb_lock
game.on_clear = cb_clear
game.on_levelup = cb_levelup
game.on_gameover = cb_gameover

# --- КНОПКИ ---
def start_game(zen=False):
    global run_time
    game.reset(zen=zen)
    run_time = 0.0
    set_state(PLAY)

def back_to_menu():
    set_state(MENU)

def quit_game():
    pygame.quit()
    sys.exit()

# Современные кнопки
volume_slider = epw.Slider(text="Volume", start=0, end=100, width=250)
volume_slider.place(S.WIDTH // 2 - 125, 680)
epw_buttons = []
btn_data = [
    ("PLAY", lambda: start_game(False), 270),
    ("ZEN MODE", lambda: start_game(True), 340),
    ("LEADERBOARD", lambda: set_state(SCORES), 410),
    ("ACHIEVEMENTS", lambda: set_state(ACHS), 480),
    ("DAILY QUESTS", lambda: set_state(DAILY), 550),
    ("QUIT", quit_game, 620),
]
for text, cb, y_pos in btn_data:
    b = epw.Button(text=text)
    b.place(S.WIDTH // 2 - 140, y_pos)
    b.command = cb
    epw_buttons.append(b)

pause_buttons = [
    ui.Button("RESUME", S.WIDTH // 2, S.HEIGHT // 2 + 40, 240, 54, lambda: set_state(PLAY)),
    ui.Button("MENU",   S.WIDTH // 2, S.HEIGHT // 2 + 110, 240, 54, lambda: set_state(MENU), accent=S.ACCENT2)
]

over_buttons = [
    ui.Button("RESTART", S.WIDTH // 2, S.HEIGHT // 2 + 90, 240, 60, start_game),
    ui.Button("MENU",    S.WIDTH // 2, S.HEIGHT // 2 + 170, 240, 60, back_to_menu, accent=S.ACCENT2),
]

# --- ОБРАБОТКА СОБЫТИЙ ---
def handle_events():
    global state, muted
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.MOUSEBUTTONDOWN:
            audio.play('ui_click')
        if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
            muted = not muted
            audio.toggle_mute(muted)

        if state == MENU:
            # Обработка событий для epw происходит централизованно
            epw.handle_event(e)
        elif state == PLAY:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE or e.key == pygame.K_p: set_state(PAUSE)
                elif e.key == pygame.K_LEFT:  game.move(-1)
                elif e.key == pygame.K_RIGHT: game.move(1)
                elif e.key == pygame.K_DOWN:  game.soft_drop()
                elif e.key == pygame.K_UP:    game.rotate(1)
                elif e.key == pygame.K_z:     game.rotate(-1)
                elif e.key == pygame.K_SPACE: game.hard_drop()
                elif e.key == pygame.K_c:
                    if game.hold_piece(): audio.play('rotate')
        elif state == PAUSE:
            for b in pause_buttons: b.handle(e)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE or e.key == pygame.K_p: set_state(PLAY)
                elif e.key == pygame.K_q: set_state(MENU)
        elif state == OVER:
            for b in over_buttons: b.handle(e)
        elif state in (SCORES, ACHS, DAILY):
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                set_state(MENU)

# --- ОТРИСОВКА ---
def draw_playfield_target(surf):
    ui.draw_playfield_frame(surf, board_x, board_y)
    ui.draw_grid_bg(surf, board_x, board_y, pygame.time.get_ticks())
    for y in range(S.ROWS):
        for x in range(S.COLS):
            col = game.grid[y][x]
            if col:
                flash = y in game.clearing
                if flash:
                    pygame.draw.rect(surf, (255, 255, 255),
                                     (board_x + x*S.CELL, board_y + y*S.CELL,
                                      S.CELL, S.CELL), border_radius=3)
                else:
                    kind = next((k for k, v in S.COLORS.items() if v == col), "I")
                    renderer.draw_block(surf, board_x + x*S.CELL, board_y + y*S.CELL, kind)
    if not game.game_over and not game.clearing:
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
        ui.draw_hud(tmp, game, sidebar_x, t)
        fx.draw(tmp)
        screen.fill(S.BG)
        screen.blit(tmp, (ox, oy))
    else:
        draw_playfield_target(screen)
        ui.draw_hud(screen, game, sidebar_x, t)
        fx.draw(screen)
        
    if muted:
        m = ui.F_SMALL.render("MUTED", True, S.DANGER)
        screen.blit(m, (S.WIDTH - 70, 10))
        
    if flash_timer > 0:
        fl = pygame.Surface((S.WIDTH, S.HEIGHT))
        fl.fill((255, 255, 255))
        fl.set_alpha(int(200 * (flash_timer / 300.0)))
        screen.blit(fl, (0, 0))

def handle_game_over():
    global meta, state, last_unlock, last_unlock_t, is_new_high
    is_new_high = game.score > meta.get('best_score', 0)
    save_score(game.score)
    newly = check_run(meta, game, run_time)
    update_persistent(meta, game, run_time)
    if newly:
        last_unlock = newly[0]
        last_unlock_t = pygame.time.get_ticks()
    set_state(OVER)

def draw_over():
    screen.fill(S.BG)
    draw_playfield_target(screen)
    ui.draw_overlay(screen, 190)
    ui.draw_text_center(screen, "GAME OVER", S.HEIGHT // 2 - 120, ui.F_TITLE, S.DANGER)
    if is_new_high:
        h = ui.F_H1.render("NEW HIGH SCORE!", True, S.GOLD)
        screen.blit(h, h.get_rect(center=(S.WIDTH // 2, S.HEIGHT // 2 - 200)))
    ui.draw_text_center(screen, f"Score: {game.score}   Lines: {game.lines}   Level: {game.level}",
                        S.HEIGHT // 2 - 30, ui.F_H2, S.TEXT)
    for b in over_buttons: b.draw(screen)

# --- ГЛАВНЫЙ ЦИКЛ ---
running = True
while running:
    # Регулировка громкости
    try:
        vol = volume_slider.get_value() / 100.0
        pygame.mixer.music.set_volume(vol)
    except:
        pass
    dt = clock.tick(S.FPS)
    t = pygame.time.get_ticks()
    mouse = pygame.mouse.get_pos()

    handle_events()

    if transition_alpha > 0:
        transition_alpha = max(0, transition_alpha - fade_speed)
    if flash_timer > 0:
        flash_timer -= dt

    if state == MENU:
        for b in menu_buttons: b.update(dt, mouse)
        ui.draw_menu(screen, [], t, stars, meta)
        epw.flip()
        stars.update(dt)
    elif state == PLAY:
        if game.game_over:
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
    elif state == SCORES:
        ui.draw_leaderboard(screen, load_scores(), meta.get('best_score', 0))
    elif state == ACHS:
        ui.draw_achievements(screen, meta, ACHIEVEMENTS)
    elif state == DAILY:
        ui.draw_dailies(screen, meta, get_daily_quests())

    if last_unlock and t - last_unlock_t < 2500:
        fade = max(0.0, 1.0 - (t - last_unlock_t) / 2500.0)
        name = next((a['name'] for a in ACHIEVEMENTS if a['id'] == last_unlock), last_unlock)
        toast = ui.F_H2.render(f"* Achievement unlocked: {name}", True, S.GOLD)
        toast.set_alpha(int(255 * fade))
        screen.blit(toast, toast.get_rect(midtop=(S.WIDTH // 2, 10)))
    elif last_unlock:
        last_unlock = None

    if transition_alpha > 0:
        fs = pygame.Surface((S.WIDTH, S.HEIGHT))
        fs.fill((0, 0, 0))
        fs.set_alpha(transition_alpha)
        screen.blit(fs, (0, 0))

    pygame.display.flip()

pygame.quit()
sys.exit()
