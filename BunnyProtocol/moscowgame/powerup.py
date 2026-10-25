import pygame
import random
from settings import *


class PowerUp(pygame.sprite.Sprite):
    TYPES = ["rapid", "triple"]

    def __init__(self, x, y):
        super().__init__()
        self.kind = random.choice(self.TYPES)
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        color = GREEN if self.kind == "rapid" else PURPLE
        pygame.draw.circle(self.image, color, (12, 12), 12)
        pygame.draw.circle(self.image, WHITE, (12, 12), 12, 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
