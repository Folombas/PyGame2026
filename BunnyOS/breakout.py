"""Breakout — арканоид в стиле BunnyOS."""
import pygame
import random
import sys
import math
import records


# === НАСТРОЙКИ ===
WIDTH, HEIGHT = 800, 600
FPS = 60

PADDLE_W, PADDLE_H = 120, 16
PADDLE_Y = HEIGHT - 50
PADDLE_SPEED = 600

BALL_R = 9
BALL_SPEED = 400
BALL_SPEED_MAX = 900

BRICK_W, BRICK_H = 70, 22
BRICK_PAD = 6
BRICK_COLS = 10
BRICK_TOP = 70
BRICK_LEFT = (WIDTH - (BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD)) // 2

# Цвета рядов (сверху вниз)
ROW_COLORS = [
    (255, 80, 100),   # красный
    (255, 140, 60),   # оранжевый
    (255, 220, 80),   # жёлтый
    (100, 220, 120),  # зелёный
    (80, 180, 240),   # голубой
    (180, 120, 240),  # фиолетовый
]

C_BG       = (12, 16, 28)
C_BORDER   = (60, 80, 130)
C_PADDLE   = (100, 200, 255)
C_BALL     = (240, 240, 220)
C_TEXT     = (220, 230, 245)
C_TEXT_DIM = (120, 140, 170)
C_GOLD     = (255, 220, 100)

VOLUME_MASTER = 0.25


