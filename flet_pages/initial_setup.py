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
            width=300
        )
        self.manager_name = ft.TextField(
            label="管理者名",
            hint_text="例: 田中太郎",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            width=300
        )
        self.username = ft.TextField(
            label="ユーザー名",
            hint_text="例: admin",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            width=300
        )
        self.password = ft.TextField(
            label="パスワード",
            hint_text="管理者用パスワード",
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
            password=True,
            can_reveal_password=True,
            width=300
        )
        
    def build(self):
        return ft.AlertDialog(
            modal=True,
            title=ft.Text("初回セットアップ", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("アプリケーションの初期設定を行います", size=16),
                    ft.Divider(height=20),
                    self.facility_name,
                    self.manager_name,
                    self.username,
                    self.password,
                    ft.Divider(height=20),
                    ft.Text("※ 管理者アカウントでログイン後、設定画面から詳細な設定が可能です", 
                           size=12, color=ft.colors.GREY_600)
                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=400,
                height=400
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
            self.page.snack_bar = ft.SnackBar(ft.Text("ユーザー名を入力してください"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        if not self.password.value.strip():
            self.page.snack_bar = ft.SnackBar(ft.Text("パスワードを入力してください"), bgcolor=ft.colors.RED_700)
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
        
        # 既存の管理者アカウントをチェック
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cur.fetchone()[0]
        
        if admin_count == 0:
            # 管理者アカウントを作成
            cur.execute("""
                INSERT INTO users (username, password, display_name, role, store_name)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.username.value,
                self.password.value,  # 実際のアプリではハッシュ化が必要
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
