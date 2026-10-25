import pygame
import random
from settings import *
from player import Player
from bullet import Bullet
from enemy import Enemy
from powerup import PowerUp
from particles import explode


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
        self.powerups = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.score = 0
        self.lives = START_LIVES
        self.last_shot = 0
        self.last_spawn = pygame.time.get_ticks()
        self.rapid_until = 0
        self.triple_until = 0
        self.shake = 0
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

        cooldown = 100 if now < self.rapid_until else BULLET_COOLDOWN
        if keys[pygame.K_SPACE] and now - self.last_shot > cooldown:
            self.last_shot = now
            if now < self.triple_until:
                for dx in (-12, 0, 12):
                    self.bullets.add(Bullet(self.player.rect.centerx + dx, self.player.rect.top))
            else:
                self.bullets.add(Bullet(self.player.rect.centerx, self.player.rect.top))

        if now - self.last_spawn > ENEMY_SPAWN_MS:
            self.last_spawn = now
            self.enemies.add(Enemy())

        self.bullets.update()
        self.enemies.update()
        self.powerups.update()
        self.particles.update()

        for enemy in pygame.sprite.groupcollide(self.enemies, self.bullets, True, True):
            self.score += 10
            explode(enemy.rect.centerx, enemy.rect.centery, ORANGE, self.particles, 12)
            self.shake = 4
            if random.random() < 0.12:
                self.powerups.add(PowerUp(*enemy.rect.center))

        for p in pygame.sprite.spritecollide(self.player, self.powerups, True):
            if p.kind == "rapid":
                self.rapid_until = now + 6000
            else:
                self.triple_until = now + 6000
            explode(p.rect.centerx, p.rect.centery, GREEN, self.particles, 8)

        for _ in pygame.sprite.spritecollide(self.player, self.enemies, True):
            if now < self.player.invulnerable_until:
                continue
            self.lives -= 1
            self.shake = 12
            explode(self.player.rect.centerx, self.player.rect.centery, CYAN, self.particles, 22)
            self.player.invulnerable_until = now + 1500
            if self.lives <= 0:
                self.high_score = max(self.high_score, self.score)
                self.state = "over"

        if self.shake > 0:
            self.shake -= 1

    def text(self, msg, font, color, center):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def draw(self):
        self.screen.fill(BLACK)

        off = (0, 0)
        if self.shake > 0:
            off = (random.randint(-self.shake, self.shake),
                   random.randint(-self.shake, self.shake))

        for group in (self.bullets, self.enemies, self.powerups, self.particles):
            for s in group:
                self.screen.blit(s.image, (s.rect.x + off[0], s.rect.y + off[1]))

        now = pygame.time.get_ticks()
        if now > self.player.invulnerable_until or (now // 100) % 2 == 0:
            self.screen.blit(self.player.image,
                             (self.player.rect.x + off[0], self.player.rect.y + off[1]))

        self.screen.blit(self.font.render(f"SCORE {self.score}", True, WHITE), (20, 16))
        for i in range(self.lives):
            x = WIDTH - 40 - i * 30
            pygame.draw.polygon(self.screen, RED, [(x, 22), (x + 10, 40), (x - 10, 40)])

        if now < self.rapid_until:
            self.text("RAPID", self.small, GREEN, (WIDTH // 2 - 60, 24))
        if now < self.triple_until:
            self.text("TRIPLE", self.small, PURPLE, (WIDTH // 2 + 60, 24))

        if self.state == "over":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))
            self.text("GAME OVER", self.big, RED, (WIDTH // 2, HEIGHT // 2 - 60))
            self.text(f"Счёт: {self.score}", self.font, WHITE, (WIDTH // 2, HEIGHT // 2 + 10))
            self.text(f"Рекорд: {self.high_score}", self.font, YELLOW, (WIDTH // 2, HEIGHT // 2 + 50))
            self.text("ENTER — снова", self.small, CYAN, (WIDTH // 2, HEIGHT // 2 + 110))

        pygame.display.flip()
