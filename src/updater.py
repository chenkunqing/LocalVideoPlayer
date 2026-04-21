"""自动更新 — 检查、下载、配置"""

import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error

from PySide6.QtCore import QThread, Signal

from constants import UPDATE_CONFIG_FILE, UPDATE_SERVER_URL
from version import get_version


class UpdateConfig:
    """读写 data/update.json（服务器地址等）"""

    def __init__(self, data_dir: str):
        self._path = os.path.join(data_dir, UPDATE_CONFIG_FILE)
        self._data = self._load()

    def _load(self) -> dict[str, str]:
        if os.path.isfile(self._path):
            with open(self._path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(self._path), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @property
    def server_url(self) -> str:
        return self._data.get("server_url", "") or UPDATE_SERVER_URL

    @server_url.setter
    def server_url(self, value: str) -> None:
        self._data["server_url"] = value.rstrip("/")
        self._save()


class UpdateChecker(QThread):
    """后台线程：检查更新"""
    update_available = Signal(dict)
    no_update = Signal()
    check_failed = Signal(str)

    def __init__(self, server_url: str, parent=None):
        super().__init__(parent)
        self._server_url = server_url

    def run(self) -> None:
        url = f"{self._server_url}/api/update/latest"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data: dict[str, object] = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            self.check_failed.emit(f"网络错误：{e.reason}")
            return
        except Exception as e:
            self.check_failed.emit(f"检查失败：{e}")
            return

        remote_version = str(data.get("version", ""))
        local_version = get_version()
        if remote_version and remote_version != local_version:
            self.update_available.emit(data)
        else:
            self.no_update.emit()


class UpdateDownloader(QThread):
    """后台线程：下载安装包"""
    progress = Signal(int, int)
    download_finished = Signal(str)
    download_failed = Signal(str)

    def __init__(self, download_url: str, parent=None):
        super().__init__(parent)
        self._download_url = download_url
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        dest = os.path.join(tempfile.gettempdir(), "KKPlayer_update.exe")
        try:
            req = urllib.request.Request(self._download_url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 65536

                with open(dest, "wb") as f:
                    while True:
                        if self._cancelled:
                            self._cleanup(dest)
                            self.download_failed.emit("下载已取消")
                            return
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total)

            self.download_finished.emit(dest)
        except Exception as e:
            self._cleanup(dest)
            if not self._cancelled:
                self.download_failed.emit(f"下载失败：{e}")

    @staticmethod
    def _cleanup(path: str) -> None:
        try:
            os.unlink(path)
        except OSError:
            pass


class UpdatePatcher(QThread):
    """后台线程：下载补丁并合并生成新 exe"""
    progress = Signal(int, int)
    download_finished = Signal(str)
    download_failed = Signal(str)

    def __init__(self, patch_url: str, parent=None):
        super().__init__(parent)
        self._patch_url = patch_url
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        import bsdiff4

        dest = os.path.join(tempfile.gettempdir(), "KKPlayer_update.exe")
        try:
            req = urllib.request.Request(self._patch_url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                patch_data = bytearray()
                chunk_size = 65536

                while True:
                    if self._cancelled:
                        self.download_failed.emit("下载已取消")
                        return
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    patch_data.extend(chunk)
                    self.progress.emit(len(patch_data), total)

            self.progress.emit(total, total)

            current_exe = sys.executable
            with open(current_exe, "rb") as f:
                old_data = f.read()

            new_data = bsdiff4.patch(old_data, bytes(patch_data))

            with open(dest, "wb") as f:
                f.write(new_data)

            self.download_finished.emit(dest)
        except Exception as e:
            self._cleanup(dest)
            if not self._cancelled:
                self.download_failed.emit(f"增量更新失败：{e}")

    @staticmethod
    def _cleanup(path: str) -> None:
        try:
            os.unlink(path)
        except OSError:
            pass


def replace_and_restart(new_exe_path: str) -> None:
    """通过批处理脚本替换当前 exe 并重启（Windows 无法覆盖运行中的 exe）"""
    current_exe = sys.executable
    bat_path = os.path.join(tempfile.gettempdir(), "kkplayer_update.bat")

    script = f"""@echo off
ping 127.0.0.1 -n 3 >nul
copy /y "{new_exe_path}" "{current_exe}"
del "{new_exe_path}"
start "" "{current_exe}"
del "%~f0"
"""
    with open(bat_path, "w", encoding="mbcs") as f:
        f.write(script)

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    from PySide6.QtWidgets import QApplication
    QApplication.quit()
