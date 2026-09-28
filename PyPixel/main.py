"""PyPixel — 2D-платформер на PyGame."""
import sys
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE, BG_COLOR,
    WORLD_WIDTH, SKY_COLOR, STAR_COLOR,
)
from player import Player
from platform import Platform
from camera import Camera


def create_stars(count: int = 80):
    """Звёзды для параллакс-фона: (x, y, размер, слой)."""
    stars = []
    for _ in range(count):
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, HEIGHT - 100)
        size = random.choice([1, 1, 1, 2, 2, 3])
        layer = random.choice([0.2, 0.4, 0.6])  # коэф. параллакса
        stars.append((x, y, size, layer))
    return stars


def create_level():
    platforms = [
        # земля (на всю ширину мира)
        Platform(0, HEIGHT - 40, WORLD_WIDTH, 40),

        # левый «двор»
        Platform(120, HEIGHT - 160, 160, 20),
        Platform(360, HEIGHT - 240, 160, 20),
        Platform(600, HEIGHT - 160, 160, 20),

        # середина — ступеньки
        Platform(820, HEIGHT - 300, 100, 20),
        Platform(980, HEIGHT - 380, 100, 20),
        Platform(1140, HEIGHT - 300, 100, 20),

        # правый «двор»
        Platform(1360, HEIGHT - 160, 160, 20),
        Platform(1600, HEIGHT - 240, 160, 20),
        Platform(1840, HEIGHT - 320, 200, 20),

        # финишная площадка
        Platform(2150, HEIGHT - 400, 200, 20),
    ]
    return platforms


def draw_background(screen, stars, camera):
    screen.fill(SKY_COLOR)
    for x, y, size, layer in stars:
        sx = int(x - camera.offset_x * layer)
        if -10 < sx < WIDTH + 10:
            pygame.draw.rect(screen, STAR_COLOR, (sx, y, size, size))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    platforms = create_level()
    stars = create_stars()
    camera = Camera(WIDTH, WORLD_WIDTH)
    player = Player(x=40, y=HEIGHT - 200)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.update(platforms)
        camera.update(player.rect)

        # --- draw ---
        draw_background(screen, stars, camera)
        for p in platforms:
            p.draw(screen, camera.ox)
        player.draw(screen, camera.ox)

        # подсказка в углу
        font = pygame.font.SysFont(None, 20)
        txt = font.render(
            f"x = {player.rect.x}   cam = {camera.ox}", True, (150, 150, 150)
        )
        screen.blit(txt, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
