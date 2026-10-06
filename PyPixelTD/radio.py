"""Радиоприёмник: объект в комнате + симулятор с крутилками."""
import math
import os
import pygame
from settings import WIDTH, HEIGHT
from radio_player import RadioPlayer
from radio_stations import load_stations


# ==================== ДИАПАЗОНЫ ====================
# Реальные станции подтянутся при старте RadioUI из radio_stations.load_stations()
BAND_TEMPLATES = [
    {"name": "FM",  "unit": "MHz", "min": 87.5, "max": 108.0, "step": 0.1},
    {"name": "УКВ", "unit": "MHz", "min": 65.0, "max": 74.0,  "step": 0.1},
    {"name": "SW",  "unit": "MHz", "min": 6.0,  "max": 18.0,  "step": 0.1},
    {"name": "MW",  "unit": "kHz", "min": 520.0,"max": 1610.0,"step": 10.0},
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
        self.knob_angle = 0.0
        self.status = ""

        # VLC-плеер
        self.player = RadioPlayer()

        # Спрайты из паков (HiFi System + Audio Knobs + Kenney)
        self.spr = {}
        self._load_sprites()

        # Звуки интерфейса (через pygame.mixer, не через VLC)
        self.snd_dial = self._load_ui_sound("dial_click.wav")
        self.snd_band = self._load_ui_sound("band_switch.wav")
        self.snd_power = self._load_ui_sound("power_click.wav")
        self.snd_noise = self._load_ui_sound("search_noise.wav")
        if self.snd_noise:
            self.snd_noise.set_volume(0.15)

        # Таймер для треска крутилки (чтоб не спамить каждый пиксель)
        self._dial_sound_cooldown = 0
        self._noise_channel = None

        # Загружаем станции и строим BANDS
        self.bands = self._build_bands()

    def _build_bands(self):
        """Строит список диапазонов с реальными станциями."""
        stations = load_stations()
        bands = []
        for tmpl in BAND_TEMPLATES:
            band = dict(tmpl)
            raw = stations.get(tmpl["name"], [])
            band["stations"] = self._place_stations(raw, band)
            bands.append(band)
        return bands

    @staticmethod
    def _place_stations(raw_stations, band):
        """Раскидывает URL-станции по частотам внутри диапазона.
        Возвращает [(freq, name, url, vol), ...]."""
        if not raw_stations:
            return []
        lo, hi = band["min"], band["max"]
        n = len(raw_stations)
        # равномерно по диапазону, с отступом от краёв
        span = (hi - lo) * 0.85
        start = lo + (hi - lo) * 0.075
        out = []
        for i, st in enumerate(raw_stations):
            freq = start + (span * i / max(1, n - 1)) if n > 1 else (lo + hi) / 2
            freq = round(freq / band["step"]) * band["step"]
            out.append((freq, st["name"], st["url"], 0.7))
        return out

    @property
    def band(self):
        return self.bands[self.band_idx]

    def _load_sprites(self):
        """Загружает спрайты из паков. Если нет — None (fallback на процедурные)."""
        import os
        base = os.path.join(os.path.dirname(__file__), "assets", "radio")
        def L(rel):
            p = os.path.join(base, rel)
            if not os.path.exists(p):
                return None
            try:
                return pygame.image.load(p).convert_alpha()
            except Exception:
                return None

        # HiFi System — компоненты
        self.spr["receiver"]  = L("hifi/receiver.png")
        self.spr["equalizer"] = L("hifi/equalizer.png")
        self.spr["turntable"] = L("hifi/turntable.png")
        self.spr["speaker"]   = L("hifi/speaker_open.png")
        self.spr["hifi_all"]  = L("hifi/hifi_system_0.png")

        # Audio Knobs — нарезанные ручки knob_rNcM.png
        knobs_dir = os.path.join(base, "knobs")
        if os.path.isdir(knobs_dir):
            for f in sorted(os.listdir(knobs_dir)):
                if f.lower().endswith(".png") and f.startswith("knob_r"):
                    key = f.replace(".png", "").lower()  # knob_r0c1
                    self.spr[key] = L(f"knobs/{f}")

        # Обрезка прозрачных краёв у всех knob_r*.png
        for key in list(self.spr.keys()):
            if key.startswith("knob_r") and self.spr[key]:
                self.spr[key] = self._trim(self.spr[key])

        # Подбираем ручки под TUNE и VOL (большая чёрная + серебристая)
        self.spr["knob_tune"] = self.spr.get("knob_r1c0")
        self.spr["knob_vol"]  = self.spr.get("knob_r1c2")
            # Псевдонимы для удобства: большая / средняя / маленькая ручка
            # (подберём после просмотра превью)

        # Автообрезка прозрачных краёв у ручек
        for key in list(self.spr.keys()):
            if key.startswith("knob_r") and self.spr[key]:
                self.spr[key] = self._trim(self.spr[key])

        # Псевдонимы: TUNE — большая, VOL — серебристая
        self.spr["knob_tune"] = self.spr.get("knob_r1c0") or self.spr.get("knob_r2c0")
        self.spr["knob_vol"]  = self.spr.get("knob_r1c2") or self.spr.get("knob_r0c0")

        # Логируем что загрузилось
        loaded = [k for k, v in self.spr.items() if v]
        if loaded:
            print(f"[radio] спрайтов загружено: {len(loaded)} ({', '.join(loaded[:5])}...)")
        else:
            print("[radio] спрайтов нет — рисуем процедурно")

    @staticmethod
    def _trim(surface):
        """Обрезает прозрачные края у Surface."""
        rect = surface.get_bounding_rect(min_alpha=20)
        if rect.w == 0 or rect.h == 0:
            return surface
        trimmed = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        trimmed.blit(surface, (0, 0), rect)
        return trimmed

    def _load_ui_sound(self, filename):
        """Загружает WAV для UI-звуков (крутилки, кнопки)."""
        import os
        path = os.path.join(os.path.dirname(__file__), "assets", "radio", filename)
        if not os.path.exists(path):
            return None
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None

    def _stop_current(self):
        self.player.stop()
        self.current_station = None

    def _tune(self):
        """Ищет станцию рядом с текущей частотой и играет её через VLC."""
        if not self.on:
            self._stop_current()
            self._stop_noise()
            self.status = "выкл"
            return
        b = self.band
        best = None
        best_dist = 999
        for freq, name, url, vol in b["stations"]:
            d = abs(freq - self.frequency)
            if d < best_dist:
                best_dist = d
                best = (freq, name, url, vol)

        threshold = max(b["step"] * 5, (b["max"] - b["min"]) * 0.02)
        if best and best_dist <= threshold:
            self._stop_noise()
            if self.current_station and self.current_station[1] == best[1]:
                return
            ok = self.player.play(best[2], best[1])
            self.player.set_volume(self.volume)
            if ok:
                self.current_station = (best[0], best[1])
                self.status = "играет"
            else:
                self.current_station = None
                self.status = "ошибка потока"
        else:
            self._stop_current()
            self.status = "поиск..."
            # Включаем белый шум (если ещё не играет)
            self._start_noise()

    def _start_noise(self):
        if not self.snd_noise:
            return
        if self._noise_channel and self._noise_channel.get_busy():
            return
        try:
            self._noise_channel = self.snd_noise.play(-1)  # цикл
        except Exception:
            self._noise_channel = None

    def _stop_noise(self):
        if self._noise_channel:
            try:
                self._noise_channel.stop()
            except Exception:
                pass
            self._noise_channel = None

    def handle_event(self, event):
        if not self.open:
            return

        import math as _m

        def angle_of(mx, my, cx, cy):
            return _m.atan2(my - cy, mx - cx)

        # --- МЫШЬ: нажатие ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # POWER
            if self._power_rect().collidepoint(mx, my):
                self.on = not self.on
                if self.snd_power:
                    self.snd_power.set_volume(0.5)
                    self.snd_power.play()
                self._tune()
                return

            # Диапазоны
            for i in range(len(self.bands)):
                if self._band_btn(i).collidepoint(mx, my):
                    self.band_idx = i
                    b = self.band
                    self.frequency = (b["min"] + b["max"]) / 2
                    if self.snd_band:
                        self.snd_band.set_volume(0.5)
                        self.snd_band.play()
                    self._tune()
                    return

            # Крутилка TUNE — крутим как ручку
            tx, ty, tr = self._tune_knob()
            if (mx - tx) ** 2 + (my - ty) ** 2 <= (tr + 20) ** 2:
                self._dragging = "tune"
                self._drag_prev_angle = angle_of(mx, my, tx, ty)
                return

            # Крутилка VOL
            vx, vy, vr = self._vol_knob()
            if (mx - vx) ** 2 + (my - vy) ** 2 <= (vr + 20) ** 2:
                self._dragging = "vol"
                self._drag_prev_angle = angle_of(mx, my, vx, vy)
                return
            return

        # --- МЫШЬ: отпустили ---
        if event.type == pygame.MOUSEBUTTONUP:
            self._dragging = None
            return

        # --- МЫШЬ: движение (крутим ручку) ---
        if event.type == pygame.MOUSEMOTION and self._dragging:
            mx, my = event.pos
            if self._dragging == "tune":
                tx, ty, tr = self._tune_knob()
                cur = angle_of(mx, my, tx, ty)
                delta = cur - self._drag_prev_angle
                if delta > _m.pi:   delta -= 2 * _m.pi
                if delta < -_m.pi:  delta += 2 * _m.pi
                self._drag_prev_angle = cur

                b = self.band
                self.frequency += delta * b["step"] * 2.0
                self.frequency = max(b["min"], min(b["max"], self.frequency))
                self.knob_angle -= delta * 2.0
                # Треск крутилки — не чаще 1 раза в 4 кадра
                if abs(delta) > 0.02 and self._dial_sound_cooldown <= 0:
                    if self.snd_dial:
                        self.snd_dial.set_volume(0.25)
                        self.snd_dial.play()
                    self._dial_sound_cooldown = 4
                self._tune()
            elif self._dragging == "vol":
                vx, vy, vr = self._vol_knob()
                cur = angle_of(mx, my, vx, vy)
                delta = cur - self._drag_prev_angle
                if delta > _m.pi:   delta -= 2 * _m.pi
                if delta < -_m.pi:  delta += 2 * _m.pi
                self._drag_prev_angle = cur

                self.volume = max(0.0, min(1.0, self.volume + delta * 0.5))
                self.player.set_volume(self.volume)
            return

        # --- КЛАВИАТУРА ---
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
            self.band_idx = (self.band_idx + 1) % len(self.bands)
            self.frequency = (b["min"] + b["max"]) / 2
            self.knob_angle = 0
            self._tune()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.frequency = max(b["min"], self.frequency - step)
            self.knob_angle -= 0.15
            self._tune()
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.frequency = min(b["max"], self.frequency + step)
            self.knob_angle += 0.15
            self._tune()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.volume = min(1.0, self.volume + 0.05)
            self.player.set_volume(self.volume)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.volume = max(0.0, self.volume - 0.05)
            self.player.set_volume(self.volume)

    def update(self, dt):
        self.tick += 1
        if self._dial_sound_cooldown > 0:
            self._dial_sound_cooldown -= 1
        if not self._dragging:
            self.knob_angle *= 0.92  # плавный возврат стрелки

    def open_ui(self):
        self.open = True
        self.on = True
        self.band_idx = 0
        st = self.band["stations"]
        self.frequency = st[0][0] if st else (self.band["min"] + self.band["max"]) / 2
        self._dragging = None           # "tune" | "vol" | None
        self._drag_prev_angle = 0.0     # предыдущий угол мыши
        self._tune()

    # ---------- ГЕОМЕТРИЯ (общая для draw и mouse) ----------
    def _vol_knob(self):
        return (WIDTH // 2 - 220, HEIGHT - 155, 55)

    def _tune_knob(self):
        return (WIDTH // 2 + 90, HEIGHT - 155, 70)

    def _band_btn(self, i):
        bw, gap = 110, 10
        total = len(self.bands) * bw + (len(self.bands) - 1) * gap
        x0 = (WIDTH - total) // 2 - 60
        return pygame.Rect(x0 + i * (bw + gap), HEIGHT - 60, bw, 36)

    def _power_rect(self):
        return pygame.Rect(WIDTH - 200, HEIGHT - 60, 130, 36)

    def close(self):
        self.open = False
        self.player.stop()
        self._stop_noise()

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
        for freq, name, _url, _vol in b["stations"]:
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
            best_d = min((abs(s[0] - self.frequency) for s in band["stations"]), default=999)
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
        vol_cx, vol_cy, vol_r = self._vol_knob()
        pygame.draw.circle(screen, (40, 25, 15), (vol_cx, vol_cy), vol_r)
        pygame.draw.circle(screen, (200, 180, 150), (vol_cx, vol_cy), vol_r - 5)
        pygame.draw.circle(screen, (60, 40, 25), (vol_cx, vol_cy), vol_r - 5, 2)
        # риска-указатель
        ang = -math.pi * 0.75 + self.volume * math.pi * 1.5
        ex = vol_cx + int(math.cos(ang) * (vol_r - 15))
        ey = vol_cy + int(math.sin(ang) * (vol_r - 15))
        pygame.draw.line(screen, (60, 40, 25), (vol_cx, vol_cy), (ex, ey), 4)
        pygame.draw.circle(screen, (60, 40, 25), (vol_cx, vol_cy), 6)
        # подпись
        vt = self.font_small.render(f"VOL  {int(self.volume*100)}%", True, (240, 220, 180))
        screen.blit(vt, (vol_cx - vt.get_width() // 2, vol_cy + 65))

        # === КРУТИЛКА ЧАСТОТЫ ===
        tun_cx, tun_cy, tun_r = self._tune_knob()
        knob_img = self.spr.get("knob_knob_large") or self.spr.get("knob_knob")
        if knob_img:
            # Масштабируем под наш радиус
            target = tun_r * 2
            scaled = pygame.transform.smoothscale(knob_img, (target, target))
            # Поворачиваем по углу
            ang_deg = -math.degrees(self.knob_angle + (self.frequency - b["min"]) / span * math.pi * 1.5 - math.pi * 0.75)
            rotated = pygame.transform.rotate(scaled, ang_deg)
            rr = rotated.get_rect(center=(tun_cx, tun_cy))
            screen.blit(rotated, rr.topleft)
        else:
            # Fallback — процедурная
            pygame.draw.circle(screen, (40, 25, 15), (tun_cx, tun_cy), tun_r)
            pygame.draw.circle(screen, (200, 180, 150), (tun_cx, tun_cy), tun_r - 6)
            pygame.draw.circle(screen, (60, 40, 25), (tun_cx, tun_cy), tun_r - 6, 3)
            for i in range(24):
                a = i * math.tau / 24
                x1 = tun_cx + int(math.cos(a) * (tun_r - 12))
                y1 = tun_cy + int(math.sin(a) * (tun_r - 12))
                x2 = tun_cx + int(math.cos(a) * (tun_r - 6))
                y2 = tun_cy + int(math.sin(a) * (tun_r - 6))
                pygame.draw.line(screen, (80, 50, 30), (x1, y1), (x2, y2), 2)
            pygame.draw.circle(screen, (240, 220, 180), (tun_cx, tun_cy), 26)
            pygame.draw.circle(screen, (60, 40, 25), (tun_cx, tun_cy), 26, 2)
            ang2 = self.knob_angle + (self.frequency - b["min"]) / span * math.pi * 1.5 - math.pi * 0.75
            ex2 = tun_cx + int(math.cos(ang2) * 22)
            ey2 = tun_cy + int(math.sin(ang2) * 22)
            pygame.draw.line(screen, (60, 40, 25), (tun_cx, tun_cy), (ex2, ey2), 4)
        tt = self.font_small.render("TUNE", True, (240, 220, 180))
        screen.blit(tt, (tun_cx - tt.get_width() // 2, tun_cy + tun_r + 8))

        # === КНОПКИ ДИАПАЗОНОВ ===
        for i, band_data in enumerate(self.bands):
            r_ = self._band_btn(i)
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
        pwr_r = self._power_rect()
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
            "Мышь: тяни крутилки · Клик: кнопки · Клавиши: ←→ ↑↓ B Space Esc",
            True, (220, 200, 170))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))
