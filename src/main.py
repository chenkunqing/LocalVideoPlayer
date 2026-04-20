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

from constants import COLOR_BG, COLOR_PANEL, COLOR_TEXT, COLOR_BORDER, COLOR_ACCENT
from main_window import MainWindow


GLOBAL_STYLE = f"""
    * {{
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        color: {COLOR_TEXT};
    }}
    QMainWindow, #MainWindow {{
        background-color: {COLOR_BG};
    }}
    QToolTip {{
        background: rgba(0, 0, 0, 0.85);
        color: white;
        border: 1px solid {COLOR_BORDER};
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
    app.setStyleSheet(GLOBAL_STYLE)

    # 数据目录
    if getattr(sys, "frozen", False):
        data_dir = os.path.join(os.path.dirname(sys.executable), "data")
    else:
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data"
        )

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
