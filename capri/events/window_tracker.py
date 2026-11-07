# events/window_tracker.py — отслеживание активного окна (Windows)
import threading
import time

try:
    import win32gui
    import win32process
    import psutil
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def get_active_window_title() -> str:
    if not WIN32_AVAILABLE:
        return ""
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        return title
    except Exception:
        return ""


def get_active_process_name() -> str:
    if not WIN32_AVAILABLE:
        return ""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name()
    except Exception:
        return ""


class WindowTracker(threading.Thread):
    def __init__(self, callback, interval=3.0):
        super().__init__(daemon=True)
        self.callback = callback
        self.interval = interval
        self._running = True
        self._last_window = ""

    def run(self):
        while self._running:
            try:
                current = get_active_process_name()
                if current and current != self._last_window:
                    self._last_window = current
                    self.callback("window_change", current)
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self._running = False