import pygame
import os

pygame.init()
os.makedirs("assets/sprites", exist_ok=True)

def create_3d_sprite(symbol, color):
    # Создаем в 4 раза больше, чтобы потом уменьшить и получить сглаживание (Anti-Aliasing)
    size = 512
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    offset = 120 # Размер фигуры
    thickness = 40

    # 1. Тень
    shadow_offset = 15
    if symbol == 'X':
        pygame.draw.line(surface, (0, 0, 0, 150), (center-offset+shadow_offset, center-offset+shadow_offset), (center+offset+shadow_offset, center+offset+shadow_offset), thickness)
        pygame.draw.line(surface, (0, 0, 0, 150), (center+offset+shadow_offset, center-offset+shadow_offset), (center-offset+shadow_offset, center+offset+shadow_offset), thickness)
    else:
        pygame.draw.circle(surface, (0, 0, 0, 150), (center+shadow_offset, center+shadow_offset), offset, thickness)

    # 2. Внешнее неоновое свечение (рисуем несколько слоев)
    for i in range(20, 0, -2):
        alpha = int(10 * (1 - i/20))
        glow_color = (*color, alpha)
        if symbol == 'X':
            pygame.draw.line(surface, glow_color, (center-offset, center-offset), (center+offset, center+offset), thickness + i*2)
            pygame.draw.line(surface, glow_color, (center+offset, center-offset), (center-offset, center+offset), thickness + i*2)
        else:
            pygame.draw.circle(surface, glow_color, (center, center), offset + i, thickness + i*2)

    # 3. Основная фигура
    if symbol == 'X':
        pygame.draw.line(surface, color, (center-offset, center-offset), (center+offset, center+offset), thickness)
        pygame.draw.line(surface, color, (center+offset, center-offset), (center-offset, center+offset), thickness)
    else:
        pygame.draw.circle(surface, color, (center, center), offset, thickness)

    # 4. Блик (чтобы было 3D)
    highlight_color = (min(255, color[0]+100), min(255, color[1]+100), min(255, color[2]+100))
    if symbol == 'X':
        pygame.draw.line(surface, highlight_color, (center-offset, center-offset), (center+offset, center+offset), thickness // 3)
        pygame.draw.line(surface, highlight_color, (center+offset, center-offset), (center-offset, center+offset), thickness // 3)
    else:
        # Для круга рисуем дугу сверху слева
        pygame.draw.arc(surface, highlight_color, (center-offset, center-offset, offset*2, offset*2), 0.5, 2.5, thickness // 3)

    # Уменьшаем до 128x128 с плавным сглаживанием
    final_surface = pygame.transform.smoothscale(surface, (128, 128))
    return final_surface

print("Генерация 3D-спрайтов...")
x_sprite = create_3d_sprite('X', (0, 255, 255))    # Неоновый голубой
o_sprite = create_3d_sprite('O', (255, 50, 150))   # Неоновый розовый

pygame.image.save(x_sprite, "assets/sprites/x_3d.png")
pygame.image.save(o_sprite, "assets/sprites/o_3d.png")
print("Успех! Спрайты x_3d.png и o_3d.png созданы в assets/sprites/")
