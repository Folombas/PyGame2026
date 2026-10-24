"""HUD и оверлеи."""
import pygame
from settings import *


class HUD:
    def __init__(self, font_small, font):
        self.font_small = font_small
        self.font = font
        self.tick = 0

    def draw(self, screen, keys_collected, total_keys, alert_level,
             lights_off_timer):
        """Верхний HUD."""
        self.tick += 1

        # Фон HUD
        bar = pygame.Rect(0, 0, WIDTH, 52)
        bg = pygame.Surface((WIDTH, 52), pygame.SRCALPHA)
        bg.fill((10, 12, 20, 220))
        screen.blit(bg, bar.topleft)
        pygame.draw.line(screen, (60, 80, 120), (0, 52), (WIDTH, 52), 1)

        # Ключи — слева
        key_icon_x = 30
        key_icon_y = 26
        for i in range(total_keys):
            collected = i < keys_collected
            color = KEY_COLOR if collected else (60, 60, 80)
            pygame.draw.circle(screen, color, (key_icon_x + i * 30, key_icon_y), 8)
            if collected:
                pygame.draw.circle(screen, (200, 160, 40),
                                  (key_icon_x + i * 30, key_icon_y - 2), 3)

        # Alert level — центр
        if alert_level > 0.05:
            bar_w = 200
            bar_x = WIDTH // 2 - bar_w // 2
            bar_y = 18
            pygame.draw.rect(screen, (30, 30, 40), (bar_x, bar_y, bar_w, 16),
                            border_radius=8)
            fill = int(bar_w * min(1.0, alert_level))
            col = (255, 220, 100) if alert_level < 0.7 else (255, 60, 80)
            pygame.draw.rect(screen, col, (bar_x, bar_y, fill, 16),
                            border_radius=8)
            label = self.font_small.render("ОБНАРУЖЕНИЕ", True, TEXT)
            screen.blit(label, (bar_x + bar_w // 2 - label.get_width() // 2,
                                bar_y + 1))

        # Lights off timer — справа
        if lights_off_timer > 0:
            txt = f"⚡ СВЕТ ВЫКЛ: {int(lights_off_timer)}"
            t = self.font_small.render(txt, True, (200, 220, 255))
            screen.blit(t, (WIDTH - t.get_width() - 20, 18))

        # Время (правый угол, над заголовком)
        time_str = f"⏱ {int(self._play_time) if hasattr(self, '_play_time') else 0}с"
        tt = self.font_small.render(time_str, True, TEXT)
        screen.blit(tt, (WIDTH - tt.get_width() - 20, 18))

        # Заголовок приложения (правый угол)
        title = self.font_small.render("BUNNY PROTOCOL", True, TEXT_DIM)
        screen.blit(title, (WIDTH - title.get_width() - 20,
                            HEIGHT - 30))

    def draw_overlay(self, screen, title, subtitle, color=ALERT):
        """Полноэкранный оверлей (game over / win)."""
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 220))
        screen.blit(ov, (0, 0))

        big = pygame.font.Font(None, 96)
        t = big.render(title, True, color)
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 80))

        if subtitle:
            s = self.font.render(subtitle, True, TEXT_DIM)
            screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 30))

        hint = self.font.render("Enter — заново   Esc — выход", True, TEXT)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 100))

    def draw_interact_hint(self, screen, panel_kind):
        """Подсказка внизу: «E — отключить свет»."""
        if panel_kind == "lights":
            txt = "E — ОТКЛЮЧИТЬ СВЕТ (5 сек)"
        else:
            txt = "E — ОТКРЫТЬ ДВЕРЬ"
        s = self.font.render(txt, True, PANEL_COLOR)
        box = pygame.Surface((s.get_width() + 24, s.get_height() + 16),
                            pygame.SRCALPHA)
        box.fill((30, 20, 50, 230))
        pygame.draw.rect(box, PANEL_COLOR,
                        (0, 0, box.get_width(), box.get_height()), 2,
                        border_radius=8)
        bx = WIDTH // 2 - box.get_width() // 2
        by = HEIGHT - 90
        screen.blit(box, (bx, by))
        screen.blit(s, (bx + 12, by + 8))
