"""视频文件扫描器"""

import os
from dataclasses import dataclass, field

from PySide6.QtCore import QThread, Signal

from constants import VIDEO_EXTENSIONS


@dataclass
class VideoItem:
    path: str
    name: str
    ext: str
    folder: str
    size_bytes: int
    modified: float
    duration: float = 0.0


def scan_folder(folder_path: str) -> list[VideoItem]:
    """同步扫描单个文件夹，返回视频文件列表"""
    items: list[VideoItem] = []
    if not os.path.isdir(folder_path):
        return items
    for root, _dirs, files in os.walk(folder_path):
        for fname in files:
            ext_lower = os.path.splitext(fname)[1].lower()
            if ext_lower not in VIDEO_EXTENSIONS:
                continue
            full = os.path.normpath(os.path.join(root, fname))
            try:
                stat = os.stat(full)
            except OSError:
                continue
            items.append(VideoItem(
                path=full,
                name=os.path.splitext(fname)[0],
                ext=ext_lower.lstrip(".").upper(),
                folder=os.path.basename(os.path.dirname(full)),
                size_bytes=stat.st_size,
                modified=stat.st_mtime,
            ))
    return items


def scan_file(file_path: str) -> VideoItem | None:
    """为单个文件创建 VideoItem"""
    ext_lower = os.path.splitext(file_path)[1].lower()
    if ext_lower not in VIDEO_EXTENSIONS:
        return None
    full = os.path.normpath(file_path)
    try:
        stat = os.stat(full)
    except OSError:
        return None
    return VideoItem(
        path=full,
        name=os.path.splitext(os.path.basename(full))[0],
        ext=ext_lower.lstrip(".").upper(),
        folder=os.path.basename(os.path.dirname(full)),
        size_bytes=stat.st_size,
        modified=stat.st_mtime,
    )


class ScanWorker(QThread):
    """后台扫描线程"""
    finished = Signal(list)

    def __init__(self, folders: list[str], parent=None):
        super().__init__(parent)
        self._folders = folders

    def run(self):
        results: list[VideoItem] = []
        for folder in self._folders:
            results.extend(scan_folder(folder))
        self.finished.emit(results)
