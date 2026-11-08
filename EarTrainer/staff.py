"""Нотный стан — 5 линий, скрипичный ключ, ноты с анимацией.

Нижняя линия = E4 (MIDI 64, диат. позиция 30).
Верхняя линия = F5 (MIDI 77, диат. позиция 38).
"""
import pygame
import theme

PITCH_INFO = [
    (0, False), (0, True),   # C,  C#
    (1, False), (1, True),   # D,  D#
    (2, False),              # E
    (3, False), (3, True),   # F,  F#
    (4, False), (4, True),   # G,  G#
    (5, False), (5, True),   # A,  A#
    (6, False),              # B
]

NOTE_NAMES_RU = ["До", "До#", "Ре", "Ре#", "Ми", "Фа", "Фа#",
                 "Соль", "Соль#", "Ля", "Ля#", "Си"]

POS_E4 = 30
POS_F5 = 38


def diatonic_position(midi: int):
    """→ (диатоническая позиция, флаг диеза)."""
    octave = midi // 12 - 1
    pc = midi % 12
    dpos, sharp = PITCH_INFO[pc]
    return octave * 7 + dpos, sharp


def note_name(midi: int) -> str:
    return f"{NOTE_NAMES_RU[midi % 12]}{midi // 12 - 1}"


class Staff:
    """Нотный стан с 5 линиями."""

    def __init__(self, width: int = 600, height: int = 175):
        self.width = width
        self.height = height
        self.line_spacing = 22
        self.bottom_line_y = height // 2 + 2 * self.line_spacing
        self.notes = []
        self.note_ages = []

    def set_notes(self, midis):
        """Задать ноты. Сбрасывает анимацию (ноты падают сверху)."""
        self.notes = list(midis)
        self.note_ages = [0.0 for _ in self.notes]

    def clear(self):
        self.notes = []
        self.note_ages = []

    def update(self, dt):
        """Тикать анимацию появления нот."""
        for i in range(len(self.note_ages)):
            if self.note_ages[i] < 1.0:
                self.note_ages[i] = min(1.0, self.note_ages[i] + dt / 400.0)

    def _note_y(self, pos: int) -> float:
        offset = (pos - POS_E4) * (self.line_spacing / 2)
        return self.bottom_line_y - offset

    def _x_for_index(self, i: int, total: int) -> int:
        if total == 1:
            return self.width // 2
        spacing = 90
        total_w = spacing * (total - 1)
        return self.width // 2 - total_w // 2 + i * spacing

    def draw(self, surf, cx, cy):
        """Нарисовать стан с центром в (cx, cy)."""
        x0 = cx - self.width // 2
        y0 = cy - self.height // 2

        # Фон
        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg.fill((22, 20, 38, 230))
        surf.blit(bg, (x0, y0))
        pygame.draw.rect(surf, (70, 60, 100),
                         (x0, y0, self.width, self.height), 2, border_radius=12)

        # 5 линий стана
        top_line_y = y0 + (self.bottom_line_y - 4 * self.line_spacing)
        bottom_line_y = y0 + self.bottom_line_y
        line_color = (140, 130, 180)
        for i in range(5):
            ly = top_line_y + i * self.line_spacing
            pygame.draw.line(surf, line_color,
                             (x0 + 30, ly), (x0 + self.width - 30, ly), 2)

        # Подсказка если пусто
        if not self.notes:
            f = theme.font(16)
            hint = f.render("Слушай звук — ноты появятся здесь", True, theme.MD_MUTED)
            surf.blit(hint, hint.get_rect(center=(cx, cy)))
            return

        # Позиции всех нот
        positions = [diatonic_position(m)[0] for m in self.notes]
        min_pos = min(positions)
        max_pos = max(positions)

        # Добавочные линии снизу (для нот ниже E4)
        below = POS_E4 - min_pos
        if below > 0:
            for i in range(1, (below // 2) + 1):
                ly = bottom_line_y + i * self.line_spacing
                for j, pos in enumerate(positions):
                    if pos <= POS_E4 - 2 * i:
                        nx = x0 + self._x_for_index(j, len(self.notes))
                        pygame.draw.line(surf, line_color,
                                         (nx - 20, ly), (nx + 20, ly), 2)

        # Добавочные линии сверху (для нот выше F5)
        above = max_pos - POS_F5
        if above > 0:
            for i in range(1, (above // 2) + 1):
                ly = top_line_y - i * self.line_spacing
                for j, pos in enumerate(positions):
                    if pos >= POS_F5 + 2 * i:
                        nx = x0 + self._x_for_index(j, len(self.notes))
                        pygame.draw.line(surf, line_color,
                                         (nx - 20, ly), (nx + 20, ly), 2)

        # Головы нот с анимацией
        for i, midi in enumerate(self.notes):
            pos, sharp = diatonic_position(midi)
            nx = x0 + self._x_for_index(i, len(self.notes))
            ny_target = y0 + self._note_y(pos)
            age = self.note_ages[i] if i < len(self.note_ages) else 1.0
            self._draw_note_animated(surf, nx, ny_target, pos, sharp, midi, age)

    def _draw_note_animated(self, surf, cx, cy_target, pos, sharp, midi, age):
        """Анимация: нота падает сверху (ease-out) с fade-in."""
        t = min(1.0, age)
        ease = 1.0 - (1.0 - t) ** 3
        cy = cy_target - (1.0 - ease) * 60
        alpha = int(255 * min(1.0, t * 2.5))

        color = theme.MD_PRIMARY
        outline = (25, 15, 45)
        head_w, head_h = 22, 15

        temp = pygame.Surface((60, 100), pygame.SRCALPHA)

        # Голова
        head_rect = pygame.Rect(0, 0, head_w, head_h)
        head_rect.center = (30, 40)
        pygame.draw.ellipse(temp, color, head_rect)
        pygame.draw.ellipse(temp, outline, head_rect, 1)

        # Штиль
        stem_up = pos <= 33
        if stem_up:
            sx = 30 + head_w // 2 - 3
            pygame.draw.line(temp, color, (sx, 37), (sx, -2), 3)
        else:
            sx = 30 - head_w // 2 + 3
            pygame.draw.line(temp, color, (sx, 43), (sx, 82), 3)

        # Диез
        if sharp:
            f = theme.font(18, bold=True)
            sh = f.render("♯", True, theme.MD_SECONDARY)
            temp.blit(sh, (30 - head_w // 2 - 16, 31))

        temp.set_alpha(alpha)
        surf.blit(temp, (cx - 30, cy - 40))

        # Подпись (только когда нота почти на месте)
        if age > 0.6:
            lbl_alpha = int(255 * ((age - 0.6) / 0.4))
            f = theme.font(13)
            lbl = f.render(note_name(midi), True, theme.MD_MUTED)
            lbl.set_alpha(lbl_alpha)
            surf.blit(lbl, lbl.get_rect(center=(cx, cy_target + 75)))
