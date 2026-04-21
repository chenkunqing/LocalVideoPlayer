"""版本号 — 读取 VERSION 文件"""

import os
import sys


def get_version() -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    version_file = os.path.join(base, "VERSION")
    if os.path.isfile(version_file):
        with open(version_file, encoding="utf-8") as f:
            return f.read().strip()
    return "unknown"
