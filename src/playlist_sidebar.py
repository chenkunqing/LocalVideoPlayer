"""播放列表侧边栏 — 搜索、导航、最近观看"""

from PySide6.QtCore import Qt, Signal, QTimer
import os

from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QSizePolicy,
)

from constants import (
    COLOR_PANEL, COLOR_BORDER_HALF, COLOR_BG, COLOR_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_DARK, COLOR_PROGRESS_BG,
    SIDEBAR_WIDTH,
)
from version import get_version


class _NavItem(QWidget):
    """侧边栏导航项"""
    clicked = Signal(str)

    def __init__(self, key: str, label: str, icon_type: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._label = label
        self._icon_type = icon_type
        self._active = False
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self._active:
            p.setBrush(QColor(COLOR_ACCENT))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, w, h, 6, 6)
            text_color = QColor(COLOR_TEXT)
        else:
            text_color = QColor(COLOR_TEXT_DIM)

        # 图标
        p.setPen(QPen(text_color, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        self._draw_icon(p, 24, h // 2)

        # 文字
        p.setPen(text_color)
        font = p.font()
        font.setPixelSize(13)
        p.setFont(font)
        p.drawText(42, 0, w - 48, h, Qt.AlignmentFlag.AlignVCenter, self._label)
        p.end()

    def _draw_icon(self, p: QPainter, cx: int, cy: int):
        s = 7
        if self._icon_type == "video":
            p.drawRect(cx - s, cy - s + 2, s * 2, s * 2 - 4)
            path = QPainterPath()
            path.moveTo(cx - 3, cy - 3)
            path.lineTo(cx + 4, cy)
            path.lineTo(cx - 3, cy + 3)
            path.closeSubpath()
            p.setBrush(p.pen().color())
            p.drawPath(path)
            p.setBrush(Qt.BrushStyle.NoBrush)
        elif self._icon_type == "clock":
            p.drawEllipse(cx - s, cy - s, s * 2, s * 2)
            p.drawLine(cx, cy - 4, cx, cy)
            p.drawLine(cx, cy, cx + 3, cy + 2)
        elif self._icon_type == "list_heart":
            # 列表图标 + 心形装饰
            for dy in (-3, 0, 3):
                p.drawLine(cx - s, cy + dy, cx + s, cy + dy)
            p.setBrush(p.pen().color())
            path = QPainterPath()
            path.moveTo(cx + s - 2, cy - s + 1)
            path.cubicTo(cx + s + 1, cy - s - 1, cx + s + 4, cy - s + 2, cx + s - 2, cy - s + 5)
            path.cubicTo(cx + s - 8, cy - s + 2, cx + s - 5, cy - s - 1, cx + s - 2, cy - s + 1)
            p.drawPath(path)
            p.setBrush(Qt.BrushStyle.NoBrush)
        elif self._icon_type == "folder":
            p.drawRoundedRect(cx - s, cy - s + 3, s * 2, s * 2 - 4, 2, 2)
            p.drawLine(cx - s, cy - s + 6, cx - s, cy - s + 3)
            p.drawLine(cx - s, cy - s + 3, cx - 2, cy - s + 3)
            p.drawLine(cx - 2, cy - s + 3, cx, cy - s + 1)
            p.drawLine(cx, cy - s + 1, cx + s, cy - s + 1)
            p.drawLine(cx + s, cy - s + 1, cx + s, cy - s + 3)
        elif self._icon_type == "keyboard":
            p.drawRoundedRect(cx - s, cy - s + 2, s * 2, s * 2 - 4, 2, 2)
            p.drawLine(cx - 4, cy - 2, cx + 4, cy - 2)
            p.drawLine(cx - 4, cy + 1, cx + 4, cy + 1)
            p.drawLine(cx - 3, cy + 4, cx + 3, cy + 4)
        elif self._icon_type == "update":
            # 下载箭头 + 底线
            p.drawLine(cx, cy - s, cx, cy + 2)
            path = QPainterPath()
            path.moveTo(cx - 4, cy - 1)
            path.lineTo(cx, cy + 4)
            path.lineTo(cx + 4, cy - 1)
            p.drawPath(path)
            p.drawLine(cx - s, cy + s - 1, cx + s, cy + s - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._key)


class _RecentItem(QWidget):
    """最近观看条目"""
    clicked = Signal(str)

    def __init__(self, name: str, path: str, thumbnail_path: str | None = None, parent=None):
        super().__init__(parent)
        self._name = name
        self._path = path
        self._hovered = False
        self._thumb_pix: QPixmap | None = None
        if thumbnail_path and os.path.isfile(thumbnail_path):
            self._thumb_pix = QPixmap(thumbnail_path)
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 缩略图
        clip = QPainterPath()
        clip.addRoundedRect(4, 4, 28, 28, 4, 4)
        if self._thumb_pix and not self._thumb_pix.isNull():
            p.save()
            p.setClipPath(clip)
            scaled = self._thumb_pix.scaled(
                28, 28,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            dx = (scaled.width() - 28) // 2
            dy = (scaled.height() - 28) // 2
            p.drawPixmap(4, 4, scaled, dx, dy, 28, 28)
            p.restore()
        else:
            p.setBrush(QColor(COLOR_PROGRESS_BG))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(4, 4, 28, 28, 4, 4)

        # 文件名
        p.setPen(QColor(COLOR_TEXT_DIM if not self._hovered else COLOR_TEXT))
        font = p.font()
        font.setPixelSize(12)
        p.setFont(font)
        text_rect = p.fontMetrics().elidedText(self._name, Qt.TextElideMode.ElideRight, w - 44)
        p.drawText(40, 0, w - 44, h, Qt.AlignmentFlag.AlignVCenter, text_rect)
        p.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._path)


class PlaylistSidebar(QWidget):
    """左侧导航栏"""
    nav_changed = Signal(str)
    search_changed = Signal(str)
    recent_item_clicked = Signal(str)
    check_update_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setStyleSheet(f"background: {COLOR_PANEL}; border-right: 1px solid {COLOR_BORDER_HALF};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 搜索区域
        search_container = QWidget()
        search_container.setFixedHeight(72)
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(24, 24, 24, 0)
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索库...")
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(9, 9, 11, 0.5);
                border: 1px solid {COLOR_PROGRESS_BG};
                border-radius: 8px;
                padding: 8px 16px 8px 36px;
                font-size: 12px;
                color: {COLOR_TEXT};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT};
            }}
        """)
        search_layout.addWidget(self._search)
        layout.addWidget(search_container)

        # 搜索防抖
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(lambda: self.search_changed.emit(self._search.text()))
        self._search.textChanged.connect(lambda: self._search_timer.start())

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(scroll_content)
        nav_layout.setContentsMargins(12, 0, 12, 12)
        nav_layout.setSpacing(0)

        # 视频库分组
        section_label = QLabel("视频库")
        section_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DARK};
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            padding: 12px 12px 8px 12px;
            background: transparent;
        """)
        nav_layout.addWidget(section_label)

        self._nav_items: dict[str, _NavItem] = {}
        for key, label, icon in [
            ("all", "全部视频", "video"),
            ("playlists", "播放列表", "list_heart"),
            ("recent", "最近播放", "clock"),
            ("folders", "文件夹", "folder"),
        ]:
            item = _NavItem(key, label, icon)
            item.clicked.connect(self._on_nav_clicked)
            nav_layout.addWidget(item)
            self._nav_items[key] = item

        self._nav_items["all"].set_active(True)
        self._current_nav = "all"

        # 最近观看
        self._recent_label = QLabel("最近观看")
        self._recent_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DARK};
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            padding: 24px 12px 8px 12px;
            background: transparent;
        """)
        nav_layout.addWidget(self._recent_label)

        self._recent_container = QWidget()
        self._recent_container.setStyleSheet("background: transparent;")
        self._recent_layout = QVBoxLayout(self._recent_container)
        self._recent_layout.setContentsMargins(0, 0, 0, 0)
        self._recent_layout.setSpacing(2)
        nav_layout.addWidget(self._recent_container)

        # 设置分组
        settings_label = QLabel("设置")
        settings_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DARK};
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            padding: 24px 12px 8px 12px;
            background: transparent;
        """)
        nav_layout.addWidget(settings_label)

        shortcuts_item = _NavItem("shortcuts", "快捷键", "keyboard")
        shortcuts_item.clicked.connect(self._on_nav_clicked)
        nav_layout.addWidget(shortcuts_item)
        self._nav_items["shortcuts"] = shortcuts_item

        update_item = _NavItem("update", "检查更新", "update")
        update_item.clicked.connect(lambda _: self.check_update_clicked.emit())
        nav_layout.addWidget(update_item)

        nav_layout.addStretch()

        # 版本号
        version_label = QLabel(f"v {get_version()}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DARK};
            font-size: 10px;
            padding: 12px;
            background: transparent;
        """)
        nav_layout.addWidget(version_label)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

    def _on_nav_clicked(self, key: str):
        if key == self._current_nav:
            return
        self._nav_items[self._current_nav].set_active(False)
        self._nav_items[key].set_active(True)
        self._current_nav = key
        self.nav_changed.emit(key)

    def update_recent(self, items: list[tuple[str, str, str | None]]):
        """更新最近观看列表，items = [(name, path, thumbnail_path), ...]"""
        while self._recent_layout.count():
            w = self._recent_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        for name, path, thumb in items[:5]:
            ri = _RecentItem(name, path, thumbnail_path=thumb)
            ri.clicked.connect(self.recent_item_clicked.emit)
            self._recent_layout.addWidget(ri)
        self._recent_label.setVisible(len(items) > 0)
