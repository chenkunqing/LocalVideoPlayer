"""版本号 — 读取 VERSION 文件"""

import os


def get_version() -> str:
    version_file = os.path.join(os.path.dirname(__file__), "VERSION")
    if os.path.isfile(version_file):
        with open(version_file, encoding="utf-8") as f:
            return f.read().strip()
    return "unknown"
