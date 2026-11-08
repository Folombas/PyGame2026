"""Тренажёр интервалов — играбельный, без emoji (векторные иконки)."""
import pygame
import theme
import ui
import icons
from effects import Effects
from trainer import Session
from theory import LEVEL_TITLES


class IntervalScreen:
    def __init__(self, level: int = 1, direction: str = "up"):
        self.level = level
        self.direction = direction
        self.session = Session("interval", level=level, direction=direction)
        self.effects = Effects()
        self.choices = self.session.current.choices(level)
        self._layout()
        self.feedback_text = ""
        self.feedback_color = theme.MD_ON_BG
        self.feedback_timer = 0
        self.back_clicked = False
        self.hover_choice = -1
        self.hover_replay = False
        self.hover_back = False

    def _layout(self):
        W = theme.WIDTH
        # Replay button
        self.replay_rect = pygame.Rect(W // 2 - 150, 200, 300, 56)
        # 4 варианта — 2x2
        bw, bh = 380, 90
        gap = 20
        sx = W // 2 - bw - gap // 2
        sy = 380
        self.choice_rects = []
        for i in range(4):
            cx = sx + (i % 2) * (bw + gap)
            cy = sy + (i // 2) * (bh + gap)
            self.choice_rects.append(pygame.Rect(cx, cy, bw, bh))
        # Back
        self.back_rect = pygame.Rect(30, theme.HEIGHT - 70, 160, 50)

    def _label_of(self, opt):
        return f"{opt[2]}  ({opt[1]})"

    def _play_current(self):
        self.session.current.play()

    def _submit(self, idx):
        opt = self.choices[idx]
        ok = self.session.submit(opt[0])

        if ok:
            self.feedback_text = "Верно!"
            self.feedback_color = theme.MD_SUCCESS
            self.effects.burst(
                self.choice_rects[idx].centerx,
                self.choice_rects[idx].centery,
                theme.MD_SUCCESS, count=28, speed=6.0,
            )
            self.effects.flash(theme.MD_SUCCESS, 150)
        else:
            self.feedback_text = f"Ошибка. Это был {self.session.current.answer_ru}"
            self.feedback_color = theme.MD_ERROR
            self.effects.burst(
                self.choice_rects[idx].centerx,
                self.choice_rects[idx].centery,
                theme.MD_ERROR, count=15, speed=3.0,
            )
            self.effects.flash(theme.MD_ERROR, 200)

        self.feedback_timer = 900
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
                self._submit(e.key - pygame.K_1)
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
        W = theme.WIDTH
        surf.fill(theme.MD_BG)

        # Заголовок с векторной иконкой ноты
        title = "Интервалы"
        f = theme.font(42, bold=True)
        tw = f.size(title)[0]
        total = 40 + 15 + tw
        x0 = W // 2 - total // 2
        icons.draw_music_note(surf, x0 + 20, 60, 40, theme.MD_PRIMARY)
        surf.blit(f.render(title, True, theme.MD_PRIMARY), (x0 + 55, 36))

        # Уровень
        level_name = LEVEL_TITLES.get(self.level, "?")
        direction_name = "вверх" if self.direction == "up" else "вниз"
        ui.draw_text_centered(
            surf, f"Уровень: {level_name}  ·  Направление: {direction_name}",
            105, 18, theme.MD_MUTED,
        )

        # Статистика — с векторными ✓ и ✗
        s = self.session
        y_stats = 145
        # Верно
        icons.draw_check(surf, W // 2 - 240, y_stats, 16, theme.MD_SUCCESS)
        ui.draw_text_left(surf, str(s.correct), W // 2 - 225, y_stats - 10, 18, theme.MD_SUCCESS, bold=True)
        # Ошибок
        icons.draw_cross(surf, W // 2 - 130, y_stats, 16, theme.MD_ERROR)
        ui.draw_text_left(surf, str(s.wrong), W // 2 - 115, y_stats - 10, 18, theme.MD_ERROR, bold=True)
        # Остальное
        ui.draw_text_left(
            surf,
            f"·  Точность: {s.accuracy:.0f}%  ·  Стрик: {s.streak} (макс {s.best_streak})",
            W // 2 - 50, y_stats - 10, 18, theme.MD_ON_BG,
        )

        # Кнопка "Слушать снова"
        rb = theme.MD_PRIMARY if self.hover_replay else theme.MD_SURFACE
        pygame.draw.rect(surf, rb, self.replay_rect, border_radius=14)
        b = theme.MD_PRIMARY if self.hover_replay else (60, 60, 75)
        pygame.draw.rect(surf, b, self.replay_rect, 2, border_radius=14)
        icons.draw_speaker(surf, self.replay_rect.centerx - 90, self.replay_rect.centery, 24, theme.MD_ON_BG)
        f2 = theme.font(22, bold=True)
        txt = f2.render("Слушать снова", True, theme.MD_ON_BG if self.hover_replay else theme.MD_ON_SURFACE)
        surf.blit(txt, txt.get_rect(center=(self.replay_rect.centerx + 15, self.replay_rect.centery)))

        # Подсказка "ПРОБЕЛ" — отдельной строкой НИЖЕ кнопки
        ui.draw_text_centered(surf, "нажми ПРОБЕЛ", self.replay_rect.bottom + 15, 14, theme.MD_MUTED)

        # Вопрос
        ui.draw_text_centered(surf, "Какой интервал прозвучал?", 340, 22, theme.MD_ON_BG, bold=True)

        # Кнопки вариантов
        for i, rect in enumerate(self.choice_rects):
            opt = self.choices[i]
            hov = (self.hover_choice == i)
            bg = theme.MD_SURFACE_HI if hov else theme.MD_SURFACE
            border = theme.MD_SECONDARY if hov else (60, 60, 75)
            pygame.draw.rect(surf, bg, rect, border_radius=14)
            pygame.draw.rect(surf, border, rect, 2, border_radius=14)
            # Номер
            num_f = theme.font(28, bold=True)
            num = num_f.render(str(i + 1), True, theme.MD_PRIMARY if hov else theme.MD_MUTED)
            surf.blit(num, (rect.x + 18, rect.centery - 16))
            # Название
            ui.draw_text_left(surf, self._label_of(opt), rect.x + 65, rect.centery - 14, 22,
                              theme.MD_ON_SURFACE)

        # Обратная связь
        if self.feedback_timer > 0 and self.feedback_text:
            ui.draw_text_centered(surf, self.feedback_text, 620, 28, self.feedback_color, bold=True)

        # Back кнопка
        bb = theme.MD_SURFACE_HI if self.hover_back else theme.MD_SURFACE
        pygame.draw.rect(surf, bb, self.back_rect, border_radius=10)
        pygame.draw.rect(surf, (60, 60, 75), self.back_rect, 2, border_radius=10)
        icons.draw_arrow_left(surf, self.back_rect.x + 30, self.back_rect.centery, 20, theme.MD_ON_SURFACE)
        f3 = theme.font(20, bold=True)
        bt = f3.render("Назад", True, theme.MD_ON_SURFACE)
        surf.blit(bt, bt.get_rect(center=(self.back_rect.centerx + 15, self.back_rect.centery)))

        # Частицы + вспышка
        self.effects.draw(surf)
        self.effects.draw_flash(surf)
