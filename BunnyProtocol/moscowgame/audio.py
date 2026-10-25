import pygame
import array
import math

def make_sound(freq, duration, volume=0.1):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        buf[i] = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
    return pygame.mixer.Sound(buffer=buf)

def init_audio():
    try:
        pygame.mixer.init()
        return {
            'shoot': make_sound(600, 0.05),
            'hit': make_sound(300, 0.1),
            'explode': make_sound(100, 0.3, 0.2)
        }
    except Exception:
        return None
