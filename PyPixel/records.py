"""Таблица рекордов. Сохраняется в records.json рядом с игрой."""
import json
import os
from datetime import datetime

RECORDS_FILE = os.path.join(os.path.dirname(__file__), "records.json")
MAX_RECORDS = 5


def load_records():
    if not os.path.exists(RECORDS_FILE):
        return []
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_record(score, pixels, total_pixels, kills, apples, level, difficulty):
    """Добавляет запись, сортирует по очкам, хранит топ-5."""
    entry = {
        "score": score,
        "pixels": pixels,
        "total_pixels": total_pixels,
        "kills": kills,
        "apples": apples,
        "level": level,
        "difficulty": difficulty,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    records = load_records()
    records.append(entry)
    records.sort(key=lambda r: r.get("score", 0), reverse=True)
    records = records[:MAX_RECORDS]
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
    return records


def best_score(difficulty=None):
    records = load_records()
    if difficulty:
        records = [r for r in records if r.get("difficulty") == difficulty]
    if not records:
        return 0
    return max(r.get("score", 0) for r in records)
