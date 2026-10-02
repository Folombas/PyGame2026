"""Игрок: физика суши + вода (плавание, утопление), лодка."""
import pygame
from settings import GRAVITY, PLAYER_SPEED, JUMP_POWER
from pixel_art import build_sprite, PLAYER_SPRITES, PLAYER_PALETTE
from sounds import play as play_sound
from blocks import TILE_SIZE, AIR, WATER


class Player:
    def __init__(self, x: int, y: int, size: int = 32):
        self.rect = pygame.Rect(x, y, size, size)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.jump_held = False

        self.sprites = {}
        for name, pattern in PLAYER_SPRITES.items():
            self.sprites[name] = {
                "right": build_sprite(pattern, PLAYER_PALETTE, scale=3, flip_x=False),
                "left":  build_sprite(pattern, PLAYER_PALETTE, scale=3, flip_x=True),
            }

        self.state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0

        # --- вода ---
        self.in_water = False
        self.head_in_water = False
        self.oxygen = 100          # 0..100
        self.has_scuba = False
        self.in_boat = False

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

        if self.in_water:
            # в воде Space = плыть вверх
            self.jump_held = jump_pressed
        else:
            if jump_pressed and self.on_ground:
                self.vel_y = JUMP_POWER
                self.on_ground = False
                play_sound("jump")
            self.jump_held = jump_pressed

    # ---------- коллизии с тайлами ----------
    def _solid_at(self, world, tx, ty):
        bt = world.get_block(tx, ty)
        return bt != AIR and bt != WATER

    def _resolve_x(self, world):
        self.rect.x += int(self.vel_x)
        tx0 = self.rect.left // TILE_SIZE
        ty0 = self.rect.top // TILE_SIZE
        tx1 = (self.rect.right - 1) // TILE_SIZE
        ty1 = (self.rect.bottom - 1) // TILE_SIZE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if not self._solid_at(world, tx, ty):
                    continue
                br = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not self.rect.colliderect(br):
                    continue
                overlap_y = min(self.rect.bottom, br.bottom) - max(self.rect.top, br.top)
                if overlap_y <= 4:
                    continue
                if self.vel_x > 0:
                    self.rect.right = br.left
                elif self.vel_x < 0:
                    self.rect.left = br.right

    def _resolve_y(self, world):
        self.on_ground = False
        self.rect.y += int(self.vel_y)
        tx0 = self.rect.left // TILE_SIZE
        ty0 = self.rect.top // TILE_SIZE
        tx1 = (self.rect.right - 1) // TILE_SIZE
        ty1 = (self.rect.bottom - 1) // TILE_SIZE
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if not self._solid_at(world, tx, ty):
                    continue
                br = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not self.rect.colliderect(br):
                    continue
                if self.vel_y > 0:
                    self.rect.bottom = br.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = br.bottom
                    self.vel_y = 0

    # ---------- вода ----------
    def _check_water(self, world):
        """Определяем: тело в воде? голова под водой?"""
        cx = self.rect.centerx // TILE_SIZE
        cy_body = self.rect.centery // TILE_SIZE
        cy_head = (self.rect.top + 4) // TILE_SIZE
        self.in_water = (world.get_block(cx, cy_body) == WATER)
        self.head_in_water = (world.get_block(cx, cy_head) == WATER)

    def update(self, world) -> None:
        self._check_water(world)

        if self.in_water:
            # --- ПЛАВАНИЕ ---
            # гравитация слабая, максимальная скорость падения низкая
            self.vel_y += GRAVITY * 0.18
            self.vel_y = min(self.vel_y, 2.0)
            # всплытие при удержании Space
            if self.jump_held:
                self.vel_y -= 0.55
                self.vel_y = max(self.vel_y, -2.6)
            # горизонтальное сопротивление
            self.vel_x *= 0.92
        else:
            # --- СУША ---
            if self.jump_held and self.vel_y < 0:
                self.vel_y += GRAVITY * 0.45
            else:
                self.vel_y += GRAVITY
            self.vel_y = min(self.vel_y, 20)

        self._resolve_x(world)
        self._resolve_y(world)

        # --- кислород ---
        if self.head_in_water and not self.has_scuba:
            self.oxygen -= 0.8
            if self.oxygen <= 0:
                self.oxygen = 0
                # утопление — урон раз в ~1.5 сек
                if not hasattr(self, "_drown_tick"):
                    self._drown_tick = 0
                self._drown_tick += 1
                if self._drown_tick % 90 == 0:
                    if hasattr(self, "on_drown"):
                        self.on_drown()
        else:
            # восстанавливаем кислород (даже если на воздухе)
            self.oxygen = min(100, self.oxygen + 1.2)

        # --- анимация ---
        if self.in_water:
            self.state = "swim"
        elif not self.on_ground:
            self.state = "jump"
        elif self.vel_x != 0:
            self.state = "walk"
        else:
            self.state = "idle"

        if self.state in ("walk", "swim"):
            self.anim_timer += 1
            if self.anim_timer >= 8:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_timer = 0
            self.anim_frame = 0

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.state == "walk":
            name = "walk_1" if self.anim_frame == 0 else "walk_2"
        elif self.state == "swim":
            name = "walk_1" if self.anim_frame == 0 else "walk_2"
        else:
            name = self.state
        direction = "right" if self.facing_right else "left"
        img = self.sprites[name][direction]
        r = img.get_rect()
        r.midbottom = (self.rect.midbottom[0] - offset_x,
                       self.rect.midbottom[1] - offset_y)
        surface.blit(img, r)
