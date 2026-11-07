# overlay/window.py — прозрачное overlay-окно
import os
import sys

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class CapriWindow(QWidget):
    # Сигналы
    close_requested = pyqtSignal()
    minimize_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._setup_window()
        self._setup_ui()
        self._setup_timers()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 460)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Контролы
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addStretch()
        self.btn_min = QPushButton("─")
        self.btn_min.setFixedSize(24, 24)
        self.btn_min.setStyleSheet(self._btn_style())
        self.btn_min.clicked.connect(self.minimize_requested.emit)
        ctrl_layout.addWidget(self.btn_min)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet(self._btn_style())
        self.btn_close.clicked.connect(self.close_requested.emit)
        ctrl_layout.addWidget(self.btn_close)
        layout.addLayout(ctrl_layout)

        # Аватар
        self.avatar_label = QLabel()
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_path = os.path.join(ASSETS_DIR, "sprites", "capri_300.png")
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.avatar_label.setPixmap(pixmap.scaled(
                260, 380,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.avatar_label.setText("CAPRI")
            self.avatar_label.setStyleSheet("color: #ff2d95; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.avatar_label)

        # Диалог
        self.dialogue_label = QLabel()
        self.dialogue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dialogue_label.setWordWrap(True)
        self.dialogue_label.setStyleSheet("""
            QLabel {
                background: rgba(10, 10, 20, 0.88);
                color: #e0e0e0;
                border: 1px solid #ff2d95;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 12px;
            }
        """)
        self.dialogue_label.hide()
        layout.addWidget(self.dialogue_label)

        # Статус
        self.status_label = QLabel("Capri // Online")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #00ff88; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(self.status_label)

    def _btn_style(self):
        return """
            QPushButton {
                background: rgba(10, 10, 20, 0.88);
                color: #00e5ff;
                border: 1px solid #00e5ff;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #00e5ff;
                color: #000;
            }
        """

    def _setup_timers(self):
        self._dialogue_timer = QTimer(self)
        self._dialogue_timer.setSingleShot(True)
        self._dialogue_timer.timeout.connect(self._hide_dialogue)

    def show_dialogue(self, text: str, duration: int = 4000):
        self.dialogue_label.setText(text)
        self.dialogue_label.show()
        self._dialogue_timer.start(duration)

    def _hide_dialogue(self):
        self.dialogue_label.hide()

    def update_status(self, text: str):
        self.status_label.setText(text)

    # --- Перетаскивание окна ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()