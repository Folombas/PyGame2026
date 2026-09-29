"""Меню."""
import random
import pygame
from settings import WIDTH, HEIGHT, DIFFICULTIES, DEFAULT_DIFFICULTY


class Menu:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.items = ["start", "difficulty", "quit"]
        self.selected = 0
        self.difficulty_key = DEFAULT_DIFFICULTY
        self.timer = 0

    def handle_event(self, event):
        """Возвращает 'start' / 'quit' / None."""
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.items)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            if self.items[self.selected] == "difficulty":
                self._cycle(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            if self.items[self.selected] == "difficulty":
                self._cycle(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            item = self.items[self.selected]
            if item == "start":
                return "start"
            elif item == "difficulty":
                self._cycle(1)
            elif item == "quit":
                return "quit"
        return None

    def _cycle(self, direction):
        keys = list(DIFFICULTIES.keys())
        i = keys.index(self.difficulty_key)
        self.difficulty_key = keys[(i + direction) % len(keys)]

    def update(self):
        self.timer += 1

    def draw(self, screen):
        screen.fill((18, 16, 30))

        # декоративные звёзды
        rng = random.Random(42)
        for _ in range(60):
            x = rng.randint(0, WIDTH)
            y = rng.randint(0, HEIGHT)
            size = rng.choice([1, 1, 2])
            pygame.draw.rect(screen, (70, 70, 110), (x, y, size, size))

        # пульсирующий заголовок
        pulse = abs((self.timer // 20) % 10 - 5) / 5.0
        g = int(160 + 80 * pulse)
        title = self.font_big.render("PYPIXEL", True, (120, g, 120))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 90))

        subtitle = self.font_small.render("2D-платформер", True, (140, 140, 160))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 140))

        # пункты меню
        start_y = 270
        for i, item in enumerate(self.items):
            if item == "start":
                text = "НАЧАТЬ ИГРУ"
            elif item == "difficulty":
                label = DIFFICULTIES[self.difficulty_key]["label"]
                text = f"< СЛОЖНОСТЬ: {label} >"
            else:
                text = "ВЫХОД"

            selected = (i == self.selected)
            color = (255, 240, 120) if selected else (200, 200, 220)
            prefix = "> " if selected else "  "
            surf = self.font_big.render(prefix + text, True, color)
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, start_y + i * 60))

        # описание сложности
        d = DIFFICULTIES[self.difficulty_key]
        descr = self.font_small.render(
            f"Жизни: {d['lives']}    HP: {d['max_hp']}    Урон: {d['hit_damage']}    Враги: x{d['enemy_speed']}",
            True, (150, 150, 170)
        )
        screen.blit(descr, (WIDTH // 2 - descr.get_width() // 2, HEIGHT - 90))

        hint = self.font_small.render(
            "Стрелки — выбор    Enter — ок    Esc — выход",
            True, (110, 110, 130)
        )
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))
