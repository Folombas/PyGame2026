"""PyPixel — 2D-платформер на PyGame."""
import sys
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE,
    WORLD_WIDTH, SKY_COLOR, STAR_COLOR, TEXT_COLOR,
)
from player import Player
from platform import Platform
from camera import Camera
from enemy import Enemy
from collectible import Pixel


def create_stars(count: int = 80):
    stars = []
    for _ in range(count):
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, HEIGHT - 100)
        size = random.choice([1, 1, 1, 2, 2, 3])
        layer = random.choice([0.2, 0.4, 0.6])
        stars.append((x, y, size, layer))
    return stars


def create_level():
    platforms = [
        Platform(0, HEIGHT - 40, WORLD_WIDTH, 40),

        Platform(120, HEIGHT - 160, 160, 20),
        Platform(360, HEIGHT - 240, 160, 20),
        Platform(600, HEIGHT - 160, 160, 20),

        Platform(820, HEIGHT - 300, 100, 20),
        Platform(980, HEIGHT - 380, 100, 20),
        Platform(1140, HEIGHT - 300, 100, 20),

        Platform(1360, HEIGHT - 160, 160, 20),
        Platform(1600, HEIGHT - 240, 160, 20),
        Platform(1840, HEIGHT - 320, 200, 20),

        Platform(2150, HEIGHT - 400, 200, 20),
    ]
    return platforms


def create_enemies():
    return [
        Enemy(200, HEIGHT - 40 - 28),
        Enemy(380, HEIGHT - 240 - 28),
        Enemy(640, HEIGHT - 160 - 28),
        Enemy(1000, HEIGHT - 380 - 28),
        Enemy(1400, HEIGHT - 160 - 28),
        Enemy(1640, HEIGHT - 240 - 28),
        Enemy(1900, HEIGHT - 320 - 28),
    ]


def create_pixels():
    coords = [
        (150, HEIGHT - 200), (200, HEIGHT - 200),
        (400, HEIGHT - 280), (460, HEIGHT - 280),
        (640, HEIGHT - 200), (700, HEIGHT - 200),
        (840, HEIGHT - 340), (1000, HEIGHT - 420),
        (1160, HEIGHT - 340),
        (1400, HEIGHT - 200), (1450, HEIGHT - 200),
        (1640, HEIGHT - 280), (1700, HEIGHT - 280),
        (1880, HEIGHT - 360), (1940, HEIGHT - 360),
        (2200, HEIGHT - 440), (2280, HEIGHT - 440),
    ]
    return [Pixel(x, y) for x, y in coords]


def draw_background(screen, stars, camera):
    screen.fill(SKY_COLOR)
    for x, y, size, layer in stars:
        sx = int(x - camera.offset_x * layer)
        if -10 < sx < WIDTH + 10:
            pygame.draw.rect(screen, STAR_COLOR, (sx, y, size, size))


def draw_hud(screen, font_big, font_small, score, total, game_over):
    score_txt = font_big.render(f"{score} / {total}", True, TEXT_COLOR)
    screen.blit(score_txt, (WIDTH - score_txt.get_width() - 20, 15))

    hint = font_small.render("← →  Space   Esc", True, (150, 150, 150))
    screen.blit(hint, (10, 10))

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        over = font_big.render("GAME OVER", True, (240, 90, 90))
        screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 40))

        info = font_small.render("R — заново    Esc — выход", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 20))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 28, bold=True)
    font_small = pygame.font.SysFont("monospace", 18)

    stars = create_stars()

    def new_game():
        platforms = create_level()
        enemies = create_enemies()
        pixels = create_pixels()
        player = Player(x=40, y=HEIGHT - 200)
        camera = Camera(WIDTH, WORLD_WIDTH)
        return platforms, enemies, pixels, player, camera, 0, False

    platforms, enemies, pixels, player, camera, score, game_over = new_game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game_over:
                    platforms, enemies, pixels, player, camera, score, game_over = new_game()

        if not game_over:
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            player.update(platforms)
            for e in enemies:
                e.update(platforms)
            camera.update(player.rect)

            # сбор пикселей
            for px in pixels:
                if px.alive and player.rect.colliderect(px.rect):
                    px.alive = False
                    score += 1

            # столкновение с врагами
            for e in enemies:
                if player.rect.colliderect(e.rect):
                    game_over = True

        # --- draw ---
        draw_background(screen, stars, camera)
        for p in platforms:
            p.draw(screen, camera.ox)
        for px in pixels:
            px.draw(screen, camera.ox)
        for e in enemies:
            e.draw(screen, camera.ox)
        player.draw(screen, camera.ox)

        total_pixels = len([p for p in create_pixels() if True])  # просто кол-во
        total_pixels = len(pixels)
        draw_hud(screen, font_big, font_small, score, total_pixels, game_over)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
