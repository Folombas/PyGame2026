"""Враг — патрулирует платформу, разворачивается на краю."""
import pygame
from settings import GRAVITY, ENEMY_SPEED
from pixel_art import build_sprite, ENEMY_SPRITES, ENEMY_PALETTE


class Enemy:
    def __init__(self, x: int, y: int, w: int = 28, h: int = 28):
        self.rect = pygame.Rect(x, y, w, h)
        self.vel_x = ENEMY_SPEED
        self.vel_y = 0.0
        self.alive = True
        self.on_ground = False
        self.facing_right = True

        self.sprites = {}
        for name, pattern in ENEMY_SPRITES.items():
            self.sprites[name] = {
                "right": build_sprite(pattern, ENEMY_PALETTE, scale=3, flip_x=False),
                "left":  build_sprite(pattern, ENEMY_PALETTE, scale=3, flip_x=True),
            }

        self.anim_frame = 0
        self.anim_timer = 0

    def _ground_ahead(self, platforms) -> bool:
        probe_x = self.rect.right + 2 if self.vel_x > 0 else self.rect.left - 4
        probe = pygame.Rect(probe_x, self.rect.bottom + 2, 2, 4)
        return any(probe.colliderect(p.rect) for p in platforms)

    def _wall_ahead(self, platforms) -> bool:
        probe_x = self.rect.right + 2 if self.vel_x > 0 else self.rect.left - 4
        probe = pygame.Rect(probe_x, self.rect.y, 2, self.rect.h)
        return any(probe.colliderect(p.rect) for p in platforms)

    def update(self, platforms) -> None:
        if not self.alive:
            return

        self.vel_y = min(self.vel_y + GRAVITY, 20)

        self.rect.x += int(self.vel_x)
        if self._wall_ahead(platforms):
            self.rect.x -= int(self.vel_x)
            self.vel_x = -self.vel_x

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

        if self.on_ground and not self._ground_ahead(platforms):
            self.rect.x -= int(self.vel_x)
            self.vel_x = -self.vel_x

        self.facing_right = self.vel_x > 0

        # анимация — медленнее, чем у игрока
        self.anim_timer += 1
        if self.anim_timer >= 14:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

    def draw(self, surface: pygame.Surface, offset_x: int = 0) -> None:
        if not self.alive:
            return
        name = "walk_1" if self.anim_frame == 0 else "walk_2"
        direction = "right" if self.facing_right else "left"
        img = self.sprites[name][direction]

        r = img.get_rect()
        r.midbottom = self.rect.midbottom
        r.x -= offset_x
        surface.blit(img, r)
