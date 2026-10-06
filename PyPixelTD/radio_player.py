"""Ядро интернет-радио через libVLC."""
import vlc


class RadioPlayer:
    """Обёртка над VLC MediaPlayer."""

    def __init__(self):
        # --no-video отключает видео-окно (у нас только аудио)
        self.instance = vlc.Instance("--no-video", "--quiet")
        self.player = self.instance.media_player_new()
        self.current_url = None
        self.current_name = None
        self.is_playing = False
        self._volume = 0.5  # 0..1

    def play_stream(self, url, name="Unknown"):
        """Запускает интернет-поток по URL."""
        if not url:
            return False
        try:
            self.stop()
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.audio_set_volume(int(self._volume * 100))
            self.player.play()
            self.current_url = url
            self.current_name = name
            self.is_playing = True
            print(f"[radio] ▶ {name}")
            return True
        except Exception as e:
            print(f"[radio] ошибка: {e}")
            self.is_playing = False
            return False

    def stop(self):
        """Останавливает воспроизведение."""
        try:
            if self.player.is_playing():
                self.player.stop()
        except Exception:
            pass
        self.is_playing = False
        self.current_url = None
        self.current_name = None

    def set_volume(self, volume):
        """Громкость 0..1."""
        self._volume = max(0.0, min(1.0, volume))
        try:
            self.player.audio_set_volume(int(self._volume * 100))
        except Exception:
            pass

    def get_volume(self):
        return self._volume

    def is_active(self):
        try:
            return self.player.is_playing() == 1
        except Exception:
            return False