class BreakoutGame:
    def __init__(self, screen=None):
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        if screen is None:
            pygame.display.set_caption("Breakout — BunnyOS")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 18)

        # Звуки
        self.snd_hit = self._load("assets/games/sounds/tetris/blip_01.wav", 0.3)
        self.snd_brick = self._load("assets/games/sounds/tetris/blip_05.wav", 0.35)
        self.snd_powerup = self._load("assets/games/sounds/tetris/powerup_01.wav", 0.5)
        self.snd_life = self._load("assets/games/sounds/tetris/hurt_01.wav", 0.5)
        self.snd_over = self._load("assets/games/sounds/tetris/gameover.wav", 0.6)
        self.snd_levelup = self._load("assets/games/sounds/tetris/jingle_01.wav", 0.5)

        self.high_score = records.get("breakout")
        self.reset()

    def _load(self, path, vol=0.5):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(vol * VOLUME_MASTER)
            return s
        except Exception:
            return None

    def reset(self):
        self.paddle_x = (WIDTH - PADDLE_W) // 2
        self.ball_x = WIDTH // 2
        self.ball_y = HEIGHT // 2
        self.ball_dx = 0
        self.ball_dy = 0
        self.ball_stuck = True  # приклеен к платформе до запуска
        self.lives = 3
        self.score = 0
        self.level = 1
        self.game_over = False
        self.won = False
        self.paused = False
        self.combo_timer = 0
        self.combo_count = 0
        self.particles = []
        self.powerups = []  # {x, y, kind}
        self._build_bricks()
        self._reset_ball()

    def _build_bricks(self):
        rows = min(5 + self.level - 1, 6)
        self.bricks = []
        for r in range(rows):
            for c in range(BRICK_COLS):
                color = ROW_COLORS[r % len(ROW_COLORS)]
                x = BRICK_LEFT + c * (BRICK_W + BRICK_PAD)
                y = BRICK_TOP + r * (BRICK_H + BRICK_PAD)
                # «Крепость» кирпича = ряд: 1 удар для верхнего, 2-3 для нижних
                hp = 1 if r < 3 else 2
                self.bricks.append({
                    "rect": pygame.Rect(x, y, BRICK_W, BRICK_H),
                    "color": color, "hp": hp, "max_hp": hp,
                })

    def _reset_ball(self):
        self.ball_x = self.paddle_x + PADDLE_W // 2
        self.ball_y = PADDLE_Y - BALL_R - 2
        self.ball_dx = 0
        self.ball_dy = 0
        self.ball_stuck = True

    def _launch_ball(self):
        angle = random.uniform(-math.pi / 3, math.pi / 3) - math.pi / 2
        self.ball_dx = math.cos(angle) * BALL_SPEED
        self.ball_dy = math.sin(angle) * BALL_SPEED
        self.ball_stuck = False

    def _spawn_particles(self, cx, cy, color, count=10):
        for _ in range(count):
            self.particles.append({
                "x": float(cx), "y": float(cy),
                "vx": random.uniform(-250, 250),
                "vy": random.uniform(-350, -50),
                "life": 0.7, "max_life": 0.7,
                "color": color, "size": random.randint(3, 6),
            })

    def _update_particles(self, dt):
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 900 * dt
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _draw_particles(self, scr):
        for p in self.particles:
            a = int(255 * (p["life"] / p["max_life"]))
            if a <= 0:
                continue
            s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            s.fill((*p["color"], a))
            scr.blit(s, (int(p["x"]), int(p["y"])))

    def _handle_events(self, events=None):
        if events is None:
            events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key in (pygame.K_p, pygame.K_SPACE) or getattr(e, "scancode", 0) == 19:
                    if not self.game_over:
                        self.paused = not self.paused
                if self.game_over or self.won:
                    if e.key == pygame.K_RETURN:
                        self.reset()
                    continue
                # Запуск мяча (SPACE / Enter)
                if self.ball_stuck and e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._launch_ball()
        return True

    def _update(self, dt):
        self._update_particles(dt)
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0

        if self.paused or self.game_over or self.won:
            return

        # Управление платформой — WASD + стрелки + scancode для русской
        keys = pygame.key.get_pressed()
        sc = 0
        # scancode для W/A/S/D: 26/4/22/7 — их берём через key.get_pressed нельзя.
        # Работаем по key-коду + дополнительно примем стрелки
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle_x -= PADDLE_SPEED * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle_x += PADDLE_SPEED * dt
        self.paddle_x = max(0, min(WIDTH - PADDLE_W, self.paddle_x))

        if self.ball_stuck:
            self.ball_x = self.paddle_x + PADDLE_W // 2
            self.ball_y = PADDLE_Y - BALL_R - 2
            return

        # Движение мяча
        self.ball_x += self.ball_dx * dt
        self.ball_y += self.ball_dy * dt

        # Отскок от стен
        if self.ball_x - BALL_R <= 0:
            self.ball_x = BALL_R
            self.ball_dx = abs(self.ball_dx)
            if self.snd_hit: self.snd_hit.play()
        elif self.ball_x + BALL_R >= WIDTH:
            self.ball_x = WIDTH - BALL_R
            self.ball_dx = -abs(self.ball_dx)
            if self.snd_hit: self.snd_hit.play()
        if self.ball_y - BALL_R <= 0:
            self.ball_y = BALL_R
            self.ball_dy = abs(self.ball_dy)
            if self.snd_hit: self.snd_hit.play()

        # Упал вниз — потеря жизни
        if self.ball_y - BALL_R > HEIGHT:
            self.lives -= 1
            if self.snd_life: self.snd_life.play()
            if self.lives <= 0:
                self.game_over = True
                try:
                    if records.submit("breakout", self.score):
                        print(f"[breakout] 🏆 Новый рекорд: {self.score}!")
                except Exception:
                    pass
                self.high_score = records.get("breakout")
                if self.snd_over: self.snd_over.play()
            else:
                self._reset_ball()
            return

        # Отскок от платформы
        if self.ball_dy > 0:
            paddle_rect = pygame.Rect(self.paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H)
            ball_rect = pygame.Rect(self.ball_x - BALL_R, self.ball_y - BALL_R,
                                    BALL_R * 2, BALL_R * 2)
            if paddle_rect.colliderect(ball_rect):
                self.ball_y = PADDLE_Y - BALL_R
                # Отражение с учётом попадания
                hit_x = (self.ball_x - (self.paddle_x + PADDLE_W / 2)) / (PADDLE_W / 2)
                hit_x = max(-1, min(1, hit_x))
                angle = hit_x * (math.pi / 3)
                # Ускоряем
                speed = min(BALL_SPEED_MAX,
                            math.hypot(self.ball_dx, self.ball_dy) + 20)
                self.ball_dx = math.sin(angle) * speed
                self.ball_dy = -math.cos(angle) * speed
                if self.snd_hit: self.snd_hit.play()

        # Отскок от кирпичей
        ball_rect = pygame.Rect(self.ball_x - BALL_R, self.ball_y - BALL_R,
                                BALL_R * 2, BALL_R * 2)
        for b in self.bricks[:]:
            if ball_rect.colliderect(b["rect"]):
                # Определяем сторону удара (по перекрытию)
                overlap_left = ball_rect.right - b["rect"].left
                overlap_right = b["rect"].right - ball_rect.left
                overlap_top = ball_rect.bottom - b["rect"].top
                overlap_bottom = b["rect"].bottom - ball_rect.top
                min_ov = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                if min_ov == overlap_left or min_ov == overlap_right:
                    self.ball_dx = -self.ball_dx
                else:
                    self.ball_dy = -self.ball_dy

                b["hp"] -= 1
                if b["hp"] <= 0:
                    # Уничтожен
                    self.bricks.remove(b)
                    self.score += 10 * self.level
                    self.combo_count += 1
                    self.combo_timer = 0.5
                    self._spawn_particles(b["rect"].centerx, b["rect"].centery,
                                          b["color"], count=12)
                    if self.snd_brick: self.snd_brick.play()
                    # С вероятностью 15% — бонус
                    if random.random() < 0.15:
                        kind = random.choice(["wide", "extra"])
                        self.powerups.append({
                            "x": b["rect"].centerx,
                            "y": b["rect"].centery,
                            "kind": kind,
                            "vy": 180,
                        })
                else:
                    # Просто повреждён — меняем цвет
                    b["color"] = tuple(max(0, c - 60) for c in b["color"])
                    self.score += 5
                break

        # Бонусы
        for pu in self.powerups[:]:
            pu["y"] += pu["vy"] * dt
            pu_rect = pygame.Rect(pu["x"] - 14, pu["y"] - 14, 28, 28)
            paddle_rect = pygame.Rect(self.paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H)
            if pu_rect.colliderect(paddle_rect):
                if pu["kind"] == "wide":
                    # Расширяем платформу на 20 (максимум 200)
                    delta = 20
                    self.paddle_x -= delta // 2
                    self.paddle_x = max(0, min(WIDTH - PADDLE_W, self.paddle_x))
                elif pu["kind"] == "extra":
                    self.lives += 1
                self.score += 25
                if self.snd_powerup: self.snd_powerup.play()
                self.powerups.remove(pu)
                continue
            if pu["y"] > HEIGHT + 30:
                self.powerups.remove(pu)

        # Победа — все кирпичи уничтожены
        if not self.bricks:
            self.won = True
            self.level += 1
            if self.snd_levelup: self.snd_levelup.play()
            try:
                if records.submit("breakout", self.score):
                    print(f"[breakout] 🏆 Рекорд: {self.score}!")
            except Exception:
                pass
            self.high_score = records.get("breakout")
            # Автопереход через 1.5 сек — сделаем через флаг
            pygame.time.set_timer(pygame.USEREVENT + 1, 1500, loops=1)

    def _draw(self):
        self.screen.fill(C_BG)

        # Рамка поля
        pygame.draw.rect(self.screen, C_BORDER,
                         (0, 0, WIDTH, HEIGHT), 2)

        # Кирпичи
        for b in self.bricks:
            color = b["color"]
            # Тёмная основа + светлая обводка
            pygame.draw.rect(self.screen, color, b["rect"], border_radius=5)
            # Верхний блик
            lighter = tuple(min(255, c + 60) for c in color)
            pygame.draw.line(self.screen, lighter,
                             (b["rect"].x + 4, b["rect"].y + 3),
                             (b["rect"].right - 4, b["rect"].y + 3), 2)
            # Тень снизу
            darker = tuple(max(0, c - 80) for c in color)
            pygame.draw.line(self.screen, darker,
                             (b["rect"].x + 4, b["rect"].bottom - 2),
                             (b["rect"].right - 4, b["rect"].bottom - 2), 2)

        # Бонусы
        for pu in self.powerups:
            if pu["kind"] == "wide":
                col = (100, 220, 255)
                letter = "W"
            else:
                col = (255, 100, 140)
                letter = "+1"
            pygame.draw.circle(self.screen, col, (int(pu["x"]), int(pu["y"])), 14)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(pu["x"]), int(pu["y"])), 14, 2)
            f = pygame.font.Font(None, 16)
            t = f.render(letter, True, (20, 20, 30))
            self.screen.blit(t, (pu["x"] - t.get_width() // 2,
                                 pu["y"] - t.get_height() // 2))

        # Платформа — с градиентом
        px, py = self.paddle_x, PADDLE_Y
        for i in range(PADDLE_H):
            t = i / PADDLE_H
            col = (
                int(C_PADDLE[0] * (1 - t) + 60 * t),
                int(C_PADDLE[1] * (1 - t) + 120 * t),
                int(C_PADDLE[2] * (1 - t) + 180 * t),
            )
            pygame.draw.line(self.screen, col,
                             (px + 3, py + i), (px + PADDLE_W - 3, py + i))
        pygame.draw.rect(self.screen, C_PADDLE,
                         (px, py, PADDLE_W, PADDLE_H),
                         border_radius=PADDLE_H // 2, width=2)

        # Мяч с свечением
        bx, by = int(self.ball_x), int(self.ball_y)
        for r in range(BALL_R, BALL_R * 2, 3):
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            a = max(0, 60 - r * 3)
            pygame.draw.circle(glow, (*C_BALL, a), (r, r), r)
            self.screen.blit(glow, (bx - r, by - r))
        pygame.draw.circle(self.screen, C_BALL, (bx, by), BALL_R)
        pygame.draw.circle(self.screen, (255, 255, 255), (bx - 3, by - 3), 3)

        # Частицы
        self._draw_particles(self.screen)

        # === HUD ===
        # Счёт
        sc = self.font.render(f"СЧЁТ: {self.score}", True, C_TEXT)
        self.screen.blit(sc, (20, 20))
        # Рекорд
        hi = self.font_small.render(f"РЕКОРД: {self.high_score}", True, C_GOLD)
        self.screen.blit(hi, (20, 52))
        # Жизни
        lives_txt = self.font.render(f"❤ {self.lives}", True, (255, 100, 140))
        self.screen.blit(lives_txt, (WIDTH - lives_txt.get_width() - 20, 20))
        # Уровень
        lvl_txt = self.font_small.render(f"УРОВЕНЬ {self.level}",
                                         True, C_TEXT_DIM)
        self.screen.blit(lvl_txt, (WIDTH - lvl_txt.get_width() - 20, 54))

        # Комбо
        if self.combo_count >= 3 and self.combo_timer > 0:
            t = min(1.0, self.combo_timer / 0.5)
            size = int(28 + 12 * t)
            f = pygame.font.Font(None, size)
            col = (255, 220, 100) if self.combo_count < 6 else (255, 140, 220)
            txt = f.render(f"x{self.combo_count} КОМБО!",
                           True, col)
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 100))

        # Приклеен — подсказка
        if self.ball_stuck and not self.game_over and not self.won:
            hint = self.font.render("Нажми SPACE — запустить мяч",
                                    True, C_TEXT)
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2,
                                     HEIGHT - 100))

        # Пауза
        if self.paused:
            self._overlay("ПАУЗА", "P — продолжить")

        # Победа
        if self.won:
            self._overlay("УРОВЕНЬ ПРОЙДЕН!",
                          f"Счёт: {self.score}",
                          "Enter — продолжить")

        # Game Over
        if self.game_over:
            self._overlay("ИГРА ОКОНЧЕНА",
                          f"Счёт: {self.score}",
                          f"Рекорд: {self.high_score}",
                          "Enter — заново, Esc — выход")

    def _overlay(self, title, *subs):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))
        tt = self.font_big.render(title, True, C_TEXT)
        self.screen.blit(tt, (WIDTH // 2 - tt.get_width() // 2,
                              HEIGHT // 2 - 80))
        for i, s in enumerate(subs):
            st = self.font.render(s, True, C_TEXT_DIM)
            self.screen.blit(st, (WIDTH // 2 - st.get_width() // 2,
                                  HEIGHT // 2 + 10 + i * 30))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            if not self._handle_events():
                break
            # Проверка автоперехода на след. уровень
            for e in pygame.event.get(pygame.USEREVENT + 1):
                if self.won:
                    self.level_up_next()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        return True

    def level_up_next(self):
        """Переход на следующий уровень."""
        new_level = self.level
        new_lives = self.lives
        new_score = self.score
        self.reset()
        self.level = new_level
        self.lives = new_lives
        self.score = new_score
        self._build_bricks()
        self._reset_ball()


if __name__ == "__main__":
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    game = BreakoutGame()
    game.run()
    pygame.quit()
    sys.exit(0)
