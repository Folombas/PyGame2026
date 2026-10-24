"""Патрулирующие антивирусы + зрение + тревога."""
import pygame
import math
import random
from settings import *
from render import draw_fov_cone


class Enemy:
    """Патрулирующий антивирус.

    Состояния:
    - patrol: ходит по точкам маршрута
    - suspicious: заметил что-то, поворачивается на цель
    - alert: погоня, кричит другим
    """
    def __init__(self, patrol_points):
        self.patrol = patrol_points if patrol_points else [(0, 0)]
        self.patrol_idx = 0
        x, y = self.patrol[0]
        self.x, self.y = float(x), float(y)
        self.angle = random.uniform(0, math.tau)
        self.state = "patrol"
        self.suspicion = 0.0  # 0..1
        self.alert_cooldown = 0.0
        self.last_seen = None
        self.radius = 14
        self.step_timer = random.uniform(0, 1)

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def _check_vision(self, player, world):
        """Видит ли игрока? Возвращает True/False."""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > ENEMY_VIEW_DIST:
            return False
        # Угол
        target_angle = math.atan2(dy, dx)
        diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        if abs(math.degrees(diff)) > ENEMY_VIEW_ANGLE / 2:
            return False
        # Препятствия?
        if world.raycast_block(self.x, self.y, player.x, player.y):
            return False
        return True

    def update(self, dt, player, world, all_enemies):
        # Проверка зрения
        sees = self._check_vision(player, world)

        if sees:
            self.suspicion = min(1.0, self.suspicion + ENEMY_DETECT_RATE * dt)
            self.last_seen = (player.x, player.y)
        else:
            self.suspicion = max(0.0, self.suspicion - ENEMY_FORGET_RATE * dt)

        # Смена состояния
        if self.suspicion >= 1.0:
            self.state = "alert"
            self._alert_others(all_enemies)
        elif self.suspicion > 0.2:
            if self.state != "alert":
                self.state = "suspicious"
        elif self.suspicion <= 0.05:
            if self.state != "alert":
                self.state = "patrol"

        # Поведение по состоянию
        if self.state == "patrol":
            self._do_patrol(dt, world)
        elif self.state == "suspicious":
            self._do_suspicious(dt)
        elif self.state == "alert":
            self._do_alert(dt, player, world)

    def _do_patrol(self, dt, world):
        # Плавный поворот к следующей точке + движение
        target_x, target_y = self.patrol[self.patrol_idx]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist < 8:
            self.patrol_idx = (self.patrol_idx + 1) % len(self.patrol)
        else:
            target_angle = math.atan2(dy, dx)
            diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += diff * min(1.0, dt * 3)
            # Двигаемся в направлении target_angle, а не текущего angle (для простоты)
            move = ENEMY_PATROL_SPEED * dt
            nx = self.x + math.cos(target_angle) * move
            ny = self.y + math.sin(target_angle) * move
            # Проверка коллизий
            if not world.is_blocking(nx, self.y):
                self.x = nx
            if not world.is_blocking(self.x, ny):
                self.y = ny

    def _do_suspicious(self, dt):
        # Медленно поворачиваемся к последней позиции
        if self.last_seen:
            target_angle = math.atan2(self.last_seen[1] - self.y,
                                       self.last_seen[0] - self.x)
            diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += diff * min(1.0, dt * 2)

    def _do_alert(self, dt, player, world):
        # Гонимся за игроком
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 2:
            target_angle = math.atan2(dy, dx)
            self.angle = target_angle
            move = ENEMY_ALERT_SPEED * dt
            nx = self.x + math.cos(target_angle) * move
            ny = self.y + math.sin(target_angle) * move
            if not world.is_blocking(nx, self.y):
                self.x = nx
            if not world.is_blocking(self.x, ny):
                self.y = ny
            # Если очень близко — тревога сработает (game over)
            if dist < self.radius + player.radius + 4:
                return "caught"

    def _alert_others(self, all_enemies):
        # Все в радиусе слышат
        if self.alert_cooldown > 0:
            return
        for e in all_enemies:
            if e is self:
                continue
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist < 400:
                e.suspicion = max(e.suspicion, 0.6)
        self.alert_cooldown = 2.0

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # FOV конус
        ang_deg = math.degrees(self.angle)
        draw_fov_cone(screen, int(self.x), int(self.y),
                      ang_deg, ENEMY_VIEW_DIST, ENEMY_VIEW_ANGLE / 2,
                      cam_x, cam_y)

        # Тело
        color = ENEMY
        if self.state == "alert":
            color = ENEMY_ALERT
        elif self.state == "suspicious":
            # Мигает
            if int(self.suspicion * 10) % 2 == 0:
                color = (255, 180, 100)

        # Тень
        pygame.draw.ellipse(screen, (0, 0, 0, 100),
                           (sx - self.radius, sy + self.radius - 4,
                            self.radius * 2, 8))

        # Тело — ромб
        pygame.draw.circle(screen, color, (sx, sy), self.radius)
        pygame.draw.circle(screen, (30, 20, 30), (sx, sy), self.radius, 2)

        # Направление — глаз
        ex = sx + int(math.cos(self.angle) * self.radius * 0.6)
        ey = sy + int(math.sin(self.angle) * self.radius * 0.6)
        pygame.draw.circle(screen, (20, 15, 20), (ex, ey), 4)

        # Индикатор подозрения
        if self.suspicion > 0.05:
            bar_w = self.radius * 2
            bar_y = sy - self.radius - 8
            pygame.draw.rect(screen, (30, 30, 40),
                            (sx - self.radius, bar_y, bar_w, 4))
            fill = int(bar_w * self.suspicion)
            bar_col = (255, 220, 100) if self.suspicion < 1 else (255, 60, 80)
            pygame.draw.rect(screen, bar_col,
                            (sx - self.radius, bar_y, fill, 4))


def spawn_enemies(world, n=4):
    """Расставляет врагов в разных комнатах."""
    enemies = []
    rooms = world.rooms[1:]  # кроме стартовой
    random.shuffle(rooms)
    for i in range(min(n, len(rooms))):
        r = rooms[i]
        # 2-3 точки патруля в комнате
        pts = []
        for _ in range(3):
            px = (r.x + random.randint(1, r.w - 2)) * TILE + TILE // 2
            py = (r.y + random.randint(1, r.h - 2)) * TILE + TILE // 2
            if not world.is_blocking(px, py):
                pts.append((px, py))
        if pts:
            enemies.append(Enemy(pts))
    return enemies
