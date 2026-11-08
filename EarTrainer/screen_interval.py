"""Тренажёр интервалов — с геймификацией: XP, hearts, streak, achievements."""
import pygame
import theme
import ui
import icons
import audio
from staff import Staff
import progress
from effects import Effects
from trainer import Session
from theory import LEVEL_TITLES


class IntervalScreen:
    def __init__(self, level: int = 1, direction: str = "up"):
        self.level = level
        self.direction = direction
        self.session = Session("interval", level=level, direction=direction)
        self.staff = Staff()
        self.effects = Effects()
        self.choices = self.session.current.choices(level)
        self.progress = progress.load()
        progress.check_daily_streak(self.progress)
        self._layout()
        self.feedback_text = ""
        self.feedback_color = theme.MD_ON_BG
        self.feedback_timer = 0
        self.back_clicked = False
        self.hover_choice = -1
        self.hover_replay = False
        self.hover_back = False
        self.xp_gain_pending = 0
        self.xp_gain_timer = 0

    def _layout(self):
        W = theme.WIDTH
        self.replay_rect = pygame.Rect(W // 2 - 150, 320, 300, 50)
        bw, bh = 380, 90
        gap = 20
        sx = W // 2 - bw - gap // 2
        sy = 380
        self.choice_rects = []
        for i in range(4):
            cx = sx + (i % 2) * (bw + gap)
            cy = sy + (i // 2) * (bh + gap)
            self.choice_rects.append(pygame.Rect(cx, cy, bw, bh))
        self.back_rect = pygame.Rect(30, theme.HEIGHT - 70, 160, 50)

    def _label_of(self, opt):
        return f"{opt[2]}  ({opt[1]})"

    def _play_current(self):
        q = self.session.current
        # Определяем две ноты интервала
        if q.direction == "up":
            a, b = q.root, q.root + q.semitones
        else:
            a, b = q.root - q.semitones, q.root
        self.staff.set_notes([a, b])
        q.play()

    def _submit(self, idx):
        opt = self.choices[idx]
        ok = self.session.submit(opt[0])
        result = progress.register_answer(self.progress, ok)

        if ok:
            self.feedback_text = "Верно!"
            self.feedback_color = theme.MD_SUCCESS
            self.effects.burst(
                self.choice_rects[idx].centerx,
                self.choice_rects[idx].centery,
                theme.MD_SUCCESS, count=28, speed=6.0,
            )
            self.effects.flash(theme.MD_SUCCESS, 150)
            audio.play("correct")
            if result["xp_gain"] > 0:
                self.xp_gain_pending = result["xp_gain"]
                self.xp_gain_timer = 900
        else:
            self.feedback_text = f"Ошибка. Это был {self.session.current.answer_ru}"
            self.feedback_color = theme.MD_ERROR
            self.effects.burst(
                self.choice_rects[idx].centerx,
                self.choice_rects[idx].centery,
                theme.MD_ERROR, count=15, speed=3.0,
            )
            self.effects.flash(theme.MD_ERROR, 200)
            audio.play("wrong")

        if result["leveled"]:
            audio.play("levelup")
            self.feedback_text += "  🎉 LEVEL UP!"
        if result["achievement"]:
            audio.play("achievement")
        if result["game_over"]:
            self.feedback_text = "💔 Сердечки кончились! Отдых нужен."
            pygame.time.set_timer(pygame.USEREVENT + 2, 1500, loops=1)
            return

        self.feedback_timer = 900
        pygame.time.set_timer(pygame.USEREVENT + 1, 700, loops=1)

    def _next_question(self):
        self.session.next_question()
        self.choices = self.session.current.choices(self.level)
        self.feedback_text = ""
        self._play_current()

    def _restart_session(self):
        self.session = Session("interval", level=self.level, direction=self.direction)
        self.choices = self.session.current.choices(self.level)
        self.progress["hearts"] = self.progress["max_hearts"]
        progress.save(self.progress)
        self.feedback_text = ""
        self._play_current()

    def handle(self, e):
        if e.type == pygame.USEREVENT + 1:
            self._next_question()
            return
        if e.type == pygame.USEREVENT + 2:
            self._restart_session()
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.back_clicked = True
                pygame.time.set_timer(pygame.USEREVENT + 1, 0, loops=0)
                pygame.time.set_timer(pygame.USEREVENT + 2, 0, loops=0)
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
                pygame.time.set_timer(pygame.USEREVENT + 2, 0, loops=0)
                return
            if self.replay_rect.collidepoint(e.pos):
                self._play_current()
                return
            for i, rect in enumerate(self.choice_rects):
                if rect.collidepoint(e.pos):
                    self._submit(i)
                    return

    def update(self, dt, mouse):
        self.staff.update(dt)
        self.effects.update(dt)
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
        if self.xp_gain_timer > 0:
            self.xp_gain_timer -= dt
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
        p = self.progress

        # ─── Верхняя панель: hearts, streak, level, XP ───
        ui.draw_hearts(surf, 30, 25, p["hearts"], p["max_hearts"])
        ui.draw_streak_badge(surf, W - 120, 20, p["streak_days"])

        cur_xp, req_xp = progress.xp_progress(p)
        ui.draw_xp_bar(surf, W // 2 - 150, 55, 300, 10, cur_xp, req_xp)
        f = theme.font(14, bold=True)
        lvl = f.render(f"Уровень {p['level']}", True, theme.MD_PRIMARY)
        surf.blit(lvl, lvl.get_rect(center=(W // 2, 35)))

        # ─── Заголовок ───
        title = "Интервалы"
        f2 = theme.font(32, bold=True)
        tw = f2.size(title)[0]
        x0 = W // 2 - (36 + 15 + tw) // 2
        icons.draw_music_note(surf, x0 + 18, 105, 32, theme.MD_PRIMARY)
        surf.blit(f2.render(title, True, theme.MD_PRIMARY), (x0 + 50, 88))

        level_name = LEVEL_TITLES.get(self.level, "?")
        direction_name = "вверх" if self.direction == "up" else "вниз"
        ui.draw_text_centered(
            surf, f"Уровень: {level_name}  ·  {direction_name}",
            130, 14, theme.MD_MUTED,
        )

        # ─── Нотный стан (новинка) ───
        self.staff.draw(surf, W // 2, 230)

        # ─── Кнопка "Слушать снова" ───
        rb = theme.MD_PRIMARY if self.hover_replay else theme.MD_SURFACE
        pygame.draw.rect(surf, rb, self.replay_rect, border_radius=14)
        b = theme.MD_PRIMARY if self.hover_replay else (60, 60, 75)
        pygame.draw.rect(surf, b, self.replay_rect, 2, border_radius=14)

        f3 = theme.font(20, bold=True)
        txt = f3.render("Слушать снова", True,
                        theme.MD_ON_BG if self.hover_replay else theme.MD_ON_SURFACE)
        icon_size = 22
        gap = 18
        total_w = icon_size + gap + txt.get_width()
        sx = self.replay_rect.centerx - total_w // 2
        icons.draw_speaker(surf, sx + icon_size // 2, self.replay_rect.centery,
                           icon_size,
                           theme.MD_ON_BG if self.hover_replay else theme.MD_ON_SURFACE)
        surf.blit(txt, (sx + icon_size + gap,
                        self.replay_rect.centery - txt.get_height() // 2))

        # ─── Вопрос ───
        ui.draw_text_centered(surf, "Какой интервал прозвучал?", 340, 20,
                              theme.MD_ON_BG, bold=True)

        # ─── Варианты ───
        for i, rect in enumerate(self.choice_rects):
            opt = self.choices[i]
            hov = (self.hover_choice == i)
            bg = theme.MD_SURFACE_HI if hov else theme.MD_SURFACE
            border = theme.MD_SECONDARY if hov else (60, 60, 75)
            pygame.draw.rect(surf, bg, rect, border_radius=14)
            pygame.draw.rect(surf, border, rect, 2, border_radius=14)
            num_f = theme.font(28, bold=True)
            num = num_f.render(str(i + 1), True, theme.MD_PRIMARY if hov else theme.MD_MUTED)
            surf.blit(num, (rect.x + 18, rect.centery - 16))
            ui.draw_text_left(surf, self._label_of(opt), rect.x + 65,
                              rect.centery - 12, 20, theme.MD_ON_SURFACE)

        # ─── Обратная связь ───
        if self.feedback_timer > 0 and self.feedback_text:
            ui.draw_text_centered(surf, self.feedback_text, 620, 22,
                                  self.feedback_color, bold=True)

        # ─── XP-буст ───
        if self.xp_gain_timer > 0 and self.xp_gain_pending > 0:
            alpha = max(0, int(255 * (self.xp_gain_timer / 900)))
            f4 = theme.font(22, bold=True)
            xt = f4.render(f"+{self.xp_gain_pending} XP", True, theme.MD_GOLD)
            xt.set_alpha(alpha)
            surf.blit(xt, xt.get_rect(center=(W // 2, 640 - (900 - self.xp_gain_timer) // 20)))

        # ─── Назад ───
        bb = theme.MD_SURFACE_HI if self.hover_back else theme.MD_SURFACE
        pygame.draw.rect(surf, bb, self.back_rect, border_radius=10)
        pygame.draw.rect(surf, (60, 60, 75), self.back_rect, 2, border_radius=10)
        icons.draw_arrow_left(surf, self.back_rect.x + 30, self.back_rect.centery,
                              20, theme.MD_ON_SURFACE)
        f5 = theme.font(18, bold=True)
        bt = f5.render("Назад", True, theme.MD_ON_SURFACE)
        surf.blit(bt, bt.get_rect(center=(self.back_rect.centerx + 15, self.back_rect.centery)))

        # Эффекты
        self.effects.draw(surf)
        self.effects.draw_flash(surf)

