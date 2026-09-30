"""Инвентарь — хотбар из 10 слотов."""
from blocks import BLOCKS

SLOTS = 10


class Inventory:
    def __init__(self):
        self.slots = [None] * SLOTS    # каждый: {"type": int, "count": int}
        self.selected = 0

    def select(self, idx):
        if 0 <= idx < SLOTS:
            self.selected = idx

    def cycle(self, direction):
        self.selected = (self.selected + direction) % SLOTS

    def add(self, block_type, count=1):
        if block_type not in BLOCKS:
            return False
        # сначала докидываем в существующий стак
        for slot in self.slots:
            if slot and slot["type"] == block_type:
                slot["count"] += count
                return True
        # иначе — в пустой
        for i in range(SLOTS):
            if self.slots[i] is None:
                self.slots[i] = {"type": block_type, "count": count}
                return True
        return False   # инвентарь полон

    def take_selected(self, count=1):
        slot = self.slots[self.selected]
        if not slot or slot["count"] < count:
            return None
        t = slot["type"]
        slot["count"] -= count
        if slot["count"] <= 0:
            self.slots[self.selected] = None
        return t

    def selected_type(self):
        slot = self.slots[self.selected]
        return slot["type"] if slot else None

    def selected_count(self):
        slot = self.slots[self.selected]
        return slot["count"] if slot else 0
