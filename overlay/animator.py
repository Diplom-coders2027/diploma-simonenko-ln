"""Аниматор спрайтов: нарезка sprite sheets и проигрывание кадров."""
import os
from typing import Dict, List, Optional

from PIL import Image
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt6.QtWidgets import QWidget


# Смещения для perch-клипов (из C#) — определены ДО таблицы
PERCH_SHIFT_X = 26.0 / 384 * 1.0
PERCH_SHIFT_Y = 36.0 / 384 * 1.0

# Таблица клипов: name -> (count, fps, height_mult, shiftX, shiftY)
# Порт из cross/Pet.cs (Capri Desktop). size базовый = 240px, арт = 384px.
CLIP_TABLE: Dict[str, tuple] = {
    "idle": (60, 24, 1.11, 11.0 / 384 * 1.11, 0.0),
    "idle_blink": (8, 24, 1.11, 11.0 / 384 * 1.11, 0.0),
    "idle_blink_glitch": (8, 24, 1.11, 11.0 / 384 * 1.11, 0.0),
    "idle_mouth": (5, 12, 1.11, 11.0 / 384 * 1.11, 0.0),
    "idle_legacy": (16, 8, 1.11, 11.0 / 384 * 1.11, 0.0),
    "laydown": (60, 12, 1.0, 0.0, 0.0),
    "laydown_blink": (8, 8, 1.0, 0.0, 0.0),
    "laydown_blink_glitch": (8, 8, 1.0, 0.0, 0.0),
    "laydown_glitch": (10, 15, 1.0, 0.0, 0.0),
    "laydown_leave": (12, 15, 1.0, 0.0, 0.0),
    "laydown_sleep": (60, 6, 1.0, 0.0, 0.0),
    "laydown_talk": (60, 12, 1.0, 0.0, 0.0),
    "perch_talk": (60, 30, 1.0, PERCH_SHIFT_X, PERCH_SHIFT_Y),
    "blink": (4, 8, 1.11, 0.0, 0.0),
    "blink_glitch": (4, 8, 1.11, 0.0, 0.0),
    "glitch": (10, 15, 1.11, 0.0, 0.0),
    "dangle": (24, 10, 1.11, 0.0, 0.0),
    "perch": (60, 30, 1.0, 0.0, 0.0),  # shift задаётся отдельно
    "perch_blink": (8, 30, 1.0, 0.0, 0.0),
    "perch_blink_glitch": (8, 30, 1.0, 0.0, 0.0),
    "perch_glitch": (10, 15, 1.0, 0.0, 0.0),
    "perch_sleep": (8, 30, 1.0, 0.0, 0.0),
    "mouth": (5, 12, 1.11, 0.0, 0.0),
    "walk": (12, 12, 1.11, 0.0, 0.0),
    "dance": (16, 16, 1.11, 0.0, 0.0),
    "perch_music": (60, 30, 1.0, 0.0, 0.0),
    "arrive": (14, 15, 1.11, 0.0, 0.0),
    "leave": (12, 15, 1.11, 0.0, 0.0),
    "perch_arrive": (14, 15, 1.0, 0.0, 0.0),
    "perch_leave": (12, 15, 1.0, 0.0, 0.0),
    "grin": (16, 8, 1.11, 0.0, 0.0),
    "sleep": (16, 6, 1.11, 0.0, 0.0),
    "wake": (13, 15, 1.11, 0.0, 0.0),
    "click": (12, 12, 1.11, 0.0, 0.0),  # click.png: 2880x144 -> 12 frames x 240
    "form": (1, 1, 1.11, 0.0, 0.0),
    "face": (1, 1, 1.11, 0.0, 0.0),
}

# Смещения для perch-клипов (из C#)
PERCH_SHIFT_X = 26.0 / 384 * 1.0
PERCH_SHIFT_Y = 36.0 / 384 * 1.0

# Применяем perch-смещения
for k in ("perch", "perch_blink", "perch_blink_glitch", "perch_glitch", "perch_sleep",
          "perch_music", "perch_arrive", "perch_leave"):
    c, f, h, sx, sy = CLIP_TABLE[k]
    CLIP_TABLE[k] = (c, f, h, PERCH_SHIFT_X, PERCH_SHIFT_Y)


