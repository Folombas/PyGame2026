import pygame
from settings import WIDTH, HEIGHT, TITLE
from game import Game


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    Game(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()
