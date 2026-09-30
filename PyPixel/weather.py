"""Погодные эффекты: снег, метель, вьюга. Работают только в холодных зонах."""
import random
import pygame
from settings import WIDTH, HEIGHT


class Weather:
    def __init__(self, count=200):
        self.flakes = []
        for _ in range(count):
            self.flakes.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(0, HEIGHT),
                "size": random.choice([1, 1, 2, 2, 3]),
                "speed": random.uniform(1.5, 4.0),
                "drift": random.uniform(-0.8, 0.8),
                "phase": random.uniform(0, 6.28),
            })
        self.timer = 0.0

    def intensity(self, camera_y):
        """0 — тепло, 1 — сильная метель. camera_y — центр камеры."""
        center = camera_y + HEIGHT / 2
        # Выше Y=800 → снег. Y=200 → макс интенсивность
        if center >= 850:
            return 0.0
        t = (850 - center) / 650.0
        return max(0.0, min(1.0, t))

    def update(self, camera_y, wind_x=0.0):
        self.timer += 0.016
        inten = self.intensity(camera_y)
        speed_mult = 1.0 + inten * 1.5
        drift_base = (0.6 + inten * 2.0) * (1 if (int(self.timer) % 10 < 5) else -1)
        drift_base += wind_x * 0.5

        for f in self.flakes:
            f["y"] += f["speed"] * speed_mult
            sway = (f["drift"] + drift_base * 0.3) + \
                   __import__("math").sin(self.timer * 2 + f["phase"]) * 0.5
            f["x"] += sway
            if f["y"] > HEIGHT + 5:
                f["y"] = -5
                f["x"] = random.uniform(0, WIDTH)
            if f["x"] < -5:
                f["x"] = WIDTH + 5
            elif f["x"] > WIDTH + 5:
                f["x"] = -5

    def draw(self, screen, camera_y):
        inten = self.intensity(camera_y)
        if inten < 0.05:
            return

        # Полупрозрачная дымка при сильной вьюге
        if inten > 0.5:
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = int((inten - 0.5) * 100)
            veil.fill((220, 230, 245, alpha))
            screen.blit(veil, (0, 0))

        for f in self.flakes:
            # Чем сильнее метель — тем крупнее и заметнее снежинки
            size = f["size"] if inten < 0.4 else min(4, f["size"] + 1)
            color = (255, 255, 255) if inten > 0.3 else (235, 240, 250)
            pygame.draw.rect(screen, color,
                             (int(f["x"]), int(f["y"]), size, size))
