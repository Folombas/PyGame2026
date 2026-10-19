"""Asteroids — космический шутер в стиле BunnyOS."""
import pygame
import random
import sys
import math
import records


WIDTH, HEIGHT = 900, 700
FPS = 60

C_BG = (8, 10, 20)
C_TEXT = (220, 230, 245)
C_TEXT_DIM = (120, 140, 170)
C_SHIP = (100, 200, 255)
C_BULLET = (255, 240, 100)
C_ASTEROID = (180, 170, 140)
C_ACCENT = (100, 180, 255)

SHIP_SIZE = 14
SHIP_TURN = 4.0
SHIP_THRUST = 300
SHIP_FRICTION = 0.99
MAX_SPEED = 400

BULLET_SPEED = 550
BULLET_LIFE = 1.2

AST_RADII = [50, 30, 18]
AST_SPEEDS = [60, 90, 120]

VOLUME_MASTER = 0.25


class Ship:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = self.vy = 0
        self.angle = -90  # смотрит вверх
        self.alive = True
        self.invuln = 2.0  # секунд неуязвимости
        self.thrusting = False

    def update(self, dt, keys):
        if not self.alive:
            return
        if self.invuln > 0:
            self.invuln -= dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= SHIP_TURN
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += SHIP_TURN
        self.thrusting = False
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            rad = math.radians(self.angle)
            self.vx += math.cos(rad) * SHIP_THRUST * dt
            self.vy += math.sin(rad) * SHIP_THRUST * dt
            self.thrusting = True
        # трение
        self.vx *= SHIP_FRICTION
        self.vy *= SHIP_FRICTION
        # макс скорость
        sp = math.hypot(self.vx, self.vy)
        if sp > MAX_SPEED:
            self.vx = self.vx / sp * MAX_SPEED
            self.vy = self.vy / sp * MAX_SPEED
        self.x += self.vx * dt
        self.y += self.vy * dt
        # wrap
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, scr):
        if not self.alive:
            return
        # мигание при неуязвимости
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            return
        rad = math.radians(self.angle)
        # треугольник
        p1 = (self.x + math.cos(rad) * SHIP_SIZE,
              self.y + math.sin(rad) * SHIP_SIZE)
        p2 = (self.x + math.cos(rad + 2.5) * SHIP_SIZE * 0.9,
              self.y + math.sin(rad + 2.5) * SHIP_SIZE * 0.9)
        p3 = (self.x + math.cos(rad - 2.5) * SHIP_SIZE * 0.9,
              self.y + math.sin(rad - 2.5) * SHIP_SIZE * 0.9)
        pygame.draw.polygon(scr, C_SHIP, [p1, p2, p3])
        pygame.draw.polygon(scr, (200, 240, 255), [p1, p2, p3], 2)
        # выхлоп
        if self.thrusting:
            px = self.x - math.cos(rad) * SHIP_SIZE * 1.2
            py = self.y - math.sin(rad) * SHIP_SIZE * 1.2
            pygame.draw.circle(scr, (255, 180, 80), (int(px), int(py)), 5)
            pygame.draw.circle(scr, (255, 240, 140), (int(px), int(py)), 2)

    def get_poly(self):
        rad = math.radians(self.angle)
        return [
            (self.x + math.cos(rad) * SHIP_SIZE,
             self.y + math.sin(rad) * SHIP_SIZE),
            (self.x + math.cos(rad + 2.5) * SHIP_SIZE * 0.9,
             self.y + math.sin(rad + 2.5) * SHIP_SIZE * 0.9),
            (self.x + math.cos(rad - 2.5) * SHIP_SIZE * 0.9,
             self.y + math.sin(rad - 2.5) * SHIP_SIZE * 0.9),
        ]


class Bullet:
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        rad = math.radians(angle)
        self.vx = math.cos(rad) * BULLET_SPEED
        self.vy = math.sin(rad) * BULLET_SPEED
        self.life = BULLET_LIFE

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x %= WIDTH
        self.y %= HEIGHT
        self.life -= dt

    def draw(self, scr):
        pygame.draw.circle(scr, C_BULLET, (int(self.x), int(self.y)), 3)


