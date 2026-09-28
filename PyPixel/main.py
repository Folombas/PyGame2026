"""PyPixel — 2D-платформер на PyGame."""
import sys
import pygame

from settings import WIDTH, HEIGHT, FPS, TITLE, BG_COLOR, GROUND_COLOR, GROUND_Y
from player import Player


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    player = Player(x=WIDTH // 2 - 16, y=GROUND_Y - 32)

    running = True
    while running:
        # --- events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # --- update ---
        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.update()

        # --- draw ---
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        player.draw(screen)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
