"""Экран загрузки BunnyOS с логотипом и прогресс-баром."""
import math
import pygame
from settings import WIDTH, HEIGHT
import os_sounds


class BootScreen:
    """Экран загрузки — 4 секунды. Показывает логотип, прогресс."""

    DURATION = 240       # кадров (~4 сек)
    LOGO_FADE = 40       # появление логотипа

    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.timer = 0
        self.done = False
        self.started_sound = False

    def update(self, dt):
        self.timer += 1
        if not self.started_sound:
            os_sounds.play("start")
            self.started_sound = True
        if self.timer >= self.DURATION:
            self.done = True
            os_sounds.play("login")
        # можно скипнуть по нажатию
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or keys[pygame.K_ESCAPE]:
            if self.timer > 30:
                self.done = True

    def draw(self, screen):
        # Фон — тёмно-синий градиент (классика XP)
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(8 + 20 * t)
            g = int(15 + 30 * t)
            b = int(40 + 60 * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # Логотип — большой круг с зайцем
        cx = WIDTH // 2
        cy = HEIGHT // 2 - 60

        # Появление логотипа (fade + scale)
        prog = min(1.0, self.timer / self.LOGO_FADE)
        scale = 0.5 + 0.5 * prog
        alpha = int(255 * prog)

        # Свечение вокруг
        glow_r = int(130 * scale)
        for i in range(6):
            r = glow_r + i * 8
            a = max(0, 60 - i * 10)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (100, 180, 255, a), (r, r), r)
            screen.blit(glow, (cx - r, cy - r))

        # Круг
        pygame.draw.circle(screen, (30, 80, 160), (cx, cy), glow_r)
        pygame.draw.circle(screen, (150, 200, 255), (cx, cy), glow_r, 3)
        pygame.draw.circle(screen, (60, 120, 200), (cx, cy), glow_r - 8, 2)

        # Зайка в центре — большой, пиксельный
        rabbit_scale = max(2, int(3 * scale))
        self._draw_rabbit(screen, cx, cy, rabbit_scale)

        # Название
        if self.timer > 20:
            title = self.font_big.render("BunnyOS", True, (255, 255, 255))
            title_shadow = self.font_big.render("BunnyOS", True, (30, 60, 120))
            tx = cx - title.get_width() // 2
            ty = cy + glow_r + 25
            screen.blit(title_shadow, (tx + 2, ty + 2))
            screen.blit(title, (tx, ty))

            sub = self.font_small.render("Версия 1.0  ·  ядро Carrot-5.15", True, (180, 210, 240))
            screen.blit(sub, (cx - sub.get_width() // 2, ty + 40))

        # Прогресс-бар внизу
        bar_w, bar_h = 400, 16
        bar_x = (WIDTH - bar_w) // 2
        bar_y = HEIGHT - 100
        pygame.draw.rect(screen, (20, 30, 60), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(screen, (100, 140, 200), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), 2)
        pygame.draw.rect(screen, (10, 15, 35), (bar_x, bar_y, bar_w, bar_h))

        # Прогресс — по времени
        progress = min(1.0, self.timer / self.DURATION)
        fill_w = int(bar_w * progress)
        # Сегменты как в XP
        for i in range(0, fill_w, 12):
            seg_w = min(10, fill_w - i)
            if seg_w <= 0:
                break
            col = (80, 160 + int(60 * math.sin(self.timer * 0.1 + i)), 240)
            pygame.draw.rect(screen, col, (bar_x + i + 1, bar_y + 2, seg_w, bar_h - 4))

        # Текст состояния
        status = self._status_text(progress)
        st = self.font_small.render(status, True, (180, 210, 240))
        screen.blit(st, (cx - st.get_width() // 2, bar_y + 30))

        # Подсказка снизу
        hint = self.font_small.render("Нажми Space чтобы пропустить", True, (100, 130, 170))
        screen.blit(hint, (cx - hint.get_width() // 2, HEIGHT - 30))

    def _status_text(self, p):
        if p < 0.2:
            return "Загрузка ядра Carrot-5.15..."
        elif p < 0.4:
            return "Инициализация морковных драйверов..."
        elif p < 0.6:
            return "Монтирование /home/zayka..."
        elif p < 0.8:
            return "Запуск оконного менеджера Lop-Ear..."
        else:
            return "Загрузка рабочего стола Bunny..."

    def _draw_rabbit(self, screen, cx, cy, scale):
        """Большой пиксельный зайка."""
        # Уши
        ear_w = 6 * scale
        ear_h = 22 * scale
        for ex in (-7 * scale, 7 * scale):
            pygame.draw.rect(screen, (255, 245, 235),
                             (cx + ex - ear_w // 2, cy - ear_h - 8 * scale, ear_w, ear_h))
            pygame.draw.rect(screen, (240, 150, 170),
                             (cx + ex - ear_w // 2 + 1, cy - ear_h - 6 * scale, ear_w - 2, ear_h - 6))

        # Голова
        head_r = 16 * scale
        pygame.draw.circle(screen, (255, 245, 235), (cx, cy), head_r)
        pygame.draw.circle(screen, (30, 25, 35), (cx, cy), head_r, max(2, scale - 1))

        # Глаза
        eye_r = 3 * scale
        eye_dx = 6 * scale
        for dx in (-eye_dx, eye_dx):
            pygame.draw.circle(screen, (30, 25, 35), (cx + dx, cy - 2 * scale), eye_r)

        # Нос
        pygame.draw.circle(screen, (240, 150, 170), (cx, cy + 5 * scale), max(2, scale))

        # Морковка в лапах
        carrot_w = 8 * scale
        carrot_h = 12 * scale
        car_x = cx + head_r - 2
        car_y = cy + 4
        pygame.draw.polygon(screen, (240, 130, 50), [
            (car_x, car_y),
            (car_x + carrot_w, car_y),
            (car_x + carrot_w // 2, car_y + carrot_h),
        ])
        pygame.draw.polygon(screen, (180, 80, 20), [
            (car_x, car_y),
            (car_x + carrot_w, car_y),
            (car_x + carrot_w // 2, car_y + carrot_h),
        ], max(1, scale - 1))
        # Ботва
        for dx in (-3, 0, 3):
            pygame.draw.line(screen, (80, 200, 90),
                             (car_x + carrot_w // 2, car_y),
                             (car_x + carrot_w // 2 + dx * scale, car_y - 6 * scale),
                             max(1, scale - 1))


class LoginScreen:
    """Экран приветствия после загрузки — как в XP."""
    DURATION = 90

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
        if keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or keys[pygame.K_ESCAPE]:
            if self.timer > 20:
                self.done = True

    def draw(self, screen):
        # Фон — как в XP (синяя заливка с полосами)
        screen.fill((40, 70, 130))
        for y in range(0, HEIGHT, 4):
            c = (40 + (y // 4) % 8, 70 + (y // 4) % 8, 130 + (y // 4) % 8)
            pygame.draw.line(screen, c, (0, y), (WIDTH, y))

        # Верхняя и нижняя полосы
        pygame.draw.rect(screen, (30, 50, 100), (0, 0, WIDTH, 60))
        pygame.draw.rect(screen, (30, 50, 100), (0, HEIGHT - 80, WIDTH, 80))
        pygame.draw.line(screen, (100, 160, 220), (0, 60), (WIDTH, 60), 2)
        pygame.draw.line(screen, (100, 160, 220), (0, HEIGHT - 80), (WIDTH, HEIGHT - 80), 2)

        # Логотип слева
        cx = 180
        cy = HEIGHT // 2

        # Круг с зайцем
        pygame.draw.circle(screen, (255, 245, 235), (cx, cy), 70)
        pygame.draw.circle(screen, (100, 160, 220), (cx, cy), 70, 3)

        # Уши
        for ex in (-14, 14):
            pygame.draw.ellipse(screen, (255, 245, 235), (cx + ex - 8, cy - 90, 16, 44))
            pygame.draw.ellipse(screen, (240, 150, 170), (cx + ex - 5, cy - 86, 10, 36))

        # Мордочка
        pygame.draw.circle(screen, (30, 25, 35), (cx - 14, cy - 6), 6)
        pygame.draw.circle(screen, (30, 25, 35), (cx + 14, cy - 6), 6)
        pygame.draw.circle(screen, (240, 150, 170), (cx, cy + 8), 4)

        # Название ОС
        title = self.font_big.render("BunnyOS", True, (255, 255, 255))
        screen.blit(title, (cx - title.get_width() // 2, cy + 90))

        # Справа — профиль пользователя
        ux = WIDTH // 2 + 100
        uy = HEIGHT // 2

        # Аватар-кружок
        pygame.draw.circle(screen, (100, 160, 220), (ux, uy - 40), 50)
        pygame.draw.circle(screen, (255, 245, 235), (ux, uy - 40), 46)
        pygame.draw.circle(screen, (30, 25, 35), (ux - 12, uy - 46), 5)
        pygame.draw.circle(screen, (30, 25, 35), (ux + 12, uy - 46), 5)
        pygame.draw.circle(screen, (240, 150, 170), (ux, uy - 32), 4)

        # Имя пользователя
        name = self.font_big.render("Зайка", True, (255, 255, 255))
        screen.blit(name, (ux - name.get_width() // 2, uy + 25))
        sub = self.font_small.render("Нажми Enter, чтобы войти", True, (200, 220, 255))
        screen.blit(sub, (ux - sub.get_width() // 2, uy + 60))

        # Внизу — "Добро пожаловать"
        welcome = self.font_big.render("Добро пожаловать в BunnyOS", True, (255, 255, 255))
        screen.blit(welcome, (WIDTH // 2 - welcome.get_width() // 2, HEIGHT - 50))