class Asteroid:
    def __init__(self, x, y, size_idx):
        self.x, self.y = x, y
        self.size_idx = size_idx
        self.radius = AST_RADII[size_idx]
        angle = random.uniform(0, math.tau)
        speed = AST_SPEEDS[size_idx]
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        # полигон (случайной формы)
        self.poly = []
        n = random.randint(8, 12)
        for i in range(n):
            a = i * math.tau / n
            r = self.radius * random.uniform(0.8, 1.2)
            self.poly.append((math.cos(a) * r, math.sin(a) * r))

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, scr):
        points = [(self.x + dx, self.y + dy) for dx, dy in self.poly]
        pygame.draw.polygon(scr, C_ASTEROID, points)
        pygame.draw.polygon(scr, (120, 110, 90), points, 2)

    def hit(self, x, y, r=5):
        return math.hypot(self.x - x, self.y - y) < self.radius + r


class AsteroidsGame:
    def __init__(self, screen=None):
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        if screen is None:
            pygame.display.set_caption("Asteroids — BunnyOS")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 18)
        self.high_score = records.get("asteroids")
        # Звуки
        self.snd_shoot = self._load("assets/games/sounds/tetris/laser_01.wav", 0.25)
        self.snd_boom = self._load("assets/games/sounds/tetris/explosion_05.wav", 0.5)
        self.snd_die = self._load("assets/games/sounds/tetris/gameover.wav", 0.5)
        self.snd_combo = self._load("assets/games/sounds/tetris/coin_05.wav", 0.4)
        self.reset()

    def _load(self, path, vol=0.5):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(vol * VOLUME_MASTER)
            return s
        except Exception:
            return None

    def reset(self):
        self.ship = Ship(WIDTH // 2, HEIGHT // 2)
        self.bullets = []
        self.asteroids = []
        self.particles = []
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.paused = False
        self.combo = 0
        self.combo_timer = 0
        self._spawn_wave()

    def _spawn_wave(self):
        n = 3 + self.level
        for _ in range(n):
            while True:
                x = random.uniform(0, WIDTH)
                y = random.uniform(0, HEIGHT)
                # не рядом с игроком
                if math.hypot(x - self.ship.x, y - self.ship.y) > 200:
                    break
            self.asteroids.append(Asteroid(x, y, 0))

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
                if self.game_over and e.key == pygame.K_RETURN:
                    self.reset()
                    continue
                if not self.game_over and not self.paused:
                    if e.key == pygame.K_SPACE or e.key == pygame.K_LCTRL:
                        if len(self.bullets) < 5:
                            rad = math.radians(self.ship.angle)
                            bx = self.ship.x + math.cos(rad) * SHIP_SIZE
                            by = self.ship.y + math.sin(rad) * SHIP_SIZE
                            self.bullets.append(Bullet(bx, by, self.ship.angle))
                            if self.snd_shoot:
                                self.snd_shoot.play()
        return True

    def _explode(self, x, y, color=C_ASTEROID, count=15):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            sp = random.uniform(50, 300)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                "life": random.uniform(0.5, 1.0),
                "max_life": 1.0,
                "color": color, "size": random.randint(2, 5),
            })

    def _update_particles(self, dt):
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _draw_particles(self, scr):
        for p in self.particles:
            a = int(255 * max(0, p["life"] / p["max_life"]))
            if a <= 0:
                continue
            s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            s.fill((*p["color"], a))
            scr.blit(s, (int(p["x"]), int(p["y"])))

    def _update(self, dt):
        self._update_particles(dt)
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0
        if self.paused or self.game_over:
            return
        keys = pygame.key.get_pressed()
        self.ship.update(dt, keys)
        for b in self.bullets[:]:
            b.update(dt)
            if b.life <= 0:
                self.bullets.remove(b)
        for a in self.asteroids:
            a.update(dt)
        # Пули vs астероиды
        for b in self.bullets[:]:
            for a in self.asteroids[:]:
                if a.hit(b.x, b.y, 3):
                    self.bullets.remove(b)
                    self.asteroids.remove(a)
                    self._explode(a.x, a.y, C_ASTEROID, 20)
                    if self.snd_boom:
                        self.snd_boom.play()
                    # очки зависят от размера
                    pts = [50, 30, 15][a.size_idx]
                    self.combo += 1
                    self.combo_timer = 1.5
                    self.score += pts * self.combo
                    # разбиваем на части
                    if a.size_idx < 2:
                        for _ in range(2):
                            child = Asteroid(a.x, a.y, a.size_idx + 1)
                            self.asteroids.append(child)
                    break
        # Корабль vs астероиды
        if self.ship.alive and self.ship.invuln <= 0:
            for a in self.asteroids:
                if a.hit(self.ship.x, self.ship.y, SHIP_SIZE * 0.7):
                    self.ship.alive = False
                    self._explode(self.ship.x, self.ship.y, C_SHIP, 40)
                    if self.snd_die:
                        self.snd_die.play()
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                        records.submit("asteroids", self.score)
                        self.high_score = records.get("asteroids")
                    else:
                        # респавн через 1 сек
                        pygame.time.set_timer(pygame.USEREVENT + 1, 1000, loops=1)
                    break
        # Следующая волна
        if not self.asteroids and not self.game_over:
            self.level += 1
            self._spawn_wave()

    def _respawn(self):
        self.ship = Ship(WIDTH // 2, HEIGHT // 2)

    def _draw(self):
        self.screen.fill(C_BG)
        # Звёзды
        rng = random.Random(42)
        for _ in range(60):
            x = rng.randint(0, WIDTH)
            y = rng.randint(0, HEIGHT)
            a = rng.randint(60, 200)
            s = pygame.Surface((2, 2), pygame.SRCALPHA)
            s.fill((a, a, 255, a))
            self.screen.blit(s, (x, y))

        for a in self.asteroids:
            a.draw(self.screen)
        for b in self.bullets:
            b.draw(self.screen)
        self.ship.draw(self.screen)
        self._draw_particles(self.screen)

        # HUD
        sc = self.font.render(f"СЧЁТ: {self.score}", True, C_TEXT)
        self.screen.blit(sc, (20, 20))
        hi = self.font_small.render(f"РЕКОРД: {self.high_score}", True, (255, 220, 100))
        self.screen.blit(hi, (20, 52))
        lv = self.font.render(f"LVL {self.level}", True, C_ACCENT)
        self.screen.blit(lv, (WIDTH // 2 - lv.get_width() // 2, 20))
        lv_lives = self.font.render(f"❤ {self.lives}", True, (255, 100, 140))
        self.screen.blit(lv_lives, (WIDTH - lv_lives.get_width() - 20, 20))

        # Комбо
        if self.combo >= 2 and self.combo_timer > 0:
            t = min(1.0, self.combo_timer / 1.5)
            col = (255, 220, 100) if self.combo < 5 else (255, 140, 220)
            ct = self.font_big.render(f"x{self.combo} КОМБО", True, col)
            self.screen.blit(ct, (WIDTH // 2 - ct.get_width() // 2, 80))

        # Управление
        hint = self.font_small.render(
            "WASD/↑↓←→ — движение    SPACE — стрелять    P — пауза    Esc — выход",
            True, C_TEXT_DIM)
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))

        if self.paused:
            self._overlay("ПАУЗА", "P — продолжить")
        if self.game_over:
            self._overlay("ИГРА ОКОНЧЕНА", f"Счёт: {self.score}",
                          f"Рекорд: {self.high_score}", "Enter — заново")

    def _overlay(self, title, *subs):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))
        tt = self.font_big.render(title, True, C_TEXT)
        self.screen.blit(tt, (WIDTH // 2 - tt.get_width() // 2, HEIGHT // 2 - 80))
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
            for e in pygame.event.get(pygame.USEREVENT + 1):
                if not self.ship.alive and self.lives > 0:
                    self._respawn()
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
    game = AsteroidsGame()
    game.run()
    pygame.quit()
    sys.exit(0)
