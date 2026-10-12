"""Система рекордов BunnyOS — рекорды сохраняются в JSON."""
import os
import json
from datetime import datetime


PATH = os.path.expanduser("~/.bunny_games/highscores.json")


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


def submit(game_id, score, higher_is_better=True):
    """Сохраняет рекорд если он лучше. Возвращает True если обновлён."""
    data = _load()
    entry = data.get(game_id, {})

    # Поддержка старого формата (просто число)
    if isinstance(entry, (int, float)):
        old_score = entry
    else:
        old_score = entry.get("score", 0)

    is_better = (score > old_score) if higher_is_better else (score < old_score)
    if is_better or old_score == 0:
        data[game_id] = {
            "score": score,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        _save(data)
        return True
    return False


def get(game_id):
    """Возвращает текущий рекорд (число) или 0."""
    data = _load()
    entry = data.get(game_id, {})
    if isinstance(entry, (int, float)):
        return entry
    return entry.get("score", 0)


def all_scores():
    """Возвращает {game_id: score}."""
    data = _load()
    result = {}
    for gid, entry in data.items():
        if isinstance(entry, (int, float)):
            result[gid] = entry
        else:
            result[gid] = entry.get("score", 0)
    return result


def reset(game_id=None):
    """Сбрасывает рекорд для игры или все."""
    if game_id is None:
        _save({})
        return
    data = _load()
    if game_id in data:
        del data[game_id]
        _save(data)
