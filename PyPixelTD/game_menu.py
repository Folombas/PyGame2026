"""Главное меню игры с настройками."""
import pygame
from settings import WIDTH, HEIGHT
import os_sounds


DIFFICULTIES = {
    "easy":   {"label": "Лёгкая",   "desc": "5 жизней, враги слабые"},
    "normal": {"label": "Обычная",  "desc": "5 жизней, обычные враги"},
    "hard":   {"label": "Сложная",  "desc": "3 жизни, злые враги"},
}

VOLUME_STEPS = [0, 20, 40, 60, 80, 100]


class GameMenu:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.selected = 0
        self.items = [
            {"id": "start",      "label": "СТАРТ ИГРЫ"},
            {"id": "difficulty", "label": "СЛОЖНОСТЬ"},
            {"id": "volume",     "label": "ГРОМКОСТЬ"},
            {"id": "fullscreen", "label": "ПОЛНЫЙ ЭКРАН"},
            {"id": "exit",       "label": "ВЫХОД"},
        ]
        self.difficulty = "normal"
        self.volume_step = 4     # 80%
        self.fullscreen = True
        self.timer = 0
        self.result = None       # None | "start" | "exit"

    def _cycle_difficulty(self):
        keys = list(DIFFICULTIES.keys())
        i = keys.index(self.difficulty)
        self.difficulty = keys[(i + 1) % len(keys)]
        os_sounds.play("click")

    def _cycle_volume(self):
        self.volume_step = (self.volume_step + 1) % len(VOLUME_STEPS)
        # Обновляем громкость системы (pygame.mixer если есть)
        v = VOLUME_STEPS[self.volume_step] / 100.0
        try:
            pygame.mixer.music.set_volume(v)
        except Exception:
            pass
        os_sounds.play("click")

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        try:
            from settings import WIDTH, HEIGHT
            if self.fullscreen:
                pygame.display.set_mode((WIDTH, HEIGHT),
                                        pygame.FULLSCREEN | pygame.SCALED)
            else:
                pygame.display.set_mode((WIDTH, HEIGHT))
        except pygame.error:
            pass
        os_sounds.play("click")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.items)
            os_sounds.play("click")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.items)
            os_sounds.play("click")
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            item = self.items[self.selected]["id"]
            if item == "difficulty":
                keys = list(DIFFICULTIES.keys())
                i = keys.index(self.difficulty)
                self.difficulty = keys[(i - 1) % len(keys)]
                os_sounds.play("click")
            elif item == "volume":
                self.volume_step = (self.volume_step - 1) % len(VOLUME_STEPS)
                os_sounds.play("click")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            item = self.items[self.selected]["id"]
            if item == "difficulty":
                self._cycle_difficulty()
            elif item == "volume":
                self._cycle_volume()
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            item = self.items[self.selected]["id"]
            if item == "start":
                os_sounds.play("start")
                self.result = "start"
            elif item == "difficulty":
                self._cycle_difficulty()
            elif item == "volume":
                self._cycle_volume()
            elif item == "fullscreen":
                self._toggle_fullscreen()
            elif item == "exit":
                self.result = "exit"
        elif event.key == pygame.K_ESCAPE:
            self.result = "exit"

    def update(self, dt):
        self.timer += 1

    def draw(self, screen):
        # Фон — градиент с матричным дождём
        screen.fill((2, 8, 5))
        import random
        rng = random.Random(13)
        chars = "01アイウ$#@"
        t = self.timer
        for col_i in range(0, WIDTH, 24):
            seed = col_i // 24
            speed = 2 + (seed * 5 % 4)
            offset = (t * speed + seed * 30) % (HEIGHT + 200)
            for j in range(8):
                y = offset - j * 24
                if -20 < y < HEIGHT:
                    fade = max(0, 0.4 - j * 0.05)
                    r = rng.randint(0, len(chars) - 1)
                    col = (int(20 * fade), int(80 * fade), int(40 * fade))
                    s = self.font_small.render(chars[r], True, col)
                    screen.blit(s, (col_i, int(y)))

        # Заголовок
        title = self.font_big.render("BUNNY", True, (100, 255, 140))
        sub = self.font_big.render("WHITE HACKER", True, (100, 255, 140))

        # Тень/свечение
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            sh1 = self.font_big.render("BUNNY", True, (20, 80, 40))
            sh2 = self.font_big.render("WHITE HACKER", True, (20, 80, 40))
            screen.blit(sh1, (WIDTH // 2 - sh1.get_width() // 2 + dx, 60 + dy))
            screen.blit(sh2, (WIDTH // 2 - sh2.get_width() // 2 + dx, 95 + dy))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 95))

        # Меню — центральные кнопки
        menu_x = WIDTH // 2
        start_y = 220
        for i, item in enumerate(self.items):
            selected = (i == self.selected)
            y = start_y + i * 60

            # Значение справа
            val = ""
            if item["id"] == "difficulty":
                val = DIFFICULTIES[self.difficulty]["label"]
            elif item["id"] == "volume":
                val = f"{VOLUME_STEPS[self.volume_step]}%"
            elif item["id"] == "fullscreen":
                val = "ВКЛ" if self.fullscreen else "ВЫКЛ"

            # Подложка
            box_w = 400
            box_h = 48
            box = pygame.Rect(menu_x - box_w // 2, y, box_w, box_h)
            if selected:
                pygame.draw.rect(screen, (30, 100, 50), box)
                pygame.draw.rect(screen, (100, 255, 140), box, 2)
            else:
                pygame.draw.rect(screen, (15, 40, 25), box)
                pygame.draw.rect(screen, (50, 120, 70), box, 1)

            # Стрелки
            label = item["label"]
            if selected and item["id"] in ("difficulty", "volume", "fullscreen"):
                label = f"<  {label}  >"

            txt = self.font_big.render(label, True,
                                        (255, 255, 255) if selected else (200, 220, 200))
            screen.blit(txt, (box.centerx - txt.get_width() // 2, box.y + 8))

            # Значение справа от кнопки
            if val and item["id"] != "start" and item["id"] != "exit":
                vt = self.font_small.render(val, True, (200, 255, 200))
                screen.blit(vt, (box.right + 14, box.y + 14))

        # Описание сложности
        d = DIFFICULTIES[self.difficulty]
        desc = self.font_small.render(d["desc"], True, (180, 220, 180))
        screen.blit(desc, (WIDTH // 2 - desc.get_width() // 2, start_y + 5 * 60 + 20))

        # Подсказка
        hint = self.font_small.render("↑↓ — выбор   ←→ — менять   Enter — ок   Esc — выход",
                                       True, (140, 180, 150))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))
