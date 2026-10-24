import random
import pygame
from .entities import Rabbit, Enemy


class GameScene:
    def __init__(self, screen, audio):
        self.screen = screen
        self.audio = audio
        self.w, self.h = screen.get_size()
        self.player = Rabbit((self.w // 2, self.h // 2), audio)
        self.enemies = []
        self.score = 0
        self.spawn_timer = 0.0
        self.to_menu = False
        self.font = pygame.font.SysFont("consolas", 22, bold=True)

        for _ in range(4):
            self.spawn_enemy()

    def spawn_enemy(self):
        side = random.choice(("top", "bottom", "left", "right"))
        if side == "top":
            pos = (random.randint(40, self.w - 40), -30)
        elif side == "bottom":
            pos = (random.randint(40, self.w - 40), self.h + 30)
        elif side == "left":
            pos = (-30, random.randint(40, self.h - 40))
        else:
            pos = (self.w + 30, random.randint(40, self.h - 40))
        self.enemies.append(Enemy(pos))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.to_menu = True
            elif event.key in (pygame.K_1, pygame.K_2):
                self.player.weapons.index = event.key - pygame.K_1
            elif event.key == pygame.K_q:
                self.player.weapons.cycle(-1)
            elif event.key == pygame.K_e:
                self.player.weapons.cycle(1)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.player.shoot(event.pos)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, (self.w, self.h))

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = max(0.35, 1.2 - self.score * 0.01)

        for enemy in self.enemies:
            enemy.update(dt, self.player.pos)

        for bullet in list(self.player.weapons.bullets):
            for enemy in self.enemies:
                if enemy.alive and bullet.pos.distance_to(enemy.pos) <= enemy.radius + bullet.radius:
                    dead = enemy.hit(bullet.damage)
                    bullet.life = 0
                    self.audio.play("hit", 0.8)
                    if dead:
                        self.score += 1
                    break

        self.player.weapons.bullets = [b for b in self.player.weapons.bullets if b.life > 0]
        self.enemies = [e for e in self.enemies if e.alive]

    def draw(self):
        self.screen.fill((10, 14, 24))

        for x in range(0, self.w, 40):
            pygame.draw.line(self.screen, (20, 30, 48), (x, 0), (x, self.h))
        for y in range(0, self.h, 40):
            pygame.draw.line(self.screen, (20, 30, 48), (0, y), (self.w, y))

        self.player.draw(self.screen, pygame.mouse.get_pos())
        for enemy in self.enemies:
            enemy.draw(self.screen)

        hud = self.font.render(
            f"WEAPON: {self.player.weapons.current.name}   SCORE: {self.score}",
            True,
            (180, 230, 255),
        )
        self.screen.blit(hud, (20, 18))

        hint = self.font.render("ESC - menu | 1/2 - weapon | Q/E - cycle", True, (120, 150, 180))
        self.screen.blit(hint, (20, self.h - 38))
