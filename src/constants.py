"""全局常量"""

# region 颜色
COLOR_BG = "#09090b"
COLOR_PANEL = "#121214"
COLOR_BORDER = "#27272a"
COLOR_BORDER_HALF = "rgba(39, 39, 42, 0.5)"
COLOR_ACCENT = "#8b5cf6"
COLOR_ACCENT_DARK = "#7c3aed"
COLOR_ACCENT_LIGHT = "#a78bfa"
COLOR_TEXT = "#fafafa"
COLOR_TEXT_DIM = "#71717a"
COLOR_TEXT_DARK = "#52525b"
COLOR_PROGRESS_BG = "#3f3f46"
COLOR_RED = "#dc2626"
COLOR_WHITE = "#ffffff"
COLOR_BLACK = "#000000"
# endregion

# region 播放速度
SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
# endregion

# region 支持的视频格式
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv",
    ".flv", ".webm", ".m4v", ".ts", ".m2ts",
    ".mpg", ".mpeg", ".rm", ".rmvb", ".3gp",
}
# endregion

# region 快捷键
SHORTCUTS = {
    "keyframe_add": "K",
    "keyframe_delete": "Shift+K",
    "keyframe_next": "Down",
    "keyframe_prev": "Up",
    "play_pause": "Space",
    "seek_forward_1": "Right",
    "seek_backward_1": "Left",
    "seek_forward_3": "Ctrl+Right",
    "seek_backward_3": "Ctrl+Left",
    "frame_forward": "Shift+Right",
    "frame_backward": "Shift+Left",
    "volume_up": "Shift+Up",
    "volume_down": "Shift+Down",
    "mute_toggle": "M",
    "fullscreen_toggle": "F",
    "escape_fullscreen": "Escape",
    "speed_up": "]",
    "speed_down": "[",
    "speed_reset": "Backspace",
}
# endregion

# region 控制栏
CONTROLS_HIDE_DELAY_MS = 2500
# endregion

# region 窗口
WINDOW_DEFAULT_WIDTH = 1280
WINDOW_DEFAULT_HEIGHT = 720
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 500
TITLE_BAR_HEIGHT = 32
# endregion

# region 侧边栏
SIDEBAR_WIDTH = 240
# endregion

# region 分页
PAGE_SIZE = 50
# endregion

# region 播放列表卡片渐变色
PLAYLIST_COLORS = [
    ("#ef4444", "#f97316"),  # 红→橙
    ("#3b82f6", "#6366f1"),  # 蓝→靛
    ("#10b981", "#14b8a6"),  # 绿→青
    ("#8b5cf6", "#a855f7"),  # 紫
    ("#f59e0b", "#eab308"),  # 琥珀→黄
    ("#ec4899", "#f43f5e"),  # 粉→玫瑰
]
# endregion

# region 缩略图
THUMBNAILS_DIR = "thumbnails"
THUMBNAIL_SEEK_RATIO = 0.3
# endregion

# region 数据文件
KEYFRAMES_FILE = "keyframes.json"
LIBRARY_FILE = "library.json"
SHORTCUTS_FILE = "shortcuts.json"
UPDATE_CONFIG_FILE = "update.json"
# endregion
