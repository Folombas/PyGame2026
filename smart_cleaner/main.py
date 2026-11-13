import pygame
import sys
import os
import shutil

# --- Настройки ---
WIDTH, HEIGHT = 900, 650
BG_COLOR = (24, 26, 32)
PANEL_COLOR = (36, 40, 50)
ACCENT_COLOR = (0, 150, 255)
SUCCESS_COLOR = (50, 205, 50)
TEXT_COLOR = (230, 230, 230)
TEXT_MUTED = (150, 150, 160)

# Целевая папка (по умолчанию Downloads)
TARGET_DIR = os.path.expanduser("~/Downloads")

# Категории файлов
CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xls", ".xlsx", ".pptx", ".csv"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac"],
    "Code": [".py", ".js", ".html", ".css", ".json", ".sh", ".c", ".cpp"],
    "Executables": [".deb", ".AppImage", ".sh"] # Осторожно с .sh, они в Code, но оставим в exe для Linux
}
# Исправляем дубликат .sh
CATEGORIES["Code"].remove(".sh")

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smart Desktop Cleaner (Linux Mint Utility)")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("dejavusans", 32, bold=True)
font_main = pygame.font.SysFont("dejavusans", 20)
font_small = pygame.font.SysFont("dejavusans", 16)

class FileOrganizer:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.files_to_move = [] # Список кортежей (old_path, new_path, category)
        self.stats = {cat: 0 for cat in CATEGORIES}
        self.total_files = 0
        self.is_scanning = False
        self.is_moving = False
        self.move_progress = 0
        self.scan_complete = False

    def scan(self):
        self.files_to_move = []
        self.stats = {cat: 0 for cat in CATEGORIES}
        self.total_files = 0
        self.move_progress = 0
        self.scan_complete = False

        if not os.path.exists(self.target_dir):
            print(f"Папка {self.target_dir} не найдена!")
            return

        for filename in os.listdir(self.target_dir):
            filepath = os.path.join(self.target_dir, filename)
            if os.path.isfile(filepath):
                ext = os.path.splitext(filename)[1].lower()
                for cat, exts in CATEGORIES.items():
                    if ext in exts:
                        new_dir = os.path.join(self.target_dir, cat)
                        new_path = os.path.join(new_dir, filename)
                        self.files_to_move.append((filepath, new_path, cat))
                        self.stats[cat] += 1
                        self.total_files += 1
                        break # Файл отнесен к одной категории
        self.scan_complete = True

    def execute_moves(self):
        if not self.files_to_move:
            return
        
        self.is_moving = True
        for filepath, new_path, cat in self.files_to_move:
            new_dir = os.path.dirname(new_path)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)
            try:
                shutil.move(filepath, new_path)
            except Exception as e:
                print(f"Ошибка при перемещении {filepath}: {e}")
            self.move_progress += 1
        
        self.is_moving = False
        self.files_to_move = [] # Очищаем список после выполнения
        self.scan_complete = False

organizer = FileOrganizer(TARGET_DIR)
state = "IDLE" # IDLE, SCANNING, READY, MOVING

