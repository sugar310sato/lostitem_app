# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# プロジェクトルート
project_root = Path.cwd()

a = Analysis(
    ['flet_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # データディレクトリ構造
        (str(project_root / 'data' / 'config'), 'data/config'),
        # YOLOモデルファイル
        (str(project_root / 'yolov8x_seg_custom.pt'), '.'),
        (str(project_root / 'yolo11x_seg_custom.pt'), '.'),
        (str(project_root / 'yolov8n.pt'), '.'),
        # 設定ファイル
        (str(project_root / 'item_classification.json'), '.'),
    ],
    hiddenimports=[
        'flet_pages.home',
        'flet_pages.camera_form',
        'flet_pages.register_form',
        'flet_pages.items_list',
        'flet_pages.notfound_list',
        'flet_pages.notfound_management',
        'flet_pages.notfound_registration',
        'flet_pages.refund_management',
        'flet_pages.police_management',
        'flet_pages.search_management',
        'flet_pages.settings',
        'flet_pages.statistics',
        'flet_pages.login_page',
        'flet_pages.initial_setup',
        'data.config.paths',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='flet_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:\\Users\\sato\\AppData\\Local\\Temp\\a66d664f-896c-44b0-879f-452d6fbb3864',
)
