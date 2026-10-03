"""Процедурные звуки ОС: старт, клик, ошибка, выключение."""
import math
import struct
import pygame

SR = 22050
_cache = {}
_ok = False


def _tone(f1, f2, dur, vol=0.35, wave="sine", decay=1.0):
    n = int(SR * dur)
    samples = []
    phase = 0.0
    for i in range(n):
        t = i / n
        f = f1 + (f2 - f1) * t
        phase += 2 * math.pi * f / SR
        if wave == "square":
            s = 1.0 if math.sin(phase) >= 0 else -1.0
        else:
            s = math.sin(phase)
        s *= (1 - t) ** decay * vol
        samples.append(int(s * 32767))
    return struct.pack(f"<{n}h", *samples)


def _chord_seq(notes):
    """Несколько нот подряд для мелодичного эффекта."""
    return b"".join(_tone(*n) for n in notes)


def init():
    global _ok
    try:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.mixer.pre_init(SR, -16, 1, 512)
        pygame.mixer.init()
        _ok = True
    except pygame.error:
        return
    try:
        # Старт BunnyOS — восходящее арпеджио C-E-G-C
        _cache["start"] = pygame.mixer.Sound(buffer=_chord_seq([
            (261, 261, 0.12, 0.30),
            (329, 329, 0.12, 0.30),
            (392, 392, 0.12, 0.30),
            (523, 523, 0.28, 0.32),
        ]))
        # Вход в систему — теплый аккорд
        _cache["login"] = pygame.mixer.Sound(buffer=_chord_seq([
            (392, 392, 0.10, 0.25),
            (523, 523, 0.30, 0.30),
        ]))
        # Выключение — нисходящее
        _cache["shutdown"] = pygame.mixer.Sound(buffer=_chord_seq([
            (523, 523, 0.15, 0.30),
            (392, 392, 0.15, 0.30),
            (261, 261, 0.35, 0.28),
        ]))
        # Клик
        _cache["click"] = pygame.mixer.Sound(buffer=_tone(1200, 900, 0.04, vol=0.15))
        # Ошибка — глухой удар
        _cache["error"] = pygame.mixer.Sound(buffer=_tone(180, 90, 0.18, vol=0.30, wave="square"))
        # Уведомление
        _cache["notify"] = pygame.mixer.Sound(buffer=_chord_seq([
            (800, 800, 0.06, 0.20),
            (1000, 1000, 0.10, 0.22),
        ]))
    except pygame.error as e:
        print(f"[os_sounds] {e}")


def play(name):
    if not _ok:
        return
    snd = _cache.get(name)
    if snd:
        snd.set_volume(0.6)
        snd.play()
