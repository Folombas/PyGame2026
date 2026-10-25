import pygame
import random
from settings import *

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.kind = random.choice(["basic", "fast", "tank"])
        
        if self.kind == "basic":
            color = RED
            self.speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
            self.hp = 1
            size = ENEMY_SIZE
        elif self.kind == "fast":
            color = ORANGE
            self.speed = random.uniform(4.0, 6.0)
            self.hp = 1
            size = (24, 20)
        else: # tank
            color = PURPLE
            self.speed = random.uniform(1.0, 1.5)
            self.hp = 3
            size = (46, 40)

        self.image = pygame.Surface(size, pygame.SRCALPHA)
        w, h = size
        pygame.draw.polygon(self.image, color, [(w // 2, h), (0, 0), (w, 0)])
        pygame.draw.circle(self.image, WHITE, (w // 2, h // 3), max(3, w // 8))
        
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -self.rect.height

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
