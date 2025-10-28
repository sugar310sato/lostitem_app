#!/usr/bin/env python3
"""
Flask拾得物管理システムの起動スクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 環境変数を設定
os.environ.setdefault('FLASK_APP', 'apps.app:create_app')
os.environ.setdefault('FLASK_ENV', 'development')

from apps.app import create_app

def main():
    """Flaskアプリケーションを起動"""
    print("拾得物管理システム (Flask) を起動しています...")
    print("=" * 50)
    
    # アプリケーションを作成
    app = create_app('local')
    
    # データベースを初期化
    with app.app_context():
        from apps.app import db
        db.create_all()
        print("データベースを初期化しました")
    
    print("=" * 50)
    print("アプリケーションが起動しました")
    print("ブラウザで http://localhost:5000 にアクセスしてください")
    print("終了するには Ctrl+C を押してください")
    print("=" * 50)
    
    # 開発サーバーを起動
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main()
