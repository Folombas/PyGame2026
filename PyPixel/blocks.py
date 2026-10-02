"""Типы блоков и их отрисовка."""
import pygame

TILE_SIZE = 32

AIR = 0
DIRT = 1
GRASS = 2
STONE = 3
COPPER = 4
IRON = 5
GOLD = 6
WOOD = 7
LEAVES = 8
SAND = 9
PLANKS = 10
BRICK = 11
DOOR = 12
TORCH = 13
WATER = 14
SNOW = 15

BLOCKS = {
    DIRT:   {"name": "Земля",  "color": (120, 80, 50),  "top": (140, 100, 65), "hardness": 14, "drop": DIRT, "tool": None},
    GRASS:  {"name": "Трава",  "color": (120, 80, 50),  "top": (85, 175, 75),  "hardness": 14, "drop": DIRT, "tool": None},
    STONE:  {"name": "Камень", "color": (110, 100, 95), "top": (130, 120, 115),"hardness": 48, "drop": STONE, "tool": "pickaxe"},
    COPPER: {"name": "Медь",   "color": (110, 100, 95), "top": (180, 110, 60), "hardness": 55, "drop": COPPER, "ore": (200, 120, 60), "tool": "pickaxe"},
    IRON:   {"name": "Железо", "color": (110, 100, 95), "top": (180, 175, 170),"hardness": 75, "drop": IRON,   "ore": (210, 200, 195), "tool": "pickaxe"},
    GOLD:   {"name": "Золото", "color": (110, 100, 95), "top": (230, 200, 80), "hardness": 95, "drop": GOLD,   "ore": (250, 220, 90), "tool": "pickaxe"},
    WOOD:   {"name": "Дерево", "color": (110, 70, 40),  "top": (130, 90, 55),  "hardness": 40, "drop": WOOD, "tool": "axe"},
    LEAVES: {"name": "Листья", "color": (60, 140, 60),  "top": (80, 170, 80),  "hardness": 10, "drop": LEAVES, "tool": "axe"},
    SAND:   {"name": "Песок",  "color": (210, 190, 130),"top": (225, 205, 145),"hardness": 12, "drop": SAND, "tool": None},
    PLANKS: {"name": "Доски",  "color": (150, 100, 60), "top": (170, 120, 75), "hardness": 20, "drop": PLANKS, "tool": "axe"},
    BRICK:  {"name": "Кирпич", "color": (150, 60, 60),  "top": (180, 80, 80),  "hardness": 40, "drop": BRICK,  "tool": "pickaxe"},
    DOOR:   {"name": "Дверь",  "color": (110, 70, 40),  "top": (150, 100, 60), "hardness": 15, "drop": DOOR,   "tool": "axe"},
    TORCH:  {"name": "Факел",  "color": (255, 180, 80), "top": (255, 220, 120),"hardness": 6,  "drop": TORCH,  "tool": None, "light": 220},
    WATER:  {"name": "Вода",   "color": (30, 80, 140),  "top": (60, 140, 200), "hardness": 999, "drop": None,  "tool": None, "liquid": True},
    SNOW:   {"name": "Снег",   "color": (230, 240, 250),"top": (255, 255, 255),"hardness": 8,  "drop": SNOW,  "tool": None},
}


def draw_block(surface, rect, block_type, offset=(0, 0)):
    if block_type == AIR or block_type not in BLOCKS:
        return
    info = BLOCKS[block_type]
    r = pygame.Rect(rect.x - offset[0], rect.y - offset[1], rect.w, rect.h)

    # Кастомная отрисовка факела
    if block_type == TORCH:
        cx = r.centerx
        # палочка
        pygame.draw.rect(surface, (110, 70, 40), (cx - 2, r.y + 10, 4, r.h - 10))
        # пламя — три круга с градиентом
        pygame.draw.circle(surface, (255, 100, 40), (cx, r.y + 8), 7)
        pygame.draw.circle(surface, (255, 180, 60), (cx, r.y + 6), 5)
        pygame.draw.circle(surface, (255, 240, 140), (cx, r.y + 5), 3)
        return

    # тело
    pygame.draw.rect(surface, info["color"], r)
    # верхняя полоска
    pygame.draw.rect(surface, info["top"], (r.x, r.y, r.w, 4))
    # тёмный контур
    dark = tuple(max(0, c - 40) for c in info["color"])
    pygame.draw.rect(surface, dark, r, 1)

    # руда — крапины + свечение
    if "ore" in info:
        ore = info["ore"]
        seed = (r.x * 73 + r.y * 131) & 0xFF

        # Пульсирующее свечение (мягкий круг за крапинами)
        import math as _m
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.7 + 0.3 * _m.sin(t * 3 + seed)
        glow_size = int(14 * pulse)

        # Крапины — 3 штуки, аккуратные
        for i in range(3):
            dx = (seed * (i + 1) * 37) % (r.w - 8) + 4
            dy = (seed * (i + 1) * 53) % (r.h - 8) + 4
            pygame.draw.rect(surface, ore, (r.x + dx, r.y + dy, 4, 4))
            pygame.draw.rect(surface, (255, 255, 240), (r.x + dx, r.y + dy, 1, 1))


def draw_dig_progress(surface, rect, progress, offset=(0, 0)):
    """Трещины на блоке во время копания."""
    if progress <= 0:
        return
    r = pygame.Rect(rect.x - offset[0], rect.y - offset[1], rect.w, rect.h)
    # затемнение
    overlay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(100 * progress)))
    surface.blit(overlay, r.topleft)
    # трещины
    if progress > 0.3:
        pygame.draw.line(surface, (20, 20, 20),
                         (r.x + 8, r.y + 4), (r.x + 16, r.y + 16), 2)
    if progress > 0.6:
        pygame.draw.line(surface, (20, 20, 20),
                         (r.x + 18, r.y + 6), (r.x + 12, r.y + 26), 2)
        pygame.draw.line(surface, (20, 20, 20),
                         (r.x + 4, r.y + 20), (r.x + 24, r.y + 18), 2)
