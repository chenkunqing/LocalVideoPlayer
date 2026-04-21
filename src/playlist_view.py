"""播放列表视图 — 侧边栏 + 视频列表主页 + 播放列表网格"""

import os
import time

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import (
    QPainter, QColor, QPen, QPainterPath, QLinearGradient, QPixmap,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFileDialog, QSizePolicy, QGridLayout,
    QDialog, QLineEdit, QMenu,
)

from constants import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_BORDER_HALF,
    COLOR_ACCENT, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_DARK,
    COLOR_PROGRESS_BG, COLOR_WHITE, COLOR_BLACK,
    VIDEO_EXTENSIONS, PAGE_SIZE,
)
from playlist_sidebar import PlaylistSidebar
from shortcut_config import ShortcutConfig
from shortcut_settings import ShortcutSettingsPanel
from update_dialog import UpdateDialog
from updater import UpdateConfig
from video_library import VideoLibrary
from video_scanner import VideoItem
from utils import format_time


class _VideoRow(QWidget):
    """视频列表行 — 复刻 index.html 的行结构"""
    clicked = Signal(str)

    def __init__(self, index: int, item: VideoItem, thumbnail_path: str | None = None, parent=None):
        super().__init__(parent)
        self._index = index
        self._item = item
        self._hovered = False
        self._thumb_pix: QPixmap | None = None
        if thumbnail_path and os.path.isfile(thumbnail_path):
            self._thumb_pix = QPixmap(thumbnail_path)
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # hover 背景
        if self._hovered:
            p.setBrush(QColor(63, 63, 70, 80))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, w, h, 8, 8)

        # 列宽比例: 50 | 52(thumb) | flex | flex | 100
        col1_w = 50
        thumb_w = 52
        col4_w = 100
        remaining = w - col1_w - thumb_w - col4_w - 32
        col2_w = remaining * 0.6
        col3_w = remaining * 0.4
        x_offset = 16

        # 序号
        p.setPen(QColor(COLOR_ACCENT if self._hovered else COLOR_TEXT_DARK))
        font = p.font()
        font.setPixelSize(13)
        p.setFont(font)
        num_str = f"{self._index + 1:02d}"
        p.drawText(x_offset, 0, col1_w, h, Qt.AlignmentFlag.AlignVCenter, num_str)
        x_offset += col1_w

        # 缩略图
        thumb_y = (h - 40) // 2
        clip = QPainterPath()
        clip.addRoundedRect(x_offset, thumb_y, 40, 40, 4, 4)

        if self._thumb_pix and not self._thumb_pix.isNull():
            p.save()
            p.setClipPath(clip)
            scaled = self._thumb_pix.scaled(
                40, 40,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            dx = (scaled.width() - 40) // 2
            dy = (scaled.height() - 40) // 2
            p.drawPixmap(x_offset, thumb_y, scaled, dx, dy, 40, 40)
            p.restore()
        else:
            p.setBrush(QColor(COLOR_PROGRESS_BG))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x_offset, thumb_y, 40, 40, 4, 4)

        # 播放三角（hover 时显示在缩略图上）
        if self._hovered:
            p.setBrush(QColor(COLOR_WHITE))
            tri = QPainterPath()
            tcx, tcy = x_offset + 20, thumb_y + 20
            tri.moveTo(tcx - 5, tcy - 6)
            tri.lineTo(tcx + 6, tcy)
            tri.lineTo(tcx - 5, tcy + 6)
            tri.closeSubpath()
            p.drawPath(tri)

        x_offset += 52

        # 文件名 + 格式
        p.setPen(QColor(COLOR_TEXT))
        font.setPixelSize(13)
        font.setBold(True)
        p.setFont(font)
        name_text = p.fontMetrics().elidedText(
            self._item.name, Qt.TextElideMode.ElideRight, int(col2_w - 60)
        )
        p.drawText(x_offset, 0, int(col2_w - 60), h // 2,
                    Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, name_text)

        p.setPen(QColor(COLOR_TEXT_DARK))
        font.setPixelSize(10)
        font.setBold(False)
        p.setFont(font)
        size_mb = self._item.size_bytes / (1024 * 1024)
        meta = f"{size_mb:.1f} MB · {self._item.ext}"
        p.drawText(x_offset, h // 2, int(col2_w - 60), h // 2,
                    Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, meta)
        x_offset += int(col2_w)

        # 文件夹
        p.setPen(QColor(COLOR_TEXT_DIM))
        font.setPixelSize(12)
        p.setFont(font)
        folder_text = p.fontMetrics().elidedText(
            self._item.folder, Qt.TextElideMode.ElideRight, int(col3_w - 16)
        )
        p.drawText(x_offset, 0, int(col3_w), h, Qt.AlignmentFlag.AlignVCenter, folder_text)
        x_offset += int(col3_w)

        # 时长
        p.setPen(QColor(COLOR_TEXT_DIM))
        font.setPixelSize(12)
        p.setFont(font)
        dur = format_time(self._item.duration) if self._item.duration > 0 else "--:--"
        p.drawText(x_offset, 0, col4_w, h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, dur)

        p.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._item.path)


