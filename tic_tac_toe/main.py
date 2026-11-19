import pygame
import sys
import math
import random

# --- Настройки ---
WIDTH, HEIGHT = 600, 800 # Чуть увеличили высоту для нижних кнопок
FPS = 60
GRID_SIZE = 3
CELL_SIZE = 140
GRID_OFFSET_X = (WIDTH - GRID_SIZE * CELL_SIZE) // 2
GRID_OFFSET_Y = 160

# Цвета
BG_COLOR = (15, 15, 25)
GRID_COLOR = (50, 50, 80)
PLAYER_COLOR = (0, 255, 255)   # X
AI_COLOR = (255, 50, 150)      # O
TEXT_COLOR = (220, 220, 255)
BUTTON_COLOR = (40, 40, 60)
BUTTON_HOVER = (60, 60, 90)
WIN_LINE_COLOR = (255, 255, 100)
THINKING_COLOR = (255, 200, 50)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Tic-Tac-Toe")
clock = pygame.time.Clock()

# Шрифты
try:
    font_title = pygame.font.Font("assets/fonts/RussoOne.ttf", 44)
    font_main = pygame.font.Font("assets/fonts/RussoOne.ttf", 24)
    font_small = pygame.font.Font("assets/fonts/RussoOne.ttf", 18)
except:
    font_title = pygame.font.SysFont("dejavusans", 44, bold=True)
    font_main = pygame.font.SysFont("dejavusans", 24, bold=True)
    font_small = pygame.font.SysFont("dejavusans", 18)

# Звуки
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

# --- Логика поля ---
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
        self.grid = [[None]*3 for _ in range(3)]
        self.winner = None
        self.win_line = None

# --- ИИ ---
def minimax(board, depth, alpha, beta, is_maximizing, ai_sym, player_sym):
    if board.winner == ai_sym: return 10 - depth
    if board.winner == player_sym: return depth - 10
    if board.winner == "Draw": return 0

    if is_maximizing:
        max_eval = -math.inf
        for r, c in board.available_moves():
            board.grid[r][c] = ai_sym
            board.check_winner()
            eval = minimax(board, depth + 1, alpha, beta, False, ai_sym, player_sym)
            board.grid[r][c] = None
            board.winner = None
            board.win_line = None
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = math.inf
        for r, c in board.available_moves():
            board.grid[r][c] = player_sym
            board.check_winner()
            eval = minimax(board, depth + 1, alpha, beta, True, ai_sym, player_sym)
            board.grid[r][c] = None
            board.winner = None
            board.win_line = None
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha: break
        return min_eval

def get_ai_move(board, difficulty, ai_sym, player_sym):
    moves = board.available_moves()
    if not moves: return None
    
    if difficulty == "Легко":
        return random.choice(moves)
    elif difficulty == "Средне":
        if random.random() < 0.6: # 60% шанс на умный ход
            return random.choice(moves)
    
    # Сложно (Минимакс)
    best_score = -math.inf
    best_move = moves[0]
    for r, c in moves:
        board.grid[r][c] = ai_sym
        board.check_winner()
        score = minimax(board, 0, -math.inf, math.inf, False, ai_sym, player_sym)
        board.grid[r][c] = None
        board.winner = None
        board.win_line = None
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return best_move

