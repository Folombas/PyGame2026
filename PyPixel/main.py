"""PyPixel — 2D-платформер на PyGame."""
import sys
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE,
    WORLD_WIDTH, SKY_COLOR, STAR_COLOR, TEXT_COLOR,
    LIVES, HEART_COLOR, HEART_EMPTY_COLOR, VICTORY_TEXT_COLOR,
    INVULN_TIME,
)
from player import Player
from camera import Camera
from flag import Flag
from fireworks import Firework
import levels


def create_stars(count: int = 80):
    stars = []
    for _ in range(count):
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, HEIGHT - 100)
        size = random.choice([1, 1, 1, 2, 2, 3])
        layer = random.choice([0.2, 0.4, 0.6])
        stars.append((x, y, size, layer))
    return stars


def load_level(index: int) -> dict:
    platforms, enemies, pixels, flag_pos = levels.LEVELS[index]()
    return {
        "platforms": platforms,
        "enemies": enemies,
        "pixels": pixels,
        "flag": Flag(*flag_pos),
        "player": Player(x=40, y=HEIGHT - 200),
        "camera": Camera(WIDTH, WORLD_WIDTH),
        "score": 0,
        "total_pixels": len(pixels),
        "invuln": 0,
        "state": "playing",     # playing / victory / all_clear / game_over
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
    """Пиксельное сердце. scale — размер 'пикселя' в px."""
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
                pygame.draw.rect(
                    surface, color,
                    (x + col * scale, y + row * scale, scale, scale)
                )


def draw_hearts(screen, lives: int, max_lives: int):
    scale = 3
    gap = 8
    heart_w = 7 * scale
    for i in range(max_lives):
        hx = 14 + i * (heart_w + gap)
        hy = 12
        color = HEART_COLOR if i < lives else HEART_EMPTY_COLOR
        draw_pixel_heart(screen, hx, hy, scale, color)


def draw_hud(screen, font_big, font_small, L, lives, level_index):
    score = L["score"]
    total = L["total_pixels"]
    score_txt = font_big.render(f"{score} / {total}", True, TEXT_COLOR)
    screen.blit(score_txt, (WIDTH - score_txt.get_width() - 20, 15))

    lvl_txt = font_small.render(f"Уровень {level_index + 1} / {len(levels.LEVELS)}",
                                True, TEXT_COLOR)
    screen.blit(lvl_txt, (WIDTH - lvl_txt.get_width() - 20, 55))

    draw_hearts(screen, lives, LIVES)

    state = L["state"]
    if state in ("victory", "all_clear", "game_over"):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

    if state == "victory":
        txt = font_big.render("УРОВЕНЬ ПРОЙДЕН!", True, VICTORY_TEXT_COLOR)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 40))

    elif state == "all_clear":
        txt = font_big.render("ВСЕ УРОВНИ ПРОЙДЕНЫ!", True, VICTORY_TEXT_COLOR)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 40))
        info = font_small.render("R — заново   Esc — выход", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 90))

    elif state == "game_over":
        txt = font_big.render("GAME OVER", True, (240, 90, 90))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))
        info = font_small.render("R — заново   Esc — выход", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 20))


def spawn_firework(L):
    fx = random.randint(80, WIDTH - 80)
    fy = random.randint(80, HEIGHT // 2)
    L["fireworks"].append(Firework(fx, fy))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 28, bold=True)
    font_small = pygame.font.SysFont("monospace", 18)

    stars = create_stars()
    level_index = 0
    lives = LIVES
    L = load_level(level_index)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and L["state"] in ("game_over", "all_clear"):
                    level_index = 0
                    lives = LIVES
                    L = load_level(level_index)

        state = L["state"]

        # ---------- UPDATE ----------
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
                    elif L["invuln"] == 0:
                        lives -= 1
                        if lives <= 0:
                            L["state"] = "game_over"
                        else:
                            # респаун
                            L["player"] = Player(x=40, y=HEIGHT - 200)
                            L["camera"] = Camera(WIDTH, WORLD_WIDTH)
                            L["invuln"] = INVULN_TIME

            # флаг
            if L["player"].rect.colliderect(L["flag"].rect):
                L["flag"].lower()
                if L["score"] >= L["total_pixels"]:
                    L["state"] = "victory"
                    L["victory_timer"] = 0

        elif state == "victory":
            L["victory_timer"] += 1
            L["camera"].update(L["player"].rect)

            if L["victory_timer"] % 18 == 0:
                spawn_firework(L)

            if L["victory_timer"] > 180:      # ~3 сек
                level_index += 1
                if level_index >= len(levels.LEVELS):
                    L = load_level(0)
                    L["state"] = "all_clear"
                else:
                    L = load_level(level_index)

        elif state == "all_clear":
            L["victory_timer"] += 1
            if L["victory_timer"] % 18 == 0:
                spawn_firework(L)

        # анимация флага идёт всегда
        L["flag"].animate(dt)

        # фейерверки
        for fw in L["fireworks"]:
            fw.update(dt)
        L["fireworks"] = [fw for fw in L["fireworks"] if not fw.dead]

        # ---------- DRAW ----------
        draw_background(screen, stars, L["camera"])
        for p in L["platforms"]:
            p.draw(screen, L["camera"].ox)
        L["flag"].draw(screen, L["camera"].ox)
        for px in L["pixels"]:
            px.draw(screen, L["camera"].ox)
        for e in L["enemies"]:
            e.draw(screen, L["camera"].ox)

        # мерцание при неуязвимости
        blink = L["invuln"] > 0 and (L["invuln"] // 4) % 2 == 0
        if not blink:
            L["player"].draw(screen, L["camera"].ox)

        for fw in L["fireworks"]:
            fw.draw(screen)

        draw_hud(screen, font_big, font_small, L, lives, level_index)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
