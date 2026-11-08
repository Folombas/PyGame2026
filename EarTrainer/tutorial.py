"""Обучающий туториал — что такое интервалы и как играть."""
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
                "icon": icons.draw_music_note,
            },
            {
                "title": "Как играть?",
                "body": [
                    "1. Нажми «Слушать снова» или ПРОБЕЛ — прозвучат два звука.",
                    "2. Выбери один из четырёх вариантов ответа (или клавиши 1–4).",
                    "3. Если ответ верный — получишь XP и сохранишь сердечко.",
                    "4. Если ошибёшься — потеряешь одно сердечко.",
                ],
                "icon": icons.draw_hearts_icon,
            },
            {
                "title": "Зачем это нужно?",
                "body": [
                    "Тренировка слуха помогает подбирать мелодии,",
                    "играть в группе и импровизировать.",
                    "10 минут в день — и через месяц ты начнёшь",
                    "узнавать интервалы на слух!",
                ],
                "icon": icons.draw_star,
            },
        ]
        self.next_rect = pygame.Rect(theme.WIDTH // 2 - 100, theme.HEIGHT - 120, 200, 60)
        self.back_rect = pygame.Rect(30, theme.HEIGHT - 70, 160, 50)
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
        self.page += 1
        audio.play("click")
        if self.page >= len(self.pages):
            self.finished = True

    def update(self, dt, mouse):
        self.hover_next = self.next_rect.collidepoint(mouse)
        self.hover_back = self.back_rect.collidepoint(mouse)

    def draw(self, surf):
        surf.fill(theme.MD_BG)
        page = self.pages[self.page]
        # Заголовок
        ui.draw_text_centered(surf, page["title"], 80, 36, theme.MD_PRIMARY, bold=True)
        # Иконка
        page["icon"](surf, theme.WIDTH // 2, 160, 60, theme.MD_SECONDARY)
        # Текст
        y = 240
        for line in page["body"]:
            ui.draw_text_centered(surf, line, y, 22, theme.MD_ON_BG)
            y += 36
        # Кнопка "Далее"
        bg = theme.MD_PRIMARY if self.hover_next else theme.MD_SURFACE
        pygame.draw.rect(surf, bg, self.next_rect, border_radius=12)
        pygame.draw.rect(surf, theme.MD_PRIMARY, self.next_rect, 2, border_radius=12)
        ui.draw_text_centered(surf, "Далее →", self.next_rect.centery - 2, 22,
                              theme.MD_ON_BG if self.hover_next else theme.MD_ON_SURFACE, bold=True)
        # Кнопка "Назад"
        bb = theme.MD_SURFACE_HI if self.hover_back else theme.MD_SURFACE
        pygame.draw.rect(surf, bb, self.back_rect, border_radius=10)
        pygame.draw.rect(surf, (60, 60, 75), self.back_rect, 2, border_radius=10)
        icons.draw_arrow_left(surf, self.back_rect.x + 30, self.back_rect.centery, 20, theme.MD_ON_SURFACE)
        ui.draw_text_centered(surf, "Пропустить", self.back_rect.centery - 2, 20,
                              theme.MD_ON_SURFACE, bold=True)
