"""Игрок."""
import pygame
from settings import (
    PLAYER_COLOR, GRAVITY, PLAYER_SPEED, JUMP_POWER, GROUND_Y
)


class Player:
    def __init__(self, x: int, y: int, size: int = 32):
        self.rect = pygame.Rect(x, y, size, size)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False

    def handle_input(self, keys) -> None:
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False

    def update(self) -> None:
        # Гравитация
        self.vel_y += GRAVITY

        # Горизонталь
        self.rect.x += int(self.vel_x)

        # Вертикаль
        self.rect.y += int(self.vel_y)

        # Коллизия с "землёй" (пока простая, потом заменим на платформы)
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)
