"""Достижения. Открывается на J."""
import pygame

# id: {name, desc, target, reward (карта/очки)}
ACHIEVEMENTS = {
    "first_dig":        {"name": "Первая копка",          "desc": "Скопать 1 блок",              "target": 1,   "reward": 10},
    "digger":           {"name": "Копатель",              "desc": "Скопать 50 блоков",           "target": 50,  "reward": 100},
    "miner":            {"name": "Шахтёр",                "desc": "Скопать 500 блоков",          "target": 500, "reward": 1000},
    "woodcutter":       {"name": "Дровосек",              "desc": "Срубить 10 деревьев",         "target": 10,  "reward": 150},
    "hunter":           {"name": "Охотник",               "desc": "Убить 10 врагов",             "target": 10,  "reward": 200},
    "slayer":           {"name": "Истребитель",           "desc": "Убить 100 врагов",            "target": 100, "reward": 1500},
    "archer":           {"name": "Стрелок",               "desc": "Попасть из лука 20 раз",      "target": 20,  "reward": 300},
    "apple_lover":      {"name": "Любитель яблок",        "desc": "Собрать 50 яблок",            "target": 50,  "reward": 250},
    "explorer":         {"name": "Путешественник",        "desc": "Пройти 1000 метров",          "target": 1000,"reward": 500},
    "deep_diver":       {"name": "Глубоко копающий",      "desc": "Спуститься на 500м",          "target": 500, "reward": 800},
    "collector_3":      {"name": "Коллекционер",          "desc": "Собрать 3 карточки культа",   "target": 3,   "reward": 0},
    "collector_6":      {"name": "Продвинутый коллекционер","desc": "Собрать 6 карточек культа","target": 6,   "reward": 0},
    "collector_all":    {"name": "Адепт Золотого Телёнка","desc": "Собрать ВСЕ 12 карточек",     "target": 12,  "reward": 0},
    "boss_slayer":      {"name": "Убийца босса",          "desc": "Победить босса",              "target": 1,   "reward": 1000},
    "philanthropist":   {"name": "Фермер",                "desc": "Собрать 100 яблок",           "target": 100, "reward": 600},
}

# Какая статистика из L соответствует достижению
TRACKER = {
    "first_dig":        "blocks_dug",
    "digger":           "blocks_dug",
    "miner":            "blocks_dug",
    "woodcutter":       "trees_chopped",
    "hunter":           "kills",
    "slayer":           "kills",
    "archer":           "arrows_hit",
    "apple_lover":      "apples",
    "explorer":         "max_x",
    "deep_diver":       "max_depth",
    "collector_3":      "cards_count",
    "collector_6":      "cards_count",
    "collector_all":    "cards_count",
    "boss_slayer":      "boss_killed",
    "philanthropist":   "apples",
}


