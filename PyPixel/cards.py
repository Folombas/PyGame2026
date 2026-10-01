"""Коллекционные карточки культа Золотого Телёнка и Знака Доллара."""
import random
import pygame

# ---------- РЕДКОСТИ ----------
RARITY = {
    "common":    {"name": "Обычная",     "color": (160, 160, 180), "glow": (200, 200, 220)},
    "uncommon":  {"name": "Необычная",   "color": (80, 200, 100),  "glow": (140, 240, 140)},
    "rare":      {"name": "Редкая",      "color": (80, 140, 240),  "glow": (120, 200, 255)},
    "epic":      {"name": "Эпическая",   "color": (170, 90, 240),  "glow": (210, 140, 255)},
    "legendary": {"name": "Легендарная", "color": (245, 200, 60),  "glow": (255, 240, 130)},
    "mythic":    {"name": "Мифическая",  "color": (240, 70, 200),  "glow": (255, 130, 240)},
}

# ---------- 12 КАРТОЧЕК ----------
CARD_DEFS = {
    "copper_coin": {
        "name": "Медяк",
        "rarity": "common",
        "icon": "coin",
        "desc": "Первый медяк культа. Пахнет потом и надеждой.",
        "flavor": "«Начни с малого — и продай дорого.»",
    },
    "novice_pick": {
        "name": "Кирка Послушника",
        "rarity": "common",
        "icon": "pick",
        "desc": "Ею добывают руду, ею же — грехи.",
        "flavor": "«Каждый удар — вклад в будущее.»",
    },
    "trade_mark": {
        "name": "Торговая Марка",
        "rarity": "common",
        "icon": "mark",
        "desc": "Клеймо принадлежности к гильдии.",
        "flavor": "«Имя — тоже товар.»",
    },
    "rusty_charm": {
        "name": "Ржавый Оберег",
        "rarity": "uncommon",
        "icon": "charm",
        "desc": "Отпугивает бедность. Немного.",
        "flavor": "«Ржавчина — тоже металл.»",
    },
    "blood_cash": {
        "name": "Кровь в Кассе",
        "rarity": "uncommon",
        "icon": "blood",
        "desc": "Первая крупная сделка. Помнят все.",
        "flavor": "«Деньги не пахнут — но липнут.»",
    },
    "first_stock": {
        "name": "Первая Акция",
        "rarity": "rare",
        "icon": "chart",
        "desc": "График вверх. Символ восхождения.",
        "flavor": "«Купи страх. Продай жадность.»",
    },
    "black_altar": {
        "name": "Чёрный Алтарь",
        "rarity": "rare",
        "icon": "altar",
        "desc": "Здесь заключают контракты с тьмой.",
        "flavor": "«Подпись — кровью, печать — золотом.»",
    },
    "eye_watcher": {
        "name": "Глаз Наблюдателя",
        "rarity": "epic",
        "icon": "eye",
        "desc": "Видит каждую транзакцию. Всегда.",
        "flavor": "«Рынок не спит. И ты не смей.»",
    },
    "seal_merchant": {
        "name": "Печать Торговца",
        "rarity": "epic",
        "icon": "seal",
        "desc": "Открывает двери, которые лучше не открывать.",
        "flavor": "«Слово дано — цену не вернуть.»",
    },
    "key_temple": {
        "name": "Ключ от Храма",
        "rarity": "legendary",
        "icon": "key",
        "desc": "Только он открывает Золотые Врата.",
        "flavor": "«Верующий платит дважды.»",
    },
    "calf_statue": {
        "name": "Золотой Телёнок",
        "rarity": "legendary",
        "icon": "calf",
        "desc": "Идол культа. Молчит — но слышит.",
        "flavor": "«Всё продаётся. Кроме веры.»",
    },
    "dollar_sign": {
        "name": "Знак Доллара $",
        "rarity": "mythic",
        "icon": "dollar",
        "desc": "Печать главной ереси. Врата всех сделок.",
        "flavor": "«Он — Альфа и Омега рынка.»",
    },
}

# ---------- ДРОП ----------
DROPS = {
    "enemy":  ["copper_coin", "novice_pick", "trade_mark", "rusty_charm"],
    "ore":    ["copper_coin", "trade_mark", "blood_cash", "black_altar"],
    "gold":   ["first_stock", "eye_watcher", "seal_merchant", "key_temple"],
    "apple":  ["copper_coin", "novice_pick", "rusty_charm"],
    "boss":   ["calf_statue", "dollar_sign", "key_temple", "seal_merchant"],
}
DROP_CHANCE = {
    "enemy": 0.15,
    "ore":   0.12,
    "gold":  0.40,
    "apple": 0.06,
    "boss":  1.00,
}


def roll_card(source, owned):
    """Кидает кубик. Возвращает id карточки или None."""
    if random.random() > DROP_CHANCE.get(source, 0.1):
        return None
    pool = DROPS.get(source, [])
    if not pool:
        return None
    # приоритет тем, которых ещё нет
    new_ones = [c for c in pool if c not in owned]
    if new_ones and random.random() < 0.7:
        return random.choice(new_ones)
    return random.choice(pool)


