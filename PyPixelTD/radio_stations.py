"""Загрузка списка станций с Radio Browser API + локальный кеш."""
import json
import os
import random
import requests

CACHE_FILE = os.path.join(os.path.dirname(__file__), "assets", "radio_cache.json")
API = "https://de1.api.radio-browser.info/json/stations/search"

# Фоллбэк — если сеть недоступна, играем эти
FALLBACK = {
    "FM": [
        {"name": "SomaFM Groove Salad", "url": "https://ice1.somafm.com/groovesalad-128-mp3"},
        {"name": "SomaFM Drone Zone",   "url": "https://ice1.somafm.com/dronezone-128-mp3"},
        {"name": "Radio Paradise",      "url": "https://stream.radioparadise.com/mp3-128"},
    ],
    "УКВ": [
        {"name": "SomaFM Indie Pop",    "url": "https://ice1.somafm.com/indiepop-128-mp3"},
        {"name": "SomaFM Underground",  "url": "https://ice1.somafm.com/u80s-128-mp3"},
    ],
    "SW": [
        {"name": "SomaFM Space",        "url": "https://ice1.somafm.com/spacestation-128-mp3"},
        {"name": "SomaFM Deep Space",   "url": "https://ice1.somafm.com/deepspaceone-128-mp3"},
    ],
    "MW": [
        {"name": "SomaFM Mission Control", "url": "https://ice1.somafm.com/missioncontrol-128-mp3"},
        {"name": "SomaFM Folk Forward",    "url": "https://ice1.somafm.com/folkfwd-128-mp3"},
    ],
}


def _fetch(query, limit=8, timeout=6):
    """Дёргает API. Возвращает список dict(name, url)."""
    try:
        params = {
            "limit": limit,
            "hidebroken": "true",
            "order": "votes",
            "reverse": "true",
            **query,
        }
        headers = {"User-Agent": "BunnyOS-Radio/1.0"}
        r = requests.get(API, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        out = []
        for s in r.json():
            url = s.get("url_resolved") or s.get("url")
            name = (s.get("name") or "?").strip()
            if url and name:
                out.append({"name": name[:40], "url": url})
        return out
    except Exception as e:
        print(f"[stations] сеть недоступна ({e}) — берём фоллбэк")
        return []


def load_stations():
    """Возвращает {band_name: [station, ...]}. Пробует кеш → API → фоллбэк."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            total = sum(len(v) for v in data.values())
            if total > 3:
                print(f"[stations] из кеша: {total} шт.")
                return data
        except Exception:
            pass

    print("[stations] тянем из Radio Browser...")
    bands = {
        "FM":  _fetch({"countrycode": "RU", "tag": "pop"}),
        "УКВ": _fetch({"tag": "classical"}),
        "SW":  _fetch({"tag": "ambient"}),
        "MW":  _fetch({"tag": "jazz"}),
    }
    # Если что-то пусто — берём фоллбэк для этой полосы
    for k, v in bands.items():
        if not v:
            bands[k] = FALLBACK.get(k, [])

    total = sum(len(v) for v in bands.values())
    if total > 3:
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(bands, f, ensure_ascii=False, indent=2)
            print(f"[stations] закешировано: {total} шт. → {CACHE_FILE}")
        except Exception as e:
            print(f"[stations] не сохранил кеш: {e}")
    return bands
