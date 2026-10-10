"""Pong с ИИ — классика в стиле BunnyOS."""
import pygame
import random
import sys
import math


# === НАСТРОЙКИ ===
WIDTH, HEIGHT = 900, 600
FPS = 60

PADDLE_W, PADDLE_H = 14, 90
PADDLE_SPEED = 550
BALL_SIZE = 16
BALL_SPEED_INIT = 420
BALL_SPEED_MAX = 900
AI_SPEED = 380  # скорость ИИ-ракетки

# === ЦВЕТА ===
C_BG       = (18, 22, 32)
C_MIDLINE  = (40, 55, 80)
C_PLAYER   = (100, 200, 255)
C_AI       = (255, 130, 100)
C_BALL     = (240, 240, 220)
C_TEXT     = (220, 230, 245)
C_TEXT_DIM = (120, 140, 170)
C_SCORE    = (255, 240, 180)

VOLUME_MASTER = 0.25


class PongGame:
    def __init__(self, screen=None):
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Понг — BunnyOS")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(None, 96)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)

        # Звуки
        self.snd_hit = self._load("assets/games/sounds/tetris/blip_01.wav", 0.4)
        self.snd_wall = self._load("assets/games/sounds/tetris/blip_05.wav", 0.3)
        self.snd_score = self._load("assets/games/sounds/tetris/coin_01.wav", 0.6)
        self.snd_over = self._load("assets/games/sounds/tetris/jingle_04.wav", 0.5)

        # Спрайты
        self.spr_player = None
        self.spr_ai = None
        self.spr_ball = None
        self._load_sprites()

        self.reset()

    def _load_sprites(self):
        """Спрайты из паков не подходят по пропорциям — рисуем процедурно."""
        self.spr_player = None
        self.spr_ai = None
        self.spr_ball = None


    def _load(self, path, vol=0.5):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(vol * VOLUME_MASTER)
            return s
        except Exception:
            return None

    def reset(self):
        self.player_y = HEIGHT // 2 - PADDLE_H // 2
        self.ai_y = HEIGHT // 2 - PADDLE_H // 2
        self.ball_trail = []
        self.player_score = 0
        self.ai_score = 0
        self.game_over = False
        self.paused = False
        self.winner = None
        self._serve(random.choice([-1, 1]))

    def _serve(self, direction):
        self.ball_x = WIDTH // 2 - BALL_SIZE // 2
        self.ball_y = HEIGHT // 2 - BALL_SIZE // 2
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        speed = BALL_SPEED_INIT
        self.ball_vx = math.cos(angle) * speed * direction
        self.ball_vy = math.sin(angle) * speed
        self.ball_speed = speed
        self.ball_trail = []  # история для шлейфа

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key in (pygame.K_SPACE, pygame.K_p):
                    self.paused = not self.paused
                if self.game_over and e.key == pygame.K_RETURN:
                    self.reset()
        return True

    def _update(self, dt):
        if self.paused or self.game_over:
            return

        # Управление игрока — WASD и стрелки
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.player_y -= PADDLE_SPEED * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.player_y += PADDLE_SPEED * dt
        # Границы
        self.player_y = max(0, min(HEIGHT - PADDLE_H, self.player_y))

        # === ИИ — следует за мячом ===
        ball_center = self.ball_y + BALL_SIZE // 2
        ai_center = self.ai_y + PADDLE_H // 2
        # ИИ реагирует только если мяч летит в его сторону
        if self.ball_vx > 0:
            diff = ball_center - ai_center
            # Зона нечувствительности (не дёргается)
            if abs(diff) > 8:
                step = AI_SPEED * dt * (1 if diff > 0 else -1)
                self.ai_y += step
            # Границы
            self.ai_y = max(0, min(HEIGHT - PADDLE_H, self.ai_y))

        # === Движение мяча ===
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        # Шлейф — запоминаем последние позиции
        if not hasattr(self, "ball_trail"):
            self.ball_trail = []
        self.ball_trail.append((self.ball_x + BALL_SIZE // 2,
                                self.ball_y + BALL_SIZE // 2))
        if len(self.ball_trail) > 12:
            self.ball_trail.pop(0)

        # Отскок от верх/низ
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy = -self.ball_vy
            if self.snd_wall:
                self.snd_wall.play()
        elif self.ball_y + BALL_SIZE >= HEIGHT:
            self.ball_y = HEIGHT - BALL_SIZE
            self.ball_vy = -self.ball_vy
            if self.snd_wall:
                self.snd_wall.play()

        # Ракетка игрока (слева)
        if self.ball_vx < 0:
            player_rect = pygame.Rect(30, self.player_y, PADDLE_W, PADDLE_H)
            ball_rect = pygame.Rect(self.ball_x, self.ball_y, BALL_SIZE, BALL_SIZE)
            if player_rect.colliderect(ball_rect):
                self.ball_x = 30 + PADDLE_W
                # Угол зависит от позиции удара
                rel = (self.ball_y + BALL_SIZE / 2 - (self.player_y + PADDLE_H / 2)) / (PADDLE_H / 2)
                rel = max(-1, min(1, rel))
                angle = rel * (math.pi / 3)  # до 60°
                self.ball_speed = min(BALL_SPEED_MAX, self.ball_speed + 30)
                self.ball_vx = math.cos(angle) * self.ball_speed
                self.ball_vy = math.sin(angle) * self.ball_speed
                if self.snd_hit:
                    self.snd_hit.play()

        # Ракетка ИИ (справа)
        if self.ball_vx > 0:
            ai_rect = pygame.Rect(WIDTH - 30 - PADDLE_W, self.ai_y, PADDLE_W, PADDLE_H)
            ball_rect = pygame.Rect(self.ball_x, self.ball_y, BALL_SIZE, BALL_SIZE)
            if ai_rect.colliderect(ball_rect):
                self.ball_x = WIDTH - 30 - PADDLE_W - BALL_SIZE
                rel = (self.ball_y + BALL_SIZE / 2 - (self.ai_y + PADDLE_H / 2)) / (PADDLE_H / 2)
                rel = max(-1, min(1, rel))
                angle = rel * (math.pi / 3)
                self.ball_speed = min(BALL_SPEED_MAX, self.ball_speed + 30)
                self.ball_vx = -math.cos(angle) * self.ball_speed
                self.ball_vy = math.sin(angle) * self.ball_speed
                if self.snd_hit:
                    self.snd_hit.play()

        # Гол забит
        if self.ball_x + BALL_SIZE < 0:
            # Игрок пропустил — очко ИИ
            self.ai_score += 1
            if self.snd_score:
                self.snd_score.play()
            self._check_end()
            if not self.game_over:
                self._serve(1)
        elif self.ball_x > WIDTH:
            # ИИ пропустил — очко игроку
            self.player_score += 1
            if self.snd_score:
                self.snd_score.play()
            self._check_end()
            if not self.game_over:
                self._serve(-1)

    def _check_end(self):
        if self.player_score >= 7:
            self.game_over = True
            self.winner = "PLAYER"
            if self.snd_over:
                self.snd_over.play()
        elif self.ai_score >= 7:
            self.game_over = True
            self.winner = "AI"
            if self.snd_over:
                self.snd_over.play()

    def _draw(self):
        self.screen.fill(C_BG)

        # Центральная линия (пунктир)
        for y in range(0, HEIGHT, 30):
            pygame.draw.rect(self.screen, C_MIDLINE,
                             (WIDTH // 2 - 2, y + 5, 4, 18))

        # === Ракетки — процедурные, с градиентом и свечением ===
        self._draw_paddle(30, self.player_y, C_PLAYER)
        self._draw_paddle(WIDTH - 30 - PADDLE_W, self.ai_y, C_AI)

        # === Шлейф мяча ===
        if hasattr(self, "ball_trail"):
            for i, (tx, ty) in enumerate(self.ball_trail[:-1]):
                t = (i + 1) / len(self.ball_trail)
                size = max(2, int(BALL_SIZE * t * 0.9))
                alpha = int(180 * t)
                trail = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(trail, (*C_BALL, alpha),
                                   (size // 2, size // 2), size // 2)
                self.screen.blit(trail, (tx - size // 2, ty - size // 2))

        # === Мяч с ярким свечением ===
        ball_cx = int(self.ball_x + BALL_SIZE // 2)
        ball_cy = int(self.ball_y + BALL_SIZE // 2)
        # Свечение
        for r in range(BALL_SIZE, BALL_SIZE * 2, 4):
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            a = max(20, 80 - r * 3)
            pygame.draw.circle(glow, (*C_BALL, a), (r, r), r)
            self.screen.blit(glow, (ball_cx - r, ball_cy - r))
        # Ядро
        pygame.draw.circle(self.screen, C_BALL, (ball_cx, ball_cy), BALL_SIZE // 2)
        # Блик
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (ball_cx - 3, ball_cy - 3), 2)

    def _draw_paddle(self, x, y, color):
        """Ракетка с градиентом и свечением."""
        # Свечение (soft glow)
        glow = pygame.Surface((PADDLE_W + 20, PADDLE_H + 20), pygame.SRCALPHA)
        for r in range(8, 0, -2):
            a = 30 - r * 2
            if a <= 0:
                continue
            pygame.draw.rect(glow, (*color, a),
                             (10 - r, 10 - r, PADDLE_W + r * 2, PADDLE_H + r * 2),
                             border_radius=12)
        self.screen.blit(glow, (x - 10, y - 10))

        # Тело ракетки — вертикальный градиент
        for i in range(PADDLE_H):
            t = i / PADDLE_H
            # В центре — ярче
            bright = 1.0 - abs(t - 0.5) * 0.6
            r = min(255, int(color[0] * bright + 40))
            g = min(255, int(color[1] * bright + 40))
            b = min(255, int(color[2] * bright + 40))
            pygame.draw.line(self.screen, (r, g, b),
                             (x + 2, y + i), (x + PADDLE_W - 2, y + i))

        # Скруглённые верх и низ
        pygame.draw.rect(self.screen, color,
                         (x, y, PADDLE_W, PADDLE_H), border_radius=7)
        # Внутренняя полоса (эффект 3D)
        inner_color = tuple(min(255, c + 60) for c in color)
        pygame.draw.line(self.screen, inner_color,
                         (x + PADDLE_W // 2, y + 6),
                         (x + PADDLE_W // 2, y + PADDLE_H - 6), 2)

        # Счёт
        p = self.font_big.render(str(self.player_score), True, C_PLAYER)
        a = self.font_big.render(str(self.ai_score), True, C_AI)
        self.screen.blit(p, (WIDTH // 2 - 100 - p.get_width() // 2, 30))
        self.screen.blit(a, (WIDTH // 2 + 100 - a.get_width() // 2, 30))

        # Подписи
        pl = self.font_small.render("ВЫ", True, C_PLAYER)
        al = self.font_small.render("ИИ", True, C_AI)
        self.screen.blit(pl, (WIDTH // 2 - 100 - pl.get_width() // 2, 130))
        self.screen.blit(al, (WIDTH // 2 + 100 - al.get_width() // 2, 130))

        # До победы
        info = self.font_small.render("До 7 очков", True, C_TEXT_DIM)
        self.screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 170))

        # Управление внизу
        hint = self.font_small.render(
            "W/S или ^ v — движение   P — пауза   Esc — выход",
            True, C_TEXT_DIM
        )
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))

        # Пауза
        if self.paused:
            self._overlay("ПАУЗА", "P — продолжить")

        # Победа / поражение
        if self.game_over:
            if self.winner == "PLAYER":
                self._overlay("ПОБЕДА!", f"{self.player_score} : {self.ai_score}",
                              "Enter — заново, Esc — выход")
            else:
                self._overlay("ПОРАЖЕНИЕ", f"{self.player_score} : {self.ai_score}",
                              "Enter — заново, Esc — выход")

    def _overlay(self, title, *subs):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))
        tt = self.font_big.render(title, True, C_TEXT)
        self.screen.blit(tt, (WIDTH // 2 - tt.get_width() // 2, HEIGHT // 2 - 80))
        for i, s in enumerate(subs):
            st = self.font.render(s, True, C_TEXT_DIM)
            self.screen.blit(st, (WIDTH // 2 - st.get_width() // 2,
                                  HEIGHT // 2 + 10 + i * 34))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.033)  # ограничение на случай лагов
            if not self._handle_events():
                break
            self._update(dt)
            self._draw()
            pygame.display.flip()
        return True


if __name__ == "__main__":
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    game = PongGame()
    game.run()
    pygame.quit()
    sys.exit(0)
