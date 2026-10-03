"""Игрок: суша, вода (плавание), лодка."""
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
        self.oxygen = 100
        self.has_scuba = False

        # --- лодка ---
        self.in_boat = None      # ссылка на Boat если сидит
        self.in_submarine = None  # ссылка на Submarine если пилотирует

    def handle_input(self, keys) -> None:
        self.keys = keys
        # горизонталь
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True

        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        self.jump_held = jump_pressed

        if not self.in_water and not self.in_boat:
            if jump_pressed and self.on_ground:
                self.vel_y = JUMP_POWER
                self.on_ground = False
                play_sound("jump")

    # ---------- коллизии ----------
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

    def _check_water(self, world):
        cx = self.rect.centerx // TILE_SIZE
        cy_body = self.rect.centery // TILE_SIZE
        cy_head = (self.rect.top + 6) // TILE_SIZE
        self.in_water = (world.get_block(cx, cy_body) == WATER)
        self.head_in_water = (world.get_block(cx, cy_head) == WATER)

    def update(self, world) -> None:
        # --- БАТИСКАФ ---
        if self.in_submarine is not None:
            sub = self.in_submarine
            self.rect.midbottom = (sub.rect.centerx, sub.rect.top + 6)
            self.vel_x = 0
            self.vel_y = 0
            self.on_ground = True
            self.state = "idle"
            # кислород восстанавливается в батискафе
            self.oxygen = min(100, self.oxygen + 2.0)
            return

        # --- ЛОДКА ---
        if self.in_boat is not None:
            boat = self.in_boat
            # двигаем лодку, игрок следует
            keys = getattr(self, "keys", None)
            if keys:
                bx = 0
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    bx = -4.5
                    self.facing_right = False
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    bx = 4.5
                    self.facing_right = True
                boat.vel_x = bx * 0.15 + boat.vel_x * 0.85  # инерция
            boat.rect.x += int(boat.vel_x)
            # проверка что под лодкой вода
            cx = boat.rect.centerx // TILE_SIZE
            cy = boat.rect.bottom // TILE_SIZE
            if world.get_block(cx, cy) != WATER:
                # лодка на мели — выйти
                self.in_boat = None
                self.rect.midbottom = (boat.rect.centerx, boat.rect.top)
                self.in_water = False
                return
            # игрок стоит на лодке
            self.rect.midbottom = (boat.rect.centerx, boat.rect.top + 4)
            self.vel_x = 0
            self.vel_y = 0
            self.on_ground = True
            self.state = "idle"
            return

        self._check_water(world)

        if self.in_water:
            # --- ПЛАВАНИЕ ---
            keys = getattr(self, "keys", None)
            # Просто стоим в воде — не тонем
            self.vel_y *= 0.85   # затухание
            if keys:
                if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]:
                    # Сильное всплытие
                    self.vel_y = -4.5
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    # Ныряем
                    self.vel_y = 3.0
                else:
                    # Медленно тонем
                    self.vel_y += 0.15

            self.vel_y = max(-5.0, min(4.0, self.vel_y))
            self.vel_x *= 0.88

            # Выход из воды на берег: если сверху есть воздух и игрок жмёт прыжок
            if keys and (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]):
                # проверяем есть ли твёрдый блок прямо над водой
                cx = self.rect.centerx // TILE_SIZE
                head_ty = (self.rect.top - 4) // TILE_SIZE
                if world.get_block(cx, head_ty) == AIR:
                    # наверху воздух — выпрыгиваем
                    self.vel_y = JUMP_POWER
                    self.in_water = False
        else:
            if self.jump_held and self.vel_y < 0:
                self.vel_y += GRAVITY * 0.45
            else:
                self.vel_y += GRAVITY
            self.vel_y = min(self.vel_y, 20)

        self._resolve_x(world)
        self._resolve_y(world)

        # --- кислород ---
        if self.head_in_water and not self.has_scuba:
            self.oxygen -= 0.35
            if self.oxygen <= 0:
                self.oxygen = 0
                if not hasattr(self, "_drown_tick"):
                    self._drown_tick = 0
                self._drown_tick += 1
                if self._drown_tick % 90 == 0 and hasattr(self, "on_drown"):
                    self.on_drown()
        else:
            self.oxygen = min(100, self.oxygen + 1.5)

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
        if self.in_boat is not None:
            return  # на лодке — рисуется только лодка, но игрок всё равно виден
        if self.state == "walk" or self.state == "swim":
            name = "walk_1" if self.anim_frame == 0 else "walk_2"
        else:
            name = self.state
        direction = "right" if self.facing_right else "left"
        img = self.sprites[name][direction]
        r = img.get_rect()
        r.midbottom = (self.rect.midbottom[0] - offset_x,
                       self.rect.midbottom[1] - offset_y)
        surface.blit(img, r)
