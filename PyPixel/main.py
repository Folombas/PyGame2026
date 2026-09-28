"""PyPixel — 2D-платформер на PyGame. Точка входа."""
import pygame
import sys

# --- Константы ---
WIDTH, HEIGHT = 800, 600
FPS = 60
TITLE = "PyPixel"

# --- Цвета (пиксельная палитра) ---
BG_COLOR = (24, 20, 37)
PLAYER_COLOR = (120, 200, 120)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(BG_COLOR)
        pygame.draw.rect(
            screen, PLAYER_COLOR,
            (WIDTH // 2 - 16, HEIGHT // 2 - 16, 32, 32)
        )
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

