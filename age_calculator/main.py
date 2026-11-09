import pygame
import sys
import random
from datetime import datetime

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Калькулятор возраста папы")
clock = pygame.time.Clock()

BG_COLOR = (30, 30, 40)
TEXT_COLOR = (255, 255, 255)
INPUT_COLOR = (200, 200, 200)
ACTIVE_COLOR = (100, 150, 255)
ERROR_COLOR = (255, 50, 50)

font = pygame.font.SysFont('arial', 32)
small_font = pygame.font.SysFont('arial', 24)
title_font = pygame.font.SysFont('arial', 40, bold=True)

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = INPUT_COLOR
        self.text = text
        self.txt_surface = small_font.render(text, True, (0, 0, 0))
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = ACTIVE_COLOR if self.active else INPUT_COLOR
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(self.text) < 10: 
                        self.text += event.unicode
                self.txt_surface = small_font.render(self.text, True, (0, 0, 0))

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 10))

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

father_input = InputBox(300, 150, 200, 40)
son_input = InputBox(300, 250, 200, 40)
input_boxes = [father_input, son_input]
button_rect = pygame.Rect(300, 350, 200, 50)

particles = []
result_text = ""
result_color = TEXT_COLOR
funny_comment = ""

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        for box in input_boxes:
            box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                try:
                    d1 = datetime.strptime(father_input.text, "%d.%m.%Y")
                    d2 = datetime.strptime(son_input.text, "%d.%m.%Y")
                    
                    years = d2.year - d1.year - ((d2.month, d2.day) < (d1.month, d1.day))
                    
                    if years < 0:
                        result_text = "Сын родился раньше отца? О_о"
                        result_color = ERROR_COLOR
                        funny_comment = "Машина времени изобретена!"
                    else:
                        result_text = f"Отцу было {years} лет!"
                        result_color = (100, 255, 100)
                        
                        if years < 18:
                            funny_comment = "Ого, папа был совсем юным!"
                        elif 18 <= years < 30:
                            funny_comment = "Классика жанра!"
                        elif 30 <= years < 45:
                            funny_comment = "Папа уже был солидным мужчиной."
                        else:
                            funny_comment = "Папа был мудрым человеком с опытом!"

                        for _ in range(150):
                            particles.append(Particle(WIDTH//2, 450))
                except ValueError:
                    result_text = "Ошибка! Введи дату как ДД.ММ.ГГГГ"
                    result_color = ERROR_COLOR
                    funny_comment = "Даже ИИ не понял этот формат..."

    screen.fill(BG_COLOR)

    title_surface = title_font.render("Когда папа стал папой?", True, (255, 200, 50))
    screen.blit(title_surface, (WIDTH//2 - title_surface.get_width()//2, 40))

    screen.blit(small_font.render("Дата рождения ОТЦА (ДД.ММ.ГГГГ):", True, TEXT_COLOR), (300, 120))
    screen.blit(small_font.render("Дата рождения СЫНА (ДД.ММ.ГГГГ):", True, TEXT_COLOR), (300, 220))

    for box in input_boxes:
        box.draw(screen)

    pygame.draw.rect(screen, (50, 200, 50), button_rect, border_radius=10)
    btn_text = font.render("РАССЧИТАТЬ", True, (255, 255, 255))
    screen.blit(btn_text, (button_rect.x + 20, button_rect.y + 10))

    if result_text:
        res_surface = font.render(result_text, True, result_color)
        screen.blit(res_surface, (WIDTH//2 - res_surface.get_width()//2, 450))
    if funny_comment:
        com_surface = small_font.render(funny_comment, True, (200, 200, 200))
        screen.blit(com_surface, (WIDTH//2 - com_surface.get_width()//2, 500))

    for p in particles[:]:
        p.update()
        p.draw(screen)
        if p.life <= 0:
            particles.remove(p)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
