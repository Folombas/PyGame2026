"""Ферма: коровы и морковь."""
import math
import random
import pygame
from blocks import TILE_SIZE


# ==================== КОРОВА ====================
class Cow:
    W, H = 56, 40

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.W, self.H)
        self.home_x = x
        self.vel_x = random.choice([-0.4, -0.3, 0.3, 0.4])
        self.timer = random.uniform(0, 6.28)
        self.range = 80
        self.anim_frame = 0
        self.anim_timer = 0
        self.moo_timer = random.randint(200, 500)
        self.is_mooing = False

    def update(self, world=None):
        self.timer += 0.04
        self.rect.x += int(self.vel_x)
        if abs(self.rect.centerx - self.home_x) > self.range:
            self.vel_x = -self.vel_x
        # анимация ходьбы
        self.anim_timer += 1
        if self.anim_timer >= 20:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2
        # мычание
        self.moo_timer -= 1
        if self.moo_timer <= 0:
            self.is_mooing = True
            self.moo_timer = random.randint(240, 600)
        if self.is_mooing:
            if self.moo_timer < 240 and self.moo_timer % 30 == 0:
                self.is_mooing = False

    def draw(self, surface, offset_x=0, offset_y=0):
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.W, self.H
        facing = 1 if self.vel_x > 0 else -1

        # тень
        pygame.draw.ellipse(surface, (0, 0, 0, 60), (x + 4, y + h - 4, w - 8, 6))

        # ноги
        leg_off = 2 if self.anim_frame else -2
        for i, lx in enumerate([6, 16, w - 22, w - 12]):
            dy = leg_off if i % 2 == 0 else -leg_off
            pygame.draw.rect(surface, (40, 40, 40), (x + lx, y + h - 10 + dy, 6, 10))

        # тело — белое с чёрными пятнами
        body = (240, 240, 235)
        body_shadow = (200, 200, 195)
        pygame.draw.ellipse(surface, body, (x + 4, y + 8, w - 8, h - 14))
        pygame.draw.ellipse(surface, body_shadow, (x + 4, y + h - 14, w - 8, 6))
        # контур
        pygame.draw.ellipse(surface, (60, 60, 60), (x + 4, y + 8, w - 8, h - 14), 1)

        # пятна
        spots = [(12, 14, 6, 5), (26, 12, 8, 6), (40, 16, 5, 4), (18, 22, 7, 5)]
        for sx, sy, sw, sh in spots:
            pygame.draw.ellipse(surface, (30, 30, 30), (x + sx, y + sy, sw, sh))

        # голова — спереди или сзади
        head_x = x + w - 18 if facing > 0 else x + 2
        # морда
        pygame.draw.ellipse(surface, body, (head_x, y + 6, 18, 20))
        pygame.draw.ellipse(surface, (60, 60, 60), (head_x, y + 6, 18, 20), 1)
        # нос
        nose_x = head_x + 10 if facing > 0 else head_x + 4
        pygame.draw.ellipse(surface, (240, 180, 200), (nose_x, y + 16, 8, 6))
        # глаз
        eye_x = head_x + 8 if facing > 0 else head_x + 6
        pygame.draw.circle(surface, (20, 20, 20), (eye_x, y + 12), 2)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x - 1, y + 11), 1)
        # рога
        pygame.draw.line(surface, (200, 180, 140),
                         (head_x + 4, y + 6), (head_x + 2, y + 2), 2)
        pygame.draw.line(surface, (200, 180, 140),
                         (head_x + 14, y + 6), (head_x + 16, y + 2), 2)

        # хвост
        tail_x = x + 2 if facing > 0 else x + w - 4
        pygame.draw.line(surface, (60, 40, 30),
                         (tail_x, y + 14),
                         (tail_x + (-1 if facing > 0 else 1) * 3, y + 4 + int(math.sin(self.timer * 2) * 2)), 2)
        # кисточка
        pygame.draw.circle(surface, (80, 50, 30),
                          (tail_x + (-1 if facing > 0 else 1) * 3,
                           y + 4 + int(math.sin(self.timer * 2) * 2)), 2)

        # мычание
        if self.is_mooing:
            mu = pygame.font.SysFont("monospace", 14, bold=True).render("Му!", True, (255, 240, 130))
            surface.blit(mu, (x + w // 2 - mu.get_width() // 2, y - 16))


# ==================== МОРКОВЬ ====================
CARROT_STAGES = ["seed", "sprout", "half", "ready"]
CARROT_GROW_TIME = [120, 180, 240]   # кадров между стадиями


class Carrot:
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty
        self.stage = 0
        self.timer = random.randint(0, 60)   # небольшая задержка
        self.ready = False

    def update(self):
        if self.stage >= 3:
            self.ready = True
            return
        self.timer += 1
        if self.timer >= CARROT_GROW_TIME[self.stage]:
            self.stage += 1
            self.timer = 0
            if self.stage >= 3:
                self.ready = True

    def draw(self, surface, offset_x=0, offset_y=0):
        cx = self.tx * TILE_SIZE + TILE_SIZE // 2 - offset_x
        cy = self.ty * TILE_SIZE + TILE_SIZE // 2 - offset_y

        # земля под грядкой — темнее
        pygame.draw.rect(surface, (90, 55, 45),
                         (cx - 14, cy + 4, 28, 10))
        pygame.draw.line(surface, (60, 35, 25), (cx - 14, cy + 4), (cx + 14, cy + 4), 2)

        if self.stage == 0:
            # семечко — точка
            pygame.draw.circle(surface, (150, 110, 60), (cx, cy + 6), 2)
        elif self.stage == 1:
            # росток
            pygame.draw.line(surface, (80, 180, 90), (cx, cy + 6), (cx, cy - 4), 2)
            pygame.draw.line(surface, (80, 180, 90), (cx, cy), (cx - 4, cy - 3), 1)
            pygame.draw.line(surface, (80, 180, 90), (cx, cy), (cx + 4, cy - 3), 1)
        elif self.stage == 2:
            # зелёный кустик, морковь видна наполовину
            pygame.draw.line(surface, (60, 160, 70), (cx, cy + 6), (cx, cy - 8), 2)
            for dx, dy in [(-6, 0), (6, 0), (-5, -6), (5, -6), (0, -10)]:
                pygame.draw.line(surface, (80, 200, 90),
                                 (cx, cy - 4), (cx + dx, cy + dy), 2)
            # морковка чуть видна
            pygame.draw.ellipse(surface, (240, 140, 60), (cx - 4, cy + 2, 8, 6))
        else:
            # готовая — оранжевая морковка + большая зелень
            for dx, dy in [(-8, -2), (8, -2), (-6, -8), (6, -8), (0, -12), (-3, -14), (3, -14)]:
                pygame.draw.line(surface, (60, 180, 80),
                                 (cx, cy - 6), (cx + dx, cy + dy), 2)
            # морковка
            carrot_pts = [
                (cx - 5, cy + 4),
                (cx + 5, cy + 4),
                (cx, cy + 12),
            ]
            pygame.draw.polygon(surface, (240, 120, 40), carrot_pts)
            pygame.draw.polygon(surface, (180, 80, 20), carrot_pts, 1)
            # блик
            pygame.draw.line(surface, (255, 200, 150), (cx - 2, cy + 5), (cx - 2, cy + 9), 1)
            # свечение готовности
            pulse = abs(math.sin(self.timer * 0.1))
            if int(self.timer) % 30 < 15:
                glow = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 200, 100, 60), (20, 20), 18)
                surface.blit(glow, (cx - 20, cy - 20))
