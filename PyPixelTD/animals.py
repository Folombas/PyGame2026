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
        # Размеры: корова крупная, курица мелкая
        self.scale = 4 if self.kind == "cow" else 2.5
        self.hitbox_w = 56 if self.kind == "cow" else 32
        self.hitbox_h = 40 if self.kind == "cow" else 28
        self.sprites = self._load_sprites()
        # Корова — ВСЕГДА боком, курица — ВСЕГДА спереди
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
        size = int(16 * self.scale)
        for face, path in files.items():
            sheet = assets.load_image(path)
            if sheet is None:
                continue
            n_frames = sheet.get_width() // 16
            for i in range(n_frames):
                sub = pygame.Surface((16, 16), pygame.SRCALPHA)
                sub.blit(sheet, (0, 0), pygame.Rect(i * 16, 0, 16, 16))
                result[face].append(pygame.transform.scale(sub, (size, size)))
        return result

    def rect(self):
        return pygame.Rect(
            int(self.x) - self.hitbox_w // 2,
            int(self.y) - self.hitbox_h,
            self.hitbox_w, self.hitbox_h)

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
                self.walk_timer = random.randint(40, 100)
                # Только влево или вправо — корова боком не идёт вверх/вниз
                self.vx = random.choice([-0.35, 0.35])
                self.vy = 0
                self.facing_right = self.vx > 0

            self.x += self.vx
            self.walk_timer -= 1

            # Если далеко от базы — разворачиваемся
            if abs(self.x - self.base_x) > self.walk_range:
                self.vx = -self.vx
                self.facing_right = self.vx > 0

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
        frames = self.sprites.get(self.facing) or self.sprites.get("front")
        if not frames:
            return
        frame_idx = self.anim_frame % len(frames)
        frame = frames[frame_idx]
        if frame is None:
            return
        img = frame
        # Отражаем только side
        if self.facing == "side" and not self.facing_right:
            img = pygame.transform.flip(frame, True, False)

        img_w = img.get_width()
        img_h = img.get_height()
        # Спрайт стоит на ногах — прижаты к нижней границе "клетки"
        sx = int(self.x) - img_w // 2 - cam_x
        sy = int(self.y) - img_h - cam_y

        # Тень
        shadow_w = int(img_w * 0.85)
        shadow_h = max(6, int(img_h * 0.15))
        shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, shadow_w, shadow_h))
        screen.blit(shadow, (sx + (img_w - shadow_w) // 2, int(self.y) - shadow_h // 2 - cam_y))

        # Спрайт
        screen.blit(img, (sx, sy))

        # Речь
        if self.talk_text and font_small:
            txt = font_small.render(self.talk_text, True, (255, 255, 255))
            bg = pygame.Surface((txt.get_width() + 8, txt.get_height() + 4), pygame.SRCALPHA)
            bg.fill((30, 25, 50, 220))
            bx = sx + img_w // 2 - bg.get_width() // 2
            by = sy - bg.get_height() - 4
            screen.blit(bg, (bx, by))
            screen.blit(txt, (bx + 4, by + 2))
