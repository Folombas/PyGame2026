"""Находит непустые регионы в nature.png — показывает где деревья."""
import pygame

pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

sheet = pygame.image.load("assets/tilesets/nature.png").convert_alpha()
W, H = sheet.get_size()
print(f"Размер листа: {W}×{H} = {W//16}×{H//16} тайлов")

# Разделим на сетку 8×8 (если предположить что дерево 4×4)
# и покажем для каждой ячейки 4×4 — есть ли там пиксели
GRID = 4   # тайла
TILE = 16
print(f"\nАнализ сетки {GRID}×{GRID} тайла ({GRID*TILE}px):\n")

cols = W // (GRID * TILE)
rows = H // (GRID * TILE)

# Ищем регионы с большим количеством непрозрачных пикселей
for gy in range(rows):
    line = ""
    for gx in range(cols):
        rect = pygame.Rect(gx * GRID * TILE, gy * GRID * TILE,
                            GRID * TILE, GRID * TILE)
        # Считаем непрозрачные пиксели
        count = 0
        total = 0
        for yy in range(rect.y, min(rect.y + rect.h, H), 2):
            for xx in range(rect.x, min(rect.x + rect.w, W), 2):
                total += 1
                if sheet.get_at((xx, yy))[3] > 50:
                    count += 1
        ratio = count / total if total else 0
        if ratio > 0.6:
            line += "█"   # плотно заполнено
        elif ratio > 0.3:
            line += "▓"
        elif ratio > 0.1:
            line += "▒"
        elif ratio > 0:
            line += "░"
        else:
            line += "·"
    print(f"y={gy}: {line}")

print()
print("Легенда: █=густо, ▓=средне, ▒=редко, ░=чуть, ·=пусто")
print(f"Каждый символ = {GRID}×{GRID} тайлов ({GRID*TILE}px)")
print("\nКоординаты символа x,y в тайлах = (x*4, y*4)")
