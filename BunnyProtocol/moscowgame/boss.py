import pygame
from settings import *

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((160, 80), pygame.SRCALPHA)
        pygame.draw.rect(self.image, PURPLE, (0, 0, 160, 80), border_radius=15)
        pygame.draw.rect(self.image, CYAN, (10, 10, 140, 60), border_radius=10)
        self.rect = self.image.get_rect(center=(WIDTH // 2, 100))
        self.hp = 100
        self.max_hp = 100
        self.vx = 3

    def update(self):
        self.rect.x += self.vx
        if self.rect.right > WIDTH or self.rect.left < 0:
            self.vx *= -1
