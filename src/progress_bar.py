"""自绘进度条 — 含关键帧标记"""

from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QBrush
from PySide6.QtWidgets import QWidget, QToolTip

from constants import COLOR_ACCENT, COLOR_ACCENT_LIGHT, COLOR_PROGRESS_BG, COLOR_WHITE
from utils import format_time


class VideoProgressBar(QWidget):
    seek_requested = Signal(float)
    drag_seek_requested = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0.0
        self._position = 0.0
        self._keyframes = []
        self._hover_x = -1
        self._dragging = False
        self._hovered = False

        self.setFixedHeight(24)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_position(self, seconds):
        if not self._dragging:
            self._position = seconds
            self.update()

    def set_duration(self, seconds):
        self._duration = seconds
        self.update()

    def set_keyframes(self, keyframes):
        self._keyframes = sorted(keyframes)
        self.update()

    def _time_at_x(self, x):
        if self.width() <= 0 or self._duration <= 0:
            return 0.0
        ratio = max(0.0, min(1.0, x / self.width()))
        return ratio * self._duration

    def _x_at_time(self, t):
        if self._duration <= 0:
            return 0
        return int((t / self._duration) * self.width())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        marker_zone_h = 8
        bar_h = 6 if self._hovered else 4
        bar_y = marker_zone_h + (16 - marker_zone_h - bar_h) // 2 + marker_zone_h // 2
        radius = bar_h / 2

        # 轨道背景
        bg_color = QColor(COLOR_PROGRESS_BG)
        bg_color.setAlphaF(0.6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg_color)
        p.drawRoundedRect(QRectF(0, bar_y, w, bar_h), radius, radius)

        if self._duration > 0:
            # 已播放进度
            played_w = (self._position / self._duration) * w
            accent = QColor(COLOR_ACCENT)
            p.setBrush(accent)
            p.drawRoundedRect(QRectF(0, bar_y, played_w, bar_h), radius, radius)

            # 拖拽手柄
            if self._hovered or self._dragging:
                handle_r = 7
                handle_x = max(handle_r, min(w - handle_r, played_w))
                handle_y = bar_y + bar_h / 2
                p.setBrush(QColor(COLOR_WHITE))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(handle_x, handle_y), handle_r, handle_r)

        # 关键帧标记（三角形）
        marker_color = QColor(COLOR_ACCENT_LIGHT)
        p.setBrush(marker_color)
        p.setPen(Qt.PenStyle.NoPen)
        for kf in self._keyframes:
            if self._duration <= 0:
                break
            kx = self._x_at_time(kf)
            triangle = QPainterPath()
            ty = bar_y - 2
            triangle.moveTo(kx - 4, ty - 6)
            triangle.lineTo(kx + 4, ty - 6)
            triangle.lineTo(kx, ty)
            triangle.closeSubpath()
            p.drawPath(triangle)

        p.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self._hover_x = -1
        self.update()

    def mouseMoveEvent(self, event):
        self._hover_x = int(event.position().x())
        if self._dragging:
            t = self._time_at_x(self._hover_x)
            self._position = t
            self.drag_seek_requested.emit(t)
            self.update()
        time_str = format_time(self._time_at_x(self._hover_x))
        QToolTip.showText(event.globalPosition().toPoint(), time_str, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            t = self._time_at_x(int(event.position().x()))
            self._position = t
            self.drag_seek_requested.emit(t)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            t = self._time_at_x(int(event.position().x()))
            self.seek_requested.emit(t)
            self.update()
