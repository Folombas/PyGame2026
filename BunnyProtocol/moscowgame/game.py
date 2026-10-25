import pygame
import random
from settings import *
from player import Player
from bullet import Bullet, EnemyBullet
from enemy import Enemy
from powerup import PowerUp
from particles import explode
from boss import Boss


class Game:
    MENU, PLAY, PAUSE, OVER = "menu", "play", "pause", "over"

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 28, bold=True)
        self.big = pygame.font.SysFont("arial", 60, bold=True)
        self.small = pygame.font.SysFont("arial", 20)
        self.high_score = 0
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                       random.uniform(0.3, 1.5)) for _ in range(120)]
        self.reset()
        self.state = self.MENU

    def reset(self):
        self.player = Player(WIDTH // 2, HEIGHT - 60)
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
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
        self.boss = None
        self.last_boss_shot = 0

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
                if self.state == self.MENU and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
                    self.state = self.PLAY
                elif self.state == self.OVER and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
                    self.state = self.PLAY
                elif self.state == self.PLAY and e.key == pygame.K_p:
                    self.state = self.PAUSE
                elif self.state == self.PAUSE and e.key == pygame.K_p:
                    self.state = self.PLAY
        return True

    def update(self):
        for i, (sx, sy, sz) in enumerate(self.stars):
            sy += sz
            if sy > HEIGHT:
                sx, sy = random.randint(0, WIDTH), 0
            self.stars[i] = (sx, sy, sz)

        if self.state != self.PLAY:
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

        interval = max(280, ENEMY_SPAWN_MS - self.score * 4)
        if now - self.last_spawn > interval:
            self.last_spawn = now
            self.enemies.add(Enemy())

        self.bullets.update()
        self.enemies.update()
        self.enemy_bullets.update()
        self.powerups.update()
        self.particles.update()

        if self.score >= 1000 and not self.boss:
            self.boss = Boss()

        if self.boss:
            self.boss.update()

        for enemy in pygame.sprite.groupcollide(self.enemies, self.bullets, True, True):
            self.score += 10
            explode(enemy.rect.centerx, enemy.rect.centery, ORANGE, self.particles, 12)
            self.shake = 4
            if random.random() < 0.02:
                self.enemy_bullets.add(EnemyBullet(enemy.rect.centerx, enemy.rect.bottom))
            if random.random() < 0.12:
                self.powerups.add(PowerUp(*enemy.rect.center))

        for p in pygame.sprite.spritecollide(self.player, self.powerups, True):
            if p.kind == "rapid":
                self.rapid_until = now + 6000
            else:
                self.triple_until = now + 6000
            explode(p.rect.centerx, p.rect.centery, GREEN, self.particles, 8)

        for _ in pygame.sprite.spritecollide(self.player, self.enemies, True):
            if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True) or now < self.player.invulnerable_until:
                continue
            self.lives -= 1
            self.shake = 12
            explode(self.player.rect.centerx, self.player.rect.centery, CYAN, self.particles, 22)
            self.player.invulnerable_until = now + 1500
            if self.lives <= 0:
                self.high_score = max(self.high_score, self.score)
                self.state = self.OVER

        if self.shake > 0:
            self.shake -= 1

    def text(self, msg, font, color, center):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def draw(self):
        self.screen.fill(BLACK)
        for sx, sy, sz in self.stars:
            c = (170, 170, 210) if sz > 1 else (80, 80, 120)
            pygame.draw.circle(self.screen, c, (int(sx), int(sy)), 1 if sz < 1 else 2)

        if self.state == self.MENU:
            self.text("MOSCOW GAME WEEK", self.big, CYAN, (WIDTH // 2, HEIGHT // 2 - 80))
            self.text("SPACE DEFENDER", self.big, YELLOW, (WIDTH // 2, HEIGHT // 2 - 10))
            self.text(f"Рекорд: {self.high_score}", self.font, YELLOW, (WIDTH // 2, HEIGHT // 2 + 40))
            self.text("ENTER / SPACE — старт", self.font, WHITE, (WIDTH // 2, HEIGHT // 2 + 90))
            self.text("<- -> движение · SPACE огонь · P пауза · ESC выход",
                      self.small, (150, 150, 180), (WIDTH // 2, HEIGHT // 2 + 140))
            pygame.display.flip()
            return

        off = (0, 0)
        if self.shake > 0:
            off = (random.randint(-self.shake, self.shake),
                   random.randint(-self.shake, self.shake))

        for group in (self.bullets, self.enemy_bullets, self.enemies, self.powerups, self.particles):
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

        if self.state == self.PAUSE:
            self.text("ПАУЗА", self.big, WHITE, (WIDTH // 2, HEIGHT // 2))

        if self.boss:
            self.screen.blit(self.boss.image, self.boss.rect)
            pygame.draw.rect(self.screen, RED, (self.boss.rect.x, self.boss.rect.y - 15, self.boss.rect.width, 10))
            pygame.draw.rect(self.screen, GREEN, (self.boss.rect.x, self.boss.rect.y - 15, self.boss.rect.width * (self.boss.hp / self.boss.max_hp), 10))

        if self.state == self.OVER:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))
            self.text("GAME OVER", self.big, RED, (WIDTH // 2, HEIGHT // 2 - 60))
            self.text(f"Счёт: {self.score}", self.font, WHITE, (WIDTH // 2, HEIGHT // 2 + 10))
            self.text(f"Рекорд: {self.high_score}", self.font, YELLOW, (WIDTH // 2, HEIGHT // 2 + 50))
            self.text("ENTER — снова", self.small, CYAN, (WIDTH // 2, HEIGHT // 2 + 110))

        pygame.display.flip()
