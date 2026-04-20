"""开发模式启动器 — 监听 src/ 下 .py 文件变化，自动重启应用"""

import os
import sys
import signal
import subprocess
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
PYTHON = sys.executable
DEBOUNCE_SECONDS = 1.0


class RestartHandler(FileSystemEventHandler):
    def __init__(self, runner: "AppRunner"):
        self._runner = runner
        self._last_trigger = 0.0

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        now = time.time()
        if now - self._last_trigger < DEBOUNCE_SECONDS:
            return
        self._last_trigger = now
        rel = os.path.relpath(event.src_path, PROJECT_ROOT)
        print(f"\n[dev] 检测到变更: {rel}，正在重启…")
        self._runner.restart()


class AppRunner:
    def __init__(self):
        self._process: subprocess.Popen[bytes] | None = None

    def start(self):
        self._process = subprocess.Popen(
            [PYTHON, os.path.join(SRC_DIR, "main.py")],
            cwd=PROJECT_ROOT,
        )
        print(f"[dev] 应用已启动 (PID={self._process.pid})")

    def stop(self):
        if self._process is None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()
        self._process = None

    def restart(self):
        self.stop()
        self.start()


def main():
    runner = AppRunner()
    runner.start()

    handler = RestartHandler(runner)
    observer = Observer()
    observer.schedule(handler, SRC_DIR, recursive=True)
    observer.start()
    print(f"[dev] 正在监听 src/ 目录，修改 .py 文件后自动重启")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[dev] 正在退出…")
    finally:
        observer.stop()
        observer.join()
        runner.stop()


if __name__ == "__main__":
    main()
