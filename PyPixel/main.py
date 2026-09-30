"""PyPixel — бесконечный процедурный платформер."""
import sys
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE, TEXT_COLOR,
    LIVES, HEART_COLOR, HEART_EMPTY_COLOR,
    INVULN_TIME, DIFFICULTIES, DEFAULT_DIFFICULTY,
    HP_BAR_BG, HP_BAR_BORDER, HP_COLOR_HIGH, HP_COLOR_MID, HP_COLOR_LOW,
)
from player import Player
from camera import Camera
from menu import Menu
from world import World, surface_y, DEATH_Y, SURFACE_Y
from records import save_record
import sounds


# ---------- ФОН ----------
def draw_cloud(surface, cx, cy, size, color=(255, 255, 255)):
    w, h = size, size // 3
    pygame.draw.ellipse(surface, color, (cx - w // 2, cy - h // 4, w, h))
    pygame.draw.ellipse(surface, color, (cx - w // 3, cy - h // 2, w // 2, h))
    pygame.draw.ellipse(surface, color, (cx, cy - h // 2, w // 2, h))
    pygame.draw.ellipse(surface, color, (cx - w // 4, cy - h + h // 2, w // 3, h))


def draw_background(screen, camera):
    oy = camera.offset_y
    ox = camera.offset_x
    ground_y = SURFACE_Y - oy

    sky_top = (90, 155, 220)
    sky_bot = (185, 220, 245)
    cave_top = (45, 28, 25)
    cave_bot = (8, 5, 10)

    for y_screen in range(HEIGHT):
        if y_screen < ground_y:
            t = min(1.0, max(0.0, (ground_y - y_screen) / 500.0))
            col = (int(sky_bot[0] * (1 - t) + sky_top[0] * t),
                   int(sky_bot[1] * (1 - t) + sky_top[1] * t),
                   int(sky_bot[2] * (1 - t) + sky_top[2] * t))
        else:
            t = min(1.0, (y_screen - ground_y) / 700.0)
            col = (int(cave_top[0] * (1 - t) + cave_bot[0] * t),
                   int(cave_top[1] * (1 - t) + cave_bot[1] * t),
                   int(cave_top[2] * (1 - t) + cave_bot[2] * t))
        pygame.draw.line(screen, col, (0, y_screen), (WIDTH, y_screen))

    # Силуэты гор
    if -100 < ground_y < HEIGHT + 100:
        for parallax, color, h, spacing in [
            (0.15, (165, 190, 220), 130, 420),
            (0.30, (135, 165, 205), 190, 360),
            (0.45, (105, 140, 185), 250, 300),
        ]:
            shift = int(ox * parallax) % spacing
            cx = -shift - spacing
            while cx <= WIDTH + spacing:
                pygame.draw.polygon(screen, color, [
                    (cx, ground_y),
                    (cx + spacing // 2, ground_y - h),
                    (cx + spacing, ground_y),
                ])
                cx += spacing

    # Облака (привязаны к мировым X, только выше земли)
    for i in range(40):
        cx_world = i * 350 + random.Random(i).randint(-100, 100)
        cy_world = 200 + (i * 137) % (SURFACE_Y - 400)
        size = 50 + (i * 31) % 50
        layer = 0.2 + (i % 3) * 0.2
        sx = int(cx_world - ox * layer)
        sy = int(cy_world - oy)
        if -size < sx < WIDTH + size and -size < sy < HEIGHT + size:
            draw_cloud(screen, sx + 3, sy + 3, size, (200, 210, 225))
            draw_cloud(screen, sx, sy, size, (255, 255, 255))


# ---------- HUD ----------
def draw_pixel_heart(surface, x, y, scale, color):
    pattern = [" xx xx ", "xxxxxxx", "xxxxxxx", " xxxxx ", "  xxx  ", "   x   "]
    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch == "x":
                pygame.draw.rect(surface, color,
                                 (x + col * scale, y + row * scale, scale, scale))


def draw_hearts(screen, lives, max_lives):
    scale = 3
    gap = 8
    hw = 7 * scale
    for i in range(max_lives):
        color = HEART_COLOR if i < lives else HEART_EMPTY_COLOR
        draw_pixel_heart(screen, 14 + i * (hw + gap), 12, scale, color)


def draw_health_bar(screen, font_small, hp, max_hp):
    x, y = 14, 46
    w, h = 200, 16
    pygame.draw.rect(screen, HP_BAR_BORDER, (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(screen, HP_BAR_BG, (x, y, w, h))
    ratio = max(0.0, hp / max_hp)
    fill = int(w * ratio)
    if ratio > 0.6:
        c = HP_COLOR_HIGH
    elif ratio > 0.3:
        c = HP_COLOR_MID
    else:
        c = HP_COLOR_LOW
    if fill > 0:
        pygame.draw.rect(screen, c, (x, y, fill, h))
    label = font_small.render(f"HP {max(0, hp)}/{max_hp}", True, (255, 255, 255))
    screen.blit(label, (x + 8, y + 1))


def draw_hud(screen, font_big, font_small, L, lives, difficulty_key):
    distance = max(0, L["max_x"]) // 10
    depth = max(0, L["max_y"] - SURFACE_Y) // 10

    score_txt = font_big.render(f"Очки: {L['score']}", True, TEXT_COLOR)
    screen.blit(score_txt, (WIDTH - score_txt.get_width() - 20, 15))

    stats = (f"Дистанция: {distance} м   Глубина: {depth} м   "
             f"Враги: {L['kills']}   Яблоки: {L['apples']}")
    s = font_small.render(stats, True, TEXT_COLOR)
    screen.blit(s, (WIDTH - s.get_width() - 20, 55))

    draw_hearts(screen, lives, DIFFICULTIES[difficulty_key]["lives"])
    draw_health_bar(screen, font_small, L["hp"], L["max_hp"])

    if L["state"] == "game_over":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        txt = font_big.render("GAME OVER", True, (240, 90, 90))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
        info = font_small.render(
            f"Дистанция: {distance} м   Глубина: {depth} м",
            True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 10))
        info2 = font_small.render("R — заново    M — меню    Esc — выход", True, TEXT_COLOR)
        screen.blit(info2, (WIDTH // 2 - info2.get_width() // 2, HEIGHT // 2 + 30))

    elif L["state"] == "paused":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        txt = font_big.render("ПАУЗА", True, (255, 240, 120))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
        info = font_small.render("Esc — продолжить    M — в меню", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 10))


# ---------- ЗАПУСК УРОВНЯ-СЕССИИ ----------
def new_session(difficulty):
    player = Player(x=0, y=surface_y(0) - 100)
    camera = Camera(WIDTH)
    camera.update(player.rect)
    return {
        "player": player,
        "camera": camera,
        "world": World(difficulty),
        "hp": difficulty["max_hp"],
        "max_hp": difficulty["max_hp"],
        "hit_damage": difficulty["hit_damage"],
        "score": 0,
        "kills": 0,
        "apples": 0,
        "invuln": 0,
        "max_x": 0,
        "max_y": surface_y(0),
        "state": "playing",
    }


def main():
    pygame.init()
    sounds.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 28, bold=True)
    font_small = pygame.font.SysFont("monospace", 18)

    menu = Menu(font_big, font_small)
    app_state = "menu"
    difficulty_key = DEFAULT_DIFFICULTY
    difficulty = DIFFICULTIES[difficulty_key]
    lives = difficulty["lives"]
    L = None

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if app_state == "menu":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue
                action = menu.handle_event(event)
                if action == "start":
                    difficulty_key = menu.difficulty_key
                    difficulty = DIFFICULTIES[difficulty_key]
                    lives = difficulty["lives"]
                    L = new_session(difficulty)
                    app_state = "playing"
                elif action == "quit":
                    running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                if L["state"] == "playing":
                    L["state"] = "paused"
                elif L["state"] == "paused":
                    L["state"] = "playing"
                else:
                    running = False
            elif event.key == pygame.K_m and L["state"] in ("paused", "game_over"):
                app_state = "menu"
            elif event.key == pygame.K_r and L["state"] == "game_over":
                L = new_session(difficulty)
                lives = difficulty["lives"]

        # ============ МЕНЮ ============
        if app_state == "menu":
            menu.update()
            menu.draw(screen)
            pygame.display.flip()
            continue

        # ============ ИГРА ============
        if L["state"] == "playing":
            keys = pygame.key.get_pressed()
            L["player"].handle_input(keys)

            L["world"].update(L["camera"])
            platforms, enemies, pixels, trees, medkits = L["world"].collect()

            L["player"].update(platforms)
            for e in enemies:
                e.update(platforms)
            L["camera"].update(L["player"].rect)

            # обновляем рекордные координаты
            L["max_x"] = max(L["max_x"], L["player"].rect.x)
            L["max_y"] = max(L["max_y"], L["player"].rect.y)

            if L["invuln"] > 0:
                L["invuln"] -= 1

            # падение в бездну
            if L["player"].rect.top > DEATH_Y:
                lives -= 1
                if lives <= 0:
                    L["state"] = "game_over"
                    sounds.play("game_over")
                    save_record(L["score"], 0, 0, L["kills"], L["apples"],
                                L["max_x"] // 10, difficulty_key)
                else:
                    L["player"] = Player(x=0, y=surface_y(0) - 100)
                    L["camera"] = Camera(WIDTH)
                    L["hp"] = L["max_hp"]
                    sounds.play("hit")

            # пиксели
            for px in pixels:
                if px.alive and L["player"].rect.colliderect(px.rect):
                    px.alive = False
                    L["score"] += 1
                    sounds.play("collect")

            # яблоки
            for tree in trees:
                for idx, arect in tree.apple_world_rects():
                    if L["player"].rect.colliderect(arect):
                        tree.collect(idx)
                        L["apples"] += 1
                        L["score"] += 2
                        sounds.play("collect")

            # аптечки
            for mk in medkits:
                if mk.alive and L["player"].rect.colliderect(mk.rect):
                    mk.alive = False
                    L["hp"] = min(L["hp"] + 30, L["max_hp"])
                    sounds.play("collect")

            # враги
            for e in enemies:
                if not e.alive:
                    continue
                if L["player"].rect.colliderect(e.rect):
                    stomp = (L["player"].vel_y > 0
                             and L["player"].rect.bottom - L["player"].vel_y
                             <= e.rect.top + 8)
                    if stomp:
                        e.alive = False
                        L["player"].vel_y = -12
                        L["kills"] += 1
                        L["score"] += 5
                        sounds.play("stomp")
                    elif L["invuln"] == 0:
                        L["hp"] -= L["hit_damage"]
                        L["invuln"] = INVULN_TIME
                        sounds.play("hit")
                        if L["hp"] <= 0:
                            lives -= 1
                            if lives <= 0:
                                L["state"] = "game_over"
                                sounds.play("game_over")
                                save_record(L["score"], 0, 0, L["kills"], L["apples"],
                                            L["max_x"] // 10, difficulty_key)
                            else:
                                L["player"] = Player(x=0, y=surface_y(0) - 100)
                                L["camera"] = Camera(WIDTH)
                                L["hp"] = L["max_hp"]

        # ---- отрисовка ----
        draw_background(screen, L["camera"])
        ox, oy = L["camera"].ox, L["camera"].oy

        platforms, enemies, pixels, trees, medkits = L["world"].collect()

        for p in platforms:
            p.draw(screen, ox, oy)
        for t in trees:
            t.draw(screen, ox, oy)
        for mk in medkits:
            mk.draw(screen, ox, oy)
        for px in pixels:
            px.draw(screen, ox, oy)
        for e in enemies:
            e.draw(screen, ox, oy)

        blink = L["invuln"] > 0 and (L["invuln"] // 4) % 2 == 0
        if not blink:
            L["player"].draw(screen, ox, oy)

        draw_hud(screen, font_big, font_small, L, lives, difficulty_key)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
