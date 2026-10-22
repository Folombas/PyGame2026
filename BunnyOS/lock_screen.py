"""Экран блокировки — Ctrl+L."""
import pygame
import math
from settings import WIDTH, HEIGHT


class LockScreen:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.timer = 0.0
        self.open = False

    def show(self):
        self.open = True
        self.timer = 0.0

    def handle_event(self, e):
        if not self.open:
            return True
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.open = False
                return True
            if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.open = False
                return True
        return True

    def update(self, dt):
        self.timer += dt

    def draw(self, screen):
        # Тёмный градиент
        for y in range(HEIGHT):
            t = y / HEIGHT
            col = (int(10 + 20 * t), int(15 + 30 * t), int(35 + 50 * t))
            pygame.draw.line(screen, col, (0, y), (WIDTH, y))

        # Пульсирующий аватар
        cx, cy = WIDTH // 2, HEIGHT // 2 - 60
        pulse = 1.0 + 0.05 * math.sin(self.timer * 2)
        r = int(80 * pulse)
        for i in range(5):
            rr = r + 6 + i * 8
            a = max(0, 30 - i * 6)
            glow = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 140, 220, a), (rr, rr), rr)
            screen.blit(glow, (cx - rr, cy - rr))

        pygame.draw.circle(screen, (40, 60, 90), (cx, cy), r)
        pygame.draw.circle(screen, (120, 180, 240), (cx, cy), r, 3)

        # Заяц
        pygame.draw.circle(screen, (240, 240, 250), (cx, cy), r - 15)
        pygame.draw.ellipse(screen, (240, 240, 250), (cx - 25, cy - r - 5, 14, 36))
        pygame.draw.ellipse(screen, (240, 240, 250), (cx + 11, cy - r - 5, 14, 36))
        pygame.draw.ellipse(screen, (240, 150, 170), (cx - 21, cy - r + 0, 6, 26))
        pygame.draw.ellipse(screen, (240, 150, 170), (cx + 15, cy - r + 0, 6, 26))
        pygame.draw.circle(screen, (30, 25, 35), (cx - 15, cy - 5), 4)
        pygame.draw.circle(screen, (30, 25, 35), (cx + 15, cy - 5), 4)
        pygame.draw.circle(screen, (240, 150, 170), (cx, cy + 8), 3)

        # Имя
        name = self.font_big.render("Зайка", True, (240, 250, 255))
        screen.blit(name, (WIDTH // 2 - name.get_width() // 2, cy + r + 30))

        # Подсказка
        if int(self.timer * 2) % 2 == 0:
            hint = self.font_small.render("Нажми Enter чтобы разблокировать",
                                          True, (150, 180, 220))
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 120))