def draw_ui(screen):
    screen.fill(BG_COLOR)

    # Заголовок
    title_surf = font_title.render("Smart File Cleaner", True, ACCENT_COLOR)
    screen.blit(title_surf, (40, 30))
    
    subtitle = font_small.render(f"Target: {TARGET_DIR}", True, TEXT_MUTED)
    screen.blit(subtitle, (40, 75))

    # Панель со статистикой
    panel_rect = pygame.Rect(40, 110, WIDTH - 80, 380)
    pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=10)

    if state == "IDLE":
        text = font_main.render("Press SCAN to analyze files in your Downloads folder.", True, TEXT_COLOR)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
        
    elif state == "SCANNING":
        text = font_main.render("Scanning files...", True, ACCENT_COLOR)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))

    elif state in ("READY", "MOVING"):
        y_offset = 140
        for cat, count in organizer.stats.items():
            if count > 0:
                # Отрисовка строки категории
                cat_text = font_main.render(f"{cat}:", True, TEXT_COLOR)
                count_text = font_main.render(f"{count} files", True, ACCENT_COLOR)
                screen.blit(cat_text, (70, y_offset))
                screen.blit(count_text, (300, y_offset))
                
                # Прогресс-бар для категории (условно)
                bar_width = 400
                bar_rect = pygame.Rect(450, y_offset + 5, bar_width, 20)
                pygame.draw.rect(screen, (20, 20, 25), bar_rect, border_radius=5)
                
                fill_width = int(bar_width * (count / organizer.total_files))
                if fill_width > 0:
                    fill_rect = pygame.Rect(450, y_offset + 5, fill_width, 20)
                    pygame.draw.rect(screen, ACCENT_COLOR, fill_rect, border_radius=5)
                
                y_offset += 40
        
        # Общий прогресс
        if state == "MOVING":
            progress = organizer.move_progress / organizer.total_files
            bar_width = WIDTH - 80
            bar_rect = pygame.Rect(40, 510, bar_width, 30)
            pygame.draw.rect(screen, (20, 20, 25), bar_rect, border_radius=8)
            
            fill_rect = pygame.Rect(40, 510, int(bar_width * progress), 30)
            pygame.draw.rect(screen, SUCCESS_COLOR, fill_rect, border_radius=8)
            
            prog_text = font_main.render(f"Moving files: {organizer.move_progress} / {organizer.total_files}", True, TEXT_COLOR)
            screen.blit(prog_text, (WIDTH//2 - prog_text.get_width()//2, 565))
        else:
            total_text = font_title.render(f"Total files to move: {organizer.total_files}", True, SUCCESS_COLOR)
            screen.blit(total_text, (WIDTH//2 - total_text.get_width()//2, 520))

    # Кнопки
    button_y = HEIGHT - 70
    scan_btn_rect = pygame.Rect(WIDTH//2 - 210, button_y, 200, 50)
    start_btn_rect = pygame.Rect(WIDTH//2 + 10, button_y, 200, 50)
    
    # Кнопка SCAN
    mouse_pos = pygame.mouse.get_pos()
    
    color_scan = (50, 50, 60) if scan_btn_rect.collidepoint(mouse_pos) else (40, 40, 50)
    if state == "SCANNING" or state == "MOVING": color_scan = (30, 30, 35)
    pygame.draw.rect(screen, color_scan, scan_btn_rect, border_radius=8)
    scan_text = font_main.render("1. SCAN FILES", True, TEXT_COLOR)
    screen.blit(scan_text, (scan_btn_rect.centerx - scan_text.get_width()//2, scan_btn_rect.centery - scan_text.get_height()//2))

    # Кнопка START
    if state in ("READY", "MOVING") and organizer.total_files > 0:
        color_start = (0, 200, 100) if start_btn_rect.collidepoint(mouse_pos) else SUCCESS_COLOR
        pygame.draw.rect(screen, color_start, start_btn_rect, border_radius=8)
        start_text = font_main.render("2. CLEAN UP!", True, (20, 20, 20))
        screen.blit(start_text, (start_btn_rect.centerx - start_text.get_width()//2, start_btn_rect.centery - start_text.get_height()//2))
    else:
        pygame.draw.rect(screen, (40, 40, 50), start_btn_rect, border_radius=8)
        start_text = font_main.render("2. CLEAN UP!", True, (80, 80, 90))
        screen.blit(start_text, (start_btn_rect.centerx - start_text.get_width()//2, start_btn_rect.centery - start_text.get_height()//2))

    return scan_btn_rect, start_btn_rect

def main():
    global state, organizer
    running = True

    while running:
        scan_btn, start_btn = draw_ui(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # ЛКМ
                    if scan_btn.collidepoint(event.pos) and state not in ("SCANNING", "MOVING"):
                        state = "SCANNING"
                        organizer.scan()
                        state = "READY"
                        
                    elif start_btn.collidepoint(event.pos) and state == "READY" and organizer.total_files > 0:
                        state = "MOVING"
                        # Выполняем перемещение в отдельном потоке или через генератор
                        # Для простоты (чтобы не усложнять код с threading) сделаем это здесь,
                        # но Pygame может подтормозить на пару секунд при 1000 файлов.
                        # В идеале нужно использовать threading, но для локальной утилиты сойдет.
                        organizer.execute_moves()
                        state = "IDLE" # Сброс после выполнения

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
