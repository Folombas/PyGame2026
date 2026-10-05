"""Ярлыки рабочего стола — иконки приложений."""
import pygame
import ui_kit


# Список приложений
ICONS = [
    {"id": "terminal",   "label": "Терминал",   "emoji": ">_",  "color": (40, 200, 120)},
    {"id": "mycomputer", "label": "Мой кролик", "emoji": "🖥",  "color": (120, 160, 220)},
    {"id": "browser",    "label": "Интернет",   "emoji": "🌐",  "color": (80, 160, 220)},
    {"id": "map",        "label": "Карта",      "emoji": "🗺",  "color": (150, 200, 120)},
    {"id": "notes",      "label": "Заметки",    "emoji": "📝",  "color": (240, 200, 100)},
    {"id": "calc",       "label": "Калькулятор","emoji": "🔢",  "color": (200, 130, 200)},
    {"id": "trash",      "label": "Корзина",    "emoji": "🗑",  "color": (140, 140, 140)},
]

ICON_W = 96
ICON_H = 96
CELL_W = 120
CELL_H = 110
PAD_X = 20
PAD_Y = 20
FONT_SIZE = 16


class DesktopIcons:
    """Система ярлыков рабочего стола."""

    def __init__(self, font_small):
        self.font = font_small
        self.icons = []
        self.selected_id = None
        self.hovered_id = None
        self.last_click_time = 0
        self.last_click_id = None
        self.double_click_ms = 350
        self._build()

    def _build(self):
        """Раскладываем ярлыки в колонки по 5 штук."""
        col = 0
        row = 0
        for i, ic in enumerate(ICONS):
            x = PAD_X + col * CELL_W
            y = PAD_Y + row * CELL_H
            rect = pygame.Rect(x, y, ICON_W, ICON_H)
            self.icons.append({**ic, "rect": rect, "col": col, "row": row})
            row += 1
            if row >= 5:
                row = 0
                col += 1

    def update(self, mouse_pos, now_ms):
        """Обновляет hovered_id по позиции мыши."""
        self.hovered_id = None
        for ic in self.icons:
            if ic["rect"].collidepoint(mouse_pos):
                self.hovered_id = ic["id"]
                break

    def handle_click(self, mouse_pos, now_ms):
        """Клик по ярлыку. Возвращает 'open:<id>' / 'select:<id>' / None."""
        for ic in self.icons:
            if ic["rect"].collidepoint(mouse_pos):
                # Двойной клик?
                if (self.last_click_id == ic["id"]
                        and now_ms - self.last_click_time < self.double_click_ms):
                    self.last_click_id = None
                    self.last_click_time = 0
                    return f"open:{ic['id']}"
                # Одиночный
                self.selected_id = ic["id"]
                self.last_click_id = ic["id"]
                self.last_click_time = now_ms
                return f"select:{ic['id']}"
        # Клик мимо — снять выделение
        self.selected_id = None
        return None

    def draw(self, screen):
        for ic in self.icons:
            r = ic["rect"]
            selected = (ic["id"] == self.selected_id)
            hovered = (ic["id"] == self.hovered_id)

            # Подсветка
            if selected:
                sel = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                sel.fill((80, 130, 200, 140))
                screen.blit(sel, r.topleft)
                pygame.draw.rect(screen, (140, 190, 255), r, 1)
            elif hovered:
                sel = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                sel.fill((255, 255, 255, 40))
                screen.blit(sel, r.topleft)

            # Иконка (эмодзи или спец)
            if ic["id"] == "terminal":
                # Терминал — рисуем чёрный квадрат с ">_"
                icon_rect = pygame.Rect(r.centerx - 24, r.y + 8, 48, 48)
                pygame.draw.rect(screen, (15, 15, 20), icon_rect, border_radius=6)
                pygame.draw.rect(screen, ic["color"], icon_rect, 2, border_radius=6)
                txt = self.font.render(">_", True, ic["color"])
                screen.blit(txt, (icon_rect.centerx - txt.get_width() // 2,
                                   icon_rect.centery - txt.get_height() // 2))

            elif ic["id"] == "trash":
                # Корзина — серая с крышкой
                bx = r.centerx - 22
                by = r.y + 15
                # корпус
                pygame.draw.polygon(screen, (140, 140, 150), [
                    (bx, by + 12), (bx + 44, by + 12),
                    (bx + 40, by + 45), (bx + 4, by + 45)])
                pygame.draw.polygon(screen, (90, 90, 100), [
                    (bx, by + 12), (bx + 44, by + 12),
                    (bx + 40, by + 45), (bx + 4, by + 45)], 2)
                # крышка
                pygame.draw.rect(screen, (160, 160, 170), (bx - 2, by + 6, 48, 6))
                pygame.draw.rect(screen, (90, 90, 100), (bx - 2, by + 6, 48, 6), 2)
                # ручка
                pygame.draw.rect(screen, (160, 160, 170), (bx + 16, by, 12, 6))
                # полоски
                for i in range(3):
                    lx = bx + 12 + i * 10
                    pygame.draw.line(screen, (90, 90, 100),
                                     (lx, by + 16), (lx, by + 42), 1)

            else:
                # Обычный эмодзи
                icon_surf = self.font.render(ic["emoji"], True, (255, 255, 255))
                icon_surf = pygame.transform.scale_by(icon_surf, 2)
                screen.blit(icon_surf, (r.centerx - icon_surf.get_width() // 2, r.y + 12))

            # Подпись (с тенью для читаемости)
            sh = self.font.render(ic["label"], True, (0, 0, 0))
            lb = self.font.render(ic["label"], True, (255, 255, 255))
            lx = r.centerx - lb.get_width() // 2
            ly = r.bottom - 22
            screen.blit(sh, (lx + 1, ly + 1))
            screen.blit(lb, (lx, ly))
