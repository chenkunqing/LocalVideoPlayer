"""工具函数"""

import hashlib
import os


def format_time(seconds):
    """秒数转为 H:MM:SS 或 M:SS 格式"""
    if seconds is None or seconds < 0:
        return "0:00"
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def file_key(path):
    """根据文件路径生成 16 位哈希键"""
    normalized = os.path.normpath(path)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
