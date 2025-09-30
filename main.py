#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 環境変数の設定
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'apps.app'

from apps.app import create_app

def main():
    """メインアプリケーションの起動関数"""
    try:
        # アプリケーションの作成
        app = create_app('local')
        
        # 開発サーバーの起動
        print("遺失物管理システムを起動しています...")
        print("ブラウザで http://localhost:5000 にアクセスしてください")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"アプリケーションの起動中にエラーが発生しました: {e}")
        input("Enterキーを押して終了してください...")
        sys.exit(1)

if __name__ == '__main__':
    main() 