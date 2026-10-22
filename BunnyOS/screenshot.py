"""Скриншоты рабочего стола."""
import os
import time
import pygame


def take_screenshot(surface, prefix="screenshot"):
    """Сохраняет screenshot в ~/bunny_sandbox/."""
    sandbox = os.path.expanduser("~/bunny_sandbox")
    os.makedirs(sandbox, exist_ok=True)
    fname = f"{prefix}_{int(time.time())}.png"
    path = os.path.join(sandbox, fname)
    try:
        pygame.image.save(surface, path)
        return path
    except Exception as e:
        print(f"[screenshot] ошибка: {e}")
        return None
