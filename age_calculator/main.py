import pygame
import sys
import random
import os
from datetime import datetime
import pygame_gui

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Калькулятор возраста папы (Material Design)")
clock = pygame.time.Clock()

# --- Надежная загрузка шрифтов ---
def load_font(path, size, bold=False):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return pygame.font.Font(path, size)
    except Exception:
        pass
    return pygame.font.SysFont("dejavusans", size, bold=bold)

font_title = load_font("assets/fonts/Roboto-Bold.ttf", 40, bold=True)
font_small = load_font("assets/fonts/Roboto-Regular.ttf", 20)
font_huge = load_font("assets/fonts/Roboto-Bold.ttf", 32, bold=True)

# --- Глобальное состояние ---
is_dark_theme = True
particles = []
result_text = ""
today_text = "" # Для вывода возраста на сегодня
current_font_size = 32

manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme_dark.json')

def build_ui():
    manager.clear_and_reset()
    global father_input, son_input, calculate_button, text_size_slider, theme_toggle, today_button
    
    father_input = pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect((300, 150), (200, 40)), manager=manager, placeholder_text="ДД.ММ.ГГГГ"
    )
    son_input = pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect((300, 250), (200, 40)), manager=manager, placeholder_text="ДД.ММ.ГГГГ"
    )
    calculate_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((300, 350), (200, 50)), text="РАССЧИТАТЬ", manager=manager
    )
    # Кнопка для быстрого заполнения текущей даты
    today_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((550, 250), (150, 40)), text="Дата: Сегодня", manager=manager
    )
    text_size_slider = pygame_gui.elements.UIHorizontalSlider(
        relative_rect=pygame.Rect((550, 400), (200, 30)), start_value=32, value_range=(16, 48), manager=manager
    )
    theme_toggle = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((550, 450), (200, 40)), text="Тема: Темная" if is_dark_theme else "Тема: Светлая", manager=manager
    )

build_ui()

class Particle:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-15, -5)
        self.color = random.choice([(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100), (255, 100, 255)])
        self.size = random.randint(3, 8)
        self.life = random.randint(40, 80)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.6 
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

def get_full_years(birth_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y")
        today = datetime.now()
        # ВОТ ОНА, ТА САМАЯ ЛОГИКА РАСЧЕТА НА СЕГОДНЯ
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except ValueError:
        return None

running = True
while running:
    time_delta = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Обработка кнопки "Рассчитать"
            if event.ui_element == calculate_button:
                d1_str, d2_str = father_input.get_text(), son_input.get_text()
                
                age_father_today = get_full_years(d1_str)
                age_son_today = get_full_years(d2_str)

                if age_father_today is not None and age_son_today is not None:
                    try:
                        d1 = datetime.strptime(d1_str, "%d.%m.%Y")
                        d2 = datetime.strptime(d2_str, "%d.%m.%Y")
                        years_at_birth = d2.year - d1.year - ((d2.month, d2.day) < (d1.month, d1.day))
                        
                        if years_at_birth < 0:
                            result_text = "Сын родился раньше отца? О_о"
                            today_text = ""
                        else:
                            result_text = f"Папе было {years_at_birth} лет при рождении сына."
                            # ЗАПИСЬ РЕЗУЛЬТАТА НА ТЕКУЩУЮ ДАТУ
                            today_text = f"На сегодня: папе {age_father_today} лет, сыну {age_son_today} лет."
                            
                            for _ in range(150): 
                                particles.append(Particle(WIDTH//2, 450))
                    except:
                        result_text = "Ошибка в датах!"
                        today_text = ""
                else:
                    result_text = "Введи даты в формате ДД.ММ.ГГГГ"
                    today_text = ""

            # Обработка кнопки "Дата: Сегодня"
            if event.ui_element == today_button:
                today_str = datetime.now().strftime("%d.%m.%Y")
                son_input.set_text(today_str)
                father_input.set_text("01.01.1980") # Пример даты отца

            # Обработка переключателя темы
            if event.ui_element == theme_toggle:
                is_dark_theme = not is_dark_theme
                if is_dark_theme:
                    manager.get_theme().load_theme('theme_dark.json')
                else:
                    manager.get_theme().load_theme('theme_light.json')
                build_ui()

        manager.process_events(event)

    manager.update(time_delta)
    
    screen.fill((30, 30, 40) if is_dark_theme else (240, 242, 245))
    text_color = (255, 255, 255) if is_dark_theme else (50, 50, 50)
    title_color = (187, 134, 252) if is_dark_theme else (98, 0, 238)
    today_color = (100, 255, 100) if is_dark_theme else (0, 150, 0)
    
    title_surface = font_title.render("Когда папа стал папой?", True, title_color)
    screen.blit(title_surface, (WIDTH//2 - title_surface.get_width()//2, 40))

    screen.blit(font_small.render("Дата рождения ОТЦА (ДД.ММ.ГГГГ):", True, text_color), (300, 120))
    screen.blit(font_small.render("Дата рождения СЫНА (ДД.ММ.ГГГГ):", True, text_color), (300, 220))
    screen.blit(font_small.render("Размер текста:", True, text_color), (550, 370))

    manager.draw_ui(screen)

    # Вывод основного результата
    if result_text:
        current_font_size = int(text_size_slider.get_current_value())
        res_font = load_font("assets/fonts/Roboto-Bold.ttf", current_font_size, bold=True)
        res_surface = res_font.render(result_text, True, title_color)
        screen.blit(res_surface, (WIDTH//2 - res_surface.get_width()//2, 480))

    # Вывод результата на текущую дату (огромный и зеленый)
    if today_text:
        today_surface = font_huge.render(today_text, True, today_color)
        screen.blit(today_surface, (WIDTH//2 - today_surface.get_width()//2, 540))

    for p in particles[:]:
        p.update()
        p.draw(screen)
        if p.life <= 0:
            particles.remove(p)

    pygame.display.flip()

pygame.quit()
