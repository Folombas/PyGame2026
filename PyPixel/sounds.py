"""Процедурные 8-битные звуки. Без .wav/.ogg — всё генерируется в памяти.

Использует только stdlib (math, struct) — numpy не нужен.
"""
import math
import struct
import pygame

SAMPLE_RATE = 22050

_sounds: dict = {}
_ok = False


def _tone(freq_start, freq_end, duration, volume=0.3, wave="square", decay=1.5):
    """Генерирует моно PCM 16-bit: синус/квадрат/пила со сдвигом частоты и затуханием."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = freq_start + (freq_end - freq_start) * t
        phase += 2 * math.pi * freq / SAMPLE_RATE
        if wave == "square":
            s = 1.0 if math.sin(phase) >= 0 else -1.0
        elif wave == "saw":
            s = 2.0 * ((phase / (2 * math.pi)) % 1.0) - 1.0
        else:
            s = math.sin(phase)
        env = (1 - t) ** decay
        s *= env * volume
        samples.append(int(s * 32767))
    return struct.pack(f"<{n}h", *samples)


def _sequence(notes):
    """Склеивает несколько тонов в одну волну. notes — список кортежей для _tone()."""
    return b"".join(_tone(*n) for n in notes)


def init():
    """Готовит звуки. Вызывать ПОСЛЕ pygame.init()."""
    global _ok
    try:
        # pygame.init() уже создал mixer с дефолтным форматом — снесём и заведём свой
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        pygame.mixer.init()
    except pygame.error as e:
        print(f"[sounds] mixer не запустился: {e} — играем без звука")
        return

    try:
        _sounds["jump"] = pygame.mixer.Sound(buffer=_tone(300, 750, 0.14, volume=0.25))
        _sounds["stomp"] = pygame.mixer.Sound(buffer=_tone(700, 200, 0.12, volume=0.30))
        _sounds["hit"] = pygame.mixer.Sound(
            buffer=_tone(220, 70, 0.28, volume=0.30, wave="sine", decay=1.0)
        )
        _sounds["collect"] = pygame.mixer.Sound(buffer=_tone(900, 1400, 0.09, volume=0.20))
        _sounds["victory"] = pygame.mixer.Sound(buffer=_sequence([
            (523, 523, 0.10, 0.25),
            (659, 659, 0.10, 0.25),
            (784, 784, 0.10, 0.25),
            (1047, 1047, 0.32, 0.25),
        ]))
        _sounds["game_over"] = pygame.mixer.Sound(buffer=_sequence([
            (400, 400, 0.15, 0.25, "square", 1.0),
            (300, 300, 0.15, 0.25, "square", 1.0),
            (200, 200, 0.35, 0.25, "square", 0.8),
        ]))
        _ok = True
        print("[sounds] инициализировано:", list(_sounds.keys()))
    except pygame.error as e:
        print(f"[sounds] ошибка генерации: {e} — играем без звука")


def play(name: str) -> None:
    if not _ok:
        return
    snd = _sounds.get(name)
    if snd is not None:
        snd.play()
