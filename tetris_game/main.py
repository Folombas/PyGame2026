import pygame
import random
import sys
import math
import array

# --- Настройки ---
WIDTH, HEIGHT = 600, 750
GRID_WIDTH, GRID_HEIGHT = 10, 20
BLOCK_SIZE = 35
SIDEBAR_WIDTH = WIDTH - (GRID_WIDTH * BLOCK_SIZE)

# Неоновая палитра
BG_COLOR = (18, 18, 28)
GRID_COLOR = (40, 40, 55)
TEXT_COLOR = (220, 220, 255)

COLORS = [
    (0, 240, 240),   # I
    (240, 240, 0),   # O
    (160, 32, 240),  # T
    (0, 240, 0),     # S
    (240, 0, 0),     # Z
    (0, 0, 240),     # J
    (240, 160, 0)    # L
]

SHAPES = [
    [[1, 5, 9, 13]], [[4, 5, 8, 9]], [[1, 4, 5, 6]],
    [[1, 2, 5, 6]], [[1, 2, 4, 5]], [[0, 1, 5, 9]], [[1, 5, 9, 8]]
]

# --- Синтез звука (без внешних файлов) ---
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

def generate_sound(freq, duration, volume=0.1, wave_type="sine"):
    sample_rate = 44100
    n_samples = int(round(sample_rate * duration))
    buf = array.array('h')
    for i in range(n_samples):
        env = min(1.0, i / 100.0, (n_samples - i) / 100.0) # Сглаживание
        t = float(i) / sample_rate
        if wave_type == "sine":
            val = math.sin(2.0 * math.pi * freq * t)
        elif wave_type == "square":
            val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
        buf.append(int(32767.0 * volume * env * val))
    return pygame.mixer.Sound(buffer=buf)

# Создаем звуки
snd_move = generate_sound(300, 0.05, 0.05, "square")
snd_rotate = generate_sound(500, 0.08, 0.05, "sine")
snd_drop = generate_sound(150, 0.15, 0.1, "square")
snd_clear = generate_sound(800, 0.2, 0.1, "sine")

