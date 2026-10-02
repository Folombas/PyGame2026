"""Глубокий океан: руины Атлантиды, корабли, киты, большие акулы."""
import math
import random
import pygame
from blocks import TILE_SIZE, WATER, AIR


# ==================== ЗАТОНУВШИЙ КОРАБЛЬ ====================
class SunkenShip:
    def __init__(self, x, y, flip=False):
        self.rect = pygame.Rect(x, y, 140, 60)
        self.flip = flip
        self.tilt = random.uniform(-0.3, 0.3)

    def update(self, world):
        pass  # статичный

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        if self.flip:
            # отражённый корабль рисуем вручную зеркально
            self._draw_ship(surface, x + 140, y, mirror=True)
        else:
            self._draw_ship(surface, x, y, mirror=False)

    def _draw_ship(self, surface, x, y, mirror=False):
        wood = (90, 60, 40)
        wood_dark = (60, 40, 25)
        wood_light = (120, 85, 60)
        m = -1 if mirror else 1

        # корпус (наклонный)
        hull = [
            (x, y + 30),
            (x + 20 * m, y + 20),
            (x + 130 * m, y + 20),
            (x + 140 * m, y + 50),
            (x + 130 * m, y + 60),
            (x + 20 * m, y + 60),
            (x, y + 45),
        ]
        pygame.draw.polygon(surface, wood, hull)
        pygame.draw.polygon(surface, wood_dark, hull, 2)

        # доски
        for i in range(3):
            yy = y + 30 + i * 10
            pygame.draw.line(surface, wood_dark,
                             (x + 10 * m, yy), (x + 130 * m, yy), 1)

        # мачта
        mast_x = x + 80 * m
        pygame.draw.rect(surface, wood_dark, (mast_x - 2, y - 40, 4, 70))
        # рея
        pygame.draw.rect(surface, wood_dark, (mast_x - 30 * m, y - 30, 60, 3))

        # порванные паруса
        pygame.draw.polygon(surface, (200, 190, 170), [
            (mast_x, y - 28),
            (mast_x + 25 * m, y - 28),
            (mast_x + 20 * m, y - 5),
            (mast_x, y - 10),
        ])
        # дыры в парусе
        pygame.draw.circle(surface, (60, 40, 25), (mast_x + 12 * m, y - 18), 3)

        # водоросли на корпусе
        for i in range(3):
            wx = x + (30 + i * 35) * m
            pygame.draw.line(surface, (60, 140, 80), (wx, y + 20),
                             (wx + random.randint(-3, 3), y + 5), 2)

        # иллюминаторы
        for i in range(3):
            cx = x + (40 + i * 30) * m
            cy = y + 38
            pygame.draw.circle(surface, (40, 70, 100), (cx, cy), 5)
            pygame.draw.circle(surface, (90, 140, 170), (cx, cy), 5, 1)


# ==================== АНТИЧНАЯ КОЛОННА ====================
class Column:
    def __init__(self, x, y, height=None, broken=False):
        self.x = x
        self.y = y
        self.height = height or random.randint(40, 90)
        self.broken = broken
        self.tilt = random.uniform(-0.08, 0.08)

    def update(self, world):
        pass

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        sx = self.x - offset_x
        sy = self.y - offset_y
        marble = (220, 215, 200)
        marble_dark = (180, 175, 160)
        marble_shadow = (140, 135, 120)

        # база (стилобат)
        pygame.draw.rect(surface, marble_dark, (sx - 14, sy - 4, 28, 8))
        pygame.draw.rect(surface, marble_shadow, (sx - 14, sy + 2, 28, 2))

        # ствол колонны
        col_h = self.height if not self.broken else self.height // 2
        top_y = sy - col_h - 4

        # канавки (fluting)
        for i in range(4):
            fx = sx - 6 + i * 4
            pygame.draw.line(surface, marble_shadow, (fx, top_y + 4), (fx, sy - 4), 1)
        pygame.draw.rect(surface, marble, (sx - 8, top_y, 16, col_h))

        # капитель (верх)
        if not self.broken:
            pygame.draw.rect(surface, marble_dark, (sx - 12, top_y - 6, 24, 8))
            pygame.draw.rect(surface, marble, (sx - 14, top_y - 10, 28, 4))
            # волюты — завитушки
            pygame.draw.circle(surface, marble_shadow, (sx - 10, top_y - 4), 3, 1)
            pygame.draw.circle(surface, marble_shadow, (sx + 10, top_y - 4), 3, 1)
        else:
            # обломок — неровный верх
            pygame.draw.polygon(surface, marble_dark, [
                (sx - 8, top_y),
                (sx - 3, top_y - 4),
                (sx + 2, top_y + 2),
                (sx + 6, top_y - 2),
                (sx + 8, top_y),
            ])

        # водоросли снизу
        for i in range(2):
            wx = sx - 10 + i * 20
            pygame.draw.line(surface, (60, 140, 80), (wx, sy),
                             (wx + random.randint(-3, 3), sy - 8), 2)


