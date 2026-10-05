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
        self.vx = random.choice([-0.3, -0.2, 0.2, 0.3])
        self.walk_range = random.randint(40, 100)
        self.anim_frame = 0
        self.anim_timer = 0
        self.moo_timer = random.randint(300, 800)
        self.talk_text = None
        self.talk_timer = 0
        self.facing_right = True
        # Размеры на экране — 32×32 (scale 2)
        self.size = 32
        self.sprite_frames = self._load_sprites()

    def _load_sprites(self):
        """Загружает 2 кадра по 16×16, увеличивает до 32×32."""
        file_map = {
            "cow": "animals/cow.png",
            "chicken": "animals/chicken.png",
        }
        sheet = assets.load_image(file_map.get(self.kind, "animals/cow.png"))
        if sheet is None:
            return [None, None]
        frames = []
        for i in range(2):
            sub = pygame.Surface((16, 16), pygame.SRCALPHA)
            sub.blit(sheet, (0, 0), pygame.Rect(i * 16, 0, 16, 16))
            frames.append(pygame.transform.scale(sub, (48, 48)))
        return frames

    def rect(self):
        return pygame.Rect(int(self.x) - 24, int(self.y) - 24, 48, 48)

    def update(self):
        # Ходим туда-сюда
        self.x += self.vx
        if abs(self.x - self.base_x) > self.walk_range:
            self.vx = -self.vx
        self.facing_right = self.vx > 0

        # Анимация
        self.anim_timer += 1
        if self.anim_timer >= 20:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

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
        frame = self.sprite_frames[self.anim_frame]
        if frame is None:
            return
        img = frame
        if not self.facing_right:
            img = pygame.transform.flip(frame, True, False)
        sx = int(self.x) - 24 - cam_x
        sy = int(self.y) - 48 - cam_y
        # Тень
        shadow = pygame.Surface((32, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, 32, 8))
        screen.blit(shadow, (sx, int(self.y) - 4 - cam_y))
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
