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

        # Звуки Тетриса — классические, синхронизированные с эффектами
        self.snd_move = self._load("assets/games/sounds/tetris/selection.wav", 0.3)
        self.snd_rotate = self._load("assets/games/sounds/tetris/selection.wav", 0.25)
        self.snd_lock = self._load("assets/games/sounds/tetris/fall.wav", 0.5)
        self.snd_clear = self._load("assets/games/sounds/tetris/line.wav", 0.7)
        self.snd_tetris = self._load("assets/games/sounds/tetris/line_clear.wav", 0.9)
        self.snd_levelup = self._load("assets/games/sounds/tetris/selection.wav", 0.6)
        self.snd_over = self._load("assets/games/sounds/tetris/gameover.wav", 0.8)

        # Эффекты
        self.particles = []            # разлетающиеся частицы
        self.clearing_rows = []        # ряды в процессе очистки
        self.clearing_timer = 0.0
        self.clearing_duration = 0.5
        self.score_pending = 0
        self.pending_spawn = False
        self.shake = 0.0               # сила тряски
        self.shake_duration = 0.0
        self.flash_screen = 0.0        # вспышка всего экрана

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
        self.fall_speed = 0.8
        # Сброс эффектов
        self.particles = []
        self.clearing_rows = []
        self.clearing_timer = 0.0
        self.score_pending = 0
        self.pending_spawn = False
        self.shake = 0.0
        self.shake_duration = 0.0
        self.flash_screen = 0.0
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
        """Создаёт новую фигуру в верхней части поля."""
        if not self.bag:
            self._refill_bag()
        self.current_key = self.next_piece
        self.next_piece = self.bag.pop(0)
        self.current = [row[:] for row in PIECES[self.current_key]]

        # Центрируем по РЕАЛЬНОЙ ширине фигуры (не по ширине матрицы)
        # Находим реальные границы непустых клеток
        min_x, max_x = 99, -1
        for row in self.current:
            for x, cell in enumerate(row):
                if cell:
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
        if max_x < 0:  # пустая (не должно случаться)
            min_x, max_x = 0, 0
        real_width = max_x - min_x + 1

        # Ставим так, чтобы центр реальной фигуры был в центре поля
        self.cx = (COLS - real_width) // 2 - min_x
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
        """Фиксирует фигуру и запускает анимацию очистки (или сразу спавнит)."""
        # Кладём фигуру в grid
        for y, row in enumerate(self.current):
            for x, cell in enumerate(row):
                if cell:
                    gy, gx = self.cy + y, self.cx + x
                    if 0 <= gy < ROWS and 0 <= gx < COLS:
                        self.grid[gy][gx] = self.current_key

        # Ищем полные ряды
        full_rows = []
        for y in range(ROWS):
            if all(self.grid[y][x] for x in range(COLS)):
                full_rows.append(y)

        if full_rows:
            # ЗАПУСКАЕМ АНИМАЦИЮ очистки
            self.clearing_rows = full_rows
            self.clearing_timer = 0.0
            self.score_pending = {1: 100, 2: 300, 3: 500, 4: 800}.get(len(full_rows), 1000) * self.level
            self.pending_spawn = True

            # Генерируем частицы из каждой клетки полных рядов
            for y in full_rows:
                for x in range(COLS):
                    if self.grid[y][x]:
                        color = PIECE_COLORS[self.grid[y][x]]
                        self._spawn_particles(x, y, color, count=5)

            # Тряска и вспышка
            self.shake = 4 + len(full_rows) * 2       # 6-12 пикселей
            self.shake_duration = 0.35
            if len(full_rows) >= 4:
                self.flash_screen = 0.25              # большая вспышка при тетрисе

            # Звук синхронизирован с анимацией: играем сразу при старте очистки
            if len(full_rows) >= 4 and self.snd_tetris:
                self.snd_tetris.play()
            elif self.snd_clear:
                self.snd_clear.play()
        else:
            # Ничего не удаляем — сразу спавним новую фигуру
            if self.snd_lock:
                self.snd_lock.play()
            self._spawn()

    def _spawn_particles(self, cell_x, cell_y, color, count=4):
        """Создаёт частицы из клетки игрового поля."""
        field_x, field_y = 15, 20
        px = field_x + cell_x * CELL + CELL // 2
        py = field_y + cell_y * CELL + CELL // 2
        for _ in range(count):
            self.particles.append({
                "x": float(px),
                "y": float(py),
                "vx": random.uniform(-350, 350),
                "vy": random.uniform(-500, -150),
                "life": 0.9,
                "max_life": 0.9,
                "color": color,
                "size": random.randint(3, 6),
            })

    def _update_particles(self, dt):
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 1200 * dt   # гравитация
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _finish_clearing(self):
        """Реально удаляет ряды и применяет очки."""
        # Удаляем ряды
        for y in sorted(self.clearing_rows, reverse=True):
            del self.grid[y]
            self.grid.insert(0, [None] * COLS)

        # Очки
        cleared = len(self.clearing_rows)
        self.lines += cleared
        self.score += self.score_pending
        new_level = self.lines // 10 + 1
        if new_level > self.level:
            self.level = new_level
            self.fall_speed = max(0.1, 0.8 - (self.level - 1) * 0.07)
            if self.snd_levelup:
                self.snd_levelup.play()

        # Сброс состояния
        self.clearing_rows = []
        self.clearing_timer = 0.0
        self.score_pending = 0

        # Спавним следующую фигуру (если ждали)
        if self.pending_spawn:
            self.pending_spawn = False
            self._spawn()

    def _draw_particles(self, scr):
        for p in self.particles:
            a = int(255 * (p["life"] / p["max_life"]))
            if a <= 0:
                continue
            s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            s.fill((*p["color"], a))
            scr.blit(s, (int(p["x"]), int(p["y"])))


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
        """Поворот на 90° с wall-kicks (5 попыток смещения)."""
        rotated = [list(row) for row in zip(*self.current[::-1])]
        # Классические wall kicks: (dx, dy) — сначала без сдвига, потом в стороны
        kicks = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1), (-1, -1), (1, -1)]
        for dx, dy in kicks:
            if self._valid(rotated, self.cx + dx, self.cy + dy):
                self.current = rotated
                self.cx += dx
                self.cy += dy
                if self.snd_rotate:
                    self.snd_rotate.play()
                return


    def _move(self, dx, dy):
        """Двигает фигуру. _valid сам проверяет границы по РЕАЛЬНЫМ клеткам."""
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
        # Звук «удара» — синхронизирован с фиксацией
        if self.snd_lock:
            self.snd_lock.play()
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
        # Таймеры эффектов работают даже на паузе
        if self.shake_duration > 0:
            self.shake_duration -= dt
            if self.shake_duration <= 0:
                self.shake = 0
        if self.flash_screen > 0:
            self.flash_screen = max(0.0, self.flash_screen - dt)

        self._update_particles(dt)

        if self.game_over or self.paused:
            return

        # Анимация очистки линий — пауза для игровой логики
        if self.clearing_rows:
            self.clearing_timer += dt
            if self.clearing_timer >= self.clearing_duration:
                self._finish_clearing()
            return

        # Обычная логика — падение фигуры
        self.fall_timer += dt
        if self.fall_timer >= self.fall_speed:
            self.fall_timer = 0
            if not self._move(0, 1):
                self._lock()


    def _draw_cell(self, scr, px, py, color, alpha=255, ghost=False):
        """Рисует клетку по АБСОЛЮТНЫМ пиксельным координатам (px, py)."""
        if ghost:
            s = pygame.Surface((CELL - 2, CELL - 2), pygame.SRCALPHA)
            pygame.draw.rect(s, (*color, 60), (0, 0, CELL - 2, CELL - 2), border_radius=4)
            pygame.draw.rect(s, (*color, 180), (0, 0, CELL - 2, CELL - 2), 2, border_radius=4)
            scr.blit(s, (px + 1, py + 1))
            return
        pygame.draw.rect(scr, color, (px + 1, py + 1, CELL - 2, CELL - 2), border_radius=4)
        lighter = tuple(min(255, c + 50) for c in color)
        pygame.draw.line(scr, lighter, (px + 4, py + 3), (px + CELL - 4, py + 3), 2)
        darker = tuple(max(0, c - 60) for c in color)
        pygame.draw.line(scr, darker, (px + 4, py + CELL - 3), (px + CELL - 4, py + CELL - 3), 2)


    def _draw(self):
        self.screen.fill(C_BG)

        # Offset для тряски
        shake_x = shake_y = 0
        if self.shake_duration > 0:
            shake_x = random.randint(-int(self.shake), int(self.shake))
            shake_y = random.randint(-int(self.shake), int(self.shake))

        # Игровое поле (со сдвигом от тряски)
        field = pygame.Rect(15 + shake_x, 20 + shake_y, PLAY_W, PLAY_H)
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
                # Пропускаем ряды, которые сейчас в анимации
                if self.clearing_rows and y in self.clearing_rows:
                    continue
                if self.grid[y][x]:
                    color = PIECE_COLORS[self.grid[y][x]]
                    self._draw_cell(self.screen,
                                    field.x + x * CELL, field.y + y * CELL,
                                    color)

        # === АНИМАЦИЯ ОЧИСТКИ ===
        if self.clearing_rows:
            progress = self.clearing_timer / self.clearing_duration
            for y in self.clearing_rows:
                for x in range(COLS):
                    px = field.x + x * CELL
                    py = field.y + y * CELL
                    value = self.grid[y][x]
                    if not value:
                        continue
                    color = PIECE_COLORS[value]

                    # Первая половина — вспышка белым
                    if progress < 0.5:
                        t = progress / 0.5
                        white_alpha = int(255 * (1 - abs(t - 0.5) * 2))
                        # Вспышка поверх цветного блока
                        self._draw_cell(self.screen, px, py, color)
                        flash = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                        flash.fill((255, 255, 255, white_alpha))
                        self.screen.blit(flash, (px, py))
                    else:
                        # Вторая половина — сжатие и исчезновение
                        t = (progress - 0.5) / 0.5
                        size = int(CELL * (1 - t))
                        alpha = int(255 * (1 - t))
                        offset = (CELL - size) // 2
                        s = pygame.Surface((size, size), pygame.SRCALPHA)
                        pygame.draw.rect(s, (*color, alpha), (0, 0, size, size), border_radius=4)
                        self.screen.blit(s, (px + offset, py + offset))

        # Призрак
        if not self.game_over and not self.clearing_rows:
            gy = self._ghost_y()
            ghost_color = PIECE_COLORS[self.current_key]
            for y, row in enumerate(self.current):
                for x, cell in enumerate(row):
                    if cell:
                        self._draw_cell(self.screen,
                                        field.x + (self.cx + x) * CELL,
                                        field.y + (gy + y) * CELL,
                                        ghost_color, ghost=True)

        # Текущая фигура
        if not self.game_over and not self.clearing_rows:
            color = PIECE_COLORS[self.current_key]
            for y, row in enumerate(self.current):
                for x, cell in enumerate(row):
                    if cell:
                        self._draw_cell(self.screen,
                                        field.x + (self.cx + x) * CELL,
                                        field.y + (self.cy + y) * CELL,
                                        color)

        # Частицы
        self._draw_particles(self.screen)

        # Рамка поля
        pygame.draw.rect(self.screen, C_BORDER, field, 2, border_radius=4)

        # === Сайдбар (БЕЗ тряски) ===
        sx = 30 + PLAY_W
        sy = 20

        self._sidebar_text("СЧЁТ", f"{self.score}", sx, sy)
        self._sidebar_text("ЛИНИИ", f"{self.lines}", sx, sy + 60)
        self._sidebar_text("УРОВЕНЬ", f"{self.level}", sx, sy + 120)

        next_y = sy + 200
        label = self.font_small.render("СЛЕДУЮЩАЯ", True, C_TEXT_DIM)
        self.screen.blit(label, (sx, next_y))

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

        controls_y = next_y + 140
        controls = [
            ("< >", "движение"),
            ("^", "поворот"),
            ("v", "ускорить"),
            ("H", "сброс вниз"),
            ("P", "пауза"),
            ("Esc", "выход"),
        ]
        for i, (key, desc) in enumerate(controls):
            kt = self.font_small.render(key, True, C_TEXT)
            dt = self.font_small.render(desc, True, C_TEXT_DIM)
            self.screen.blit(kt, (sx, controls_y + i * 20))
            self.screen.blit(dt, (sx + 55, controls_y + i * 20))

        # Вспышка всего экрана (при тетрисе — 4 линии)
        if self.flash_screen > 0:
            a = int(255 * (self.flash_screen / 0.25) * 0.5)
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, a))
            self.screen.blit(flash, (0, 0))

        if self.paused:
            self._overlay("ПАУЗА", "P — продолжить")

        if self.game_over:
            self._overlay("ИГРА ОКОНЧЕНА", f"Счёт: {self.score}",
                          "Enter — заново, Esc — выход")


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
