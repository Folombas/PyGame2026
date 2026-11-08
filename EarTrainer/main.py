"""EarTrainer — каркас главного окна."""
import sys
import pygame
import theme
import ui

pygame.init()
screen = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))
pygame.display.set_caption("EarTrainer — Тренажёр слуха")
clock = pygame.time.Clock()

mode_buttons = [
    ui.Button("🎼  Интервалы",  (theme.WIDTH // 2 - 320, 220, 300, 90), lambda: None),
    ui.Button("🎹  Аккорды",    (theme.WIDTH // 2 + 20,  220, 300, 90), lambda: None),
    ui.Button("🎵  Ноты",       (theme.WIDTH // 2 - 320, 340, 300, 90), lambda: None),
    ui.Button("📊  Статистика", (theme.WIDTH // 2 + 20,  340, 300, 90), lambda: None),
]
quit_btn = ui.Button(
    "Выход",
    (theme.WIDTH // 2 - 100, 520, 200, 60),
    lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)),
    accent=theme.MD_ERROR,
)
all_buttons = mode_buttons + [quit_btn]

running = True
while running:
    dt = clock.tick(theme.FPS)
    mouse = pygame.mouse.get_pos()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        for b in all_buttons:
            b.handle(e)
    for b in all_buttons:
        b.update(dt, mouse)
    screen.fill(theme.MD_BG)
    ui.draw_text_centered(screen, "EarTrainer", 110, 56, theme.MD_PRIMARY, bold=True)
    ui.draw_text_centered(screen, "Тренажёр музыкального слуха", 165, 22, theme.MD_MUTED)
    for b in all_buttons:
        b.draw(screen)
    ui.draw_text_centered(screen, "Режимы в разработке",
                          theme.HEIGHT - 40, 16, theme.MD_MUTED)
    pygame.display.flip()

pygame.quit()
sys.exit()
