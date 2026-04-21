"""快捷键注册"""

from PySide6.QtGui import QShortcut, QKeySequence

from constants import SPEED_OPTIONS
from shortcut_config import ShortcutConfig


def setup_shortcuts(window, config: ShortcutConfig) -> list[QShortcut]:
    """注册所有快捷键到主窗口，返回 QShortcut 列表以便后续销毁重建"""
    mpv = window.mpv_widget
    overlay = window.controls_overlay
    kf_mgr = window.keyframe_manager

    shortcuts: list[QShortcut] = []

    def _bind(key_name: str, handler: object) -> None:
        seq = config.get(key_name)
        if seq:
            sc = QShortcut(QKeySequence(seq), window)
            sc.activated.connect(handler)
            shortcuts.append(sc)

    def play_pause():
        if mpv.is_eof:
            mpv.seek_absolute(0)
            mpv.set_pause(False)
            return
        mpv.toggle_pause()

    def seek_fwd_1():
        mpv.seek(1)

    def seek_bwd_1():
        mpv.seek(-1)

    def seek_fwd_3():
        mpv.seek(3)

    def seek_bwd_3():
        mpv.seek(-3)

    def frame_forward():
        mpv.frame_step()

    def frame_backward():
        mpv.frame_back_step()

    def volume_up():
        v = min(100, mpv.get_volume() + 5)
        mpv.set_volume(v)
        overlay.volume_slider.setValue(int(v))

    def volume_down():
        v = max(0, mpv.get_volume() - 5)
        mpv.set_volume(v)
        overlay.volume_slider.setValue(int(v))

    def mute_toggle():
        window.toggle_mute()

    def fullscreen_toggle():
        window.toggle_fullscreen()

    def escape_fullscreen():
        window.exit_fullscreen()

    def keyframe_add():
        if window.current_file:
            pos = mpv.current_position
            if kf_mgr.add_keyframe(window.current_file, pos):
                window.refresh_keyframes()

    def keyframe_delete():
        if window.current_file:
            pos = mpv.current_position
            if kf_mgr.delete_keyframe(window.current_file, pos):
                window.refresh_keyframes()

    def keyframe_next():
        if window.current_file:
            pos = mpv.current_position
            nxt = kf_mgr.get_next_keyframe(window.current_file, pos)
            if nxt is not None:
                mpv.seek_absolute(nxt)

    def keyframe_prev():
        if window.current_file:
            pos = mpv.current_position
            prev = kf_mgr.get_prev_keyframe(window.current_file, pos)
            if prev is not None:
                mpv.seek_absolute(prev)

    def speed_up():
        current = mpv.get_speed()
        for s in SPEED_OPTIONS:
            if s > current + 0.01:
                mpv.set_speed(s)
                overlay.speed_button.setText(f"{s}x")
                break

    def speed_down():
        current = mpv.get_speed()
        for s in reversed(SPEED_OPTIONS):
            if s < current - 0.01:
                mpv.set_speed(s)
                overlay.speed_button.setText(f"{s}x")
                break

    def speed_reset():
        mpv.set_speed(1.0)
        overlay.speed_button.setText("1.0x")

    _bind("play_pause", play_pause)
    _bind("seek_forward_1", seek_fwd_1)
    _bind("seek_backward_1", seek_bwd_1)
    _bind("seek_forward_3", seek_fwd_3)
    _bind("seek_backward_3", seek_bwd_3)
    _bind("frame_forward", frame_forward)
    _bind("frame_backward", frame_backward)
    _bind("volume_up", volume_up)
    _bind("volume_down", volume_down)
    _bind("mute_toggle", mute_toggle)
    _bind("fullscreen_toggle", fullscreen_toggle)
    _bind("escape_fullscreen", escape_fullscreen)
    _bind("keyframe_add", keyframe_add)
    _bind("keyframe_delete", keyframe_delete)
    _bind("keyframe_next", keyframe_next)
    _bind("keyframe_prev", keyframe_prev)
    _bind("speed_up", speed_up)
    _bind("speed_down", speed_down)
    _bind("speed_reset", speed_reset)

    return shortcuts
