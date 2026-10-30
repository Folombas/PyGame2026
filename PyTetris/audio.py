"""Procedural sound effects. No asset files needed."""
import numpy as np
import pygame

_OK = True
try:
    pygame.mixer.pre_init(22050, -16, 2, 512)
    pygame.mixer.init()
except Exception:
    _OK = False

def _tone(freq, dur, vol=0.3, wave='sine', decay=4.0):
    sr = 22050
    n = max(1, int(sr * dur))
    t = np.linspace(0, dur, n, False)
    if wave == 'sine':
        w = np.sin(2 * np.pi * freq * t)
    elif wave == 'square':
        w = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == 'tri':
        w = 2 * np.abs(2 * (freq * t - np.floor(freq * t + 0.5))) - 1
    else:
        w = np.sin(2 * np.pi * freq * t)
    env = np.exp(-decay * t)
    pcm = (w * env * vol * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((pcm, pcm)))

SOUNDS = {}
if _OK:
    try:
        SOUNDS = {
            'move':     _tone(330, 0.04, 0.12, 'square'),
            'rotate':   _tone(440, 0.05, 0.18, 'square'),
            'lock':     _tone(220, 0.08, 0.22),
            'clear':    _tone(660, 0.15, 0.28),
            'tetris':   _tone(880, 0.30, 0.32, decay=2.5),
            'levelup':  _tone(550, 0.22, 0.30),
            'gameover': _tone(110, 0.60, 0.35, decay=2.0),
            'menu':     _tone(550, 0.06, 0.18, 'square'),
            'combo':    _tone(880, 0.10, 0.25, 'square'),
            'powerup':  _tone(1200, 0.20, 0.30, 'sine'),
            'ui_hover': _tone(880, 0.03, 0.10, 'sine'),
            'ui_click': _tone(660, 0.05, 0.20, 'square'),
        }
    except Exception:
        SOUNDS = {}

def play(name):
    snd = SOUNDS.get(name)
    if snd:
        try:
            snd.play()
        except Exception:
            pass

def toggle_mute(muted):
    if _OK:
        if muted:
            pygame.mixer.pause()
        else:
            pygame.mixer.unpause()


def load_music(path="assets/music/funky_chiptune.ogg"):
    if not _OK:
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.4)
        print(f"🎵 Музыка загружена (stream): {path}")
    except Exception as e:
        print(f"⚠️ Музыка не загружена: {e}")

def play_music():
    if _OK:
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
        except Exception:
            pass

def stop_music():
    if _OK:
        pygame.mixer.music.stop()

# Загружаем музыку при импорте
load_music()

def set_sfx_volume(vol):
    for snd in SOUNDS.values():
        snd.set_volume(vol)
