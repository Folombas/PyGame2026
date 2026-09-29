"""Игрок."""
import pygame
from settings import GRAVITY, PLAYER_SPEED, JUMP_POWER
from pixel_art import build_sprite, PLAYER_SPRITES, PLAYER_PALETTE


class Player:
    def __init__(self, x: int, y: int, size: int = 32):
        self.rect = pygame.Rect(x, y, size, size)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True

        # Собираем все спрайты по одному разу
        self.sprites = {}
        for name, pattern in PLAYER_SPRITES.items():
            self.sprites[name] = {
                "right": build_sprite(pattern, PLAYER_PALETTE, scale=3, flip_x=False),
                "left":  build_sprite(pattern, PLAYER_PALETTE, scale=3, flip_x=True),
            }

        self.state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0

    def handle_input(self, keys) -> None:
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False

    def update(self, platforms) -> None:
        # --- физика ---
        self.vel_y += GRAVITY
        self.vel_y = min(self.vel_y, 20)

        self.rect.x += int(self.vel_x)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left
                elif self.vel_x < 0:
                    self.rect.left = p.rect.right

        self.on_ground = False
        self.rect.y += int(self.vel_y)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

        # --- анимация ---
        if not self.on_ground:
            self.state = "jump"
        elif self.vel_x != 0:
            self.state = "walk"
        else:
            self.state = "idle"

        if self.state == "walk":
            self.anim_timer += 1
            if self.anim_timer >= 8:      # кадр каждые 8 тиков (~7.5 FPS при 60)
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_timer = 0
            self.anim_frame = 0

    def draw(self, surface: pygame.Surface, offset_x: int = 0) -> None:
        if self.state == "walk":
            name = "walk_1" if self.anim_frame == 0 else "walk_2"
        else:
            name = self.state

        direction = "right" if self.facing_right else "left"
        img = self.sprites[name][direction]

        r = img.get_rect()
        r.midbottom = self.rect.midbottom
        r.x -= offset_x
        surface.blit(img, r)
