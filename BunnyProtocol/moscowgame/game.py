import pygame
from settings import *
from player import Player
from bullet import Bullet


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.player = Player(WIDTH // 2, HEIGHT - 60)
        self.bullets = pygame.sprite.Group()
        self.last_shot = 0

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
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        if keys[pygame.K_SPACE] and now - self.last_shot > BULLET_COOLDOWN:
            self.last_shot = now
            self.bullets.add(Bullet(self.player.rect.centerx, self.player.rect.top))
        self.bullets.update()

    def draw(self):
        self.screen.fill(BLACK)
        self.bullets.draw(self.screen)
        self.screen.blit(self.player.image, self.player.rect)
        pygame.display.flip()
