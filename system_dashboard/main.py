import pygame
import sys
import os
import time

# --- Настройки ---
WIDTH, HEIGHT = 1000, 700
MIN_WIDTH, MIN_HEIGHT = 850, 600  # МИНИМАЛЬНЫЙ РАЗМЕР ОКНА
FPS = 60

BG_COLOR = (18, 20, 26)
PANEL_COLOR = (28, 32, 40)
GRID_COLOR = (40, 45, 55)
TEXT_COLOR = (220, 225, 230)
ACCENT_COLOR = (0, 180, 255)
GREEN_COLOR = (50, 255, 100)
YELLOW_COLOR = (255, 220, 50)
NET_COLOR = (255, 100, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Mint System Dashboard v2.1 (Adaptive)")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("dejavusans", 32, bold=True)
font_main = pygame.font.SysFont("dejavusans", 22)
font_small = pygame.font.SysFont("dejavusans", 16)

# --- Сбор системных метрик ---
def get_cpu_usage():
    try:
        with open('/proc/stat', 'r') as f: line = f.readline()
        parts = list(map(int, line.split()[1:9]))
        total = sum(parts)
        busy = total - parts[3] - parts[4]
        return busy, total
    except: return 0, 1

def get_ram_usage():
    try:
        meminfo = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2: meminfo[parts[0][:-1]] = int(parts[1])
        total = meminfo.get('MemTotal', 1)
        available = meminfo.get('MemAvailable', 1)
        return total - available, total
    except: return 0, 1

def get_net_usage():
    try:
        rx, tx = 0, 0
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()[2:]
            for line in lines:
                parts = line.split()
                if parts[0] != 'lo:':
                    rx += int(parts[1])
                    tx += int(parts[9])
        return rx, tx
    except: return 0, 0

def format_bytes(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0: return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

def format_speed(bytes_per_sec):
    if bytes_per_sec < 1024: return f"{bytes_per_sec:.0f} B/s"
    elif bytes_per_sec < 1024**2: return f"{bytes_per_sec/1024:.1f} KB/s"
    else: return f"{bytes_per_sec/1024**2:.1f} MB/s"

# --- Класс Дашборда ---
class Dashboard:
    def __init__(self):
        self.history_len = 60
        self.cpu_history = [0] * self.history_len
        self.ram_history = [0] * self.history_len
        
        self.cpu_busy, self.cpu_total = get_cpu_usage()
        self.ram_used, self.ram_total = get_ram_usage()
        
        self.prev_net_rx, self.prev_net_tx = get_net_usage()
        self.net_rx_speed = 0
        self.net_tx_speed = 0
        
        self.last_update = time.time()

    def update_stats(self):
        now = time.time()
        dt = now - self.last_update
        if dt <= 0: dt = 1
        self.last_update = now

        new_busy, new_total = get_cpu_usage()
        d_total = new_total - self.cpu_total
        d_busy = new_busy - self.cpu_busy
        cpu_pct = (d_busy / d_total * 100) if d_total > 0 else 0
        self.cpu_busy, self.cpu_total = new_busy, new_total
        self.cpu_history.append(cpu_pct)
        self.cpu_history.pop(0)

        self.ram_used, self.ram_total = get_ram_usage()
        ram_pct = (self.ram_used / self.ram_total * 100) if self.ram_total > 0 else 0
        self.ram_history.append(ram_pct)
        self.ram_history.pop(0)

        new_rx, new_tx = get_net_usage()
        self.net_rx_speed = max(0, (new_rx - self.prev_net_rx) / dt)
        self.net_tx_speed = max(0, (new_tx - self.prev_net_tx) / dt)
        self.prev_net_rx, self.prev_net_tx = new_rx, new_tx

    def draw_chart(self, surface, x, y, width, height, data, color, label, current_val_text):
        surface.blit(font_main.render(label, True, TEXT_COLOR), (x, y - 30))
        
        # Текст значения прижимаем к правому краю графика
        val_surf = font_small.render(current_val_text, True, color)
        val_rect = val_surf.get_rect(topright=(x + width, y - 25))
        surface.blit(val_surf, val_rect)
        
        chart_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, PANEL_COLOR, chart_rect)
        
        for i in range(1, 4):
            line_y = y + (height // 4) * i
            pygame.draw.line(surface, GRID_COLOR, (x, line_y), (x + width, line_y), 1)

        points = []
        step_x = width / (len(data) - 1)
        for i, val in enumerate(data):
            px = x + i * step_x
            py = y + height - (val / 100 * height)
            points.append((px, py))
            
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, 3)

    def draw(self, surface):
        surface.fill(BG_COLOR)
        w, h = surface.get_size()
        
        # --- Динамические отступы ---
        padding = 40
        sidebar_w = 280
        spacing = 20

        # Header
        surface.blit(font_title.render("Mint System Dashboard v2.1", True, ACCENT_COLOR), (padding, 30))
        
        # FPS текст прижимаем к правому верхнему углу
        fps_text = font_small.render(f"FPS: {int(clock.get_fps())} | F11: Fullscreen | ESC: Exit", True, (100, 100, 100))
        fps_rect = fps_text.get_rect(topright=(w - padding, 45))
        surface.blit(fps_text, fps_rect)

        # --- Расчет размеров графиков ---
        # Доступная ширина для графиков = общая ширина - отступы - ширина правой панели - зазор
        avail_chart_w = w - (padding * 2) - sidebar_w - spacing
        
        # Доступная высота делится на два графика (CPU и RAM)
        # Отступ сверху 120px (заголовки), снизу 40px
        avail_h = h - 150 - 40
        chart_h = (avail_h - spacing) // 2

        # Отрисовка графиков
        self.draw_chart(surface, padding, 120, avail_chart_w, chart_h, self.cpu_history, ACCENT_COLOR, "CPU Usage", f"{self.cpu_history[-1]:.1f}%")
        
        ram_y = 120 + chart_h + spacing + 30 # +30 для заголовка второго графика
        self.draw_chart(surface, padding, ram_y, avail_chart_w, chart_h, self.ram_history, GREEN_COLOR, "RAM Usage", 
                        f"{format_bytes(self.ram_used*1024)} / {format_bytes(self.ram_total*1024)}")

        # --- Правая колонка ---
        right_x = w - sidebar_w - padding
        panel_h = h - 120 - 40 # Высота панели до нижнего края
        pygame.draw.rect(surface, PANEL_COLOR, (right_x, 120, sidebar_w, panel_h), border_radius=10)
        
        surface.blit(font_main.render("Network Speed", True, TEXT_COLOR), (right_x + 20, 140))
        
        surface.blit(font_small.render("Download", True, (150, 150, 160)), (right_x + 20, 190))
        dl_text = font_main.render(format_speed(self.net_rx_speed), True, NET_COLOR)
        surface.blit(dl_text, (right_x + 20, 210))
        
        surface.blit(font_small.render("Upload", True, (150, 150, 160)), (right_x + 20, 260))
        ul_text = font_main.render(format_speed(self.net_tx_speed), True, YELLOW_COLOR)
        surface.blit(ul_text, (right_x + 20, 280))

        surface.blit(font_main.render("Disk Usage (/)", True, TEXT_COLOR), (right_x + 20, 360))
        try:
            st = os.statvfs('/')
            total = st.f_frsize * st.f_blocks
            free = st.f_frsize * st.f_bavail
            used = total - free
            pct = (used / total) * 100
            
            bar_w = sidebar_w - 40
            pygame.draw.rect(surface, (15, 18, 25), (right_x + 20, 400, bar_w, 20), border_radius=5)
            pygame.draw.rect(surface, YELLOW_COLOR, (right_x + 20, 400, bar_w * (pct/100), 20), border_radius=5)
            
            surface.blit(font_small.render(f"{format_bytes(used)} / {format_bytes(total)}", True, TEXT_COLOR), (right_x + 20, 430))
        except:
            pass

def main():
    global screen
    dashboard = Dashboard()
    running = True
    fullscreen = False
    update_timer = 0
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        update_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            
            # --- ОБРАБОТКА ИЗМЕНЕНИЯ РАЗМЕРА ОКНА С ОГРАНИЧЕНИЕМ ---
            if event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    # Берем новые размеры, но не меньше минимальных
                    new_w = max(MIN_WIDTH, event.w)
                    new_h = max(MIN_HEIGHT, event.h)
                    screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)

        if update_timer >= 1.0:
            dashboard.update_stats()
            update_timer = 0

        dashboard.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
