# -*- mode: python ; coding: utf-8 -*-
# KK Player PyInstaller 打包配置

import os

block_cipher = None
project_root = SPECPATH

a = Analysis(
    [os.path.join(project_root, 'src', 'main.py')],
    pathex=[os.path.join(project_root, 'src')],
    binaries=[(os.path.join(project_root, 'libmpv-2.dll'), '.')],
    datas=[
        (os.path.join(project_root, 'src', 'VERSION'), '.'),
        (os.path.join(project_root, 'icon.ico'), '.'),
    ],
    hiddenimports=['mpv', 'bsdiff4'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebChannel',
        'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtQmlModels',
        'PySide6.QtDesigner', 'PySide6.QtDesignerComponents',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic',
        'PySide6.QtQuick3D', 'PySide6.QtQuick3DRuntimeRender',
        'PySide6.QtGraphs', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
        'PySide6.QtNetwork', 'PySide6.QtNetworkAuth',
        'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
        'PySide6.QtShaderTools',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtSensors',
        'PySide6.QtSerialPort', 'PySide6.QtPositioning',
        'PySide6.QtRemoteObjects', 'PySide6.QtSql', 'PySide6.QtTest',
        'PySide6.QtXml', 'PySide6.QtHelp', 'PySide6.QtSvgWidgets',
        'PySide6.QtWebSockets', 'PySide6.QtConcurrent',
        'PIL', 'Pillow', 'ssl', '_ssl',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤不需要的 Qt DLL（excludes 只排除 Python 模块，不拦截 DLL）
EXCLUDE_DLLS = {
    'Qt6Network', 'Qt6OpenGL', 'Qt6Pdf', 'Qt6Qml', 'Qt6QmlMeta',
    'Qt6QmlModels', 'Qt6QmlWorkerScript', 'Qt6Quick', 'Qt6Svg',
    'Qt6VirtualKeyboard', 'Qt6WebEngine', 'Qt6ShaderTools',
    'Qt6Quick3D', 'Qt63D', 'Qt6Charts', 'Qt6Graphs', 'Qt6Designer',
    'opengl32sw', 'qtvirtualkeyboardplugin', 'qpdf',
    'qdirect2d', 'qminimal', 'qoffscreen', 'qtuiotouchplugin',
    'qicns', 'qtga', 'qtiff', 'qwbmp',
    'libcrypto', 'libssl',
    '_imaging', '_webp',
}
a.binaries = [
    b for b in a.binaries
    if not any(name in b[0] for name in EXCLUDE_DLLS)
]
a.datas = [
    d for d in a.datas
    if 'translations' not in d[0]
]
a.binaries = [
    b for b in a.binaries
    if not any(name in b[0] for name in EXCLUDE_DLLS)
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KKPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.ico'),
)
