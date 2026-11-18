"""Отслеживание бездействия пользователя."""
import time
import threading


class IdleTracker:
    def __init__(self, callback, threshold: float = 120.0, poll: float = 5.0):
        self.callback = callback
        self.threshold = threshold
        self.poll = poll
        self._running = False
        self._thread = None
        self._last_activity = time.time()

    def notify_activity(self):
        self._last_activity = time.time()

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
            idle = time.time() - self._last_activity
            if idle >= self.threshold:
                try:
                    self.callback(idle)
                except Exception:
                    pass
                # сбрасываем, чтобы не спамить
                self._last_activity = time.time()
            time.sleep(self.poll)
