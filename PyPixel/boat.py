"""Лодка — плавает по воде, игрок может сесть."""
import pygame


class Boat:
    W, H = 56, 24

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.W, self.H)
        self.vel_x = 0.0
        self.bob_timer = 0.0

    def update(self, world):
        self.bob_timer += 0.08
        # мягкое покачивание на воде
        self.rect.x += int(self.vel_x)
        # затухание
        self.vel_x *= 0.96
        # если под лодкой не вода — она остаётся на месте (плывёт медленнее)
        cx = self.rect.centerx // 32
        cy = self.rect.bottom // 32
        if world.get_block(cx, cy) != 14:  # WATER
            self.vel_x *= 0.5

    def draw(self, surface, offset_x=0, offset_y=0):
        import math
        bob = int(math.sin(self.bob_timer) * 2)
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y + bob
        w, h = self.W, self.H

        # корпус — коричневое дерево
        pygame.draw.polygon(surface, (140, 90, 55), [
            (x, y + 6), (x + w, y + 6), (x + w - 8, y + h), (x + 8, y + h)])
        pygame.draw.polygon(surface, (90, 55, 30), [
            (x, y + 6), (x + w, y + 6), (x + w, y + 8), (x, y + 8)])
        # внутренняя часть (тёмная)
        pygame.draw.polygon(surface, (70, 45, 25), [
            (x + 6, y + 8), (x + w - 6, y + 8), (x + w - 12, y + h - 4), (x + 12, y + h - 4)])
        # борта
        pygame.draw.line(surface, (170, 120, 70), (x, y + 6), (x + 8, y + h), 2)
        pygame.draw.line(surface, (170, 120, 70), (x + w, y + 6), (x + w - 8, y + h), 2)
        # весло
        pygame.draw.line(surface, (100, 70, 40), (x + w // 2, y + 4), (x + w // 2 + 14, y - 8), 3)
        pygame.draw.ellipse(surface, (60, 40, 20), (x + w // 2 + 10, y - 12, 10, 6))
