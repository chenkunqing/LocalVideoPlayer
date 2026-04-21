"""更新对话框 — 检查更新、显示 changelog、下载进度"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QProgressBar, QLineEdit,
)

from theme import theme
from updater import (
    UpdateConfig, UpdateChecker, UpdateDownloader, UpdatePatcher,
    replace_and_restart,
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
        self._new_exe_path: str = ""
        self._is_patching: bool = False

        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 340)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._frame = QWidget()
        self._frame.setObjectName("updateFrame")
        outer.addWidget(self._frame)

        self._layout = QVBoxLayout(self._frame)
        self._layout.setContentsMargins(24, 20, 24, 24)
        self._layout.setSpacing(16)

        # 标题栏
        title_row = QHBoxLayout()
        self._title_label = QLabel("检查更新")
        title_row.addWidget(self._title_label)
        title_row.addStretch()

        self._close_btn = QPushButton("✕")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.clicked.connect(self._on_close)
        title_row.addWidget(self._close_btn)
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

        self._apply_theme()

        # 根据配置决定初始状态
        if not self._config.server_url:
            self._show_config_input()
        else:
            self._start_check()

    def _apply_theme(self) -> None:
        self._frame.setStyleSheet(f"""
            #updateFrame {{
                background: {theme.color("panel")};
                border: 1px solid {theme.color("border")};
                border-radius: 12px;
            }}
        """)
        self._title_label.setStyleSheet(
            f"color: {theme.color('text')}; font-size: 15px; font-weight: bold; background: transparent;"
        )
        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.color("text_dim")};
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {theme.color("hover_strong")}; color: {theme.color("text")}; }}
        """)

    # region 配置服务器地址

    def _show_config_input(self) -> None:
        self._clear_content()
        self._title_label.setText("配置更新服务器")

        hint = QLabel("请输入更新服务器地址：")
        hint.setStyleSheet(f"color: {theme.color('text_dim')}; font-size: 13px; background: transparent;")
        self._content_layout.addWidget(hint)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://example.com")
        self._url_input.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.color("bg")};
                border: 1px solid {theme.color("progress_bg")};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                color: {theme.color("text")};
            }}
            QLineEdit::placeholder {{ color: {theme.color("text_dark")}; }}
            QLineEdit:focus {{ border-color: {theme.color("accent")}; }}
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
        status.setStyleSheet(f"color: {theme.color('text_dim')}; font-size: 13px; background: transparent;")
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
        label.setStyleSheet(f"color: {theme.color('text_dim')}; font-size: 13px; background: transparent;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addStretch()
        self._content_layout.addWidget(label)
        self._content_layout.addStretch()

        self._add_buttons("关闭", self.reject)

    def _on_check_failed(self, msg: str) -> None:
        self._clear_content()
        self._title_label.setText("检查更新")

        label = QLabel(msg)
        label.setStyleSheet(f"color: {theme.color('text_dim')}; font-size: 13px; background: transparent;")
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
        ver_label.setStyleSheet(f"color: {theme.color('text')}; font-size: 13px; background: transparent;")
        self._content_layout.addWidget(ver_label)

        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            size_label = QLabel(f"文件大小：{size_mb:.1f} MB")
            size_label.setStyleSheet(
                f"color: {theme.color('text_dim')}; font-size: 12px; background: transparent;"
            )
            self._content_layout.addWidget(size_label)

        if changelog:
            log_label = QLabel(changelog)
            log_label.setStyleSheet(
                f"color: {theme.color('text_dim')}; font-size: 12px; background: transparent;"
            )
            log_label.setWordWrap(True)
            self._content_layout.addWidget(log_label)

        self._content_layout.addStretch()

        self._add_buttons("取消", self.reject, "下载更新", self._start_download)

    # endregion

    # region 下载

    def _can_patch(self) -> bool:
        """判断是否可以走增量更新"""
        if not self._update_info:
            return False
        patch_url = str(self._update_info.get("patch_url", ""))
        prev_version = str(self._update_info.get("prev_version", ""))
        return bool(patch_url) and prev_version == get_version()

    def _start_download(self) -> None:
        if not self._update_info:
            return

        self._is_patching = self._can_patch()
        self._show_download_ui()

        if self._is_patching:
            patch_url = str(self._update_info["patch_url"])
            self._downloader = UpdatePatcher(patch_url, self)
            self._downloader.download_failed.connect(self._on_patch_failed)
        else:
            download_url = str(self._update_info.get("download_url", ""))
            if not download_url:
                return
            self._downloader = UpdateDownloader(download_url, self)
            self._downloader.download_failed.connect(self._on_download_failed)

        self._downloader.progress.connect(self._on_download_progress)
        self._downloader.download_finished.connect(self._on_download_finished)
        self._downloader.start()

    def _show_download_ui(self) -> None:
        self._clear_content()
        label = "增量更新中..." if self._is_patching else "下载更新"
        self._title_label.setText(label)

        self._progress_label = QLabel("正在下载...")
        self._progress_label.setStyleSheet(
            f"color: {theme.color('text_dim')}; font-size: 13px; background: transparent;"
        )
        self._content_layout.addWidget(self._progress_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {theme.color("progress_bg")};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {theme.color("accent")};
                border-radius: 3px;
            }}
        """)
        self._content_layout.addWidget(self._progress_bar)

        self._size_label = QLabel("")
        self._size_label.setStyleSheet(
            f"color: {theme.color('text_dark')}; font-size: 11px; background: transparent;"
        )
        self._content_layout.addWidget(self._size_label)

        self._content_layout.addStretch()

        self._add_buttons("取消下载", self._cancel_download)

    def _on_patch_failed(self, msg: str) -> None:
        """增量更新失败，回退到全量下载"""
        self._is_patching = False
        download_url = str(self._update_info.get("download_url", ""))
        if not download_url:
            self._on_download_failed(msg)
            return

        self._show_download_ui()
        self._progress_label.setText("增量失败，切换全量下载...")

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

        label = QLabel("新版本已下载完成，点击「立即更新」将自动替换并重启应用。")
        label.setStyleSheet(f"color: {theme.color('text_dim')}; font-size: 13px; background: transparent;")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addStretch()
        self._content_layout.addWidget(label)
        self._content_layout.addStretch()

        self._new_exe_path = path
        self._add_buttons("稍后更新", self.reject, "立即更新", self._do_replace)

    def _on_download_failed(self, msg: str) -> None:
        self._clear_content()
        self._title_label.setText("下载失败")

        label = QLabel(msg)
        label.setStyleSheet(f"color: {theme.color('text_dim')}; font-size: 13px; background: transparent;")
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

    def _do_replace(self) -> None:
        replace_and_restart(self._new_exe_path)

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
                color: {theme.color("text_dim")};
                border: 1px solid {theme.color("progress_bg")};
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {theme.color("hover")}; }}
        """)
        sec_btn.clicked.connect(secondary_action)
        self._btn_row.addWidget(sec_btn)

        if primary_text and primary_action:
            pri_btn = QPushButton(primary_text)
            pri_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pri_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {theme.color("accent")};
                    color: {theme.color("white")};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background: {theme.color("accent_dark")}; }}
            """)
            pri_btn.clicked.connect(primary_action)
            self._btn_row.addWidget(pri_btn)

    def _on_close(self) -> None:
        if self._downloader and self._downloader.isRunning():
            self._downloader.cancel()
        self.reject()

    # endregion
