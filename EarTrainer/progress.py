"""Система прогресса: XP, уровни, стрики, hearts, daily quests, achievements."""
import json
import os
import datetime

SAVE_FILE = os.path.join(os.path.dirname(__file__), "progress.json")

# Порог XP для каждого уровня (L1→L2 = 100, L2→L3 = 250, ...)
XP_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5200]

ACHIEVEMENTS = [
    {"id": "first",     "name": "Первый шаг",     "desc": "Ответить правильно 1 раз",  "check": lambda p: p["total_correct"] >= 1},
    {"id": "streak10",  "name": "На волне",       "desc": "Стрик 10 правильных",       "check": lambda p: p["best_streak"] >= 10},
    {"id": "streak25",  "name": "Слухач",         "desc": "Стрик 25 правильных",       "check": lambda p: p["best_streak"] >= 25},
    {"id": "streak50",  "name": "Абсолют",        "desc": "Стрик 50 правильных",       "check": lambda p: p["best_streak"] >= 50},
    {"id": "correct50", "name": "Полтинник",      "desc": "50 правильных ответов",     "check": lambda p: p["total_correct"] >= 50},
    {"id": "correct200","name": "Двести",         "desc": "200 правильных ответов",    "check": lambda p: p["total_correct"] >= 200},
    {"id": "level5",    "name": "Продвинутый",    "desc": "Достичь 5 уровня",          "check": lambda p: p["level"] >= 5},
    {"id": "level10",   "name": "Маэстро",        "desc": "Достичь 10 уровня",         "check": lambda p: p["level"] >= 10},
    {"id": "daily3",    "name": "Постоянство",    "desc": "3 дня подряд",              "check": lambda p: p["streak_days"] >= 3},
    {"id": "daily7",    "name": "Неделя силы",    "desc": "7 дней подряд",             "check": lambda p: p["streak_days"] >= 7},
]

DEFAULT = {
    "xp": 0, "level": 1,
    "total_correct": 0, "total_wrong": 0,
    "streak": 0, "best_streak": 0,
    "streak_days": 0, "last_played_date": "",
    "hearts": 5, "max_hearts": 5,
    "achievements": [],
    "daily_date": "", "daily_done": 0, "daily_target": 5,
    "sessions": 0,
}


def _today():
    return datetime.date.today().isoformat()


def load() -> dict:
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return DEFAULT.copy()


def save(p: dict):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2, ensure_ascii=False)


def check_daily_streak(p: dict) -> bool:
    """Обновляет дневной стрик. True, если день новый."""
    today = _today()
    if p["last_played_date"] == today:
        return False
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    if p["last_played_date"] == yesterday:
        p["streak_days"] += 1
    else:
        p["streak_days"] = 1
    p["last_played_date"] = today
    # Новый daily reset
    if p["daily_date"] != today:
        p["daily_date"] = today
        p["daily_done"] = 0
        p["daily_target"] = 5
    save(p)
    return True


def xp_for_level(level: int) -> int:
    if level - 1 < len(XP_THRESHOLDS):
        return XP_THRESHOLDS[level - 1]
    # Экстраполяция для больших уровней
    return XP_THRESHOLDS[-1] + (level - len(XP_THRESHOLDS)) * 1500


def next_level_xp(level: int) -> int:
    return xp_for_level(level + 1)


def xp_progress(p: dict):
    """Возвращает (current_xp_in_level, required_for_next)."""
    cur = xp_for_level(p["level"])
    nxt = next_level_xp(p["level"])
    return p["xp"] - cur, nxt - cur


def add_xp(p: dict, amount: int) -> bool:
    """Добавляет XP. True, если был level-up."""
    p["xp"] += amount
    leveled = False
    while p["xp"] >= next_level_xp(p["level"]):
        p["level"] += 1
        leveled = True
        p["hearts"] = p["max_hearts"]  # награда: полные hearts
    save(p)
    return leveled


def register_answer(p: dict, correct: bool) -> dict:
    """Регистрирует ответ. Возвращает: {leveled, xp_gain, achievement, game_over}."""
    result = {"leveled": False, "xp_gain": 0, "achievement": None, "game_over": False}

    if correct:
        p["total_correct"] += 1
        p["streak"] += 1
        p["best_streak"] = max(p["best_streak"], p["streak"])
        p["daily_done"] += 1
        # XP зависит от стрика (бонус за streak)
        xp_gain = 10 + min(p["streak"] - 1, 20)
        result["xp_gain"] = xp_gain
        result["leveled"] = add_xp(p, xp_gain)
        # Награда: heart каждые 5 правильных
        if p["total_correct"] % 5 == 0 and p["hearts"] < p["max_hearts"]:
            p["hearts"] += 1
    else:
        p["total_wrong"] += 1
        p["streak"] = 0
        p["hearts"] -= 1
        if p["hearts"] <= 0:
            result["game_over"] = True

    save(p)

    # Проверка достижений
    for a in ACHIEVEMENTS:
        if a["id"] not in p["achievements"] and a["check"](p):
            p["achievements"].append(a["id"])
            save(p)
            result["achievement"] = a
            break

    return result


def get_achievement(aid: str):
    return next((a for a in ACHIEVEMENTS if a["id"] == aid), None)


def daily_progress(p: dict) -> tuple:
    """(done, target) для сегодняшнего дейлика."""
    if p["daily_date"] != _today():
        return 0, 5
    return p["daily_done"], p["daily_target"]
