import pygame
import sys
import os

# --- Настройки ---
WIDTH, HEIGHT = 800, 600
FPS = 60
BG_COLOR = (20, 24, 30)
PANEL_COLOR = (30, 35, 45)
TEXT_COLOR = (220, 225, 230)
ACCENT_COLOR = (0, 180, 255)
GREEN_COLOR = (50, 255, 100)
YELLOW_COLOR = (255, 220, 50)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mint System Dashboard")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("dejavusans", 32, bold=True)
font_main = pygame.font.SysFont("dejavusans", 22)
font_small = pygame.font.SysFont("dejavusans", 16)

# --- Функции чтения системных метрик ---
def get_cpu_usage():
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        user, nice, system, idle, iowait, irq, softirq, steal = map(int, parts[1:9])
        total = user + nice + system + idle + iowait + irq + softirq + steal
        busy = total - idle - iowait
        return busy, total
    except Exception:
        return 0, 1

def get_ram_usage():
    try:
        meminfo = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    meminfo[parts[0][:-1]] = int(parts[1])
        total = meminfo.get('MemTotal', 1)
        available = meminfo.get('MemAvailable', 1)
        used = total - available
        return used, total
    except Exception:
        return 0, 1

def get_disk_usage():
    try:
        statvfs = os.statvfs('/')
        total = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_bavail
        used = total - free
        return used, total
    except Exception:
        return 0, 1

def get_uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    except Exception:
        return "0h 0m"

def format_bytes(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

# --- Класс Дашборда ---
class Dashboard:
    def __init__(self):
        self.cpu_busy = 0
        self.cpu_total = 1
        self.prev_cpu_busy = 0
        self.prev_cpu_total = 0
        self.cpu_percent = 0
        
        self.ram_used = 0
        self.ram_total = 1
        self.ram_percent = 0
        
        self.disk_used = 0
        self.disk_total = 1
        self.disk_percent = 0
        
        self.uptime = "0h 0m"
        self.update_stats()

    def update_stats(self):
        # CPU
        self.prev_cpu_busy = self.cpu_busy
        self.prev_cpu_total = self.cpu_total
        self.cpu_busy, self.cpu_total = get_cpu_usage()
        
        delta_total = self.cpu_total - self.prev_cpu_total
        delta_busy = self.cpu_busy - self.prev_cpu_busy
        if delta_total > 0:
            self.cpu_percent = (delta_busy / delta_total) * 100
            
        # RAM
        self.ram_used, self.ram_total = get_ram_usage()
        self.ram_percent = (self.ram_used / self.ram_total) * 100 if self.ram_total > 0 else 0
        
        # Disk
        self.disk_used, self.disk_total = get_disk_usage()
        self.disk_percent = (self.disk_used / self.disk_total) * 100 if self.disk_total > 0 else 0
        
        # Uptime
        self.uptime = get_uptime()

    def draw_bar(self, surface, x, y, width, height, percent, color, label, value_text):
        # Label
        label_surf = font_main.render(label, True, TEXT_COLOR)
        surface.blit(label_surf, (x, y))
        
        # Bar bg
        bar_bg = pygame.Rect(x, y + 35, width, height)
        pygame.draw.rect(surface, (15, 18, 25), bar_bg, border_radius=10)
        
        # Bar fill
        fill_width = int(width * (percent / 100))
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y + 35, fill_width, height)
            pygame.draw.rect(surface, color, fill_rect, border_radius=10)
            
        # Value text
        val_surf = font_small.render(value_text, True, TEXT_COLOR)
        surface.blit(val_surf, (x, y + 35 + height + 5))

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        # Header
        title = font_title.render("Mint System Dashboard", True, ACCENT_COLOR)
        surface.blit(title, (40, 30))
        
        uptime_surf = font_main.render(f"Uptime: {self.uptime}", True, TEXT_COLOR)
        surface.blit(uptime_surf, (WIDTH - 200, 45))
        
        # Panels
        panel_rect = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 130)
        pygame.draw.rect(surface, PANEL_COLOR, panel_rect, border_radius=15)
        
        # CPU
        self.draw_bar(surface, 70, 130, WIDTH - 140, 30, self.cpu_percent, 
                      ACCENT_COLOR, "CPU Usage", f"{self.cpu_percent:.1f}%")
        
        # RAM
        ram_text = f"{format_bytes(self.ram_used * 1024)} / {format_bytes(self.ram_total * 1024)}"
        self.draw_bar(surface, 70, 240, WIDTH - 140, 30, self.ram_percent, 
                      GREEN_COLOR, "RAM Usage", ram_text)
        
        # Disk
        disk_text = f"{format_bytes(self.disk_used)} / {format_bytes(self.disk_total)}"
        self.draw_bar(surface, 70, 350, WIDTH - 140, 30, self.disk_percent, 
                      YELLOW_COLOR, "Disk Usage (/)", disk_text)

        # Footer
        footer = font_small.render("Данные обновляются каждые 0.5 сек. Нажмите ESC для выхода.", True, (100, 100, 100))
        surface.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT - 30))

def main():
    dashboard = Dashboard()
    running = True
    update_timer = 0
    update_interval = 0.5 # Обновление раз в полсекунды

    while running:
        dt = clock.tick(FPS) / 1000.0
        update_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Периодическое обновление данных
        if update_timer >= update_interval:
            dashboard.update_stats()
            update_timer = 0

        dashboard.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
