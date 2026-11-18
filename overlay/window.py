"""Прозрачное overlay-окно с Капри, анимациями и взаимодействием."""
import os
import time
from typing import Optional

from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor, QAction
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QMenu, QApplication,
    QFileDialog, QMessageBox, QSystemTrayIcon,
)

from core.state import CapriState
from core.event_bus import EventBus
from overlay.animator import Animator, CLIP_TABLE


class SpeechBubble(QWidget):
    """Диалоговый пузырь Капри."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setStyleSheet(
            "QLabel {"
            "  background: rgba(18, 14, 24, 230);"
            "  color: #f0e6ff;"
            "  border: 1px solid rgba(180, 120, 255, 180);"
            "  border-radius: 12px;"
            "  padding: 8px 12px;"
            "  font-family: 'BarlowSemiCondensed';"
            "  font-size: 13px;"
            "}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.label)

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)
        self.hide()

    def show_text(self, text: str, duration_ms: int = 4000):
        self._hide_timer.stop()
        self.label.setText(text)
        self.adjustSize()
        if self.width() > 280:
            self.label.setFixedWidth(260)
            self.adjustSize()
        self._anim.stop()
        self._anim.setStartValue(self._opacity.opacity())
        self._anim.setEndValue(1.0)
        self.show()
        self._anim.start()
        self._hide_timer.start(max(500, duration_ms))

    def _fade_out(self):
        self._hide_timer.stop()
        self._anim.stop()
        self._anim.setStartValue(self._opacity.opacity())
        self._anim.setEndValue(0.0)
        try:
            self._anim.finished.disconnect(self._hide_after_fade)
        except Exception:
            pass
        self._anim.finished.connect(self._hide_after_fade)
        self._anim.start()

    def _hide_after_fade(self):
        try:
            self._anim.finished.disconnect(self._hide_after_fade)
        except Exception:
            pass
        self.hide()


class CapriWindow(QWidget):
    """Главное overlay-окно."""

    petted = pyqtSignal()
    file_dropped = pyqtSignal(str)

    def __init__(self, state: CapriState, bus: EventBus, assets_dir: str, parent=None):
        super().__init__(parent)
        self.state = state
        self.bus = bus
        self.assets_dir = assets_dir

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)

        self.animator = Animator(assets_dir, self)
        self.animator.set_base_size(state.size)
        self.animator.size_changed.connect(self._sync_size)

        # Layout, чтобы окно подстраивалось под размер аниматора
        from PyQt6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.animator)

        self.bubble = SpeechBubble()

        # Перетаскивание
        self._drag_pos: Optional[QPoint] = None
        self._click_time: float = 0.0
        self._click_count: int = 0

        # Позиция
        self.move(state.x, state.y)

        # Контекстное меню
        self._build_context_menu()

        # Таймер сохранения состояния
        self._save_timer = QTimer(self)
        self._save_timer.timeout.connect(self._save_state)
        self._save_timer.start(5000)

        # Idle-таймер: если долго не трогали — sleep
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._check_idle)
        self._idle_timer.start(10000)

        # Слушаем события шины
        bus.on("say", self._on_say)
        bus.on("animation", self._on_animation)
        bus.on("mood", self._on_mood)

        self.show()

    def _build_context_menu(self):
        self.menu = QMenu(self)
        self.menu.setStyleSheet(
            "QMenu { background: rgba(18,14,24,235); color: #f0e6ff; border: 1px solid rgba(180,120,255,180); border-radius: 8px; padding: 4px; }"
            "QMenu::item { padding: 6px 24px; border-radius: 4px; }"
            "QMenu::item:selected { background: rgba(120,60,200,180); }"
        )
        act_talk = self.menu.addAction("💬 Поговорить")
        act_talk.triggered.connect(lambda: self.bus.emit("say", "greeting"))
        act_files = self.menu.addAction("📁 Рабочая папка")
        act_files.triggered.connect(self._open_workspace)
        act_meta = self.menu.addAction("ℹ️ Метаданные активного окна")
        act_meta.triggered.connect(self._show_window_meta)
        self.menu.addSeparator()
        act_size = self.menu.addMenu("Размер")
        for sz in (180, 240, 300, 360):
            a = act_size.addAction(f"{sz}px")
            a.triggered.connect(lambda checked, s=sz: self._set_size(s))
        act_sound = self.menu.addAction("🔊 Звук: вкл/выкл")
        act_sound.triggered.connect(self._toggle_sound)
        self.menu.addSeparator()
        act_quit = self.menu.addAction("❌ Выход")
        act_quit.triggered.connect(QApplication.quit)

    def _set_size(self, size: int):
        self.state.size = size
        self.animator.set_base_size(size)
        self._save_state()

    def _toggle_sound(self):
        self.state.sound_enabled = not self.state.sound_enabled
        self._save_state()

    def _open_workspace(self):
        ws = self._workspace_dir()
        os.makedirs(ws, exist_ok=True)
        # Открываем в системном файловом менеджере
        import subprocess, sys
        try:
            if sys.platform == "win32":
                os.startfile(ws)
            elif sys.platform == "darwin":
                subprocess.run(["open", ws])
            else:
                subprocess.run(["xdg-open", ws])
        except Exception as e:
            self.bus.emit("say", "error")
            print(f"Не удалось открыть папку: {e}")

    def _workspace_dir(self) -> str:
        base = os.path.dirname(os.path.abspath(__file__))
        # рабочая папка рядом с приложением
        root = os.path.dirname(base)
        ws = os.path.join(root, "capri_workspace")
        os.makedirs(ws, exist_ok=True)
        return ws

    def _show_window_meta(self):
        try:
            from events.window_metadata import get_active_window_metadata
            meta = get_active_window_metadata()
            text = "\n".join(f"{k}: {v}" for k, v in meta.items())
            self.bubble.show_text(text, 6000)
        except Exception as e:
            self.bubble.show_text(f"Ошибка: {e}", 4000)

    def _sync_size(self):
        self.adjustSize()
        if self.bubble.isVisible():
            self.bubble.move(self.x() + self.width() // 2 - self.bubble.width() // 2,
                             self.y() - self.bubble.height() - 8)

    def _save_state(self):
        try:
            self.state.x = self.x()
            self.state.y = self.y()
            state_path = os.path.join(self.assets_dir, "..", "state.json")
            state_path = os.path.normpath(state_path)
            self.state.save(state_path)
        except Exception as e:
            print(f"save state error: {e}")

    def _check_idle(self):
        if time.time() - self.state.last_interaction > 120:
            if self.animator.current_name not in ("sleep", "laydown", "perch_sleep"):
                self.animator.load_clip("sleep")
                self.bus.emit("say", "idle")

    def _on_say(self, category: str = "greeting"):
        # Импортируем движок диалогов лениво
        try:
            from dialogue.engine import DialogueEngine
            eng = DialogueEngine(self.assets_dir)
            text = eng.pick(category, self.state)
            if text:
                self.state.bubble_text = text
                self.bubble.show_text(text)
                self.bubble.move(self.x() + self.width() // 2 - self.bubble.width() // 2,
                                 self.y() - self.bubble.height() - 8)
        except Exception as e:
            print(f"dialogue error: {e}")

    def _on_animation(self, name: str):
        if name in CLIP_TABLE:
            self.animator.load_clip(name)
            self.state.current_clip = name

    def _on_mood(self, delta: int):
        self.state.mood = max(0, min(100, self.state.mood + delta))

    # --- события мыши ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._click_time = time.time()
            self._click_count += 1
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            # Перемещаем пузырь вместе
            if self.bubble.isVisible():
                self.bubble.move(self.x() + self.width() // 2 - self.bubble.width() // 2,
                                 self.y() - self.bubble.height() - 8)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Если клик (не перетаскивание) — погладить
            if time.time() - self._click_time < 0.3 and self._click_count <= 2:
                self._pet()
            self._drag_pos = None
            self._click_count = 0
            event.accept()

    def _pet(self):
        self.state.last_interaction = time.time()
        self.state.mood = min(100, self.state.mood + 5)
        self.animator.load_clip("grin")
        self.bus.emit("say", "pet")
        QTimer.singleShot(1500, lambda: self.animator.load_clip("idle"))
        self.petted.emit()

    def mouseDoubleClickEvent(self, event):
        self.bus.emit("say", "greeting")

    def contextMenuEvent(self, event):
        self.menu.exec(event.globalPosition().toPoint())

    # --- drag & drop файлов ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.file_dropped.emit(path)
                self._handle_dropped_file(path)
        event.acceptProposedAction()

    def _handle_dropped_file(self, path: str):
        self.state.last_interaction = time.time()
        try:
            from files.manager import FileManager
            fm = FileManager(self._workspace_dir())
            meta = fm.metadata(path)
            text = f"Файл: {os.path.basename(path)}\n" + "\n".join(f"{k}: {v}" for k, v in meta.items())
            self.bubble.show_text(text, 6000)
            self.bubble.move(self.x() + self.width() // 2 - self.bubble.width() // 2,
                             self.y() - self.bubble.height() - 8)
        except Exception as e:
            self.bubble.show_text(f"Ошибка: {e}", 4000)
        self.animator.load_clip("click")
        QTimer.singleShot(1000, lambda: self.animator.load_clip("idle"))

    def enterEvent(self, event):
        self.state.last_interaction = time.time()
        if self.animator.current_name in ("idle", "sleep"):
            self.animator.load_clip("idle_blink")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.animator.current_name in ("idle_blink", "idle_blink_glitch"):
            self.animator.load_clip("idle")
        super().leaveEvent(event)

    def closeEvent(self, event):
        self._save_state()
        super().closeEvent(event)
