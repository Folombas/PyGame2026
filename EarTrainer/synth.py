"""Процедурный синтез звука — ноты, интервалы, аккорды.
Без внешних .wav: всё генерируется через numpy и pygame.mixer.
"""
import numpy as np
import pygame

SAMPLE_RATE = 44100
_cache = {}
_audio_ok = True

try:
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
    pygame.mixer.init()
except Exception:
    _audio_ok = False


def midi_to_freq(note: int) -> float:
    """MIDI → Гц. A4 (69) = 440 Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def _wave(freq: float, duration: float, wave: str = "sine") -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    if wave == "sine":
        return np.sin(2 * np.pi * freq * t)
    if wave == "tri":
        return 2 * np.abs(2 * (freq * t - np.floor(freq * t + 0.5))) - 1
    if wave == "square":
        return np.sign(np.sin(2 * np.pi * freq * t))
    if wave == "saw":
        return 2 * (freq * t - np.floor(freq * t + 0.5))
    return np.sin(2 * np.pi * freq * t)


def _envelope(n: int, attack: float = 0.02, release: float = 0.35) -> np.ndarray:
    env = np.ones(n)
    a = int(attack * SAMPLE_RATE)
    r = int(release * SAMPLE_RATE)
    if 0 < a < n:
        env[:a] = np.linspace(0, 1, a) ** 0.5
    if 0 < r < n:
        env[-r:] = np.linspace(1, 0, r) ** 1.5
    return env


def _to_sound(buf: np.ndarray):
    pcm = (np.clip(buf, -1.0, 1.0) * 32767).astype(np.int16)
    stereo = np.column_stack((pcm, pcm))
    return pygame.sndarray.make_sound(stereo)


def _note_buffer(note: int, duration: float, volume: float, wave: str) -> np.ndarray:
    key = ("n", note, duration, wave)
    if key in _cache:
        return _cache[key]
    n = int(SAMPLE_RATE * duration)
    buf = _wave(midi_to_freq(note), duration, wave)
    buf *= _envelope(n) * volume
    _cache[key] = buf
    return buf


def interval_buffer(root: int, semitones: int, direction: str = "up",
                    duration: float = 0.8, gap: float = 0.35,
                    volume: float = 0.35, wave: str = "sine") -> np.ndarray:
    key = ("i", root, semitones, direction, duration, gap)
    if key in _cache:
        return _cache[key]
    up = root + semitones
    dn = root - semitones
    a, b = (root, up) if direction == "up" else (dn, root)
    w1 = _note_buffer(a, duration, volume, wave)
    w2 = _note_buffer(b, duration, volume, wave)
    silence = np.zeros(int(SAMPLE_RATE * gap))
    buf = np.concatenate([w1, silence, w2])
    _cache[key] = buf
    return buf


def chord_buffer(root: int, semitones_list, duration: float = 1.2,
                 volume: float = 0.25, wave: str = "sine") -> np.ndarray:
    key = ("c", root, tuple(semitones_list), duration, wave)
    if key in _cache:
        return _cache[key]
    n = int(SAMPLE_RATE * duration)
    env = _envelope(n, attack=0.05, release=0.5)
    mix = np.zeros(n)
    for s in semitones_list:
        mix += _wave(midi_to_freq(root + s), duration, wave) * env
    mix *= volume / len(semitones_list)
    _cache[key] = mix
    return mix


def _play(buf: np.ndarray):
    if not _audio_ok:
        return
    try:
        _to_sound(buf).play()
    except Exception:
        pass


def play_note(note: int, duration: float = 1.0, wave: str = "sine"):
    _play(_note_buffer(note, duration, 0.35, wave))


def play_interval(root: int, semitones: int, direction: str = "up", wave: str = "sine"):
    _play(interval_buffer(root, semitones, direction, wave=wave))


def play_chord(root: int, semitones_list, wave: str = "sine"):
    _play(chord_buffer(root, semitones_list, wave=wave))


def play_success():
    _play(interval_buffer(60, 4, "up", duration=0.15, gap=0.03, volume=0.4))


def play_fail():
    _play(interval_buffer(60, 1, "up", duration=0.2, gap=0.02, volume=0.35))
