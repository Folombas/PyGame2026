import pygame
from settings import *
from player import Player


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.player = Player(WIDTH // 2, HEIGHT - 60)

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
        self.player.update(pygame.key.get_pressed())

    def draw(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.player.image, self.player.rect)
        pygame.display.flip()