def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    """Конвертирует PIL Image (RGBA) в QPixmap."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


class Clip:
    """Один спрайт-лист: нарезка на кадры + параметры."""

    def __init__(self, name: str, assets_dir: str):
        self.name = name
        base_name = name.replace("_flipped", "")
        if name not in CLIP_TABLE:
            if base_name in CLIP_TABLE:
                self.count, self.fps, self.height_mult, self.shift_x, self.shift_y = CLIP_TABLE[base_name]
            else:
                # fallback: treat as single frame
                self.count, self.fps, self.height_mult, self.shift_x, self.shift_y = 1, 8, 1.11, 0.0, 0.0
        else:
            self.count, self.fps, self.height_mult, self.shift_x, self.shift_y = CLIP_TABLE[name]

        path = os.path.join(assets_dir, "sprites", name + ".png")
        if not os.path.exists(path):
            # flipped-версии: ищем базовый
            base = name.replace("_flipped", "")
            path = os.path.join(assets_dir, "sprites", base + ".png")
        self.flipped = "_flipped" in name

        self.strip: Optional[Image.Image] = None
        self.frames: List[QPixmap] = []
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
                self.strip = img
                w, h = img.size
                if self.count <= 0 or w % self.count != 0:
                    # fallback: один кадр
                    self.count = 1
                frame_w = w // self.count
                for i in range(self.count):
                    box = (i * frame_w, 0, (i + 1) * frame_w, h)
                    frame = img.crop(box)
                    if self.flipped:
                        frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
                    self.frames.append(pil_to_qpixmap(frame))
            except Exception as e:
                print(f"[Animator] ошибка загрузки {name}: {e}")

    @property
    def frame_count(self) -> int:
        return max(1, len(self.frames))

    @property
    def interval_ms(self) -> int:
        return max(1, int(1000.0 / self.fps))

    def frame(self, index: int) -> Optional[QPixmap]:
        if not self.frames:
            return None
        return self.frames[index % len(self.frames)]


class Animator(QWidget):
    """Виджет-аниматор: показывает текущий кадр клипа."""

    size_changed = pyqtSignal()

    def __init__(self, assets_dir: str, parent=None):
        super().__init__(parent)
        self.assets_dir = assets_dir
        self._clips: Dict[str, Clip] = {}
        self._current_name: str = "idle"
        self._current: Optional[Clip] = None
        self._frame_index: int = 0
        self._playing: bool = True
        self._base_size: int = 240

        # Прозрачность
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # Тень
        try:
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            from PyQt6.QtGui import QColor
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(24)
            shadow.setColor(QColor(0, 0, 0, 150))
            shadow.setOffset(0, 10)
            self.setGraphicsEffect(shadow)
        except Exception:
            pass

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self.load_clip("idle")

    def base_size(self) -> int:
        return self._base_size

    def set_base_size(self, size: int) -> None:
        self._base_size = size
        self._update_geometry()

    def load_clip(self, name: str) -> None:
        if name not in self._clips:
            self._clips[name] = Clip(name, self.assets_dir)
        self._current_name = name
        self._current = self._clips[name]
        self._frame_index = 0
        if self._playing:
            self._timer.start(self._current.interval_ms)
        self._update_geometry()
        self.update()

    @property
    def current_name(self) -> str:
        return self._current_name

    def play(self) -> None:
        self._playing = True
        if self._current is not None:
            self._timer.start(self._current.interval_ms)

    def pause(self) -> None:
        self._playing = False
        self._timer.stop()

    def _advance(self) -> None:
        if self._current is None:
            return
        self._frame_index = (self._frame_index + 1) % self._current.frame_count
        self.update()

    def _update_geometry(self) -> None:
        if self._current is None:
            return
        h_mult = self._current.height_mult
        tall = self._base_size * h_mult
        wide = tall * self._current.frames[0].width() / self._current.frames[0].height() if self._current.frames else tall
        # Используем размеры кадра спрайта
        if self._current.frames:
            fw = self._current.frames[0].width()
            fh = self._current.frames[0].height()
            tall = self._base_size * h_mult
            wide = tall * fw / fh
        # Размер окна = размер кадра (1:1) + запас, без масштабирования спрайтов
        pad_x, pad_y = 60, 40
        self.setFixedSize(fw + pad_x, fh + pad_y)
        self.resize(fw + pad_x, fh + pad_y)
        self.updateGeometry()
        self.size_changed.emit()

    def paintEvent(self, event):
        if self._current is None:
            return
        pm = self._current.frame(self._frame_index)
        if pm is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        # Рисуем кадр 1:1, центрированный, без масштабирования
        try:
            sx = int(self._current.shift_x * self._base_size)
            sy = int(self._current.shift_y * self._base_size)
        except Exception:
            sx, sy = 0, 0
        x = (self.width() - pm.width()) // 2 + sx
        y = (self.height() - pm.height()) // 2 + sy
        painter.drawPixmap(x, y, pm)
        painter.end()
