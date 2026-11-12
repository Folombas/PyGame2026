import pygame
import sys
import math
import random

# --- Настройки ---
WIDTH, HEIGHT = 1000, 600
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 6

BG_COLOR = (20, 24, 35)
PLATFORM_COLOR = (45, 52, 71)
TEXT_COLOR = (255, 255, 255)

# --- Инициализация и загрузка ассетов ---
pygame.init()
pygame.mixer.init()

# Звуки
try:
    snd_jump = pygame.mixer.Sound("assets/sounds/jump.wav")
    snd_coin = pygame.mixer.Sound("assets/sounds/coin.wav")
    snd_hit = pygame.mixer.Sound("assets/sounds/hit.wav")
    snd_win = pygame.mixer.Sound("assets/sounds/win.wav")
except Exception as e:
    print(f"Ошибка загрузки звуков: {e}")
    # Заглушки, если звуки не скачались
    snd_jump = snd_coin = snd_hit = snd_win = None

class SpriteSheet:
    def __init__(self, filename, frame_w, frame_h):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except Exception as e:
            print(f"Ошибка загрузки спрайта {filename}: {e}")
            self.sheet = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            pygame.draw.rect(self.sheet, (255, 0, 255), (0, 0, frame_w, frame_h)) # Розовый квадрат при ошибке
        
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.cols = self.sheet.get_width() // frame_w
        self.rows = self.sheet.get_height() // frame_h
        self.frames = []
        self.load_frames()

    def load_frames(self):
        for y in range(self.rows):
            for x in range(self.cols):
                rect = pygame.Rect(x * self.frame_w, y * self.frame_h, self.frame_w, self.frame_h)
                image = self.sheet.subsurface(rect)
                self.frames.append(image)

    def get_frame(self, index):
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return self.frames[0]

# Загружаем спрайты (пути могут отличаться в зависимости от версии Kenney pack)
# Ищем файлы в папке assets/sprites/kenney
import os
sprite_path = "assets/sprites/kenney/PNG/Players/playerGreen_stand.png"
if not os.path.exists(sprite_path):
    # Пробуем другие возможные пути
    for root, dirs, files in os.walk("assets/sprites/kenney"):
        for file in files:
            if "player" in file.lower() and file.endswith(".png") and "stand" in file.lower():
                sprite_path = os.path.join(root, file)
                break

# Создаем спрайт-листы (упрощенно: один кадр для стояния, один для прыжка)
# В реальном проекте нужно нарезать анимацию бега
player_stand = SpriteSheet(sprite_path, 64, 64).get_frame(0) if os.path.exists(sprite_path) else None
player_jump = player_stand # Заглушка

# Для врага ищем спрайт
enemy_path = None
for root, dirs, files in os.walk("assets/sprites/kenney"):
    for file in files:
        if "slime" in file.lower() and file.endswith(".png"):
            enemy_path = os.path.join(root, file)
            break
enemy_sprite = SpriteSheet(enemy_path, 64, 64).get_frame(0) if enemy_path else None

# --- Классы ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 60)
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.alive = True
        self.facing_right = True
        self.anim_timer = 0

    def update(self, keys, platforms):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
            self.facing_right = True

        self.vy += GRAVITY

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = JUMP_STRENGTH
            self.on_ground = False
            if snd_jump: snd_jump.play()

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

        if self.rect.top > HEIGHT + 200:
            self.alive = False

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        
        # Выбираем спрайт
        if not self.on_ground and player_jump:
            img = player_jump
        elif player_stand:
            img = player_stand
        else:
            # Заглушка, если спрайтов нет
            pygame.draw.rect(screen, (255, 85, 85), draw_rect, border_radius=5)
            return

        # Масштабируем и отражаем при необходимости
        scaled_img = pygame.transform.scale(img, (self.rect.width, self.rect.height))
        if not self.facing_right:
            scaled_img = pygame.transform.flip(scaled_img, True, False)
            
        screen.blit(scaled_img, (draw_rect.x, draw_rect.y))

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        pygame.draw.rect(screen, PLATFORM_COLOR, draw_rect, border_radius=3)
        pygame.draw.rect(screen, (60, 70, 90), (draw_rect.x, draw_rect.y, draw_rect.width, 5), border_radius=3)

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
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
        
        if enemy_sprite:
            scaled_img = pygame.transform.scale(enemy_sprite, (self.rect.width, self.rect.height))
            screen.blit(scaled_img, (draw_rect.x, draw_rect.y))
        else:
            pygame.draw.rect(screen, (170, 50, 200), draw_rect, border_radius=10)

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.collected = False

    def draw(self, screen, cam_x):
        if not self.collected:
            draw_rect = self.rect.copy()
            draw_rect.x -= cam_x
            pygame.draw.circle(screen, (255, 215, 0), draw_rect.center, 10)
            pygame.draw.circle(screen, (255, 255, 200), draw_rect.center, 5)

