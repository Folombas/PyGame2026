"""Bunny's Descent — roguelike в вселенной BunnyOS."""
import sys
import pygame
from settings import *
from dungeon import Dungeon
from player import Player


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

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == "title" and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.start_game()
                elif self.state == "game":
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.player.try_move(0, -1, self.dungeon)
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.player.try_move(0, 1, self.dungeon)
                    elif e.key in (pygame.K_LEFT, pygame.K_a):
                        self.player.try_move(-1, 0, self.dungeon)
                    elif e.key in (pygame.K_RIGHT, pygame.K_d):
                        self.player.try_move(1, 0, self.dungeon)

    def update(self, dt):
        self.timer += dt
        if self.state == "game":
            self.player.update(dt)
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
        self.screen.blit(title, (tx, HEIGHT // 2 - 100))

        sub = self.font.render("Провал в систему", True, C_ACCENT)
        sx = WIDTH // 2 - sub.get_width() // 2
        self.screen.blit(sub, (sx, HEIGHT // 2 - 30))

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
            self.player.draw(self.screen, int(self.cam_x), int(self.cam_y))
            self.draw_hud()
        pygame.display.flip()

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
