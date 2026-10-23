"""Quest system — прогрессия в BunnyOS."""
import os
import json


QUEST_PATH = os.path.expanduser("~/.bunny_quests.json")


# === Квесты ===
QUESTS = [
    {
        "id": "first_bash",
        "title": "Первый контакт",
        "desc": "Выполни 'uname -a' в REAL BASH",
        "hint": "Super+B (или Ctrl+Alt+B) → набери uname -a",
        "reward": "Открыт квест 2",
    },
    {
        "id": "grep_secret",
        "title": "Кладоискатель",
        "desc": "Найди файл с 'BUNNY_SECRET' в /etc",
        "hint": "grep -r BUNNY_SECRET /etc",
        "reward": "Разблокирована команда 'hint --deep'",
    },
    {
        "id": "descent_start",
        "title": "Провал в систему",
        "desc": "Запусти BunnyDescent из BunnyOS",
        "hint": "Набери 'descent' в терминале",
        "reward": "Открыт доступ к 6-й игре",
    },
    {
        "id": "descent_3",
        "title": "Три уровня",
        "desc": "Спустись на 3-й уровень в BunnyDescent",
        "hint": "Убей врагов, иди к лестнице",
        "reward": "Ясность растёт",
    },
    {
        "id": "all_done",
        "title": "Исследователь",
        "desc": "Заверши все предыдущие квесты",
        "hint": "Продолжай исследовать",
        "reward": "🏆 Финальный статус: HACKER",
    },
]


def _load():
    if not os.path.exists(QUEST_PATH):
        return {"completed": [], "active": "first_bash"}
    try:
        with open(QUEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"completed": [], "active": "first_bash"}


def _save(data):
    try:
        with open(QUEST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_quest(qid):
    for q in QUESTS:
        if q["id"] == qid:
            return q
    return None


def get_active():
    data = _load()
    return get_quest(data.get("active"))


def is_completed(qid):
    return qid in _load().get("completed", [])


def complete(qid):
    """Отметить квест выполненным + активировать следующий."""
    data = _load()
    if qid in data.get("completed", []):
        return False
    data.setdefault("completed", []).append(qid)
    # Найти следующий
    for q in QUESTS:
        if q["id"] not in data["completed"]:
            data["active"] = q["id"]
            break
    _save(data)
    return True


def progress():
    """(выполнено, всего)."""
    data = _load()
    return len(data.get("completed", [])), len(QUESTS)


def is_all_completed():
    done, total = progress()
    return done >= total
