"""视频缩略图生成器 — 通过 mpv 截图提取关键帧"""

import hashlib
import locale
import os
import threading
import time

from PySide6.QtCore import QThread, Signal

from constants import THUMBNAIL_SEEK_RATIO


def _thumb_path(video_path: str, thumb_dir: str) -> str:
    key = hashlib.md5(video_path.encode("utf-8")).hexdigest()
    return os.path.join(thumb_dir, f"{key}.jpg")


def _generate_one(path: str, seek: float, out: str) -> bool:
    """为单个视频生成缩略图，成功返回 True"""
    import mpv

    locale.setlocale(locale.LC_NUMERIC, "C")
    seekable_evt = threading.Event()
    seek_done = threading.Event()

    player = mpv.MPV(
        ao="null",
        really_quiet=True,
        vo="null",
        aid="no",
        sid="no",
    )
    player["vf"] = "scale=160:90:force_original_aspect_ratio=increase,crop=160:90"

    @player.property_observer("seekable")
    def _on_seekable(_name: str, value: object) -> None:
        if value:
            seekable_evt.set()

    @player.property_observer("time-pos")
    def _on_time(_name: str, value: object) -> None:
        if isinstance(value, (int, float)) and value >= seek * 0.8:
            seek_done.set()

    try:
        player.play(path)
        if not seekable_evt.wait(timeout=5):
            player.terminate()
            return False

        player.command("seek", str(seek), "absolute")
        seek_done.wait(timeout=5)
        time.sleep(0.1)

        player.screenshot_to_file(out, includes="video")
        player.terminate()
        return os.path.isfile(out)
    except Exception:
        try:
            player.terminate()
        except Exception:
            pass
        return False


def generate_thumbnails(
    paths: list[str],
    duration_cache: dict[str, float],
    thumb_dir: str,
) -> dict[str, str]:
    """批量生成缩略图，跳过已存在的。返回 {视频路径: 缩略图路径}。"""
    os.makedirs(thumb_dir, exist_ok=True)
    result: dict[str, str] = {}

    for path in paths:
        out = _thumb_path(path, thumb_dir)
        if os.path.isfile(out):
            result[path] = out
            continue

        duration = duration_cache.get(path, 0.0)
        seek = max(duration * THUMBNAIL_SEEK_RATIO, 0.5) if duration > 0 else 1.0

        if _generate_one(path, seek, out):
            result[path] = out

    return result


class ThumbnailWorker(QThread):
    """后台缩略图生成线程"""
    finished = Signal(dict)

    def __init__(
        self,
        paths: list[str],
        duration_cache: dict[str, float],
        thumb_dir: str,
        parent=None,
    ):
        super().__init__(parent)
        self._paths = paths
        self._duration_cache = duration_cache
        self._thumb_dir = thumb_dir

    def run(self):
        result = generate_thumbnails(self._paths, self._duration_cache, self._thumb_dir)
        self.finished.emit(result)