class _ListHeader(QWidget):
    """列表表头"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()

        col1_w = 50
        thumb_w = 52
        col4_w = 100
        remaining = w - col1_w - thumb_w - col4_w - 32
        col2_w = remaining * 0.6
        col3_w = remaining * 0.4
        x_offset = 16

        p.setPen(QColor(COLOR_TEXT_DARK))
        font = p.font()
        font.setPixelSize(10)
        font.setBold(True)
        p.setFont(font)

        p.drawText(x_offset, 0, col1_w, h, Qt.AlignmentFlag.AlignVCenter, "#")
        x_offset += col1_w
        p.drawText(x_offset, 0, int(thumb_w + col2_w), h, Qt.AlignmentFlag.AlignVCenter, "标题")
        x_offset += thumb_w + int(col2_w)
        p.drawText(x_offset, 0, int(col3_w), h, Qt.AlignmentFlag.AlignVCenter, "文件夹")
        x_offset += int(col3_w)
        p.drawText(x_offset, 0, col4_w, h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "时长")

        # 底部分割线
        p.setPen(QPen(QColor(COLOR_BORDER), 1))
        p.drawLine(16, h - 1, w - 16, h - 1)
        p.end()


class _PlaylistCard(QWidget):
    """播放列表卡片"""
    clicked = Signal(str)
    play_clicked = Signal(str)
    delete_clicked = Signal(str)

    CARD_HEIGHT = 180

    def __init__(self, playlist: dict[str, object], parent=None):
        super().__init__(parent)
        self._playlist = playlist
        self._hovered = False
        self.setMinimumHeight(self.CARD_HEIGHT)
        self.setMaximumHeight(self.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 卡片背景
        bg_alpha = 96 if self._hovered else 64
        p.setBrush(QColor(63, 63, 70, bg_alpha))
        p.setPen(QPen(QColor(COLOR_BORDER), 1))
        p.drawRoundedRect(1, 1, w - 2, h - 2, 16, 16)

        # 渐变图标方块
        icon_x, icon_y, icon_s = 20, 20, 56
        color_from = str(self._playlist.get("color_from", "#3b82f6"))
        color_to = str(self._playlist.get("color_to", "#6366f1"))
        grad = QLinearGradient(icon_x, icon_y, icon_x + icon_s, icon_y + icon_s)
        grad.setColorAt(0, QColor(color_from))
        grad.setColorAt(1, QColor(color_to))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(icon_x, icon_y, icon_s, icon_s, 12, 12)

        # 图标中央的播放三角
        p.setBrush(QColor(255, 255, 255, 200))
        tri = QPainterPath()
        cx, cy = icon_x + icon_s // 2, icon_y + icon_s // 2
        tri.moveTo(cx - 8, cy - 10)
        tri.lineTo(cx + 10, cy)
        tri.lineTo(cx - 8, cy + 10)
        tri.closeSubpath()
        p.drawPath(tri)

        # hover 时右上角播放按钮
        if self._hovered:
            btn_x, btn_y, btn_r = w - 56, 20, 36
            p.setBrush(QColor(COLOR_WHITE))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(btn_x, btn_y, btn_r, btn_r)
            p.setBrush(QColor(COLOR_BLACK))
            play = QPainterPath()
            pcx, pcy = btn_x + btn_r // 2, btn_y + btn_r // 2
            play.moveTo(pcx - 5, pcy - 7)
            play.lineTo(pcx + 7, pcy)
            play.lineTo(pcx - 5, pcy + 7)
            play.closeSubpath()
            p.drawPath(play)

        # 列表名称
        p.setPen(QColor(COLOR_TEXT))
        font = p.font()
        font.setPixelSize(16)
        font.setBold(True)
        p.setFont(font)
        name = str(self._playlist.get("name", ""))
        name_elided = p.fontMetrics().elidedText(name, Qt.TextElideMode.ElideRight, w - 40)
        p.drawText(20, 92, w - 40, 24, Qt.AlignmentFlag.AlignVCenter, name_elided)

        # 统计信息
        p.setPen(QColor(COLOR_TEXT_DIM))
        font.setPixelSize(12)
        font.setBold(False)
        p.setFont(font)
        videos = self._playlist.get("videos", [])
        count = len(videos) if isinstance(videos, list) else 0
        updated = self._playlist.get("updated_at", 0)
        if isinstance(updated, (int, float)) and updated > 0:
            t = time.localtime(updated)
            date_str = time.strftime("%Y-%m-%d", t)
        else:
            date_str = "—"
        stats = f"{count} 个视频 · 更新于 {date_str}"
        p.drawText(20, 118, w - 40, 20, Qt.AlignmentFlag.AlignVCenter, stats)

        p.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            btn_x, btn_y, btn_r = self.width() - 56, 20, 36
            pos = event.position()
            if (btn_x <= pos.x() <= btn_x + btn_r and
                    btn_y <= pos.y() <= btn_y + btn_r):
                self.play_clicked.emit(str(self._playlist.get("id", "")))
            else:
                self.clicked.emit(str(self._playlist.get("id", "")))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {COLOR_PANEL}; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 4px;
            }}
            QMenu::item {{ padding: 6px 24px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {COLOR_ACCENT}; }}
        """)
        delete_action = menu.addAction("删除播放列表")
        action = menu.exec(event.globalPos())
        if action == delete_action:
            self.delete_clicked.emit(str(self._playlist.get("id", "")))


