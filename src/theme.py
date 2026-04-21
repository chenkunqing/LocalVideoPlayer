"""主题管理 — 深色/浅色切换"""

import json
import os

from PySide6.QtCore import QObject, Signal

SETTINGS_FILE = "settings.json"

DARK = {
    "bg": "#09090b",
    "panel": "#121214",
    "border": "#27272a",
    "border_half": "rgba(39, 39, 42, 0.5)",
    "accent": "#8b5cf6",
    "accent_dark": "#7c3aed",
    "accent_light": "#a78bfa",
    "text": "#fafafa",
    "text_dim": "#71717a",
    "text_dark": "#52525b",
    "progress_bg": "#3f3f46",
    "red": "#dc2626",
    "white": "#ffffff",
    "black": "#000000",
    "hover": "rgba(39, 39, 42, 0.6)",
    "hover_strong": "rgba(39, 39, 42, 0.8)",
    "input_bg": "rgba(9, 9, 11, 0.5)",
    "menu_bg": "rgba(24, 24, 27, 0.95)",
    "scrollbar": "#3f3f46",
    "btn_face": "#ffffff",
    "btn_face_text": "#000000",
    "btn_face_hover": "#e4e4e7",
}

LIGHT = {
    "bg": "#f4f4f5",
    "panel": "#ffffff",
    "border": "#e4e4e7",
    "border_half": "rgba(228, 228, 231, 0.5)",
    "accent": "#8b5cf6",
    "accent_dark": "#7c3aed",
    "accent_light": "#a78bfa",
    "text": "#18181b",
    "text_dim": "#52525b",
    "text_dark": "#a1a1aa",
    "progress_bg": "#d4d4d8",
    "red": "#dc2626",
    "white": "#ffffff",
    "black": "#000000",
    "hover": "rgba(0, 0, 0, 0.06)",
    "hover_strong": "rgba(0, 0, 0, 0.1)",
    "input_bg": "rgba(0, 0, 0, 0.04)",
    "menu_bg": "rgba(255, 255, 255, 0.95)",
    "scrollbar": "#a1a1aa",
    "btn_face": "#18181b",
    "btn_face_text": "#ffffff",
    "btn_face_hover": "#27272a",
}


class ThemeManager(QObject):
    theme_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._name = "dark"
        self._colors = dict(DARK)
        self._settings_path = ""

    def color(self, key: str) -> str:
        return self._colors[key]

    @property
    def is_dark(self) -> bool:
        return self._name == "dark"

    def load(self, data_dir: str) -> None:
        self._settings_path = os.path.join(data_dir, SETTINGS_FILE)
        try:
            with open(self._settings_path, encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("theme", "dark")
            if name in ("dark", "light"):
                self._name = name
                self._colors = dict(LIGHT if name == "light" else DARK)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        if not self._settings_path:
            return
        data: dict[str, object] = {}
        try:
            with open(self._settings_path, encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        data["theme"] = self._name
        tmp = self._settings_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._settings_path)

    def toggle(self) -> None:
        self._name = "light" if self._name == "dark" else "dark"
        self._colors = dict(LIGHT if self._name == "light" else DARK)
        self._save()
        self.theme_changed.emit()

    def set_theme(self, name: str) -> None:
        if name == self._name:
            return
        self._name = name
        self._colors = dict(LIGHT if name == "light" else DARK)
        self._save()
        self.theme_changed.emit()


theme = ThemeManager()
