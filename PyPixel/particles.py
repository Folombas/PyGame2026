"""Частицы: кровь, искры, пыль. Всё пиксельно, всё в коде."""
import random
import math
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size=2, gravity=0.3):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def update(self):
        alive = []
        for p in self.particles:
            p.life -= 1
            if p.life <= 0:
                continue
            p.vy += p.gravity
            p.x += p.vx
            p.y += p.vy
            # трение
            p.vx *= 0.94
            alive.append(p)
        self.particles = alive

    def draw(self, surface, offset_x, offset_y):
        for p in self.particles:
            sx = int(p.x) - offset_x
            sy = int(p.y) - offset_y
            if -10 < sx < surface.get_width() + 10 and -10 < sy < surface.get_height() + 10:
                # затухание по жизни
                a = p.life / p.max_life
                size = max(1, int(p.size * (0.5 + a * 0.5)))
                pygame.draw.rect(surface, p.color, (sx, sy, size, size))

    # ---------- пресеты ----------
    def spawn_blood(self, x, y, direction=0, count=14):
        """Кровь от врага. direction — куда брызгать (радианы, 0 = вправо)."""
        for _ in range(count):
            ang = direction + random.uniform(-1.0, 1.0)
            spd = random.uniform(2, 6)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 2
            life = random.randint(20, 40)
            col = random.choice([(200, 30, 40), (170, 20, 30), (230, 60, 60)])
            self.particles.append(Particle(x, y, vx, vy, life, col, size=random.choice([2, 2, 3]), gravity=0.4))

    def spawn_sparks(self, x, y, count=8):
        """Искры при копании камня/руды."""
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(1, 3)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 1
            life = random.randint(10, 20)
            col = random.choice([(255, 220, 120), (255, 180, 80), (240, 240, 200)])
            self.particles.append(Particle(x, y, vx, vy, life, col, size=2, gravity=0.2))

    def spawn_dirt(self, x, y, count=10, color=(120, 80, 50)):
        """Комья земли при копании."""
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(1, 3)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 2
            life = random.randint(15, 30)
            col = tuple(max(0, c + random.randint(-20, 20)) for c in color)
            self.particles.append(Particle(x, y, vx, vy, life, col, size=3, gravity=0.35))

    def spawn_leaves(self, x, y, count=16):
        """Листья при рубке дерева."""
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(1, 4)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 1
            life = random.randint(30, 60)
            col = random.choice([(60, 150, 60), (90, 180, 80), (40, 120, 50)])
            self.particles.append(Particle(x, y, vx, vy, life, col, size=3, gravity=0.15))

    def spawn_dust(self, x, y, count=6):
        """Пыль при беге."""
        for _ in range(count):
            vx = random.uniform(-1, 1)
            vy = random.uniform(-1, -0.2)
            life = random.randint(8, 16)
            col = (180, 160, 130)
            self.particles.append(Particle(x, y, vx, vy, life, col, size=2, gravity=0.05))
