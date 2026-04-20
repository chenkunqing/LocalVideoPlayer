"""快捷键设置面板 — 内嵌在主内容区域"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea,
)

from constants import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_DARK,
    COLOR_PROGRESS_BG, COLOR_WHITE, COLOR_BLACK, SHORTCUTS,
)
from shortcut_config import ShortcutConfig, SHORTCUT_LABELS


class _KeyBindingButton(QPushButton):
    """快捷键绑定按钮 — 点击后进入录制模式"""
    binding_changed = Signal(str, str)

    def __init__(self, action: str, current_seq: str, parent: QWidget | None = None):
        super().__init__(current_seq, parent)
        self._action = action
        self._recording = False
        self._current_seq = current_seq
        self.setFixedSize(140, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_normal_style()

    def set_sequence(self, seq: str) -> None:
        self._current_seq = seq
        if not self._recording:
            self.setText(seq)

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

        # 忽略单独的修饰键
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
                border: 1px solid {COLOR_ACCENT};
                border-radius: 6px;
                color: {COLOR_ACCENT};
                font-size: 12px;
                padding: 0 12px;
            }}
        """)
        self.setFocus()
        self.grabKeyboard()

    def _cancel_recording(self) -> None:
        self._recording = False
        self.releaseKeyboard()
        self.setText(self._current_seq)
        self._apply_normal_style()

    def _apply_normal_style(self) -> None:
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(63, 63, 70, 0.4);
                border: 1px solid {COLOR_PROGRESS_BG};
                border-radius: 6px;
                color: {COLOR_TEXT};
                font-size: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: rgba(63, 63, 70, 0.7);
                border-color: {COLOR_TEXT_DIM};
            }}
        """)


class _ShortcutRow(QWidget):
    """单行快捷键设置"""

    def __init__(
        self, action: str, label: str, seq: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        name_label = QLabel(label)
        name_label.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 13px;
            background: transparent;
        """)
        layout.addWidget(name_label)
        layout.addStretch()

        self.button = _KeyBindingButton(action, seq)
        layout.addWidget(self.button)


class ShortcutSettingsPanel(QWidget):
    """快捷键设置面板"""

    def __init__(self, config: ShortcutConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self._buttons: dict[str, _KeyBindingButton] = {}
        self.setStyleSheet(f"background: {COLOR_BG};")

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
        title = QLabel("快捷键设置")
        title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 32px;
            font-weight: 900;
            background: transparent;
        """)
        title_col.addWidget(title)

        count = len(SHORTCUTS)
        stats = QLabel(f"共 {count} 个快捷键")
        stats.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM};
            font-size: 13px;
            background: transparent;
        """)
        title_col.addWidget(stats)
        title_row.addLayout(title_col)
        title_row.addStretch()

        reset_btn = QPushButton("恢复默认")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(f"""
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
        reset_btn.clicked.connect(self._on_reset_all)
        title_row.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        header_layout.addLayout(title_row)
        header_layout.addStretch()
        layout.addWidget(header)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
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
            rows_layout.addWidget(row)
            self._buttons[action] = row.button

        rows_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        config.shortcuts_changed.connect(self._refresh_all)

    def _on_binding_changed(self, action: str, new_seq: str) -> None:
        conflict = self._config.set_binding(action, new_seq)
        if conflict is not None:
            self._config.swap_binding(action, new_seq)

    def _on_reset_all(self) -> None:
        self._config.reset_all()

    def _refresh_all(self) -> None:
        current = self._config.get_all()
        for action, btn in self._buttons.items():
            btn.set_sequence(current.get(action, ""))
