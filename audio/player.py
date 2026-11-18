"""Воспроизведение звуков (Qt Multimedia)."""
import os
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect


class AudioPlayer:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.sounds_dir = os.path.join(assets_dir, "sounds")
        os.makedirs(self.sounds_dir, exist_ok=True)
        self._effects: dict = {}
        self.enabled = True

    def play(self, name: str, volume: float = 0.6) -> None:
        if not self.enabled:
            return
        path = os.path.join(self.sounds_dir, name + ".wav")
        if not os.path.exists(path):
            path = os.path.join(self.sounds_dir, name + ".mp3")
        if not os.path.exists(path):
            return
        try:
            if name not in self._effects:
                eff = QSoundEffect()
                eff.setSource(QUrl.fromLocalFile(os.path.abspath(path)))
                eff.setVolume(volume)
                self._effects[name] = eff
            self._effects[name].play()
        except Exception as e:
            print(f"[Audio] ошибка воспроизведения {name}: {e}")

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
