"""Создаёт PNG с пронумерованными тайлами из спрайт-листа.
Открой результат в просмотрщике — увидишь где какой тайл."""
import sys
import pygame

pygame.init()
# Невидимое окно — нужно для convert_alpha()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

if len(sys.argv) < 2:
    print("Использование: python preview_tiles.py <путь_к_спрайт-листу> [tile_size]")
    print("Пример: python preview_tiles.py assets/tilesets/floor.png 16")
    sys.exit(1)

path = sys.argv[1]
tile_size = int(sys.argv[2]) if len(sys.argv) > 2 else 16

sheet = pygame.image.load(path).convert_alpha()
cols = sheet.get_width() // tile_size
rows = sheet.get_height() // tile_size

# Размер ячейки в превью
CELL = 40
pad = 16
label_h = 12

W = cols * CELL + pad * 2
H = rows * CELL + pad * 2

surf = pygame.Surface((W, H))
surf.fill((30, 30, 40))

font = pygame.font.SysFont("monospace", 9)

for ty in range(rows):
    for tx in range(cols):
        # Вырезаем тайл
        rect = pygame.Rect(tx * tile_size, ty * tile_size, tile_size, tile_size)
        tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        tile.blit(sheet, (0, 0), rect)
        # Масштабируем до CELL×CELL
        tile = pygame.transform.scale(tile, (CELL, CELL))

        x = pad + tx * CELL
        y = pad + ty * CELL
        surf.blit(tile, (x, y))
        # Рамка
        pygame.draw.rect(surf, (60, 60, 80), (x, y, CELL, CELL), 1)
        # Координаты
        label = font.render(f"{tx},{ty}", True, (255, 220, 80))
        # Фон под текст
        lb = pygame.Surface((label.get_width(), label.get_height()))
        lb.fill((0, 0, 0))
        surf.blit(lb, (x + 2, y + 2))
        surf.blit(label, (x + 2, y + 2))

# Заголовок
head = pygame.font.SysFont("monospace", 14, bold=True)
t = head.render(f"{path}  ·  tile {tile_size}px  ·  grid {cols}x{rows}", True, (200, 255, 200))
surf2 = pygame.Surface((max(W, t.get_width() + 20), H + 30))
surf2.fill((20, 20, 28))
surf2.blit(t, (10, 6))
surf2.blit(surf, (0, 30))

out = path.replace(".png", "_preview.png")
pygame.image.save(surf2, out)
print(f"✓ Сохранено: {out}")
print(f"  Открой в просмотрщике: xdg-open {out}")
