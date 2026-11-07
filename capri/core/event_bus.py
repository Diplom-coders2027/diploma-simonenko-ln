# core/event_bus.py — простая шина событий
import threading
from typing import Callable, Dict, List

class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def on(self, event_type: str, callback: Callable):
        with self._lock:
            self._listeners.setdefault(event_type, []).append(callback)

    def emit(self, event_type: str, data=None):
        with self._lock:
            listeners = list(self._listeners.get(event_type, []))
        for cb in listeners:
            try:
                cb(data)
            except Exception as e:
                print(f"EventBus error [{event_type}]: {e}")

    def off(self, event_type: str, callback: Callable):
        with self._lock:
            if event_type in self._listeners:
                self._listeners[event_type] = [
                    c for c in self._listeners[event_type] if c != callback
                ]

# Глобальный экземпляр
bus = EventBus()