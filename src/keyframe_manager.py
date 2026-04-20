"""关键帧管理器 — JSON 持久化"""

import bisect
import json
import os
import tempfile

from utils import file_key


class KeyframeManager:

    def __init__(self, data_dir):
        self._path = os.path.join(data_dir, "keyframes.json")
        os.makedirs(data_dir, exist_ok=True)
        self._data = self._load()

    def get_keyframes(self, file_path):
        """获取指定视频的所有关键帧（已排序）"""
        key = file_key(file_path)
        entry = self._data.get(key)
        if entry is None:
            return []
        return list(entry["keyframes"])

    def add_keyframe(self, file_path, time_pos):
        """在指定时间添加关键帧，自动去重（0.1秒内视为相同）"""
        key = file_key(file_path)
        if key not in self._data:
            self._data[key] = {"path": os.path.normpath(file_path), "keyframes": []}
        kfs = self._data[key]["keyframes"]
        for kf in kfs:
            if abs(kf - time_pos) < 0.1:
                return False
        bisect.insort(kfs, round(time_pos, 3))
        self._save()
        return True

    def delete_keyframe(self, file_path, time_pos, tolerance=0.5):
        """删除距离 time_pos 最近的关键帧（在容差范围内）"""
        key = file_key(file_path)
        entry = self._data.get(key)
        if not entry or not entry["keyframes"]:
            return False
        kfs = entry["keyframes"]
        closest_idx = None
        closest_dist = float("inf")
        for i, kf in enumerate(kfs):
            dist = abs(kf - time_pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_idx = i
        if closest_dist <= tolerance:
            kfs.pop(closest_idx)
            self._save()
            return True
        return False

    def get_next_keyframe(self, file_path, current_pos):
        """获取当前位置之后的下一个关键帧"""
        kfs = self.get_keyframes(file_path)
        idx = bisect.bisect_right(kfs, current_pos + 0.05)
        if idx < len(kfs):
            return kfs[idx]
        return None

    def get_prev_keyframe(self, file_path, current_pos):
        """获取当前位置之前的上一个关键帧"""
        kfs = self.get_keyframes(file_path)
        idx = bisect.bisect_left(kfs, current_pos - 0.05)
        if idx > 0:
            return kfs[idx - 1]
        return None

    def _load(self):
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self):
        dir_name = os.path.dirname(self._path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._path)
        except OSError:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
