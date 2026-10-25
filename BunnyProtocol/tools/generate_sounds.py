from pathlib import Path
import math
import random
import struct
import wave

SR = 44100
OUT = Path(__file__).resolve().parents[1] / "assets" / "sounds"
rng = random.Random(42)

def clamp(x):
    return max(-1.0, min(1.0, x))

def write_wav(name, samples):
    OUT.mkdir(parents=True, exist_ok=True)
    data = b"".join(struct.pack("<h", int(clamp(s) * 32767)) for s in samples)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)

def env(i, n, attack=0.01, release=0.15):
    a = max(1, int(SR * attack))
    r = max(1, int(SR * release))
    if i < a:
        return i / a
    if i > n - r:
        return max(0.0, (n - i) / r)
    return 1.0

def tone(freq, dur, vol=0.5, kind="sine", sweep=0.0):
    n = int(SR * dur)
    out = []
    phase = 0.0
    for i in range(n):
        f = freq + sweep * (i / max(1, n - 1))
        phase += 2.0 * math.pi * f / SR
        if kind == "square":
            s = 1.0 if math.sin(phase) >= 0 else -1.0
        else:
            s = math.sin(phase)
        out.append(s * vol * env(i, n))
    return out

def noise(dur, vol=0.4):
    n = int(SR * dur)
    return [rng.uniform(-1.0, 1.0) * vol * (1.0 - i / n) for i in range(n)]

def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return [clamp(v) for v in out]

def arp(freqs, step=0.06, vol=0.35):
    out = []
    for f in freqs:
        out.extend(tone(f, step, vol))
    return out

write_wav("click.wav", mix(tone(1250, 0.035, 0.35, "square"), tone(820, 0.05, 0.18, "sine", -300)))
write_wav("hover.wav", tone(640, 0.045, 0.18, "sine", 120))
write_wav("shoot.wav", mix(tone(180, 0.12, 0.35, "square", -80), noise(0.09, 0.25)))
write_wav("hit.wav", mix(tone(90, 0.16, 0.45, "sine", -40), noise(0.12, 0.3)))
write_wav("menu_open.wav", arp([440, 554, 659, 880], 0.055, 0.3))
print("Sounds written to", OUT)
