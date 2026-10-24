from dataclasses import dataclass, field
import math
import random
import pygame
from pygame.math import Vector2


@dataclass
class Bullet:
    pos: Vector2
    vel: Vector2
    radius: float = 4
    damage: int = 1
    life: float = 1.2

    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            (255, 230, 80),
            (int(self.pos.x), int(self.pos.y)),
            int(self.radius),
        )


@dataclass
class Weapon:
    name: str
    cooldown: float
    damage: int
    speed: float
    spread: float
    pellets: int
    radius: float
    color: tuple
    timer: float = field(default=0.0, init=False, repr=False)


class WeaponSystem:
    def __init__(self, audio):
        self.audio = audio
        self.weapons = [
            Weapon("Pistol", 0.18, 1, 900, 0.02, 1, 4, (255, 220, 80)),
            Weapon("Shotgun", 0.55, 1, 750, 0.25, 7, 5, (255, 150, 60)),
        ]
        self.index = 0
        self.bullets = []

    @property
    def current(self):
        return self.weapons[self.index]

    def cycle(self, direction):
        self.index = (self.index + direction) % len(self.weapons)

    def update(self, dt):
        self.current.timer = max(0.0, self.current.timer - dt)
        self.bullets = [b for b in self.bullets if b.update(dt)]

    def shoot(self, origin, target):
        weapon = self.current
        if weapon.timer > 0:
            return []

        weapon.timer = weapon.cooldown
        direction = Vector2(target) - Vector2(origin)
        if direction.length_squared() == 0:
            direction = Vector2(1, 0)
        base = direction.normalize()
        base_angle = math.atan2(base.y, base.x)

        new_bullets = []
        for _ in range(weapon.pellets):
            spread = random.uniform(-weapon.spread, weapon.spread) if weapon.spread else 0.0
            angle = base_angle + spread
            vel = Vector2(math.cos(angle), math.sin(angle)) * weapon.speed
            pos = Vector2(origin) + base * 26
            new_bullets.append(
                Bullet(pos, vel, weapon.radius, weapon.damage)
            )

        self.bullets.extend(new_bullets)
        self.audio.play("shoot", 0.8)
        return new_bullets

    def draw(self, surface):
        for bullet in self.bullets:
            bullet.draw(surface)
