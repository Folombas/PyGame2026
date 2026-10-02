"""Сундуки с сокровищами. Спавнятся в пещерах, открываются ЛКМ."""
import random
import pygame
from settings import TILE


class Chest:
    W, H = 26, 22

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.W, self.H)
        self.opened = False
        self.pulse_timer = random.uniform(0, 6.28)
        self.loot = self._roll_loot()

    def _roll_loot(self):
        """Случайный лут при создании. Только id'ы, очки позже."""
        loot = []
        # всегда что-то ценное
        choices = [
            ("gold_coin", random.randint(5, 25)),
            ("iron_ore", random.randint(2, 6)),
            ("copper_ore", random.randint(3, 8)),
            ("glowberry_seed", random.randint(1, 3)),
            ("neonbud_seed", random.randint(1, 3)),
        ]
        random.shuffle(choices)
        loot = choices[:random.randint(2, 4)]
        # редкая карточка
        if random.random() < 0.35:
            loot.append(("card", 1))
        return loot

    def draw(self, surface, offset_x=0, offset_y=0):
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.W, self.H

        # Свечение — привлекает внимание в темноте
        self.pulse_timer += 0.05
        pulse = (pygame.math.Vector2(1, 1).rotate(0).x
                 if False else abs((int(self.pulse_timer * 3) % 20) - 10) / 10.0)
        glow_alpha = 60 + int(pulse * 100)
        glow = pygame.Surface((w + 40, h + 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 220, 100, glow_alpha // 3),
                           (w // 2 + 20, h // 2 + 20), 32)
        surface.blit(glow, (x - 20, y - 20))

        # Основание — тёмное дерево
        pygame.draw.rect(surface, (80, 50, 25), (x, y, w, h))
        pygame.draw.rect(surface, (50, 30, 15), (x, y, w, h), 2)

        # Крышка — светлее
        pygame.draw.rect(surface, (130, 85, 45), (x + 1, y + 1, w - 2, h // 2 - 1))
        pygame.draw.rect(surface, (50, 30, 15), (x + 1, y + 1, w - 2, h // 2 - 1), 1)

        # Золотые полоски
        pygame.draw.rect(surface, (220, 180, 60), (x, y + h // 2 - 1, w, 2))
        pygame.draw.rect(surface, (220, 180, 60), (x + w // 2 - 2, y, 4, h))

        # Замок
        pygame.draw.circle(surface, (255, 220, 100), (x + w // 2, y + h // 2), 4)
        pygame.draw.circle(surface, (120, 90, 30), (x + w // 2, y + h // 2), 4, 1)
        pygame.draw.rect(surface, (120, 90, 30), (x + w // 2 - 1, y + h // 2, 2, 5))

        if self.opened:
            # открытый — крышка наклонена, пусто
            pygame.draw.rect(surface, (30, 20, 10), (x + 2, y + 2, w - 4, h // 2 - 2))
            pygame.draw.rect(surface, (30, 20, 10), (x + 2, y + h // 2 + 1, w - 4, h // 2 - 3))


def draw_opened_marker(screen, chest, offset_x, offset_y):
    """Когда игрок открыл — маленькая анимация."""
    pass
