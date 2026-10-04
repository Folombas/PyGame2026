"""Загрузка спрайтов из assets/. Если файла нет — возвращает None,
и игра использует процедурный спрайт."""
import os
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_cache = {}


def load_image(rel_path):
    if rel_path in _cache:
        return _cache[rel_path]
    full = os.path.join(ASSETS_DIR, rel_path)
    if not os.path.exists(full):
        _cache[rel_path] = None
        return None
    try:
        img = pygame.image.load(full).convert_alpha()
        _cache[rel_path] = img
        return img
    except pygame.error as e:
        print(f"[assets] не загрузил {rel_path}: {e}")
        _cache[rel_path] = None
        return None


def extract_tile(sheet, tx, ty, tile_w, tile_h, scale=1):
    if sheet is None:
        return None
    rect = pygame.Rect(tx * tile_w, ty * tile_h, tile_w, tile_h)
    sub = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
    sub.blit(sheet, (0, 0), rect)
    if scale != 1:
        sub = pygame.transform.scale(sub, (tile_w * scale, tile_h * scale))
    return sub


def list_available():
    print(f"[assets] ищу в {ASSETS_DIR}")
    if not os.path.exists(ASSETS_DIR):
        print("  ⚠ папки assets/ нет")
        return
    found = False
    for root, dirs, files in os.walk(ASSETS_DIR):
        for f in files:
            if f.lower().endswith((".png", ".jpg")):
                rel = os.path.relpath(os.path.join(root, f), ASSETS_DIR)
                print(f"  ✓ {rel}")
                found = True
    if not found:
        print("  ⚠ файлов PNG не найдено")
