# データディレクトリ構造

このディレクトリには、アプリケーションのすべてのデータファイルが保存されます。

## ディレクトリ構造

```
data/
├── config/           # 設定ファイル
│   ├── __init__.py
│   ├── paths.py      # パス設定
│   └── user_settings.json  # ユーザー設定
│
├── database/         # データベースファイル
│   └── lostitem.db   # メインデータベース
│
├── images/           # 画像ファイル
│   ├── main/         # メイン画像
│   ├── sub/          # サブ画像
│   └── bundle/       # まとめ画像
│
├── logs/             # ログファイル
│   ├── app.log       # アプリケーションログ
│   └── error.log     # エラーログ
│
└── backups/          # バックアップファイル
    ├── database/     # データベースバックアップ
    └── images/       # 画像バックアップ
```

## パス設定の使用方法

### 基本的な使い方

```python
from data.config import DB_PATH, IMAGES_DIR, ensure_directories

# ディレクトリを確保
ensure_directories()

# データベース接続
import sqlite3
conn = sqlite3.connect(str(DB_PATH))

# 画像保存
image_path = IMAGES_DIR / "main" / "image_001.jpg"
```

### データベースの移行

旧データベース（ルートディレクトリの`lostitem.db`）から新しい場所への自動移行：

```python
from data.config import get_db_path

# 新しい場所を使用（旧データベースがあれば自動移行）
db_path = get_db_path(use_new_location=True)

# 旧場所を使用
db_path = get_db_path(use_new_location=False)
```

## 注意事項

1. **バックアップ**: 定期的にdatabaseディレクトリとimagesディレクトリをバックアップしてください
2. **権限**: データディレクトリには書き込み権限が必要です
3. **移行**: 既存のデータベースは自動的に新しい場所に移行されます
4. **ログ**: ログファイルは定期的にクリーンアップすることをお勧めします

## .gitignore設定

以下のファイルはGit管理から除外することを推奨：

```
data/database/*.db
data/images/**/*
data/logs/**/*
data/backups/**/*
data/config/user_settings.json
```

