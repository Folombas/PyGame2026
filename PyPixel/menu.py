"""Меню."""
import random
import pygame
from settings import WIDTH, HEIGHT, DIFFICULTIES, DEFAULT_DIFFICULTY
from records import load_records
import sound_settings
import sounds


class Menu:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.items = ["start", "difficulty", "sound", "records", "quit"]
        self.selected = 0
        self.difficulty_key = DEFAULT_DIFFICULTY
        self.timer = 0
        self.mode = "main"       # main / records
        self.records = []

    def handle_event(self, event):
        """Возвращает 'start' / 'quit' / None."""
        if event.type != pygame.KEYDOWN:
            return None

        # ---- Экран рекордов ----
        if self.mode == "records":
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_BACKSPACE):
                self.mode = "main"
            return None

        # ---- Экран настроек звука ----
        if self.mode == "sound":
            cfg = sound_settings.load()
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_BACKSPACE):
                self.mode = "main"
            elif event.key in (pygame.K_SPACE, pygame.K_m):
                cfg["enabled"] = not cfg["enabled"]
                sound_settings.save(cfg)
                sounds.reload_settings()
            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_MINUS):
                cfg["volume"] = max(0.0, round(cfg["volume"] - 0.1, 2))
                sound_settings.save(cfg)
                sounds.reload_settings()
                sounds.play("collect")   # превью
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_PLUS, pygame.K_EQUALS):
                cfg["volume"] = min(1.0, round(cfg["volume"] + 0.1, 2))
                sound_settings.save(cfg)
                sounds.reload_settings()
                sounds.play("collect")   # превью
            return None

        # ---- Главное меню ----
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
            elif item == "sound":
                self.mode = "sound"
            elif item == "records":
                self.records = load_records()
                self.mode = "records"
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
        if self.mode == "records":
            self._draw_records(screen)
        elif self.mode == "sound":
            self._draw_sound(screen)
        else:
            self._draw_main(screen)

    def _draw_sound(self, screen):
        screen.fill((18, 16, 30))
        title = self.font_big.render("НАСТРОЙКИ ЗВУКА", True, (255, 240, 120))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        cfg = sound_settings.load()
        status = "ВКЛ" if cfg.get("enabled", True) else "ВЫКЛ"
        vol = int(cfg.get("volume", 0.5) * 100)

        # Звук вкл/выкл
        c1 = (255, 255, 255) if cfg.get("enabled", True) else (150, 150, 150)
        line1 = self.font_big.render(f"ЗВУК:  < {status} >", True, c1)
        screen.blit(line1, (WIDTH // 2 - line1.get_width() // 2, 240))

        # Громкость
        bar_x = WIDTH // 2 - 150
        bar_y = 340
        bar_w, bar_h = 300, 24
        pygame.draw.rect(screen, (40, 40, 60), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(screen, (200, 200, 220), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), 2)
        pygame.draw.rect(screen, (25, 25, 40), (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * cfg.get("volume", 0.5))
        if fill > 0:
            pygame.draw.rect(screen, (100, 200, 120), (bar_x, bar_y, fill, bar_h))
        vol_txt = self.font_small.render(f"ГРОМКОСТЬ:  {vol}%", True, (255, 255, 255))
        screen.blit(vol_txt, (WIDTH // 2 - vol_txt.get_width() // 2, bar_y - 30))

        hint = self.font_small.render(
            "←→ — громкость    Space/M — вкл/выкл    Esc — назад",
            True, (150, 150, 170)
        )
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 60))

    def _draw_main(self, screen):
        screen.fill((18, 16, 30))
        rng = random.Random(42)
        for _ in range(60):
            x = rng.randint(0, WIDTH)
            y = rng.randint(0, HEIGHT)
            size = rng.choice([1, 1, 2])
            pygame.draw.rect(screen, (70, 70, 110), (x, y, size, size))

        pulse = abs((self.timer // 20) % 10 - 5) / 5.0
        g = int(160 + 80 * pulse)
        title = self.font_big.render("PYPIXEL", True, (120, g, 120))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))

        subtitle = self.font_small.render("2D-платформер", True, (140, 140, 160))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 118))

        start_y = 230
        for i, item in enumerate(self.items):
            if item == "start":
                text = "НАЧАТЬ ИГРУ"
            elif item == "difficulty":
                label = DIFFICULTIES[self.difficulty_key]["label"]
                text = f"< СЛОЖНОСТЬ: {label} >"
            elif item == "sound":
                text = "НАСТРОЙКИ ЗВУКА"
            elif item == "records":
                text = "РЕКОРДЫ"
            else:
                text = "ВЫХОД"

            selected = (i == self.selected)
            color = (255, 240, 120) if selected else (200, 200, 220)
            prefix = "> " if selected else "  "
            surf = self.font_big.render(prefix + text, True, color)
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, start_y + i * 55))

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

    def _draw_records(self, screen):
        screen.fill((18, 16, 30))
        title = self.font_big.render("РЕКОРДЫ", True, (255, 240, 120))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

        if not self.records:
            info = self.font_small.render("Пока пусто — сыграй и поставь рекорд!", True, (180, 180, 200))
            screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 20))
        else:
            y = 140
            for i, r in enumerate(self.records, 1):
                line = (
                    f"{i}. {r.get('score', 0):>5} очк.  "
                    f"Ур.{r.get('level', '?')}  "
                    f"{r.get('difficulty', '?'):<6}  "
                    f"Ябл:{r.get('apples', 0):<3} "
                    f"Вр:{r.get('kills', 0):<3} "
                    f"{r.get('date', '')}"
                )
                color = (255, 240, 120) if i == 1 else (200, 200, 220)
                surf = self.font_small.render(line, True, color)
                screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
                y += 40

        hint = self.font_small.render("Esc / Enter — назад", True, (110, 110, 130))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))
