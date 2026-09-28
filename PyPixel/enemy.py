"""Враг — патрулирует платформу, разворачивается на краю."""
import pygame
from settings import ENEMY_COLOR, ENEMY_SPEED, GRAVITY


class Enemy:
    def __init__(self, x: int, y: int, w: int = 28, h: int = 28):
        self.rect = pygame.Rect(x, y, w, h)
        self.vel_x = ENEMY_SPEED
        self.vel_y = 0.0

    def _ground_ahead(self, platforms) -> bool:
        """Есть ли платформа прямо под 'передним' краем врага."""
        probe_x = self.rect.right + 2 if self.vel_x > 0 else self.rect.left - 4
        probe = pygame.Rect(probe_x, self.rect.bottom + 2, 2, 4)
        return any(probe.colliderect(p.rect) for p in platforms)

    def _wall_ahead(self, platforms) -> bool:
        """Есть ли стена прямо перед врагом."""
        probe_x = self.rect.right + 2 if self.vel_x > 0 else self.rect.left - 4
        probe = pygame.Rect(probe_x, self.rect.y, 2, self.rect.h)
        return any(probe.colliderect(p.rect) for p in platforms)

    def update(self, platforms) -> None:
        # гравитация
        self.vel_y = min(self.vel_y + GRAVITY, 20)

        # движение по X
        self.rect.x += int(self.vel_x)

        # разворот у стены
        if self._wall_ahead(platforms):
            self.rect.x -= int(self.vel_x)
            self.vel_x = -self.vel_x

        # движение по Y
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

        # разворот на краю (только когда стоим на платформе)
        if self.on_ground and not self._ground_ahead(platforms):
            self.rect.x -= int(self.vel_x)
            self.vel_x = -self.vel_x

    def draw(self, surface: pygame.Surface, offset_x: int = 0) -> None:
        r = self.rect.move(-offset_x, 0)
        pygame.draw.rect(surface, ENEMY_COLOR, r)
        # «глаз» — чтобы видеть направление
        eye_x = r.x + (r.w - 8 if self.vel_x > 0 else 4)
        pygame.draw.rect(surface, (255, 255, 255), (eye_x, r.y + 6, 4, 4))
