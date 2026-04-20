"""版本号 — 优先读 git commit，打包环境回退到 VERSION 文件"""

import os
import subprocess


def get_version() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    version_file = os.path.join(os.path.dirname(__file__), "VERSION")
    if os.path.isfile(version_file):
        with open(version_file, encoding="utf-8") as f:
            return f.read().strip()

    return "unknown"