class Goal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 100)

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        pygame.draw.rect(screen, (50, 255, 150), draw_rect, border_radius=5)
        pygame.draw.polygon(screen, (255, 255, 255), [(draw_rect.centerx, draw_rect.y), (draw_rect.centerx + 30, draw_rect.y + 20), (draw_rect.centerx, draw_rect.y + 40)])

# --- Создание уровня ---
def create_level():
    platforms = []
    enemies = []
    coins = []
    
    platforms.append(Platform(0, HEIGHT - 50, WIDTH * 3, 50))
    platforms.append(Platform(300, 450, 150, 20))
    platforms.append(Platform(550, 350, 150, 20))
    platforms.append(Platform(800, 250, 150, 20))
    platforms.append(Platform(1100, 400, 200, 20))
    platforms.append(Platform(1400, 300, 150, 20))
    
    coins.append(Coin(350, 400))
    coins.append(Coin(400, 400))
    coins.append(Coin(600, 300))
    coins.append(Coin(650, 300))
    coins.append(Coin(850, 200))
    coins.append(Coin(1150, 350))
    
    enemies.append(Enemy(500, HEIGHT - 90))
    enemies.append(Enemy(900, HEIGHT - 90))
    enemies.append(Enemy(1300, HEIGHT - 90))
    
    goal = Goal(WIDTH * 2.5, HEIGHT - 150)
    
    return platforms, enemies, coins, goal

def draw_parallax_bg(screen, cam_x):
    for i in range(0, WIDTH * 3, 400):
        pygame.draw.circle(screen, (30, 35, 50), (i - cam_x * 0.2, 300), 150)
    for i in range(200, WIDTH * 3, 500):
        pygame.draw.circle(screen, (35, 40, 60), (i - cam_x * 0.5, 400), 100)

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Runner (Sprite Edition)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 40, bold=True)
    
    player = Player(100, HEIGHT - 150)
    platforms, enemies, coins, goal = create_level()
    cam_x = 0
    score = 0
    state = "PLAYING"

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and state != "PLAYING":
                    player = Player(100, HEIGHT - 150)
                    platforms, enemies, coins, goal = create_level()
                    cam_x = 0
                    score = 0
                    state = "PLAYING"

        if state == "PLAYING":
            keys = pygame.key.get_pressed()
            player.update(keys, platforms)
            
            target_cam_x = player.rect.centerx - WIDTH // 3
            cam_x += (target_cam_x - cam_x) * 0.1
            if cam_x < 0: cam_x = 0

            for enemy in enemies:
                if enemy.alive:
                    enemy.update(platforms)
                    if player.rect.colliderect(enemy.rect):
                        if player.vy > 0 and player.rect.bottom < enemy.rect.centery:
                            enemy.alive = False
                            player.vy = -10
                            score += 100
                            if snd_hit: snd_hit.play()
                        else:
                            state = "GAME_OVER"
                            if snd_hit: snd_hit.play()

            for coin in coins:
                if not coin.collected and player.rect.colliderect(coin.rect):
                    coin.collected = True
                    score += 50
                    if snd_coin: snd_coin.play()

            if player.rect.colliderect(goal.rect):
                state = "WIN"
                if snd_win: snd_win.play()

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
            win_text = font.render("ПОБЕДА!", True, (50, 255, 150))
            screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2 - 40))
            r_text = pygame.font.SysFont("dejavusans", 24).render("Нажми R чтобы играть снова", True, TEXT_COLOR)
            screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT//2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
