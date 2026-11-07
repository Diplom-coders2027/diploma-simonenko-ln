# core/state.py — состояние Капри
import threading

class CapriState:
    def __init__(self):
        self.mood = "neutral"
        self.last_event = ""
        self.event_count = 0
        self._lock = threading.Lock()

    def update_mood(self, mood: str):
        with self._lock:
            self.mood = mood

    def record_event(self, event: str):
        with self._lock:
            self.last_event = event
            self.event_count += 1

    def get_mood(self) -> str:
        with self._lock:
            return self.mood

    def get_event_count(self) -> int:
        with self._lock:
            return self.event_count

# Глобальный экземпляр
state = CapriState()