# ==================== РУИНЫ ХРАМА ====================
class TempleRuin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.columns = []
        # ряд колонн 4-6 штук
        n = random.randint(4, 6)
        spacing = 50
        start = x - (n - 1) * spacing // 2
        for i in range(n):
            broken = random.random() < 0.4
            h = random.randint(50, 90) if not broken else random.randint(25, 45)
            self.columns.append(Column(start + i * spacing, y, h, broken))

        self.architrave_ok = random.random() > 0.5    # сохранилась ли балка

    def update(self, world):
        for c in self.columns:
            c.update(world)

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        # перекрытие (балка) — если сохранилось
        if self.architrave_ok and len(self.columns) >= 3:
            sx = self.columns[0].x - offset_x
            ex = self.columns[-1].x - offset_x
            sy = self.columns[0].y - offset_y - self.columns[0].height - 14
            pygame.draw.rect(surface, (200, 195, 180), (sx - 12, sy, ex - sx + 24, 10))
            pygame.draw.rect(surface, (160, 155, 140), (sx - 12, sy, ex - sx + 24, 2))
            pygame.draw.rect(surface, (140, 135, 120), (sx - 12, sy + 8, ex - sx + 24, 2))

        # колонны
        for c in self.columns:
            c.draw(surface, offset_x, offset_y, world)


# ==================== СТАТУЯ ПОСЕЙДОНА ====================
class PoseidonStatue:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = random.uniform(0, 6.28)

    def update(self, world):
        self.timer += 0.02

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        sx = self.x - offset_x
        sy = self.y - offset_y
        marble = (215, 210, 195)
        marble_dark = (170, 165, 150)

        # постамент
        pygame.draw.rect(surface, marble_dark, (sx - 35, sy - 10, 70, 14))
        pygame.draw.rect(surface, marble, (sx - 30, sy - 22, 60, 14))
        pygame.draw.rect(surface, marble_dark, (sx - 30, sy - 22, 60, 3))

        # тело (торс)
        body_y = sy - 22
        pygame.draw.ellipse(surface, marble, (sx - 20, body_y - 50, 40, 55))
        # руки
        # левая — держит трезубец
        pygame.draw.line(surface, marble, (sx - 15, body_y - 40),
                         (sx - 40, body_y - 55), 8)
        pygame.draw.line(surface, marble, (sx - 40, body_y - 55),
                         (sx - 45, body_y - 90), 6)
        # правая — опущена
        pygame.draw.line(surface, marble, (sx + 15, body_y - 40),
                         (sx + 38, body_y - 20), 8)

        # голова
        head_y = body_y - 70
        pygame.draw.circle(surface, marble, (sx, head_y), 16)
        # корона/лавровый венок
        pygame.draw.arc(surface, (200, 180, 90), (sx - 18, head_y - 16, 36, 20),
                        0, math.pi, 3)

        # длинная борода — волнистая
        for i in range(5):
            bx = sx - 10 + i * 5
            by = head_y + 14 + int(math.sin(self.timer + i * 0.6) * 2)
            pygame.draw.line(surface, marble_dark, (bx, by), (bx, by + 30), 3)
        # глаза
        pygame.draw.circle(surface, marble_dark, (sx - 5, head_y - 2), 2)
        pygame.draw.circle(surface, marble_dark, (sx + 5, head_y - 2), 2)

        # ТРЕЗУБЕЦ
        tx = sx - 45
        ty = body_y - 90
        # рукоять
        pygame.draw.rect(surface, (200, 180, 90), (tx - 2, ty - 60, 4, 60))
        # зубцы
        for i in range(3):
            zx = tx - 12 + i * 12
            pygame.draw.rect(surface, (200, 180, 90), (zx - 1, ty - 75, 2, 15))
            # наконечник (остр)
            pygame.draw.polygon(surface, (220, 200, 120), [
                (zx - 3, ty - 75), (zx + 3, ty - 75), (zx, ty - 82)])

        # водоросли на статуе
        pygame.draw.line(surface, (60, 140, 80), (sx - 12, sy - 20),
                         (sx - 16, sy - 2), 2)
        pygame.draw.line(surface, (60, 140, 80), (sx + 10, sy - 20),
                         (sx + 14, sy - 4), 2)


