"""Системные звуки BunnyOS (в стиле Windows)."""
import os
import pygame

# Путь к папке со звуками
SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds", "windows")

_sounds = {}
_ok = False

# Список звуков, которые будем загружать (имя_файла: ключ)
SOUND_FILES = {
    "start": "start.wav",         # Запуск системы
    "shutdown": "shutdown.wav",   # Выключение
    "logon": "logon.wav",         # Вход в систему
    "error": "error.wav",         # Ошибка
    "notify": "notify.wav",       # Уведомление
    "menu": "menu.wav",           # Открытие меню
    "minimize": "minimize.wav",   # Сворачивание окна
    "restore": "restore.wav",     # Разворачивание окна
}

def init():
    """Загружает все звуки. Вызывать после pygame.mixer.init()."""
    global _ok
    # Проверяем, что микшер инициализирован
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except pygame.error:
            print("[sounds] mixer не запустился")
            return

    for key, filename in SOUND_FILES.items():
        path = os.path.join(SOUNDS_DIR, filename)
        if os.path.exists(path):
            try:
                _sounds[key] = pygame.mixer.Sound(path)
            except pygame.error as e:
                print(f"[sounds] не загрузил {filename}: {e}")
        else:
            print(f"[sounds] файл не найден: {filename}")
    _ok = True
    print(f"[sounds] загружено {len(_sounds)} звуков")

def play(name: str):
    """Проигрывает звук по ключу."""
    if not _ok:
        return
    snd = _sounds.get(name)
    if snd:
        snd.play()
