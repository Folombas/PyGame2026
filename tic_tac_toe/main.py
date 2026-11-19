import pygame
import sys
import math
import random
import os

# --- Настройки ---
WIDTH, HEIGHT = 600, 750
FPS = 60
GRID_SIZE = 3
CELL_SIZE = 150
GRID_OFFSET_X = (WIDTH - GRID_SIZE * CELL_SIZE) // 2
GRID_OFFSET_Y = 180

# Цвета (Неоновая палитра)
BG_COLOR = (15, 15, 25)
GRID_COLOR = (50, 50, 80)
PLAYER_COLOR = (0, 255, 255)   # X
AI_COLOR = (255, 50, 150)      # O
TEXT_COLOR = (220, 220, 255)
BUTTON_COLOR = (40, 40, 60)
BUTTON_HOVER = (60, 60, 90)
WIN_LINE_COLOR = (255, 255, 100)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Tic-Tac-Toe")
clock = pygame.time.Clock()

# --- Загрузка шрифтов ---
try:
    font_title = pygame.font.Font("assets/fonts/Orbitron.ttf", 48)
    font_main = pygame.font.Font("assets/fonts/Orbitron.ttf", 28)
    font_small = pygame.font.Font("assets/fonts/Orbitron.ttf", 20)
except:
    font_title = pygame.font.SysFont("dejavusans", 48, bold=True)
    font_main = pygame.font.SysFont("dejavusans", 28, bold=True)
    font_small = pygame.font.SysFont("dejavusans", 20)

# --- Загрузка звуков ---
try:
    snd_click = pygame.mixer.Sound("assets/sounds/click.wav")
except:
    snd_click = None

def generate_tone(freq, duration, volume=0.1):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        val = int(32767 * volume * math.sin(2 * math.pi * freq * t))
        buf.extend(val.to_bytes(2, 'little', signed=True))
    return pygame.mixer.Sound(buffer=buf)

snd_win = generate_tone(880, 0.3, 0.15)
snd_lose = generate_tone(220, 0.4, 0.15)
snd_draw = generate_tone(440, 0.2, 0.1)

# --- Игровая логика ---
class Board:
    def __init__(self):
        self.grid = [[None]*3 for _ in range(3)]
        self.winner = None
        self.win_line = None

    def available_moves(self):
        return [(r, c) for r in range(3) for c in range(3) if self.grid[r][c] is None]

    def make_move(self, r, c, player):
        if self.grid[r][c] is None:
            self.grid[r][c] = player
            self.check_winner()
            return True
        return False

    def check_winner(self):
        # Проверка строк, столбцов и диагоналей
        for i in range(3):
            if self.grid[i][0] == self.grid[i][1] == self.grid[i][2] and self.grid[i][0]:
                self.winner = self.grid[i][0]
                self.win_line = ((0, i), (1, i), (2, i))
                return
            if self.grid[0][i] == self.grid[1][i] == self.grid[2][i] and self.grid[0][i]:
                self.winner = self.grid[0][i]
                self.win_line = ((i, 0), (i, 1), (i, 2))
                return
        if self.grid[0][0] == self.grid[1][1] == self.grid[2][2] and self.grid[0][0]:
            self.winner = self.grid[0][0]
            self.win_line = ((0, 0), (1, 1), (2, 2))
            return
        if self.grid[0][2] == self.grid[1][1] == self.grid[2][0] and self.grid[0][2]:
            self.winner = self.grid[0][2]
            self.win_line = ((0, 2), (1, 1), (2, 0))
            return
        if not self.available_moves():
            self.winner = "Draw"

    def reset(self):
        self.__init__()

# --- ИИ (Минимакс с альфа-бета отсечением) ---
def minimax(board, depth, alpha, beta, is_maximizing):
    if board.winner == 'O':
        return 10 - depth
    if board.winner == 'X':
        return depth - 10
    if board.winner == "Draw":
        return 0

    if is_maximizing:
        max_eval = -math.inf
        for r, c in board.available_moves():
            board.grid[r][c] = 'O'
            board.check_winner()
            eval = minimax(board, depth + 1, alpha, beta, False)
            board.grid[r][c] = None
            board.winner = None
            board.win_line = None
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r, c in board.available_moves():
            board.grid[r][c] = 'X'
            board.check_winner()
            eval = minimax(board, depth + 1, alpha, beta, True)
            board.grid[r][c] = None
            board.winner = None
            board.win_line = None
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_ai_move(board, difficulty):
    if difficulty == "Easy":
        moves = board.available_moves()
        return random.choice(moves) if moves else None
    elif difficulty == "Medium":
        # 50% шанс на оптимальный ход, 50% на случайный
        if random.random() < 0.5:
            moves = board.available_moves()
            return random.choice(moves) if moves else None
    # Hard / Impossible
    best_score = -math.inf
    best_move = None
    for r, c in board.available_moves():
        board.grid[r][c] = 'O'
        board.check_winner()
        score = minimax(board, 0, -math.inf, math.inf, False)
        board.grid[r][c] = None
        board.winner = None
        board.win_line = None
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return best_move

