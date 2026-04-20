"""生成 KK Player 应用图标"""

import sys
from PySide6.QtCore import Qt, QRect, QPointF
from PySide6.QtGui import (
    QGuiApplication, QImage, QPainter, QColor, QBrush,
    QPen, QPainterPath, QLinearGradient, QRadialGradient,
)


BLUE = QColor("#4A9EFF")
BLUE_LIGHT = QColor("#6BB5FF")
BLUE_DARK = QColor("#2D7CE0")
BG = QColor("#181818")
SIZES = [256, 128, 64, 48, 32, 16]


def draw_icon(size: int) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    s = size
    margin = s * 0.02

    # 圆角矩形背景
    bg_path = QPainterPath()
    radius = s * 0.18
    bg_path.addRoundedRect(margin, margin, s - margin * 2, s - margin * 2, radius, radius)

    bg_grad = QLinearGradient(0, 0, 0, s)
    bg_grad.setColorAt(0, QColor("#1e1e1e"))
    bg_grad.setColorAt(1, QColor("#111111"))
    p.fillPath(bg_path, QBrush(bg_grad))

    # 播放三角形（右偏移让视觉居中）
    cx = s * 0.53
    cy = s * 0.50
    tri_h = s * 0.44
    tri_w = tri_h * 0.9

    tri = QPainterPath()
    tri.moveTo(cx - tri_w * 0.4, cy - tri_h * 0.5)
    tri.lineTo(cx + tri_w * 0.6, cy)
    tri.lineTo(cx - tri_w * 0.4, cy + tri_h * 0.5)
    tri.closeSubpath()

    # 蓝色渐变填充
    tri_grad = QLinearGradient(cx - tri_w * 0.4, cy - tri_h * 0.5, cx + tri_w * 0.6, cy + tri_h * 0.5)
    tri_grad.setColorAt(0, BLUE_LIGHT)
    tri_grad.setColorAt(1, BLUE_DARK)
    p.fillPath(tri, QBrush(tri_grad))

    # 高光效果
    highlight = QRadialGradient(QPointF(cx - tri_w * 0.1, cy - tri_h * 0.2), tri_h * 0.6)
    highlight.setColorAt(0, QColor(255, 255, 255, 35))
    highlight.setColorAt(1, QColor(255, 255, 255, 0))
    p.fillPath(tri, QBrush(highlight))

    p.end()
    return img


def main():
    app = QGuiApplication(sys.argv)

    images = [draw_icon(s) for s in SIZES]

    # 保存为多尺寸 ICO
    from PySide6.QtGui import QImageWriter
    ico_path = "icon.ico"

    # PySide6 QImageWriter 不支持多尺寸 ICO，改用逐个 PNG 后手动拼 ICO
    import struct, io

    def build_ico(imgs: list[QImage]) -> bytes:
        entries = []
        data_blocks = []
        offset = 6 + 16 * len(imgs)

        for img in imgs:
            buf = io.BytesIO()
            # 转为 PNG bytes
            ba = img.save  # noqa
            from PySide6.QtCore import QBuffer, QIODevice
            qbuf = QBuffer()
            qbuf.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(qbuf, "PNG")
            png_data = bytes(qbuf.data())
            qbuf.close()

            w = img.width() if img.width() < 256 else 0
            h = img.height() if img.height() < 256 else 0

            entry = struct.pack('<BBBBHHII',
                w, h, 0, 0, 1, 32, len(png_data), offset)
            entries.append(entry)
            data_blocks.append(png_data)
            offset += len(png_data)

        header = struct.pack('<HHH', 0, 1, len(imgs))
        return header + b''.join(entries) + b''.join(data_blocks)

    ico_bytes = build_ico(images)
    with open(ico_path, 'wb') as f:
        f.write(ico_bytes)

    # 同时保存 256x256 PNG 预览
    images[0].save("icon.png", "PNG")

    print(f"已生成 icon.ico ({len(SIZES)} 个尺寸) 和 icon.png")


if __name__ == "__main__":
    main()
