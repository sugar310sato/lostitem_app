"""
パス設定ファイル
アプリケーション全体で使用するパスを一元管理
"""
from pathlib import Path

# プロジェクトのルートディレクトリ
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# データディレクトリ
DATA_DIR = ROOT_DIR / "data"

# データベースディレクトリとファイル
DATABASE_DIR = DATA_DIR / "database"
DB_PATH = DATABASE_DIR / "lostitem.db"

# 画像保存ディレクトリ
IMAGES_DIR = DATA_DIR / "images"
MAIN_IMAGES_DIR = IMAGES_DIR / "main"
SUB_IMAGES_DIR = IMAGES_DIR / "sub"
BUNDLE_IMAGES_DIR = IMAGES_DIR / "bundle"

# ログディレクトリ
LOGS_DIR = DATA_DIR / "logs"
APP_LOG_PATH = LOGS_DIR / "app.log"
ERROR_LOG_PATH = LOGS_DIR / "error.log"

# バックアップディレクトリ
BACKUPS_DIR = DATA_DIR / "backups"
DB_BACKUP_DIR = BACKUPS_DIR / "database"
IMAGE_BACKUP_DIR = BACKUPS_DIR / "images"

# PDFファイルディレクトリ
PDF_DIR = ROOT_DIR / "apps" / "PDFfile"
DISPOSAL_PDF_DIR = PDF_DIR / "disposal_file"
POLICE_PDF_DIR = PDF_DIR / "police_file"
REFUND_PDF_DIR = PDF_DIR / "refund_list_file"
RETURN_ITEM_PDF_DIR = PDF_DIR / "return_item_file"

# 設定ファイルディレクトリ
CONFIG_DIR = DATA_DIR / "config"
USER_SETTINGS_PATH = CONFIG_DIR / "user_settings.json"

# 旧データベースパス（互換性のため）
LEGACY_DB_PATH = ROOT_DIR / "lostitem.db"


def ensure_directories():
    """必要なディレクトリを作成"""
    directories = [
        DATA_DIR,
        DATABASE_DIR,
        IMAGES_DIR,
        MAIN_IMAGES_DIR,
        SUB_IMAGES_DIR,
        BUNDLE_IMAGES_DIR,
        LOGS_DIR,
        BACKUPS_DIR,
        DB_BACKUP_DIR,
        IMAGE_BACKUP_DIR,
        CONFIG_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"データディレクトリを確認・作成しました: {DATA_DIR}")


def get_db_path(use_new_location=True):
    """
    データベースパスを取得
    
    Args:
        use_new_location: Trueの場合は新しい場所、Falseの場合は旧場所
    
    Returns:
        Path: データベースファイルのパス
    """
    if use_new_location:
        # 新しいデータベースが存在しない場合、旧データベースから移行
        if not DB_PATH.exists() and LEGACY_DB_PATH.exists():
            import shutil
            ensure_directories()
            shutil.copy2(LEGACY_DB_PATH, DB_PATH)
            print(f"データベースを移行しました: {LEGACY_DB_PATH} -> {DB_PATH}")
        return DB_PATH
    else:
        return LEGACY_DB_PATH


if __name__ == "__main__":
    # ディレクトリ構造を確認
    ensure_directories()
    print("\n=== パス設定 ===")
    print(f"ルートディレクトリ: {ROOT_DIR}")
    print(f"データディレクトリ: {DATA_DIR}")
    print(f"データベースパス: {DB_PATH}")
    print(f"画像ディレクトリ: {IMAGES_DIR}")
    print(f"ログディレクトリ: {LOGS_DIR}")
    print(f"バックアップディレクトリ: {BACKUPS_DIR}")

