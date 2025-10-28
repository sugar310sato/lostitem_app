import flet as ft
import sqlite3
from pathlib import Path

class InitialSetupDialog(ft.UserControl):
    """初回起動時のセットアップダイアログ"""
    
    def __init__(self, on_setup_complete=None):
        super().__init__()
        self.on_setup_complete = on_setup_complete
        self.facility_name = ft.TextField(
            label="施設名",
            hint_text="例: 〇〇ショッピングモール",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            width=400
        )
        self.manager_name = ft.TextField(
            label="管理者名",
            hint_text="例: 田中太郎",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            width=400
        )
        self.username = ft.TextField(
            label="ユーザーID（半角英数字のみ）",
            hint_text="例: admin",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            width=400,
            on_change=lambda e: self._validate_username(e)
        )
        self.username_error = ft.Text("", color=ft.colors.RED, size=12, visible=False)
        self.password = ft.TextField(
            label="パスワード",
            hint_text="管理者用パスワード",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            password=True,
            can_reveal_password=True,
            width=400,
            on_change=lambda e: self._validate_password(e)
        )
        self.password_error = ft.Text("", color=ft.colors.RED, size=12, visible=False)
        
    def build(self):
        # パスワード要件の説明
        password_requirements = ft.Container(
            content=ft.Column([
                ft.Text("パスワード要件:", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                ft.Text("• 6文字以上", size=11, color=ft.colors.GREY_700),
                ft.Text("• 大文字、小文字、数字、記号のうち2種類以上を組み合わせ", size=11, color=ft.colors.GREY_700),
                ft.Text("  例: Abc123 / test@1 / Pass99", size=10, color=ft.colors.GREY_600, italic=True),
            ], spacing=3),
            padding=10,
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.colors.BLUE_200)
        )
        
        return ft.AlertDialog(
            modal=True,
            title=ft.Text("初回セットアップ", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("アプリケーションの初期設定を行います", size=16),
                    ft.Divider(height=20),
                    ft.Text("施設名", size=14, weight=ft.FontWeight.BOLD),
                    self.facility_name,
                    ft.Text("管理者名", size=14, weight=ft.FontWeight.BOLD),
                    self.manager_name,
                    ft.Divider(height=10),
                    ft.Text("新規ログイン設定", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    self.username,
                    self.username_error,
                    self.password,
                    self.password_error,
                    password_requirements,
                    ft.Divider(height=20),
                    ft.Text("※ 管理者アカウントでログイン後、設定画面から詳細な設定が可能です", 
                           size=11, color=ft.colors.GREY_600)
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=650
            ),
            actions=[
                ft.TextButton(
                    "セットアップ開始",
                    on_click=self._start_setup,
                    style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
    
    def _validate_username(self, e):
        """ユーザーIDのバリデーション（半角英数字のみ）"""
        value = e.control.value
        if value:
            # 半角英数字のみかチェック
            if not value.isalnum():
                self.username_error.value = "ユーザーIDは半角英数字のみ使用可能です"
                self.username_error.visible = True
            else:
                self.username_error.visible = False
        else:
            self.username_error.visible = False
        self.update()
    
    def _validate_password(self, e):
        """パスワードのバリデーション"""
        value = e.control.value
        if value:
            # パスワード要件チェック
            if len(value) < 6:
                self.password_error.value = "パスワードは6文字以上である必要があります"
                self.password_error.visible = True
            else:
                # 大文字、小文字、数字、記号のうち2種類以上を使用しているかチェック
                has_upper = any(c.isupper() for c in value)
                has_lower = any(c.islower() for c in value)
                has_digit = any(c.isdigit() for c in value)
                has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value)
                
                types_count = sum([has_upper, has_lower, has_digit, has_special])
                
                if types_count < 2:
                    self.password_error.value = "パスワードには大文字、小文字、数字、記号のうち2種類以上を組み合わせてください"
                    self.password_error.visible = True
                else:
                    self.password_error.visible = False
        else:
            self.password_error.visible = False
        self.update()
    
    def _start_setup(self, e):
        """セットアップを開始"""
        if not self.facility_name.value.strip():
            self.page.snack_bar = ft.SnackBar(ft.Text("施設名を入力してください"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        if not self.manager_name.value.strip():
            self.page.snack_bar = ft.SnackBar(ft.Text("管理者名を入力してください"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        if not self.username.value.strip():
            self.page.snack_bar = ft.SnackBar(ft.Text("ユーザーIDを入力してください"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # ユーザーIDのバリデーション
        if not self.username.value.isalnum():
            self.username_error.value = "ユーザーIDは半角英数字のみ使用可能です"
            self.username_error.visible = True
            self.page.snack_bar = ft.SnackBar(ft.Text("ユーザーIDは半角英数字のみ使用可能です"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        if not self.password.value.strip():
            self.page.snack_bar = ft.SnackBar(ft.Text("パスワードを入力してください"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # パスワード要件チェック
        if len(self.password.value) < 6:
            self.page.snack_bar = ft.SnackBar(ft.Text("パスワードは6文字以上である必要があります"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        has_upper = any(c.isupper() for c in self.password.value)
        has_lower = any(c.islower() for c in self.password.value)
        has_digit = any(c.isdigit() for c in self.password.value)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in self.password.value)
        
        types_count = sum([has_upper, has_lower, has_digit, has_special])
        
        if types_count < 2:
            self.page.snack_bar = ft.SnackBar(ft.Text("パスワードには大文字、小文字、数字、記号のうち2種類以上を組み合わせてください"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        try:
            # データベースに管理者アカウントを作成
            self._create_admin_account()
            
            # 初期設定を保存
            self._save_initial_settings()
            
            # セットアップ完了
            self.page.snack_bar = ft.SnackBar(
                ft.Text("セットアップが完了しました"), 
                bgcolor=ft.colors.GREEN_700
            )
            self.page.snack_bar.open = True
            
            # ダイアログを閉じる
            self.page.dialog.open = False
            self.page.update()
            
            # コールバックを呼び出し
            if self.on_setup_complete:
                self.on_setup_complete({
                    'username': self.username.value,
                    'display_name': self.manager_name.value,
                    'role': 'admin',
                    'store_name': self.facility_name.value
                })
                
        except Exception as ex:
            print(f"セットアップエラー: {ex}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"セットアップエラー: {str(ex)}"), 
                bgcolor=ft.colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _create_admin_account(self):
        """管理者アカウントを作成"""
        db_path = Path(__file__).parent.parent / "lostitem.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # usersテーブルが存在するかチェック
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                store_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # 既存のテーブルにある場合、不足しているカラムを追加
        try:
            cur.execute("PRAGMA table_info(users)")
            columns = {column[1]: column for column in cur.fetchall()}
            
            if 'password' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN password TEXT")
                conn.commit()
                print("passwordカラムを追加しました")
            
            if 'role' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
                conn.commit()
                print("roleカラムを追加しました")
            
            if 'store_name' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN store_name TEXT")
                conn.commit()
                print("store_nameカラムを追加しました")
            
            if 'display_name' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
                conn.commit()
                print("display_nameカラムを追加しました")
            
            if 'created_at' not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
                print("created_atカラムを追加しました")
            
            if 'email' not in columns:
                # emailカラムを追加（オプションなのでNULLを許可）
                cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
                conn.commit()
                print("emailカラムを追加しました")
            
            if 'password_hash' not in columns:
                # password_hashカラムを追加（passwordと同じ値を使用）
                cur.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
                conn.commit()
                print("password_hashカラムを追加しました")
        except Exception as e:
            print(f"カラム追加エラー: {e}")
        
        # 既存の管理者アカウントをチェック（roleカラムが存在する場合のみ）
        try:
            cur.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cur.fetchall()]
            if 'role' in columns:
                cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                admin_count = cur.fetchone()[0]
            else:
                # roleカラムが存在しない場合は0とする
                admin_count = 0
        except Exception as e:
            print(f"管理者アカウントチェックエラー: {e}")
            admin_count = 0
        
        if admin_count == 0:
            # テーブルのカラムを確認
            cur.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cur.fetchall()]
            has_email = 'email' in columns
            has_password_hash = 'password_hash' in columns
            
            # 管理者アカウントを作成
            if has_email and has_password_hash:
                cur.execute("""
                    INSERT INTO users (username, password, password_hash, display_name, role, store_name, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.username.value,
                    self.password.value,
                    self.password.value,  # password_hashも同じパスワードを使用
                    self.manager_name.value,
                    'admin',
                    self.facility_name.value,
                    f"{self.username.value}@example.com"
                ))
            elif has_email:
                cur.execute("""
                    INSERT INTO users (username, password, display_name, role, store_name, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.username.value,
                    self.password.value,
                    self.manager_name.value,
                    'admin',
                    self.facility_name.value,
                    f"{self.username.value}@example.com"
                ))
            elif has_password_hash:
                cur.execute("""
                    INSERT INTO users (username, password, password_hash, display_name, role, store_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.username.value,
                    self.password.value,
                    self.password.value,  # password_hashも同じパスワードを使用
                    self.manager_name.value,
                    'admin',
                    self.facility_name.value
                ))
            else:
                cur.execute("""
                    INSERT INTO users (username, password, display_name, role, store_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.username.value,
                    self.password.value,
                    self.manager_name.value,
                    'admin',
                    self.facility_name.value
                ))
            print("管理者アカウントを作成しました")
        else:
            print("管理者アカウントは既に存在します")
        
        conn.commit()
        conn.close()
    
    def _save_initial_settings(self):
        """初期設定を保存"""
        db_path = Path(__file__).parent.parent / "lostitem.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # settingsテーブルを作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # 既存のテーブルにある場合、不足しているカラムを追加
        try:
            cur.execute("PRAGMA table_info(settings)")
            columns = {column[1]: column for column in cur.fetchall()}
            
            if 'updated_at' not in columns:
                cur.execute("ALTER TABLE settings ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
                print("settings.updated_atカラムを追加しました")
        except Exception as e:
            print(f"カラム追加エラー: {e}")
        
        # 初期設定を保存
        initial_settings = {
            'facility_name': self.facility_name.value,
            'storage_places': '["月～日", "冷蔵庫", "貴重品置き場", "かさ置き場", "小物置き場"]',
            'find_places': '["1階 エントランス", "2階 フードコート", "3階 レストラン街"]',
            'staff_list': '[]'
        }
        
        for key, value in initial_settings.items():
            cur.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
        
        conn.commit()
        conn.close()
        print("初期設定を保存しました")
