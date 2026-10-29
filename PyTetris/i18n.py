LANG = "en"
TRANSLATIONS = {
    "en": {
        "play": "PLAY", "sprint": "SPRINT", "time": "TIME", "goal": "GOAL", "win": "GOAL REACHED!", "zen": "ZEN MODE", "lb": "LEADERBOARD", "ach": "ACHIEVEMENTS",
        "daily": "DAILY QUESTS", "lang": "LANGUAGE: EN", "quit": "QUIT",
        "score": "SCORE", "level": "LEVEL", "lines": "LINES", "next": "NEXT", "hold": "HOLD",
        "paused": "PAUSED", "game_over": "GAME OVER", "new_high": "NEW HIGH SCORE!",
        "resume": "RESUME", "menu": "MENU", "restart": "RESTART", "total_lines": "Total Lines",
        "best_score": "Best Score", "controls": "← → move  ↑ rotate  ↓ soft  SPACE hard  C hold  P pause",
        "ach1": "First Blood", "ach2": "TETRIS!", "ach3": "Combo x3", "ach4": "Combo Machine",
        "ach5": "Rising Star", "ach6": "Ascended", "ach7": "High Scorer", "ach8": "Legend",
        "ach9": "Marathon", "ach10": "Line Master",
        "achd1": "Clear your first line", "achd2": "Clear 4 lines at once", "achd3": "Chain 3+ line clears",
        "achd4": "Chain 5+ line clears", "achd5": "Reach level 5", "achd6": "Reach level 10",
        "achd7": "Reach 5000 points", "achd8": "Reach 20000 points", "achd9": "Survive 5 minutes in one run",
        "achd10": "Clear 50 lines total",
        "settings": "SETTINGS", "rank": "RANK", "collection": "COLLECTION", "back": "BACK", "music": "Music Vol", "sfx": "SFX Vol", 
        "ghost": "Ghost Piece", "shake": "Screen Shake",
        "d_lines": "Clear {target} lines today", "d_score": "Score {target} points", "d_time": "Play for {target} minutes today"
    },
    "ru": {
        "play": "ИГРАТЬ", "sprint": "СПРИНТ", "time": "ВРЕМЯ", "goal": "ЦЕЛЬ", "win": "ЦЕЛЬ ДОСТИГНУТА!", "zen": "ДЗЕН", "lb": "РЕКОРДЫ", "ach": "ДОСТИЖЕНИЯ",
        "daily": "ЗАДАНИЯ", "lang": "ЯЗЫК: RU", "quit": "ВЫХОД",
        "score": "СЧЕТ", "level": "УРОВЕНЬ", "lines": "ЛИНИИ", "next": "СЛЕД.", "hold": "ХОЛД",
        "paused": "ПАУЗА", "game_over": "ИГРА ОКОНЧЕНА", "new_high": "НОВЫЙ РЕКОРД!",
        "resume": "ПРОДОЛЖИТЬ", "menu": "МЕНЮ", "restart": "ЗАНОВО", "total_lines": "Всего линий",
        "best_score": "Лучший счет", "controls": "← → движ.  ↑ поворот  ↓ ускор.  SPACE сброс  C холд  P пауза",
        "ach1": "Первая кровь", "ach2": "ТЕТРИС!", "ach3": "Комбо x3", "ach4": "Машина комбо",
        "ach5": "Восходящая звезда", "ach6": "Вознесение", "ach7": "Много очков", "ach8": "Легенда",
        "ach9": "Марафонец", "ach10": "Мастер линий",
        "achd1": "Соберите первую линию", "achd2": "Соберите 4 линии сразу", "achd3": "Сделайте комбо из 3+ линий",
        "achd4": "Сделайте комбо из 5+ линий", "achd5": "Достигните 5 уровня", "achd6": "Достигните 10 уровня",
        "achd7": "Наберите 5000 очков", "achd8": "Наберите 20000 очков", "achd9": "Продержитесь 5 минут за игру",
        "achd10": "Соберите 50 линий всего",
        "settings": "НАСТРОЙКИ", "rank": "РАНГ", "collection": "КОЛЛЕКЦИЯ", "back": "НАЗАД", "music": "Гром. музыки", "sfx": "Гром. звуков", 
        "ghost": "Призрак фигуры", "shake": "Тряска экрана",
        "d_lines": "Соберите {target} линий сегодня", "d_score": "Наберите {target} очков", "d_time": "Играйте {target} минут сегодня"
    }
}
def t(key, **kwargs):
    s = TRANSLATIONS.get(LANG, TRANSLATIONS["en"]).get(key, key)
    return s.format(**kwargs) if kwargs else s
