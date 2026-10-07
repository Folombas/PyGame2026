"""Воспроизведение интернет-радио через VLC."""
import vlc


class RadioPlayer:
    """Обёртка над VLC MediaPlayer. Играет URL-потоки в фоне."""

    def __init__(self):
        self.instance = vlc.Instance("--no-video", "--quiet")
        self.player = self.instance.media_player_new()
        self.current_url = None
        self.current_name = None
        self.volume = 0.5  # 0..1

    def play(self, url, name=""):
        """Начинает воспроизведение URL. Останавливает предыдущее."""
        if not url:
            return False
        if self.current_url == url:
            return True
        try:
            self.player.stop()
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.audio_set_volume(int(self.volume * 100))
            self.player.play()
            self.current_url = url
            self.current_name = name
            print(f"[radio] ▶ {name}  ({url})")
            return True
        except Exception as e:
            print(f"[radio] ✗ ошибка: {e}")
            self.current_url = None
            return False

    def stop(self):
        """Останавливает воспроизведение."""
        try:
            self.player.stop()
        except Exception:
            pass
        self.current_url = None
        self.current_name = None

    def is_playing(self):
        """Играет ли сейчас что-то."""
        try:
            return bool(self.player.is_playing())
        except Exception:
            return False

    def set_volume(self, vol):
        """vol: 0.0 .. 1.0"""
        self.volume = max(0.0, min(1.0, vol))
        try:
            self.player.audio_set_volume(int(self.volume * 100))
        except Exception:
            pass
