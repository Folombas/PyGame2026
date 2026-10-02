"""Квесты — цели, дающие смысл игре."""
import pygame


QUESTS = [
    {
        "id": "first_dig",
        "title": "Копнуть вглубь",
        "desc": "Скопать 10 блоков",
        "target": 10,
        "tracker": "blocks_dug",
        "reward": 100,
    },
    {
        "id": "find_chest",
        "title": "Кладоискатель",
        "desc": "Открыть 1 сундук",
        "target": 1,
        "tracker": "chests_opened",
        "reward": 200,
    },
    {
        "id": "hunter",
        "title": "Охотник",
        "desc": "Убить 5 врагов",
        "target": 5,
        "tracker": "kills",
        "reward": 150,
    },
    {
        "id": "diver",
        "title": "Исследователь глубин",
        "desc": "Спуститься на 30м",
        "target": 30,
        "tracker": "max_depth",
        "reward": 300,
    },
    {
        "id": "collector",
        "title": "Коллекционер",
        "desc": "Собрать 3 карточки культа",
        "target": 3,
        "tracker": "cards_count",
        "reward": 500,
    },
    {
        "id": "swimmer",
        "title": "Пловец",
        "desc": "Провести под водой 30 секунд",
        "target": 30,
        "tracker": "seconds_underwater",
        "reward": 250,
    },
    {
        "id": "scuba",
        "title": "Аквалангист",
        "desc": "Активировать акваланг",
        "target": 1,
        "tracker": "scuba_used",
        "reward": 100,
    },
]


class QuestUI:
    def __init__(self, font_big, font_small):
        self.font_big = font_big
        self.font_small = font_small
        self.completed = set()
        self.timer = 0
        self.flash_timer = 0
        self.flash_quest = None

    def update(self):
        self.timer += 1
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def check(self, stats):
        """Проверяет квесты, возвращает список новых выполненных."""
        newly = []
        for q in QUESTS:
            if q["id"] in self.completed:
                continue
            val = stats.get(q["tracker"], 0)
            if val >= q["target"]:
                self.completed.add(q["id"])
                newly.append(q)
        if newly:
            self.flash_quest = newly[0]["title"]
            self.flash_timer = 180
        return newly

    def get_current(self):
        """Возвращает активный квест (первый невыполненный)."""
        for q in QUESTS:
            if q["id"] not in self.completed:
                return q
        return None

    def draw_sidebar(self, screen, stats, difficulty_label):
        """Мини-панель активного квеста в левом верхнем углу."""
        q = self.get_current()
        if not q:
            # все выполнены
            txt = self.font_small.render("✅ Все квесты выполнены!", True, (100, 240, 130))
            screen.blit(txt, (14, 118))
            return

        cur = stats.get(q["tracker"], 0)
        prog = min(1.0, cur / q["target"])

        # фон
        box_w, box_h = 320, 60
        x, y = 14, 116
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((20, 15, 40, 210))
        pygame.draw.rect(bg, (255, 220, 80, 255), (0, 0, box_w, box_h), 2)
        screen.blit(bg, (x, y))

        # иконка слева
        pygame.draw.circle(screen, (255, 220, 80), (x + 22, y + 30), 14)
        pygame.draw.circle(screen, (255, 255, 255), (x + 22, y + 30), 14, 2)
        q_mark = self.font_big.render("!", True, (60, 40, 20))
        screen.blit(q_mark, (x + 22 - q_mark.get_width() // 2, y + 30 - q_mark.get_height() // 2))

        # название
        title = self.font_small.render(q["title"], True, (255, 240, 120))
        screen.blit(title, (x + 46, y + 6))

        # описание + прогресс
        prog_txt = self.font_small.render(
            f"{q['desc']}  ({min(cur, q['target'])}/{q['target']})",
            True, (220, 220, 240))
        screen.blit(prog_txt, (x + 46, y + 26))

        # прогресс-бар
        bar_x = x + 46
        bar_y = y + 44
        bar_w = box_w - 60
        bar_h = 6
        pygame.draw.rect(screen, (40, 40, 60), (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * prog)
        if fill > 0:
            pygame.draw.rect(screen, (100, 240, 130), (bar_x, bar_y, fill, bar_h))

        # всплывашка при завершении
        if self.flash_timer > 0 and self.flash_quest:
            fade = min(1.0, self.flash_timer / 60.0)
            slide = min(1.0, (180 - self.flash_timer) / 20.0)
            bw2, bh2 = 460, 80
            x2 = WIDTH_HALF - bw2 // 2
            y2 = int(-120 + slide * 140)
            box = pygame.Surface((bw2, bh2), pygame.SRCALPHA)
            box.fill((20, 40, 25, int(240 * fade)))
            pygame.draw.rect(box, (100, 240, 130, int(255 * fade)), (0, 0, bw2, bh2), 3)
            t1 = self.font_small.render("✅ КВЕСТ ВЫПОЛНЕН!", True, (100, 240, 130, int(255 * fade)))
            t2 = self.font_big.render(self.flash_quest, True, (255, 255, 255, int(255 * fade)))
            box.blit(t1, (20, 10))
            box.blit(t2, (20, 34))
            screen.blit(box, (x2, y2))


# Костыль для доступа к WIDTH из main
from settings import WIDTH as _W
WIDTH_HALF = _W // 2
