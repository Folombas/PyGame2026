"""EarTrainer — главное меню + роутинг экранов."""
import sys
import pygame
import theme
import ui
import icons
from screen_interval import IntervalScreen
from tutorial import TutorialScreen

pygame.init()
screen = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))
pygame.display.set_caption("EarTrainer — Тренажёр слуха")
clock = pygame.time.Clock()

MENU = "menu"
TUTORIAL = 'tutorial'
INTERVAL = "interval"
state = MENU
interval_screen = None
tutorial_screen = None

# Карточки с иконками: (key, label, desc, color, icon_fn)
MODE_CARDS = [
    ("interval", "Интервалы", "Узнавание интервалов на слух", theme.MD_PRIMARY, icons.draw_music_note),
    ("chord",    "Аккорды",   "Определение типа аккорда",     theme.MD_SECONDARY, icons.draw_music_note),
    ("note",     "Ноты",      "Абсолютный слух",              theme.MD_GOLD, icons.draw_music_note),
    ("stats",    "Статистика", "Прогресс и достижения",       theme.MD_MUTED, icons.draw_bar_chart),
]

_card_w, _card_h = 320, 110
_card_gap = 20
_start_x = theme.WIDTH // 2 - _card_w - _card_gap // 2
_start_y = 220
_card_rects = {}
for i, (key, _label, _desc, _color, _icon) in enumerate(MODE_CARDS):
    cx = _start_x + (i % 2) * (_card_w + _card_gap)
    cy = _start_y + (i // 2) * (_card_h + _card_gap)
    _card_rects[key] = pygame.Rect(cx, cy, _card_w, _card_h)

_quit_rect = pygame.Rect(theme.WIDTH // 2 - 100, 540, 200, 60)
_tutorial_rect = pygame.Rect(theme.WIDTH // 2 - 100, 480, 200, 50)
_hovered = {k: False for k in _card_rects}
_quit_hover = False


def start_interval():
    global state, interval_screen
    interval_screen = IntervalScreen(level=1, direction="up")
    state = INTERVAL
    interval_screen._play_current()


def go_menu():
    global state, interval_screen
    state = MENU
    interval_screen = None
tutorial_screen = None


running = True
while running:
    dt = clock.tick(theme.FPS)
    mouse = pygame.mouse.get_pos()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
            continue
        if state == INTERVAL and interval_screen:
            interval_screen.handle(e)
            if interval_screen.back_clicked:
                go_menu()
        elif state == TUTORIAL and tutorial_screen:
            tutorial_screen.handle(e)
            if tutorial_screen.finished:
                state = MENU
                tutorial_screen = None
        elif state == MENU:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if _card_rects["interval"].collidepoint(e.pos):
                    start_interval()
                elif _tutorial_rect.collidepoint(e.pos):
                    tutorial_screen = TutorialScreen()
                    state = TUTORIAL
                elif _quit_rect.collidepoint(e.pos):
                    running = False

    if state == INTERVAL and interval_screen:
        interval_screen.update(dt, mouse)
        interval_screen.draw(screen)
    elif state == TUTORIAL and tutorial_screen:
        tutorial_screen.update(dt, mouse)
        tutorial_screen.draw(screen)
        if tutorial_screen.finished:
            state = MENU
            tutorial_screen = None
    else:
        for k, r in _card_rects.items():
            _hovered[k] = r.collidepoint(mouse)
        _quit_hover = _quit_rect.collidepoint(mouse)

        screen.fill(theme.MD_BG)
        ui.draw_text_centered(screen, "EarTrainer", 90, 56, theme.MD_PRIMARY, bold=True)
        ui.draw_text_centered(screen, "Тренажёр музыкального слуха", 140, 22, theme.MD_MUTED)

        for key, label, desc, color, icon_fn in MODE_CARDS:
            rect = _card_rects[key]
            bg = theme.MD_SURFACE_HI if _hovered.get(key) else theme.MD_SURFACE
            pygame.draw.rect(screen, bg, rect, border_radius=16)
            border = color if _hovered.get(key) else (60, 60, 75)
            pygame.draw.rect(screen, border, rect, 2, border_radius=16)
            # Иконка
            icon_fn(screen, rect.x + 30, rect.y + 30, 30,
                    color if _hovered.get(key) else theme.MD_MUTED)
            # Текст
            ui.draw_text_left(screen, label, rect.x + 65, rect.y + 14, 24,
                             color if _hovered.get(key) else theme.MD_ON_SURFACE, bold=True)
            ui.draw_text_left(screen, desc, rect.x + 65, rect.y + 58, 16, theme.MD_MUTED)

        qbg = (60, 20, 20) if _quit_hover else theme.MD_SURFACE
        pygame.draw.rect(screen, qbg, _quit_rect, border_radius=12)
        qborder = theme.MD_ERROR if _quit_hover else (60, 60, 75)
        pygame.draw.rect(screen, qborder, _quit_rect, 2, border_radius=12)
        ui.draw_text_centered(screen, "Выход", _quit_rect.centery - 2, 22,
                              theme.MD_ERROR if _quit_hover else theme.MD_ON_SURFACE, bold=True)

        # Кнопка туториала
        ui.draw_text_centered(screen, "Как играть?", _tutorial_rect.centery - 2, 22,
                              theme.MD_SECONDARY, bold=True)
        ui.draw_text_centered(screen, "Прогресс: 0 очков  ·  Стрик: 0 дней",
                              theme.HEIGHT - 40, 16, theme.MD_MUTED)

    pygame.display.flip()

pygame.quit()
sys.exit()
