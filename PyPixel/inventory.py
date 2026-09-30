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
            if slot and slot.get("type") == block_type:
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
        if not slot or "tool" in slot or slot.get("count", 0) < count:
            return None
        t = slot["type"]
        slot["count"] -= count
        if slot["count"] <= 0:
            self.slots[self.selected] = None
        return t

# ---------- ИНСТРУМЕНТЫ ----------
    def add_tool(self, tool_id):
        # уже есть?
        for slot in self.slots:
            if slot and slot.get("tool") == tool_id:
                return True
        for i in range(SLOTS):
            if self.slots[i] is None:
                self.slots[i] = {"tool": tool_id}
                return True
        return False

    def selected_tool(self):
        slot = self.slots[self.selected]
        if slot and "tool" in slot:
            return slot["tool"]
        return None

    def selected_is_tool(self):
        slot = self.slots[self.selected]
        return bool(slot and "tool" in slot)

    def selected_type(self):
        slot = self.slots[self.selected]
        return slot["type"] if slot else None

    def selected_count(self):
        slot = self.slots[self.selected]
        return slot["count"] if slot else 0
