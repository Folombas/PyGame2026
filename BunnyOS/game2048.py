"""2048 — головоломка с плавной анимацией."""
import pygame
import random
import sys
import math


SIZE = 4
CELL = 110
GAP = 12
BOARD = SIZE * CELL + (SIZE + 1) * GAP
SIDE_W = 200
WIDTH = BOARD + SIDE_W + 30
HEIGHT = BOARD + 40
FPS = 60

C_BG       = (18, 22, 32)
C_BOARD    = (28, 34, 48)
C_EMPTY    = (40, 48, 66)
C_BORDER   = (60, 80, 120)
C_TEXT     = (220, 230, 245)
C_TEXT_DIM = (120, 140, 170)

TILE_COLORS = {
    2:    (238, 228, 218),
    4:    (237, 224, 200),
    8:    (242, 177, 121),
    16:   (245, 149, 99),
    32:   (246, 124, 95),
    64:   (246, 94, 59),
    128:  (237, 207, 114),
    256:  (237, 204, 97),
    512:  (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    4096: (240, 100, 160),
    8192: (200, 60, 220),
}

TEXT_COLORS = {2: (60, 60, 60), 4: (60, 60, 60)}
TEXT_LIGHT = (250, 250, 250)

VOLUME_MASTER = 0.25


class Game2048:
    def __init__(self, screen=None):
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2048 — BunnyOS")
        self.clock = pygame.time.Clock()
        self.font_tile = pygame.font.Font(None, 48)
        self.font_big = pygame.font.Font(None, 44)
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        self.snd_move = self._load("assets/games/sounds/tetris/selection.wav", 0.3)
        self.snd_merge = self._load("assets/games/sounds/tetris/coin_01.wav", 0.5)
        self.snd_win = self._load("assets/games/sounds/tetris/jingle_01.wav", 0.6)
        self.snd_over = self._load("assets/games/sounds/tetris/gameover.wav", 0.5)

        self.reset()

    def _load(self, path, vol=0.5):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(vol * VOLUME_MASTER)
            return s
        except Exception:
            return None

    def reset(self):
        self.grid = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.best = getattr(self, "best", 0)
        self.game_over = False
        self.won = False
        self.win_shown = False
        self.animations = []
        self._spawn()
        self._spawn()

    def _spawn(self):
        empties = [(r, c) for r in range(SIZE) for c in range(SIZE)
                   if self.grid[r][c] == 0]
        if not empties:
            return
        r, c = random.choice(empties)
        self.grid[r][c] = 4 if random.random() < 0.1 else 2
        self.animations.append({
            "r": r, "c": c, "value": self.grid[r][c],
            "t": 0.0, "kind": "spawn",
        })

    def _can_move(self):
        for r in range(SIZE):
            for c in range(SIZE):
                if self.grid[r][c] == 0:
                    return True
        for r in range(SIZE):
            for c in range(SIZE):
                v = self.grid[r][c]
                if c + 1 < SIZE and self.grid[r][c + 1] == v:
                    return True
                if r + 1 < SIZE and self.grid[r + 1][c] == v:
                    return True
        return False

    def _slide_line(self, line):
        non_zero = [x for x in line if x != 0]
        result = []
        score = 0
        merges = []
        i = 0
        while i < len(non_zero):
            if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
                merged = non_zero[i] * 2
                merges.append(len(result))
                result.append(merged)
                score += merged
                i += 2
            else:
                result.append(non_zero[i])
                i += 1
        while len(result) < SIZE:
            result.append(0)
        return result, score, merges

    def _move(self, direction):
        old_grid = [row[:] for row in self.grid]
        gained = 0
        merge_cells = []

        if direction == "left":
            for r in range(SIZE):
                new, sc, mg = self._slide_line(self.grid[r])
                self.grid[r] = new
                gained += sc
                merge_cells.extend([(r, c) for c in mg])
        elif direction == "right":
            for r in range(SIZE):
                new, sc, mg = self._slide_line(list(reversed(self.grid[r])))
                self.grid[r] = list(reversed(new))
                gained += sc
                merge_cells.extend([(r, SIZE - 1 - c) for c in mg])
        elif direction == "up":
            for c in range(SIZE):
                col = [self.grid[r][c] for r in range(SIZE)]
                new, sc, mg = self._slide_line(col)
                for r in range(SIZE):
                    self.grid[r][c] = new[r]
                gained += sc
                merge_cells.extend([(r, c) for r in mg])
        elif direction == "down":
            for c in range(SIZE):
                col = [self.grid[r][c] for r in range(SIZE)]
                new, sc, mg = self._slide_line(list(reversed(col)))
                new = list(reversed(new))
                for r in range(SIZE):
                    self.grid[r][c] = new[r]
                gained += sc
                merge_cells.extend([(SIZE - 1 - r, c) for r in mg])

        if self.grid != old_grid:
            self.score += gained
            self.best = max(self.best, self.score)
            for (r, c) in merge_cells:
                self.animations.append({
                    "r": r, "c": c, "value": self.grid[r][c],
                    "t": 0.0, "kind": "merge",
                })
            if gained > 0 and self.snd_merge:
                self.snd_merge.play()
            elif self.snd_move:
                self.snd_move.play()

            for row in self.grid:
                if 2048 in row and not self.win_shown:
                    self.win_shown = True
                    self.won = True
                    if self.snd_win:
                        self.snd_win.play()

            self._spawn()
            if not self._can_move():
                self.game_over = True
                if self.snd_over:
                    self.snd_over.play()
            return True
        return False

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key == pygame.K_r:
                    self.reset()
                    continue
                if self.game_over:
                    if e.key == pygame.K_RETURN:
                        self.reset()
                    continue
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self._move("left")
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self._move("right")
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self._move("up")
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self._move("down")
        return True

    def _update(self, dt):
        for a in self.animations:
            a["t"] += dt
        self.animations = [a for a in self.animations if a["t"] < 0.2]

    def _draw_tile(self, scr, x, y, value, scale=1.0, alpha=255):
        if value == 0:
            pygame.draw.rect(scr, C_EMPTY, (x, y, CELL, CELL), border_radius=8)
            return
        color = TILE_COLORS.get(value, (255, 100, 200))
        txt_col = TEXT_COLORS.get(value, TEXT_LIGHT)

        size = int(CELL * scale)
        offset = (CELL - size) // 2

        sh = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 60), (0, 0, size, size), border_radius=8)
        scr.blit(sh, (x + offset + 3, y + offset + 3))

        s = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (0, 0, size, size), border_radius=8)
        lighter = tuple(min(255, c + 30) for c in color)
        pygame.draw.rect(s, lighter, (0, 0, size, size // 3), border_radius=8)
        if alpha < 255:
            s.set_alpha(alpha)
        scr.blit(s, (x + offset, y + offset))

        font_size = 48 if value < 100 else 40 if value < 1000 else 32
        f = pygame.font.Font(None, font_size)
        text = f.render(str(value), True, txt_col)
        tx = x + CELL // 2 - text.get_width() // 2
        ty = y + CELL // 2 - text.get_height() // 2
        if alpha < 255:
            text.set_alpha(alpha)
        scr.blit(text, (tx, ty))

    def _draw(self):
        self.screen.fill(C_BG)

        board_rect = pygame.Rect(15, 20, BOARD, BOARD)
        pygame.draw.rect(self.screen, C_BOARD, board_rect, border_radius=12)

        for r in range(SIZE):
            for c in range(SIZE):
                x = board_rect.x + GAP + c * (CELL + GAP)
                y = board_rect.y + GAP + r * (CELL + GAP)
                self._draw_tile(self.screen, x, y, self.grid[r][c])

        for a in self.animations:
            x = board_rect.x + GAP + a["c"] * (CELL + GAP)
            y = board_rect.y + GAP + a["r"] * (CELL + GAP)
            t = a["t"] / 0.2
            if a["kind"] == "spawn":
                scale = 0.3 + 0.7 * min(1.0, t)
                alpha = int(255 * min(1.0, t))
            else:
                scale = 1.0 + 0.2 * math.sin(t * math.pi)
                alpha = 255
            self._draw_tile(self.screen, x, y, a["value"], scale, alpha)

        pygame.draw.rect(self.screen, C_BORDER, board_rect, 2, border_radius=12)

        sx = board_rect.right + 20
        sy = 20

        title = self.font_big.render("2048", True, (240, 200, 80))
        self.screen.blit(title, (sx, sy))

        self._sidebar_box(sx, sy + 60, SIDE_W - 20, 60, "СЧЁТ", str(self.score))
        self._sidebar_box(sx, sy + 130, SIDE_W - 20, 60, "РЕКОРД", str(self.best))

        controls_y = sy + 220
        controls = [
            ("^ v < >", "движение"),
            ("WASD", "то же"),
            ("R", "новая игра"),
            ("Esc", "выход"),
        ]
        label = self.font_small.render("УПРАВЛЕНИЕ", True, C_TEXT_DIM)
        self.screen.blit(label, (sx, controls_y))
        for i, (key, desc) in enumerate(controls):
            kt = self.font_small.render(key, True, C_TEXT)
            dt = self.font_small.render(desc, True, C_TEXT_DIM)
            self.screen.blit(kt, (sx, controls_y + 25 + i * 22))
            self.screen.blit(dt, (sx + 80, controls_y + 25 + i * 22))

        if self.won and not self.game_over:
            badge = self.font.render("2048!", True, (240, 200, 80))
            self.screen.blit(badge, (sx, sy + 180))

        if self.game_over:
            self._overlay("ИГРА ОКОНЧЕНА", f"Счёт: {self.score}",
                          "Enter — заново, R — сброс, Esc — выход")

    def _sidebar_box(self, x, y, w, h, label, value):
        box = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, C_BOARD, box, border_radius=8)
        pygame.draw.rect(self.screen, C_BORDER, box, 1, border_radius=8)
        lt = self.font_small.render(label, True, C_TEXT_DIM)
        vt = self.font.render(value, True, C_TEXT)
        self.screen.blit(lt, (x + 12, y + 8))
        self.screen.blit(vt, (x + 12, y + 28))

    def _overlay(self, title, *subs):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))
        tt = self.font_big.render(title, True, C_TEXT)
        self.screen.blit(tt, (WIDTH // 2 - tt.get_width() // 2, HEIGHT // 2 - 60))
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
    game = Game2048()
    game.run()
    pygame.quit()
    sys.exit(0)