class AchievementsUI:
    def __init__(self, font_big, font_small):
        self.open = False
        self.font_big = font_big
        self.font_small = font_small
        self.selected = 0
        self.timer = 0

    def toggle(self):
        self.open = not self.open

    def update(self):
        if self.open:
            self.timer += 1

    def handle_event(self, event):
        if not self.open:
            return False
        if event.type != pygame.KEYDOWN:
            return False
        ids = list(ACHIEVEMENTS.keys())
        if event.key in (pygame.K_ESCAPE, pygame.K_j):
            self.open = False
            return True
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(ids)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(ids)
        return True

    def check_unlocks(self, stats, unlocked_set):
        """Проверяет условия достижений, возвращает список новых."""
        new_unlocked = []
        for aid, ach in ACHIEVEMENTS.items():
            if aid in unlocked_set:
                continue
            tracker_key = TRACKER.get(aid)
            if not tracker_key:
                continue
            value = stats.get(tracker_key, 0)
            if value >= ach["target"]:
                unlocked_set.add(aid)
                new_unlocked.append(aid)
        return new_unlocked

    def draw(self, screen, stats, unlocked):
        if not self.open:
            return
        W, H = screen.get_size()
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((5, 3, 15, 230))
        screen.blit(veil, (0, 0))

        title = self.font_big.render("🏆 ДОСТИЖЕНИЯ", True, (255, 220, 80))
        screen.blit(title, (W // 2 - title.get_width() // 2, 24))

        total = len(ACHIEVEMENTS)
        have = len(unlocked)
        sub = self.font_small.render(
            f"Получено: {have} / {total}", True, (200, 200, 220))
        screen.blit(sub, (W // 2 - sub.get_width() // 2, 60))

        hint = self.font_small.render("J / Esc — закрыть    ↑↓ — выбрать", True, (140, 140, 170))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

        # Левая колонка — список
        list_w = 500
        list_x = 60
        list_y = 100
        row_h = 50
        ids = list(ACHIEVEMENTS.keys())

        for i, aid in enumerate(ids):
            row_y = list_y + i * (row_h + 4)
            rect = pygame.Rect(list_x, row_y, list_w, row_h)
            ach = ACHIEVEMENTS[aid]
            got = aid in unlocked
            tracker_key = TRACKER.get(aid)
            value = stats.get(tracker_key, 0)
            progress = min(1.0, value / ach["target"]) if ach["target"] > 0 else 0

            # фон
            if i == self.selected:
                bg = (60, 50, 100)
            elif got:
                bg = (30, 50, 35)
            else:
                bg = (22, 20, 40)
            pygame.draw.rect(screen, bg, rect)
            border = (255, 220, 80) if got else (90, 80, 130)
            if i == self.selected:
                border = (255, 255, 255)
            pygame.draw.rect(screen, border, rect, 2)

            # галочка/замок
            mark = "✓" if got else "🔒"
            m = self.font_big.render(mark, True, (100, 240, 120) if got else (120, 120, 140))
            screen.blit(m, (rect.x + 8, rect.y + 8))

            # название
            name_col = (255, 240, 150) if got else (220, 220, 240)
            nm = self.font_big.render(ach["name"], True, name_col)
            screen.blit(nm, (rect.x + 44, rect.y + 4))

            # описание + прогресс
            desc = self.font_small.render(ach["desc"], True, (170, 170, 200))
            screen.blit(desc, (rect.x + 44, rect.y + 28))

            # прогресс-бар справа
            bar_x = rect.right - 110
            bar_y = rect.y + 16
            bar_w = 90
            bar_h = 16
            pygame.draw.rect(screen, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h))
            fill = int(bar_w * progress)
            c = (100, 220, 120) if got else (100, 150, 220)
            pygame.draw.rect(screen, c, (bar_x, bar_y, fill, bar_h))
            pygame.draw.rect(screen, (150, 150, 180), (bar_x, bar_y, bar_w, bar_h), 1)
            txt = self.font_small.render(f"{min(int(value), ach['target'])}/{ach['target']}",
                                          True, (255, 255, 255))
            screen.blit(txt, (bar_x + bar_w // 2 - txt.get_width() // 2, bar_y))

        # Правая панель — детали выбранного
        if 0 <= self.selected < len(ids):
            aid = ids[self.selected]
            ach = ACHIEVEMENTS[aid]
            got = aid in unlocked

            panel_x = list_x + list_w + 30
            panel_y = 100
            panel_w = W - panel_x - 60
            panel_h = H - 200
            panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            pygame.draw.rect(screen, (18, 14, 32), panel)
            pygame.draw.rect(screen, (255, 220, 80) if got else (90, 80, 130), panel, 3)

            # большая иконка-медаль
            cx = panel.centerx
            cy = panel.y + 90
            medal_col = (255, 220, 80) if got else (80, 80, 100)
            pygame.draw.circle(screen, medal_col, (cx, cy), 50)
            pygame.draw.circle(screen, (255, 255, 255) if got else (120, 120, 140),
                             (cx, cy), 50, 3)
            star = self.font_big.render("★", True, (60, 40, 20) if got else (40, 40, 60))
            screen.blit(star, (cx - star.get_width() // 2, cy - star.get_height() // 2))

            nm = self.font_big.render(ach["name"], True, (255, 240, 150))
            screen.blit(nm, (panel.centerx - nm.get_width() // 2, panel.y + 160))

            desc = self.font_small.render(ach["desc"], True, (200, 200, 220))
            screen.blit(desc, (panel.centerx - desc.get_width() // 2, panel.y + 200))

            if ach["reward"] > 0:
                rew = self.font_small.render(f"Награда: +{ach['reward']} очков",
                                              True, (255, 200, 100))
                screen.blit(rew, (panel.centerx - rew.get_width() // 2, panel.y + 230))

            # прогресс
            tracker_key = TRACKER.get(aid)
            value = stats.get(tracker_key, 0)
            progress = min(1.0, value / ach["target"]) if ach["target"] > 0 else 0
            bar_x = panel.x + 30
            bar_y = panel.y + 280
            bar_w = panel.w - 60
            bar_h = 24
            pygame.draw.rect(screen, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h))
            fill = int(bar_w * progress)
            c = (100, 220, 120) if got else (100, 150, 220)
            pygame.draw.rect(screen, c, (bar_x, bar_y, fill, bar_h))
            pygame.draw.rect(screen, (150, 150, 180), (bar_x, bar_y, bar_w, bar_h), 2)
            ptxt = self.font_small.render(
                f"{min(int(value), ach['target'])} / {ach['target']}   ({int(progress*100)}%)",
                True, (255, 255, 255))
            screen.blit(ptxt, (bar_x + bar_w // 2 - ptxt.get_width() // 2, bar_y + 4))

            # статус
            status = "✓ ПОЛУЧЕНО" if got else "В процессе..."
            st = self.font_small.render(status, True,
                                          (100, 240, 120) if got else (200, 200, 200))
            screen.blit(st, (panel.centerx - st.get_width() // 2, bar_y + 40))
