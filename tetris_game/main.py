import pygame
import random
import sys

# --- Настройки и константы ---
WIDTH, HEIGHT = 600, 750
GRID_WIDTH, GRID_HEIGHT = 10, 20
BLOCK_SIZE = 35
SIDEBAR_WIDTH = WIDTH - (GRID_WIDTH * BLOCK_SIZE)

# Цвета (Неоновая палитра)
BG_COLOR = (18, 18, 28)
GRID_COLOR = (40, 40, 55)
TEXT_COLOR = (220, 220, 255)

# Цвета фигур
COLORS = [
    (0, 240, 240),   # I - Cyan
    (240, 240, 0),   # O - Yellow
    (160, 32, 240),  # T - Purple
    (0, 240, 0),     # S - Green
    (240, 0, 0),     # Z - Red
    (0, 0, 240),     # J - Blue
    (240, 160, 0)    # L - Orange
]

# Формы фигур
SHAPES = [
    [[1, 5, 9, 13]],           # I
    [[4, 5, 8, 9]],            # O (в виде квадрата)
    [[1, 4, 5, 6]],            # T
    [[1, 2, 5, 6]],            # S
    [[1, 2, 4, 5]],            # Z
    [[0, 1, 5, 9]],            # J
    [[1, 5, 9, 8]]             # L
]

class Piece:
    def __init__(self, shape_idx):
        self.shape_idx = shape_idx
        self.color = COLORS[shape_idx]
        self.shape = SHAPES[shape_idx]
        self.x = GRID_WIDTH // 2 - 2
        self.y = 0

    def rotate(self, grid):
        # Вращение матрицы (по часовой стрелке)
        old_shape = self.shape
        if self.shape_idx == 1: # Квадрат не вращаем
            return
            
        new_shape = [[self.shape[len(self.shape) - 1 - j][i] for j in range(len(self.shape))] for i in range(len(self.shape[0]))]
        self.shape = new_shape
        
        # Если при вращении вылезли за границы, откатываем
        if not valid_space(self, grid):
            self.shape = old_shape

class Tetris:
    def __init__(self):
        self.grid = [[(0, 0, 0) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.fall_time = 0
        self.fall_speed = 0.5 # Секунд на клетку

    def new_piece(self):
        return Piece(random.randint(0, len(SHAPES) - 1))

    def check_lines(self):
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y][x] != (0, 0, 0) for x in range(GRID_WIDTH)):
                lines_to_clear.append(y)
                
        for y in lines_to_clear:
            del self.grid[y]
            self.grid.insert(0, [(0, 0, 0) for _ in range(GRID_WIDTH)])
            
        self.lines_cleared += len(lines_to_clear)
        self.score += [0, 100, 300, 500, 800][len(lines_to_clear)]
        
        # Повышение уровня каждые 10 линий
        self.level = self.lines_cleared // 10 + 1
        self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)

    def run(self, screen, font, small_font):
        screen.fill(BG_COLOR)
        
        # Отрисовка игрового поля
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(screen, GRID_COLOR, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)
                if self.grid[y][x] != (0, 0, 0):
                    pygame.draw.rect(screen, self.grid[y][x], (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1), border_radius=4)

        # Ghost Piece (Тень фигуры)
        if not self.game_over:
            ghost_y = self.current_piece.y
            ghost_piece = Piece(self.current_piece.shape_idx)
            ghost_piece.shape = self.current_piece.shape
            ghost_piece.x = self.current_piece.x
            
            while True:
                ghost_piece.y = ghost_y + 1
                if not valid_space(ghost_piece, self.grid):
                    break
                ghost_y += 1

            for y in range(len(self.current_piece.shape)):
                for x in range(len(self.current_piece.shape[y])):
                    if self.current_piece.shape[y][x] > 0:
                        pygame.draw.rect(screen, (60, 60, 80), 
                                         ((self.current_piece.x + x) * BLOCK_SIZE, (ghost_y + y) * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1), 2, border_radius=4)

            # Отрисовка текущей фигуры
            for y in range(len(self.current_piece.shape)):
                for x in range(len(self.current_piece.shape[y])):
                    if self.current_piece.shape[y][x] > 0:
                        pygame.draw.rect(screen, self.current_piece.color, 
                                         ((self.current_piece.x + x) * BLOCK_SIZE, (self.current_piece.y + y) * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1), border_radius=4)

        # --- Боковая панель (UI) ---
        sidebar_x = GRID_WIDTH * BLOCK_SIZE + 10
        
        # Счет
        score_text = font.render(f"СЧЕТ", True, (150, 150, 180))
        screen.blit(score_text, (sidebar_x, 30))
        score_val = font.render(f"{self.score}", True, TEXT_COLOR)
        screen.blit(score_val, (sidebar_x, 60))

        # Уровень
        level_text = small_font.render(f"Уровень: {self.level}", True, (150, 150, 180))
        screen.blit(level_text, (sidebar_x, 120))

        # Следующая фигура
        next_text = font.render("ДАЛЕЕ", True, (150, 150, 180))
        screen.blit(next_text, (sidebar_x, 200))
        
        # Отрисовка следующей фигуры (маленькая)
        next_shape = SHAPES[self.next_piece.shape_idx]
        next_color = COLORS[self.next_piece.shape_idx]
        for y in range(len(next_shape)):
            for x in range(len(next_shape[y])):
                if next_shape[y][x] > 0:
                    pygame.draw.rect(screen, next_color, 
                                     (sidebar_x + (x * 25) + 10, 250 + (y * 25), 24, 24), border_radius=3)

        # Управление
        controls = ["УПРАВЛЕНИЕ:", "← → : Движение", "↑ : Вращение", "↓ : Ускорить", "Пробел : Сброс"]
        for i, text in enumerate(controls):
            c_surf = small_font.render(text, True, (100, 100, 120))
            screen.blit(c_surf, (sidebar_x, 450 + i * 25))

        # Game Over
        if self.game_over:
            go_text = font.render("GAME OVER", True, (240, 0, 0))
            screen.blit(go_text, (sidebar_x, 650))
            restart_text = small_font.render("Нажми R для рестарта", True, TEXT_COLOR)
            screen.blit(restart_text, (sidebar_x, 690))