# --- Класс игры ---
class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = 'X'
        self.game_over = False
        self.difficulty = "Hard"
        self.paused = False
        self.state = "MENU"  # MENU, PLAYING, PAUSED, GAME_OVER
        self.winner_display_timer = 0
        self.hover_cell = None

    def reset(self):
        self.board.reset()
        self.current_player = 'X'
        self.game_over = False
        self.winner_display_timer = 0

    def handle_click(self, pos):
        if self.state != "PLAYING" or self.game_over:
            return
        x, y = pos
        if GRID_OFFSET_X <= x < GRID_OFFSET_X + GRID_SIZE*CELL_SIZE and GRID_OFFSET_Y <= y < GRID_OFFSET_Y + GRID_SIZE*CELL_SIZE:
            c = (x - GRID_OFFSET_X) // CELL_SIZE
            r = (y - GRID_OFFSET_Y) // CELL_SIZE
            if self.board.make_move(r, c, self.current_player):
                if snd_click: snd_click.play()
                if self.board.winner:
                    self.game_over = True
                    if self.board.winner == 'X': snd_win.play()
                    elif self.board.winner == 'O': snd_lose.play()
                    else: snd_draw.play()
                else:
                    self.current_player = 'O' if self.current_player == 'X' else 'X'

    def update_ai(self):
        if self.state == "PLAYING" and not self.game_over and self.current_player == 'O':
            move = get_ai_move(self.board, self.difficulty)
            if move:
                r, c = move
                self.board.make_move(r, c, 'O')
                if self.board.winner:
                    self.game_over = True
                    if self.board.winner == 'O': snd_lose.play()
                    elif self.board.winner == 'X': snd_win.play()
                    else: snd_draw.play()
                else:
                    self.current_player = 'X'

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        if self.state == "MENU":
            self.draw_menu(surface)
            return

        # Заголовок
        title = font_title.render("NEON TIC-TAC-TOE", True, PLAYER_COLOR)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 40))

        # Сетка
        for i in range(1, GRID_SIZE):
            pygame.draw.line(surface, GRID_COLOR, 
                             (GRID_OFFSET_X + i*CELL_SIZE, GRID_OFFSET_Y),
                             (GRID_OFFSET_X + i*CELL_SIZE, GRID_OFFSET_Y + GRID_SIZE*CELL_SIZE), 3)
            pygame.draw.line(surface, GRID_COLOR,
                             (GRID_OFFSET_X, GRID_OFFSET_Y + i*CELL_SIZE),
                             (GRID_OFFSET_X + GRID_SIZE*CELL_SIZE, GRID_OFFSET_Y + i*CELL_SIZE), 3)

        # Подсветка наведения
        if self.hover_cell and not self.game_over and self.state == "PLAYING":
            hr, hc = self.hover_cell
            pygame.draw.rect(surface, (40, 40, 60), 
                             (GRID_OFFSET_X + hc*CELL_SIZE, GRID_OFFSET_Y + hr*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # Фигуры
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.board.grid[r][c]:
                    center = (GRID_OFFSET_X + c*CELL_SIZE + CELL_SIZE//2, GRID_OFFSET_Y + r*CELL_SIZE + CELL_SIZE//2)
                    color = PLAYER_COLOR if self.board.grid[r][c] == 'X' else AI_COLOR
                    if self.board.grid[r][c] == 'X':
                        # Рисуем X
                        offset = 30
                        pygame.draw.line(surface, color, (center[0]-offset, center[1]-offset), (center[0]+offset, center[1]+offset), 8)
                        pygame.draw.line(surface, color, (center[0]+offset, center[1]-offset), (center[0]-offset, center[1]+offset), 8)
                    else:
                        # Рисуем O
                        pygame.draw.circle(surface, color, center, 40, 8)

        # Линия победы
        if self.board.win_line:
            start = (GRID_OFFSET_X + self.board.win_line[0][1]*CELL_SIZE + CELL_SIZE//2,
                     GRID_OFFSET_Y + self.board.win_line[0][0]*CELL_SIZE + CELL_SIZE//2)
            end = (GRID_OFFSET_X + self.board.win_line[2][1]*CELL_SIZE + CELL_SIZE//2,
                   GRID_OFFSET_Y + self.board.win_line[2][0]*CELL_SIZE + CELL_SIZE//2)
            pygame.draw.line(surface, WIN_LINE_COLOR, start, end, 10)

        # Статус
        if self.game_over:
            if self.board.winner == "Draw":
                msg = "НИЧЬЯ!"
            elif self.board.winner == 'X':
                msg = "ТЫ ПОБЕДИЛ!"
            else:
                msg = "ПОБЕДИЛ ИИ!"
            status = font_main.render(msg, True, WIN_LINE_COLOR)
            surface.blit(status, (WIDTH//2 - status.get_width()//2, 620))
            
            # Кнопка рестарта
            btn_rect = pygame.Rect(WIDTH//2 - 100, 670, 200, 50)
            pygame.draw.rect(surface, BUTTON_COLOR, btn_rect, border_radius=10)
            btn_text = font_main.render("ЗАНОВО", True, TEXT_COLOR)
            surface.blit(btn_text, (btn_rect.centerx - btn_text.get_width()//2, btn_rect.centery - btn_text.get_height()//2))
        else:
            turn_msg = "ТВОЙ ХОД" if self.current_player == 'X' else "ХОД ИИ..."
            status = font_small.render(turn_msg, True, TEXT_COLOR)
            surface.blit(status, (WIDTH//2 - status.get_width()//2, 620))

        # Пауза
        if self.state == "PAUSED":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            pause_text = font_title.render("ПАУЗА", True, WIN_LINE_COLOR)
            surface.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 50))
            cont_text = font_small.render("ESC - Продолжить", True, TEXT_COLOR)
            surface.blit(cont_text, (WIDTH//2 - cont_text.get_width()//2, HEIGHT//2 + 20))

    def draw_menu(self, surface):
        title = font_title.render("NEON TIC-TAC-TOE", True, PLAYER_COLOR)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        # Кнопка Старт
        btn_start = pygame.Rect(WIDTH//2 - 150, 250, 300, 60)
        mouse_pos = pygame.mouse.get_pos()
        color = BUTTON_HOVER if btn_start.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_start, border_radius=15)
        start_text = font_main.render("СТАРТ ИГРЫ", True, TEXT_COLOR)
        surface.blit(start_text, (btn_start.centerx - start_text.get_width()//2, btn_start.centery - start_text.get_height()//2))

        # Кнопка Сложность
        btn_diff = pygame.Rect(WIDTH//2 - 150, 340, 300, 60)
        color = BUTTON_HOVER if btn_diff.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_diff, border_radius=15)
        diff_text = font_main.render(f"СЛОЖНОСТЬ: {self.difficulty}", True, TEXT_COLOR)
        surface.blit(diff_text, (btn_diff.centerx - diff_text.get_width()//2, btn_diff.centery - diff_text.get_height()//2))

        # Кнопка Выход
        btn_exit = pygame.Rect(WIDTH//2 - 150, 430, 300, 60)
        color = BUTTON_HOVER if btn_exit.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_exit, border_radius=15)
        exit_text = font_main.render("ВЫХОД", True, TEXT_COLOR)
        surface.blit(exit_text, (btn_exit.centerx - exit_text.get_width()//2, btn_exit.centery - exit_text.get_height()//2))

        # Инструкция
        info = font_small.render("Клик по клетке - поставить X", True, (150, 150, 180))
        surface.blit(info, (WIDTH//2 - info.get_width()//2, 600))
        info2 = font_small.render("ESC - пауза / выход из игры", True, (150, 150, 180))
        surface.blit(info2, (WIDTH//2 - info2.get_width()//2, 630))

# --- Главный цикл ---
def main():
    game = Game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == "PLAYING":
                        game.state = "PAUSED"
                    elif game.state == "PAUSED":
                        game.state = "PLAYING"
                    elif game.state == "GAME_OVER" or game.state == "MENU":
                        game.state = "MENU"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == "MENU":
                    mx, my = event.pos
                    if pygame.Rect(WIDTH//2 - 150, 250, 300, 60).collidepoint(event.pos):
                        game.reset()
                        game.state = "PLAYING"
                        if snd_click: snd_click.play()
                    elif pygame.Rect(WIDTH//2 - 150, 340, 300, 60).collidepoint(event.pos):
                        diffs = ["Easy", "Medium", "Hard"]
                        idx = diffs.index(game.difficulty)
                        game.difficulty = diffs[(idx + 1) % 3]
                        if snd_click: snd_click.play()
                    elif pygame.Rect(WIDTH//2 - 150, 430, 300, 60).collidepoint(event.pos):
                        running = False
                elif game.state == "PLAYING":
                    if game.game_over:
                        btn_rect = pygame.Rect(WIDTH//2 - 100, 670, 200, 50)
                        if btn_rect.collidepoint(event.pos):
                            game.reset()
                            game.state = "PLAYING"
                            if snd_click: snd_click.play()
                    else:
                        game.handle_click(event.pos)

            if event.type == pygame.MOUSEMOTION and game.state == "PLAYING":
                mx, my = event.pos
                if GRID_OFFSET_X <= mx < GRID_OFFSET_X + GRID_SIZE*CELL_SIZE and GRID_OFFSET_Y <= my < GRID_OFFSET_Y + GRID_SIZE*CELL_SIZE:
                    game.hover_cell = ((my - GRID_OFFSET_Y) // CELL_SIZE, (mx - GRID_OFFSET_X) // CELL_SIZE)
                else:
                    game.hover_cell = None

        # Логика ИИ
        if game.state == "PLAYING" and not game.game_over:
            game.update_ai()

        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