# --- Классы визуальных эффектов ---
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-10, -2)
        self.color = color
        self.life = random.randint(20, 40)
        self.size = random.randint(2, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.5
        self.life -= 1

    def draw(self, screen, offset_x=0, offset_y=0):
        if self.life > 0:
            alpha = max(0, self.life / 40)
            color = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
            pygame.draw.circle(screen, color, (int(self.x + offset_x), int(self.y + offset_y)), self.size)

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = 60

    def update(self):
        self.y -= 2
        self.life -= 1

    def draw(self, screen, font, offset_x=0, offset_y=0):
        if self.life > 0:
            surf = font.render(self.text, True, self.color)
            screen.blit(surf, (self.x + offset_x, self.y + offset_y))

class Piece:
    def __init__(self, shape_idx):
        self.shape_idx = shape_idx
        self.color = COLORS[shape_idx]
        self.shape = SHAPES[shape_idx]
        self.x = GRID_WIDTH // 2 - 2
        self.y = 0

    def rotate(self, grid):
        if self.shape_idx == 1: return
        old_shape = self.shape
        self.shape = [[old_shape[len(old_shape) - 1 - j][i] for j in range(len(old_shape))] for i in range(len(old_shape[0]))]
        if not valid_space(self, grid): self.shape = old_shape

class Tetris:
    def __init__(self):
        self.grid = [[(0, 0, 0) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.fall_speed = 0.5
        self.shake_timer = 0
        self.particles = []
        self.floating_texts = []

    def new_piece(self):
        return Piece(random.randint(0, len(SHAPES) - 1))

    def check_lines(self):
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y][x] != (0, 0, 0) for x in range(GRID_WIDTH)):
                lines_to_clear.append(y)
                
        for y in lines_to_clear:
            # Взрыв частиц при сборе линии
            for x in range(GRID_WIDTH):
                color = self.grid[y][x]
                for _ in range(3): # 3 частицы на блок
                    self.particles.append(Particle(x * BLOCK_SIZE + BLOCK_SIZE//2, y * BLOCK_SIZE + BLOCK_SIZE//2, color))
            
            del self.grid[y]
            self.grid.insert(0, [(0, 0, 0) for _ in range(GRID_WIDTH)])
            
        if lines_to_clear:
            snd_clear.play()
            self.shake_timer = 10 # Тряска экрана
            points = [0, 100, 300, 500, 800][len(lines_to_clear)]
            self.score += points * self.level
            self.lines_cleared += len(lines_to_clear)
            
            # Всплывающий текст
            self.floating_texts.append(FloatingText(WIDTH//2, HEIGHT//2, f"+{points}", (255, 255, 100)))

        self.level = self.lines_cleared // 10 + 1
        self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)

    def run(self, screen, font, small_font):
        # Логика тряски экрана
        offset_x, offset_y = 0, 0
        if self.shake_timer > 0:
            offset_x = random.randint(-4, 4)
            offset_y = random.randint(-4, 4)
            self.shake_timer -= 1

        screen.fill(BG_COLOR)
        
        # Отрисовка поля со смещением (тряска)
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(screen, GRID_COLOR, (x * BLOCK_SIZE + offset_x, y * BLOCK_SIZE + offset_y, BLOCK_SIZE, BLOCK_SIZE), 1)
                if self.grid[y][x] != (0, 0, 0):
                    pygame.draw.rect(screen, self.grid[y][x], (x * BLOCK_SIZE + offset_x, y * BLOCK_SIZE + offset_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1), border_radius=4)

        # Ghost Piece
        if not self.game_over:
            ghost_y = self.current_piece.y
            ghost_piece = Piece(self.current_piece.shape_idx)
            ghost_piece.shape = self.current_piece.shape
            ghost_piece.x = self.current_piece.x
            while True:
                ghost_piece.y = ghost_y + 1
                if not valid_space(ghost_piece, self.grid): break
                ghost_y += 1
            for y in range(len(self.current_piece.shape)):
                for x in range(len(self.current_piece.shape[y])):
                    if self.current_piece.shape[y][x] > 0:
                        pygame.draw.rect(screen, (60, 60, 80), 
                                         ((self.current_piece.x + x) * BLOCK_SIZE + offset_x, (ghost_y + y) * BLOCK_SIZE + offset_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1), 2, border_radius=4)

            # Текущая фигура
            for y in range(len(self.current_piece.shape)):
                for x in range(len(self.current_piece.shape[y])):
                    if self.current_piece.shape[y][x] > 0:
                        pygame.draw.rect(screen, self.current_piece.color, 
                                         ((self.current_piece.x + x) * BLOCK_SIZE + offset_x, (self.current_piece.y + y) * BLOCK_SIZE + offset_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1), border_radius=4)

        # Частицы и текст
        for p in self.particles[:]:
            p.update()
            p.draw(screen, offset_x, offset_y)
            if p.life <= 0: self.particles.remove(p)
        for t in self.floating_texts[:]:
            t.update()
            t.draw(screen, font, offset_x, offset_y)
            if t.life <= 0: self.floating_texts.remove(t)

        # UI
        sidebar_x = GRID_WIDTH * BLOCK_SIZE + 10
        screen.blit(font.render(f"СЧЕТ", True, (150, 150, 180)), (sidebar_x, 30))
        screen.blit(font.render(f"{self.score}", True, TEXT_COLOR), (sidebar_x, 60))
        screen.blit(small_font.render(f"Уровень: {self.level}", True, (150, 150, 180)), (sidebar_x, 120))
        screen.blit(font.render("ДАЛЕЕ", True, (150, 150, 180)), (sidebar_x, 200))
        
        next_shape = SHAPES[self.next_piece.shape_idx]
        next_color = COLORS[self.next_piece.shape_idx]
        for y in range(len(next_shape)):
            for x in range(len(next_shape[y])):
                if next_shape[y][x] > 0:
                    pygame.draw.rect(screen, next_color, (sidebar_x + (x * 25) + 10, 250 + (y * 25), 24, 24), border_radius=3)

        if self.game_over:
            screen.blit(font.render("GAME OVER", True, (240, 0, 0)), (sidebar_x, 650))
            screen.blit(small_font.render("Нажми R", True, TEXT_COLOR), (sidebar_x, 690))

def valid_space(piece, grid):
    for y in range(len(piece.shape)):
        for x in range(len(piece.shape[y])):
            if piece.shape[y][x] > 0:
                grid_x, grid_y = piece.x + x, piece.y + y
                if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y >= GRID_HEIGHT: return False
                if grid_y >= 0 and grid[grid_y][grid_x] != (0, 0, 0): return False
    return True

def lock_piece(tetris):
    for y in range(len(tetris.current_piece.shape)):
        for x in range(len(tetris.current_piece.shape[y])):
            if tetris.current_piece.shape[y][x] > 0:
                grid_y, grid_x = tetris.current_piece.y + y, tetris.current_piece.x + x
                if grid_y >= 0: tetris.grid[grid_y][grid_x] = tetris.current_piece.color
                    
    tetris.check_lines()
    tetris.current_piece = tetris.next_piece
    tetris.next_piece = tetris.new_piece()
    if not valid_space(tetris.current_piece, tetris.grid): tetris.game_over = True

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Tetris (Juiced Edition)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 30, bold=True)
    small_font = pygame.font.SysFont("dejavusans", 20)

    tetris = Tetris()
    running = True
    fall_time = 0

    while running:
        time_delta = clock.tick(60) / 1000.0
        fall_time += time_delta

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
                
            if event.type == pygame.KEYDOWN and not tetris.game_over:
                if event.key == pygame.K_LEFT:
                    tetris.current_piece.x -= 1
                    if not valid_space(tetris.current_piece, tetris.grid): tetris.current_piece.x += 1
                    else: snd_move.play()
                if event.key == pygame.K_RIGHT:
                    tetris.current_piece.x += 1
                    if not valid_space(tetris.current_piece, tetris.grid): tetris.current_piece.x -= 1
                    else: snd_move.play()
                if event.key == pygame.K_DOWN:
                    tetris.current_piece.y += 1
                    if not valid_space(tetris.current_piece, tetris.grid):
                        tetris.current_piece.y -= 1
                        lock_piece(tetris)
                if event.key == pygame.K_UP:
                    tetris.current_piece.rotate(tetris.grid)
                    snd_rotate.play()
                if event.key == pygame.K_SPACE:
                    while valid_space(tetris.current_piece, tetris.grid): tetris.current_piece.y += 1
                    tetris.current_piece.y -= 1
                    tetris.shake_timer = 5 # Легкая тряска при жестком сбросе
                    snd_drop.play()
                    lock_piece(tetris)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and tetris.game_over:
                tetris = Tetris()

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
