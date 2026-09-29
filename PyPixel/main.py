"""PyPixel — 2D-платформер на PyGame."""
import sys
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE,
    WORLD_WIDTH, SKY_COLOR, STAR_COLOR, TEXT_COLOR,
    HEART_COLOR, HEART_EMPTY_COLOR, VICTORY_TEXT_COLOR,
    INVULN_TIME,
    HP_BAR_BG, HP_BAR_BORDER, HP_COLOR_HIGH, HP_COLOR_MID, HP_COLOR_LOW,
    DIFFICULTIES, DEFAULT_DIFFICULTY,
)
from player import Player
from camera import Camera
from flag import Flag
from fireworks import Firework
from menu import Menu
import levels
import sounds


def create_stars(count=80):
    stars = []
    for _ in range(count):
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, HEIGHT - 100)
        size = random.choice([1, 1, 1, 2, 2, 3])
        layer = random.choice([0.2, 0.4, 0.6])
        stars.append((x, y, size, layer))
    return stars


def load_level(index, difficulty, apples=0):
    platforms, enemies, pixels, trees, flag_pos = levels.LEVELS[index]()
    speed = difficulty["enemy_speed"]
    for e in enemies:
        e.vel_x = speed if e.vel_x > 0 else -speed

    return {
        "platforms": platforms,
        "enemies": enemies,
        "pixels": pixels,
        "trees": trees,
        "apples": apples,
        "flag": Flag(*flag_pos),
        "player": Player(x=40, y=HEIGHT - 200),
        "camera": Camera(WIDTH, WORLD_WIDTH),
        "score": 0,
        "total_pixels": len(pixels),
        "invuln": 0,
        "max_hp": difficulty["max_hp"],
        "hp": difficulty["max_hp"],
        "hit_damage": difficulty["hit_damage"],
        "state": "playing",   # playing / paused / victory / all_clear / game_over
        "fireworks": [],
        "victory_timer": 0,
    }


def draw_background(screen, stars, camera):
    screen.fill(SKY_COLOR)
    for x, y, size, layer in stars:
        sx = int(x - camera.offset_x * layer)
        if -10 < sx < WIDTH + 10:
            pygame.draw.rect(screen, STAR_COLOR, (sx, y, size, size))


def draw_pixel_heart(surface, x, y, scale, color):
    pattern = [
        " xx xx ",
        "xxxxxxx",
        "xxxxxxx",
        " xxxxx ",
        "  xxx  ",
        "   x   ",
    ]
    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch == "x":
                pygame.draw.rect(surface, color,
                                 (x + col * scale, y + row * scale, scale, scale))


def draw_hearts(screen, lives, max_lives):
    scale = 3
    gap = 8
    heart_w = 7 * scale
    for i in range(max_lives):
        hx = 14 + i * (heart_w + gap)
        hy = 12
        color = HEART_COLOR if i < lives else HEART_EMPTY_COLOR
        draw_pixel_heart(screen, hx, hy, scale, color)


