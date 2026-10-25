import pygame
from settings import *
from player import Player
from bullet import Bullet
from enemy import Enemy


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 28, bold=True)
        self.player = Player(WIDTH // 2, HEIGHT - 60)
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.score = 0
        self.last_shot = 0
        self.last_spawn = pygame.time.get_ticks()

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

        if now - self.last_spawn > ENEMY_SPAWN_MS:
            self.last_spawn = now
            self.enemies.add(Enemy())

        self.bullets.update()
        self.enemies.update()

        for _ in pygame.sprite.groupcollide(self.enemies, self.bullets, True, True):
            self.score += 10

    def draw(self):
        self.screen.fill(BLACK)
        self.bullets.draw(self.screen)
        self.enemies.draw(self.screen)
        self.screen.blit(self.player.image, self.player.rect)
        hud = self.font.render(f"SCORE {self.score}", True, WHITE)
        self.screen.blit(hud, (20, 16))
        pygame.display.flip()
