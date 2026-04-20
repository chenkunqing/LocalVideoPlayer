"""视频缩略图生成器 — 通过 ffmpeg 提取关键帧"""

import hashlib
import os
import subprocess

from PySide6.QtCore import QThread, Signal

from constants import THUMBNAIL_SEEK_RATIO


def _thumb_path(video_path: str, thumb_dir: str) -> str:
    key = hashlib.md5(video_path.encode("utf-8")).hexdigest()
    return os.path.join(thumb_dir, f"{key}.jpg")


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

        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", f"{seek:.2f}",
                    "-i", path,
                    "-frames:v", "1",
                    "-vf", "scale=160:90:force_original_aspect_ratio=increase,crop=160:90",
                    "-q:v", "6",
                    out,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            if os.path.isfile(out):
                result[path] = out
        except Exception:
            pass

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
