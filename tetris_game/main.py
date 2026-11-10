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

BG_COLOR = (18, 18, 28)
GRID_COLOR = (40, 40, 55)
TEXT_COLOR = (220, 220, 255)
NEON_PINK = (255, 20, 147)

COLORS = [
    (0, 240, 240), (240, 240, 0), (160, 32, 240), 
    (0, 240, 0), (240, 0, 0), (0, 0, 240), (240, 160, 0)
]

SHAPES = [
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]], # I
    [[1, 1], [1, 1]], # O
    [[0, 1, 0], [1, 1, 1], [0, 0, 0]], # T
    [[0, 1, 1], [1, 1, 0], [0, 0, 0]], # S
    [[1, 1, 0], [0, 1, 1], [0, 0, 0]], # Z
    [[1, 0, 0], [1, 1, 1], [0, 0, 0]], # J
    [[0, 0, 1], [1, 1, 1], [0, 0, 0]]  # L
]

# --- Синтез звука ---
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

def generate_sound(freq, duration, volume=0.1, wave_type="sine"):
    sample_rate = 44100
    n_samples = int(round(sample_rate * duration))
    buf = array.array('h')
    for i in range(n_samples):
        env = min(1.0, i / 100.0, (n_samples - i) / 100.0)
        t = float(i) / sample_rate
        val = math.sin(2.0 * math.pi * freq * t) if wave_type == "sine" else (1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0)
        buf.append(int(32767.0 * volume * env * val))
    return pygame.mixer.Sound(buffer=buf)

snd_move = generate_sound(300, 0.05, 0.05, "square")
snd_rotate = generate_sound(500, 0.08, 0.05, "sine")
snd_drop = generate_sound(150, 0.15, 0.1, "square")
snd_clear = generate_sound(800, 0.2, 0.1, "sine")

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-5, 5), random.uniform(-10, -2)
        self.color, self.life, self.size = color, random.randint(20, 40), random.randint(2, 6)

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
        self.x, self.y, self.text, self.color, self.life = x, y, text, color, 60

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
        self.shape = [row[:] for row in SHAPES[shape_idx]]
        self.x = (GRID_WIDTH - len(self.shape[0])) // 2
        self.y = 0

    def rotate(self, grid):
        if self.shape_idx == 1: return
        old_shape = self.shape
        self.shape = [list(row) for row in zip(*self.shape[::-1])]
        if not valid_space(self, grid): self.shape = old_shape

