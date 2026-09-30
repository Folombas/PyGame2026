"""Настройки звука: сохраняются в sound_settings.json."""
import json
import os

FILE = os.path.join(os.path.dirname(__file__), "sound_settings.json")

DEFAULTS = {
    "enabled": True,
    "volume": 0.5,     # 0.0 .. 1.0
}


def load():
    if not os.path.exists(FILE):
        return dict(DEFAULTS)
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            result = dict(DEFAULTS)
            result.update({k: data.get(k, DEFAULTS[k]) for k in DEFAULTS})
            return result
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save(settings):
    try:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
