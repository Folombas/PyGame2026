"""Тетрис — классика в тёмном стиле BunnyOS."""
import pygame
import random
import sys


# === НАСТРОЙКИ ===
CELL = 28
COLS, ROWS = 10, 20
PLAY_W, PLAY_H = COLS * CELL, ROWS * CELL
SIDE_W = 180
WIDTH = PLAY_W + SIDE_W + 30
HEIGHT = PLAY_H + 40
FPS = 60

# === ЦВЕТА ===
C_BG       = (18, 22, 32)
C_PLAY_BG  = (10, 12, 20)
C_GRID     = (30, 36, 50)
C_BORDER   = (60, 80, 120)
C_TEXT     = (220, 230, 245)
C_TEXT_DIM = (120, 140, 170)
C_SHADOW   = (40, 50, 70)

# Фигуры (I, O, T, S, Z, J, L) — 4x4 матрицы
PIECES = {
    "I": [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    "O": [[1,1],[1,1]],
    "T": [[0,1,0],[1,1,1],[0,0,0]],
    "S": [[0,1,1],[1,1,0],[0,0,0]],
    "Z": [[1,1,0],[0,1,1],[0,0,0]],
    "J": [[1,0,0],[1,1,1],[0,0,0]],
    "L": [[0,0,1],[1,1,1],[0,0,0]],
}

PIECE_COLORS = {
    "I": (80, 220, 240),
    "O": (250, 220, 80),
    "T": (190, 100, 240),
    "S": (100, 230, 120),
    "Z": (240, 90, 110),
    "J": (80, 130, 250),
    "L": (250, 160, 60),
}


class TetrisGame:
    def __init__(self, screen=None):
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Тетрис — BunnyOS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.font_big = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 18)

        # Звуки (пытаемся загрузить, иначе None)
        self.snd_move = self._load("assets/games/sounds/crunch.wav", 0.2)
        self.snd_drop = self._load("assets/games/sounds/crunch.wav", 0.4)
        self.snd_clear = self._load("assets/games/sounds/music.mp3", 0.4)
        self.snd_over = self._load("assets/games/sounds/crash.mp3", 0.6)

        self.reset()

    def _load(self, path, vol=0.5):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(vol)
            return s
        except Exception:
            return None

    def reset(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.fall_timer = 0.0
        self.fall_speed = 0.8  # секунд на клетку
        # ВАЖНО: bag и next_piece инициализируем ДО _spawn()
        self.bag = []
        self._refill_bag()
        self.next_piece = self.bag.pop(0)
        self._spawn()

    def _refill_bag(self):
        """7-bag randomizer — все фигуры выпадают равномерно."""
        bag = list(PIECES.keys())
        random.shuffle(bag)
        self.bag = bag

    def _spawn(self):
        if not self.bag:
            self._refill_bag()
        self.current_key = self.next_piece
        self.next_piece = self.bag.pop(0)
        self.current = [row[:] for row in PIECES[self.current_key]]
        self.cx = COLS // 2 - len(self.current[0]) // 2
        self.cy = 0
        if not self._valid(self.current, self.cx, self.cy):
            self.game_over = True
            if self.snd_over:
                self.snd_over.play()

    def _valid(self, piece, px, py):
        for y, row in enumerate(piece):
            for x, cell in enumerate(row):
                if not cell:
                    continue
                nx, ny = px + x, py + y
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return False
                if ny >= 0 and self.grid[ny][nx]:
                    return False
        return True

    def _lock(self):
        for y, row in enumerate(self.current):
            for x, cell in enumerate(row):
                if cell:
                    gy, gx = self.cy + y, self.cx + x
                    if 0 <= gy < ROWS and 0 <= gx < COLS:
                        self.grid[gy][gx] = self.current_key
        # Проверяем линии
        cleared = self._clear_lines()
        if cleared > 0:
            self.lines += cleared
            # Очки: 1 линия = 100, 2 = 300, 3 = 500, 4 = 800
            points = {1: 100, 2: 300, 3: 500, 4: 800}.get(cleared, 1000)
            self.score += points * self.level
            # Уровень каждые 10 линий
            new_level = self.lines // 10 + 1
            if new_level > self.level:
                self.level = new_level
                self.fall_speed = max(0.1, 0.8 - (self.level - 1) * 0.07)
            if self.snd_clear:
                self.snd_clear.play()
        self._spawn()

    def _clear_lines(self):
        """Удаляет полные ряды и возвращает их количество."""
        # Шаг 1: находим ВСЕ полные ряды явным циклом
        full_rows = []
        for y in range(ROWS):
            is_full = True
            for x in range(COLS):
                if not self.grid[y][x]:
                    is_full = False
                    break
            if is_full:
                full_rows.append(y)

        if not full_rows:
            return 0

        # Отладка — видим в консоли сколько строк удаляется
        print(f"[tetris] 🧹 Удалено рядов: {len(full_rows)} ({full_rows})")

        # Шаг 2: собираем новый grid БЕЗ полных рядов (сверху вниз)
        new_grid = []
        for y in range(ROWS):
            if y not in full_rows:
                new_grid.append(self.grid[y])

        # Шаг 3: добавляем пустые ряды СВЕРХУ, чтобы длина стала ROWS
        while len(new_grid) < ROWS:
            new_grid.insert(0, [None] * COLS)

        # Шаг 4: заменяем grid целиком
        self.grid = new_grid
        return len(full_rows)


    def _rotate(self):
        # Транспонирование + reverse строк = поворот на 90°
        rotated = [list(row) for row in zip(*self.current[::-1])]
        for dx in (0, -1, 1, -2, 2):  # wall kicks
            if self._valid(rotated, self.cx + dx, self.cy):
                self.current = rotated
                self.cx += dx
                if self.snd_move:
                    self.snd_move.play()
                return

    def _move(self, dx, dy):
        if self._valid(self.current, self.cx + dx, self.cy + dy):
            self.cx += dx
            self.cy += dy
            if self.snd_move and dx != 0:
                self.snd_move.play()
            return True
        return False

    def _hard_drop(self):
        while self._valid(self.current, self.cx, self.cy + 1):
            self.cy += 1
            self.score += 2  # бонус за hard drop
        if self.snd_drop:
            self.snd_drop.play()
        self._lock()

    def _ghost_y(self):
        """Куда упадёт фигура — для отрисовки призрака."""
        y = self.cy
        while self._valid(self.current, self.cx, y + 1):
            y += 1
        return y

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key == pygame.K_p or e.key == pygame.K_SPACE:
                    if not self.game_over:
                        self.paused = not self.paused
                    return True
                if self.game_over:
                    if e.key == pygame.K_RETURN:
                        self.reset()
                    return True
                if self.paused:
                    return True
                # Управление
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self._move(-1, 0)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self._move(1, 0)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    if self._move(0, 1):
                        self.fall_timer = 0
                        self.score += 1
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self._rotate()
                elif e.key == pygame.K_SPACE:
                    pass
                elif e.key == pygame.K_h:
                    self._hard_drop()
        return True

    def _update(self, dt):
        if self.game_over or self.paused:
            return
        self.fall_timer += dt
        if self.fall_timer >= self.fall_speed:
            self.fall_timer = 0
            if not self._move(0, 1):
                self._lock()

    def _draw_cell(self, scr, x, y, color, alpha=255, ghost=False):
        px = x * CELL
        py = y * CELL
        if ghost:
            s = pygame.Surface((CELL - 2, CELL - 2), pygame.SRCALPHA)
            pygame.draw.rect(s, (*color, 60), (0, 0, CELL - 2, CELL - 2), border_radius=4)
            pygame.draw.rect(s, (*color, 180), (0, 0, CELL - 2, CELL - 2), 2, border_radius=4)
            scr.blit(s, (px + 1, py + 1))
            return
        # Основа
        pygame.draw.rect(scr, color, (px + 1, py + 1, CELL - 2, CELL - 2), border_radius=4)
        # Верхний блик
        lighter = tuple(min(255, c + 50) for c in color)
        pygame.draw.line(scr, lighter, (px + 4, py + 3), (px + CELL - 4, py + 3), 2)
        # Нижняя тень
        darker = tuple(max(0, c - 60) for c in color)
        pygame.draw.line(scr, darker, (px + 4, py + CELL - 3), (px + CELL - 4, py + CELL - 3), 2)

    def _draw(self):
        self.screen.fill(C_BG)

        # Игровое поле
        field = pygame.Rect(15, 20, PLAY_W, PLAY_H)
        pygame.draw.rect(self.screen, C_PLAY_BG, field)

        # Сетка
        for x in range(1, COLS):
            pygame.draw.line(self.screen, C_GRID,
                             (field.x + x * CELL, field.y),
                             (field.x + x * CELL, field.bottom), 1)
        for y in range(1, ROWS):
            pygame.draw.line(self.screen, C_GRID,
                             (field.x, field.y + y * CELL),
                             (field.right, field.y + y * CELL), 1)

        # Зафиксированные блоки
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x]:
                    color = PIECE_COLORS[self.grid[y][x]]
                    self._draw_cell(self.screen,
                                    field.x // CELL + x, field.y // CELL + y,
                                    color)

        # Призрак (куда упадёт)
        if not self.game_over:
            gy = self._ghost_y()
            ghost_color = PIECE_COLORS[self.current_key]
            for y, row in enumerate(self.current):
                for x, cell in enumerate(row):
                    if cell:
                        self._draw_cell(self.screen,
                                        field.x // CELL + self.cx + x,
                                        field.y // CELL + gy + y,
                                        ghost_color, ghost=True)

        # Текущая фигура
        if not self.game_over:
            color = PIECE_COLORS[self.current_key]
            for y, row in enumerate(self.current):
                for x, cell in enumerate(row):
                    if cell:
                        self._draw_cell(self.screen,
                                        field.x // CELL + self.cx + x,
                                        field.y // CELL + self.cy + y,
                                        color)

        # Рамка поля
        pygame.draw.rect(self.screen, C_BORDER, field, 2, border_radius=4)

        # === Сайдбар ===
        sx = 30 + PLAY_W
        sy = 20

        # Счёт
        self._sidebar_text("СЧЁТ", f"{self.score}", sx, sy)
        self._sidebar_text("ЛИНИИ", f"{self.lines}", sx, sy + 60)
        self._sidebar_text("УРОВЕНЬ", f"{self.level}", sx, sy + 120)

        # Следующая фигура
        next_y = sy + 200
        label = self.font_small.render("СЛЕДУЮЩАЯ", True, C_TEXT_DIM)
        self.screen.blit(label, (sx, next_y))

        # Отрисовка next в маленьком квадрате
        box = pygame.Rect(sx, next_y + 22, SIDE_W - 30, 90)
        pygame.draw.rect(self.screen, C_PLAY_BG, box)
        pygame.draw.rect(self.screen, C_GRID, box, 1, border_radius=4)

        next_piece = PIECES[self.next_piece]
        color = PIECE_COLORS[self.next_piece]
        mini = 22
        pw = len(next_piece[0]) * mini
        ph = len(next_piece) * mini
        ox = box.x + (box.w - pw) // 2
        oy = box.y + (box.h - ph) // 2
        for y, row in enumerate(next_piece):
            for x, cell in enumerate(row):
                if cell:
                    px = ox + x * mini
                    py = oy + y * mini
                    pygame.draw.rect(self.screen, color,
                                     (px + 1, py + 1, mini - 2, mini - 2),
                                     border_radius=3)
                    lighter = tuple(min(255, c + 50) for c in color)
                    pygame.draw.line(self.screen, lighter,
                                     (px + 3, py + 3), (px + mini - 3, py + 3), 1)

        # Управление
        controls_y = next_y + 140
        controls = [
            ("← →", "движение"),
            ("↑", "поворот"),
            ("↓", "ускорить"),
            ("H", "сброс вниз"),
            ("P", "пауза"),
            ("Esc", "выход"),
        ]
        for i, (key, desc) in enumerate(controls):
            kt = self.font_small.render(key, True, C_TEXT)
            dt = self.font_small.render(desc, True, C_TEXT_DIM)
            self.screen.blit(kt, (sx, controls_y + i * 20))
            self.screen.blit(dt, (sx + 55, controls_y + i * 20))

        # Пауза
        if self.paused:
            self._overlay("ПАУЗА", "P — продолжить")

        # Конец игры
        if self.game_over:
            self._overlay("ИГРА ОКОНЧЕНА", f"Счёт: {self.score}", "Enter — заново, Esc — выход")

    def _sidebar_text(self, label, value, x, y):
        lt = self.font_small.render(label, True, C_TEXT_DIM)
        vt = self.font.render(value, True, C_TEXT)
        self.screen.blit(lt, (x, y))
        self.screen.blit(vt, (x, y + 18))

    def _overlay(self, title, *subs):
        # Затемнение
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))
        # Заголовок
        tt = self.font_big.render(title, True, C_TEXT)
        self.screen.blit(tt, (WIDTH // 2 - tt.get_width() // 2, HEIGHT // 2 - 60))
        # Подписи
        for i, s in enumerate(subs):
            st = self.font.render(s, True, C_TEXT_DIM)
            self.screen.blit(st, (WIDTH // 2 - st.get_width() // 2, HEIGHT // 2 + 10 + i * 30))

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
    game = TetrisGame()
    game.run()
    pygame.quit()
    sys.exit(0)