def valid_space(piece, grid):
    for y in range(len(piece.shape)):
        for x in range(len(piece.shape[y])):
            if piece.shape[y][x] > 0:
                grid_x = piece.x + x
                grid_y = piece.y + y
                # Проверка границ
                if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y >= GRID_HEIGHT:
                    return False
                # Проверка столкновения с другими фигурами
                if grid_y >= 0 and grid[grid_y][grid_x] != (0, 0, 0):
                    return False
    return True

def lock_piece(tetris):
    for y in range(len(tetris.current_piece.shape)):
        for x in range(len(tetris.current_piece.shape[y])):
            if tetris.current_piece.shape[y][x] > 0:
                grid_y = tetris.current_piece.y + y
                grid_x = tetris.current_piece.x + x
                if grid_y >= 0:
                    tetris.grid[grid_y][grid_x] = tetris.current_piece.color
                    
    tetris.check_lines()
    tetris.current_piece = tetris.next_piece
    tetris.next_piece = tetris.new_piece()
    
    if not valid_space(tetris.current_piece, tetris.grid):
        tetris.game_over = True

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Tetris")
    clock = pygame.time.Clock()
    
    # Шрифты (системные для надежности)
    font = pygame.font.SysFont("dejavusans", 30, bold=True)
    small_font = pygame.font.SysFont("dejavusans", 20)

    tetris = Tetris()
    running = True
    fall_time = 0

    while running:
        time_delta = clock.tick(60) / 1000.0
        fall_time += time_delta

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN and not tetris.game_over:
                # Движение влево
                if event.key == pygame.K_LEFT:
                    tetris.current_piece.x -= 1
                    if not valid_space(tetris.current_piece, tetris.grid):
                        tetris.current_piece.x += 1
                
                # Движение вправо
                if event.key == pygame.K_RIGHT:
                    tetris.current_piece.x += 1
                    if not valid_space(tetris.current_piece, tetris.grid):
                        tetris.current_piece.x -= 1
                
                # Ускорение вниз
                if event.key == pygame.K_DOWN:
                    tetris.current_piece.y += 1
                    if not valid_space(tetris.current_piece, tetris.grid):
                        tetris.current_piece.y -= 1
                        lock_piece(tetris)
                
                # Вращение
                if event.key == pygame.K_UP:
                    tetris.current_piece.rotate(tetris.grid)
                
                # Мгновенный сброс (Hard Drop)
                if event.key == pygame.K_SPACE:
                    while valid_space(tetris.current_piece, tetris.grid):
                        tetris.current_piece.y += 1
                    tetris.current_piece.y -= 1
                    lock_piece(tetris)

            # Рестарт
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and tetris.game_over:
                tetris = Tetris()

        # Гравитация
        if fall_time > tetris.fall_speed and not tetris.game_over:
            fall_time = 0
            tetris.current_piece.y += 1
            if not valid_space(tetris.current_piece, tetris.grid):
                tetris.current_piece.y -= 1
                lock_piece(tetris)

        tetris.run(screen, font, small_font)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
