"""Экран тренажёра интервалов — полностью играбельный."""
import pygame
import random
import theme
import ui
import synth
from effects import Effects
from trainer import Session
from theory import LEVEL_TITLES, INTERVALS


class IntervalScreen:
    def __init__(self, level: int = 1, direction: str = "up"):
        self.level = level
        self.direction = direction
        self.session = Session("interval", level=level, direction=direction)
        self.effects = Effects()

        # Выбор вариантов фиксируется на текущий вопрос
        self.choices = self.session.current.choices(level)
        self._layout()

        self.feedback_text = ""
        self.feedback_color = theme.MD_ON_BG
        self.feedback_timer = 0

        self.back_clicked = False

    def _layout(self):
        W, H = theme.WIDTH, theme.HEIGHT
        # 4 кнопки вариантов, 2x2
        bw, bh = 380, 90
        gap = 20
        start_x = W // 2 - bw - gap // 2
        start_y = 380
        self.choice_rects = []
        for i in range(4):
            cx = start_x + (i % 2) * (bw + gap)
            cy = start_y + (i // 2) * (bh + gap)
            self.choice_rects.append(pygame.Rect(cx, cy, bw, bh))

        self.replay_rect = pygame.Rect(W // 2 - 140, 280, 280, 60)
        self.back_rect = pygame.Rect(30, H - 70, 160, 50)

        # hover
        self.hover_choice = -1
        self.hover_replay = False
        self.hover_back = False

    def _label_of(self, opt):
        """opt = (semitones, short, ru, diff). Возвращает 'ru (short)'."""
        return f"{opt[2]}  ({opt[1]})"

    def _play_current(self):
        self.session.current.play()

    def _submit(self, idx):
        opt = self.choices[idx]
        semitones = opt[0]
        ok = self.session.submit(semitones)

        if ok:
            self.feedback_text = "✓ Верно!"
            self.feedback_color = theme.MD_SUCCESS
            self.effects.burst(
                self.choice_rects[idx].centerx,
                self.choice_rects[idx].centery,
                theme.MD_SUCCESS,
                count=28,
                speed=6.0,
            )
            self.effects.flash(theme.MD_SUCCESS, 150)
        else:
            self.feedback_text = f"✗ Это был {self.session.current.answer_ru}"
            self.feedback_color = theme.MD_ERROR
            self.effects.burst(
                self.choice_rects[idx].centerx,
                self.choice_rects[idx].centery,
                theme.MD_ERROR,
                count=15,
                speed=3.0,
            )
            self.effects.flash(theme.MD_ERROR, 200)

        self.feedback_timer = 900
        # следующий вопрос через 700мс — но проще: сразу генерим и меняем варианты
        pygame.time.set_timer(pygame.USEREVENT + 1, 700, loops=1)

    def _next_question(self):
        self.session.next_question()
        self.choices = self.session.current.choices(self.level)
        self.feedback_text = ""
        self._play_current()

    def handle(self, e):
        if e.type == pygame.USEREVENT + 1:
            self._next_question()
            return

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.back_clicked = True
                pygame.time.set_timer(pygame.USEREVENT + 1, 0, loops=0)
                return
            if e.key == pygame.K_SPACE:
                self._play_current()
                return
            if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = e.key - pygame.K_1
                self._submit(idx)
            return

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.back_rect.collidepoint(e.pos):
                self.back_clicked = True
                pygame.time.set_timer(pygame.USEREVENT + 1, 0, loops=0)
                return
            if self.replay_rect.collidepoint(e.pos):
                self._play_current()
                return
            for i, rect in enumerate(self.choice_rects):
                if rect.collidepoint(e.pos):
                    self._submit(i)
                    return

    def update(self, dt, mouse):
        self.effects.update(dt)
        if self.feedback_timer > 0:
            self.feedback_timer -= dt

        self.hover_choice = -1
        for i, rect in enumerate(self.choice_rects):
            if rect.collidepoint(mouse):
                self.hover_choice = i
                break
        self.hover_replay = self.replay_rect.collidepoint(mouse)
        self.hover_back = self.back_rect.collidepoint(mouse)

    def draw(self, surf):
        W, H = theme.WIDTH, theme.HEIGHT
        surf.fill(theme.MD_BG)

        # Заголовок
        ui.draw_text_centered(surf, "🎼  Интервалы", 50, 42,
                              theme.MD_PRIMARY, bold=True)
        level_name = LEVEL_TITLES.get(self.level, "?")
        direction_name = "вверх" if self.direction == "up" else "вниз"
        ui.draw_text_centered(
            surf,
            f"Уровень: {level_name}  ·  Направление: {direction_name}",
            95, 18, theme.MD_MUTED,
        )

        # Статистика
        s = self.session
        stats_y = 130
        ui.draw_text_centered(
            surf,
            f"✓ {s.correct}   ✗ {s.wrong}   ·   Точность: {s.accuracy:.0f}%   ·   Стрик: {s.streak} (макс {s.best_streak})",
            stats_y, 18, theme.MD_ON_BG,
        )

        # Кнопка "Слушать снова"
        rb = theme.MD_PRIMARY if self.hover_replay else theme.MD_SURFACE
        pygame.draw.rect(surf, rb, self.replay_rect, border_radius=14)
        b = theme.MD_PRIMARY if self.hover_replay else (60, 60, 75)
        pygame.draw.rect(surf, b, self.replay_rect, 2, border_radius=14)
        ui.draw_text_centered(
            surf, "🔊  Слушать снова",
            self.replay_rect.centery - 2, 22,
            theme.MD_ON_BG if self.hover_replay else theme.MD_ON_SURFACE,
            bold=True,
        )
        ui.draw_text_centered(surf, "(ПРОБЕЛ)", self.replay_rect.bottom + 12, 14, theme.MD_MUTED)

        # Подсказка "какой интервал?"
        hint_y = 340
        ui.draw_text_centered(surf, "Какой интервал прозвучал?", hint_y, 22,
                              theme.MD_ON_BG, bold=True)

        # Кнопки вариантов
        for i, rect in enumerate(self.choice_rects):
            opt = self.choices[i]
            hov = (self.hover_choice == i)
            bg = theme.MD_SURFACE_HI if hov else theme.MD_SURFACE
            border = theme.MD_SECONDARY if hov else (60, 60, 75)
            pygame.draw.rect(surf, bg, rect, border_radius=14)
            pygame.draw.rect(surf, border, rect, 2, border_radius=14)
            # Номер слева
            num = str(i + 1)
            ui.draw_text_left(surf, num, rect.x + 16, rect.centery - 14, 26,
                              theme.MD_PRIMARY if hov else theme.MD_MUTED, bold=True)
            # Название
            ui.draw_text_left(surf, self._label_of(opt),
                              rect.x + 60, rect.centery - 14, 22,
                              theme.MD_ON_SURFACE, bold=False)

        # Обратная связь
        if self.feedback_timer > 0 and self.feedback_text:
            ui.draw_text_centered(surf, self.feedback_text, 620, 28,
                                  self.feedback_color, bold=True)

        # Кнопка "Назад"
        bb = theme.MD_SURFACE_HI if self.hover_back else theme.MD_SURFACE
        pygame.draw.rect(surf, bb, self.back_rect, border_radius=10)
        pygame.draw.rect(surf, (60, 60, 75), self.back_rect, 2, border_radius=10)
        ui.draw_text_centered(surf, "← Назад",
                              self.back_rect.centery - 2, 20,
                              theme.MD_ON_SURFACE, bold=True)

        # Частицы и вспышка
        self.effects.draw(surf)
        self.effects.draw_flash(surf)
