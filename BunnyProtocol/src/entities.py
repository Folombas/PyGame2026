import pygame
from pygame.math import Vector2
from .weapons import WeaponSystem


class Rabbit:
    def __init__(self, pos, audio):
        self.pos = Vector2(pos)
        self.speed = 300
        self.radius = 24
        self.audio = audio
        self.weapons = WeaponSystem(audio)

    def update(self, dt, keys, bounds):
        direction = Vector2(0, 0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1

        if direction.length_squared():
            self.pos += direction.normalize() * self.speed * dt

        self.pos.x = max(self.radius, min(bounds[0] - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(bounds[1] - self.radius, self.pos.y))
        self.weapons.update(dt)

    def shoot(self, target):
        return self.weapons.shoot(self.pos, target)

    def draw(self, surface, aim_pos):
        x, y = int(self.pos.x), int(self.pos.y)

        pygame.draw.ellipse(surface, (245, 245, 250), (x - 18, y - 50, 14, 42))
        pygame.draw.ellipse(surface, (245, 245, 250), (x + 4, y - 50, 14, 42))
        pygame.draw.ellipse(surface, (255, 180, 190), (x - 15, y - 46, 8, 32))
        pygame.draw.ellipse(surface, (255, 180, 190), (x + 7, y - 46, 8, 32))

        pygame.draw.circle(surface, (240, 240, 245), (x, y), self.radius)
        pygame.draw.circle(surface, (40, 40, 50), (x - 7, y - 5), 3)
        pygame.draw.circle(surface, (40, 40, 50), (x + 7, y - 5), 3)
        pygame.draw.circle(surface, (255, 120, 140), (x, y + 7), 4)

        direction = Vector2(aim_pos) - self.pos
        if direction.length_squared() > 0:
            end = self.pos + direction.normalize() * 38
            pygame.draw.line(surface, (70, 80, 95), (x, y), (int(end.x), int(end.y)), 6)
            pygame.draw.circle(
                surface,
                self.weapons.current.color,
                (int(end.x), int(end.y)),
                5,
            )

        self.weapons.draw(surface)


class Enemy:
    def __init__(self, pos):
        self.pos = Vector2(pos)
        self.radius = 20
        self.hp = 3
        self.alive = True
        self.color = (220, 70, 90)

    def update(self, dt, target):
        direction = Vector2(target) - self.pos
        if direction.length_squared() > 4:
            self.pos += direction.normalize() * 55 * dt

    def hit(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.circle(surface, self.color, (x, y), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (x - 6, y - 4), 3)
        pygame.draw.circle(surface, (255, 255, 255), (x + 6, y - 4), 3)
        pygame.draw.circle(surface, (30, 20, 30), (x, y + 6), 4)