def draw_health_bar(screen, font_small, hp, max_hp):
    x, y = 14, 46
    w, h = 200, 16
    pygame.draw.rect(screen, HP_BAR_BORDER, (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(screen, HP_BAR_BG, (x, y, w, h))
    ratio = max(0.0, hp / max_hp)
    fill_w = int(w * ratio)
    if ratio > 0.6:
        color = HP_COLOR_HIGH
    elif ratio > 0.3:
        color = HP_COLOR_MID
    else:
        color = HP_COLOR_LOW
    if fill_w > 0:
        pygame.draw.rect(screen, color, (x, y, fill_w, h))
    label = font_small.render(f"HP {max(0, hp)}/{max_hp}", True, (255, 255, 255))
    screen.blit(label, (x + 8, y + 1))


def draw_apples_counter(screen, font_big, apples):
    """Счётчик собранных яблок — яркая плашка в правом верхнем углу."""
    text = font_big.render(str(apples), True, (255, 240, 240))

    pad_x, pad_y = 14, 6
    icon_w = 18
    inner_gap = 8
    box_w = pad_x * 2 + icon_w + inner_gap + text.get_width()
    box_h = max(text.get_height() + pad_y * 2, 36)
    box_x = WIDTH - box_w - 20
    box_y = 92

    # фон-плашка
    pygame.draw.rect(screen, (45, 30, 45), (box_x, box_y, box_w, box_h))
    pygame.draw.rect(screen, (180, 80, 90), (box_x, box_y, box_w, box_h), 2)

    # иконка яблока
    ix = box_x + pad_x + icon_w // 2
    iy = box_y + box_h // 2
    pygame.draw.circle(screen, (140, 30, 40), (ix, iy), 8)
    pygame.draw.circle(screen, (220, 50, 60), (ix, iy), 7)
    pygame.draw.rect(screen, (255, 180, 180), (ix - 3, iy - 3, 2, 2))
    pygame.draw.rect(screen, (100, 200, 100), (ix + 1, iy - 11, 4, 4))

    # число
    tx = box_x + pad_x + icon_w + inner_gap
    ty = box_y + (box_h - text.get_height()) // 2
    screen.blit(text, (tx, ty))


def draw_hud(screen, font_big, font_small, L, lives, level_index, difficulty_key):
    score = L["score"]
    total = L["total_pixels"]
    score_txt = font_big.render(f"{score} / {total}", True, TEXT_COLOR)
    screen.blit(score_txt, (WIDTH - score_txt.get_width() - 20, 15))

    lvl_txt = font_small.render(
        f"Уровень {level_index + 1} / {len(levels.LEVELS)}    {DIFFICULTIES[difficulty_key]['label']}",
        True, TEXT_COLOR
    )
    screen.blit(lvl_txt, (WIDTH - lvl_txt.get_width() - 20, 55))

    draw_hearts(screen, lives, DIFFICULTIES[difficulty_key]["lives"])
    draw_health_bar(screen, font_small, L["hp"], L["max_hp"])
    draw_apples_counter(screen, font_big, L["apples"])

    state = L["state"]
    if state in ("victory", "all_clear", "game_over", "paused"):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

    if state == "paused":
        txt = font_big.render("ПАУЗА", True, (255, 240, 120))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
        info = font_small.render("Esc — продолжить    M — в меню", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 10))

    elif state == "victory":
        txt = font_big.render("УРОВЕНЬ ПРОЙДЕН!", True, VICTORY_TEXT_COLOR)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 40))

    elif state == "all_clear":
        txt = font_big.render("ВСЕ УРОВНИ ПРОЙДЕНЫ!", True, VICTORY_TEXT_COLOR)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 40))
        info = font_small.render("R — заново    M — меню    Esc — выход", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 90))

    elif state == "game_over":
        txt = font_big.render("GAME OVER", True, (240, 90, 90))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))
        info = font_small.render("R — заново    M — меню    Esc — выход", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 20))


