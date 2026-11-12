import pygame
import sys
import math
import array
import random

# --- Настройки ---
WIDTH, HEIGHT = 1000, 600
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 6

# Цвета (Стильный минимализм / Неон)
BG_COLOR = (20, 24, 35)
PLATFORM_COLOR = (45, 52, 71)
PLAYER_COLOR = (255, 85, 85)
COIN_COLOR = (255, 215, 0)
ENEMY_COLOR = (170, 50, 200)
GOAL_COLOR = (50, 255, 150)
TEXT_COLOR = (255, 255, 255)

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

snd_jump = generate_sound(400, 0.1, 0.05, "square")
snd_coin = generate_sound(800, 0.1, 0.05, "sine")
snd_hit = generate_sound(150, 0.2, 0.1, "square")
snd_win = generate_sound(1000, 0.3, 0.1, "sine")

# --- Классы ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 40)
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.alive = True
        self.facing_right = True

    def update(self, keys, platforms):
        # Горизонтальное движение
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
            self.facing_right = True

        # Гравитация
        self.vy += GRAVITY

        # Прыжок
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = JUMP_STRENGTH
            self.on_ground = False
            snd_jump.play()

        # Коллизия по X
        self.rect.x += self.vx
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0: self.rect.right = p.rect.left
                if self.vx < 0: self.rect.left = p.rect.right

        # Коллизия по Y
        self.rect.y += self.vy
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy = 0

        # Смерть от падения
        if self.rect.top > HEIGHT + 200:
            self.alive = False

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        # Тело
        pygame.draw.rect(screen, PLAYER_COLOR, draw_rect, border_radius=5)
        # Глаз
        eye_x = draw_rect.right - 10 if self.facing_right else draw_rect.left + 5
        pygame.draw.circle(screen, (255, 255, 255), (eye_x, draw_rect.y + 10), 4)

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        pygame.draw.rect(screen, PLATFORM_COLOR, draw_rect, border_radius=3)
        # Блик для стиля
        pygame.draw.rect(screen, (60, 70, 90), (draw_rect.x, draw_rect.y, draw_rect.width, 5), border_radius=3)

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.vx = -2
        self.alive = True

    def update(self, platforms):
        self.rect.x += self.vx
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0: self.rect.right = p.rect.left
                if self.vx < 0: self.rect.left = p.rect.right
                self.vx *= -1

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        pygame.draw.rect(screen, ENEMY_COLOR, draw_rect, border_radius=10)
        pygame.draw.circle(screen, (255, 255, 255), (draw_rect.x + 8, draw_rect.y + 10), 3)
        pygame.draw.circle(screen, (255, 255, 255), (draw_rect.x + 22, draw_rect.y + 10), 3)

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.collected = False

    def draw(self, screen, cam_x):
        if not self.collected:
            draw_rect = self.rect.copy()
            draw_rect.x -= cam_x
            pygame.draw.circle(screen, COIN_COLOR, draw_rect.center, 10)
            pygame.draw.circle(screen, (255, 255, 200), draw_rect.center, 5)

class Goal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 100)

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        pygame.draw.rect(screen, GOAL_COLOR, draw_rect, border_radius=5)
        # Флаг
        pygame.draw.polygon(screen, (255, 255, 255), [(draw_rect.centerx, draw_rect.y), (draw_rect.centerx + 30, draw_rect.y + 20), (draw_rect.centerx, draw_rect.y + 40)])

# --- Создание уровня ---
def create_level():
    platforms = []
    enemies = []
    coins = []
    
    # Земля
    platforms.append(Platform(0, HEIGHT - 50, WIDTH * 3, 50))
    
    # Платформы
    platforms.append(Platform(300, 450, 150, 20))
    platforms.append(Platform(550, 350, 150, 20))
    platforms.append(Platform(800, 250, 150, 20))
    platforms.append(Platform(1100, 400, 200, 20))
    platforms.append(Platform(1400, 300, 150, 20))
    
    # Монетки
    coins.append(Coin(350, 400))
    coins.append(Coin(400, 400))
    coins.append(Coin(600, 300))
    coins.append(Coin(650, 300))
    coins.append(Coin(850, 200))
    coins.append(Coin(1150, 350))
    
    # Враги
    enemies.append(Enemy(500, HEIGHT - 80))
    enemies.append(Enemy(900, HEIGHT - 80))
    enemies.append(Enemy(1300, HEIGHT - 80))
    
    # Цель
    goal = Goal(WIDTH * 2.5, HEIGHT - 150)
    
    return platforms, enemies, coins, goal

def draw_parallax_bg(screen, cam_x):
    # Дальний план
    for i in range(0, WIDTH * 3, 400):
        pygame.draw.circle(screen, (30, 35, 50), (i - cam_x * 0.2, 300), 150)
    # Средний план
    for i in range(200, WIDTH * 3, 500):
        pygame.draw.circle(screen, (35, 40, 60), (i - cam_x * 0.5, 400), 100)

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Runner (Mario Inspired)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 40, bold=True)
    
    player = Player(100, HEIGHT - 150)
    platforms, enemies, coins, goal = create_level()
    cam_x = 0
    score = 0
    state = "PLAYING" # PLAYING, WIN, GAME_OVER

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and state != "PLAYING":
                    # Рестарт
                    player = Player(100, HEIGHT - 150)
                    platforms, enemies, coins, goal = create_level()
                    cam_x = 0
                    score = 0
                    state = "PLAYING"

        if state == "PLAYING":
            keys = pygame.key.get_pressed()
            player.update(keys, platforms)
            
            # Движение камеры (следим за игроком)
            target_cam_x = player.rect.centerx - WIDTH // 3
            cam_x += (target_cam_x - cam_x) * 0.1 # Плавный скроллинг
            
            # Ограничение камеры
            if cam_x < 0: cam_x = 0

            for enemy in enemies:
                if enemy.alive:
                    enemy.update(platforms)
                    # Столкновение с игроком
                    if player.rect.colliderect(enemy.rect):
                        if player.vy > 0 and player.rect.bottom < enemy.rect.centery:
                            # Прыгнули на врага
                            enemy.alive = False
                            player.vy = -10
                            score += 100
                            snd_hit.play()
                        else:
                            # Получили урон
                            state = "GAME_OVER"
                            snd_hit.play()

            for coin in coins:
                if not coin.collected and player.rect.colliderect(coin.rect):
                    coin.collected = True
                    score += 50
                    snd_coin.play()

            if player.rect.colliderect(goal.rect):
                state = "WIN"
                snd_win.play()

            if not player.alive:
                state = "GAME_OVER"

        # --- Отрисовка ---
        screen.fill(BG_COLOR)
        draw_parallax_bg(screen, cam_x)

        for p in platforms:
            p.draw(screen, cam_x)
            
        goal.draw(screen, cam_x)

        for coin in coins:
            coin.draw(screen, cam_x)

        for enemy in enemies:
            if enemy.alive:
                enemy.draw(screen, cam_x)

        player.draw(screen, cam_x)

        # UI
        score_text = font.render(f"СЧЕТ: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (20, 20))

        if state == "GAME_OVER":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            go_text = font.render("GAME OVER", True, (255, 50, 50))
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 40))
            r_text = pygame.font.SysFont("dejavusans", 24).render("Нажми R для рестарта", True, TEXT_COLOR)
            screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT//2 + 20))

        elif state == "WIN":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            win_text = font.render("ПОБЕДА!", True, GOAL_COLOR)
            screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2 - 40))
            r_text = pygame.font.SysFont("dejavusans", 24).render("Нажми R чтобы играть снова", True, TEXT_COLOR)
            screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT//2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
