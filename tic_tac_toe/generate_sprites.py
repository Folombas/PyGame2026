import pygame
import os

pygame.init()
os.makedirs("assets/sprites", exist_ok=True)

def create_neon_sprite(symbol, color):
    size = 128
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Мощное свечение (рисуем много слоев)
    for radius in range(30, 0, -2):
        alpha = int(5 * (1 - radius/30))
        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        if symbol == 'X':
            pygame.draw.line(glow_surf, (*color, alpha), (20, 20), (108, 108), 10)
            pygame.draw.line(glow_surf, (*color, alpha), (108, 20), (20, 108), 10)
        else:
            pygame.draw.circle(glow_surf, (*color, alpha), (64, 64), 45, 10)
        surface.blit(glow_surf, (0, 0))
    
    # Основная фигура
    if symbol == 'X':
        pygame.draw.line(surface, color, (20, 20), (108, 108), 10)
        pygame.draw.line(surface, color, (108, 20), (20, 108), 10)
        # Внутренний белый блик
        pygame.draw.line(surface, (255, 255, 255), (30, 30), (98, 98), 3)
        pygame.draw.line(surface, (255, 255, 255), (98, 30), (30, 98), 3)
    else:
        pygame.draw.circle(surface, color, (64, 64), 45, 10)
        pygame.draw.circle(surface, (255, 255, 255), (64, 64), 45, 3)
    
    return surface

x_sprite = create_neon_sprite('X', (0, 255, 255))
o_sprite = create_neon_sprite('O', (255, 50, 150))

pygame.image.save(x_sprite, "assets/sprites/x.png")
pygame.image.save(o_sprite, "assets/sprites/o.png")
print("Новые жирные спрайты X и O сгенерированы!")
