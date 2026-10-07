"""Лимиты расходов по категориям (хранятся в JSON)."""
import json
import os


PATH = os.path.expanduser("~/.bunny_budget/budgets.json")


def _load():
    if not os.path.exists(PATH):
        return {}
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_limit(category, amount):
    data = _load()
    data[category] = float(amount)
    _save(data)


def get_limit(category):
    return _load().get(category)


def delete_limit(category):
    data = _load()
    if category in data:
        del data[category]
        _save(data)
        return True
    return False


def all_limits():
    return _load()
