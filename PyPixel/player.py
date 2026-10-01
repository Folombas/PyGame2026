"""Игрок."""
import pygame
from settings import GRAVITY, PLAYER_SPEED, JUMP_POWER
from pixel_art import build_sprite, PLAYER_SPRITES, PLAYER_PALETTE
from sounds import play as play_sound


class Player:
    def __init__(self, x: int, y: int, size: int = 32):
        self.rect = pygame.Rect(x, y, size, size)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.jump_held = False

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
        jump_keys = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
        jump_pressed = any(keys[k] for k in jump_keys)
        if jump_pressed and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False
            play_sound("jump")
        self.jump_held = jump_pressed

    def update(self, platforms) -> None:
        # --- физика с variable jump ---
        # Если летим вверх И игрок держит прыжок → ослабляем гравитацию
        if self.jump_held and self.vel_y < 0:
            self.vel_y += GRAVITY * 0.45
        else:
            self.vel_y += GRAVITY
        self.vel_y = min(self.vel_y, 20)

        self.rect.x += int(self.vel_x)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                # Игрок стоит на этой платформе (касание сверху) —
                # это НЕ стена, не блокируем по X
                overlap_y = min(self.rect.bottom, p.rect.bottom) - max(self.rect.top, p.rect.top)
                if overlap_y <= 3:
                    continue
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

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.state == "walk":
            name = "walk_1" if self.anim_frame == 0 else "walk_2"
        else:
            name = self.state

        direction = "right" if self.facing_right else "left"
        img = self.sprites[name][direction]

        r = img.get_rect()
        r.midbottom = (self.rect.midbottom[0] - offset_x, self.rect.midbottom[1] - offset_y)
        surface.blit(img, r)
