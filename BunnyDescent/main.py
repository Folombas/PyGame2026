"""Bunny's Descent — roguelike в вселенной BunnyOS."""
import sys
import math
import pygame
from settings import *
from dungeon import Dungeon
from player import Player
from enemies import Enemy
import random


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bunny's Descent")
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_big = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)

        self.state = "title"
        self.timer = 0.0

    def start_game(self):
        self.dungeon = Dungeon(level=1)
        sx, sy = self.dungeon.spawn_pos()
        self.player = Player(sx, sy)
        self.cam_x = self.cam_y = 0
        self.state = "game"
        self._spawn_enemies()
        self.particles = []

    def _spawn_enemies(self):
        self.enemies = []
        free = self.dungeon.free_cells(exclude={(self.player.x, self.player.y)})
        # Разное количество в зависимости от уровня
        n = 6 + self.dungeon.level * 2
        for _ in range(min(n, len(free))):
            cell = random.choice(free)
            free.remove(cell)
            # Тип врага по глубине
            r = random.random()
            if self.dungeon.level >= 7 and r < 0.1:
                kind = "boss"
            elif self.dungeon.level >= 4 and r < 0.3:
                kind = "firewall"
            elif r < 0.5:
                kind = "virus"
            else:
                kind = "bug"
            self.enemies.append(Enemy(cell[0], cell[1], kind))

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state in ("title", "dead") and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.state == "dead":
                        self.state = "title"
                        self.timer = 0.0
                    else:
                        self.start_game()
                elif self.state == "game":
                    dx = dy = 0
                    if e.key in (pygame.K_UP, pygame.K_w): dy = -1
                    elif e.key in (pygame.K_DOWN, pygame.K_s): dy = 1
                    elif e.key in (pygame.K_LEFT, pygame.K_a): dx = -1
                    elif e.key in (pygame.K_RIGHT, pygame.K_d): dx = 1
                    if dx or dy:
                        self._try_player_action(dx, dy)

    def _try_player_action(self, dx, dy):
        """Атака или движение."""
        tx, ty = self.player.x + dx, self.player.y + dy
        # Есть ли враг на клетке?
        target = None
        for en in self.enemies:
            if en.x == tx and en.y == ty:
                target = en
                break
        if target:
            # Атака
            import random
            dmg = random.randint(self.player.attack - 1, self.player.attack + 1)
            target.hp -= dmg
            target.hit_flash = 0.15
            self._spawn_hit_particles(target.x, target.y, (255, 255, 200))
            if target.hp <= 0:
                # XP за убийство
                self.player.xp += target.xp_reward
                self.enemies.remove(target)
                # Левел-ап
                if self.player.xp >= self.player.level * 20:
                    self.player.xp -= self.player.level * 20
                    self.player.level += 1
                    self.player.max_hp += 5
                    self.player.hp = self.player.max_hp
                    self.player.attack += 1
                    self.player.defense += 0.5
        else:
            # Движение
            self.player.try_move(dx, dy, self.dungeon)

    def _spawn_hit_particles(self, tx, ty, color):
        import random
        for _ in range(8):
            a = random.uniform(0, 6.28)
            sp = random.uniform(80, 200)
            self.particles.append({
                "x": tx * TILE + TILE // 2, "y": ty * TILE + TILE // 2,
                "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                "life": 0.4, "max_life": 0.4,
                "color": color, "size": random.randint(2, 4),
            })

    def update(self, dt):
        self.timer += dt
        if self.state == "game":
            self.player.update(dt)
            # Враги
            for en in self.enemies[:]:
                en.update(dt, self.player, self.dungeon, self.enemies)
            # Смерть игрока
            if self.player.hp <= 0:
                self.state = "dead"
                self.death_timer = 0
            # Частицы
            for p in self.particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += 400 * dt
                p["life"] -= dt
            self.particles = [p for p in self.particles if p["life"] > 0]
            # Камера — центрируется на игроке
            target_x = self.player.x * TILE - WIDTH // 2 + TILE // 2
            target_y = self.player.y * TILE - HEIGHT // 2 + TILE // 2
            self.cam_x += (target_x - self.cam_x) * 0.15
            self.cam_y += (target_y - self.cam_y) * 0.15
            # Ограничения карты
            max_x = MAP_W * TILE - WIDTH
            max_y = MAP_H * TILE - HEIGHT
            self.cam_x = max(0, min(max_x, self.cam_x))
            self.cam_y = max(0, min(max_y, self.cam_y))

    def draw_title(self):
        self.screen.fill(C_BG)
        title = self.font_big.render("BUNNY'S DESCENT", True, C_GOLD)
        tx = WIDTH // 2 - title.get_width() // 2
        self.screen.blit(title, (tx, HEIGHT // 2 - 140))

        sub = self.font.render("Путь любопытства", True, C_ACCENT)
        sx = WIDTH // 2 - sub.get_width() // 2
        self.screen.blit(sub, (sx, HEIGHT // 2 - 70))

        # Философия
        lore = [
            "Зайка нашёл аномалию в своей системе.",
            "Он не хочет её взломать.",
            "Он хочет её — понять.",
            "",
            "10 уровней глубины. 10 слоёв загадок.",
            "Каждое существо хранит своё знание.",
        ]
        for i, line in enumerate(lore):
            color = C_TEXT if line else C_TEXT
            l = self.font_small.render(line, True, color)
            self.screen.blit(l, (WIDTH // 2 - l.get_width() // 2,
                                  HEIGHT // 2 - 30 + i * 24))

        if int(self.timer * 2) % 2 == 0:
            hint = self.font.render("Нажми ENTER чтобы начать", True, C_TEXT)
            hx = WIDTH // 2 - hint.get_width() // 2
            self.screen.blit(hint, (hx, HEIGHT // 2 + 60))

        v = self.font_small.render("v0.2 — procedural dungeon", True, C_TEXT_DIM)
        self.screen.blit(v, (20, HEIGHT - 30))

    def draw_map(self):
        cam_x = int(self.cam_x)
        cam_y = int(self.cam_y)
        # Видимый диапазон
        tx0 = max(0, cam_x // TILE)
        ty0 = max(0, cam_y // TILE)
        tx1 = min(MAP_W, (cam_x + WIDTH) // TILE + 1)
        ty1 = min(MAP_H, (cam_y + HEIGHT) // TILE + 1)

        for ty in range(ty0, ty1):
            for tx in range(tx0, tx1):
                t = self.dungeon.tiles[ty][tx]
                px = tx * TILE - cam_x
                py = ty * TILE - cam_y
                if t == 0:
                    # Стена
                    pygame.draw.rect(self.screen, C_WALL,
                                     (px, py, TILE, TILE))
                    pygame.draw.rect(self.screen, C_WALL_TOP,
                                     (px, py, TILE, 4))
                elif t == 1:
                    # Пол
                    color = C_FLOOR if (tx + ty) % 2 == 0 else C_FLOOR_DARK
                    pygame.draw.rect(self.screen, color,
                                     (px, py, TILE, TILE))
                elif t == 3:
                    # Лестница вниз
                    pygame.draw.rect(self.screen, C_FLOOR,
                                     (px, py, TILE, TILE))
                    # Стрелки вниз
                    for i in range(3):
                        cy = py + 8 + i * 6
                        pygame.draw.polygon(self.screen, C_STAIRS, [
                            (px + 6, cy),
                            (px + TILE - 6, cy),
                            (px + TILE // 2, cy + 6)
                        ])

    def draw_hud(self):
        # HP
        hp_pct = self.player.hp / self.player.max_hp
        bar_w = 220
        pygame.draw.rect(self.screen, (30, 20, 30), (20, 20, bar_w, 22))
        pygame.draw.rect(self.screen, C_HP, (20, 20, int(bar_w * hp_pct), 22))
        pygame.draw.rect(self.screen, C_TEXT, (20, 20, bar_w, 22), 2)
        hp_txt = self.font_small.render(
            f"HP {self.player.hp}/{self.player.max_hp}", True, C_TEXT)
        self.screen.blit(hp_txt, (24, 24))

        # XP
        xp_pct = self.player.xp / (self.player.level * 20) if self.player.level > 0 else 0
        pygame.draw.rect(self.screen, (20, 30, 40), (20, 50, 220, 12))
        pygame.draw.rect(self.screen, C_XP, (20, 50, int(220 * xp_pct), 12))
        pygame.draw.rect(self.screen, C_TEXT, (20, 50, 220, 12), 1)
        xp_txt = self.font_small.render(f"LVL {self.player.level}  XP {self.player.xp}/{self.player.level*20}", True, C_XP)
        self.screen.blit(xp_txt, (24, 50))

        # Глубина
        depth = self.font.render(f"ГЛУБИНА {self.dungeon.level}", True, C_GOLD)
        self.screen.blit(depth, (WIDTH // 2 - depth.get_width() // 2, 20))

        # Подсказки
        hint = self.font_small.render(
            "WASD/стрелки — движение    Esc — выход", True, C_TEXT_DIM)
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))

    def draw(self):
        if self.state == "title":
            self.draw_title()
        elif self.state == "game":
            self.screen.fill(C_BG)
            self.draw_map()
            # Враги
            for en in self.enemies:
                en.draw(self.screen, int(self.cam_x), int(self.cam_y))
            # Игрок
            self.player.draw(self.screen, int(self.cam_x), int(self.cam_y))
            # Частицы
            for p in self.particles:
                a = int(255 * (p["life"] / p["max_life"]))
                s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
                s.fill((*p["color"], a))
                self.screen.blit(s, (int(p["x"] - self.cam_x), int(p["y"] - self.cam_y)))
            self.draw_hud()
        elif self.state == "dead":
            self.draw_dead()
        pygame.display.flip()

    def draw_dead(self):
        self.screen.fill((30, 10, 15))
        t = self.font_big.render("ВЗЛОМ ПРОВАЛЕН", True, C_DANGER)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 80))
        s = self.font.render(f"Глубина: {self.dungeon.level}", True, C_TEXT)
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2))
        h = self.font.render("Enter — попробовать снова", True, C_ACCENT)
        self.screen.blit(h, (WIDTH // 2 - h.get_width() // 2, HEIGHT // 2 + 60))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Game().run()
