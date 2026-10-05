"""Радиоприёмник: объект в комнате + симулятор с крутилками."""
import math
import os
import pygame
from settings import WIDTH, HEIGHT


# ==================== СТАНЦИИ ПО ДИАПАЗОНАМ ====================
# (частота, название, файл-звук, громкость)
BANDS = [
    {
        "name": "FM",
        "unit": "MHz",
        "min": 87.5, "max": 108.0,
        "step": 0.1,
        "stations": [
            (91.5,  "Carrot FM",     "station_magic.wav",   0.35),
            (98.7,  "Bunny News",    "station_birds.wav",   0.30),
            (104.2, "Neon Wave",     "station_strange.wav", 0.35),
        ],
    },
    {
        "name": "УКВ",
        "unit": "MHz",
        "min": 65.0, "max": 74.0,
        "step": 0.1,
        "stations": [
            (66.8, "Радио Маяк",     "station_rain.wav",  0.35),
            (70.5, "Классика",       "station_river.wav", 0.40),
        ],
    },
    {
        "name": "SW",
        "unit": "MHz",
        "min": 6.0, "max": 18.0,
        "step": 0.1,
        "stations": [
            (9.5,  "Voice of Bunny", "station_river.wav",  0.35),
            (12.3, "Pirate Radio",   "station_storm.wav",  0.40),
            (16.7, "Bunny Jazz",     "station_dog.wav",    0.35),
        ],
    },
    {
        "name": "MW",
        "unit": "kHz",
        "min": 520.0, "max": 1610.0,
        "step": 10.0,
        "stations": [
            (700,  "Old Timer",      "station_storm.wav",  0.40),
            (1200, "Sport",          "station_birds.wav",  0.35),
        ],
    },
]


# ==================== ОБЪЕКТ ПРИЁМНИКА В КОМНАТЕ ====================
class Radio:
    """Стоит на тумбочке в комнате."""
    def __init__(self, x, y):
        # x, y — координаты левого-нижнего угла (на тумбочке)
        self.rect = pygame.Rect(x - 26, y - 26, 52, 26)
        self.tx = x
        self.ty = y
        self.pulse = 0.0

    def interact_rect(self):
        """Зона взаимодействия (рядом с приёмником)."""
        return self.rect.inflate(80, 80)

    def update(self):
        self.pulse += 0.06

    def draw(self, surface, offset_x, offset_y):
        x = self.tx - offset_x - 26
        y = self.ty - offset_y - 26
        w, h = 52, 26

        # Тень
        pygame.draw.ellipse(surface, (0, 0, 0, 60),
                            (x + 2, y + h - 3, w - 4, 6))

        # Корпус — дерево
        pygame.draw.rect(surface, (120, 80, 50), (x, y, w, h), border_radius=3)
        pygame.draw.rect(surface, (60, 40, 25), (x, y, w, h), 2, border_radius=3)
        # Верхняя светлая полоса
        pygame.draw.rect(surface, (160, 110, 70), (x + 1, y + 1, w - 2, 4))

        # Динамик — кружки-сетка слева
        for gy in range(3):
            for gx in range(3):
                gcx = x + 8 + gx * 5
                gcy = y + 8 + gy * 5
                pygame.draw.circle(surface, (60, 40, 25), (gcx, gcy), 2)

        # Крутилка справа
        cx = x + w - 12
        cy = y + h // 2
        pygame.draw.circle(surface, (60, 40, 25), (cx, cy), 7)
        pygame.draw.circle(surface, (220, 200, 170), (cx, cy), 6)
        pygame.draw.circle(surface, (80, 60, 40), (cx, cy), 6, 1)
        # риска
        pygame.draw.line(surface, (60, 40, 25),
                         (cx, cy), (cx + 4, cy - 3), 1)

        # Индикатор (пульсирующий)
        light = (240, 60, 60) if int(self.pulse * 2) % 2 else (150, 30, 30)
        pygame.draw.circle(surface, light, (x + 6, y + h - 6), 2)

        # Подсказка "E" когда рядом
        # (рисуется отдельно в main)


