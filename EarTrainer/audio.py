"""Звуковые эффекты: сначала WAV из assets/sfx, иначе — процедурный синтез."""
import os
import pygame
import synth  # процедурный fallback

_sounds = {}
_audio_ok = True
_muted = False

try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
except Exception:
    _audio_ok = False


def load_all():
    base = os.path.join(os.path.dirname(__file__), "assets", "sfx")
    names = ("click", "hover", "switch", "success", "error",
             "note", "levelup", "achievement", "correct", "wrong")
    for name in names:
        path = os.path.join(base, f"{name}.wav")
        if os.path.exists(path):
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(0.6)
                _sounds[name] = snd
            except Exception:
                pass


def play(name: str):
    if _muted or not _audio_ok:
        return
    snd = _sounds.get(name)
    if snd:
        try:
            snd.play()
            return
        except Exception:
            pass
    # Fallback на процедурный
    if name in ("correct", "success"):
        synth.play_success()
    elif name in ("wrong", "error"):
        synth.play_fail()
    elif name == "note":
        synth.play_note(69, 0.25)


def toggle_mute():
    global _muted
    _muted = not _muted
    if _muted:
        pygame.mixer.pause()
    else:
        pygame.mixer.unpause()
    return _muted


def is_muted() -> bool:
    return _muted


load_all()
