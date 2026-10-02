"""Подводный мир: 4 вида рыб, черепахи, морские коньки, акулы, водоросли, кораллы."""
import math
import random
import pygame
from blocks import TILE_SIZE, WATER, AIR


# ============ РЫБЫ (4 вида) ============
FISH_TYPES = {
    "red":    {"body": (240, 120, 80),  "fin": (200, 80, 60),  "size": (24, 16), "speed": 1.2, "pattern": None},
    "blue":   {"body": (80, 160, 240),  "fin": (50, 110, 200), "size": (20, 14), "speed": 1.6, "pattern": "stripes"},
    "yellow": {"body": (250, 220, 90),  "fin": (230, 180, 50), "size": (22, 18), "speed": 1.0, "pattern": "spots"},
    "glow":   {"body": (140, 240, 200), "fin": (100, 200, 160), "size": (18, 12), "speed": 0.9, "pattern": "glow"},
}


class Fish:
    def __init__(self, x, y, kind=None):
        self.kind = kind or random.choice(list(FISH_TYPES.keys()))
        info = FISH_TYPES[self.kind]
        w, h = info["size"]
        self.rect = pygame.Rect(x, y, w, h)
        self.spawn_x = x
        self.spawn_y = y
        base_speed = info["speed"]
        self.vel_x = random.choice([-base_speed, base_speed]) * random.uniform(0.7, 1.4)
        self.alive = True
        self.timer = random.uniform(0, 6.28)
        self.range = random.randint(80, 220)

    def update(self, world):
        if not self.alive:
            return
        self.timer += 0.05
        self.rect.x += int(self.vel_x)
        if abs(self.rect.centerx - self.spawn_x) > self.range:
            self.vel_x = -self.vel_x
        self.rect.y = self.spawn_y + int(math.sin(self.timer) * 8)
        tx = (self.rect.centerx + (10 if self.vel_x > 0 else -10)) // TILE_SIZE
        ty = self.rect.centery // TILE_SIZE
        if world.get_block(tx, ty) != WATER:
            self.vel_x = -self.vel_x

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if not self.alive:
            return
        if world is not None:
            tx = self.rect.centerx // TILE_SIZE
            ty = self.rect.centery // TILE_SIZE
            if world.get_block(tx, ty) != WATER:
                return
        info = FISH_TYPES[self.kind]
        body_col = info["body"]
        fin_col = info["fin"]
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.rect.w, self.rect.h
        right = self.vel_x > 0

        # свечение
        if self.kind == "glow":
            glow_a = 100 + int(50 * math.sin(self.timer * 2))
            glow = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*body_col, glow_a // 3), ((w + 24) // 2, (h + 24) // 2), (w + 24) // 2)
            surface.blit(glow, (x - 12, y - 12))

        # тело
        pygame.draw.ellipse(surface, body_col, (x, y + 2, w - 6, h - 4))

        # узоры
        if info["pattern"] == "stripes":
            for i in range(3):
                sx = x + 4 + i * 5
                pygame.draw.line(surface, fin_col, (sx, y + 3), (sx, y + h - 3), 2)
        elif info["pattern"] == "spots":
            for dx, dy in [(4, 4), (10, 8), (8, 2)]:
                pygame.draw.circle(surface, fin_col, (x + dx, y + dy), 2)

        # хвост
        if right:
            pygame.draw.polygon(surface, fin_col, [(x, y + h // 2), (x - 6, y + 2), (x - 6, y + h - 2)])
            eye_x = x + w - 8
        else:
            pygame.draw.polygon(surface, fin_col, [(x + w - 4, y + h // 2), (x + w + 2, y + 2), (x + w + 2, y + h - 2)])
            eye_x = x + 4

        # глаз
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + h // 2), 3)
        pygame.draw.circle(surface, (20, 20, 20), (eye_x, y + h // 2), 2)


# ============ ЧЕРЕПАХА ============
class Turtle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 32)
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = random.choice([-0.8, -0.5, 0.5, 0.8])
        self.alive = True
        self.timer = random.uniform(0, 6.28)
        self.range = random.randint(150, 300)

    def update(self, world):
        if not self.alive:
            return
        self.timer += 0.03
        self.rect.x += int(self.vel_x)
        if abs(self.rect.centerx - self.spawn_x) > self.range:
            self.vel_x = -self.vel_x
        self.rect.y = self.spawn_y + int(math.sin(self.timer) * 12)
        tx = (self.rect.centerx + (15 if self.vel_x > 0 else -15)) // TILE_SIZE
        ty = self.rect.centery // TILE_SIZE
        if world.get_block(tx, ty) != WATER:
            self.vel_x = -self.vel_x

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if not self.alive:
            return
        if world is not None:
            tx = self.rect.centerx // TILE_SIZE
            ty = self.rect.centery // TILE_SIZE
            if world.get_block(tx, ty) != WATER:
                return
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.rect.w, self.rect.h
        right = self.vel_x > 0

        # плавники/лапы
        pygame.draw.ellipse(surface, (60, 120, 80), (x + 2, y + h - 8, 8, 6))
        pygame.draw.ellipse(surface, (60, 120, 80), (x + w - 10, y + h - 8, 8, 6))
        # голова
        head_x = x + w - 8 if right else x
        pygame.draw.circle(surface, (100, 170, 120), (head_x + 4, y + 8), 8)
        pygame.draw.circle(surface, (20, 20, 20), (head_x + (6 if right else 2), y + 6), 2)
        # панцирь
        pygame.draw.ellipse(surface, (50, 110, 70), (x + 4, y + 2, w - 10, h - 4))
        pygame.draw.ellipse(surface, (80, 150, 100), (x + 6, y + 4, w - 14, h - 8))
        # линии на панцире
        for i in range(3):
            cx = x + 8 + i * 8
            pygame.draw.line(surface, (40, 90, 60), (cx, y + 5), (cx, y + h - 5), 1)


# ============ МОРСКОЙ КОНЁК ============
class Seahorse:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 14, 32)
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = random.choice([-0.4, 0.4])
        self.vel_y = 0.0
        self.alive = True
        self.timer = random.uniform(0, 6.28)
        self.range = random.randint(60, 140)
        self.color = random.choice([
            (240, 200, 100), (240, 130, 200), (120, 200, 240), (200, 240, 140),
        ])

    def update(self, world):
        if not self.alive:
            return
        self.timer += 0.05
        self.rect.x += int(self.vel_x)
        if abs(self.rect.centerx - self.spawn_x) > self.range:
            self.vel_x = -self.vel_x
        # морской конёк стоит вертикально и качается
        self.rect.y = self.spawn_y + int(math.sin(self.timer) * 10)

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if not self.alive:
            return
        if world is not None:
            tx = self.rect.centerx // TILE_SIZE
            ty = self.rect.centery // TILE_SIZE
            if world.get_block(tx, ty) != WATER:
                return
        x = self.rect.x - offset_x + self.rect.w // 2
        y = self.rect.y - offset_y
        # хвост
        for i in range(6):
            tx = x + int(math.sin(self.timer + i * 0.4) * 2)
            ty = y + self.rect.h - i * 3
            pygame.draw.circle(surface, self.color, (tx, ty), max(1, 3 - i // 2))
        # тело
        pygame.draw.ellipse(surface, self.color, (x - 4, y + 8, 8, 16))
        # голова
        pygame.draw.circle(surface, self.color, (x, y + 6), 5)
        # рыльце
        pygame.draw.rect(surface, self.color, (x, y + 4, 8, 3))
        # плавник
        pygame.draw.polygon(surface, (*self.color, 180), [
            (x + 4, y + 12), (x + 9, y + 14), (x + 4, y + 18)])
        # глаз
        pygame.draw.circle(surface, (255, 255, 255), (x + 1, y + 5), 2)
        pygame.draw.circle(surface, (20, 20, 20), (x + 1, y + 5), 1)


# ============ АКУЛА ============
class Shark:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 64, 28)
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = random.choice([-1.8, 1.8])
        self.vel_y = 0.0
        self.alive = True
        self.timer = 0.0
        self.chase_timer = 0
        self.aggro = False
        self.damage_cooldown = 0

    def update(self, world, player):
        if not self.alive:
            return
        self.timer += 0.05
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

        # агро: если игрок в воде и ближе 400px
        px, py = player.rect.centerx, player.rect.centery
        dx = px - self.rect.centerx
        dy = py - self.rect.centery
        dist = math.hypot(dx, dy)

        if player.in_water and dist < 400:
            self.aggro = True
            self.chase_timer = 90
        elif self.chase_timer > 0:
            self.chase_timer -= 1
            if self.chase_timer <= 0:
                self.aggro = False

        if self.aggro:
            spd = 2.4
            if dist > 1:
                self.vel_x = dx / dist * spd
                self.vel_y = dy / dist * spd
        else:
            # патруль
            self.vel_x = 1.4 if self.vel_x >= 0 else -1.4
            self.vel_y = math.sin(self.timer) * 0.6

        # движение с проверкой воды
        nx = self.rect.x + int(self.vel_x)
        ny = self.rect.y + int(self.vel_y)
        tx = nx // TILE_SIZE
        ty = (ny + self.rect.h // 2) // TILE_SIZE
        if world.get_block(tx, ty) == WATER:
            self.rect.x = nx
            self.rect.y = ny
        else:
            self.vel_x = -self.vel_x
            self.vel_y = -self.vel_y

        # столкновение с игроком
        if self.damage_cooldown == 0 and self.rect.colliderect(player.rect):
            self.damage_cooldown = 120
            if hasattr(player, "on_shark_bite"):
                player.on_shark_bite()

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if not self.alive:
            return
        if world is not None:
            tx = self.rect.centerx // TILE_SIZE
            ty = self.rect.centery // TILE_SIZE
            if world.get_block(tx, ty) != WATER:
                return
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.rect.w, self.rect.h
        right = self.vel_x > 0

        body = (110, 130, 160)
        dark = (70, 85, 110)

        # тело
        pygame.draw.ellipse(surface, body, (x, y + 4, w - 10, h - 8))
        # брюхо
        pygame.draw.ellipse(surface, (200, 210, 220), (x + 8, y + h - 14, w - 24, 8))
        # плавник спинной
        pygame.draw.polygon(surface, dark, [
            (x + w // 2 - 4, y + 4),
            (x + w // 2 + 4, y - 6),
            (x + w // 2 + 10, y + 4),
        ])
        # хвост
        if right:
            pygame.draw.polygon(surface, dark, [
                (x, y + h // 2),
                (x - 12, y + 2),
                (x - 8, y + h // 2),
                (x - 12, y + h - 2),
            ])
            eye_x = x + w - 14
            mouth_x = x + w - 6
        else:
            pygame.draw.polygon(surface, dark, [
                (x + w - 4, y + h // 2),
                (x + w + 8, y + 2),
                (x + w + 4, y + h // 2),
                (x + w + 8, y + h - 2),
            ])
            eye_x = x + 8
            mouth_x = x + 2

        # глаз
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 10), 3)
        pygame.draw.circle(surface, (10, 10, 10), (eye_x, y + 10), 2)
        # пасть
        pygame.draw.line(surface, (60, 40, 40), (mouth_x, y + 16), (mouth_x + (8 if right else -8), y + 16), 2)

        # агро — красное свечение
        if self.aggro:
            glow = pygame.Surface((w + 30, h + 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (240, 60, 60, 80), ((w + 30) // 2, (h + 30) // 2), (w + 30) // 2)
            surface.blit(glow, (x - 15, y - 15))


# ============ ВОДОРОСЛИ ============
class Seaweed:
    def __init__(self, x, y, height=None):
        self.x = x
        self.y = y
        self.height = height or random.randint(20, 56)
        self.timer = random.uniform(0, 6.28)
        self.segments = max(3, self.height // 8)

    def update(self):
        self.timer += 0.04

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if world is not None:
            tx = self.x // TILE_SIZE
            ty = (self.y - 4) // TILE_SIZE
            if world.get_block(tx, ty) != WATER:
                return
        sx = self.x - offset_x
        sy = self.y - offset_y
        col = (40, 160, 90)
        col2 = (70, 200, 120)
        seg_h = self.height / self.segments
        for i in range(self.segments):
            t = i / self.segments
            sway = math.sin(self.timer + i * 0.5) * (2 + t * 4)
            px = sx + sway
            py = sy - i * seg_h
            pygame.draw.circle(surface, col, (int(px), int(py)), 3)
            pygame.draw.circle(surface, col2, (int(px) - 1, int(py) - 1), 1)


# ============ КОРАЛЛ ============
class Coral:
    PALETTES = [
        ((240, 100, 160), (255, 160, 200)),
        ((255, 180, 80), (255, 220, 140)),
        ((160, 100, 240), (200, 160, 255)),
        ((240, 90, 90), (255, 140, 140)),
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.col, self.col2 = random.choice(self.PALETTES)
        self.branches = []
        for _ in range(random.randint(2, 4)):
            angle = random.uniform(-0.9, 0.9)
            length = random.randint(10, 22)
            self.branches.append((angle, length))
        self.timer = random.uniform(0, 6.28)

    def update(self):
        self.timer += 0.03

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if world is not None:
            tx = self.x // TILE_SIZE
            ty = (self.y - 4) // TILE_SIZE
            if world.get_block(tx, ty) != WATER:
                return
        sx = self.x - offset_x
        sy = self.y - offset_y
        pygame.draw.rect(surface, self.col, (sx - 2, sy - 10, 4, 12))
        for ang, ln in self.branches:
            ex = sx + int(math.sin(ang) * ln)
            ey = sy - 10 - int(math.cos(ang) * ln * 0.8)
            pygame.draw.line(surface, self.col, (sx, sy - 8), (ex, ey), 3)
            pygame.draw.circle(surface, self.col2, (ex, ey), 3)
        glow_a = 60 + int(40 * math.sin(self.timer))
        glow = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.col2, glow_a), (15, 15), 12)
        surface.blit(glow, (sx - 15, sy - 20))