# ==================== КИТ ====================
class Whale:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 160, 70)
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = random.choice([-1.0, 1.0])
        self.timer = random.uniform(0, 6.28)
        self.range = 600
        self.alive = True

    def update(self, world):
        if not self.alive:
            return
        self.timer += 0.02
        self.rect.x += int(self.vel_x * 0.8)
        if abs(self.rect.centerx - self.spawn_x) > self.range:
            self.vel_x = -self.vel_x
        self.rect.y = self.spawn_y + int(math.sin(self.timer) * 20)

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if not self.alive:
            return
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.rect.w, self.rect.h
        right = self.vel_x > 0

        body = (60, 80, 120)
        belly = (140, 160, 200)
        dark = (35, 50, 80)

        # тело
        pygame.draw.ellipse(surface, body, (x + 10, y + 10, w - 20, h - 20))
        # брюхо
        pygame.draw.ellipse(surface, belly, (x + 15, y + h - 32, w - 30, 16))
        # полосы на брюхе
        for i in range(5):
            sx = x + 30 + i * 20
            pygame.draw.line(surface, dark, (sx, y + h - 28), (sx, y + h - 16), 1)

        # хвост — большой
        if right:
            pygame.draw.polygon(surface, dark, [
                (x + 5, y + h // 2),
                (x - 30, y + 5),
                (x - 22, y + h // 2),
                (x - 30, y + h - 5),
            ])
            eye_x = x + w - 25
        else:
            pygame.draw.polygon(surface, dark, [
                (x + w - 5, y + h // 2),
                (x + w + 30, y + 5),
                (x + w + 22, y + h // 2),
                (x + w + 30, y + h - 5),
            ])
            eye_x = x + 25

        # глаз
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 28), 4)
        pygame.draw.circle(surface, (10, 10, 10), (eye_x, y + 28), 3)

        # фонтан из дыхала (иногда)
        if int(self.timer * 2) % 8 == 0:
            fx = x + w // 2 if right else x + w // 2
            for i in range(6):
                pygame.draw.circle(surface, (200, 230, 255),
                                   (fx + random.randint(-4, 4), y - random.randint(0, 20)), 2)


# ==================== БОЛЬШАЯ АКУЛА (глубоководная) ====================
class BigShark:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 96, 40)
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = random.choice([-1.6, 1.6])
        self.vel_y = 0.0
        self.alive = True
        self.timer = 0.0
        self.aggro = False
        self.chase_timer = 0
        self.damage_cooldown = 0

    def update(self, world, player):
        if not self.alive:
            return
        self.timer += 0.05
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

        px, py = player.rect.centerx, player.rect.centery
        dx = px - self.rect.centerx
        dy = py - self.rect.centery
        dist = math.hypot(dx, dy) or 1

        if player.in_water and dist < 350:
            self.aggro = True
            self.chase_timer = 120
        elif self.chase_timer > 0:
            self.chase_timer -= 1
            if self.chase_timer <= 0:
                self.aggro = False

        if self.aggro:
            spd = 2.8
            self.vel_x = dx / dist * spd
            self.vel_y = dy / dist * spd
        else:
            self.vel_x = 1.6 if self.vel_x >= 0 else -1.6
            self.vel_y = math.sin(self.timer) * 0.8

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

        if self.damage_cooldown == 0 and self.rect.colliderect(player.rect):
            self.damage_cooldown = 120
            if hasattr(player, "on_shark_bite"):
                player.on_shark_bite()

    def draw(self, surface, offset_x=0, offset_y=0, world=None):
        if not self.alive:
            return
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.rect.w, self.rect.h
        right = self.vel_x > 0

        body = (90, 110, 140)
        dark = (50, 65, 90)

        pygame.draw.ellipse(surface, body, (x, y + 5, w - 12, h - 10))
        pygame.draw.ellipse(surface, (200, 210, 220), (x + 10, y + h - 18, w - 30, 10))

        # большой спинной плавник
        pygame.draw.polygon(surface, dark, [
            (x + w // 2 - 8, y + 5),
            (x + w // 2, y - 12),
            (x + w // 2 + 14, y + 5),
        ])

        # хвост
        if right:
            pygame.draw.polygon(surface, dark, [
                (x + 2, y + h // 2),
                (x - 22, y - 4),
                (x - 14, y + h // 2),
                (x - 22, y + h + 4),
            ])
            eye_x = x + w - 22
            mouth_x = x + w - 8
        else:
            pygame.draw.polygon(surface, dark, [
                (x + w - 2, y + h // 2),
                (x + w + 22, y - 4),
                (x + w + 14, y + h // 2),
                (x + w + 22, y + h + 4),
            ])
            eye_x = x + 12
            mouth_x = x + 2

        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 14), 4)
        pygame.draw.circle(surface, (10, 10, 10), (eye_x, y + 14), 3)
        # пасть с зубами
        pygame.draw.line(surface, (60, 30, 30), (mouth_x, y + 22), (mouth_x + (14 if right else -14), y + 22), 2)
        for i in range(3):
            tx = mouth_x + (i * 5 if right else -i * 5)
            pygame.draw.polygon(surface, (250, 250, 250), [
                (tx, y + 22), (tx + 2, y + 26), (tx - 2, y + 26)])

        # агро свечение
        if self.aggro:
            glow = pygame.Surface((w + 40, h + 40), pygame.SRCALPHA)
            pygame.draw.circle(glow, (240, 60, 60, 80), ((w + 40) // 2, (h + 40) // 2), (w + 40) // 2)
            surface.blit(glow, (x - 20, y - 20))
