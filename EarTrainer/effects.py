"""Лёгкая система частиц — искры при успехе, вспышка при провале."""
import math
import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color, speed=4.0, life=30, size=3):
        ang = random.uniform(0, math.tau)
        r = random.uniform(0.3, 1.0) * speed
        self.x, self.y = x, y
        self.vx = math.cos(ang) * r
        self.vy = math.sin(ang) * r - 2.0
        self.life = self.max_life = life
        self.color = color
        self.size = size

    def update(self, dt):
        f = dt / 16.67
        self.x += self.vx * f
        self.y += self.vy * f
        self.vy += 0.25 * f
        self.vx *= 0.98
        self.life -= f

    def draw(self, surf):
        if self.life <= 0:
            return
        a = max(0, self.life / self.max_life)
        size = max(1, int(self.size * a))
        color = self.color
        try:
            surf_alpha = (*color[:3], int(255 * a))
            pygame.draw.circle(surf, surf_alpha, (int(self.x), int(self.y)), size)
        except Exception:
            pygame.draw.circle(surf, color, (int(self.x), int(self.y)), size)


class Effects:
    def __init__(self):
        self.particles = []
        self.flash_color = None
        self.flash_timer = 0
        self.flash_duration = 250

    def burst(self, x, y, color, count=20, speed=5.0):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed=speed))

    def flash(self, color, duration=250):
        self.flash_color = color
        self.flash_timer = duration
        self.flash_duration = duration

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        if self.flash_timer > 0:
            self.flash_timer -= dt

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

    def draw_flash(self, surf):
        if self.flash_timer > 0 and self.flash_color:
            a = int(140 * (self.flash_timer / self.flash_duration))
            overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            overlay.fill((*self.flash_color, a))
            surf.blit(overlay, (0, 0))
