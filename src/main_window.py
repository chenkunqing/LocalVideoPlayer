"""主窗口 — 编排所有组件"""

import os

from PySide6.QtCore import Qt, QTimer, QUrl, QEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget

from constants import (
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    CONTROLS_HIDE_DELAY_MS, VIDEO_EXTENSIONS,
)
from title_bar import TitleBar
from mpv_widget import MpvWidget
from controls_overlay import ControlsOverlay
from keyframe_manager import KeyframeManager
from shortcut_config import ShortcutConfig
from video_library import VideoLibrary
from playlist_view import PlaylistView
from shortcuts import setup_shortcuts
from utils import format_time


class MainWindow(QWidget):

    def __init__(self, data_dir):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("KK Player")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#MainWindow { background-color: #09090b; }")
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        self.current_file = None
        self._pre_mute_volume = 100
        self._is_fullscreen = False

        # 关键帧管理器
        self.keyframe_manager = KeyframeManager(data_dir)

        # 视频库
        self.video_library = VideoLibrary(data_dir)

        # 快捷键配置
        self.shortcut_config = ShortcutConfig(data_dir)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        self.title_bar = TitleBar()
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_requested.connect(self._toggle_maximize)
        self.title_bar.close_requested.connect(self.close)
        self.title_bar.home_requested.connect(self.show_library)
        main_layout.addWidget(self.title_bar)

        # 主视图切换（库视图 / 播放器视图）
        self._view_stack = QStackedWidget()

        # 库视图
        self.playlist_view = PlaylistView(self.video_library, self.shortcut_config)
        self.playlist_view.play_video_requested.connect(self._on_play_requested)
        self._view_stack.addWidget(self.playlist_view)

        # 播放器视图（视频 + 底部控制栏）
        player_view = QWidget()
        player_view.setMouseTracking(True)
        pv_layout = QVBoxLayout(player_view)
        pv_layout.setContentsMargins(0, 0, 0, 0)
        pv_layout.setSpacing(0)

        self.mpv_widget = MpvWidget()
        self.controls_overlay = ControlsOverlay()

        # 顶部信息栏浮动在视频上方（不参与布局）
        self.controls_overlay._top_bar.setParent(self.mpv_widget)
        self.controls_overlay._top_bar.raise_()
        self.mpv_widget.installEventFilter(self)

        pv_layout.addWidget(self.mpv_widget, 1)
        pv_layout.addWidget(self.controls_overlay._bottom_bar)

        self._view_stack.addWidget(player_view)

        main_layout.addWidget(self._view_stack, 1)

        # 信号连接
        self._connect_signals()

        # 快捷键
        self._shortcuts = setup_shortcuts(self, self.shortcut_config)
        self.shortcut_config.shortcuts_changed.connect(self._rebuild_shortcuts)
        self.controls_overlay.update_tooltips(self.shortcut_config)

        # 控制栏自动隐藏
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide_timer)
        self._hide_timer.start(CONTROLS_HIDE_DELAY_MS)

        # 窗口大小调整边距（无边框窗口，委托系统原生调整）
        self._resize_margin = 8

    def _connect_signals(self):
        mpv = self.mpv_widget
        overlay = self.controls_overlay

        mpv.position_changed.connect(overlay.update_position)
        mpv.duration_changed.connect(overlay.update_duration)
        mpv.pause_changed.connect(overlay.update_pause_state)

        overlay.progress_bar.seek_requested.connect(mpv.seek_absolute)
        overlay.progress_bar.drag_seek_requested.connect(mpv.seek_keyframe)

        overlay.play_button.clicked.connect(self._play_or_restart)
        overlay.fullscreen_requested.connect(self.toggle_fullscreen)

        overlay.volume_slider.valueChanged.connect(lambda v: mpv.set_volume(v))

        overlay.speed_menu.triggered.connect(self._on_speed_selected)

        overlay.add_keyframe_button.clicked.connect(self._add_keyframe)
        overlay.prev_keyframe_button.clicked.connect(self._prev_keyframe)
        overlay.next_keyframe_button.clicked.connect(self._next_keyframe)

        overlay.volume_button.clicked.connect(self.toggle_mute)

    def _rebuild_shortcuts(self) -> None:
        for sc in self._shortcuts:
            sc.deleteLater()
        self._shortcuts = setup_shortcuts(self, self.shortcut_config)
        self.controls_overlay.update_tooltips(self.shortcut_config)

    def _on_play_requested(self, path: str):
        self.play_file(path)

    def show_library(self):
        """切换到库视图"""
        self.mpv_widget.set_pause(True)
        self._view_stack.setCurrentIndex(0)
        self.title_bar.set_mode("library")

    def show_player(self):
        """切换到播放器视图"""
        self._view_stack.setCurrentIndex(1)
        self.title_bar.set_mode("player")

    def play_file(self, path):
        self.current_file = os.path.normpath(path)
        name = os.path.basename(path)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        ext = os.path.splitext(path)[1].upper().lstrip(".")
        meta = f"{size_mb:.1f} MB · {ext}"
        self.controls_overlay.set_video_title(name, meta)
        self.mpv_widget.play(self.current_file)
        self.refresh_keyframes()
        self.show_player()
        self.video_library.add_recent(self.current_file)

    def refresh_keyframes(self):
        if self.current_file:
            kfs = self.keyframe_manager.get_keyframes(self.current_file)
            self.controls_overlay.set_keyframes(kfs)

    def _play_or_restart(self):
        if self.mpv_widget.is_eof:
            self.mpv_widget.seek_absolute(0)
            self.mpv_widget.set_pause(False)
        else:
            self.mpv_widget.toggle_pause()

    def toggle_fullscreen(self):
        if self._is_fullscreen:
            self.exit_fullscreen()
        else:
            self._is_fullscreen = True
            self.title_bar.hide()
            self.showFullScreen()
            self.controls_overlay.set_fullscreen_state(True)

    def exit_fullscreen(self):
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.title_bar.show()
            self.showNormal()
            self.controls_overlay.set_fullscreen_state(False)

    def toggle_mute(self):
        current = self.mpv_widget.get_volume()
        if current > 0:
            self._pre_mute_volume = current
            self.mpv_widget.set_volume(0)
            self.controls_overlay.volume_slider.setValue(0)
            self.controls_overlay.volume_button.set_icon_type("volume_mute")
        else:
            self.mpv_widget.set_volume(self._pre_mute_volume)
            self.controls_overlay.volume_slider.setValue(int(self._pre_mute_volume))
            self.controls_overlay.volume_button.set_icon_type("volume_high")

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.title_bar.set_maximized_icon(False)
        else:
            self.showMaximized()
            self.title_bar.set_maximized_icon(True)

    def _on_speed_selected(self, action):
        speed = action.data()
        if speed:
            self.mpv_widget.set_speed(speed)
            self.controls_overlay.speed_button.setText(f"{speed}x")

    def _add_keyframe(self):
        if self.current_file:
            pos = self.mpv_widget.current_position
            self.keyframe_manager.add_keyframe(self.current_file, pos)
            self.refresh_keyframes()

    def _next_keyframe(self):
        if self.current_file:
            nxt = self.keyframe_manager.get_next_keyframe(
                self.current_file, self.mpv_widget.current_position
            )
            if nxt is not None:
                self.mpv_widget.seek_absolute(nxt)

    def _prev_keyframe(self):
        if self.current_file:
            prev = self.keyframe_manager.get_prev_keyframe(
                self.current_file, self.mpv_widget.current_position
            )
            if prev is not None:
                self.mpv_widget.seek_absolute(prev)

    def _on_hide_timer(self):
        if not self.controls_overlay._paused:
            self.controls_overlay.hide_controls()
            self.setCursor(Qt.CursorShape.BlankCursor)

    def mouseMoveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self._view_stack.currentIndex() == 1:
            self.controls_overlay.show_controls()
            self._hide_timer.start(CONTROLS_HIDE_DELAY_MS)

        # 无边框窗口：悬停时更新光标
        if not self._is_fullscreen and not self.isMaximized():
            self._update_resize_cursor(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.position().toPoint())
            if edge and not self._is_fullscreen and not self.isMaximized():
                qt_edges = self._to_qt_edges(edge)
                if qt_edges and self.windowHandle():
                    self.windowHandle().startSystemResize(qt_edges)
                    return
        # 点击视频区域 → 播放/暂停（仅播放器可见时）
        if self._view_stack.currentIndex() == 1:
            pos = event.position()
            title_h = self.title_bar.height() if self.title_bar.isVisible() else 0
            if pos.y() > title_h:
                overlay = self.controls_overlay
                g_top = overlay._top_bar.geometry()
                local_y = pos.y() - title_h
                bottom_bar = overlay._bottom_bar
                if not g_top.contains(int(pos.x()), int(local_y)) and \
                   not bottom_bar.underMouse():
                    if self.mpv_widget.is_eof:
                        self.mpv_widget.seek_absolute(0)
                        self.mpv_widget.set_pause(False)
                    else:
                        self.mpv_widget.toggle_pause()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def _get_resize_edge(self, pos):
        m = self._resize_margin
        w, h = self.width(), self.height()
        edges = []
        if pos.x() < m:
            edges.append("left")
        elif pos.x() > w - m:
            edges.append("right")
        if pos.y() < m:
            edges.append("top")
        elif pos.y() > h - m:
            edges.append("bottom")
        return "_".join(edges) if edges else None

    def _update_resize_cursor(self, pos):
        edge = self._get_resize_edge(pos)
        cursors = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "top_left": Qt.CursorShape.SizeFDiagCursor,
            "bottom_right": Qt.CursorShape.SizeFDiagCursor,
            "top_right": Qt.CursorShape.SizeBDiagCursor,
            "bottom_left": Qt.CursorShape.SizeBDiagCursor,
        }
        if edge and edge in cursors:
            self.setCursor(cursors[edge])

    _EDGE_MAP = {
        "left": Qt.Edge.LeftEdge,
        "right": Qt.Edge.RightEdge,
        "top": Qt.Edge.TopEdge,
        "bottom": Qt.Edge.BottomEdge,
    }

    def _to_qt_edges(self, edge_str: str) -> Qt.Edges:
        result = Qt.Edge(0)
        for part in edge_str.split("_"):
            if part in self._EDGE_MAP:
                result |= self._EDGE_MAP[part]
        return result

    # region 拖拽文件

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                ext = os.path.splitext(path)[1].lower()
                if ext in VIDEO_EXTENSIONS:
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self.controls_overlay.show_controls()
                self._hide_timer.start(CONTROLS_HIDE_DELAY_MS)
                self.play_file(path)
                return

    # endregion

    def closeEvent(self, event):
        self.mpv_widget.destroy()
        super().closeEvent(event)