# ==================== UI РАДИО ====================
class RadioUI:
    """Полноэкранный интерфейс радиоприёмника."""
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.open = False
        self.band_idx = 0
        self.frequency = 98.7
        self.volume = 0.5
        self.on = True
        self.tick = 0
        self.current_station = None
        self.current_sound = None
        self.target_volume = 0.5
        # Кеш звуков
        self._sounds = {}
        # Анимация крутилки
        self.knob_angle = 0.0

    # ---------- СИСТЕМА ----------
    @property
    def band(self):
        return BANDS[self.band_idx]

    def _load_sound(self, filename):
        if filename in self._sounds:
            return self._sounds[filename]
        path = os.path.join(os.path.dirname(__file__), "assets", "radio", filename)
        if not os.path.exists(path):
            self._sounds[filename] = None
            return None
        try:
            snd = pygame.mixer.Sound(path)
            self._sounds[filename] = snd
            return snd
        except pygame.error as e:
            print(f"[radio] не загрузил {filename}: {e}")
            self._sounds[filename] = None
            return None

    def _stop_current(self):
        if self.current_sound:
            self.current_sound.stop()
        self.current_sound = None
        self.current_station = None

    def _tune(self):
        """Проверяет, есть ли станция на текущей частоте."""
        self._stop_current()
        if not self.on:
            return
        # Ищем ближайшую станцию
        best = None
        best_dist = 999
        for freq, name, snd_file, vol in self.band["stations"]:
            d = abs(freq - self.frequency)
            if d < best_dist:
                best_dist = d
                best = (freq, name, snd_file, vol)
        # Порог захвата — 0.8 от шага или 1.5% диапазона
        threshold = max(self.band["step"] * 2, (self.band["max"] - self.band["min"]) * 0.015)
        if best and best_dist <= threshold:
            snd = self._load_sound(best[2])
            if snd:
                snd.set_volume(self.volume * best[3])
                snd.play(-1)  # цикл
                self.current_sound = snd
                self.current_station = (best[0], best[1])

    def handle_event(self, event):
        if not self.open:
            return
        if event.type != pygame.KEYDOWN:
            return
        b = self.band
        step = b["step"]
        if event.key == pygame.K_ESCAPE:
            self.close()
        elif event.key == pygame.K_SPACE:
            self.on = not self.on
            self._tune()
        elif event.key in (pygame.K_TAB, pygame.K_b):
            self.band_idx = (self.band_idx + 1) % len(BANDS)
            self.frequency = (b["min"] + b["max"]) / 2  # сброс на середину
            self._tune()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.frequency -= step
            self.frequency = max(b["min"], self.frequency)
            self.knob_angle -= 0.15
            self._tune()
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.frequency += step
            self.frequency = min(b["max"], self.frequency)
            self.knob_angle += 0.15
            self._tune()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.volume = min(1.0, self.volume + 0.05)
            if self.current_sound:
                self.current_sound.set_volume(self.volume)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.volume = max(0.0, self.volume - 0.05)
            if self.current_sound:
                self.current_sound.set_volume(self.volume)

    def update(self, dt):
        self.tick += 1
        self.knob_angle *= 0.92  # плавное возвращение

    def open_ui(self):
        self.open = True
        self.on = True
        self.frequency = 98.7
        self.band_idx = 0
        self._tune()

    def close(self):
        self.open = False
        self._stop_current()

    # ---------- ОТРИСОВКА ----------
    def draw(self, screen):
        # Фон — деревянный градиент
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(80 + 40 * t)
            g = int(55 + 25 * t)
            b = int(35 + 20 * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # Общая деревянная рамка
        frame = pygame.Rect(40, 40, WIDTH - 80, HEIGHT - 80)
        pygame.draw.rect(screen, (50, 30, 20), frame, border_radius=20)
        inner = frame.inflate(-12, -12)
        pygame.draw.rect(screen, (120, 80, 50), inner, border_radius=15)
        # вертикальные полосы-текстура
        for i in range(0, inner.w, 8):
            col = (105, 70, 45) if (i // 8) % 2 == 0 else (125, 85, 55)
            pygame.draw.line(screen, col,
                             (inner.x + i, inner.y + 8),
                             (inner.x + i, inner.bottom - 8), 1)

        # === ЗАГОЛОВОК ===
        title = self.font_big.render("📻  BunnyRadio  ·  Model 1975", True, (240, 220, 180))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

        # === ДИНАМИК (слева) ===
        sp = pygame.Rect(80, 130, 320, 260)
        pygame.draw.rect(screen, (40, 25, 15), sp, border_radius=10)
        pygame.draw.rect(screen, (70, 45, 30), sp, 3, border_radius=10)
        # сетка-гриль
        for gy in range(sp.y + 12, sp.bottom - 8, 10):
            pygame.draw.line(screen, (60, 40, 25),
                             (sp.x + 10, gy), (sp.right - 10, gy), 2)

        # === ШКАЛА ЧАСТОТ (сверху справа) ===
        scale_x = 440
        scale_y = 140
        scale_w = 480
        scale_h = 50
        pygame.draw.rect(screen, (240, 230, 200),
                         (scale_x, scale_y, scale_w, scale_h), border_radius=6)
        pygame.draw.rect(screen, (60, 40, 25),
                         (scale_x, scale_y, scale_w, scale_h), 2, border_radius=6)

        b = self.band
        span = b["max"] - b["min"]
        # деления
        n_ticks = 11
        for i in range(n_ticks):
            tx = scale_x + 12 + i * (scale_w - 24) / (n_ticks - 1)
            freq_at = b["min"] + span * (i / (n_ticks - 1))
            pygame.draw.line(screen, (60, 40, 25),
                             (tx, scale_y + 5), (tx, scale_y + 15), 1)
            label = f"{freq_at:.0f}" if span > 100 else f"{freq_at:.1f}"
            t = self.font_small.render(label, True, (80, 50, 30))
            screen.blit(t, (tx - t.get_width() // 2, scale_y + 30))

        # указатель-стрелка
        pos_ratio = (self.frequency - b["min"]) / span
        ptr_x = scale_x + 12 + pos_ratio * (scale_w - 24)
        pygame.draw.polygon(screen, (220, 40, 40), [
            (ptr_x, scale_y - 4),
            (ptr_x - 7, scale_y - 18),
            (ptr_x + 7, scale_y - 18),
        ])
        pygame.draw.line(screen, (220, 40, 40),
                         (ptr_x, scale_y - 18), (ptr_x, scale_y + 18), 2)

        # метки станций на шкале
        for freq, name, _, _ in b["stations"]:
            if b["min"] <= freq <= b["max"]:
                r_ = (freq - b["min"]) / span
                mx = scale_x + 12 + r_ * (scale_w - 24)
                pygame.draw.circle(screen, (60, 200, 100), (int(mx), scale_y + 20), 3)

        # === ИНФО ЭКРАН ===
        info = pygame.Rect(440, 210, 480, 180)
        pygame.draw.rect(screen, (20, 30, 20), info, border_radius=8)
        pygame.draw.rect(screen, (60, 40, 25), info, 3, border_radius=8)

        # частота крупно
        freq_txt = f"{self.frequency:.1f} {b['unit']}"
        ft = self.font_big.render(freq_txt, True, (100, 240, 130))
        screen.blit(ft, (info.centerx - ft.get_width() // 2, info.y + 20))

        # станция
        if self.current_station:
            st_text = f"▶ {self.current_station[1]}"
            st = self.font_small.render(st_text, True, (100, 240, 130))
            screen.blit(st, (info.centerx - st.get_width() // 2, info.y + 70))
            # полоска сигнала
            sig = pygame.Rect(info.x + 20, info.y + 110, info.w - 40, 14)
            pygame.draw.rect(screen, (30, 60, 30), sig)
            # Определяем силу сигнала
            band = self.band
            best_d = min(abs(s[0] - self.frequency) for s in band["stations"])
            thresh = max(band["step"] * 2, (band["max"] - band["min"]) * 0.015)
            strength = max(0.0, 1.0 - best_d / thresh)
            fill = int(sig.w * strength)
            if fill > 0:
                pygame.draw.rect(screen, (60, 200, 100), (sig.x, sig.y, fill, sig.h))
            s_txt = self.font_small.render("СИГНАЛ", True, (150, 200, 150))
            screen.blit(s_txt, (sig.x, sig.y - 16))
        else:
            nt = self.font_small.render("— нет сигнала —", True, (120, 100, 80))
            screen.blit(nt, (info.centerx - nt.get_width() // 2, info.y + 80))

        # === КРУТИЛКА ГРОМКОСТИ ===
        vol_cx = 380
        vol_cy = 520
        pygame.draw.circle(screen, (40, 25, 15), (vol_cx, vol_cy), 55)
        pygame.draw.circle(screen, (200, 180, 150), (vol_cx, vol_cy), 50)
        pygame.draw.circle(screen, (60, 40, 25), (vol_cx, vol_cy), 50, 2)
        # риска-указатель
        ang = -math.pi * 0.75 + self.volume * math.pi * 1.5
        ex = vol_cx + int(math.cos(ang) * 38)
        ey = vol_cy + int(math.sin(ang) * 38)
        pygame.draw.line(screen, (60, 40, 25), (vol_cx, vol_cy), (ex, ey), 4)
        pygame.draw.circle(screen, (60, 40, 25), (vol_cx, vol_cy), 6)
        # подпись
        vt = self.font_small.render(f"VOL  {int(self.volume*100)}%", True, (240, 220, 180))
        screen.blit(vt, (vol_cx - vt.get_width() // 2, vol_cy + 65))

        # === КРУТИЛКА ЧАСТОТЫ ===
        tun_cx = 700
        tun_cy = 520
        pygame.draw.circle(screen, (40, 25, 15), (tun_cx, tun_cy), 70)
        pygame.draw.circle(screen, (200, 180, 150), (tun_cx, tun_cy), 64)
        pygame.draw.circle(screen, (60, 40, 25), (tun_cx, tun_cy), 64, 3)
        # рифление по краю
        for i in range(24):
            a = i * math.tau / 24
            x1 = tun_cx + int(math.cos(a) * 58)
            y1 = tun_cy + int(math.sin(a) * 58)
            x2 = tun_cx + int(math.cos(a) * 64)
            y2 = tun_cy + int(math.sin(a) * 64)
            pygame.draw.line(screen, (80, 50, 30), (x1, y1), (x2, y2), 2)
        # центральный индикатор
        pygame.draw.circle(screen, (240, 220, 180), (tun_cx, tun_cy), 26)
        pygame.draw.circle(screen, (60, 40, 25), (tun_cx, tun_cy), 26, 2)
        # стрелка
        ang2 = self.knob_angle + (self.frequency - b["min"]) / span * math.pi * 1.5 - math.pi * 0.75
        ex2 = tun_cx + int(math.cos(ang2) * 22)
        ey2 = tun_cy + int(math.sin(ang2) * 22)
        pygame.draw.line(screen, (60, 40, 25), (tun_cx, tun_cy), (ex2, ey2), 4)
        # подпись
        tt = self.font_small.render("TUNE", True, (240, 220, 180))
        screen.blit(tt, (tun_cx - tt.get_width() // 2, tun_cy + 82))

        # === КНОПКИ ДИАПАЗОНОВ ===
        btn_y = 640
        btn_start = 200
        for i, band_data in enumerate(BANDS):
            bw = 110
            bx = btn_start + i * (bw + 10)
            r_ = pygame.Rect(bx, btn_y, bw, 36)
            active = (i == self.band_idx)
            base = (200, 120, 60) if active else (160, 110, 70)
            pygame.draw.rect(screen, base, r_, border_radius=6)
            pygame.draw.rect(screen, (60, 40, 25), r_, 2, border_radius=6)
            # блик
            pygame.draw.line(screen, (240, 200, 140),
                             (r_.x + 4, r_.y + 2), (r_.right - 4, r_.y + 2), 1)
            t = self.font_small.render(band_data["name"], True, (255, 240, 210))
            screen.blit(t, (r_.centerx - t.get_width() // 2,
                            r_.centery - t.get_height() // 2))

        # === ИНДИКАТОР ВКЛ/ВЫКЛ ===
        pwr_r = pygame.Rect(720, 640, 110, 36)
        pygame.draw.rect(screen, (80, 50, 30), pwr_r, border_radius=6)
        pygame.draw.rect(screen, (60, 40, 25), pwr_r, 2, border_radius=6)
        col = (240, 60, 60) if self.on else (60, 30, 30)
        if self.on and (self.tick // 20) % 2 == 0:
            col = (255, 120, 120)
        pygame.draw.circle(screen, col, (pwr_r.x + 20, pwr_r.centery), 8)
        pygame.draw.circle(screen, (40, 20, 20), (pwr_r.x + 20, pwr_r.centery), 8, 2)
        t = self.font_small.render("POWER", True, (240, 220, 180))
        screen.blit(t, (pwr_r.x + 38, pwr_r.centery - t.get_height() // 2))

        # === ПОДСКАЗКА ВНИЗУ ===
        hint = self.font_small.render(
            "←→ — частота   ↑↓ — громкость   B — диапазон   Space — вкл/выкл   Esc — выход",
            True, (220, 200, 170))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))
