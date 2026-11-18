"""Отслеживание активного окна (polling)."""
import time
import threading


class WindowTracker:
    def __init__(self, callback, interval: float = 2.0):
        self.callback = callback
        self.interval = interval
        self._running = False
        self._thread = None
        self._last_title = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        while self._running:
            try:
                from events.window_metadata import get_active_window_metadata
                meta = get_active_window_metadata()
                title = meta.get("Заголовок", "")
                if title != self._last_title:
                    self._last_title = title
                    self.callback(meta)
            except Exception:
                pass
            time.sleep(self.interval)
