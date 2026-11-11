import pygame
import random
import sys
import math
import array

# --- Настройки ---
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 5
MARGIN = 150
CELL_SIZE = (WIDTH - 2 * MARGIN) // GRID_SIZE

BG_COLOR = (30, 30, 40)
GRID_BG_COLOR = (40, 40, 55)
TEXT_COLOR = (255, 255, 255)

GEM_COLORS = [
    (255, 85, 85), (85, 170, 255), (85, 255, 85), 
    (255, 255, 85), (255, 85, 255), (255, 170, 85)
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

snd_swap = generate_sound(400, 0.1, 0.05, "sine")
snd_match = generate_sound(800, 0.15, 0.1, "sine")
snd_error = generate_sound(150, 0.2, 0.1, "square")
snd_fall = generate_sound(300, 0.05, 0.05, "square")

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-8, 8), random.uniform(-8, 8)
        self.color, self.life, self.size = color, random.randint(20, 40), random.randint(3, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            alpha = max(0, self.life / 40)
            c = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
            pygame.draw.circle(screen, c, (int(self.x), int(self.y)), self.size)

class Gem:
    def __init__(self, x, y, type_idx):
        self.x, self.y = x, y
        self.type = type_idx
        self.color = GEM_COLORS[type_idx]
        self.draw_x = x * CELL_SIZE + MARGIN
        self.draw_y = y * CELL_SIZE + MARGIN

    def draw(self, screen, selected=False):
        center = (int(self.draw_x + CELL_SIZE // 2), int(self.draw_y + CELL_SIZE // 2))
        radius = CELL_SIZE // 2 - 8
        
        pygame.draw.circle(screen, (10, 10, 15), (center[0] + 4, center[1] + 4), radius)
        pygame.draw.circle(screen, self.color, center, radius)
        
        highlight_color = (min(255, self.color[0] + 100), min(255, self.color[1] + 100), min(255, self.color[2] + 100))
        pygame.draw.circle(screen, highlight_color, (center[0] - radius // 3, center[1] - radius // 3), radius // 3)
        
        if selected:
            pygame.draw.circle(screen, (255, 255, 255), center, radius + 4, 4)

class Match3:
    def __init__(self):
        self.grid = []
        self.score = 0
        self.state = "IDLE"
        self.drag_start = None
        self.swap_pair = None
        self.anim_timer = 0
        self.particles = []
        self.generate_grid()

    def generate_grid(self):
        while True:
            self.grid = [[Gem(x, y, random.randint(0, 5)) for x in range(GRID_SIZE)] for y in range(GRID_SIZE)]
            if not self.find_matches():
                break

    def find_matches(self):
        matches = set()
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE - 2):
                if self.grid[y][x].type == self.grid[y][x+1].type == self.grid[y][x+2].type:
                    matches.update([(x, y), (x+1, y), (x+2, y)])
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 2):
                if self.grid[y][x].type == self.grid[y+1][x].type == self.grid[y+2][x].type:
                    matches.update([(x, y), (x, y+1), (x, y+2)])
        return matches

    def update(self):
        if self.state == "IDLE":
            pass
            
        elif self.state == "SWAPPING":
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                self.execute_swap()
                
        elif self.state == "SWAP_BACK":
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                self.execute_swap()
                snd_error.play()

        elif self.state == "REMOVING":
            self.anim_timer += 1
            if self.anim_timer >= 15:
                self.anim_timer = 0
                self.remove_matches()

        elif self.state == "FALLING":
            self.anim_timer += 1
            if self.anim_timer >= 5:
                self.anim_timer = 0
                
                moved = self.apply_gravity()
                
                if not moved:
                    # Проверяем, все ли камни долетели до своих мест
                    all_landed = True
                    for x in range(GRID_SIZE):
                        for y in range(GRID_SIZE):
                            gem = self.grid[y][x]
                            if gem:
                                target_x = x * CELL_SIZE + MARGIN
                                target_y = y * CELL_SIZE + MARGIN
                                if gem.draw_x < target_x: gem.draw_x = min(gem.draw_x + 30, target_x)
                                elif gem.draw_x > target_x: gem.draw_x = max(gem.draw_x - 30, target_x)
                                if gem.draw_y < target_y: gem.draw_y = min(gem.draw_y + 30, target_y)
                                elif gem.draw_y > target_y: gem.draw_y = max(gem.draw_y - 30, target_y)
                                
                                if gem.draw_x != target_x or gem.draw_y != target_y:
                                    all_landed = False
                    
                    if all_landed:
                        self.state = "IDLE"
                        if self.find_matches(): # ИСПРАВЛЕНО: убрано 'not'
                            self.state = "REMOVING"
                            self.anim_timer = 0
                            snd_match.play()
                            for x, y in self.find_matches():
                                for _ in range(5):
                                    self.particles.append(Particle(x * CELL_SIZE + MARGIN + CELL_SIZE//2, y * CELL_SIZE + MARGIN + CELL_SIZE//2, self.grid[y][x].color))

    def handle_mouse_down(self, pos):
        if self.state != "IDLE": return
        mx, my = pos
        gx, gy = (mx - MARGIN) // CELL_SIZE, (my - MARGIN) // CELL_SIZE
        
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            if self.grid[gy][gx]:
                self.drag_start = (gx, gy)

    def handle_mouse_motion(self, pos):
        if self.drag_start and self.state == "IDLE":
            mx, my = pos
            gx, gy = self.drag_start
            if self.grid[gy][gx]:
                # Камень следует за мышью
                self.grid[gy][gx].draw_x = mx - CELL_SIZE // 2
                self.grid[gy][gx].draw_y = my - CELL_SIZE // 2

    def handle_mouse_up(self, pos):
        if not self.drag_start: return
        sx, sy = self.drag_start
        self.drag_start = None # Сбрасываем перетаскивание
        
        # Возвращаем камень на сетку визуально
        if self.grid[sy][sx]:
            self.grid[sy][sx].draw_x = sx * CELL_SIZE + MARGIN
            self.grid[sy][sx].draw_y = sy * CELL_SIZE + MARGIN
            
        if self.state != "IDLE": return
        
        mx, my = pos
        gx, gy = (mx - MARGIN) // CELL_SIZE, (my - MARGIN) // CELL_SIZE
        
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            if abs(sx - gx) + abs(sy - gy) == 1:
                self.swap_pair = ((sx, sy), (gx, gy))
                self.state = "SWAPPING"
                self.anim_timer = 0
                snd_swap.play()

    def execute_swap(self):
        (x1, y1), (x2, y2) = self.swap_pair
        self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
        
        self.grid[y1][x1].x, self.grid[y1][x1].y = x1, y1
        self.grid[y2][x2].x, self.grid[y2][x2].y = x2, y2
        self.grid[y1][x1].draw_x = x1 * CELL_SIZE + MARGIN
        self.grid[y1][x1].draw_y = y1 * CELL_SIZE + MARGIN
        self.grid[y2][x2].draw_x = x2 * CELL_SIZE + MARGIN
        self.grid[y2][x2].draw_y = y2 * CELL_SIZE + MARGIN

        if self.state == "SWAPPING":
            matches = self.find_matches()
            if matches:
                self.state = "REMOVING"
                snd_match.play()
            else:
                self.state = "SWAP_BACK"
        else:
            self.state = "IDLE"

    def remove_matches(self):
        matches = self.find_matches()
        for x, y in matches:
            for _ in range(8):
                self.particles.append(Particle(x * CELL_SIZE + MARGIN + CELL_SIZE//2, y * CELL_SIZE + MARGIN + CELL_SIZE//2, self.grid[y][x].color))
            self.grid[y][x] = None
        self.score += len(matches) * 10
        self.state = "FALLING"

    def apply_gravity(self):
        moved = False
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 1, -1, -1):
                if self.grid[y][x] is None:
                    for ny in range(y - 1, -1, -1):
                        if self.grid[ny][x] is not None:
                            self.grid[y][x] = self.grid[ny][x]
                            self.grid[ny][x] = None
                            self.grid[y][x].y = y
                            moved = True
                            snd_fall.play()
                            break
        for x in range(GRID_SIZE):
            if self.grid[0][x] is None:
                new_gem = Gem(x, 0, random.randint(0, 5))
                new_gem.draw_y = -CELL_SIZE # Появляется сверху
                self.grid[0][x] = new_gem
                moved = True
        return moved

    def draw(self, screen, font):
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GRID_BG_COLOR, (MARGIN - 15, MARGIN - 15, GRID_SIZE * CELL_SIZE + 30, GRID_SIZE * CELL_SIZE + 30), border_radius=20)

        # Рисуем все камни, КРОМЕ перетаскиваемого
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x]:
                    if self.drag_start == (x, y):
                        continue
                    self.grid[y][x].draw(screen)

        # Рисуем перетаскиваемый камень поверх всех остальных
        if self.drag_start:
            dx, dy = self.drag_start
            if self.grid[dy][dx]:
                self.grid[dy][dx].draw(screen, selected=True)

        for p in self.particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                self.particles.remove(p)

        score_surf = font.render(f"СЧЕТ: {self.score}", True, TEXT_COLOR)
        screen.blit(score_surf, (MARGIN, 40))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Match-3: Candy Blast (Drag & Drop)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 40, bold=True)
    small_font = pygame.font.SysFont("dejavusans", 24)
    
    game = Match3()
    state = "MENU"
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if state == "MENU" and event.key == pygame.K_RETURN:
                    state = "PLAYING"
                    game = Match3()
                elif state == "PLAYING" and event.key == pygame.K_ESCAPE:
                    state = "MENU"

            if state == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    game.handle_mouse_down(pygame.mouse.get_pos())
                elif event.type == pygame.MOUSEMOTION:
                    game.handle_mouse_motion(pygame.mouse.get_pos())
                elif event.type == pygame.MOUSEBUTTONUP:
                    game.handle_mouse_up(pygame.mouse.get_pos())

        if state == "MENU":
            screen.fill(BG_COLOR)
            title = font.render("CANDY BLAST 5x5", True, (255, 100, 150))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
            
            play_txt = font.render("Нажми ENTER для игры", True, TEXT_COLOR)
            screen.blit(play_txt, (WIDTH//2 - play_txt.get_width()//2, HEIGHT//2))
            
            rules = ["Зажми камень мышкой и потяни", "на соседний камень, чтобы поменять", "Собирай 3 и более в ряд!"]
            for i, text in enumerate(rules):
                r_surf = small_font.render(text, True, (150, 150, 180))
                screen.blit(r_surf, (WIDTH//2 - r_surf.get_width()//2, HEIGHT//2 + 100 + i * 30))

        elif state == "PLAYING":
            game.update()
            game.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
