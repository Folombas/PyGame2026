from pathlib import Path
import pygame

class Audio:
    def __init__(self, root=None):
        self.root = Path(root or Path(__file__).resolve().parents[1] / "assets" / "sounds")
        self.enabled = True
        self.muted = False
        self.sounds = {}
        self.base_volume = 0.7

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
        except pygame.error:
            self.enabled = False

        for name in ("click", "hover", "shoot", "hit", "menu_open"):
            path = self.root / f"{name}.wav"
            if path.exists():
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(path))
                except pygame.error:
                    pass

    def play(self, name, volume=1.0):
        if not self.enabled or self.muted:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(self.base_volume * volume)
            sound.play()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted and self.enabled:
            pygame.mixer.stop()
        return not self.muted
