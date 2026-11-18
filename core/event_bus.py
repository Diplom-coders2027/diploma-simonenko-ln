"""Простая шина событий для связи модулей."""
from typing import Callable, Dict, List


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        self._listeners.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable) -> None:
        if event in self._listeners:
            try:
                self._listeners[event].remove(callback)
            except ValueError:
                pass

    def emit(self, event: str, *args, **kwargs) -> None:
        for cb in list(self._listeners.get(event, [])):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                print(f"[EventBus] ошибка в обработчике {event}: {e}")

    def clear(self) -> None:
        self._listeners.clear()
