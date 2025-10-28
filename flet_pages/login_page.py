import flet as ft
import sqlite3
import hashlib
import sys
from pathlib import Path

# パス設定をインポート
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.config import get_db_path, ensure_directories

# データベースパスを取得（新しい場所を優先、旧場所からの自動移行あり）
DB_PATH = get_db_path(use_new_location=False)  # 一旦、旧場所を使用


def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()


def validate_password(password: str) -> tuple[bool, str]:
    """
    パスワードの強度をチェック
    Returns: (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "パスワードは6文字以上である必要があります"
    
    # 大文字、小文字、数字、記号のうち、2種類以上を使用しているかチェック
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    # 使用している種類をカウント
    types_count = sum([has_upper, has_lower, has_digit, has_special])
    
    if types_count < 2:
        return False, "パスワードには大文字、小文字、数字、記号のうち2種類以上を組み合わせてください"
    
    return True, ""


def verify_user(username: str, password: str) -> dict:
    """ユーザー認証"""
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
        cur = conn.cursor()
        
        # 既存のusersテーブルの構造を確認
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cur.fetchone() is not None
        
        if not table_exists:
            # usersテーブルが存在しない場合は新規作成
            cur.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    display_name TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            conn.commit()
            print("usersテーブルを作成しました")
        else:
            # 既存テーブルのカラムをチェック
            cur.execute("PRAGMA table_info(users)")
            columns = {column[1]: column for column in cur.fetchall()}
            
            # 必要なカラムがない場合は追加
            if "password" not in columns:
                print("passwordカラムを追加します...")
                cur.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT ''")
                conn.commit()
            
            if "role" not in columns:
                print("roleカラムを追加します...")
                cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
                conn.commit()
            
            if "display_name" not in columns:
                print("display_nameカラムを追加します...")
                cur.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
                conn.commit()
            
            if "created_at" not in columns:
                print("created_atカラムを追加します...")
                cur.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
            
            if "last_login" not in columns:
                print("last_loginカラムを追加します...")
                cur.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
                conn.commit()
            
            # emailカラムがある場合、NOT NULL制約を確認
            if "email" in columns:
                # emailカラムがある場合でも、必須でない形に変更
                print("emailカラムが検出されました（互換性のため保持）")
        
        # デフォルト管理者が存在しない場合は作成
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cur.fetchone()[0] == 0:
            default_password = hash_password("Admin1")
            
            # テーブル構造を確認
            cur.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cur.fetchall()]
            
            # password_hashとpasswordの両方のカラムに同じ値を設定
            if "email" in columns and "password_hash" in columns:
                # emailとpassword_hashの両方がある場合
                cur.execute(
                    "INSERT INTO users (username, password, password_hash, display_name, role, email) VALUES (?, ?, ?, ?, ?, ?)",
                    ("admin", default_password, default_password, "管理者", "admin", "admin@example.com")
                )
            elif "password_hash" in columns:
                # password_hashがある場合
                cur.execute(
                    "INSERT INTO users (username, password, password_hash, display_name, role) VALUES (?, ?, ?, ?, ?)",
                    ("admin", default_password, default_password, "管理者", "admin")
                )
            elif "email" in columns:
                # emailのみがある場合
                cur.execute(
                    "INSERT INTO users (username, password, display_name, role, email) VALUES (?, ?, ?, ?, ?)",
                    ("admin", default_password, "管理者", "admin", "admin@example.com")
                )
            else:
                # 基本カラムのみ
                cur.execute(
                    "INSERT INTO users (username, password, display_name, role) VALUES (?, ?, ?, ?)",
                    ("admin", default_password, "管理者", "admin")
                )
            
            conn.commit()
            print("デフォルト管理者を作成しました: username='admin', password='Admin1'")
            print("初回ログイン後、必ずパスワードを変更してください！")
        
        # ユーザー認証
        hashed_password = hash_password(password)
        cur.execute(
            "SELECT id, username, display_name, role FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user = cur.fetchone()
        
        if user:
            # 最終ログイン時刻を更新
            cur.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user[0],)
            )
            conn.commit()
            
            return {
                "id": user[0],
                "username": user[1],
                "display_name": user[2],
                "role": user[3]
            }
        
        return None
        
    except Exception as e:
        print(f"認証エラー: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 必ずデータベース接続をクローズ
        if conn:
            try:
                conn.close()
            except:
                pass


class LoginDialog(ft.UserControl):
    """ログインダイアログ"""
    def __init__(self, on_login_success=None):
        super().__init__()
        self.on_login_success = on_login_success
        self.dialog = None
    
    def build(self):
        self.username_field = ft.TextField(
            label="ユーザー名",
            hint_text="ユーザー名を入力",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            width=300,
            autofocus=True
        )
        
        self.password_field = ft.TextField(
            label="パスワード",
            hint_text="パスワードを入力",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            password=True,
            can_reveal_password=True,
            width=300,
            on_submit=lambda e: self.login()
        )
        
        self.error_text = ft.Text("", color=ft.colors.RED, size=12)
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("ログイン", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("システムを使用するにはログインしてください", size=12, color=ft.colors.GREY_700),
                    ft.Divider(),
                    self.username_field,
                    self.password_field,
                    self.error_text,
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "初回ログイン: ユーザー名「admin」、パスワード「Admin1」",
                                size=10,
                                color=ft.colors.BLUE_700,
                                italic=True
                            ),
                            ft.Text(
                                "⚠️ 初回ログイン後、必ずパスワードを変更してください",
                                size=9,
                                color=ft.colors.RED_700,
                                italic=True,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.TextButton(
                                "新規ユーザー登録",
                                on_click=lambda e: self.show_register_dialog(),
                                style=ft.ButtonStyle(
                                    color=ft.colors.GREEN_700,
                                )
                            )
                        ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.START),
                        padding=ft.padding.only(top=10)
                    )
                ], spacing=10, tight=True),
                width=350,
                padding=20
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=self.cancel),
                ft.ElevatedButton(
                    "ログイン",
                    on_click=lambda e: self.login(),
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        return self.dialog
    
    def login(self):
        """ログイン処理"""
        username = self.username_field.value
        password = self.password_field.value
        
        if not username or not password:
            self.error_text.value = "ユーザー名とパスワードを入力してください"
            if self.page:
                self.page.update()
            return
        
        user = verify_user(username, password)
        
        if user:
            self.error_text.value = ""
            if self.on_login_success and callable(self.on_login_success):
                self.on_login_success(user)
            self.close()
        else:
            self.error_text.value = "ユーザー名またはパスワードが正しくありません"
            if self.page:
                self.page.update()
    
    def cancel(self, e):
        """キャンセル"""
        if self.dialog and self.page:
            self.dialog.open = False
            self.page.update()
    
    def close(self):
        """ダイアログを閉じる"""
        if self.dialog and self.page:
            self.dialog.open = False
            self.page.update()
    
    def show(self):
        """ダイアログを表示"""
        if self.dialog and self.page:
            self.page.dialog = self.dialog
            self.dialog.open = True
            self.page.update()
    
    def show_register_dialog(self):
        """新規ユーザー登録ダイアログを表示"""
        new_username = ft.TextField(label="新しいユーザー名", width=300, hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        new_password = ft.TextField(label="新しいパスワード", password=True, can_reveal_password=True, width=300, hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        new_display_name = ft.TextField(label="表示名", width=300, hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        error_text = ft.Text("", color=ft.colors.RED, size=12)
        
        password_requirements = ft.Container(
            content=ft.Column([
                ft.Text("パスワード要件:", size=11, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                ft.Text("• 6文字以上", size=10, color=ft.colors.GREY_700),
                ft.Text("• 大文字、小文字、数字、記号のうち2種類以上を組み合わせ", size=10, color=ft.colors.GREY_700),
                ft.Text("  例: Abc123 / test@1 / Pass99 など", size=9, color=ft.colors.GREY_600, italic=True),
            ], spacing=3),
            padding=10,
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.colors.BLUE_200)
        )
        
        def register_user(e):
            if not new_username.value or not new_password.value:
                error_text.value = "ユーザー名とパスワードを入力してください"
                if self.page:
                    self.page.update()
                return
            
            # パスワード強度チェック
            is_valid, error_message = validate_password(new_password.value)
            if not is_valid:
                error_text.value = error_message
                if self.page:
                    self.page.update()
                return
            
            conn = None
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                
                # ユーザー名の重複チェック
                cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username.value,))
                if cur.fetchone()[0] > 0:
                    error_text.value = "このユーザー名は既に使用されています"
                    if self.page:
                        self.page.update()
                    return
                
                # ユーザー名の長さチェック
                if len(new_username.value) < 3:
                    error_text.value = "ユーザー名は3文字以上である必要があります"
                    if self.page:
                        self.page.update()
                    return
                
                # テーブル構造を確認
                cur.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cur.fetchall()]
                
                # 新規ユーザーを登録
                hashed_password = hash_password(new_password.value)
                
                # password_hashとpasswordの両方のカラムに同じ値を設定
                if "email" in columns and "password_hash" in columns:
                    # emailとpassword_hashの両方がある場合
                    cur.execute(
                        "INSERT INTO users (username, password, password_hash, display_name, role, email) VALUES (?, ?, ?, ?, ?, ?)",
                        (new_username.value, hashed_password, hashed_password, new_display_name.value or new_username.value, "user", f"{new_username.value}@example.com")
                    )
                elif "password_hash" in columns:
                    # password_hashがある場合
                    cur.execute(
                        "INSERT INTO users (username, password, password_hash, display_name, role) VALUES (?, ?, ?, ?, ?)",
                        (new_username.value, hashed_password, hashed_password, new_display_name.value or new_username.value, "user")
                    )
                elif "email" in columns:
                    # emailのみがある場合
                    cur.execute(
                        "INSERT INTO users (username, password, display_name, role, email) VALUES (?, ?, ?, ?, ?)",
                        (new_username.value, hashed_password, new_display_name.value or new_username.value, "user", f"{new_username.value}@example.com")
                    )
                else:
                    # 基本カラムのみ
                    cur.execute(
                        "INSERT INTO users (username, password, display_name, role) VALUES (?, ?, ?, ?)",
                        (new_username.value, hashed_password, new_display_name.value or new_username.value, "user")
                    )
                
                conn.commit()
                
                # 登録成功
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("ユーザー登録が完了しました。ログインしてください。"),
                        bgcolor=ft.colors.GREEN_700
                    )
                    self.page.snack_bar.open = True
                    self.page.dialog.open = False
                    self.page.update()
                
            except Exception as ex:
                error_text.value = f"登録エラー: {ex}"
                if self.page:
                    self.page.update()
            finally:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
        
        register_dialog = ft.AlertDialog(
            title=ft.Text("新規ユーザー登録"),
            content=ft.Container(
                content=ft.Column([
                    new_username,
                    new_password,
                    new_display_name,
                    password_requirements,
                    error_text
                ], spacing=10, tight=True),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("登録", on_click=register_user, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
            ]
        )
        
        if self.page:
            self.page.dialog = register_dialog
            register_dialog.open = True
            self.page.update()

