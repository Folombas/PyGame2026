"""Враг — патрулирует, разворачивается на краю. Работает с World напрямую."""
import pygame
from settings import GRAVITY, ENEMY_SPEED
from pixel_art import build_sprite, ENEMY_SPRITES, ENEMY_PALETTE
from blocks import TILE_SIZE, AIR


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

    def _block_solid_at(self, world, px, py):
        """True если в мировой точке есть твёрдый блок."""
        tx = int(px) // TILE_SIZE
        ty = int(py) // TILE_SIZE
        return world.get_block(tx, ty) != AIR

    def _ground_ahead(self, world):
        probe_x = self.rect.right + 2 if self.vel_x > 0 else self.rect.left - 4
        return self._block_solid_at(world, probe_x, self.rect.bottom + 4)

    def _wall_ahead(self, world):
        probe_x = self.rect.right + 4 if self.vel_x > 0 else self.rect.left - 6
        return self._block_solid_at(world, probe_x, self.rect.centery)

    def update(self, world):
        """world — объект World с методом get_block(tx, ty)."""
        if not self.alive:
            return

        self.vel_y = min(self.vel_y + GRAVITY, 20)

        # X-движение
        self.rect.x += int(self.vel_x)
        if self._wall_ahead(world):
            self.rect.x -= int(self.vel_x)
            self.vel_x = -self.vel_x

        # Y-движение
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        # проверяем пересечение с тайлами
        if self._check_tile_collision(world, "y"):
            pass

        if self.on_ground and not self._ground_ahead(world):
            self.rect.x -= int(self.vel_x)
            self.vel_x = -self.vel_x

        self.facing_right = self.vel_x > 0

        self.anim_timer += 1
        if self.anim_timer >= 14:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

    def _check_tile_collision(self, world, axis):
        """Проверка и разрешение коллизии с тайлами."""
        tx0 = self.rect.left // TILE_SIZE
        ty0 = self.rect.top // TILE_SIZE
        tx1 = (self.rect.right - 1) // TILE_SIZE
        ty1 = (self.rect.bottom - 1) // TILE_SIZE
        collided = False
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if world.get_block(tx, ty) == AIR:
                    continue
                block_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE,
                                         TILE_SIZE, TILE_SIZE)
                if not self.rect.colliderect(block_rect):
                    continue
                collided = True
                if axis == "y":
                    if self.vel_y > 0:
                        self.rect.bottom = block_rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:
                        self.rect.top = block_rect.bottom
                        self.vel_y = 0
                elif axis == "x":
                    if self.vel_x > 0:
                        self.rect.right = block_rect.left
                    elif self.vel_x < 0:
                        self.rect.left = block_rect.right
        return collided

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.alive:
            return
        name = "walk_1" if self.anim_frame == 0 else "walk_2"
        direction = "right" if self.facing_right else "left"
        img = self.sprites[name][direction]
        r = img.get_rect()
        r.midbottom = (self.rect.midbottom[0] - offset_x,
                       self.rect.midbottom[1] - offset_y)
        surface.blit(img, r)
