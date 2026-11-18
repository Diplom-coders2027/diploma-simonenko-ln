"""Состояние Капри: текущая анимация, настроение, позиция, размер."""
import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CapriState:
    # Текущая анимация (ключ из ClipTable)
    current_clip: str = "idle"
    # Направление: True = смотрит влево
    facing_left: bool = False
    # Размер (базовый, пиксели)
    size: int = 240
    # Позиция окна (x, y)
    x: int = 100
    y: int = 100
    # Настроение 0..100
    mood: int = 70
    # Уровень энергии 0..100
    energy: int = 80
    # Время последнего взаимодействия (секунды с эпохи)
    last_interaction: float = 0.0
    # Включён ли звук
    sound_enabled: bool = True
    # Включена ли анимация
    animation_enabled: bool = True
    # Текущий диалоговый пузырь
    bubble_text: Optional[str] = None
    bubble_until: float = 0.0
    # Имя пользователя (для диалогов)
    user_name: str = "Лев"

    def to_dict(self) -> dict:
        return {
            "current_clip": self.current_clip,
            "facing_left": self.facing_left,
            "size": self.size,
            "x": self.x,
            "y": self.y,
            "mood": self.mood,
            "energy": self.energy,
            "last_interaction": self.last_interaction,
            "sound_enabled": self.sound_enabled,
            "animation_enabled": self.animation_enabled,
            "user_name": self.user_name,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CapriState":
        s = cls()
        for k, v in d.items():
            if hasattr(s, k):
                setattr(s, k, v)
        return s

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "CapriState":
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        except Exception:
            return cls()
