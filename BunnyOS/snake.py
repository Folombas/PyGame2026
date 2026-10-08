"""Змейка — классика в стиле Pico-8."""
import pygame
import random
import sys


# === НАСТРОЙКИ ===
CELL = 20
COLS, ROWS = 30, 22
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL
FPS = 8

# === ЦВЕТА (Pico-8 палитра) ===
C_BG      = (0, 0, 0)
C_SNAKE   = (0, 228, 54)
C_HEAD    = (255, 241, 232)
C_FOOD    = (255, 0, 77)
C_GRID    = (29, 43, 83)
C_TEXT    = (255, 241, 232)


class SnakeGame:
    def __init__(self, screen=None):
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Змейка — BunnyOS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)

        # Звуки
        self.snd_crunch = self._load_sound("assets/games/sounds/crunch.wav")
        self.snd_crash = self._load_sound("assets/games/sounds/crash.mp3")

        self.reset()

    def _load_sound(self, path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)
        self.next_dir = (1, 0)
        self.food = self._random_food()
        self.score = 0
        self.game_over = False
        self.paused = False
        self.tick = 0

    def _random_food(self):
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in self.snake:
                return pos

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key == pygame.K_SPACE and not self.game_over:
                    self.paused = not self.paused
                if self.game_over and e.key == pygame.K_RETURN:
                    self.reset()
                if not self.paused and not self.game_over:
                    if e.key in (pygame.K_UP, pygame.K_w) and self.direction != (0, 1):
                        self.next_dir = (0, -1)
                    elif e.key in (pygame.K_DOWN, pygame.K_s) and self.direction != (0, -1):
                        self.next_dir = (0, 1)
                    elif e.key in (pygame.K_LEFT, pygame.K_a) and self.direction != (1, 0):
                        self.next_dir = (-1, 0)
                    elif e.key in (pygame.K_RIGHT, pygame.K_d) and self.direction != (-1, 0):
                        self.next_dir = (1, 0)
        return True

    def _update(self):
        if self.paused or self.game_over:
            return
        self.tick += 1
        if self.tick < 5:
            return
        self.tick = 0

        self.direction = self.next_dir
        hx, hy = self.snake[0]
        nx, ny = hx + self.direction[0], hy + self.direction[1]

        # Стены
        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            self._die()
            return
        # Себя
        if (nx, ny) in self.snake[:-1]:
            self._die()
            return

        self.snake.insert(0, (nx, ny))

        # Еда
        if (nx, ny) == self.food:
            self.score += 1
            if self.snd_crunch:
                self.snd_crunch.play()
            self.food = self._random_food()
        else:
            self.snake.pop()

    def _die(self):
        self.game_over = True
        if self.snd_crash:
            self.snd_crash.play()

    def _draw(self):
        self.screen.fill(C_BG)
        # Сетка
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(self.screen, C_GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(self.screen, C_GRID, (0, y), (WIDTH, y))
        # Еда
        fx, fy = self.food
        pygame.draw.rect(self.screen, C_FOOD,
                         (fx * CELL + 2, fy * CELL + 2, CELL - 4, CELL - 4),
                         border_radius=4)
        # Змейка
        for i, (x, y) in enumerate(self.snake):
            col = C_HEAD if i == 0 else C_SNAKE
            pygame.draw.rect(self.screen, col,
                             (x * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2),
                             border_radius=3)
        # Счёт
        sc = self.font.render(f"Счёт: {self.score}", True, C_TEXT)
        self.screen.blit(sc, (10, 10))

        if self.paused:
            self._center_text("ПАУЗА", self.big_font)
        if self.game_over:
            self._center_text(f"ИГРА ОКОНЧЕНА\nСчёт: {self.score}", self.big_font)
            hint = self.font.render("Enter — заново, Esc — выход", True, C_TEXT)
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 40))

    def _center_text(self, text, font):
        lines = text.split("\n")
        total_h = len(lines) * font.get_height()
        y0 = HEIGHT // 2 - total_h // 2
        for i, line in enumerate(lines):
            surf = font.render(line, True, C_TEXT)
            x = WIDTH // 2 - surf.get_width() // 2
            self.screen.blit(surf, (x, y0 + i * font.get_height()))

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            if not self._handle_events():
                break
            self._update()
            self._draw()
            pygame.display.flip()
        return True  # вернуться в ОС


if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init()
    game = SnakeGame()
    game.run()
    pygame.quit()
    sys.exit(0)
