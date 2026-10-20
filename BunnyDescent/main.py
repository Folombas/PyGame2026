"""Bunny's Descent — roguelike в вселенной BunnyOS."""
import sys
import pygame
from settings import *


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bunny's Descent")
        self.clock = pygame.time.Clock()
        self.running = True

        # Шрифты
        self.font_big = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)

        self.state = "title"
        self.timer = 0.0

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == "title" and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state = "game"
                    self.timer = 0.0

    def update(self, dt):
        self.timer += dt

    def draw_title(self):
        self.screen.fill(C_BG)
        # Заголовок
        title = self.font_big.render("BUNNY'S DESCENT", True, C_GOLD)
        tx = WIDTH // 2 - title.get_width() // 2
        self.screen.blit(title, (tx, HEIGHT // 2 - 100))

        sub = self.font.render("Провал в систему", True, C_ACCENT)
        sx = WIDTH // 2 - sub.get_width() // 2
        self.screen.blit(sub, (sx, HEIGHT // 2 - 30))

        # Мигающая подсказка
        if int(self.timer * 2) % 2 == 0:
            hint = self.font.render("Нажми ENTER чтобы начать", True, C_TEXT)
            hx = WIDTH // 2 - hint.get_width() // 2
            self.screen.blit(hint, (hx, HEIGHT // 2 + 60))

        # Версия
        v = self.font_small.render("v0.1 — roguelike prototype", True, C_TEXT_DIM)
        self.screen.blit(v, (20, HEIGHT - 30))

    def draw(self):
        if self.state == "title":
            self.draw_title()
        elif self.state == "game":
            self.screen.fill(C_BG)
            txt = self.font.render("Уровень 1 — загрузка...", True, C_TEXT)
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Game().run()
