"""自定义标题栏 — Win11 风格"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from constants import TITLE_BAR_HEIGHT
from theme import theme


class _WinButton(QPushButton):
    """标题栏窗口按钮"""

    def __init__(self, btn_type, parent=None):
        super().__init__(parent)
        self._type = btn_type
        self.setFixedSize(46, TITLE_BAR_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_theme()
        theme.theme_changed.connect(self._apply_theme)

    def _apply_theme(self) -> None:
        if self._type == "close":
            self.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; }}
                QPushButton:hover {{ background: {theme.color("red")}; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; }}
                QPushButton:hover {{ background: {theme.color("hover")}; }}
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(theme.color("text")), 1))
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
        self._apply_theme()
        self.update()


class TitleBar(QWidget):
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()
    home_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(TITLE_BAR_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(0)

        # 图标
        self._icon_label = QLabel("▶")
        layout.addWidget(self._icon_label)

        layout.addSpacing(8)

        # 标题
        self._title = QLabel("KK Player")
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

        self._apply_theme()
        theme.theme_changed.connect(self._apply_theme)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"background: {theme.color('panel')}; border-bottom: 1px solid {theme.color('border_half')};"
        )
        self._icon_label.setStyleSheet(
            f"color: {theme.color('accent')}; font-size: 14px; background: transparent;"
        )
        self._title.setStyleSheet(f"""
            color: {theme.color("text_dim")};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: -0.5px;
            background: transparent;
        """)

    def set_mode(self, mode: str):
        """切换标题栏模式: 'library' 隐藏返回按钮, 'player' 显示返回按钮"""
        self._home_btn.setVisible(mode == "player")

    def set_maximized_icon(self, is_maximized):
        self._max_btn.set_type("restore" if is_maximized else "maximize")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win.isMaximized():
                win.showNormal()
            handle = win.windowHandle()
            if handle:
                handle.startSystemMove()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_requested.emit()
