import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        w, h = PLAYER_SIZE
        pygame.draw.polygon(self.image, CYAN, [(w // 2, 0), (w, h), (w // 2, h - 8), (0, h)])
        pygame.draw.circle(self.image, WHITE, (w // 2, h // 2), 5)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PLAYER_SPEED
        self.invulnerable_until = 0
        self.dash_cooldown = 0

    def update(self, keys, now):
        current_speed = self.speed
        
        # Рывок на Shift
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and now > self.dash_cooldown:
            current_speed = self.speed * 3.5
            self.invulnerable_until = max(self.invulnerable_until, now + 200)
            self.dash_cooldown = now + 1500 # КД рывка 1.5 сек

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += current_speed
            
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
