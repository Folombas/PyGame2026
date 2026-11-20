# generate_sprites.py
import pygame
import os

pygame.init()
os.makedirs("assets/sprites", exist_ok=True)

def create_neon_sprite(symbol, color):
    size = 128
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Свечение (рисуем несколько слоев с прозрачностью)
    for radius in range(20, 0, -2):
        alpha = int(10 * (1 - radius/20))
        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        if symbol == 'X':
            pygame.draw.line(glow_surf, (*color, alpha), (30, 30), (98, 98), 6)
            pygame.draw.line(glow_surf, (*color, alpha), (98, 30), (30, 98), 6)
        else:
            pygame.draw.circle(glow_surf, (*color, alpha), (64, 64), 40, 6)
        surface.blit(glow_surf, (0, 0))
    
    # Основная фигура
    if symbol == 'X':
        pygame.draw.line(surface, color, (30, 30), (98, 98), 6)
        pygame.draw.line(surface, color, (98, 30), (30, 98), 6)
    else:
        pygame.draw.circle(surface, color, (64, 64), 40, 6)
    
    return surface

# Создаем спрайты
x_sprite = create_neon_sprite('X', (0, 255, 255))  # Cyan
o_sprite = create_neon_sprite('O', (255, 50, 150)) # Pink

pygame.image.save(x_sprite, "assets/sprites/x.png")
pygame.image.save(o_sprite, "assets/sprites/o.png")
print("Спрайты X и O успешно сгенерированы!")
