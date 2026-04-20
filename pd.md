# 2026-04-20

【18:35】fix: 修复拖拽视频文件到播放器后鼠标光标消失的问题 — dropEvent 中恢复箭头光标并重启隐藏定时器 | src/main_window.py

【18:38】fix: 修复视频播放时底部控制栏无法显示的问题 — ControlsOverlay 及子容器未启用 mouseTracking，导致鼠标移动事件无法冒泡到 MainWindow 触发 show_controls | src/controls_overlay.py, src/main_window.py
