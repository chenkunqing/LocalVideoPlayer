"""控制栏覆盖层 — 播放控制 UI"""

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QFont, QIcon,
    QPixmap, QPainterPath,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QMenu, QGraphicsOpacityEffect, QSizePolicy, QSpacerItem,
)

from constants import SPEED_OPTIONS, SHORTCUTS
from progress_bar import VideoProgressBar
from theme import theme
from utils import format_time


class _GradientWidget(QWidget):
    """带渐变背景的容器（浮动在视频上方，始终使用深色渐变）"""

    def __init__(self, direction="bottom", parent=None):
        super().__init__(parent)
        self._direction = direction
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        p = QPainter(self)
        rect = self.rect()
        grad = QLinearGradient(0, 0, 0, rect.height())
        if self._direction == "bottom":
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(0.3, QColor(0, 0, 0, 100))
            grad.setColorAt(1, QColor(0, 0, 0, 240))
        else:
            grad.setColorAt(0, QColor(0, 0, 0, 200))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(rect, grad)
        p.end()


class _IconButton(QPushButton):
    """纯图标按钮，QPainter 绘制"""

    def __init__(self, icon_type, size=40, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_theme()
        theme.theme_changed.connect(self._apply_theme)

    def _apply_theme(self) -> None:
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {theme.color("hover")};
            }}
        """)

    def set_icon_type(self, icon_type):
        self._icon_type = icon_type
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(theme.color("text")), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = self.width() // 2, self.height() // 2
        s = 8

        if self._icon_type == "play":
            path = QPainterPath()
            path.moveTo(cx - 5, cy - 7)
            path.lineTo(cx + 7, cy)
            path.lineTo(cx - 5, cy + 7)
            path.closeSubpath()
            p.setBrush(QColor(theme.color("text")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)
        elif self._icon_type == "pause":
            p.setBrush(QColor(theme.color("text")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(cx - 6, cy - 7, 4, 14, 1, 1)
            p.drawRoundedRect(cx + 2, cy - 7, 4, 14, 1, 1)
        elif self._icon_type == "skip_back":
            p.setPen(QPen(QColor(theme.color("text")), 2))
            p.drawLine(cx + 4, cy - 5, cx - 2, cy)
            p.drawLine(cx - 2, cy, cx + 4, cy + 5)
            p.drawLine(cx - 4, cy - 5, cx - 4, cy + 5)
        elif self._icon_type == "skip_forward":
            p.setPen(QPen(QColor(theme.color("text")), 2))
            p.drawLine(cx - 4, cy - 5, cx + 2, cy)
            p.drawLine(cx + 2, cy, cx - 4, cy + 5)
            p.drawLine(cx + 4, cy - 5, cx + 4, cy + 5)
        elif self._icon_type == "volume_high":
            p.setPen(QPen(QColor(theme.color("text")), 1.5))
            p.drawLine(cx - 6, cy - 3, cx - 3, cy - 3)
            p.drawLine(cx - 3, cy - 3, cx + 1, cy - 6)
            p.drawLine(cx + 1, cy - 6, cx + 1, cy + 6)
            p.drawLine(cx + 1, cy + 6, cx - 3, cy + 3)
            p.drawLine(cx - 3, cy + 3, cx - 6, cy + 3)
            p.drawLine(cx - 6, cy + 3, cx - 6, cy - 3)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(cx + 2, cy - 4, 6, 8, -60 * 16, 120 * 16)
        elif self._icon_type == "volume_mute":
            p.setPen(QPen(QColor(theme.color("text")), 1.5))
            p.drawLine(cx - 6, cy - 3, cx - 3, cy - 3)
            p.drawLine(cx - 3, cy - 3, cx + 1, cy - 6)
            p.drawLine(cx + 1, cy - 6, cx + 1, cy + 6)
            p.drawLine(cx + 1, cy + 6, cx - 3, cy + 3)
            p.drawLine(cx - 3, cy + 3, cx - 6, cy + 3)
            p.drawLine(cx - 6, cy + 3, cx - 6, cy - 3)
            p.setPen(QPen(QColor(theme.color("text")), 2))
            p.drawLine(cx + 4, cy - 4, cx + 9, cy + 4)
            p.drawLine(cx + 9, cy - 4, cx + 4, cy + 4)
        elif self._icon_type == "fullscreen":
            p.setPen(QPen(QColor(theme.color("text")), 2))
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                x0, y0 = cx + dx * 7, cy + dy * 7
                p.drawLine(x0, y0, x0 - dx * 5, y0)
                p.drawLine(x0, y0, x0, y0 - dy * 5)
        elif self._icon_type == "fullscreen_exit":
            p.setPen(QPen(QColor(theme.color("text")), 2))
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                x0, y0 = cx + dx * 3, cy + dy * 3
                p.drawLine(x0, y0, x0 + dx * 5, y0)
                p.drawLine(x0, y0, x0, y0 + dy * 5)
        elif self._icon_type == "keyframe_add":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.color("accent")))
            path = QPainterPath()
            path.moveTo(cx, cy - 7)
            path.lineTo(cx + 6, cy)
            path.lineTo(cx, cy + 7)
            path.lineTo(cx - 6, cy)
            path.closeSubpath()
            p.drawPath(path)
            p.setPen(QPen(QColor(theme.color("text")), 2))
            p.drawLine(cx - 3, cy, cx + 3, cy)
            p.drawLine(cx, cy - 3, cx, cy + 3)
        elif self._icon_type == "keyframe_prev":
            p.setPen(QPen(QColor(theme.color("accent")), 2))
            p.drawLine(cx + 3, cy - 5, cx - 3, cy)
            p.drawLine(cx - 3, cy, cx + 3, cy + 5)
            p.drawLine(cx - 4, cy - 5, cx - 4, cy + 5)
        elif self._icon_type == "keyframe_next":
            p.setPen(QPen(QColor(theme.color("accent")), 2))
            p.drawLine(cx - 3, cy - 5, cx + 3, cy)
            p.drawLine(cx + 3, cy, cx - 3, cy + 5)
            p.drawLine(cx + 4, cy - 5, cx + 4, cy + 5)

        p.end()


class ControlsOverlay(QWidget):
    fullscreen_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

        self._paused = True
        self._duration = 0.0
        self._is_fullscreen = False
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部信息栏（浮动在视频上方，始终深色文字）
        self._top_bar = _GradientWidget("top")
        self._top_bar.setFixedHeight(80)
        self._top_bar.setMouseTracking(True)
        self._top_opacity = QGraphicsOpacityEffect(self._top_bar)
        self._top_opacity.setOpacity(1.0)
        self._top_bar.setGraphicsEffect(self._top_opacity)
        self._top_fade = QPropertyAnimation(self._top_opacity, b"opacity")
        self._top_fade.setDuration(300)
        self._top_fade.setEasingCurve(QEasingCurve.Type.InOutQuad)
        top_layout = QVBoxLayout(self._top_bar)
        top_layout.setContentsMargins(24, 12, 24, 0)
        self._title_label = QLabel("KK Player")
        self._title_label.setStyleSheet("color: #fafafa; font-size: 18px; font-weight: bold; background: transparent;")
        self._meta_label = QLabel("拖拽视频文件到此处开始播放")
        self._meta_label.setStyleSheet("color: #71717a; font-size: 12px; background: transparent;")
        top_layout.addWidget(self._title_label)
        top_layout.addWidget(self._meta_label)
        layout.addWidget(self._top_bar)

        # 中间透明区域（点击播放/暂停）
        self._center = QWidget()
        self._center.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._center.setAutoFillBackground(False)
        self._center.setStyleSheet("background: transparent;")
        self._center.setMouseTracking(True)
        layout.addWidget(self._center, 1)

        # 底部控制栏（独立于视频区域）
        self._bottom_bar = QWidget()
        self._bottom_bar.setFixedHeight(110)
        self._bottom_bar.setMouseTracking(True)
        bottom_layout = QVBoxLayout(self._bottom_bar)
        bottom_layout.setContentsMargins(16, 20, 16, 12)
        bottom_layout.setSpacing(8)

        # 进度条
        self.progress_bar = VideoProgressBar()
        bottom_layout.addWidget(self.progress_bar)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        # 左侧按钮
        self._play_btn = _IconButton("pause")
        self._play_btn.setToolTip(f"播放/暂停 ({SHORTCUTS['play_pause']})")
        self._play_btn.clicked.connect(self._on_play_clicked)
        btn_row.addWidget(self._play_btn)

        self._prev_kf_btn = _IconButton("keyframe_prev", 36)
        self._prev_kf_btn.setToolTip(f"上一关键帧 ({SHORTCUTS['keyframe_prev']})")
        btn_row.addWidget(self._prev_kf_btn)

        self._next_kf_btn = _IconButton("keyframe_next", 36)
        self._next_kf_btn.setToolTip(f"下一关键帧 ({SHORTCUTS['keyframe_next']})")
        btn_row.addWidget(self._next_kf_btn)

        # 音量组
        self._vol_btn = _IconButton("volume_high", 36)
        self._vol_btn.setToolTip(f"静音 ({SHORTCUTS['mute_toggle']})")
        self._vol_btn.clicked.connect(self._on_mute_clicked)
        btn_row.addWidget(self._vol_btn)

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setToolTip(f"音量 ({SHORTCUTS['volume_up']}/{SHORTCUTS['volume_down']})")
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(100)
        self._vol_slider.setFixedWidth(80)
        btn_row.addWidget(self._vol_slider)

        # 时间标签
        self._time_label = QLabel("0:00 / 0:00")
        btn_row.addWidget(self._time_label)

        btn_row.addStretch()

        # 右侧按钮
        self._add_kf_btn = _IconButton("keyframe_add", 36)
        self._add_kf_btn.setToolTip(f"添加关键帧 ({SHORTCUTS['keyframe_add']})")
        btn_row.addWidget(self._add_kf_btn)

        # 倍速按钮
        self._speed_btn = QPushButton("1.0x")
        self._speed_btn.setToolTip(f"播放倍速 ({SHORTCUTS['speed_down']}/{SHORTCUTS['speed_up']})")
        self._speed_btn.setFixedSize(48, 32)
        self._speed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._speed_menu = QMenu(self)
        for spd in SPEED_OPTIONS:
            action = self._speed_menu.addAction(f"{spd}x")
            action.setData(spd)
        self._speed_btn.setMenu(self._speed_menu)
        btn_row.addWidget(self._speed_btn)

        # 全屏按钮
        self._fs_btn = _IconButton("fullscreen", 36)
        self._fs_btn.setToolTip(f"全屏 ({SHORTCUTS['fullscreen_toggle']})")
        self._fs_btn.clicked.connect(self._on_fullscreen_clicked)
        btn_row.addWidget(self._fs_btn)

        bottom_layout.addLayout(btn_row)

        self._apply_theme()
        theme.theme_changed.connect(self._apply_theme)

    def _apply_theme(self) -> None:
        self._bottom_bar.setStyleSheet(f"background-color: {theme.color('panel')};")
        self._vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {theme.color("border")};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: white;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.color("text_dim")};
                border-radius: 2px;
            }}
        """)
        self._time_label.setStyleSheet(f"""
            color: {theme.color("text_dim")};
            font-size: 12px;
            font-family: 'Consolas', 'Courier New', monospace;
            background: transparent;
            padding-left: 8px;
        """)
        self._speed_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {theme.color("text")};
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {theme.color("hover")};
            }}
        """)
        self._speed_menu.setStyleSheet(f"""
            QMenu {{
                background: {theme.color("menu_bg")};
                border: 1px solid {theme.color("border")};
                border-radius: 8px;
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 6px 16px;
                color: {theme.color("text")};
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background: {theme.color("hover_strong")};
            }}
        """)

    # region 公开接口

    def update_position(self, seconds):
        self.progress_bar.set_position(seconds)
        pos_str = format_time(seconds)
        dur_str = format_time(self._duration)
        self._time_label.setText(f"{pos_str} / {dur_str}")

    def update_duration(self, seconds):
        self._duration = seconds
        self.progress_bar.set_duration(seconds)

    def update_pause_state(self, paused):
        self._paused = paused
        self._play_btn.set_icon_type("play" if paused else "pause")

    def set_video_title(self, title, meta=""):
        self._title_label.setText(title)
        self._meta_label.setText(meta)

    def set_keyframes(self, keyframes):
        self.progress_bar.set_keyframes(keyframes)

    def set_fullscreen_state(self, is_fs):
        self._is_fullscreen = is_fs
        self._fs_btn.set_icon_type("fullscreen_exit" if is_fs else "fullscreen")

    def show_controls(self):
        self._top_fade.stop()
        self._top_fade.setStartValue(self._top_opacity.opacity())
        self._top_fade.setEndValue(1.0)
        self._top_fade.start()

    def hide_controls(self):
        self._top_fade.stop()
        self._top_fade.setStartValue(self._top_opacity.opacity())
        self._top_fade.setEndValue(0.0)
        self._top_fade.start()

    def update_tooltips(self, config) -> None:
        """根据当前快捷键配置刷新所有按钮 tooltip"""
        self._play_btn.setToolTip(f"播放/暂停 ({config.get('play_pause')})")
        self._prev_kf_btn.setToolTip(f"上一关键帧 ({config.get('keyframe_prev')})")
        self._next_kf_btn.setToolTip(f"下一关键帧 ({config.get('keyframe_next')})")
        self._vol_btn.setToolTip(f"静音 ({config.get('mute_toggle')})")
        self._vol_slider.setToolTip(f"音量 ({config.get('volume_up')}/{config.get('volume_down')})")
        self._add_kf_btn.setToolTip(f"添加关键帧 ({config.get('keyframe_add')})")
        self._speed_btn.setToolTip(f"播放倍速 ({config.get('speed_down')}/{config.get('speed_up')})")
        self._fs_btn.setToolTip(f"全屏 ({config.get('fullscreen_toggle')})")

    # endregion

    # region 信号连接点

    @property
    def play_button(self):
        return self._play_btn

    @property
    def prev_keyframe_button(self):
        return self._prev_kf_btn

    @property
    def next_keyframe_button(self):
        return self._next_kf_btn

    @property
    def add_keyframe_button(self):
        return self._add_kf_btn

    @property
    def volume_slider(self):
        return self._vol_slider

    @property
    def volume_button(self):
        return self._vol_btn

    @property
    def speed_menu(self):
        return self._speed_menu

    @property
    def speed_button(self):
        return self._speed_btn

    @property
    def fullscreen_button(self):
        return self._fs_btn

    # endregion

    # region 内部槽

    def _on_play_clicked(self):
        pass  # 由 main_window 连接

    def _on_mute_clicked(self):
        pass  # 由 main_window 连接

    def _on_fullscreen_clicked(self):
        self.fullscreen_requested.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            top_rect = self._top_bar.geometry()
            if not top_rect.contains(int(pos.x()), int(pos.y())):
                return  # 由 main_window 处理中心区域点击
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            top_rect = self._top_bar.geometry()
            if not top_rect.contains(int(pos.x()), int(pos.y())):
                self.fullscreen_requested.emit()

    # endregion
