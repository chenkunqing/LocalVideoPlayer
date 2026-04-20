"""自定义标题栏 — Win11 风格"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from constants import (
    COLOR_PANEL, COLOR_BORDER_HALF, COLOR_ACCENT, COLOR_TEXT,
    COLOR_TEXT_DIM, COLOR_RED, TITLE_BAR_HEIGHT,
)


class _WinButton(QPushButton):
    """标题栏窗口按钮"""

    def __init__(self, btn_type, parent=None):
        super().__init__(parent)
        self._type = btn_type
        self.setFixedSize(46, TITLE_BAR_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if btn_type == "close":
            self.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; }}
                QPushButton:hover {{ background: {COLOR_RED}; }}
            """)
        else:
            self.setStyleSheet("""
                QPushButton { background: transparent; border: none; }
                QPushButton:hover { background: #27272a; }
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(COLOR_TEXT), 1))
        cx, cy = self.width() // 2, self.height() // 2

        if self._type == "minimize":
            p.drawLine(cx - 5, cy, cx + 5, cy)
        elif self._type == "maximize":
            p.drawRect(cx - 5, cy - 4, 10, 8)
        elif self._type == "restore":
            p.drawRect(cx - 3, cy - 4, 8, 7)
            p.drawLine(cx - 5, cy - 2, cx - 5, cy + 5)
            p.drawLine(cx - 5, cy + 5, cx + 3, cy + 5)
            p.drawLine(cx + 3, cy + 5, cx + 3, cy - 2)
            p.drawLine(cx - 5, cy - 2, cx - 2, cy - 2)
        elif self._type == "close":
            p.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            p.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)
        elif self._type == "home":
            path = QPainterPath()
            path.moveTo(cx, cy - 6)
            path.lineTo(cx - 7, cy)
            path.lineTo(cx - 5, cy)
            path.lineTo(cx - 5, cy + 5)
            path.lineTo(cx + 5, cy + 5)
            path.lineTo(cx + 5, cy)
            path.lineTo(cx + 7, cy)
            path.closeSubpath()
            p.drawPath(path)

        p.end()

    def set_type(self, btn_type):
        self._type = btn_type
        self.update()


class TitleBar(QWidget):
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()
    home_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self.setStyleSheet(f"background: {COLOR_PANEL}; border-bottom: 1px solid {COLOR_BORDER_HALF};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(0)

        # 图标
        icon_label = QLabel("▶")
        icon_label.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 14px; background: transparent;")
        layout.addWidget(icon_label)

        layout.addSpacing(8)

        # 标题
        self._title = QLabel("KK Player")
        self._title.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: -0.5px;
            background: transparent;
        """)
        layout.addWidget(self._title)

        layout.addStretch()

        # 返回主页按钮
        self._home_btn = _WinButton("home")
        self._home_btn.clicked.connect(self.home_requested.emit)
        self._home_btn.hide()
        layout.addWidget(self._home_btn)

        # 窗口按钮
        self._min_btn = _WinButton("minimize")
        self._max_btn = _WinButton("maximize")
        self._close_btn = _WinButton("close")

        self._min_btn.clicked.connect(self.minimize_requested.emit)
        self._max_btn.clicked.connect(self.maximize_requested.emit)
        self._close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(self._min_btn)
        layout.addWidget(self._max_btn)
        layout.addWidget(self._close_btn)

        self._dragging = False
        self._drag_start = None

    def set_mode(self, mode: str):
        """切换标题栏模式: 'library' 隐藏返回按钮, 'player' 显示返回按钮"""
        self._home_btn.setVisible(mode == "player")

    def set_maximized_icon(self, is_maximized):
        self._max_btn.set_type("restore" if is_maximized else "maximize")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start = event.globalPosition().toPoint() - self.window().pos()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            if self.window().isMaximized():
                self.window().showNormal()
                self._drag_start = event.globalPosition().toPoint() - self.window().pos()
            else:
                self.window().move(new_pos)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_start = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_requested.emit()
