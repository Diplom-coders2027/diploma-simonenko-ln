"""Мониторинг процессов (опционально)."""
import time
import threading


class ProcessMonitor:
    def __init__(self, callback, interval: float = 10.0, watch_list=None):
        self.callback = callback
        self.interval = interval
        self.watch_list = watch_list or []
        self._running = False
        self._thread = None

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
                from events.window_metadata import get_process_list
                procs = get_process_list(10)
                if self.watch_list:
                    found = [p for p in procs if any(w.lower() in (p.get("name") or "").lower() for w in self.watch_list)]
                    if found:
                        self.callback(found)
                else:
                    self.callback(procs)
            except Exception:
                pass
            time.sleep(self.interval)
