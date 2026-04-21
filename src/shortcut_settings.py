"""快捷键设置面板 — 内嵌在主内容区域"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea,
)

from constants import SHORTCUTS
from shortcut_config import ShortcutConfig, SHORTCUT_LABELS
from theme import theme


class _KeyBindingButton(QPushButton):
    """快捷键绑定按钮 — 点击后进入录制模式"""
    binding_changed = Signal(str, str)

    def __init__(self, action: str, current_seq: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._action = action
        self._recording = False
        self._current_seq = current_seq
        self.setFixedSize(140, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_display_text()
        self._apply_normal_style()
        theme.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self) -> None:
        if not self._recording:
            self._apply_normal_style()

    def set_sequence(self, seq: str) -> None:
        self._current_seq = seq
        if not self._recording:
            self._apply_display_text()
            self._apply_normal_style()

    def _apply_display_text(self) -> None:
        self.setText(self._current_seq if self._current_seq else "未设置")

    def mousePressEvent(self, event: object) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_recording()
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event: object) -> None:
        if not self._recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._cancel_recording()
            return

        modifier_keys = {
            Qt.Key.Key_Control, Qt.Key.Key_Shift,
            Qt.Key.Key_Alt, Qt.Key.Key_Meta,
        }
        if key in modifier_keys:
            return

        seq = QKeySequence(event.keyCombination()).toString()
        if not seq:
            return

        self._recording = False
        self.releaseKeyboard()
        self._apply_normal_style()
        self.binding_changed.emit(self._action, seq)

    def focusOutEvent(self, event: object) -> None:
        if self._recording:
            self._cancel_recording()
        super().focusOutEvent(event)

    def _start_recording(self) -> None:
        self._recording = True
        self.setText("按下新快捷键...")
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(139, 92, 246, 0.15);
                border: 1px solid {theme.color("accent")};
                border-radius: 6px;
                color: {theme.color("accent")};
                font-size: 12px;
                padding: 0 12px;
            }}
        """)
        self.setFocus()
        self.grabKeyboard()

    def _cancel_recording(self) -> None:
        self._recording = False
        self.releaseKeyboard()
        self._apply_display_text()
        self._apply_normal_style()

    def _apply_normal_style(self) -> None:
        text_color = theme.color("text") if self._current_seq else theme.color("text_dark")
        self.setStyleSheet(f"""
            QPushButton {{
                background: {theme.color("hover")};
                border: 1px solid {theme.color("progress_bg")};
                border-radius: 6px;
                color: {text_color};
                font-size: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {theme.color("hover_strong")};
                border-color: {theme.color("text_dim")};
            }}
        """)


class _ShortcutRow(QWidget):
    """单行快捷键设置"""
    clear_requested = Signal(str)

    def __init__(
        self, action: str, label: str, seq: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._action = action
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        self._name_label = QLabel(label)
        layout.addWidget(self._name_label)
        layout.addStretch()

        self.button = _KeyBindingButton(action, seq)
        layout.addWidget(self.button)

        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(32, 32)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.clicked.connect(lambda: self.clear_requested.emit(self._action))
        layout.addWidget(self.delete_button)

        self._apply_theme()
        theme.theme_changed.connect(self._apply_theme)

    def _apply_theme(self) -> None:
        self._name_label.setStyleSheet(f"""
            color: {theme.color("text")};
            font-size: 13px;
            background: transparent;
        """)
        self.delete_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                color: {theme.color("text_dim")};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(220, 38, 38, 0.15);
                border-color: {theme.color("red")};
                color: {theme.color("red")};
            }}
        """)


class ShortcutSettingsPanel(QWidget):
    """快捷键设置面板"""

    def __init__(self, config: ShortcutConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self._buttons: dict[str, _KeyBindingButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 头部
        header = QWidget()
        header.setFixedHeight(140)
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(32, 32, 32, 0)
        header_layout.setSpacing(0)

        title_row = QHBoxLayout()

        title_col = QVBoxLayout()
        self._title = QLabel("快捷键设置")
        title_col.addWidget(self._title)

        count = len(SHORTCUTS)
        self._stats = QLabel(f"共 {count} 个快捷键")
        title_col.addWidget(self._stats)
        title_row.addLayout(title_col)
        title_row.addStretch()

        self._reset_btn = QPushButton("恢复默认")
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.clicked.connect(self._on_reset_all)
        title_row.addWidget(self._reset_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        header_layout.addLayout(title_row)
        header_layout.addStretch()
        layout.addWidget(header)

        # 滚动区域
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        rows_layout = QVBoxLayout(scroll_content)
        rows_layout.setContentsMargins(16, 0, 16, 16)
        rows_layout.setSpacing(2)

        current = config.get_all()
        for action in SHORTCUTS:
            label = SHORTCUT_LABELS.get(action, action)
            seq = current.get(action, "")
            row = _ShortcutRow(action, label, seq)
            row.button.binding_changed.connect(self._on_binding_changed)
            row.clear_requested.connect(self._on_clear_binding)
            rows_layout.addWidget(row)
            self._buttons[action] = row.button

        rows_layout.addStretch()
        self._scroll.setWidget(scroll_content)
        layout.addWidget(self._scroll, 1)

        config.shortcuts_changed.connect(self._refresh_all)

        self._apply_theme()
        theme.theme_changed.connect(self._apply_theme)

    def _apply_theme(self) -> None:
        self.setStyleSheet(f"background: {theme.color('bg')};")
        self._title.setStyleSheet(f"""
            color: {theme.color("text")};
            font-size: 32px;
            font-weight: 900;
            background: transparent;
        """)
        self._stats.setStyleSheet(f"""
            color: {theme.color("text_dim")};
            font-size: 13px;
            background: transparent;
        """)
        self._reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.color("btn_face")};
                color: {theme.color("btn_face_text")};
                border: none;
                border-radius: 20px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {theme.color("btn_face_hover")};
            }}
        """)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {theme.color("scrollbar")};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

    def _on_binding_changed(self, action: str, new_seq: str) -> None:
        conflict = self._config.set_binding(action, new_seq)
        if conflict is not None:
            self._config.swap_binding(action, new_seq)

    def _on_clear_binding(self, action: str) -> None:
        self._config.clear_binding(action)

    def _on_reset_all(self) -> None:
        self._config.reset_all()

    def _refresh_all(self) -> None:
        current = self._config.get_all()
        for action, btn in self._buttons.items():
            btn.set_sequence(current.get(action, ""))
