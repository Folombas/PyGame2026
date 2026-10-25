import pygame
from .audio import Audio
from .menu import MainMenu
from .game_scene import GameScene


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Unix Rabbit: Terminal Arsenal")
    clock = pygame.time.Clock()

    audio = Audio()
    menu = MainMenu(screen, audio)
    game = None
    state = "menu"
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "menu":
                menu.handle_event(event)
                if menu.action == "start":
                    menu.reset()
                    game = GameScene(screen, audio)
                    state = "game"
                elif menu.action == "quit":
                    running = False
            elif state == "game" and game:
                game.handle_event(event)
                if game.to_menu:
                    state = "menu"
                    menu.reset()

        if state == "menu":
            menu.update(dt)
            menu.draw()
        elif state == "game" and game:
            game.update(dt)
            game.draw()

        pygame.display.flip()

    pygame.quit()
