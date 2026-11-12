import pygame
import sys
import os
import math

# --- Настройки ---
WIDTH, HEIGHT = 1000, 600
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 6

BG_COLOR = (107, 140, 255)  # Классический голубой фон неба
PLATFORM_COLOR = (139, 69, 19) # Коричневый цвет земли

# --- Инициализация ---
pygame.init()
pygame.mixer.init()

# --- Загрузка звуков ---
try:
    snd_jump = pygame.mixer.Sound("assets/sounds/jump.wav")
    snd_coin = pygame.mixer.Sound("assets/sounds/coin.wav")
    snd_stomp = pygame.mixer.Sound("assets/sounds/stomp.wav")
    snd_gameover = pygame.mixer.Sound("assets/sounds/gameover.wav")
    snd_win = pygame.mixer.Sound("assets/sounds/stage_clear.wav")
except Exception as e:
    print(f"Ошибка загрузки звуков: {e}")
    snd_jump = snd_coin = snd_stomp = snd_gameover = snd_win = None

# --- Нарезка спрайтов ---
class SpriteSheet:
    def __init__(self, filename, frame_w, frame_h):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except Exception as e:
            print(f"Ошибка загрузки {filename}: {e}")
            self.sheet = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            pygame.draw.rect(self.sheet, (255, 0, 255), (0, 0, frame_w, frame_h))
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.frames = []
        self.load_frames()

    def load_frames(self):
        sheet_w, sheet_h = self.sheet.get_size()
        for y in range(0, sheet_h, self.frame_h):
            for x in range(0, sheet_w, self.frame_w):
                rect = pygame.Rect(x, y, self.frame_w, self.frame_h)
                image = self.sheet.subsurface(rect)
                self.frames.append(image)

    def get_frame(self, index):
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return self.frames[0]

# Загружаем Марио (в оригинале кадры 16x16, но в файле они могут быть крупнее)
mario_sheet = SpriteSheet("assets/sprites/smallmariosheet.png", 16, 16)
# Берем кадр для стояния (обычно первый) и прыжка
mario_stand = mario_sheet.get_frame(0) 
mario_jump = mario_sheet.get_frame(1) if len(mario_sheet.frames) > 1 else mario_stand

# Загружаем врага (Гумба)
enemy_sheet = SpriteSheet("assets/sprites/enemysheet.png", 16, 16)
enemy_sprite = enemy_sheet.get_frame(0)

# --- Классы ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30) # Хитбокс
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.alive = True
        self.facing_right = True

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
        
        img = mario_jump if not self.on_ground else mario_stand
        
        # Масштабируем спрайт (в оригинале 16x16, нам нужно 30x30)
        scaled_img = pygame.transform.scale(img, (30, 30))
        if not self.facing_right:
            scaled_img = pygame.transform.flip(scaled_img, True, False)
            
        screen.blit(scaled_img, (draw_rect.x, draw_rect.y))

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        # Рисуем землю (коричневый прямоугольник с травой сверху)
        pygame.draw.rect(screen, (139, 69, 19), draw_rect) # Земля
        pygame.draw.rect(screen, (34, 139, 34), (draw_rect.x, draw_rect.y, draw_rect.width, 10)) # Трава

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
        
        scaled_img = pygame.transform.scale(enemy_sprite, (30, 30))
        # Отражаем Гумбу в зависимости от направления
        if self.vx > 0:
            scaled_img = pygame.transform.flip(scaled_img, True, False)
            
        screen.blit(scaled_img, (draw_rect.x, draw_rect.y))

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.collected = False

    def draw(self, screen, cam_x):
        if not self.collected:
            draw_rect = self.rect.copy()
            draw_rect.x -= cam_x
            # Рисуем монетку (желтый кружок с бликом)
            pygame.draw.circle(screen, (255, 215, 0), draw_rect.center, 10)
            pygame.draw.circle(screen, (255, 255, 100), draw_rect.center, 5)

class Goal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 100)

    def draw(self, screen, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        # Рисуем флагшток
        pygame.draw.rect(screen, (200, 200, 200), (draw_rect.centerx, draw_rect.y, 5, draw_rect.height))
        # Рисуем флаг
        pygame.draw.polygon(screen, (50, 255, 50), [(draw_rect.centerx + 5, draw_rect.y + 10), (draw_rect.centerx + 40, draw_rect.y + 25), (draw_rect.centerx + 5, draw_rect.y + 40)])

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
    
    enemies.append(Enemy(500, HEIGHT - 80))
    enemies.append(Enemy(900, HEIGHT - 80))
    enemies.append(Enemy(1300, HEIGHT - 80))
    
    goal = Goal(WIDTH * 2.5, HEIGHT - 150)
    
    return platforms, enemies, coins, goal

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Super Mario Bros - PyGame Edition")
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
            
            # Плавная камера
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
                            if snd_stomp: snd_stomp.play()
                        else:
                            state = "GAME_OVER"
                            if snd_gameover: snd_gameover.play()

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
                if snd_gameover: snd_gameover.play()

        # --- Отрисовка ---
        screen.fill(BG_COLOR)

        # Рисуем облака (простой параллакс)
        for i in range(0, WIDTH * 3, 600):
            pygame.draw.ellipse(screen, (255, 255, 255), (i - cam_x * 0.3, 100, 100, 50))

        for p in platforms:
            p.draw(screen, cam_x)
            
        goal.draw(screen, cam_x)

        for coin in coins:
            coin.draw(screen, cam_x)

        for enemy in enemies:
            if enemy.alive:
                enemy.draw(screen, cam_x)

        player.draw(screen, cam_x)

        score_text = font.render(f"СЧЕТ: {score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 20))

        if state == "GAME_OVER":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            go_text = font.render("GAME OVER", True, (255, 50, 50))
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 40))
            r_text = pygame.font.SysFont("dejavusans", 24).render("Нажми R для рестарта", True, (255, 255, 255))
            screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT//2 + 20))

        elif state == "WIN":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            win_text = font.render("ПОБЕДА!", True, (50, 255, 50))
            screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2 - 40))
            r_text = pygame.font.SysFont("dejavusans", 24).render("Нажми R чтобы играть снова", True, (255, 255, 255))
            screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT//2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
