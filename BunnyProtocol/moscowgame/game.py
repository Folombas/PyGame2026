import pygame
from settings import *


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            running = self.handle_events()
            self.update()
            self.draw()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False
        return True

    def update(self):
        pass

    def draw(self):
        self.screen.fill(BLACK)
        pygame.display.flip()
