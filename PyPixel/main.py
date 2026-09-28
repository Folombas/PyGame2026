"""PyPixel — 2D-платформер на PyGame."""
import sys
import pygame

from settings import WIDTH, HEIGHT, FPS, TITLE, BG_COLOR
from player import Player
from platform import Platform


def create_level():
    """Простой тестовый уровень — набор платформ."""
    platforms = [
        # земля
        Platform(0, HEIGHT - 40, WIDTH, 40),
        # полки
        Platform(120, HEIGHT - 160, 160, 20),
        Platform(360, HEIGHT - 240, 160, 20),
        Platform(600, HEIGHT - 160, 160, 20),
        # ступеньки
        Platform(280, HEIGHT - 380, 100, 20),
        Platform(460, HEIGHT - 440, 100, 20),
    ]
    return platforms


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    platforms = create_level()
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

        screen.fill(BG_COLOR)
        for p in platforms:
            p.draw(screen)
        player.draw(screen)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
