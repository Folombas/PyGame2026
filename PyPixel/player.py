"""Игрок."""
import pygame
from settings import (
    PLAYER_COLOR, GRAVITY, PLAYER_SPEED, JUMP_POWER
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

    def update(self, platforms) -> None:
        # --- гравитация ---
        self.vel_y += GRAVITY
        # ограничим падение, чтобы не пролетать сквозь платформы
        self.vel_y = min(self.vel_y, 20)

        # --- движение по X и коллизии ---
        self.rect.x += int(self.vel_x)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:                # идём вправо — выталкиваем влево
                    self.rect.right = p.rect.left
                elif self.vel_x < 0:              # идём влево — выталкиваем вправо
                    self.rect.left = p.rect.right

        # --- движение по Y и коллизии ---
        self.on_ground = False
        self.rect.y += int(self.vel_y)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:                # падаем — стоим на платформе
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:              # летим вверх — бьёмся головой
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

        def draw(self, surface: pygame.Surface, offset_x: int = 0) -> None:
	        r = self.rect.move(-offset_x, 0)
        	pygame.draw.rect(surface, PLAYER_COLOR, r)
