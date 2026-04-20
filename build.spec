# -*- mode: python ; coding: utf-8 -*-
# PureView 视频播放器 PyInstaller 打包配置

import os

block_cipher = None
project_root = SPECPATH

a = Analysis(
    [os.path.join(project_root, 'src', 'main.py')],
    pathex=[os.path.join(project_root, 'src')],
    binaries=[(os.path.join(project_root, 'libmpv-2.dll'), '.')],
    datas=[],
    hiddenimports=['mpv'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PureView',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PureView',
)
