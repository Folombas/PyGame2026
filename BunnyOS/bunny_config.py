"""Persistence — сохранение настроек BunnyOS."""
import os
import json


CONFIG_PATH = os.path.expanduser("~/.bunny_config.json")

DEFAULTS = {
    "tiling": True,
    "workspaces": 9,
    "wallpaper": "gen_space.png",
    "volume": 0.25,
    "last_ws": 0,
}


def load():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULTS.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge с defaults
        result = DEFAULTS.copy()
        result.update(data)
        return result
    except Exception:
        return DEFAULTS.copy()


def save(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[config] save error: {e}")
        return False


def update(**kwargs):
    """Обновить отдельные ключи и сохранить."""
    cfg = load()
    cfg.update(kwargs)
    return save(cfg)
