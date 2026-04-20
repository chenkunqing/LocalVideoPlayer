"""视频库数据模型 — 管理文件夹列表、最近播放、播放列表"""

import json
import os
import time
import uuid

from PySide6.QtCore import QObject, Signal

from constants import LIBRARY_FILE, PLAYLIST_COLORS
from video_scanner import VideoItem, scan_folder, scan_file, probe_durations, ScanWorker


class VideoLibrary(QObject):
    """视频库：持久化文件夹与最近播放记录，启动时重新扫描"""

    library_changed = Signal()
    recent_changed = Signal()
    playlists_changed = Signal()

    def __init__(self, data_dir: str, parent=None):
        super().__init__(parent)
        self._data_path = os.path.join(data_dir, LIBRARY_FILE)
        self._folders: list[str] = []
        self._recent: list[dict[str, object]] = []
        self._playlists: list[dict[str, object]] = []
        self._videos: list[VideoItem] = []
        self._duration_cache: dict[str, float] = {}
        self._scan_worker: ScanWorker | None = None
        self._load()

    def _load(self):
        if not os.path.isfile(self._data_path):
            return
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._folders = data.get("folders", [])
            self._recent = data.get("recent", [])
            self._playlists = data.get("playlists", [])
            self._duration_cache = data.get("durations", {})
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self):
        data = {
            "folders": self._folders,
            "recent": self._recent,
            "playlists": self._playlists,
            "durations": self._duration_cache,
        }
        os.makedirs(os.path.dirname(self._data_path), exist_ok=True)
        tmp = self._data_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._data_path)

    @property
    def folders(self) -> list[str]:
        return list(self._folders)

    @property
    def videos(self) -> list[VideoItem]:
        return list(self._videos)

    @property
    def recent(self) -> list[dict[str, object]]:
        return list(self._recent)

    def add_folder(self, path: str):
        norm = os.path.normpath(path)
        if norm in self._folders:
            return
        self._folders.append(norm)
        self._save()
        self.rescan()

    def remove_folder(self, path: str):
        norm = os.path.normpath(path)
        if norm in self._folders:
            self._folders.remove(norm)
            self._save()
            self.rescan()

    def add_file(self, path: str):
        """拖拽添加单个文件"""
        item = scan_file(path)
        if item is None:
            return
        existing_paths = {v.path for v in self._videos}
        if item.path not in existing_paths:
            dur_map = probe_durations([item.path], self._duration_cache)
            item.duration = dur_map.get(item.path, 0.0)
            self._duration_cache.update(dur_map)
            self._videos.append(item)
            self._save()
            self.library_changed.emit()

    def rescan(self):
        """异步重新扫描所有文件夹"""
        if self._scan_worker is not None and self._scan_worker.isRunning():
            return
        if not self._folders:
            self._videos.clear()
            self.library_changed.emit()
            return
        self._scan_worker = ScanWorker(self._folders, self._duration_cache, self)
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.start()

    def _on_scan_done(self, items: list[VideoItem], dur_map: dict[str, float]):
        seen: set[str] = set()
        unique: list[VideoItem] = []
        for item in items:
            if item.path not in seen:
                seen.add(item.path)
                unique.append(item)
        self._videos = unique
        self._duration_cache.update(dur_map)
        self._save()
        self.library_changed.emit()

    def add_recent(self, path: str, progress: float = 0.0):
        norm = os.path.normpath(path)
        self._recent = [r for r in self._recent if r.get("path") != norm]
        self._recent.insert(0, {
            "path": norm,
            "timestamp": time.time(),
            "progress": progress,
        })
        if len(self._recent) > 20:
            self._recent = self._recent[:20]
        self._save()
        self.recent_changed.emit()

    def get_recent_videos(self) -> list[VideoItem]:
        """返回最近播放中仍存在于库中的视频"""
        path_map = {v.path: v for v in self._videos}
        result: list[VideoItem] = []
        for r in self._recent:
            p = r.get("path", "")
            if isinstance(p, str) and p in path_map:
                result.append(path_map[p])
        return result

    def video_count(self) -> int:
        return len(self._videos)

    def folder_count(self) -> int:
        return len(self._folders)

    def total_size_bytes(self) -> int:
        return sum(v.size_bytes for v in self._videos)

    # region 播放列表

    @property
    def playlists(self) -> list[dict[str, object]]:
        return list(self._playlists)

    def create_playlist(self, name: str) -> dict[str, object]:
        color_pair = PLAYLIST_COLORS[len(self._playlists) % len(PLAYLIST_COLORS)]
        playlist: dict[str, object] = {
            "id": uuid.uuid4().hex[:12],
            "name": name,
            "videos": [],
            "created_at": time.time(),
            "updated_at": time.time(),
            "color_from": color_pair[0],
            "color_to": color_pair[1],
        }
        self._playlists.append(playlist)
        self._save()
        self.playlists_changed.emit()
        return playlist

    def delete_playlist(self, playlist_id: str):
        self._playlists = [p for p in self._playlists if p.get("id") != playlist_id]
        self._save()
        self.playlists_changed.emit()

    def rename_playlist(self, playlist_id: str, name: str):
        for p in self._playlists:
            if p.get("id") == playlist_id:
                p["name"] = name
                p["updated_at"] = time.time()
                self._save()
                self.playlists_changed.emit()
                return

    def add_to_playlist(self, playlist_id: str, path: str):
        norm = os.path.normpath(path)
        for p in self._playlists:
            if p.get("id") == playlist_id:
                videos = p.get("videos", [])
                if not isinstance(videos, list):
                    videos = []
                if norm not in videos:
                    videos.append(norm)
                    p["videos"] = videos
                    p["updated_at"] = time.time()
                    self._save()
                    self.playlists_changed.emit()
                return

    def remove_from_playlist(self, playlist_id: str, path: str):
        norm = os.path.normpath(path)
        for p in self._playlists:
            if p.get("id") == playlist_id:
                videos = p.get("videos", [])
                if isinstance(videos, list) and norm in videos:
                    videos.remove(norm)
                    p["updated_at"] = time.time()
                    self._save()
                    self.playlists_changed.emit()
                return

    def get_playlist(self, playlist_id: str) -> dict[str, object] | None:
        for p in self._playlists:
            if p.get("id") == playlist_id:
                return dict(p)
        return None

    def get_playlist_video_paths(self, playlist_id: str) -> list[str]:
        for p in self._playlists:
            if p.get("id") == playlist_id:
                videos = p.get("videos", [])
                return list(videos) if isinstance(videos, list) else []
        return []

    def get_playlist_videos(self, playlist_id: str) -> list[VideoItem]:
        paths = self.get_playlist_video_paths(playlist_id)
        path_map = {v.path: v for v in self._videos}
        result: list[VideoItem] = []
        for p in paths:
            if p in path_map:
                result.append(path_map[p])
            elif os.path.isfile(p):
                item = scan_file(p)
                if item:
                    item.duration = self._duration_cache.get(item.path, 0.0)
                    result.append(item)
        return result

    # endregion
