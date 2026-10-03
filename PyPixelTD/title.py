"""Заставка игры Bunny - White Hacker."""
import math
import pygame
from settings import WIDTH, HEIGHT


class TitleScreen:
    DURATION = 300   # 5 секунд
    FADE_IN = 40
    FADE_OUT = 40

    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.timer = 0
        self.done = False

    def update(self, dt):
        self.timer += 1
        if self.timer >= self.DURATION:
            self.done = True
        keys = pygame.key.get_pressed()
        if self.timer > 40 and (keys[pygame.K_SPACE] or keys[pygame.K_RETURN]):
            self.done = True

    def draw(self, screen):
        # Чёрный фон с "цифровым дождём" — матрица
        screen.fill((0, 5, 0))
        t = self.timer

        # Символы матрицы — процедурные
        import random
        rng = random.Random(42)
        chars = "01アイウエオカキクケコサシスセソ$#@%&*+="
        for col_i in range(0, WIDTH, 18):
            seed = col_i // 18
            speed = 2 + (seed * 7 % 5)
            offset = (t * speed + seed * 40) % (HEIGHT + 200)
            for j in range(15):
                y = offset - j * 22
                if -20 < y < HEIGHT + 20:
                    fade = max(0, 1 - j / 15)
                    r = rng.randint(0, len(chars) - 1)
                    ch = chars[r]
                    col = (int(30 * fade), int(180 * fade), int(60 * fade))
                    if j == 0:
                        col = (200, 255, 200)
                    s = self.font_small.render(ch, True, col)
                    screen.blit(s, (col_i, int(y)))

        # Затемнение центра
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))
        screen.blit(veil, (0, 0))

        # Fade in/out
        if t < self.FADE_IN:
            a = 255 - int(255 * (t / self.FADE_IN))
        elif t > self.DURATION - self.FADE_OUT:
            a = int(255 * ((t - (self.DURATION - self.FADE_OUT)) / self.FADE_OUT))
        else:
            a = 0
        if a > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, a))
            screen.blit(fade_surf, (0, 0))

        # Логотип — зайка-хакер
        cx = WIDTH // 2
        cy = HEIGHT // 2 - 30

        # Свечение вокруг логотипа
        pulse = math.sin(t * 0.08) * 0.3 + 1
        glow_r = int(110 * pulse)
        for i in range(5):
            r = glow_r + i * 12
            a = max(0, 60 - i * 12)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (40, 255, 100, a), (r, r), r)
            screen.blit(glow, (cx - r, cy - r))

        # Круг-логотип
        pygame.draw.circle(screen, (0, 30, 10), (cx, cy), glow_r)
        pygame.draw.circle(screen, (60, 255, 120), (cx, cy), glow_r, 3)
        pygame.draw.circle(screen, (20, 180, 60), (cx, cy), glow_r - 10, 2)

        # Зайка — белый на чёрном, в очках хакера
        self._draw_hacker_rabbit(screen, cx, cy, 3)

        # Название игры
        if t > 20:
            title_line1 = self.font_big.render("BUNNY", True, (80, 255, 130))
            title_line2 = self.font_big.render("WHITE HACKER", True, (80, 255, 130))
            # Свечение
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                sh1 = self.font_big.render("BUNNY", True, (20, 80, 40))
                sh2 = self.font_big.render("WHITE HACKER", True, (20, 80, 40))
                tx = cx - sh1.get_width() // 2
                ty = cy + glow_r + 30
                screen.blit(sh1, (tx + dx, ty + dy))
                screen.blit(sh2, (tx + dx, ty + 50 + dy))
            screen.blit(title_line1, (cx - title_line1.get_width() // 2, cy + glow_r + 30))
            screen.blit(title_line2, (cx - title_line2.get_width() // 2, cy + glow_r + 60))

        # Подсказка
        if t > 90:
            blink = (t // 20) % 2 == 0
            if blink:
                hint = self.font_small.render("Нажми Space чтобы продолжить",
                                              True, (60, 200, 100))
                screen.blit(hint, (cx - hint.get_width() // 2, HEIGHT - 60))

    def _draw_hacker_rabbit(self, screen, cx, cy, scale):
        # Уши
        for ex in (-8 * scale, 8 * scale):
            pygame.draw.rect(screen, (255, 255, 255),
                             (cx + ex - 3 * scale, cy - 30 * scale, 6 * scale, 22 * scale))
            pygame.draw.rect(screen, (255, 200, 210),
                             (cx + ex - 2 * scale, cy - 28 * scale, 4 * scale, 18 * scale))
        # Голова
        head_r = 18 * scale
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), head_r)
        pygame.draw.circle(screen, (40, 255, 100), (cx, cy), head_r, 2)

        # Чёрные очки хакера
        eye_dx = 7 * scale
        eye_w = 7 * scale
        eye_h = 5 * scale
        pygame.draw.rect(screen, (20, 20, 25),
                         (cx - eye_dx - eye_w, cy - 4 * scale, eye_w * 2, eye_h))
        pygame.draw.rect(screen, (20, 20, 25),
                         (cx + eye_dx - eye_w, cy - 4 * scale, eye_w * 2, eye_h))
        # Мостик
        pygame.draw.rect(screen, (20, 20, 25),
                         (cx - 3, cy - 2, 6, 2))
        # Блики на очках (зелёные — терминал)
        pygame.draw.rect(screen, (60, 255, 120),
                         (cx - eye_dx - eye_w + 2, cy - 3 * scale, 3, 1))
        pygame.draw.rect(screen, (60, 255, 120),
                         (cx + eye_dx - eye_w + 2, cy - 3 * scale, 3, 1))

        # Нос
        pygame.draw.circle(screen, (255, 180, 200), (cx, cy + 5 * scale), 2 * scale)

        # Ноутбук с зелёным экраном в лапах
        lx = cx - 14 * scale
        ly = cy + 16 * scale
        lw = 28 * scale
        lh = 4 * scale
        pygame.draw.rect(screen, (60, 60, 70), (lx, ly, lw, lh))
        pygame.draw.rect(screen, (30, 30, 40), (lx, ly, lw, lh), 2)
        # Крышка ноутбука — открытая
        pygame.draw.polygon(screen, (60, 60, 70), [
            (lx + 2, ly),
            (lx + 6, ly - 12 * scale),
            (lx + lw - 6, ly - 12 * scale),
            (lx + lw - 2, ly),
        ])
        # Экран ноутбука — зелёный с кодом
        pygame.draw.polygon(screen, (0, 20, 5), [
            (lx + 3, ly - 1),
            (lx + 6, ly - 11 * scale),
            (lx + lw - 6, ly - 11 * scale),
            (lx + lw - 3, ly - 1),
        ])
        # Строчки кода
        for i in range(4):
            yy = ly - 10 * scale + i * 2 * scale
            xx = lx + 6
            w = (10 + (i * 5) % 12) * scale
            pygame.draw.rect(screen, (60, 255, 100), (xx, yy, w, 1))
