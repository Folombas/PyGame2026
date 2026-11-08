"""Нотный стан — визуализация нот на 5 линиях (скрипичный ключ).

Без диезов/бемолей показывает ноту в её натуральной позиции, диез
рисуется знаком ♯ слева от головы. Добавочные линии рисуются автоматически.
"""
import pygame
import theme

# Питч-класс (0=C..11=B) → (диатоническая позиция в октаве, есть_диез)
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

# Опорные точки скрипичного ключа:
#   Нижняя линия = E4 = диатоническая позиция 30
#   Верхняя линия = F5 = диатоническая позиция 38
POS_E4 = 30
POS_F5 = 38


def diatonic_position(midi: int):
    """Возвращает (диатоническая_позиция, флаг_диеза)."""
    octave = midi // 12 - 1
    pc = midi % 12
    dpos, sharp = PITCH_INFO[pc]
    return octave * 7 + dpos, sharp


def note_name(midi: int):
    """Возвращает 'До4', 'Фа#5' и т.п."""
    return f"{NOTE_NAMES_RU[midi % 12]}{midi // 12 - 1}"


class Staff:
    """Нотный стан с 5 линиями и нотами."""

    def __init__(self, width: int = 560, height: int = 170):
        self.width = width
        self.height = height
        self.line_spacing = 22  # расстояние между линиями
        # Y нижней линии стана внутри виджета
        self.bottom_line_y = height // 2 + 2 * self.line_spacing
        self.notes = []  # список midi-нот для отрисовки

    def set_notes(self, midis):
        """Задать ноты, которые нужно показать."""
        self.notes = list(midis)

    def clear(self):
        self.notes = []

    def _note_y(self, pos: int) -> float:
        """Y нотной головы (центра) внутри виджета по диатонической позиции."""
        offset = (pos - POS_E4) * (self.line_spacing / 2)
        return self.bottom_line_y - offset

    def _x_for_index(self, i: int, total: int) -> int:
        """X-позиция для i-й ноты из total. Центрируем."""
        if total == 1:
            return self.width // 2
        spacing = 90
        total_w = spacing * (total - 1)
        return self.width // 2 - total_w // 2 + i * spacing

    def draw(self, surf, cx, cy):
        """Нарисовать стан с центром виджета в (cx, cy)."""
        x0 = cx - self.width // 2
        y0 = cy - self.height // 2

        # Фон стана
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

        if not self.notes:
            # Пока ничего не задано — показываем подсказку
            f = theme.font(16)
            hint = f.render("🎵 нажми ПРОБЕЛ или «Слушать снова»", True, theme.MD_MUTED)
            surf.blit(hint, hint.get_rect(center=(cx, cy)))
            return

        # Пред-расчёт: диатонические позиции всех нот
        positions = [diatonic_position(m)[0] for m in self.notes]
        min_pos = min(positions)
        max_pos = max(positions)

        # Добавочные линии снизу
        below = POS_E4 - min_pos
        if below > 0:
            for i in range(1, (below // 2) + 1):
                ly = bottom_line_y + i * self.line_spacing
                # рисуем только там, где нужна нота
                for j, pos in enumerate(positions):
                    if pos <= POS_E4 - 2 * i:
                        nx = x0 + self._x_for_index(j, len(self.notes))
                        pygame.draw.line(surf, line_color,
                                         (nx - 20, ly), (nx + 20, ly), 2)

        # Добавочные линии сверху
        above = max_pos - POS_F5
        if above > 0:
            for i in range(1, (above // 2) + 1):
                ly = top_line_y - i * self.line_spacing
                for j, pos in enumerate(positions):
                    if pos >= POS_F5 + 2 * i:
                        nx = x0 + self._x_for_index(j, len(self.notes))
                        pygame.draw.line(surf, line_color,
                                         (nx - 20, ly), (nx + 20, ly), 2)

        # Головы нот
        for i, midi in enumerate(self.notes):
            pos, sharp = diatonic_position(midi)
            nx = x0 + self._x_for_index(i, len(self.notes))
            ny = y0 + self._note_y(pos)
            self._draw_note_head(surf, nx, ny, pos, sharp)

    def _draw_note_head(self, surf, cx, cy, pos, sharp):
        """Отрисовка головы + штиля + знака диеза."""
        color = theme.MD_PRIMARY
        outline = (25, 15, 45)
        head_w, head_h = 22, 15

        # Голова ноты
        head_rect = pygame.Rect(0, 0, head_w, head_h)
        head_rect.center = (cx, cy)
        pygame.draw.ellipse(surf, color, head_rect)
        pygame.draw.ellipse(surf, outline, head_rect, 1)

        # Штиль — вверх, если нота ниже средней линии (pos < 34)
        stem_up = pos <= 33
        if stem_up:
            sx = cx + head_w // 2 - 3
            sy_from = cy - 3
            sy_to = cy - 42
        else:
            sx = cx - head_w // 2 + 3
            sy_from = cy + 3
            sy_to = cy + 42
        pygame.draw.line(surf, color, (sx, sy_from), (sx, sy_to), 3)

        # Диез — слева от головы
        if sharp:
            f = theme.font(18, bold=True)
            sh = f.render("♯", True, theme.MD_SECONDARY)
            surf.blit(sh, (cx - head_w // 2 - 16, cy - 9))

        # Название ноты под станом
        f = theme.font(13)
        lbl = f.render(note_name(self._midi_of_pos(pos, sharp)), True, theme.MD_MUTED)
        surf.blit(lbl, lbl.get_rect(center=(cx, cy + 75)))

    def _midi_of_pos(self, pos, sharp):
        """Обратное преобразование (для подписи)."""
        # Ищем midi, у которого diatonic_position даёт (pos, sharp)
        # Простой перебор в разумном диапазоне
        for midi in range(20, 108):
            p, s = diatonic_position(midi)
            if p == pos and s == sharp:
                return midi
        return 60
