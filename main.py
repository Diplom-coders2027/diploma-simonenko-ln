"""Точка входа Capri Desktop Companion."""
import os
import sys
import time
import getpass

# Корень проекта
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QObject, pyqtSignal

from core.state import CapriState
from core.event_bus import EventBus
from overlay.window import CapriWindow
from audio.player import AudioPlayer
from events.window_tracker import WindowTracker
from events.idle_tracker import IdleTracker
from events.process_monitor import ProcessMonitor


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    assets_dir = os.path.join(ROOT, "assets")
    state_path = os.path.join(ROOT, "state.json")
    state = CapriState.load(state_path)
    if not state.user_name or state.user_name == "Лев":
        state.user_name = getpass.getuser()
    if state.x == 100 and state.y == 100:
        screen = app.primaryScreen().geometry()
        state.x = screen.width() // 2 - 120
        state.y = screen.height() // 2 - 120

    bus = EventBus()
    audio = AudioPlayer(assets_dir)
    bus.on("sound", lambda name: audio.play(name))

    window = CapriWindow(state, bus, assets_dir)

    # Трей-иконка
    tray = QSystemTrayIcon()
    icon_path = os.path.join(assets_dir, "capri.png")
    if os.path.exists(icon_path):
        tray.setIcon(QIcon(icon_path))
    tray.setToolTip("Капри")
    tray_menu = QMenu()
    act_show = tray_menu.addAction("Показать")
    act_show.triggered.connect(window.show)
    act_quit = tray_menu.addAction("Выход")
    act_quit.triggered.connect(app.quit)
    tray.setContextMenu(tray_menu)
    tray.show()

    # Трекеры
    def on_window_change(meta):
        title = (meta.get("Заголовок") or "").lower()
        proc = (meta.get("Процесс") or "").lower()
        if any(w in title or w in proc for w in ("steam",)):
            bus.emit("animation", "idle")
            bus.emit("say", "steam")
        elif any(w in title or w in proc for w in ("code", "visual studio", "pycharm", "idea", "terminal", "cmd", "powershell")):
            bus.emit("animation", "perch")
            bus.emit("say", "vscode")
        elif any(w in title or w in proc for w in ("telegram",)):
            bus.emit("animation", "idle")
            bus.emit("say", "telegram")
        elif any(w in title or w in proc for w in ("discord",)):
            bus.emit("animation", "idle")
            bus.emit("say", "discord")
        elif any(w in title for w in ("chrome", "firefox", "edge", "browser", "opera")):
            bus.emit("animation", "idle")
            bus.emit("say", "browser")
        elif any(w in title for w in ("steam",)):
            bus.emit("animation", "idle")
            bus.emit("say", "steam")

    class Bridge(QObject):
        window_changed = pyqtSignal(dict)

    bridge = Bridge()
    bridge.window_changed.connect(on_window_change)

    def _track(meta):
        bridge.window_changed.emit(meta)

    wt = WindowTracker(_track, interval=3.0)
    wt.start()

    # Idle tracker через сигнал
    def on_idle(idle_sec):
        window.animator.load_clip("sleep")
        bus.emit("say", "sleep")

    class IdleBridge(QObject):
        idled = pyqtSignal(float)

    idle_bridge = IdleBridge()
    idle_bridge.idled.connect(on_idle)

    def _idle_cb(idle_sec):
        idle_bridge.idled.emit(idle_sec)

    it = IdleTracker(_idle_cb, threshold=180.0, poll=10.0)
    it.start()
    # уведомляем о активности при кликах
    window.petted.connect(it.notify_activity)

    # Мониторинг процессов (опционально, лёгкий)
    def on_procs(procs):
        pass
    pm = ProcessMonitor(on_procs, interval=30.0)
    pm.start()

    # Сохранение при выходе
    app.aboutToQuit.connect(lambda: state.save(state_path))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
