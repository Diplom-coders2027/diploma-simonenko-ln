# events/idle_tracker.py — отслеживание бездействия
import threading
import time

try:
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def get_idle_seconds() -> float:
    if not WIN32_AVAILABLE:
        return 0.0
    try:
        # GetLastInputInfo
        import ctypes
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    except Exception:
        return 0.0


class IdleTracker(threading.Thread):
    def __init__(self, callback, threshold=120.0, interval=10.0):
        super().__init__(daemon=True)
        self.callback = callback
        self.threshold = threshold
        self.interval = interval
        self._running = True
        self._triggered = False

    def run(self):
        while self._running:
            idle = get_idle_seconds()
            if idle >= self.threshold and not self._triggered:
                self._triggered = True
                self.callback("idle", f"{int(idle)}s")
            elif idle < self.threshold:
                self._triggered = False
            time.sleep(self.interval)

    def stop(self):
        self._running = False