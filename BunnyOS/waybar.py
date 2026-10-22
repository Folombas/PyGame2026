"""Waybar — верхняя панель в стиле Hyprland."""
import pygame
import time
from theme import *
from settings import WIDTH


class Waybar:
    def __init__(self, font_small, font_bold):
        self.font = font_small
        self.font_bold = font_bold
        self.tick = 0
        self._cpu = 0.0
        self._mem = 0.0

    def update(self, dt):
        self.tick += 1
        if self.tick % 60 == 0:  # раз в секунду
            self._update_stats()

    def _update_stats(self):
        try:
            import real_sys
            load, total, used = real_sys.real_htop()
            self._mem = (used / total * 100) if total else 0
            import os
            self._cpu = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
        except Exception:
            pass

    def draw(self, screen, current_ws, num_ws, windows_per_ws):
        # Фон
        bar = pygame.Rect(0, 0, WIDTH, WAYBAR_H)
        pygame.draw.rect(screen, (10, 10, 18), bar)
        # Нижняя линия — градиент
        colors = gradient_h(GRAD_ACTIVE, WIDTH)
        for x in range(WIDTH):
            pygame.draw.line(screen, colors[x], (x, WAYBAR_H - 1), (x, WAYBAR_H))
        # Свечение
        glow = pygame.Surface((WIDTH, 8), pygame.SRCALPHA)
        for y in range(8):
            a = int(60 * (1 - y / 8))
            pygame.draw.line(glow, (*NEON_CYAN, a), (0, y), (WIDTH, y))
        screen.blit(glow, (0, WAYBAR_H))

        # === Workspaces (слева) ===
        x = 20
        for i in range(num_ws):
            count = len(windows_per_ws[i])
            active = (i == current_ws)
            occupied = count > 0

            # Квадрат
            size = 28
            r = pygame.Rect(x, (WAYBAR_H - size) // 2, size, size)

            if active:
                # Активный — неоновый градиент
                for yy in range(size):
                    t = yy / size
                    c = blend(NEON_CYAN, NEON_PURPLE, t)
                    pygame.draw.line(screen, c, (r.x, r.y + yy), (r.right, r.y + yy))
                pygame.draw.rect(screen, NEON_CYAN, r, 2, border_radius=6)
                # Свечение
                glow = pygame.Surface((size + 16, size + 16), pygame.SRCALPHA)
                for g in range(8, 0, -2):
                    a = int(80 * (g / 8))
                    pygame.draw.rect(glow, (*NEON_CYAN, a),
                                     (8 - g, 8 - g, size + g * 2, size + g * 2),
                                     border_radius=8)
                screen.blit(glow, (r.x - 8, r.y - 8))
                text_col = (10, 10, 20)
            elif occupied:
                # Занятый — тёмный с неоновой обводкой
                pygame.draw.rect(screen, BG_HOVER, r, border_radius=6)
                pygame.draw.rect(screen, NEON_PURPLE, r, 2, border_radius=6)
                text_col = NEON_PURPLE
            else:
                # Пустой — просто цифра
                text_col = TEXT_DIM

            t = self.font_bold.render(str(i + 1), True, text_col)
            screen.blit(t, (r.centerx - t.get_width() // 2,
                           r.centery - t.get_height() // 2))

            # Индикатор — есть ли окна
            if occupied and not active:
                pygame.draw.circle(screen, NEON_CYAN,
                                   (r.centerx, r.bottom + 4), 2)
            x += size + 8

        # === Заголовок активного окна (центр) ===
        # Пропустим — рисуется в main

        # === Справа — часы и статы ===
        # Часы
        clock = time.strftime("%H:%M")
        ct = self.font_bold.render(clock, True, TEXT)
        cx = WIDTH - ct.get_width() - 20
        screen.blit(ct, (cx, (WAYBAR_H - ct.get_height()) // 2))

        # Статы — CPU/RAM
        cpu_str = f"CPU {self._cpu:.1f}"
        ram_str = f"RAM {self._mem:.0f}%"
        cpu_t = self.font.render(cpu_str, True,
                                  NEON_CYAN if self._cpu < 2 else NEON_YELLOW)
        ram_t = self.font.render(ram_str, True,
                                  NEON_CYAN if self._mem < 70 else NEON_RED)
        ram_x = cx - ram_t.get_width() - 20
        cpu_x = ram_x - cpu_t.get_width() - 20
        screen.blit(cpu_t, (cpu_x, (WAYBAR_H - cpu_t.get_height()) // 2))
        screen.blit(ram_t, (ram_x, (WAYBAR_H - ram_t.get_height()) // 2))

        # Иконка режима — TILING / FLOAT
        mode_str = "TILING"
        mode_t = self.font.render(mode_str, True, NEON_PURPLE)
        screen.blit(mode_t, (cpu_x - mode_t.get_width() - 20,
                             (WAYBAR_H - mode_t.get_height()) // 2))
