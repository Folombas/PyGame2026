"""Обучающий туториал — 3 экрана."""
import pygame
import theme
import ui
import icons
import audio


class TutorialScreen:
    def __init__(self):
        self.page = 0
        self.pages = [
            {
                "title": "Что такое интервал?",
                "body": [
                    "Интервал — это расстояние между двумя нотами.",
                    "Например, от «до» до «соль» — это квинта.",
                    "Чем больше расстояние, тем шире звучит интервал.",
                ],
                "icon": "note",
            },
            {
                "title": "Как играть?",
                "body": [
                    "1. Нажми «Слушать снова» или ПРОБЕЛ — прозвучат два звука.",
                    "2. Выбери один из четырёх вариантов (или клавиши 1–4).",
                    "3. Верный ответ — получишь XP и сохранишь сердечко.",
                    "4. Ошибка — потеряешь одно сердечко.",
                ],
                "icon": "hearts",
            },
            {
                "title": "Зачем это нужно?",
                "body": [
                    "Тренировка слуха помогает подбирать мелодии,",
                    "играть в группе и импровизировать.",
                    "10 минут в день — и через месяц ты начнёшь",
                    "узнавать интервалы на слух!",
                ],
                "icon": "star",
            },
        ]
        self.next_rect = pygame.Rect(theme.WIDTH // 2 - 100, theme.HEIGHT - 130, 200, 55)
        self.back_rect = pygame.Rect(30, theme.HEIGHT - 130, 160, 50)
        self.finished = False
        self.hover_next = False
        self.hover_back = False

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.finished = True
            elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.next_rect.collidepoint(e.pos):
                self._advance()
            elif self.back_rect.collidepoint(e.pos):
                self.finished = True

    def _advance(self):
        audio.play("click")
        self.page += 1
        if self.page >= len(self.pages):
            self.finished = True

    def update(self, dt, mouse):
        self.hover_next = self.next_rect.collidepoint(mouse)
        self.hover_back = self.back_rect.collidepoint(mouse)

    def draw(self, surf):
        surf.fill(theme.MD_BG)
        if self.page >= len(self.pages):
            return
        page = self.pages[self.page]

        # Заголовок
        ui.draw_text_centered(surf, page["title"], 80, 36, theme.MD_PRIMARY, bold=True)

        # Иконка
        cx, cy = theme.WIDTH // 2, 165
        if page["icon"] == "note":
            icons.draw_music_note(surf, cx, cy, 50, theme.MD_SECONDARY)
        elif page["icon"] == "hearts":
            icons.draw_hearts_icon(surf, cx, cy, 50, theme.MD_ERROR)
        elif page["icon"] == "star":
            icons.draw_star(surf, cx, cy, 50, theme.MD_GOLD)

        # Текст
        y = 240
        for line in page["body"]:
            ui.draw_text_centered(surf, line, y, 20, theme.MD_ON_BG)
            y += 34

        # ─── Кнопка "Далее" ───
        bg = theme.MD_PRIMARY if self.hover_next else theme.MD_SURFACE
        pygame.draw.rect(surf, bg, self.next_rect, border_radius=12)
        pygame.draw.rect(surf, theme.MD_PRIMARY, self.next_rect, 2, border_radius=12)

        if self.page == len(self.pages) - 1:
            label = "Начать!"
        else:
            label = "Далее"

        txt_color = theme.MD_ON_PRIMARY if self.hover_next else theme.MD_ON_SURFACE
        f = theme.font(22, bold=True)
        t = f.render(label, True, txt_color)
        t_rect = t.get_rect(center=self.next_rect.center)
        surf.blit(t, t_rect)

        # Векторная стрелка справа от текста (для "Далее")
        if self.page < len(self.pages) - 1:
            icons.draw_arrow_right(
                surf,
                self.next_rect.right - 25,
                self.next_rect.centery,
                16,
                txt_color,
            )

        # ─── Кнопка "Пропустить" (слева) ───
        bb = theme.MD_SURFACE_HI if self.hover_back else theme.MD_SURFACE
        pygame.draw.rect(surf, bb, self.back_rect, border_radius=10)
        pygame.draw.rect(surf, (60, 60, 75), self.back_rect, 2, border_radius=10)
        icons.draw_arrow_left(surf, self.back_rect.x + 22, self.back_rect.centery, 18, theme.MD_ON_SURFACE)
        f2 = theme.font(18)
        sk = f2.render("Пропустить", True, theme.MD_ON_SURFACE)
        surf.blit(sk, sk.get_rect(center=(self.back_rect.centerx + 12, self.back_rect.centery)))

        # Индикатор страниц
        total = len(self.pages)
        for i in range(total):
            dot_x = theme.WIDTH // 2 - (total - 1) * 15 // 2 + i * 15
            dot_y = theme.HEIGHT - 40
            col = theme.MD_PRIMARY if i == self.page else theme.MD_MUTED
            pygame.draw.circle(surf, col, (dot_x, dot_y), 6)

        # Подсказка клавиш
        hint = theme.font(14).render("ПРОБЕЛ — далее  ·  ESC — пропустить", True, theme.MD_MUTED)
        surf.blit(hint, hint.get_rect(center=(theme.WIDTH // 2, theme.HEIGHT - 15)))
