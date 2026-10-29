import random
from settings import COLS, ROWS, SHAPES, COLORS

class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.color = COLORS[kind]
        import random
        self.powerup = random.choices([None, 'bomb', 'freeze', 'clear'], weights=[80, 8, 6, 6])[0]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = -len(self.shape)

    def cells(self, dx=0, dy=0, shape=None):
        s = shape if shape is not None else self.shape
        for yy, row in enumerate(s):
            for xx, v in enumerate(row):
                if v:
                    yield self.x + xx + dx, self.y + yy + dy

class Game:
    LINE_SCORE = {1: 100, 2: 300, 3: 500, 4: 800}

    def __init__(self):
        self.on_clear = None    # callback(rows, count)
        self.on_lock = None
        self.on_rotate = None
        self.on_move = None
        self.on_gameover = None
        self.on_win = None
        self.on_levelup = None
        self.reset()

    def reset(self, zen=False, mode='classic'):
        self.zen = zen
        self.mode = mode
        self.elapsed_time = 0.0
        self.freeze_timer = 0
        self.garbage_timer = 10000
        self.show_ghost = True
        self.fall_speed_mult = 1.0
        self.show_grid = True
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.powerup_grid = {}
        self.bag = []
        self.current = self._spawn()
        self.next = self._spawn()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.combo = 0
        self.max_combo = 0
        self.pieces = 0
        self.game_over = False
        self.b2b = False
        self.fall_timer = 0.0
        self.lock_timer = 0.0
        self.clearing = []
        self.clear_timer = 0.0
        self.hold = None
        self.hold_used = False

    def _spawn(self):
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        return Piece(self.bag.pop())

    def fall_ms(self):
        return max(70, 600 - (self.level - 1) * 55)

    def valid(self, p, dx=0, dy=0, shape=None):
        for gx, gy in p.cells(dx, dy, shape):
            if gx < 0 or gx >= COLS or gy >= ROWS:
                return False
            if gy >= 0 and self.grid[gy][gx] is not None:
                return False
        return True

    def move(self, dx):
        if self.valid(self.current, dx=dx):
            self.current.x += dx
            if self.on_move: self.on_move()
            return True
        return False

    def rotate(self, direction=1):
        old = self.current.shape
        if direction == 1:
            new = [list(r) for r in zip(*old[::-1])]
        else:
            new = [list(r) for r in zip(*old)][::-1]
        for dx, dy in [(0,0),(-1,0),(1,0),(0,-1),(-2,0),(2,0),(-1,-1),(1,-1)]:
            if self.valid(self.current, dx, dy, new):
                self.current.x += dx
                self.current.y += dy
                self.current.shape = new
                if self.on_rotate: self.on_rotate()
                return True
        return False

    def soft_drop(self):
        if self.valid(self.current, dy=1):
            self.current.y += 1
            self.score += 1
            self.fall_timer = 0
            return True
        return False

    def hard_drop(self):
        d = 0
        while self.valid(self.current, dy=1):
            self.current.y += 1
            d += 1
        self.score += d * 2
        self.lock()
        return d

    def lock(self):
        self.pieces += 1
        for gx, gy in self.current.cells():
            if gy < 0:
                self.game_over = True
                if self.on_gameover: self.on_gameover()
                return
            self.grid[gy][gx] = self.current.color
            if self.current.powerup:
                self.powerup_grid[(gx, gy)] = self.current.powerup

        full = [y for y in range(ROWS) if all(c is not None for c in self.grid[y])]
        if full:
            self.lines += len(full)
            self.score += self.LINE_SCORE[len(full)] * self.level
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
            if self.combo > 1:
                self.score += 50 * self.combo * self.level
            
            if len(full) == 4:
                if getattr(self, 'b2b', False):
                    self.score += int(self.LINE_SCORE[4] * 0.5 * self.level)
                self.b2b = True
            else:
                self.b2b = False
            self.clearing = full
            self.clear_timer = 220.0
            if self.on_clear: self.on_clear(full, len(full))
            new_level = 1 + self.lines // 10
            if new_level > self.level:
                self.level = new_level
                if self.on_levelup: self.on_levelup(self.level)
            if self.mode == 'sprint' and self.lines >= 40:
                self.win = True
                if self.on_win: self.on_win()
        else:
            self.combo = 0

        if self.on_lock: self.on_lock()
        self.hold_used = False
        self.current = self.next
        self.next = self._spawn()
        self.fall_timer = 0
        self.lock_timer = 0
        if not self.valid(self.current):
            if self.zen:
                self.grid = [[None] * COLS for _ in range(ROWS)]
        self.powerup_grid = {}
            else:
                self.game_over = True
            if self.on_gameover: self.on_gameover()

    def _resolve_clear(self):
        kept = [row for i, row in enumerate(self.grid) if i not in self.clearing]
        while len(kept) < ROWS:
            kept.insert(0, [None] * COLS)
        self.grid = kept
        self.clearing = []

    def update(self, dt):
        if self.game_over or self.win:
            return
        if self.mode == 'sprint':
            self.elapsed_time += dt
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
        if self.mode == 'survival' and not self.win and not self.game_over:
            self.garbage_timer -= dt
            if self.garbage_timer <= 0:
                self.push_garbage()
                self.garbage_timer = 10000
        if self.clearing:
            self.clear_timer -= dt
            if self.clear_timer <= 0:
                self._resolve_clear()
            return

        self.fall_timer += dt
        speed_mod = 2.0 if self.freeze_timer > 0 else 1.0
        if self.fall_timer >= self.fall_ms() / (self.fall_speed_mult * speed_mod):
            self.fall_timer = 0
            if self.valid(self.current, dy=1):
                self.current.y += 1
            else:
                self.lock_timer += self.fall_ms()
                if self.lock_timer >= 400:
                    self.lock()
                    self.lock_timer = 0

    def hold_piece(self):
        if self.hold_used:
            return False
        if self.hold is None:
            self.hold = self.current.kind
            self.current = self.next
            self.next = self._spawn()
        else:
            h = self.hold
            self.hold = self.current.kind
            self.current = Piece(h)
        self.hold_used = True
        return True


    def push_garbage(self):
        # Проверяем, не забит ли верх
        if any(cell is not None for cell in self.grid[0]):
            self.game_over = True
            if self.on_gameover: self.on_gameover()
            return
        self.grid.pop(0)
        self.grid.append([(100, 100, 100)] * COLS) # Серый мусор
        self.current.y -= 1 # Сдвигаем текущую фигуру вверх
    def ghost_y(self):
        g = 0
        while self.valid(self.current, dy=g + 1):
            g += 1
        return self.current.y + g
