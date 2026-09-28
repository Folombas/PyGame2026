"""Фейерверки для победы."""
import math
import random
import pygame


COLORS = [
    (255, 100, 120), (255, 220, 100), (120, 220, 255),
    (180, 255, 140), (255, 160, 220), (255, 255, 255),
]


class Firework:
    def __init__(self, x: float, y: float):
        self.color = random.choice(COLORS)
        self.particles = []
        count = random.randint(28, 42)
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.5, 6.0)
            life = random.uniform(0.7, 1.4)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": life,
                "max_life": life,
            })

    def update(self, dt: float) -> None:
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.12       # гравитация
            p["vx"] *= 0.985
            p["vy"] *= 0.985
            p["life"] -= dt

    @property
    def dead(self) -> bool:
        return all(p["life"] <= 0 for p in self.particles)

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            if p["life"] <= 0:
                continue
            a = p["life"] / p["max_life"]
            size = max(1, int(3 * a + 1))
            pygame.draw.rect(
                surface, self.color,
                (int(p["x"]), int(p["y"]), size, size)
            )
