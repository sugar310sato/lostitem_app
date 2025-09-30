#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """PyInstallerをインストールする"""
    print("PyInstallerをインストールしています...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    print("PyInstallerのインストールが完了しました。")

def create_spec_file():
    """PyInstallerのspecファイルを作成する"""
    # プロジェクトのルートディレクトリを取得
    project_root = Path.cwd()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# プロジェクトのルートディレクトリ
project_root = Path(r"{project_root}")

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[r"{project_root}"],
    binaries=[],
    datas=[
        # 静的ファイル
        (r"{project_root}/apps/static", 'apps/static'),
        # テンプレートファイル
        (r"{project_root}/apps/auth/templates", 'apps/auth/templates'),
        (r"{project_root}/apps/bundleditems/templates", 'apps/bundleditems/templates'),
        (r"{project_root}/apps/crud/templates", 'apps/crud/templates'),
        (r"{project_root}/apps/disposal/templates", 'apps/disposal/templates'),
        (r"{project_root}/apps/items/templates", 'apps/items/templates'),
        (r"{project_root}/apps/notfound/templates", 'apps/notfound/templates'),
        (r"{project_root}/apps/police/templates", 'apps/police/templates'),
        (r"{project_root}/apps/refund/templates", 'apps/refund/templates'),
        (r"{project_root}/apps/register/templates", 'apps/register/templates'),
        (r"{project_root}/apps/return_item/templates", 'apps/return_item/templates'),
        # 画像フォルダ
        (r"{project_root}/apps/images", 'apps/images'),
        (r"{project_root}/apps/renamed_images", 'apps/renamed_images'),
        # モデルファイル
        (r"{project_root}/apps/register/model_folder", 'apps/register/model_folder'),
        # PDFファイルフォルダ
        (r"{project_root}/apps/PDFfile", 'apps/PDFfile'),
        # 設定ファイル
        (r"{project_root}/apps/config.sample", 'apps/config.py'),
        # データベースファイル
        (r"{project_root}/local.sqlite", '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_login',
        'flask_migrate',
        'flask_sqlalchemy',
        'flask_wtf',
        'flask_wtf.csrf',
        'jinja2',
        'werkzeug',
        'sqlalchemy',
        'alembic',
        'wtforms',
        'email_validator',
        'pillow',
        'torch',
        'torchvision',
        'transformers',
        'open_clip',
        'reportlab',
        'googletrans',
        'requests',
        'numpy',
        'tqdm',
        'huggingface_hub',
        'safetensors',
        'tokenizers',
        'sentencepiece',
        'regex',
        'sympy',
        'mpmath',
        'networkx',
        'timm',
        'ftfy',
        'fsspec',
        'filelock',
        'platformdirs',
        'packaging',
        'pathspec',
        'tomli',
        'typing_extensions',
        'mypy_extensions',
        'mypy',
        'mccabe',
        'pycodestyle',
        'pyflakes',
        'flake8',
        'black',
        'isort',
        'colorama',
        'click',
        'blinker',
        'certifi',
        'chardet',
        'charset_normalizer',
        'dnspython',
        'filelock',
        'flask_debugtoolbar',
        'flask_mail',
        'flask_paginate',
        'greenlet',
        'h11',
        'h2',
        'hpack',
        'hstspreload',
        'httpcore',
        'httpx',
        'hyperframe',
        'idna',
        'itsdangerous',
        'mako',
        'markupsafe',
        'pyyaml',
        'rfc3986',
        'sniffio',
        'urllib3',
        'wcwidth',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='遺失物管理システム',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('lostitem_app.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("specファイルが作成されました: lostitem_app.spec")

def build_exe():
    """exeファイルをビルドする"""
    print("exeファイルをビルドしています...")
    
    # PyInstallerでビルド
    result = subprocess.run([
        'pyinstaller',
        '--clean',
        'lostitem_app.spec'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("ビルドが成功しました！")
        print("exeファイルは dist/遺失物管理システム.exe に作成されました。")
    else:
        print("ビルド中にエラーが発生しました:")
        print(result.stderr)
        return False
    
    return True

def create_config_file():
    """設定ファイルを作成する"""
    if not os.path.exists('apps/config.py'):
        shutil.copy('apps/config.sample', 'apps/config.py')
        print("設定ファイルが作成されました: apps/config.py")

def main():
    """メイン関数"""
    print("遺失物管理システムのexeファイルビルドを開始します...")
    
    try:
        # 1. PyInstallerのインストール
        install_pyinstaller()
        
        # 2. 設定ファイルの作成
        create_config_file()
        
        # 3. specファイルの作成
        create_spec_file()
        
        # 4. exeファイルのビルド
        if build_exe():
            print("\n=== ビルド完了 ===")
            print("dist/遺失物管理システム.exe を実行してください。")
            print("初回起動時は少し時間がかかる場合があります。")
        else:
            print("\n=== ビルド失敗 ===")
            print("エラーメッセージを確認して問題を解決してください。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False
    
    return True

if __name__ == '__main__':
    main() 