class _CreatePlaylistDialog(QDialog):
    """创建播放列表对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 200)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QWidget()
        frame.setObjectName("dialogFrame")
        frame.setStyleSheet(f"""
            #dialogFrame {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        outer.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # 自定义标题栏
        title_row = QHBoxLayout()
        title_label = QLabel("创建新列表")
        title_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 15px; font-weight: bold; background: transparent;")
        title_row.addWidget(title_label)
        title_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLOR_TEXT_DIM};
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: rgba(63, 63, 70, 0.8); color: {COLOR_TEXT}; }}
        """)
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(close_btn)
        layout.addLayout(title_row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入播放列表名称...")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_BG};
                border: 1px solid {COLOR_PROGRESS_BG};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                color: {COLOR_TEXT};
            }}
            QLineEdit::placeholder {{
                color: {COLOR_TEXT_DARK};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT};
            }}
        """)
        layout.addWidget(self.name_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLOR_TEXT_DIM};
                border: 1px solid {COLOR_PROGRESS_BG};
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: rgba(63, 63, 70, 0.5); }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("创建")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT};
                color: {COLOR_WHITE};
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #7c3aed; }}
        """)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

    def get_name(self) -> str:
        return self.name_input.text().strip()


class PlaylistView(QWidget):
    """播放列表主视图"""
    play_video_requested = Signal(str)

    def __init__(
        self,
        library: VideoLibrary,
        shortcut_config: ShortcutConfig | None = None,
        update_config: UpdateConfig | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._library = library
        self._shortcut_config = shortcut_config
        self._update_config = update_config
        self._filter_text = ""
        self._nav_mode = "all"
        self._current_playlist_id: str | None = None
        self._displayed: list[VideoItem] = []

        self.setStyleSheet(f"background: {COLOR_BG};")
        self.setAcceptDrops(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 侧边栏
        self._sidebar = PlaylistSidebar()
        self._sidebar.nav_changed.connect(self._on_nav_changed)
        self._sidebar.search_changed.connect(self._on_search_changed)
        self._sidebar.recent_item_clicked.connect(self.play_video_requested.emit)
        self._sidebar.check_update_clicked.connect(self._on_check_update)
        layout.addWidget(self._sidebar)

        # 主内容区
        main_area = QWidget()
        main_area.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 头部
        header = QWidget()
        header.setFixedHeight(140)
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(32, 32, 32, 0)
        header_layout.setSpacing(0)

        # 标题行
        title_row = QHBoxLayout()

        # 返回按钮（播放列表详情时显示）
        self._back_btn = QPushButton("←")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setFixedSize(36, 36)
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(63, 63, 70, 0.5);
                color: {COLOR_TEXT};
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: rgba(63, 63, 70, 0.8); }}
        """)
        self._back_btn.clicked.connect(self.go_back_to_playlist_grid)
        self._back_btn.hide()
        title_row.addWidget(self._back_btn, alignment=Qt.AlignmentFlag.AlignTop)

        title_col = QVBoxLayout()
        self._title = QLabel("本地视频库")
        self._title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 32px;
            font-weight: 900;
            background: transparent;
        """)
        title_col.addWidget(self._title)
        self._stats = QLabel("共 0 个视频")
        self._stats.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM};
            font-size: 13px;
            background: transparent;
        """)
        title_col.addWidget(self._stats)
        title_row.addLayout(title_col)
        title_row.addStretch()

        # 添加文件夹按钮
        self._add_btn = QPushButton("添加文件夹")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_WHITE};
                color: {COLOR_BLACK};
                border: none;
                border-radius: 20px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #e4e4e7;
            }}
        """)
        self._add_btn.clicked.connect(self._on_add_folder)
        title_row.addWidget(self._add_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        header_layout.addLayout(title_row)
        header_layout.addStretch()
        self._header = header
        main_layout.addWidget(header)

        # 列表表头
        self._list_header = _ListHeader()
        main_layout.addWidget(self._list_header)

        # 滚动区域
        self._video_scroll = QScrollArea()
        self._video_scroll.setWidgetResizable(True)
        self._video_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._video_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #3f3f46;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self._list_container = QWidget()
        self._list_container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()

        self._video_scroll.setWidget(self._list_container)
        main_layout.addWidget(self._video_scroll, 1)

        # 空状态提示
        self._empty_label = QLabel("点击「添加文件夹」或拖拽视频文件到此处")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DARK};
            font-size: 14px;
            background: transparent;
            padding: 80px;
        """)
        self._empty_label.hide()
        main_layout.addWidget(self._empty_label)

        # 播放列表卡片网格区域
        self._playlist_grid_scroll = QScrollArea()
        self._playlist_grid_scroll.setWidgetResizable(True)
        self._playlist_grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._playlist_grid_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 6px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #3f3f46; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        self._playlist_grid_container = QWidget()
        self._playlist_grid_container.setStyleSheet("background: transparent;")
        self._playlist_grid_layout = QGridLayout(self._playlist_grid_container)
        self._playlist_grid_layout.setContentsMargins(0, 0, 16, 16)
        self._playlist_grid_layout.setSpacing(16)
        self._playlist_grid_scroll.setWidget(self._playlist_grid_container)
        self._playlist_grid_scroll.hide()
        main_layout.addWidget(self._playlist_grid_scroll, 1)

        # 播放列表空状态
        self._playlist_empty_label = QLabel("还没有播放列表，点击「创建新列表」开始")
        self._playlist_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._playlist_empty_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DARK};
            font-size: 14px;
            background: transparent;
            padding: 80px;
        """)
        self._playlist_empty_label.hide()
        main_layout.addWidget(self._playlist_empty_label)

        # 快捷键设置面板
        if shortcut_config is not None:
            self._shortcut_panel = ShortcutSettingsPanel(shortcut_config)
        else:
            self._shortcut_panel = QWidget()
        self._shortcut_panel.hide()
        main_layout.addWidget(self._shortcut_panel, 1)

        layout.addWidget(main_area, 1)

        # 信号连接
        self._library.library_changed.connect(self._refresh)
        self._library.recent_changed.connect(self._refresh_recent)
        self._library.playlists_changed.connect(self._refresh)

        # 初始扫描
        if self._library.folders:
            self._library.rescan()
        self._refresh_recent()

    def _on_nav_changed(self, key: str):
        self._nav_mode = key
        self._current_playlist_id = None
        self._refresh()

    def _on_search_changed(self, text: str):
        self._filter_text = text.strip().lower()
        self._refresh()

    def _on_check_update(self) -> None:
        if self._update_config is None:
            return
        dlg = UpdateDialog(self._update_config, self)
        dlg.exec()

    def _on_add_folder(self):
        if self._nav_mode == "playlists" and self._current_playlist_id is None:
            self._create_playlist()
            return
        if self._nav_mode == "playlists" and self._current_playlist_id is not None:
            self._add_video_to_playlist()
            return
        path = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if path:
            self._library.add_folder(path)

    def _create_playlist(self):
        dialog = _CreatePlaylistDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            if name:
                self._library.create_playlist(name)

    def _add_video_to_playlist(self):
        if not self._current_playlist_id:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (" + " ".join(f"*{e}" for e in sorted(VIDEO_EXTENSIONS)) + ")"
        )
        for p in paths:
            self._library.add_to_playlist(self._current_playlist_id, p)

    def go_back_to_playlist_grid(self):
        """从播放列表详情返回列表网格"""
        if self._nav_mode == "playlists" and self._current_playlist_id is not None:
            self._current_playlist_id = None
            self._refresh()

    def _refresh(self):
        is_shortcuts = self._nav_mode == "shortcuts"

        # 快捷键设置面板
        self._shortcut_panel.setVisible(is_shortcuts)
        if is_shortcuts:
            self._header.hide()
            self._list_header.hide()
            self._video_scroll.hide()
            self._empty_label.hide()
            self._playlist_grid_scroll.hide()
            self._playlist_empty_label.hide()
            return

        self._header.show()

        is_playlist_grid = self._nav_mode == "playlists" and self._current_playlist_id is None
        is_playlist_detail = self._nav_mode == "playlists" and self._current_playlist_id is not None

        # 返回按钮
        self._back_btn.setVisible(is_playlist_detail)

        # 切换视图可见性
        self._playlist_grid_scroll.setVisible(is_playlist_grid)
        self._video_scroll.setVisible(not is_playlist_grid)
        self._playlist_empty_label.hide()

        if is_playlist_grid:
            self._refresh_playlist_grid()
            return

        # 视频列表模式（全部、最近、文件夹、播放列表详情）
        self._playlist_grid_scroll.hide()
        self._playlist_empty_label.hide()

        if is_playlist_detail:
            videos = self._library.get_playlist_videos(self._current_playlist_id)
            pl = self._library.get_playlist(self._current_playlist_id)
            pl_name = str(pl.get("name", "")) if pl else ""
            self._title.setText(pl_name)
            self._stats.setText(f"共 {len(videos)} 个视频")
            self._add_btn.setText("添加视频")
        else:
            videos = self._library.videos
            if self._nav_mode == "recent":
                videos = self._library.get_recent_videos()

            self._title.setText("本地视频库")
            count = self._library.video_count()
            total_gb = self._library.total_size_bytes() / (1024 ** 3)
            self._stats.setText(f"共 {count} 个视频 · {total_gb:.1f} GB")
            self._add_btn.setText("添加文件夹")

        if self._filter_text:
            videos = [v for v in videos if self._filter_text in v.name.lower()]

        self._displayed = videos

        # 清除旧行
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # 添加新行
        for i, v in enumerate(videos[:PAGE_SIZE]):
            thumb = self._library.get_thumbnail(v.path)
            row = _VideoRow(i, v, thumbnail_path=thumb)
            row.clicked.connect(self.play_video_requested.emit)
            self._list_layout.insertWidget(i, row)

        has_items = len(videos) > 0
        self._list_header.setVisible(has_items)
        self._empty_label.setVisible(not has_items and not is_playlist_detail)

    def _refresh_playlist_grid(self):
        """刷新播放列表卡片网格"""
        self._list_header.hide()
        self._empty_label.hide()
        self._video_scroll.hide()

        # 清除旧卡片
        while self._playlist_grid_layout.count():
            item = self._playlist_grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        playlists = self._library.playlists

        # 更新头部
        self._title.setText("我的播放列表")
        self._stats.setText(f"共 {len(playlists)} 个列表")
        self._add_btn.setText("创建新列表")

        if not playlists:
            self._playlist_grid_scroll.hide()
            self._playlist_empty_label.show()
            return

        self._playlist_grid_scroll.show()
        self._playlist_empty_label.hide()

        cols = 3
        for i, pl in enumerate(playlists):
            card = _PlaylistCard(pl)
            card.clicked.connect(self._on_playlist_card_clicked)
            card.play_clicked.connect(self._on_playlist_play_clicked)
            card.delete_clicked.connect(self._on_playlist_delete)
            self._playlist_grid_layout.addWidget(card, i // cols, i % cols)

        # 填充空列，保持卡片不被拉伸到全宽
        for col in range(cols):
            self._playlist_grid_layout.setColumnStretch(col, 1)

    def _on_playlist_card_clicked(self, playlist_id: str):
        self._current_playlist_id = playlist_id
        self._refresh()

    def _on_playlist_play_clicked(self, playlist_id: str):
        videos = self._library.get_playlist_videos(playlist_id)
        if videos:
            self.play_video_requested.emit(videos[0].path)

    def _on_playlist_delete(self, playlist_id: str):
        self._library.delete_playlist(playlist_id)

    def _refresh_recent(self):
        recent = self._library.recent
        items = [
            (
                os.path.splitext(os.path.basename(r.get("path", "")))[0],
                str(r.get("path", "")),
                self._library.get_thumbnail(str(r.get("path", ""))),
            )
            for r in recent
        ]
        self._sidebar.update_recent(items)

    # region 拖拽支持

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ext = os.path.splitext(url.toLocalFile())[1].lower()
                if ext in VIDEO_EXTENSIONS:
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                self.play_video_requested.emit(path)
                return

    # endregion