# --- Главный класс игры ---
class Game:
    def __init__(self):
        self.state = "MENU"  # MENU, SETTINGS, PLAYING, PAUSED, GAME_OVER
        self.board = Board()
        
        # Настройки
        self.difficulty = "Сложно"
        self.player_symbol = 'X'
        self.sound_enabled = True
        
        # Игровой процесс
        self.current_turn = 'X'
        self.game_over = False
        self.hover_cell = None
        
        # Анимации и ИИ
        self.ai_thinking = False
        self.ai_timer = 0
        self.ai_think_delay = 0.8 # 0.8 секунды на подумать
        
        self.piece_anims = {} # (r, c) -> progress (0.0 to 1.0)
        
        self.reset()

    def reset(self):
        self.board.reset()
        self.game_over = False
        self.piece_anims.clear()
        self.ai_thinking = False
        self.ai_timer = 0
        
        # Если игрок выбрал 'O', то ИИ ('X') ходит первым
        self.current_turn = 'X' 
        if self.player_symbol == 'O':
            self.start_ai_turn()

    def get_ai_symbol(self):
        return 'O' if self.player_symbol == 'X' else 'X'

    def start_ai_turn(self):
        if not self.game_over:
            self.ai_thinking = True
            self.ai_timer = 0

    def execute_move(self, r, c, symbol):
        if self.board.make_move(r, c, symbol):
            self.piece_anims[(r, c)] = 0.0 # Запуск анимации
            if self.sound_enabled and snd_click: snd_click.play()
            
            if self.board.winner:
                self.game_over = True
                if self.sound_enabled:
                    if self.board.winner == self.player_symbol: snd_win.play()
                    elif self.board.winner == self.get_ai_symbol(): snd_lose.play()
                    else: snd_draw.play()
            else:
                self.current_turn = self.get_ai_symbol() if symbol == self.player_symbol else self.player_symbol
                if self.current_turn == self.get_ai_symbol():
                    self.start_ai_turn()

    def update(self, dt):
        # Обновление анимаций
        for k in list(self.piece_anims.keys()):
            self.piece_anims[k] += dt * 4.0 # Скорость анимации
            if self.piece_anims[k] > 1.0:
                self.piece_anims[k] = 1.0
                
        # Логика ИИ
        if self.state == "PLAYING" and self.ai_thinking and not self.game_over:
            self.ai_timer += dt
            if self.ai_timer >= self.ai_think_delay:
                move = get_ai_move(self.board, self.difficulty, self.get_ai_symbol(), self.player_symbol)
                if move:
                    self.execute_move(move[0], move[1], self.get_ai_symbol())
                self.ai_thinking = False

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        if self.state == "MENU":
            self.draw_menu(surface)
        elif self.state == "SETTINGS":
            self.draw_settings(surface)
        elif self.state in ("PLAYING", "PAUSED", "GAME_OVER"):
            self.draw_game(surface)

    def draw_menu(self, surface):
        title = font_title.render("NEON TIC-TAC-TOE", True, PLAYER_COLOR)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        mx, my = pygame.mouse.get_pos()
        
        # Кнопка Старт
        btn_start = pygame.Rect(WIDTH//2 - 150, 250, 300, 60)
        color = BUTTON_HOVER if btn_start.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_start, border_radius=15)
        surface.blit(font_main.render("СТАРТ ИГРЫ", True, TEXT_COLOR), (btn_start.centerx - 70, btn_start.centery - 15))

        # Кнопка Настройки
        btn_settings = pygame.Rect(WIDTH//2 - 150, 340, 300, 60)
        color = BUTTON_HOVER if btn_settings.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_settings, border_radius=15)
        surface.blit(font_main.render("НАСТРОЙКИ", True, TEXT_COLOR), (btn_settings.centerx - 70, btn_settings.centery - 15))

        # Кнопка Выход
        btn_exit = pygame.Rect(WIDTH//2 - 150, 430, 300, 60)
        color = BUTTON_HOVER if btn_exit.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_exit, border_radius=15)
        surface.blit(font_main.render("ВЫХОД", True, TEXT_COLOR), (btn_exit.centerx - 35, btn_exit.centery - 15))

    def draw_settings(self, surface):
        title = font_title.render("НАСТРОЙКИ", True, PLAYER_COLOR)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        mx, my = pygame.mouse.get_pos()
        
        # Сложность
        btn_diff = pygame.Rect(WIDTH//2 - 200, 220, 400, 50)
        color = BUTTON_HOVER if btn_diff.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_diff, border_radius=10)
        surface.blit(font_main.render(f"Сложность: {self.difficulty}", True, TEXT_COLOR), (btn_diff.centerx - 130, btn_diff.centery - 12))

        # Фигурка
        btn_sym = pygame.Rect(WIDTH//2 - 200, 290, 400, 50)
        color = BUTTON_HOVER if btn_sym.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_sym, border_radius=10)
        surface.blit(font_main.render(f"Играть за: {self.player_symbol}", True, TEXT_COLOR), (btn_sym.centerx - 90, btn_sym.centery - 12))

        # Звук
        btn_snd = pygame.Rect(WIDTH//2 - 200, 360, 400, 50)
        color = BUTTON_HOVER if btn_snd.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_snd, border_radius=10)
        snd_text = "Звук: ВКЛ" if self.sound_enabled else "Звук: ВЫКЛ"
        surface.blit(font_main.render(snd_text, True, TEXT_COLOR), (btn_snd.centerx - 70, btn_snd.centery - 12))

        # Назад
        btn_back = pygame.Rect(WIDTH//2 - 150, 500, 300, 50)
        color = BUTTON_HOVER if btn_back.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_back, border_radius=10)
        surface.blit(font_main.render("НАЗАД", True, TEXT_COLOR), (btn_back.centerx - 40, btn_back.centery - 12))

    def draw_game(self, surface):
        # Заголовок
        title = font_title.render("NEON TIC-TAC-TOE", True, PLAYER_COLOR)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 30))

        # Подсказка о том, чей ход
        if not self.game_over:
            turn_text = "ТВОЙ ХОД" if self.current_turn == self.player_symbol else "ИИ ДУМАЕТ..."
            color = PLAYER_COLOR if self.current_turn == self.player_symbol else THINKING_COLOR
            # Мигание для ИИ
            if self.current_turn == self.get_ai_symbol() and self.ai_thinking and int(pygame.time.get_ticks() / 300) % 2 == 0:
                color = (100, 100, 100) # Тускнеет
            surface.blit(font_small.render(turn_text, True, color), (WIDTH//2 - 60, 110))

        # Сетка
        for i in range(1, GRID_SIZE):
            pygame.draw.line(surface, GRID_COLOR, (GRID_OFFSET_X + i*CELL_SIZE, GRID_OFFSET_Y), (GRID_OFFSET_X + i*CELL_SIZE, GRID_OFFSET_Y + GRID_SIZE*CELL_SIZE), 3)
            pygame.draw.line(surface, GRID_COLOR, (GRID_OFFSET_X, GRID_OFFSET_Y + i*CELL_SIZE), (GRID_OFFSET_X + GRID_SIZE*CELL_SIZE, GRID_OFFSET_Y + i*CELL_SIZE), 3)

        # Наведение
        if self.hover_cell and not self.game_over and self.current_turn == self.player_symbol and not self.ai_thinking:
            hr, hc = self.hover_cell
            if self.board.grid[hr][hc] is None:
                pygame.draw.rect(surface, (30, 35, 50), (GRID_OFFSET_X + hc*CELL_SIZE, GRID_OFFSET_Y + hr*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # Фигуры с анимацией
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.board.grid[r][c]:
                    anim_progress = self.piece_anims.get((r, c), 1.0) # Если нет анимации, рисуем сразу
                    center = (GRID_OFFSET_X + c*CELL_SIZE + CELL_SIZE//2, GRID_OFFSET_Y + r*CELL_SIZE + CELL_SIZE//2)
                    color = PLAYER_COLOR if self.board.grid[r][c] == self.player_symbol else AI_COLOR
                    
                    if self.board.grid[r][c] == 'X':
                        offset = 30 * anim_progress
                        pygame.draw.line(surface, color, (center[0]-offset, center[1]-offset), (center[0]+offset, center[1]+offset), int(8 * anim_progress))
                        pygame.draw.line(surface, color, (center[0]+offset, center[1]-offset), (center[0]-offset, center[1]+offset), int(8 * anim_progress))
                    else:
                        radius = int(40 * anim_progress)
                        if radius > 2:
                            pygame.draw.circle(surface, color, center, radius, int(8 * anim_progress))

        # Линия победы
        if self.board.win_line:
            start = (GRID_OFFSET_X + self.board.win_line[0][1]*CELL_SIZE + CELL_SIZE//2, GRID_OFFSET_Y + self.board.win_line[0][0]*CELL_SIZE + CELL_SIZE//2)
            end = (GRID_OFFSET_X + self.board.win_line[2][1]*CELL_SIZE + CELL_SIZE//2, GRID_OFFSET_Y + self.board.win_line[2][0]*CELL_SIZE + CELL_SIZE//2)
            pygame.draw.line(surface, WIN_LINE_COLOR, start, end, 8)

        # Статус игры
        if self.game_over:
            if self.board.winner == "Draw": msg = "НИЧЬЯ!"
            elif self.board.winner == self.player_symbol: msg = "ТЫ ПОБЕДИЛ!"
            else: msg = "ПОБЕДИЛ ИИ!"
            status = font_main.render(msg, True, WIN_LINE_COLOR)
            surface.blit(status, (WIDTH//2 - status.get_width()//2, 630))
            
            # Кнопка Заново
            btn_rect = pygame.Rect(WIDTH//2 - 100, 680, 200, 50)
            pygame.draw.rect(surface, BUTTON_COLOR, btn_rect, border_radius=10)
            btn_text = font_main.render("ЗАНОВО", True, TEXT_COLOR)
            surface.blit(btn_text, (btn_rect.centerx - btn_text.get_width()//2, btn_rect.centery - btn_text.get_height()//2))
            
        # Кнопка В МЕНЮ (всегда)
        btn_menu = pygame.Rect(WIDTH//2 - 100, 740, 200, 40)
        mx, my = pygame.mouse.get_pos()
        color = BUTTON_HOVER if btn_menu.collidepoint(mx, my) else BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_menu, border_radius=8)
        menu_text = font_small.render("В МЕНЮ", True, TEXT_COLOR)
        surface.blit(menu_text, (btn_menu.centerx - menu_text.get_width()//2, btn_menu.centery - menu_text.get_height()//2))

        # Пауза
        if self.state == "PAUSED":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            surface.blit(overlay, (0, 0))
            pause_text = font_title.render("ПАУЗА", True, WIN_LINE_COLOR)
            surface.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 50))
            cont_text = font_small.render("ESC - Продолжить", True, TEXT_COLOR)
            surface.blit(cont_text, (WIDTH//2 - cont_text.get_width()//2, HEIGHT//2 + 20))

# --- Главный цикл ---
def main():
    game = Game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if game.state == "PLAYING":
                    game.state = "PAUSED"
                elif game.state == "PAUSED":
                    game.state = "PLAYING"
                elif game.state in ("SETTINGS", "GAME_OVER"):
                    game.state = "MENU"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # === МЕНЮ ===
                if game.state == "MENU":
                    if pygame.Rect(WIDTH//2 - 150, 250, 300, 60).collidepoint(event.pos):
                        game.reset()
                        game.state = "PLAYING"
                    elif pygame.Rect(WIDTH//2 - 150, 340, 300, 60).collidepoint(event.pos):
                        game.state = "SETTINGS"
                    elif pygame.Rect(WIDTH//2 - 150, 430, 300, 60).collidepoint(event.pos):
                        running = False
                        
                # === НАСТРОЙКИ ===
                elif game.state == "SETTINGS":
                    if pygame.Rect(WIDTH//2 - 200, 220, 400, 50).collidepoint(event.pos):
                        diffs = ["Легко", "Средне", "Сложно"]
                        game.difficulty = diffs[(diffs.index(game.difficulty) + 1) % 3]
                    elif pygame.Rect(WIDTH//2 - 200, 290, 400, 50).collidepoint(event.pos):
                        game.player_symbol = 'O' if game.player_symbol == 'X' else 'X'
                    elif pygame.Rect(WIDTH//2 - 200, 360, 400, 50).collidepoint(event.pos):
                        game.sound_enabled = not game.sound_enabled
                    elif pygame.Rect(WIDTH//2 - 150, 500, 300, 50).collidepoint(event.pos):
                        game.state = "MENU"

                # === ИГРА ===
                elif game.state == "PLAYING":
                    # Кнопка в меню
                    if pygame.Rect(WIDTH//2 - 100, 740, 200, 40).collidepoint(event.pos):
                        game.state = "MENU"
                        
                    elif game.game_over:
                        if pygame.Rect(WIDTH//2 - 100, 680, 200, 50).collidepoint(event.pos):
                            game.reset()
                    else:
                        # Клик по клетке
                        if GRID_OFFSET_X <= mx < GRID_OFFSET_X + GRID_SIZE*CELL_SIZE and GRID_OFFSET_Y <= my < GRID_OFFSET_Y + GRID_SIZE*CELL_SIZE:
                            if game.current_turn == game.player_symbol and not game.ai_thinking:
                                c = (mx - GRID_OFFSET_X) // CELL_SIZE
                                r = (my - GRID_OFFSET_Y) // CELL_SIZE
                                if game.board.grid[r][c] is None:
                                    game.execute_move(r, c, game.player_symbol)

            if event.type == pygame.MOUSEMOTION and game.state == "PLAYING" and not game.game_over:
                if GRID_OFFSET_X <= mx < GRID_OFFSET_X + GRID_SIZE*CELL_SIZE and GRID_OFFSET_Y <= my < GRID_OFFSET_Y + GRID_SIZE*CELL_SIZE:
                    game.hover_cell = ((my - GRID_OFFSET_Y) // CELL_SIZE, (mx - GRID_OFFSET_X) // CELL_SIZE)
                else:
                    game.hover_cell = None

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