def spawn_firework(L):
    fx = random.randint(80, WIDTH - 80)
    fy = random.randint(80, HEIGHT // 2)
    L["fireworks"].append(Firework(fx, fy))


def main():
    pygame.init()
    sounds.init()
    fullscreen = True

    def create_screen(fs):
        flags = (pygame.SCALED | pygame.FULLSCREEN) if fs else 0
        try:
            return pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1)
        except pygame.error:
            return pygame.display.set_mode((WIDTH, HEIGHT), flags)

    screen = create_screen(fullscreen)
    pygame.mouse.set_visible(False)
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 28, bold=True)
    font_small = pygame.font.SysFont("monospace", 18)

    stars = create_stars()
    menu = Menu(font_big, font_small)

    app_state = "menu"     # menu / playing
    difficulty_key = DEFAULT_DIFFICULTY
    difficulty = DIFFICULTIES[difficulty_key]
    lives = difficulty["lives"]
    level_index = 0
    L = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ================= EVENTS =================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                fullscreen = not fullscreen
                screen = create_screen(fullscreen)
                continue

            # ----- МЕНЮ -----
            if app_state == "menu":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue
                action = menu.handle_event(event)
                if action == "start":
                    difficulty_key = menu.difficulty_key
                    difficulty = DIFFICULTIES[difficulty_key]
                    lives = difficulty["lives"]
                    level_index = 0
                    L = load_level(level_index, difficulty)
                    app_state = "playing"
                elif action == "quit":
                    running = False
                continue

            # ----- ИГРА -----
            if event.type != pygame.KEYDOWN:
                continue

            state = L["state"]

            if event.key == pygame.K_ESCAPE:
                if state == "playing":
                    L["state"] = "paused"
                elif state == "paused":
                    L["state"] = "playing"
                else:
                    running = False

            elif event.key == pygame.K_m and state in ("paused", "game_over", "all_clear"):
                app_state = "menu"

            elif event.key == pygame.K_r and state in ("game_over", "all_clear"):
                lives = difficulty["lives"]
                level_index = 0
                L = load_level(level_index, difficulty)

        # ================= UPDATE =================
        if app_state == "menu":
            menu.update()
            menu.draw(screen)
            pygame.display.flip()
            continue

        state = L["state"]

        if state == "playing":
            keys = pygame.key.get_pressed()
            L["player"].handle_input(keys)
            L["player"].update(L["platforms"])
            for e in L["enemies"]:
                e.update(L["platforms"])
            L["camera"].update(L["player"].rect)

            if L["invuln"] > 0:
                L["invuln"] -= 1

            # сбор пикселей
            for px in L["pixels"]:
                if px.alive and L["player"].rect.colliderect(px.rect):
                    px.alive = False
                    L["score"] += 1
                    sounds.play("collect")

            # сбор яблок с деревьев
            for tree in L["trees"]:
                for idx, arect in tree.apple_world_rects():
                    if L["player"].rect.colliderect(arect):
                        tree.collect(idx)
                        L["apples"] += 1
                        sounds.play("collect")

            # враги
            for e in L["enemies"]:
                if not e.alive:
                    continue
                if L["player"].rect.colliderect(e.rect):
                    stomp = (
                        L["player"].vel_y > 0
                        and L["player"].rect.bottom - L["player"].vel_y <= e.rect.top + 8
                    )
                    if stomp:
                        e.alive = False
                        L["player"].vel_y = -12
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
                            else:
                                L["player"] = Player(x=40, y=HEIGHT - 200)
                                L["camera"] = Camera(WIDTH, WORLD_WIDTH)
                                L["hp"] = L["max_hp"]

            # флаг
            if L["player"].rect.colliderect(L["flag"].rect):
                L["flag"].lower()
                if L["score"] >= L["total_pixels"]:
                    L["state"] = "victory"
                    L["victory_timer"] = 0
                    sounds.play("victory")

        elif state == "victory":
            L["victory_timer"] += 1
            L["camera"].update(L["player"].rect)
            if L["victory_timer"] % 18 == 0:
                spawn_firework(L)
            if L["victory_timer"] > 180:
                level_index += 1
                if level_index >= len(levels.LEVELS):
                    final_score = L["score"]
                    final_apples = L["apples"]
                    L = load_level(0, difficulty, final_apples)
                    L["score"] = final_score
                    L["state"] = "all_clear"
                    level_index = len(levels.LEVELS)
                else:
                    L = load_level(level_index, difficulty, L["apples"])

        elif state == "all_clear":
            L["victory_timer"] += 1
            if L["victory_timer"] % 18 == 0:
                spawn_firework(L)

        L["flag"].animate(dt)
        for fw in L["fireworks"]:
            fw.update(dt)
        L["fireworks"] = [fw for fw in L["fireworks"] if not fw.dead]

        # ================= DRAW =================
        draw_background(screen, stars, L["camera"])
        for p in L["platforms"]:
            p.draw(screen, L["camera"].ox)
        for t in L["trees"]:
            t.draw(screen, L["camera"].ox)
        L["flag"].draw(screen, L["camera"].ox)
        for px in L["pixels"]:
            px.draw(screen, L["camera"].ox)
        for e in L["enemies"]:
            e.draw(screen, L["camera"].ox)

        blink = L["invuln"] > 0 and (L["invuln"] // 4) % 2 == 0
        if not blink:
            L["player"].draw(screen, L["camera"].ox)

        for fw in L["fireworks"]:
            fw.draw(screen)

        draw_hud(screen, font_big, font_small, L, lives, level_index, difficulty_key)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
