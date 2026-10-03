"""Top-down игрок."""
import pygame
from settings import *
from sprites import get_player_sprite


class PlayerTD:
    SPEED = 3.0

    def __init__(self, tx, ty):
        self.x = float(tx * TILE)
        self.y = float(ty * TILE)
        self.w = 20
        self.h = 28
        self.direction = "down"
        self.anim_frame = 0
        self.anim_timer = 0
        self.moving = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, keys, can_walk_fn):
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1

        # Направление
        if dx < 0: self.direction = "left"
        elif dx > 0: self.direction = "right"
        elif dy < 0: self.direction = "up"
        elif dy > 0: self.direction = "down"

        self.moving = (dx != 0 or dy != 0)

        if self.moving:
            import math
            l = math.hypot(dx, dy)
            dx, dy = dx / l, dy / l

            # Двигаем по осям раздельно для скольжения
            nx = self.x + dx * self.SPEED
            if can_walk_fn(int(nx), int(self.y), self.w, self.h):
                self.x = nx
            ny = self.y + dy * self.SPEED
            if can_walk_fn(int(self.x), int(ny), self.w, self.h):
                self.y = ny

            # Анимация
            self.anim_timer += 1
            if self.anim_timer >= 8:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_frame = 0
            self.anim_timer = 0

    def draw(self, screen, offset_x, offset_y):
        sprite = get_player_sprite(self.direction, self.anim_frame)
        sx = self.x - offset_x + (self.w - sprite.get_width()) // 2
        sy = self.y - offset_y + (self.h - sprite.get_height())
        # тень
        pygame.draw.ellipse(screen, (0, 0, 0, 60),
                            (self.x - offset_x, self.y - offset_y + self.h - 4, self.w, 6))
        screen.blit(sprite, (sx, sy))
