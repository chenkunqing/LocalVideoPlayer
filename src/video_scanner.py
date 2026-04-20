"""视频文件扫描器"""

import locale
import os
import threading
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


def probe_durations(
    paths: list[str], cache: dict[str, float]
) -> dict[str, float]:
    """用 headless mpv 实例批量探测视频时长，跳过已缓存的"""
    result = dict(cache)
    uncached = [p for p in paths if p not in result or result[p] <= 0]
    if not uncached:
        return result

    import mpv

    locale.setlocale(locale.LC_NUMERIC, "C")
    ready = threading.Event()
    dur_val: list[float] = [0.0]

    player = mpv.MPV(vid="no", ao="null", really_quiet=True)

    @player.property_observer("duration")
    def _on_dur(_name: str, value: object) -> None:
        if isinstance(value, (int, float)) and value > 0:
            dur_val[0] = float(value)
            ready.set()

    for path in uncached:
        ready.clear()
        dur_val[0] = 0.0
        try:
            player.play(path)
            ready.wait(timeout=3)
            if dur_val[0] > 0:
                result[path] = dur_val[0]
        except Exception:
            pass

    try:
        player.terminate()
    except Exception:
        pass

    return result


class ScanWorker(QThread):
    """后台扫描线程"""
    finished = Signal(list, dict)

    def __init__(
        self, folders: list[str], duration_cache: dict[str, float] | None = None, parent=None
    ):
        super().__init__(parent)
        self._folders = folders
        self._duration_cache = duration_cache or {}

    def run(self):
        results: list[VideoItem] = []
        for folder in self._folders:
            results.extend(scan_folder(folder))

        paths = [item.path for item in results]
        dur_map = probe_durations(paths, self._duration_cache)

        for item in results:
            item.duration = dur_map.get(item.path, 0.0)

        self.finished.emit(results, dur_map)
