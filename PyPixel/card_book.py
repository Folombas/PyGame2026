"""Книга коллекционных карточек. Открывается на B."""
import pygame
from settings import WIDTH, HEIGHT
from cards import CARD_DEFS, RARITY, draw_card_icon


COLS = 4
ROWS = 3
CELL_W = 130
CELL_H = 170
GAP = 14


class CardBook:
    def __init__(self, font_big, font_small):
        self.open = False
        self.font_big = font_big
        self.font_small = font_small
        self.selected = 0     # индекс выбранной карточки
        self.timer = 0

    def toggle(self):
        self.open = not self.open

    def update(self):
        if self.open:
            self.timer += 1

    def handle_event(self, event, owned):
        """Возвращает True если событие поглощено."""
        if not self.open:
            return False
        if event.type != pygame.KEYDOWN:
            return False
        total = len(CARD_DEFS)
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_b:
            self.open = False
            return True
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.selected = (self.selected - 1) % total
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.selected = (self.selected + 1) % total
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - COLS) % total
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + COLS) % total
        return True

    def _card_ids(self):
        return list(CARD_DEFS.keys())

    def _grid_rect(self):
        total_w = COLS * CELL_W + (COLS - 1) * GAP
        total_h = ROWS * CELL_H + (ROWS - 1) * GAP
        x = 60
        y = (HEIGHT - total_h) // 2 + 10
        return pygame.Rect(x, y, total_w, total_h)

    def draw(self, screen, owned):
        if not self.open:
            return

        # затемнение фона
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((5, 3, 15, 220))
        screen.blit(veil, (0, 0))

        # заголовок
        title = self.font_big.render("КНИГА КУЛЬТА", True, (255, 220, 80))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        collected = len([c for c in CARD_DEFS if c in owned])
        total = len(CARD_DEFS)
        sub = self.font_small.render(
            f"Собрано: {collected} / {total}", True, (200, 200, 220))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 66))

        hint = self.font_small.render(
            "B / Esc — закрыть    Стрелки — выбрать", True, (140, 140, 170))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))

        grid = self._grid_rect()
        ids = self._card_ids()

        for i, cid in enumerate(ids):
            row = i // COLS
            col = i % COLS
            cx = grid.x + col * (CELL_W + GAP)
            cy = grid.y + row * (CELL_H + GAP)
            rect = pygame.Rect(cx, cy, CELL_W, CELL_H)
            has = cid in owned
            selected = (i == self.selected)
            self._draw_card_tile(screen, rect, cid, has, selected)

        # правая панель — детали
        self._draw_detail(screen, ids[self.selected], owned)

    def _draw_card_tile(self, screen, rect, cid, owned, selected):
        info = CARD_DEFS[cid]
        rar = RARITY[info["rarity"]]
        border_col = rar["color"] if owned else (70, 70, 90)

        # фон
        bg = (25, 20, 40) if owned else (15, 12, 22)
        pygame.draw.rect(screen, bg, rect)
        pygame.draw.rect(screen, border_col, rect, 3 if selected else 2)

        # свечение если legendary/mythic и owned
        if owned and info["rarity"] in ("legendary", "mythic"):
            glow = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
            pulse = abs((self.timer // 12) % 20 - 10) / 10.0
            alpha = int(60 + pulse * 80)
            pygame.draw.rect(glow, (*rar["glow"], alpha),
                             (10, 10, rect.w, rect.h), 4)
            screen.blit(glow, (rect.x - 10, rect.y - 10))

        # иконка
        icon_rect = pygame.Rect(rect.x + 15, rect.y + 14, rect.w - 30, rect.h - 70)
        if owned:
            draw_card_icon(screen, info["icon"], icon_rect)
        else:
            # силуэт — вопросительный знак
            pygame.draw.rect(screen, (30, 25, 50), icon_rect)
            q = self.font_big.render("?", True, (90, 80, 120))
            screen.blit(q, (icon_rect.centerx - q.get_width() // 2,
                            icon_rect.centery - q.get_height() // 2))

        # имя
        name_col = (240, 240, 255) if owned else (100, 100, 120)
        name = self.font_small.render(info["name"], True, name_col)
        if name.get_width() > rect.w - 8:
            name = pygame.transform.smoothscale(
                name, (rect.w - 8, name.get_height()))
        screen.blit(name, (rect.centerx - name.get_width() // 2,
                            rect.bottom - 46))

        # редкость
        rar_s = self.font_small.render(
            rar["name"], True, rar["color"] if owned else (70, 70, 90))
        screen.blit(rar_s, (rect.centerx - rar_s.get_width() // 2,
                             rect.bottom - 24))

    def _draw_detail(self, screen, cid, owned):
        info = CARD_DEFS[cid]
        rar = RARITY[info["rarity"]]

        panel_w = 320
        panel_x = WIDTH - panel_w - 40
        panel_y = 100
        panel_h = HEIGHT - 160
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(screen, (18, 14, 32), panel)
        pygame.draw.rect(screen, rar["color"] if owned else (70, 70, 90), panel, 3)

        # большая иконка
        icon_rect = pygame.Rect(panel.x + 40, panel.y + 30, panel.w - 80, 180)
        if owned:
            draw_card_icon(screen, info["icon"], icon_rect)
        else:
            pygame.draw.rect(screen, (25, 20, 40), icon_rect)
            q = self.font_big.render("?", True, (80, 70, 100))
            screen.blit(q, (icon_rect.centerx - q.get_width() // 2,
                            icon_rect.centery - q.get_height() // 2))

        # имя
        name_col = (255, 240, 120) if owned else (90, 90, 110)
        name = self.font_big.render(info["name"], True, name_col)
        if name.get_width() > panel.w - 20:
            name = pygame.transform.smoothscale(
                name, (panel.w - 20, name.get_height()))
        screen.blit(name, (panel.centerx - name.get_width() // 2,
                            panel.y + 230))

        # редкость
        rar_s = self.font_small.render(
            f"— {rar['name']} —", True, rar["color"] if owned else (80, 80, 100))
        screen.blit(rar_s, (panel.centerx - rar_s.get_width() // 2,
                             panel.y + 270))

        if owned:
            # описание
            self._wrap_text(screen, info["desc"], panel.x + 16, panel.y + 315,
                            panel.w - 32, (220, 220, 235))
            # флейвор курсивом
            self._wrap_text(screen, info["flavor"], panel.x + 16,
                            panel.y + 400, panel.w - 32, (150, 180, 220))
        else:
            lock = self.font_small.render(
                "Не найдено. Ищи в мире...", True, (150, 100, 120))
            screen.blit(lock, (panel.centerx - lock.get_width() // 2,
                                panel.y + 330))

    def _wrap_text(self, screen, text, x, y, max_w, color):
        words = text.split()
        line = ""
        for word in words:
            test = line + (" " if line else "") + word
            surf = self.font_small.render(test, True, color)
            if surf.get_width() > max_w:
                s = self.font_small.render(line, True, color)
                screen.blit(s, (x, y))
                y += 22
                line = word
            else:
                line = test
        if line:
            s = self.font_small.render(line, True, color)
            screen.blit(s, (x, y))
