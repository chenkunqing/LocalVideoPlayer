"""KK Player — 入口"""

import os
import sys

# libmpv DLL 路径设置（必须在 import mpv 之前）
if getattr(sys, "frozen", False):
    _dll_dir = sys._MEIPASS
else:
    _dll_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.add_dll_directory(_dll_dir)
os.environ["PATH"] = _dll_dir + os.pathsep + os.environ.get("PATH", "")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from theme import theme
from main_window import MainWindow


def _build_global_style() -> str:
    return f"""
    * {{
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        color: {theme.color("text")};
    }}
    QMainWindow, #MainWindow {{
        background-color: {theme.color("bg")};
    }}
    QToolTip {{
        background: rgba(0, 0, 0, 0.85);
        color: white;
        border: 1px solid {theme.color("border")};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
        font-family: 'Consolas', monospace;
    }}
    """


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KK Player")
    app.setStyle("Fusion")

    # 数据目录
    if getattr(sys, "frozen", False):
        data_dir = os.path.join(os.path.dirname(sys.executable), "data")
    else:
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data"
        )

    theme.load(data_dir)
    app.setStyleSheet(_build_global_style())
    theme.theme_changed.connect(lambda: app.setStyleSheet(_build_global_style()))

    window = MainWindow(data_dir)
    window.show()

    # 命令行参数打开文件
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.isfile(file_path):
            window.play_file(file_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
