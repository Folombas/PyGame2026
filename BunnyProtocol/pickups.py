"""Ключи, выход, хакерские панели."""
import pygame
import math
import random
from settings import *


class Key:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.radius = 12
        self.bob = random.uniform(0, 6.28)
        self.collected = False

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def update(self, dt, player):
        self.bob += dt * 3
        if not self.collected:
            dx = player.x - self.x
            dy = player.y - self.y
            if math.hypot(dx, dy) < self.radius + player.radius:
                self.collected = True
                return True
        return False

    def draw(self, screen, cam_x, cam_y):
        if self.collected:
            return
        bob_offset = int(math.sin(self.bob) * 4)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y) + bob_offset

        # Свечение
        glow = pygame.Surface((self.radius * 4, self.radius * 4),
                              pygame.SRCALPHA)
        for i in range(4):
            r = self.radius + i * 4
            a = 60 - i * 12
            pygame.draw.circle(glow, (*KEY_COLOR, a),
                              (self.radius * 2, self.radius * 2), r)
        screen.blit(glow, (sx - self.radius * 2, sy - self.radius * 2))

        # Ключ (простой)
        pygame.draw.circle(screen, KEY_COLOR, (sx, sy), self.radius)
        pygame.draw.circle(screen, (180, 140, 40), (sx, sy), self.radius, 2)
        # Отверстие
        pygame.draw.circle(screen, (40, 30, 10), (sx, sy - 3), 3)
        # Зубцы
        pygame.draw.rect(screen, KEY_COLOR,
                        (sx - 3, sy + self.radius - 4, 6, 8))


class Exit:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.rect_ = pygame.Rect(int(x) - 20, int(y) - 20, 40, 40)
        self.tick = 0.0

    def update(self, dt, player, keys_collected):
        self.tick += dt

    def can_enter(self, player, keys_collected):
        dx = player.x - self.x
        dy = player.y - self.y
        if math.hypot(dx, dy) < 30 and keys_collected >= KEYS_REQUIRED:
            return True
        return False

    def draw(self, screen, cam_x, cam_y, keys_collected):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        unlocked = keys_collected >= KEYS_REQUIRED

        # Пульсация
        pulse = 1.0 + 0.1 * math.sin(self.tick * 3)

        if unlocked:
            color = EXIT_COLOR
            glow_a = 80
        else:
            color = (120, 120, 140)
            glow_a = 30

        # Свечение
        r = int(30 * pulse)
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, glow_a), (r, r), r)
        screen.blit(glow, (sx - r, sy - r))

        # Дверь
        pygame.draw.rect(screen, color,
                        (sx - 20, sy - 20, 40, 40), border_radius=6)
        pygame.draw.rect(screen, (30, 40, 50),
                        (sx - 20, sy - 20, 40, 40), 2, border_radius=6)

        # Замок или стрелка
        if unlocked:
            # Стрелка выхода →
            pygame.draw.polygon(screen, (20, 60, 30), [
                (sx - 6, sy - 10), (sx + 6, sy), (sx - 6, sy + 10),
                (sx - 6, sy + 4), (sx - 12, sy + 4),
                (sx - 12, sy - 4), (sx - 6, sy - 4),
            ])
        else:
            # Замок
            pygame.draw.rect(screen, (60, 60, 80),
                            (sx - 8, sy - 4, 16, 14), border_radius=2)
            pygame.draw.arc(screen, (60, 60, 80),
                           (sx - 6, sy - 12, 12, 12), 0, math.pi, 2)


class HackPanel:
    """Хакерская панель — отключает свет на 5 сек или открывает дверь."""
    def __init__(self, x, y, kind="lights"):
        self.x, self.y = float(x), float(y)
        self.kind = kind
        self.used = False
        self.radius = 14

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def dist_to(self, player):
        return math.hypot(self.x - player.x, self.y - player.y)

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        color = PANEL_COLOR if not self.used else (60, 40, 80)

        pygame.draw.rect(screen, color,
                        (sx - self.radius, sy - self.radius,
                         self.radius * 2, self.radius * 2),
                        border_radius=4)
        pygame.draw.rect(screen, (30, 20, 50),
                        (sx - self.radius, sy - self.radius,
                         self.radius * 2, self.radius * 2),
                        2, border_radius=4)

        # Иконка
        if self.kind == "lights":
            # Молния
            pygame.draw.polygon(screen, (255, 255, 200), [
                (sx, sy - 8), (sx + 4, sy - 2), (sx - 1, sy - 1),
                (sx + 2, sy + 8), (sx - 4, sy + 1), (sx + 1, sy),
            ])
        else:
            # Замок
            pygame.draw.rect(screen, (255, 220, 150),
                            (sx - 6, sy - 2, 12, 10), border_radius=2)
            pygame.draw.arc(screen, (255, 220, 150),
                           (sx - 5, sy - 9, 10, 10), 0, math.pi, 2)


def spawn_keys(world, n=KEYS_REQUIRED):
    """Расставляет ключи в дальних комнатах."""
    keys = []
    rooms = world.rooms[1:]  # не в стартовой
    random.shuffle(rooms)
    used_cells = []
    for i in range(min(n, len(rooms))):
        r = rooms[i]
        for _ in range(10):
            px = (r.x + random.randint(1, r.w - 2)) * TILE + TILE // 2
            py = (r.y + random.randint(1, r.h - 2)) * TILE + TILE // 2
            if not world.is_blocking(px, py) and (px, py) not in used_cells:
                used_cells.append((px, py))
                keys.append(Key(px, py))
                break
    return keys


def spawn_panels(world, n=2):
    """Расставляет панели в комнатах."""
    panels = []
    rooms = world.rooms[1:]
    random.shuffle(rooms)
    for i in range(min(n, len(rooms))):
        r = rooms[i]
        for _ in range(10):
            px = (r.x + random.randint(1, r.w - 2)) * TILE + TILE // 2
            py = (r.y + random.randint(1, r.h - 2)) * TILE + TILE // 2
            if not world.is_blocking(px, py):
                kind = "lights" if i == 0 else "door"
                panels.append(HackPanel(px, py, kind))
                break
    return panels
