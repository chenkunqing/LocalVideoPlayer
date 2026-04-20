# PureView - 本地视频播放器

极简风格的本地视频播放器，基于 libmpv 引擎，提供流畅的播放体验与关键帧标记、播放列表管理等实用功能。

## 功能特性

### 视频播放

- 支持 15 种常见格式：MP4、MKV、AVI、MOV、WMV、FLV、WebM、M4V、TS、M2TS、MPG、MPEG、RM、RMVB、3GP
- GPU 硬件加速解码
- 播放速度调节（0.5x / 0.75x / 1.0x / 1.25x / 1.5x / 2.0x）
- 音量控制与独立静音开关
- 拖放视频文件直接播放

### 关键帧标记

- 在视频任意位置添加/删除关键帧书签
- 进度条上直观显示关键帧位置
- 快捷键在关键帧之间快速跳转
- 自动持久化存储

### 视频库管理

- 添加多个文件夹，自动递归扫描视频文件
- 显示文件名、大小、格式、时长等元数据
- 最近播放记录（最多 20 条）
- 分页加载，支持大量文件

### 播放列表

- 创建、重命名、删除播放列表
- 向列表中添加/移除视频
- 渐变色卡片展示，视觉区分

### 快捷键自定义

- 17 个可自定义快捷键操作
- 冲突检测与自动交换
- 支持一键恢复默认设置

### 界面

- 深色主题，Win11 风格无边框窗口
- 播放时控制栏自动隐藏（2.5 秒无操作后淡出）
- 全屏模式
- 窗口四边及四角自由缩放

## 安装

### 环境要求

- Python 3.10+
- Windows 操作系统
- `libmpv-2.dll`（放置于项目根目录）

### 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：

| 依赖 | 用途 |
|------|------|
| PySide6 >= 6.6.0 | Qt6 界面框架 |
| python-mpv >= 1.0.6 | libmpv Python 绑定 |
| pyinstaller >= 6.0 | 打包为独立可执行文件 |
| watchdog >= 6.0.0 | 开发模式文件监听 |

## 使用方法

### 启动

```bash
# 直接运行
python src/main.py

# 开发模式（文件修改后自动重启）
python dev.py

# 指定视频文件打开
python src/main.py "C:\path\to\video.mp4"
```

### 打包为可执行文件

```bash
pyinstaller build.spec
```

输出路径：`dist/PureView/PureView.exe`

## 默认快捷键

| 操作 | 快捷键 |
|------|--------|
| 播放 / 暂停 | `Space` |
| 前进 1 秒 | `Right` |
| 后退 1 秒 | `Left` |
| 前进 3 秒 | `Ctrl+Right` |
| 后退 3 秒 | `Ctrl+Left` |
| 音量增大 | `Shift+Up` |
| 音量减小 | `Shift+Down` |
| 静音切换 | `M` |
| 全屏 | `F` |
| 退出全屏 | `Escape` |
| 添加关键帧 | `K` |
| 删除关键帧 | `Shift+K` |
| 下一个关键帧 | `Down` |
| 上一个关键帧 | `Up` |
| 加速播放 | `]` |
| 减速播放 | `[` |
| 速度重置 | `Backspace` |

所有快捷键均可在设置中自定义。

## 项目结构

```
PureView/
├── src/                    # 源代码
│   ├── main.py             # 入口，全局样式
│   ├── main_window.py      # 主窗口，视图切换
│   ├── mpv_widget.py       # libmpv 渲染组件
│   ├── controls_overlay.py # 底部控制栏 + 顶部信息栏
│   ├── progress_bar.py     # 自定义进度条（含关键帧标记）
│   ├── title_bar.py        # 无边框标题栏
│   ├── playlist_view.py    # 视频库 / 播放列表视图
│   ├── playlist_sidebar.py # 侧边栏导航
│   ├── video_library.py    # 数据模型与持久化
│   ├── video_scanner.py    # 文件夹扫描与时长探测
│   ├── keyframe_manager.py # 关键帧管理
│   ├── shortcuts.py        # 快捷键注册
│   ├── shortcut_config.py  # 快捷键配置读写
│   ├── shortcut_settings.py# 快捷键设置界面
│   ├── constants.py        # 全局常量
│   └── utils.py            # 工具函数
├── data/                   # 运行时数据（自动生成）
│   ├── library.json        # 视频库、播放列表
│   ├── keyframes.json      # 关键帧数据
│   └── shortcuts.json      # 自定义快捷键
├── requirements.txt        # Python 依赖
├── build.spec              # PyInstaller 打包配置
├── dev.py                  # 开发模式启动脚本
└── libmpv-2.dll            # mpv 视频引擎库
```

## 技术栈

- **界面框架**：PySide6（Qt 6）
- **视频引擎**：libmpv（通过 python-mpv 绑定）
- **数据存储**：JSON 文件
- **打包工具**：PyInstaller
