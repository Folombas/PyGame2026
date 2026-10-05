"""Животные на лугу: коровы и куры."""
import random
import pygame
import assets


class Animal:
    """Базовое животное. Спрайт 32×16 = 2 кадра по 16×16."""

    def __init__(self, tx, ty, kind="cow"):
        self.tx = tx
        self.ty = ty
        self.kind = kind
        self.base_x = tx * 32 + 16
        self.base_y = ty * 32 + 32
        self.x = float(self.base_x)
        self.y = float(self.base_y)
        self.vx = 0.0
        self.vy = 0.0
        self.walk_range = random.randint(30, 70)
        self.anim_frame = 0
        self.anim_timer = 0
        self.moo_timer = random.randint(300, 800)
        # Паттерн: пасётся N кадров, потом идёт M кадров
        self.idle_timer = random.randint(120, 300)  # стоим
        self.walk_timer = 0                          # идём
        self.talk_text = None
        self.talk_timer = 0
        self.facing_right = True
        # Размеры на экране — 32×32 (scale 2)
        self.size = 48
        self.sprites = self._load_sprites()   # {"front": [..], "side": [..]}
        # Корова — ВСЕГДА боком, курица — ВСЕГДА спереди (бокового нет)
        if self.kind == "cow" and self.sprites.get("side"):
            self.facing = "side"
        else:
            self.facing = "front"

    def _load_sprites(self):
        """Загружает кадры для front и side. Cow — обе, chicken — только front."""
        files = {"front": "animals/cow.png", "side": "animals/cow_side.png"}
        if self.kind == "chicken":
            files = {"front": "animals/chicken.png", "side": "animals/chicken.png"}

        result = {"front": [], "side": []}
        for face, path in files.items():
            sheet = assets.load_image(path)
            if sheet is None:
                continue
            # Автоопределение количества кадров
            n_frames = sheet.get_width() // 16
            for i in range(n_frames):
                sub = pygame.Surface((16, 16), pygame.SRCALPHA)
                sub.blit(sheet, (0, 0), pygame.Rect(i * 16, 0, 16, 16))
                result[face].append(pygame.transform.scale(sub, (48, 48)))
        return result

    def rect(self):
        return pygame.Rect(int(self.x) - 24, int(self.y) - 24, 48, 48)

    def update(self):
        # Паттерн: пасётся → идёт немного → снова пасётся
        if self.idle_timer > 0:
            self.idle_timer -= 1
            self.vx = 0.0
            self.vy = 0.0
            self.anim_frame = 0   # стоит — 1-й кадр
        else:
            # Начинаем новый цикл ходьбы
            if self.walk_timer <= 0:
                self.walk_timer = random.randint(30, 90)
                # Случайное направление движения
                angle = random.choice([0, 90, 180, 270])
                if angle == 0:    self.vx = 0.3;  self.vy = 0
                elif angle == 90: self.vx = 0;    self.vy = 0.3
                elif angle == 180: self.vx = -0.3; self.vy = 0
                else:             self.vx = 0;    self.vy = -0.3
                # Направление движения (для отражения)
                if abs(self.vx) > 0.01:
                    self.facing_right = self.vx > 0

            self.x += self.vx
            self.y += self.vy
            self.walk_timer -= 1

            # Если далеко от базы — возвращаемся (просто стоп)
            if abs(self.x - self.base_x) > self.walk_range:
                self.x = self.base_x + (self.walk_range if self.x > self.base_x else -self.walk_range)
                self.walk_timer = 0
            if abs(self.y - self.base_y) > self.walk_range:
                self.y = self.base_y + (self.walk_range if self.y > self.base_y else -self.walk_range)
                self.walk_timer = 0

            # Анимация ходьбы — циклится по всем кадрам
            self.anim_timer += 1
            if self.anim_timer >= 12:
                self.anim_timer = 0
                frames = self.sprites.get(self.facing, [])
                if frames:
                    self.anim_frame = (self.anim_frame + 1) % len(frames)

            # Закончили ходьбу → пасёмся
            if self.walk_timer <= 0:
                self.idle_timer = random.randint(150, 400)

        # Разговоры
        if self.talk_timer > 0:
            self.talk_timer -= 1
            if self.talk_timer == 0:
                self.talk_text = None

        # Мычание / кудахтанье
        self.moo_timer -= 1
        if self.moo_timer <= 0:
            self.moo_timer = random.randint(400, 1000)
            if random.random() < 0.3:
                self.say("Му!" if self.kind == "cow" else "Ко-ко!")

    def say(self, text, frames=120):
        self.talk_text = text
        self.talk_timer = frames

    def draw(self, screen, cam_x, cam_y, font_small=None):
        # Используем правильный набор кадров
        frames = self.sprites.get(self.facing) or self.sprites.get("front")
        if not frames:
            return
        # Защита от выхода за пределы массива
        frame_idx = self.anim_frame % len(frames)
        frame = frames[frame_idx]
        if frame is None:
            return
        img = frame
        # Отражаем только side
        if self.facing == "side" and not self.facing_right:
            img = pygame.transform.flip(frame, True, False)
        sx = int(self.x) - 24 - cam_x
        sy = int(self.y) - 48 - cam_y
        # Тень
        shadow = pygame.Surface((44, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, 44, 10))
        screen.blit(shadow, (sx + 2, int(self.y) - 5 - cam_y))
        # Спрайт
        screen.blit(img, (sx, sy))

        # Речь
        if self.talk_text and font_small:
            txt = font_small.render(self.talk_text, True, (255, 255, 255))
            bg = pygame.Surface((txt.get_width() + 8, txt.get_height() + 4), pygame.SRCALPHA)
            bg.fill((30, 25, 50, 220))
            bx = sx + 16 - bg.get_width() // 2
            by = sy - bg.get_height() - 4
            screen.blit(bg, (bx, by))
            screen.blit(txt, (bx + 4, by + 2))
