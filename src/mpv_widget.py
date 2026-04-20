"""mpv 嵌入 QWidget — 视频渲染核心"""

import locale

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget


class MpvWidget(QWidget):
    position_changed = Signal(float)
    duration_changed = Signal(float)
    pause_changed = Signal(bool)
    eof_reached = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setStyleSheet("background: black;")

        locale.setlocale(locale.LC_NUMERIC, "C")

        import mpv
        self.player = mpv.MPV(
            wid=str(int(self.winId())),
            vo="gpu",
            hwdec="auto-safe",
            keep_open="yes",
            input_default_bindings=False,
            input_vo_keyboard=False,
            osc=False,
            cursor_autohide="no",
            msg_level="all=warn",
        )

        self.player.observe_property("time-pos", self._on_time_pos)
        self.player.observe_property("duration", self._on_duration)
        self.player.observe_property("pause", self._on_pause)
        self.player.observe_property("eof-reached", self._on_eof)

    def _on_time_pos(self, _name, value):
        if value is not None:
            self.position_changed.emit(float(value))

    def _on_duration(self, _name, value):
        if value is not None:
            self.duration_changed.emit(float(value))

    def _on_pause(self, _name, value):
        if value is not None:
            self.pause_changed.emit(bool(value))

    def _on_eof(self, _name, value):
        if value:
            self.eof_reached.emit()

    def play(self, path):
        self.player.play(path)

    def toggle_pause(self):
        self.player.pause = not self.player.pause

    def set_pause(self, paused):
        self.player.pause = paused

    def seek(self, seconds, reference="relative"):
        self.player.seek(seconds, reference=reference)

    def seek_absolute(self, seconds):
        self.player.seek(seconds, reference="absolute", precision="exact")

    def seek_keyframe(self, seconds):
        """拖拽时使用关键帧精度（更快）"""
        self.player.seek(seconds, reference="absolute", precision="keyframes")

    def set_volume(self, value):
        self.player.volume = max(0, min(100, value))

    def get_volume(self):
        return self.player.volume or 100

    def set_speed(self, speed):
        self.player.speed = speed

    def get_speed(self):
        return self.player.speed or 1.0

    @property
    def current_position(self):
        return self.player.time_pos or 0.0

    @property
    def current_duration(self):
        return self.player.duration or 0.0

    def destroy(self):
        self.player.terminate()
