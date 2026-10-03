"""Деревня: домики и жители-NPC."""
import random
import pygame


# ==================== ДОМИК ====================
class House:
    W = 96    # 3 тайла
    H = 96

    def __init__(self, x, y, style=0):
        """x, y — координаты в пикселях (top-left угла дома, y — основание дома)."""
        self.rect = pygame.Rect(x, y - self.H, self.W, self.H)
        self.style = style
        self.has_light = True  # окно светится ночью
        self.timer = random.uniform(0, 6.28)

    def update(self):
        self.timer += 0.03

    def draw(self, surface, offset_x=0, offset_y=0, night=False):
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.W, self.H

        # стены из досок
        wood = (150, 105, 65) if self.style == 0 else (170, 120, 80)
        wood_dark = (90, 60, 35)
        pygame.draw.rect(surface, wood, (x + 6, y + 40, w - 12, h - 40))
        # доски вертикальные
        for i in range(1, 5):
            lx = x + 6 + i * (w - 12) // 5
            pygame.draw.line(surface, wood_dark, (lx, y + 40), (lx, y + h - 4), 1)
        # контур стен
        pygame.draw.rect(surface, wood_dark, (x + 6, y + 40, w - 12, h - 40), 2)

        # крыша — треугольная, из тёмного дерева
        roof_col = (100, 60, 40)
        roof_light = (140, 90, 60)
        pygame.draw.polygon(surface, roof_col, [
            (x, y + 42),
            (x + w // 2, y),
            (x + w, y + 42),
        ])
        pygame.draw.polygon(surface, roof_light, [
            (x + 6, y + 42),
            (x + w // 2, y + 6),
            (x + w - 6, y + 42),
        ])
        # контур крыши
        pygame.draw.lines(surface, wood_dark, False, [
            (x, y + 42), (x + w // 2, y), (x + w, y + 42)], 2)
        # черепица — линии
        for i in range(4):
            ly = y + 12 + i * 8
            ratio = (ly - y) / 42
            lx1 = int(x + w // 2 - w // 2 * ratio)
            lx2 = int(x + w // 2 + w // 2 * ratio)
            pygame.draw.line(surface, wood_dark, (lx1, ly), (lx2, ly), 1)

        # дверь
        door_w, door_h = 20, 40
        door_x = x + w // 2 - door_w // 2
        door_y = y + h - door_h
        pygame.draw.rect(surface, (80, 50, 30), (door_x, door_y, door_w, door_h))
        pygame.draw.rect(surface, (50, 30, 15), (door_x, door_y, door_w, door_h), 2)
        # ручка
        pygame.draw.circle(surface, (220, 180, 80), (door_x + door_w - 4, door_y + door_h // 2), 2)

        # окно
        win_size = 18
        win_x = x + 12
        win_y = y + 55
        # рама
        pygame.draw.rect(surface, (60, 40, 25), (win_x - 2, win_y - 2, win_size + 4, win_size + 4))
        # стекло — светится ночью
        if night:
            glow = (255, 220, 130)
            # свечение вокруг окна
            pulse = abs((self.timer * 2) % 2 - 1)
            alpha = int(40 + pulse * 40)
            glow_surf = pygame.Surface((win_size + 40, win_size + 40), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 220, 130, alpha),
                               ((win_size + 40) // 2, (win_size + 40) // 2), 30)
            surface.blit(glow_surf, (win_x - 13, win_y - 13))
        else:
            glow = (150, 190, 220)
        pygame.draw.rect(surface, glow, (win_x, win_y, win_size, win_size))
        # перегородки окна
        pygame.draw.line(surface, (60, 40, 25),
                         (win_x + win_size // 2, win_y),
                         (win_x + win_size // 2, win_y + win_size), 2)
        pygame.draw.line(surface, (60, 40, 25),
                         (win_x, win_y + win_size // 2),
                         (win_x + win_size, win_y + win_size // 2), 2)

        # труба на крыше
        pygame.draw.rect(surface, (110, 70, 50), (x + w - 28, y + 4, 12, 22))
        pygame.draw.rect(surface, (70, 45, 30), (x + w - 28, y + 4, 12, 22), 1)


# ==================== ЖИТЕЛЬ ====================
VILLAGER_NAMES = ["Фермер", "Кузнец", "Торговец", "Старейшина", "Пастух"]
SHIRT_COLORS = [
    (200, 80, 80), (80, 160, 200), (200, 180, 80), (140, 90, 200), (100, 200, 120),
]


class Villager:
    def __init__(self, x, y, name=None, home_x=None):
        self.rect = pygame.Rect(x, y, 24, 32)
        self.spawn_x = x
        self.home_x = home_x or x
        self.name = name or random.choice(VILLAGER_NAMES)
        self.shirt = random.choice(SHIRT_COLORS)
        self.skin = (240, 200, 170)
        self.vel_x = random.choice([-0.6, 0.6])
        self.timer = random.uniform(0, 6.28)
        self.range = 60
        self.anim_timer = 0
        self.anim_frame = 0
        self.talking_timer = 0
        self.saying = None

    def say(self, text, frames=180):
        self.saying = text
        self.talking_timer = frames

    def update(self, world=None):
        self.timer += 0.04
        # ходит туда-сюда
        self.rect.x += int(self.vel_x)
        if abs(self.rect.centerx - self.home_x) > self.range:
            self.vel_x = -self.vel_x
        # анимация шага
        self.anim_timer += 1
        if self.anim_timer >= 14:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2
        if self.talking_timer > 0:
            self.talking_timer -= 1
        else:
            self.saying = None

    def draw(self, surface, offset_x=0, offset_y=0, font=None):
        x = self.rect.x - offset_x
        y = self.rect.y - offset_y
        w, h = self.rect.w, self.rect.h
        facing = 1 if self.vel_x > 0 else -1

        # тень
        pygame.draw.ellipse(surface, (0, 0, 0, 60), (x, y + h - 3, w, 5))

        # ноги
        leg_offset = 3 if self.anim_frame else -3
        pygame.draw.rect(surface, (60, 40, 30), (x + 4, y + h - 10, 6, 10))
        pygame.draw.rect(surface, (60, 40, 30), (x + w - 10, y + h - 10, 6, 10))

        # тело — рубаха
        pygame.draw.rect(surface, self.shirt, (x + 3, y + 12, w - 6, h - 22))
        pygame.draw.rect(surface, (0, 0, 0), (x + 3, y + 12, w - 6, h - 22), 1)

        # руки
        pygame.draw.rect(surface, self.shirt, (x, y + 14, 4, 12))
        pygame.draw.rect(surface, self.shirt, (x + w - 4, y + 14, 4, 12))

        # голова
        pygame.draw.rect(surface, self.skin, (x + 5, y, w - 10, 14))
        pygame.draw.rect(surface, (0, 0, 0), (x + 5, y, w - 10, 14), 1)

        # волосы
        hair_col = (60, 40, 30) if random.random() < 0.7 else (180, 140, 80)
        pygame.draw.rect(surface, hair_col, (x + 4, y - 2, w - 8, 6))

        # глаза
        eye_x = x + 8 if facing > 0 else x + w - 12
        pygame.draw.rect(surface, (20, 20, 20), (eye_x, y + 6, 2, 3))
        pygame.draw.rect(surface, (20, 20, 20), (eye_x + 6, y + 6, 2, 3))

        # речь — облачко
        if self.saying and font:
            txt = font.render(self.saying, True, (255, 255, 255))
            bw = txt.get_width() + 12
            bh = txt.get_height() + 8
            bx = x + w // 2 - bw // 2
            by = y - bh - 8
            pygame.draw.rect(surface, (30, 25, 50, 230), (bx, by, bw, bh))
            pygame.draw.rect(surface, (200, 200, 220), (bx, by, bw, bh), 2)
            # хвостик
            pygame.draw.polygon(surface, (30, 25, 50), [
                (x + w // 2 - 4, by + bh),
                (x + w // 2 + 4, by + bh),
                (x + w // 2, by + bh + 6),
            ])
            pygame.draw.polygon(surface, (200, 200, 220), [
                (x + w // 2 - 4, by + bh),
                (x + w // 2 + 4, by + bh),
                (x + w // 2, by + bh + 6),
            ], 1)
            surface.blit(txt, (bx + 6, by + 4))

        # имя над головой
        if font:
            name_surf = font.render(self.name, True, (255, 255, 255))
            name_bg = pygame.Surface((name_surf.get_width() + 6, name_surf.get_height() + 2),
                                     pygame.SRCALPHA)
            name_bg.fill((0, 0, 0, 140))
            nx = x + w // 2 - name_bg.get_width() // 2
            ny = y - name_bg.get_height() - (28 if self.saying else 4)
            surface.blit(name_bg, (nx, ny))
            surface.blit(name_surf, (nx + 3, ny + 1))
