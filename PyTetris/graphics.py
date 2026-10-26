import os
import pygame
from settings import CELL, COLORS

class BlockRenderer:
    def __init__(self, assets_dir="assets/blocks"):
        self.sprites = {}
        self.use_sprites = False
        try:
            for kind in ["I", "J", "L", "O", "S", "T", "Z"]:
                path = os.path.join(assets_dir, f"{kind}.png")
                img = pygame.image.load(path).convert_alpha()
                # Масштабируем под размер клетки с небольшим отступом
                img = pygame.transform.scale(img, (CELL - 2, CELL - 2))
                self.sprites[kind] = img
            self.use_sprites = True
            print("✅ Спрайты блоков успешно загружены")
        except Exception as e:
            print(f"⚠️ Спрайты не загружены, используется цветной fallback: {e}")

    def draw_block(self, surf, x, y, kind, glow=0.0):
        if self.use_sprites and kind in self.sprites:
            surf.blit(self.sprites[kind], (x + 1, y + 1))
        else:
            # Fallback: рисуем цветной квадрат как раньше
            color = COLORS.get(kind, (255, 255, 255))
            rect = pygame.Rect(x + 1, y + 1, CELL - 2, CELL - 2)
            pygame.draw.rect(surf, color, rect, border_radius=4)
            hi = tuple(min(255, c + 60) for c in color)
            pygame.draw.rect(surf, hi, rect, 1, border_radius=4)
