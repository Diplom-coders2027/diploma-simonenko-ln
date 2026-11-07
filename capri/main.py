# main.py — точка входа Capri
import os
import sys
import threading

# Добавляем корень проекта в path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.state import state
from core.event_bus import bus
from overlay.window import CapriWindow
from dialogue.engine import DialogueEngine
from audio.player import play_async
from events.window_tracker import WindowTracker
from events.idle_tracker import IdleTracker
from files.manager import work_dir

# Инициализация
dialogue_engine = DialogueEngine()
window_tracker = None
idle_tracker = None


def on_event(event_type: str, data=None):
    """Обработчик событий от трекеров."""
    state.record_event(event_type)
    phrase = dialogue_engine.random_phrase(event_type)
    if phrase:
        # Обновляем UI через сигнал (thread-safe)
        from PyQt6.QtCore import QMetaObject, Qt as QtCore_Qt
        QMetaObject.invokeMethod(
            app_window, "show_dialogue",
            QtCore_Qt.ConnectionType.QueuedConnection,
            str(phrase)
        )
    play_async(event_type)


def setup_trackers():
    global window_tracker, idle_tracker
    window_tracker = WindowTracker(
        callback=lambda et, d: on_event(et, d),
        interval=3.0
    )
    window_tracker.start()

    idle_tracker = IdleTracker(
        callback=lambda et, d: on_event(et, d),
        threshold=120.0,
        interval=10.0
    )
    idle_tracker.start()


def main():
    global app_window
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Создаём рабочую директорию
    work_dir()

    # Окно
    app_window = CapriWindow()
    app_window.close_requested.connect(app.quit)
    app_window.minimize_requested.connect(app_window.showMinimized)
    app_window.show()

    # Приветствие
    phrase = dialogue_engine.random_phrase("greeting")
    if phrase:
        app_window.show_dialogue(phrase, 5000)
    play_async("greeting")

    # Запуск трекеров
    setup_trackers()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()