import pygame
import sys
import random
from datetime import datetime
import pygame_gui

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Калькулятор возраста папы")
clock = pygame.time.Clock()

# Используем встроенные шрифты системы (DejaVu Sans)
font_title = pygame.font.SysFont("dejavusans", 40, bold=True)
font_main = pygame.font.SysFont("dejavusans", 28)
font_small = pygame.font.SysFont("dejavusans", 20)

manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')

father_input = pygame_gui.elements.UITextEntryLine(
    relative_rect=pygame.Rect((300, 150), (200, 40)),
    manager=manager,
    placeholder_text="ДД.ММ.ГГГГ"
)
son_input = pygame_gui.elements.UITextEntryLine(
    relative_rect=pygame.Rect((300, 250), (200, 40)),
    manager=manager,
    placeholder_text="ДД.ММ.ГГГГ"
)
calculate_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((300, 350), (200, 50)),
    text="РАССЧИТАТЬ",
    manager=manager
)
text_size_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((550, 450), (200, 30)),
    start_value=32,
    value_range=(16, 48),
    manager=manager
)
theme_toggle = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((550, 500), (200, 40)),
    text="Тема: Светлая",
    manager=manager
)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
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

particles = []
result_text = ""
funny_comment = ""
current_font_size = 32

def calculate_age_on_today(birth_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y")
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except ValueError:
        return None

running = True
while running:
    time_delta = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == calculate_button:
                d1_str = father_input.get_text()
                d2_str = son_input.get_text()
                
                age_father_today = calculate_age_on_today(d1_str)
                age_son_today = calculate_age_on_today(d2_str)

                if age_father_today is not None and age_son_today is not None:
                    try:
                        d1 = datetime.strptime(d1_str, "%d.%m.%Y")
                        d2 = datetime.strptime(d2_str, "%d.%m.%Y")
                        years_at_birth = d2.year - d1.year - ((d2.month, d2.day) < (d1.month, d1.day))
                        
                        result_text = f"Отцу было {years_at_birth} лет, когда родился сын."
                        funny_comment = f"Сейчас папе {age_father_today} лет, а сыну {age_son_today}."
                        
                        for _ in range(100):
                            particles.append(Particle(WIDTH//2, 450))
                    except:
                        result_text = "Ошибка в датах!"
                        funny_comment = ""
                else:
                    result_text = "Введи даты в формате ДД.ММ.ГГГГ"
                    funny_comment = ""

            if event.ui_element == theme_toggle:
                if theme_toggle.text == "Тема: Светлая":
                    theme_toggle.set_text("Тема: Темная")
                else:
                    theme_toggle.set_text("Тема: Светлая")

        manager.process_events(event)

    manager.update(time_delta)
    screen.fill((30, 30, 40))

    title_surface = font_title.render("Когда папа стал папой?", True, (255, 200, 50))
    screen.blit(title_surface, (WIDTH//2 - title_surface.get_width()//2, 40))

    screen.blit(font_small.render("Дата рождения ОТЦА (ДД.ММ.ГГГГ):", True, (255, 255, 255)), (300, 120))
    screen.blit(font_small.render("Дата рождения СЫНА (ДД.ММ.ГГГГ):", True, (255, 255, 255)), (300, 220))

    manager.draw_ui(screen)

    if result_text:
        current_font_size = int(text_size_slider.get_current_value())
        res_font = pygame.font.SysFont("dejavusans", current_font_size)
        res_surface = res_font.render(result_text, True, (100, 255, 100))
        screen.blit(res_surface, (WIDTH//2 - res_surface.get_width()//2, 500))

    if funny_comment:
        com_surface = font_small.render(funny_comment, True, (200, 200, 200))
        screen.blit(com_surface, (WIDTH//2 - com_surface.get_width()//2, 560))

    for p in particles[:]:
        p.update()
        p.draw(screen)
        if p.life <= 0:
            particles.remove(p)

    pygame.display.flip()

pygame.quit()
sys.exit()