# ---------- ИКОНКИ (программно) ----------
def draw_card_icon(surface, icon_id, rect):
    """Рисует пиксельную иконку внутри rect (квадратный)."""
    cx, cy = rect.centerx, rect.centery
    r = min(rect.w, rect.h) // 2 - 6

    if icon_id == "coin":
        pygame.draw.circle(surface, (200, 130, 60), (cx, cy), r)
        pygame.draw.circle(surface, (240, 180, 100), (cx, cy), r, 2)
        pygame.draw.circle(surface, (120, 70, 30), (cx, cy), r - 4, 1)
        # символ $
        for dy in (-r//2, 0, r//2):
            pygame.draw.line(surface, (120, 70, 30),
                             (cx - r//3, cy + dy), (cx + r//3, cy + dy), 2)

    elif icon_id == "pick":
        pygame.draw.rect(surface, (140, 90, 55), (cx - 2, cy - r + 6, 4, r + 6))
        pygame.draw.rect(surface, (220, 230, 240), (cx - r, cy - r, 2*r, 5))

    elif icon_id == "mark":
        pygame.draw.rect(surface, (100, 60, 40), (cx - r, cy - r, 2*r, 2*r))
        pygame.draw.rect(surface, (200, 150, 90), (cx - r + 3, cy - r + 3, 2*r - 6, 2*r - 6), 2)
        pygame.draw.circle(surface, (240, 200, 100), (cx, cy), r // 2)

    elif icon_id == "charm":
        pygame.draw.circle(surface, (140, 90, 50), (cx, cy), r)
        pygame.draw.circle(surface, (80, 40, 25), (cx, cy), r - 4, 3)
        pygame.draw.line(surface, (200, 120, 60), (cx, cy - r), (cx, cy + r), 2)

    elif icon_id == "blood":
        for dx, dy in [(0, -6), (-4, 2), (4, 2), (0, 8)]:
            pygame.draw.circle(surface, (200, 30, 40), (cx + dx, cy + dy), 5)
        pygame.draw.circle(surface, (140, 15, 25), (cx, cy + 2), 3)

    elif icon_id == "chart":
        # столбики графика
        for i, h in enumerate([8, 14, 10, 20, 26]):
            x = cx - r + i * (r // 3) + 2
            pygame.draw.rect(surface, (80, 200, 100), (x, cy + r - h, 4, h))
        pygame.draw.line(surface, (255, 220, 80), (cx - r, cy), (cx + r, cy - r // 2), 2)

    elif icon_id == "altar":
        pygame.draw.rect(surface, (30, 20, 35), (cx - r, cy, 2*r, r))
        pygame.draw.rect(surface, (60, 40, 70), (cx - r + 4, cy - 4, 2*r - 8, 6))
        pygame.draw.circle(surface, (200, 100, 240), (cx, cy - 6), 4)

    elif icon_id == "eye":
        pygame.draw.ellipse(surface, (240, 240, 255), (cx - r, cy - r // 2, 2*r, r))
        pygame.draw.circle(surface, (200, 60, 100), (cx, cy), r // 2)
        pygame.draw.circle(surface, (20, 15, 30), (cx, cy), r // 3)
        pygame.draw.circle(surface, (255, 255, 255), (cx - 2, cy - 2), 2)

    elif icon_id == "seal":
        pygame.draw.circle(surface, (150, 40, 60), (cx, cy), r)
        pygame.draw.circle(surface, (230, 90, 130), (cx, cy), r - 3, 3)
        # $ по центру
        pygame.draw.line(surface, (255, 220, 100), (cx, cy - r//2), (cx, cy + r//2), 3)
        pygame.draw.circle(surface, (255, 220, 100), (cx, cy - r//3), r//4, 2)
        pygame.draw.circle(surface, (255, 220, 100), (cx, cy + r//3), r//4, 2)

    elif icon_id == "key":
        pygame.draw.circle(surface, (240, 200, 60), (cx - r//2, cy), r//2, 4)
        pygame.draw.rect(surface, (240, 200, 60), (cx, cy - 3, r, 6))
        pygame.draw.rect(surface, (240, 200, 60), (cx + r//2, cy, 3, 8))
        pygame.draw.rect(surface, (240, 200, 60), (cx + r - 8, cy, 3, 8))

    elif icon_id == "calf":
        # тело
        pygame.draw.ellipse(surface, (240, 200, 60), (cx - r, cy - r//2, 2*r, r + 4))
        # голова
        pygame.draw.circle(surface, (245, 210, 80), (cx - r - 2, cy - r//3), r//2)
        # рога
        pygame.draw.line(surface, (240, 220, 120), (cx - r - 4, cy - r//2 - 2), (cx - r, cy - r), 2)
        pygame.draw.line(surface, (240, 220, 120), (cx - r + 2, cy - r//2 - 2), (cx - r + 4, cy - r), 2)
        # глаз
        pygame.draw.circle(surface, (30, 20, 20), (cx - r - 3, cy - r//3), 2)
        # хвост
        pygame.draw.line(surface, (200, 160, 50), (cx + r, cy - 4), (cx + r + 4, cy - 10), 2)

    elif icon_id == "dollar":
        # крупный $
        c = (245, 220, 80)
        w = 6
        # верх
        pygame.draw.rect(surface, c, (cx - r//2, cy - r, r, w))
        pygame.draw.rect(surface, c, (cx - r//2, cy - r, w, r//2))
        # середина
        pygame.draw.rect(surface, c, (cx - r//2, cy - w//2, r, w))
        # низ
        pygame.draw.rect(surface, c, (cx - r//2, cy + r - w, r, w))
        pygame.draw.rect(surface, c, (cx + r//2 - w, cy, w, r))
        # вертикальная
        pygame.draw.rect(surface, c, (cx - 3, cy - r - 4, 6, 2*r + 8))
