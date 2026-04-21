"""快捷键配置管理 — 用户自定义快捷键持久化"""

import json
import os
import tempfile

from PySide6.QtCore import QObject, Signal

from constants import SHORTCUTS, SHORTCUTS_FILE


SHORTCUT_LABELS: dict[str, str] = {
    "keyframe_add": "添加关键帧",
    "keyframe_delete": "删除关键帧",
    "keyframe_next": "下一关键帧",
    "keyframe_prev": "上一关键帧",
    "play_pause": "播放/暂停",
    "seek_forward_1": "快进 1 秒",
    "seek_backward_1": "快退 1 秒",
    "seek_forward_3": "快进 3 秒",
    "seek_backward_3": "快退 3 秒",
    "frame_forward": "下一帧",
    "frame_backward": "上一帧",
    "volume_up": "音量增大",
    "volume_down": "音量减小",
    "mute_toggle": "静音切换",
    "fullscreen_toggle": "全屏切换",
    "escape_fullscreen": "退出全屏",
    "speed_up": "加速播放",
    "speed_down": "减速播放",
    "speed_reset": "重置速度",
}


class ShortcutConfig(QObject):
    """管理用户自定义快捷键，持久化到 JSON 文件"""
    shortcuts_changed = Signal()

    def __init__(self, data_dir: str):
        super().__init__()
        self._path = os.path.join(data_dir, SHORTCUTS_FILE)
        os.makedirs(data_dir, exist_ok=True)
        self._overrides: dict[str, str] = self._load()

    def get(self, action: str) -> str:
        return self._overrides.get(action, SHORTCUTS.get(action, ""))

    def get_all(self) -> dict[str, str]:
        merged = dict(SHORTCUTS)
        merged.update(self._overrides)
        return merged

    def set_binding(self, action: str, key_seq: str) -> str | None:
        """设置绑定。若与其他动作冲突，返回冲突动作名；否则返回 None。"""
        current_all = self.get_all()
        for other_action, other_seq in current_all.items():
            if other_action != action and other_seq == key_seq:
                return other_action
        self._overrides[action] = key_seq
        self._save()
        self.shortcuts_changed.emit()
        return None

    def swap_binding(self, action: str, key_seq: str) -> None:
        """设置绑定，并将冲突方交换为当前动作的原绑定。"""
        current_all = self.get_all()
        old_seq = current_all.get(action, "")
        for other_action, other_seq in current_all.items():
            if other_action != action and other_seq == key_seq:
                self._overrides[other_action] = old_seq
                break
        self._overrides[action] = key_seq
        self._save()
        self.shortcuts_changed.emit()

    def clear_binding(self, action: str) -> None:
        """清除某个动作的快捷键绑定"""
        self._overrides[action] = ""
        self._save()
        self.shortcuts_changed.emit()

    def reset_all(self) -> None:
        self._overrides.clear()
        self._save()
        self.shortcuts_changed.emit()

    def _load(self) -> dict[str, str]:
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        dir_name = os.path.dirname(self._path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._overrides, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._path)
        except OSError:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
