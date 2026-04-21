"""更新对话框 — 检查更新、显示 changelog、下载进度"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QProgressBar, QLineEdit,
)

from constants import (
    COLOR_PANEL, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_TEXT_DARK, COLOR_ACCENT, COLOR_WHITE, COLOR_PROGRESS_BG, COLOR_BG,
)
from updater import (
    UpdateConfig, UpdateChecker, UpdateDownloader, launch_installer_and_quit,
)
from version import get_version


class UpdateDialog(QDialog):
    """自动更新对话框"""

    def __init__(self, update_config: UpdateConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = update_config
        self._checker: UpdateChecker | None = None
        self._downloader: UpdateDownloader | None = None
        self._update_info: dict[str, object] | None = None

        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 340)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._frame = QWidget()
        self._frame.setObjectName("updateFrame")
        self._frame.setStyleSheet(f"""
            #updateFrame {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        outer.addWidget(self._frame)

        self._layout = QVBoxLayout(self._frame)
        self._layout.setContentsMargins(24, 20, 24, 24)
        self._layout.setSpacing(16)

        # 标题栏
        title_row = QHBoxLayout()
        self._title_label = QLabel("检查更新")
        self._title_label.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 15px; font-weight: bold; background: transparent;"
        )
        title_row.addWidget(self._title_label)
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
        close_btn.clicked.connect(self._on_close)
        title_row.addWidget(close_btn)
        self._layout.addLayout(title_row)

        # 内容区域（动态切换）
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)
        self._layout.addWidget(self._content, 1)

        # 底部按钮行
        self._btn_row = QHBoxLayout()
        self._btn_row.addStretch()
        self._layout.addLayout(self._btn_row)

        # 根据配置决定初始状态
        if not self._config.server_url:
            self._show_config_input()
        else:
            self._start_check()

    # region 配置服务器地址

    def _show_config_input(self) -> None:
        self._clear_content()
        self._title_label.setText("配置更新服务器")

        hint = QLabel("请输入更新服务器地址：")
        hint.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; background: transparent;")
        self._content_layout.addWidget(hint)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://example.com")
        self._url_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_BG};
                border: 1px solid {COLOR_PROGRESS_BG};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                color: {COLOR_TEXT};
            }}
            QLineEdit::placeholder {{ color: {COLOR_TEXT_DARK}; }}
            QLineEdit:focus {{ border-color: {COLOR_ACCENT}; }}
        """)
        self._content_layout.addWidget(self._url_input)
        self._content_layout.addStretch()

        self._add_buttons("取消", self.reject, "保存并检查", self._save_url_and_check)

    def _save_url_and_check(self) -> None:
        url = self._url_input.text().strip()
        if not url:
            return
        self._config.server_url = url
        self._start_check()

    # endregion

    # region 检查更新

    def _start_check(self) -> None:
        self._clear_content()
        self._title_label.setText("检查更新")

        status = QLabel("正在检查更新...")
        status.setObjectName("statusLabel")
        status.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; background: transparent;")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addStretch()
        self._content_layout.addWidget(status)
        self._content_layout.addStretch()

        self._clear_buttons()

        self._checker = UpdateChecker(self._config.server_url, self)
        self._checker.update_available.connect(self._on_update_available)
        self._checker.no_update.connect(self._on_no_update)
        self._checker.check_failed.connect(self._on_check_failed)
        self._checker.start()

    def _on_no_update(self) -> None:
        self._clear_content()
        self._title_label.setText("检查更新")

        label = QLabel(f"当前版本：v {get_version()}\n\n已是最新版本")
        label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; background: transparent;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addStretch()
        self._content_layout.addWidget(label)
        self._content_layout.addStretch()

        self._add_buttons("关闭", self.reject)

    def _on_check_failed(self, msg: str) -> None:
        self._clear_content()
        self._title_label.setText("检查更新")

        label = QLabel(msg)
        label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; background: transparent;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        self._content_layout.addStretch()
        self._content_layout.addWidget(label)
        self._content_layout.addStretch()

        self._add_buttons("关闭", self.reject, "重试", self._start_check)

    def _on_update_available(self, info: dict[str, object]) -> None:
        self._update_info = info
        self._clear_content()
        self._title_label.setText("发现新版本")

        version = str(info.get("version", ""))
        changelog = str(info.get("changelog", ""))
        file_size = int(info.get("file_size", 0))

        ver_label = QLabel(f"新版本：v {version}　　当前：v {get_version()}")
        ver_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 13px; background: transparent;")
        self._content_layout.addWidget(ver_label)

        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            size_label = QLabel(f"安装包大小：{size_mb:.1f} MB")
            size_label.setStyleSheet(
                f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;"
            )
            self._content_layout.addWidget(size_label)

        if changelog:
            log_label = QLabel(changelog)
            log_label.setStyleSheet(
                f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;"
            )
            log_label.setWordWrap(True)
            self._content_layout.addWidget(log_label)

        self._content_layout.addStretch()

        self._add_buttons("取消", self.reject, "下载更新", self._start_download)

    # endregion

    # region 下载

    def _start_download(self) -> None:
        if not self._update_info:
            return
        download_url = str(self._update_info.get("download_url", ""))
        if not download_url:
            return

        self._clear_content()
        self._title_label.setText("下载更新")

        self._progress_label = QLabel("正在下载...")
        self._progress_label.setStyleSheet(
            f"color: {COLOR_TEXT_DIM}; font-size: 13px; background: transparent;"
        )
        self._content_layout.addWidget(self._progress_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLOR_PROGRESS_BG};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {COLOR_ACCENT};
                border-radius: 3px;
            }}
        """)
        self._content_layout.addWidget(self._progress_bar)

        self._size_label = QLabel("")
        self._size_label.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 11px; background: transparent;"
        )
        self._content_layout.addWidget(self._size_label)

        self._content_layout.addStretch()

        self._add_buttons("取消下载", self._cancel_download)

        self._downloader = UpdateDownloader(download_url, self)
        self._downloader.progress.connect(self._on_download_progress)
        self._downloader.download_finished.connect(self._on_download_finished)
        self._downloader.download_failed.connect(self._on_download_failed)
        self._downloader.start()

    def _on_download_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            percent = int(downloaded * 100 / total)
            self._progress_bar.setValue(percent)
            dl_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self._progress_label.setText(f"正在下载... {percent}%")
            self._size_label.setText(f"{dl_mb:.1f} / {total_mb:.1f} MB")
        else:
            dl_mb = downloaded / (1024 * 1024)
            self._progress_label.setText(f"正在下载... {dl_mb:.1f} MB")

    def _on_download_finished(self, path: str) -> None:
        self._clear_content()
        self._title_label.setText("下载完成")

        label = QLabel("安装包已下载完成，点击「安装更新」将关闭当前应用并启动安装程序。")
        label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; background: transparent;")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addStretch()
        self._content_layout.addWidget(label)
        self._content_layout.addStretch()

        self._installer_path = path
        self._add_buttons("稍后安装", self.reject, "安装更新", self._install)

    def _on_download_failed(self, msg: str) -> None:
        self._clear_content()
        self._title_label.setText("下载失败")

        label = QLabel(msg)
        label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; background: transparent;")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addStretch()
        self._content_layout.addWidget(label)
        self._content_layout.addStretch()

        self._add_buttons("关闭", self.reject, "重试", self._start_download)

    def _cancel_download(self) -> None:
        if self._downloader:
            self._downloader.cancel()
        self.reject()

    def _install(self) -> None:
        launch_installer_and_quit(self._installer_path)

    # endregion

    # region 工具方法

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _clear_buttons(self) -> None:
        while self._btn_row.count():
            item = self._btn_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_buttons(
        self,
        secondary_text: str,
        secondary_action: object,
        primary_text: str | None = None,
        primary_action: object | None = None,
    ) -> None:
        self._clear_buttons()
        self._btn_row.addStretch()

        sec_btn = QPushButton(secondary_text)
        sec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sec_btn.setStyleSheet(f"""
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
        sec_btn.clicked.connect(secondary_action)
        self._btn_row.addWidget(sec_btn)

        if primary_text and primary_action:
            pri_btn = QPushButton(primary_text)
            pri_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pri_btn.setStyleSheet(f"""
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
            pri_btn.clicked.connect(primary_action)
            self._btn_row.addWidget(pri_btn)

    def _on_close(self) -> None:
        if self._downloader and self._downloader.isRunning():
            self._downloader.cancel()
        self.reject()

    # endregion
