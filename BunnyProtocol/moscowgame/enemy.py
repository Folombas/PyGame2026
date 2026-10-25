import pygame
import random
from settings import *


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface(ENEMY_SIZE, pygame.SRCALPHA)
        w, h = ENEMY_SIZE
        pygame.draw.polygon(self.image, RED, [(w // 2, h), (0, 0), (w, 0)])
        pygame.draw.circle(self.image, ORANGE, (w // 2, 10), 5)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        self.speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