class Tetris:
    def __init__(self):
        self.grid = [[(0, 0, 0) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece, self.next_piece = self.new_piece(), self.new_piece()
        self.score, self.level, self.lines_cleared = 0, 1, 0
        self.game_over, self.fall_speed = False, 0.5
        self.shake_timer = 0
        self.particles, self.floating_texts = [], []

    def new_piece(self):
        return Piece(random.randint(0, len(SHAPES) - 1))

    def check_lines(self):
        lines_to_clear = [y for y in range(GRID_HEIGHT) if all(self.grid[y][x] != (0, 0, 0) for x in range(GRID_WIDTH))]
        for y in lines_to_clear:
            for x in range(GRID_WIDTH):
                for _ in range(3): self.particles.append(Particle(x * BLOCK_SIZE + BLOCK_SIZE//2, y * BLOCK_SIZE + BLOCK_SIZE//2, self.grid[y][x]))
            del self.grid[y]
            self.grid.insert(0, [(0, 0, 0) for _ in range(GRID_WIDTH)])
            
        if lines_to_clear:
            snd_clear.play()
            self.shake_timer = 10
            points = [0, 100, 300, 500, 800][len(lines_to_clear)]
            self.score += points * self.level
            self.lines_cleared += len(lines_to_clear)
            self.floating_texts.append(FloatingText(WIDTH//2, HEIGHT//2, f"+{points}", (255, 255, 100)))

        self.level = self.lines_cleared // 10 + 1
        self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)

    def update(self, time_delta):
        if not self.game_over:
            self.fall_time = getattr(self, 'fall_time', 0) + time_delta
            if self.fall_time > self.fall_speed:
                self.fall_time = 0
                self.current_piece.y += 1
                if not valid_space(self.current_piece, self.grid):
                    self.current_piece.y -= 1
                    lock_piece(self)

    def draw(self, screen, font, small_font):
        offset_x, offset_y = (random.randint(-4, 4), random.randint(-4, 4)) if self.shake_timer > 0 else (0, 0)
        if self.shake_timer > 0: self.shake_timer -= 1

        screen.fill(BG_COLOR)
        
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(screen, GRID_COLOR, (x * BLOCK_SIZE + offset_x, y * BLOCK_SIZE + offset_y, BLOCK_SIZE, BLOCK_SIZE), 1)
                if self.grid[y][x] != (0, 0, 0):
                    pygame.draw.rect(screen, self.grid[y][x], (x * BLOCK_SIZE + offset_x, y * BLOCK_SIZE + offset_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1), border_radius=4)

        if not self.game_over:
            ghost_y = self.current_piece.y
            ghost = Piece(self.current_piece.shape_idx)
            ghost.shape, ghost.x = self.current_piece.shape, self.current_piece.x
            while True:
                ghost.y = ghost_y + 1
                if not valid_space(ghost, self.grid): break
                ghost_y += 1
                
            for y in range(len(self.current_piece.shape)):
                for x in range(len(self.current_piece.shape[y])):
                    if self.current_piece.shape[y][x] > 0:
                        pygame.draw.rect(screen, (60, 60, 80), ((self.current_piece.x + x) * BLOCK_SIZE + offset_x, (ghost_y + y) * BLOCK_SIZE + offset_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1), 2, border_radius=4)
                        pygame.draw.rect(screen, self.current_piece.color, ((self.current_piece.x + x) * BLOCK_SIZE + offset_x, (self.current_piece.y + y) * BLOCK_SIZE + offset_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1), border_radius=4)

        for p in self.particles[:]:
            p.update(); p.draw(screen, offset_x, offset_y)
            if p.life <= 0: self.particles.remove(p)
        for t in self.floating_texts[:]:
            t.update(); t.draw(screen, font, offset_x, offset_y)
            if t.life <= 0: self.floating_texts.remove(t)

        # UI Sidebar
        sx = GRID_WIDTH * BLOCK_SIZE + 10
        screen.blit(font.render(f"СЧЕТ", True, (150, 150, 180)), (sx, 30))
        screen.blit(font.render(f"{self.score}", True, TEXT_COLOR), (sx, 60))
        screen.blit(small_font.render(f"Уровень: {self.level}", True, (150, 150, 180)), (sx, 120))
        screen.blit(font.render("ДАЛЕЕ", True, (150, 150, 180)), (sx, 200))
        
        for y in range(len(SHAPES[self.next_piece.shape_idx])):
            for x in range(len(SHAPES[self.next_piece.shape_idx][y])):
                if SHAPES[self.next_piece.shape_idx][y][x] > 0:
                    pygame.draw.rect(screen, COLORS[self.next_piece.shape_idx], (sx + (x * 25) + 10, 250 + (y * 25), 24, 24), border_radius=3)

def valid_space(piece, grid):
    for y in range(len(piece.shape)):
        for x in range(len(piece.shape[y])):
            if piece.shape[y][x] > 0:
                gx, gy = piece.x + x, piece.y + y
                if gx < 0 or gx >= GRID_WIDTH or gy >= GRID_HEIGHT or (gy >= 0 and grid[gy][gx] != (0, 0, 0)): return False
    return True

def lock_piece(tetris):
    for y in range(len(tetris.current_piece.shape)):
        for x in range(len(tetris.current_piece.shape[y])):
            if tetris.current_piece.shape[y][x] > 0:
                if tetris.current_piece.y + y >= 0: tetris.grid[tetris.current_piece.y + y][tetris.current_piece.x + x] = tetris.current_piece.color
    tetris.check_lines()
    tetris.current_piece = tetris.next_piece
    tetris.next_piece = tetris.new_piece()
    if not valid_space(tetris.current_piece, tetris.grid): tetris.game_over = True

def draw_menu(screen, font, small_font):
    screen.fill(BG_COLOR)
    title = font.render("NEON TETRIS", True, NEON_PINK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
    
    start_txt = font.render("Нажми ENTER чтобы играть", True, TEXT_COLOR)
    screen.blit(start_txt, (WIDTH//2 - start_txt.get_width()//2, HEIGHT//2))
    
    controls = ["УПРАВЛЕНИЕ:", "← → : Движение", "↑ : Вращение", "↓ : Ускорить", "Пробел : Сброс", "P / ESC : Пауза"]
    for i, text in enumerate(controls):
        c_surf = small_font.render(text, True, (150, 150, 180))
        screen.blit(c_surf, (WIDTH//2 - c_surf.get_width()//2, HEIGHT//2 + 60 + i * 25))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Tetris")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 30, bold=True)
    small_font = pygame.font.SysFont("dejavusans", 20)

    tetris = Tetris()
    state = "MENU" # MENU, PLAYING, PAUSED, GAME_OVER
    running = True

    while running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
                
            if event.type == pygame.KEYDOWN:
                if state == "MENU":
                    if event.key == pygame.K_RETURN:
                        tetris = Tetris()
                        state = "PLAYING"
                
                elif state == "PLAYING":
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        state = "PAUSED"
                    elif not tetris.game_over:
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
                            tetris.shake_timer = 5
                            snd_drop.play()
                            lock_piece(tetris)
                            
                elif state == "PAUSED":
                    if event.key in (pygame.K_p, pygame.K_ESCAPE): state = "PLAYING"
                    elif event.key == pygame.K_m: state = "MENU"
                
                elif state == "GAME_OVER":
                    if event.key == pygame.K_r: 
                        tetris = Tetris()
                        state = "PLAYING"
                    elif event.key == pygame.K_m: state = "MENU"

        # Обновление и отрисовка
        if state == "MENU":
            draw_menu(screen, font, small_font)
            
        elif state == "PLAYING" or state == "PAUSED":
            if state == "PLAYING":
                tetris.update(time_delta)
                if tetris.game_over: state = "GAME_OVER"
            
            tetris.draw(screen, font, small_font)
            
            if state == "PAUSED":
                # Полупрозрачный оверлей
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                
                pause_txt = font.render("ПАУЗА", True, NEON_PINK)
                screen.blit(pause_txt, (WIDTH//2 - pause_txt.get_width()//2, HEIGHT//2 - 40))
                
                resume_txt = small_font.render("P/ESC - Продолжить", True, TEXT_COLOR)
                menu_txt = small_font.render("M - В главное меню", True, TEXT_COLOR)
                screen.blit(resume_txt, (WIDTH//2 - resume_txt.get_width()//2, HEIGHT//2 + 20))
                screen.blit(menu_txt, (WIDTH//2 - menu_txt.get_width()//2, HEIGHT//2 + 50))

        elif state == "GAME_OVER":
            tetris.draw(screen, font, small_font)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            go_txt = font.render("GAME OVER", True, (240, 0, 0))
            screen.blit(go_txt, (WIDTH//2 - go_txt.get_width()//2, HEIGHT//2 - 40))
            
            r_txt = small_font.render("R - Рестарт", True, TEXT_COLOR)
            m_txt = small_font.render("M - Главное меню", True, TEXT_COLOR)
            screen.blit(r_txt, (WIDTH//2 - r_txt.get_width()//2, HEIGHT//2 + 20))
            screen.blit(m_txt, (WIDTH//2 - m_txt.get_width()//2, HEIGHT//2 + 50))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
