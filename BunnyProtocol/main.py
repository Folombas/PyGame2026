"""Bunny Protocol — точка входа."""
import sys
import pygame
from settings import *


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bunny Protocol")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(None, 96)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)
        self.state = "title"
        self.running = True
        self.timer = 0.0

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.running = False
            if self.state == "title" and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = "play"

    def update(self, dt):
        self.timer += dt

    def draw_title(self):
        self.screen.fill(BG)
        # Заголовок
        t = self.font_big.render("BUNNY", True, (120, 200, 255))
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 120))
        t2 = self.font_big.render("PROTOCOL", True, (255, 80, 140))
        self.screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 - 40))

        # Подзаголовок
        s = self.font.render("проникновение · стелс · данные", True, TEXT_DIM)
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 60))

        # Мигающая подсказка
        if int(self.timer * 2) % 2 == 0:
            h = self.font.render("ENTER — начать проникновение", True, TEXT)
            self.screen.blit(h, (WIDTH // 2 - h.get_width() // 2, HEIGHT // 2 + 130))

        # Управление
        ctrl = [
            "WASD / стрелки — движение",
            "E — взаимодействие с панелью",
            "Shift — бег (осторожно: громче)",
            "Esc — выход",
        ]
        for i, line in enumerate(ctrl):
            ct = self.font_small.render(line, True, TEXT_DIM)
            self.screen.blit(ct, (WIDTH // 2 - ct.get_width() // 2,
                                   HEIGHT - 140 + i * 22))

    def draw(self):
        if self.state == "title":
            self.draw_title()
        else:
            self.screen.fill(BG)
            t = self.font.render("ЗАГРУЗКА МИРА...", True, TEXT)
            self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Game().run()
