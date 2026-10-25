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
        self.big = pygame.font.SysFont("arial", 60, bold=True)
        self.small = pygame.font.SysFont("arial", 20)
        self.high_score = 0
        self.state = "play"
        self.reset()

    def reset(self):
        self.player = Player(WIDTH // 2, HEIGHT - 60)
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.score = 0
        self.lives = START_LIVES
        self.last_shot = 0
        self.last_spawn = pygame.time.get_ticks()
        self.state = "play"

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
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if self.state == "over" and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
        return True

    def update(self):
        if self.state != "play":
            return
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

        for _ in pygame.sprite.spritecollide(self.player, self.enemies, True):
            if now < self.player.invulnerable_until:
                continue
            self.lives -= 1
            self.player.invulnerable_until = now + 1500
            if self.lives <= 0:
                self.high_score = max(self.high_score, self.score)
                self.state = "over"

    def text(self, msg, font, color, center):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def draw(self):
        self.screen.fill(BLACK)
        self.bullets.draw(self.screen)
        self.enemies.draw(self.screen)
        self.screen.blit(self.player.image, self.player.rect)

        self.screen.blit(self.font.render(f"SCORE {self.score}", True, WHITE), (20, 16))
        for i in range(self.lives):
            x = WIDTH - 40 - i * 30
            pygame.draw.polygon(self.screen, RED, [(x, 22), (x + 10, 40), (x - 10, 40)])

        if self.state == "over":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))
            self.text("GAME OVER", self.big, RED, (WIDTH // 2, HEIGHT // 2 - 60))
            self.text(f"Счёт: {self.score}", self.font, WHITE, (WIDTH // 2, HEIGHT // 2 + 10))
            self.text(f"Рекорд: {self.high_score}", self.font, YELLOW, (WIDTH // 2, HEIGHT // 2 + 50))
            self.text("ENTER — снова", self.small, CYAN, (WIDTH // 2, HEIGHT // 2 + 110))

        pygame.display.flip()
