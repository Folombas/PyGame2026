"""Система крафта. Рецепты + логика."""
import pygame
from settings import *
from blocks import PLANKS, BRICK, DOOR
from tools import PICKAXE, AXE, SWORD, BOW


# Рецепты: {id: {"name", "inputs": {item: count}, "output": (item, count)}}
# item может быть ID блока (int) или ID инструмента (str)
RECIPES = [
    {
        "id": "planks",
        "name": "Доски x4",
        "inputs": {1: 1},          # 1 = DIRT (пока используем как "бревно" — упрощённо)
        "output": (PLANKS, 4),
    },
    {
        "id": "brick",
        "name": "Кирпич x2",
        "inputs": {3: 2},          # 3 = STONE
        "output": (BRICK, 2),
    },
    {
        "id": "door",
        "name": "Дверь x1",
        "inputs": {PLANKS: 6},
        "output": (DOOR, 1),
    },
]


class CraftingUI:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.open = False
        self.hovered = -1
        self.flash_timer = 0     # подсветка успешного крафта
        self.flash_recipe = -1
        self.error_timer = 0     # подсветка ошибки
        self.error_recipe = -1

    def toggle(self):
        self.open = not self.open
        self.hovered = -1

    def handle_mouse(self, mouse_pos, clicked, inventory):
        """Возвращает True если крафт был произведён."""
        if not self.open:
            return False

        mx, my = mouse_pos
        self.hovered = -1

        for i, recipe in enumerate(RECIPES):
            rect = self._recipe_rect(i)
            if rect.collidepoint(mx, my):
                self.hovered = i
                if clicked:
                    if self._try_craft(recipe, inventory):
                        self.flash_timer = 12
                        self.flash_recipe = i
                        return True
                    else:
                        self.error_timer = 15
                        self.error_recipe = i
        return False

    def _recipe_rect(self, i):
        w, h = 360, 64
        x = (WIDTH - w) // 2
        y = 180 + i * (h + 10)
        return pygame.Rect(x, y, w, h)

    def _try_craft(self, recipe, inventory):
        # проверяем ресурсы (только блоки в инвентаре)
        for item, need in recipe["inputs"].items():
            have = self._count_in_inventory(inventory, item)
            if have < need:
                return False
        # списываем
        for item, need in recipe["inputs"].items():
            self._remove_from_inventory(inventory, item, need)
        # добавляем
        out_item, out_cnt = recipe["output"]
        self._add_to_inventory(inventory, out_item, out_cnt)
        return True

    def _count_in_inventory(self, inv, item_id):
        total = 0
        for slot in inv.slots:
            if slot and slot.get("type") == item_id:
                total += slot.get("count", 0)
        return total

    def _remove_from_inventory(self, inv, item_id, count):
        for slot in inv.slots:
            if not slot or slot.get("type") != item_id:
                continue
            take = min(count, slot["count"])
            slot["count"] -= take
            count -= take
            if slot["count"] <= 0:
                idx = inv.slots.index(slot)
                inv.slots[idx] = None
            if count <= 0:
                break

    def _add_to_inventory(self, inv, item_id, count):
        for slot in inv.slots:
            if slot and slot.get("type") == item_id:
                slot["count"] += count
                return True
        for i in range(len(inv.slots)):
            if inv.slots[i] is None:
                inv.slots[i] = {"type": item_id, "count": count}
                return True
        return False

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.error_timer > 0:
            self.error_timer -= 1

    def draw(self, screen, inventory):
        if not self.open:
            return

        # затемнение
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 180))
        screen.blit(veil, (0, 0))

        # заголовок
        title = self.font_big.render("🔨 КРАФТ", True, NEON_YELLOW if 'NEON_YELLOW' in dir() else (255, 240, 120))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        hint = self.font_small.render("C — закрыть   ЛКМ — скрафтить", True, (180, 180, 200))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 140))

        for i, recipe in enumerate(RECIPES):
            rect = self._recipe_rect(i)
            can_craft = True
            for item, need in recipe["inputs"].items():
                if self._count_in_inventory(inventory, item) < need:
                    can_craft = False
                    break

            # цвет
            if self.error_timer > 0 and self.error_recipe == i:
                bg = (100, 30, 30)
            elif self.flash_timer > 0 and self.flash_recipe == i:
                bg = (30, 100, 40)
            elif self.hovered == i:
                bg = (60, 50, 90)
            else:
                bg = (30, 25, 50)

            border = (200, 200, 220) if self.hovered == i else (100, 90, 130)
            if not can_craft:
                border = (100, 60, 60)
            pygame.draw.rect(screen, bg, rect)
            pygame.draw.rect(screen, border, rect, 2)

            # название
            name_col = (240, 240, 255) if can_craft else (150, 100, 100)
            name = self.font_big.render(recipe["name"], True, name_col)
            screen.blit(name, (rect.x + 14, rect.y + 8))

            # список ингредиентов
            ingr_parts = []
            for item, need in recipe["inputs"].items():
                have = self._count_in_inventory(inventory, item)
                mark = "✓" if have >= need else "✗"
                ingr_parts.append(f"{mark} {need}x блок#{item} ({have})")
            ingr = self.font_small.render(" ".join(ingr_parts), True, (180, 180, 200))
            screen.blit(ingr, (rect.x + 14, rect.y + 38))


def count_block(inventory, block_id):
    """Сколько блоков данного типа в инвентаре."""
    total = 0
    for slot in inventory.slots:
        if slot and slot.get("type") == block_id:
            total += slot.get("count", 0)
    return total
