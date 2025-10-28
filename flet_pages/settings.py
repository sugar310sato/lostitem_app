import flet as ft
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"


def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_store_name(user_id):
    """ユーザーの店舗名を取得"""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
        cur = conn.cursor()
        # カラムが存在するかチェック
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]
        if 'store_name' not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN store_name TEXT DEFAULT '未設定'")
            conn.commit()
            print("店舗名カラムを追加しました")
        cur.execute("SELECT store_name FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result else "未設定"
    except Exception:
        return "未設定"

def update_user_store_name(user_id, store_name):
    """ユーザーの店舗名を更新"""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
        cur = conn.cursor()
        cur.execute("UPDATE users SET store_name = ? WHERE id = ?", (store_name, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"店舗名更新エラー: {e}")
        return False


class SettingsView(ft.UserControl):
    """設定画面"""
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        self.selected_tab = 0
        print(f"SettingsView.__init__(): current_user = {self.current_user}")
    
    def build(self):
        print("SettingsView.build(): 開始")
        # タブを作成
        print("SettingsView.build(): タブ作成開始")
        
        print("SettingsView.build(): 一般設定タブ作成")
        general_tab = ft.Tab(
            text="一般",
            icon=ft.icons.SETTINGS,
            content=self.build_general_settings()
        )
        
        print("SettingsView.build(): ユーザー管理タブ作成")
        user_management_tab = ft.Tab(
            text="ユーザー管理",
            icon=ft.icons.PEOPLE,
            content=self.build_user_management()
        )
        
        notification_tab = ft.Tab(
                    text="通知",
                    icon=ft.icons.NOTIFICATIONS,
                    content=self.build_notification_settings()
        )
        
        account_tab = ft.Tab(
            text="アカウント設定",
                    icon=ft.icons.ACCOUNT_CIRCLE,
                    content=self.build_account_settings()
        )
        
        data_management_tab = ft.Tab(
                    text="データ管理",
                    icon=ft.icons.STORAGE,
                    content=self.build_data_management()
        )
        
        print("SettingsView.build(): タブオブジェクト作成")
        tabs = ft.Tabs(
            selected_index=self.selected_tab,
            animation_duration=300,
            tabs=[
                general_tab,
                user_management_tab,
                notification_tab,
                account_tab,
                data_management_tab,
            ],
            expand=1,
        )
        
        print("SettingsView.build(): Columnコンテナ作成")
        result = ft.Column([
            ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda e: self.page.go("/"),
                    tooltip="ホームに戻る"
                ),
                ft.Text("設定", size=28, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider(),
            ft.Container(
                content=tabs,
                expand=True,
                padding=10
            )
        ], expand=True, spacing=0)
        
        print("SettingsView.build(): 完了")
        return result
    
    def build_general_settings(self):
        """一般設定"""
        print("build_general_settings: 開始")
        # 管理者権限チェック
        if self.current_user.get("role") != "admin":
            print("build_general_settings: 管理者権限なし")
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.LOCK, size=60, color=ft.colors.GREY_400),
                    ft.Text("この機能は管理者のみ利用可能です", size=16, color=ft.colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                alignment=ft.alignment.center,
                expand=True
            )
        
        # 設定データを取得
        print("build_general_settings: get_general_settings()呼び出し前")
        settings = self.get_general_settings()
        print(f"build_general_settings: 設定取得完了 - {len(settings)}件")
        
        # 施設名設定（データベースから最新の値を取得）
        current_facility_name = settings.get('facility_name', self.current_user.get('store_name', '未設定'))
        facility_name = ft.TextField(
            label="施設名",
            value=current_facility_name,
            width=400,
            hint_text="施設名を入力してください",
            read_only=True
        )
        
        def save_facility_name():
            """施設名を保存"""
            try:
                conn = sqlite3.connect(str(DB_PATH))
                cur = conn.cursor()
                
                # 施設名を設定テーブルに保存
                cur.execute("""
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, ('facility_name', facility_name.value))
                
                # ユーザーテーブルのstore_nameも更新
                cur.execute("""
                    UPDATE users SET store_name = ? WHERE id = ?
                """, (facility_name.value, self.current_user.get('id')))
                
                conn.commit()
                conn.close()
                
                self.page.snack_bar = ft.SnackBar(ft.Text("施設名を保存しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
            except Exception as e:
                print(f"施設名保存エラー: {e}")
                self.page.snack_bar = ft.SnackBar(ft.Text(f"保存エラー: {e}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        def edit_facility_name():
            """施設名を編集モードに切り替え"""
            facility_name.read_only = False
            facility_name.focus()
            self.page.update()
        
        def cancel_edit_facility_name():
            """施設名の編集をキャンセル"""
            facility_name.value = self.current_user.get('store_name', '未設定')
            facility_name.read_only = True
            self.page.update()
        
        # 保管場所設定
        storage_places = self.get_storage_places()
        storage_places_list = ft.Column([], spacing=5, scroll=ft.ScrollMode.AUTO)
        
        def load_storage_places():
            storage_places_list.controls.clear()
            
            # STORAGE_PLACEの項目を取得
            from apps.config import STORAGE_PLACE
            base_places = [item[0] for item in STORAGE_PLACE]
            
            # ベース項目（編集・削除可能）
            for place in base_places:
                storage_places_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(place, size=14, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                icon_size=16,
                                tooltip="編集",
                                on_click=lambda e, p=place: self.show_edit_storage_place_dialog(p, load_storage_places)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_size=16,
                                icon_color=ft.colors.RED_700,
                                tooltip="削除",
                                on_click=lambda e, p=place: self.show_delete_storage_place_dialog(p, load_storage_places)
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=5,
                        bgcolor=ft.colors.WHITE
                    )
                )
            
            # データベースの追加項目（編集・削除可能）
            db_places = [place for place in storage_places if place not in base_places]
            for place in db_places:
                storage_places_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(place, size=14),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                icon_size=16,
                                tooltip="編集",
                                on_click=lambda e, p=place: self.show_edit_storage_place_dialog(p, load_storage_places)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_size=16,
                                icon_color=ft.colors.RED_700,
                                tooltip="削除",
                                on_click=lambda e, p=place: self.show_delete_storage_place_dialog(p, load_storage_places)
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=5,
                        bgcolor=ft.colors.WHITE
                    )
                )
            # ページに追加される前にupdate()を呼ばない
        
        # 拾得場所設定
        find_places = self.get_find_places()
        find_places_list = ft.Column([], spacing=5, scroll=ft.ScrollMode.AUTO)
        
        def load_find_places():
            find_places_list.controls.clear()
            for place in find_places:
                find_places_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(place, size=14),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                icon_size=16,
                                tooltip="編集",
                                on_click=lambda e, p=place: self.show_edit_find_place_dialog(p, load_find_places)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_size=16,
                                icon_color=ft.colors.RED_700,
                                tooltip="削除",
                                on_click=lambda e, p=place: self.show_delete_find_place_dialog(p, load_find_places)
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=5,
                        bgcolor=ft.colors.WHITE
                    )
                )
            # ページに追加される前にupdate()を呼ばない
        
        # データを読み込む
        load_storage_places()
        load_find_places()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("一般設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # 施設名設定
                ft.Row([
                    ft.Text("施設名", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            tooltip="編集",
                            on_click=lambda e: edit_facility_name()
                        ),
                        ft.IconButton(
                            icon=ft.icons.SAVE,
                            tooltip="保存",
                            on_click=lambda e: save_facility_name(),
                            icon_color=ft.colors.GREEN_700
                        ),
                        ft.IconButton(
                            icon=ft.icons.CANCEL,
                            tooltip="キャンセル",
                            on_click=lambda e: cancel_edit_facility_name(),
                            icon_color=ft.colors.RED_700
                        )
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                facility_name,
                
                ft.Divider(),
                
                # 保管場所設定
                ft.Row([
                    ft.Text("保管場所設定", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "新規追加",
                        icon=ft.icons.ADD,
                        on_click=lambda e: self.show_add_storage_place_dialog(load_storage_places),
                        bgcolor=ft.colors.GREEN_700,
                        color=ft.colors.WHITE,
                        height=35
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=storage_places_list,
                    height=200,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    padding=5
                ),
                
                ft.Divider(),
                
                # 拾得場所設定
                ft.Row([
                    ft.Text("拾得場所設定", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "新規追加",
                        icon=ft.icons.ADD,
                        on_click=lambda e: self.show_add_find_place_dialog(load_find_places),
                        bgcolor=ft.colors.GREEN_700,
                        color=ft.colors.WHITE,
                        height=35
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=find_places_list,
                    height=200,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    padding=5
                ),
                
                ft.Container(height=20),
                ft.ElevatedButton(
                    "設定を保存",
                    icon=ft.icons.SAVE,
                    on_click=lambda e: self.save_general_settings({
                        "facility_name": facility_name.value,
                    }),
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                )
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True
        )
    
    def build_user_management(self):
        """ユーザー管理"""
        print("build_user_management: 開始")
        # 管理者権限チェック
        if self.current_user.get("role") != "admin":
            print("build_user_management: 管理者権限なし")
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.LOCK, size=60, color=ft.colors.GREY_400),
                    ft.Text("この機能は管理者のみ利用可能です", size=16, color=ft.colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                padding=50,
                alignment=ft.alignment.center,
                expand=True
            )
        
        print("build_user_management: 管理者権限あり、担当者一覧取得開始")
        # 担当者一覧を取得
        staff_list = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        def load_staff():
            print("load_staff: 開始")
            staff_list.controls.clear()
            print("load_staff: get_staff_list() 呼び出し前")
            staff_members = self.get_staff_list()
            print(f"load_staff: 担当者数 = {len(staff_members)}")
            
            for staff in staff_members:
                staff_card = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.PERSON, size=40, color=ft.colors.BLUE_700),
                        ft.Column([
                            ft.Text(staff, size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("担当者", size=12, color=ft.colors.GREY_700),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                tooltip="編集",
                                on_click=lambda e, s=staff: self.show_edit_staff_dialog(s, load_staff)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                tooltip="削除",
                                icon_color=ft.colors.RED_700,
                                on_click=lambda e, s=staff: self.show_delete_staff_dialog(s, load_staff)
                            ),
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.colors.WHITE
                )
                staff_list.controls.append(staff_card)
            
            print("load_staff: UI構築完了")
        
        print("build_user_management: load_staff()呼び出し前")
        try:
            load_staff()
            print("build_user_management: load_staff()呼び出し完了")
        except Exception as le:
            print(f"build_user_management: load_staff()エラー: {le}")
            import traceback
            traceback.print_exc()
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("担当者管理", size=20, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "新規担当者追加",
                        icon=ft.icons.PERSON_ADD,
                        on_click=lambda e: self.show_add_staff_dialog(load_staff),
                        bgcolor=ft.colors.GREEN_700,
                        color=ft.colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                staff_list,
            ], spacing=10, expand=True),
            padding=20,
            expand=True
        )
    
    def build_notification_settings(self):
        """通知設定"""
        return ft.Container(
            content=ft.Column([
                ft.Text("通知設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("通知機能は今後実装予定です", size=16, color=ft.colors.GREY_600)
            ], spacing=20),
            padding=20,
            expand=True
        )
    
    def build_account_settings(self):
        """アカウント設定"""
        return ft.Container(
            content=ft.Column([
                ft.Text("アカウント設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("アカウント設定機能は今後実装予定です", size=16, color=ft.colors.GREY_600)
            ], spacing=20),
            padding=20,
            expand=True
        )
    
    def build_data_management(self):
        """データ管理"""
        return ft.Container(
            content=ft.Column([
                ft.Text("データ管理", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("データ管理機能は今後実装予定です", size=16, color=ft.colors.GREY_600)
            ], spacing=20),
            padding=20,
            expand=True
        )
    
    # ========================================
    # データベース操作メソッド
    # ========================================
    
    def get_general_settings(self):
        """一般設定を取得"""
        print("get_general_settings: 開始")
        try:
            print(f"get_general_settings: DB接続開始 - {DB_PATH}")
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            print("get_general_settings: DB接続成功")
            cur = conn.cursor()
            
            print("get_general_settings: settingsテーブル作成")
            # settingsテーブルが存在しない場合は作成
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("get_general_settings: settingsテーブル作成完了")
            
            # 既存のテーブルにupdated_atカラムがない場合は追加
            print("get_general_settings: updated_atカラムチェック")
            try:
                cur.execute("SELECT updated_at FROM settings LIMIT 1")
                print("get_general_settings: updated_atカラム存在")
            except sqlite3.OperationalError:
                # カラムが存在しない場合は追加
                print("get_general_settings: updated_atカラム追加")
                cur.execute("ALTER TABLE settings ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
                print("get_general_settings: updated_atカラム追加完了")
            
            # デフォルトの担当者リストを初期化
            print("get_general_settings: staff_listチェック")
            cur.execute("SELECT value FROM settings WHERE key = 'staff_list'")
            result = cur.fetchone()
            if not result:
                # デフォルトの担当者リストを設定
                print("get_general_settings: staff_list初期化")
                import json
                default_staff = ["佐藤", "鈴木", "田中", "高橋"]
                cur.execute("INSERT INTO settings (key, value) VALUES (?, ?)", 
                          ("staff_list", json.dumps(default_staff, ensure_ascii=False)))
                conn.commit()
                print("get_general_settings: staff_list初期化完了")
            else:
                print("get_general_settings: staff_list存在")
            
            print("get_general_settings: 全設定取得")
            settings = {}
            cur.execute("SELECT key, value FROM settings")
            for row in cur.fetchall():
                settings[row[0]] = row[1]
            print(f"get_general_settings: 設定取得完了 - {len(settings)}件")
            
            conn.close()
            print("get_general_settings: DB接続クローズ完了")
            return settings
        except Exception as e:
            print(f"設定取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_staff_list(self):
        """担当者リストを取得"""
        try:
            import json
            settings = self.get_general_settings()
            staff_json = settings.get("staff_list", "[]")
            return json.loads(staff_json)
        except Exception as e:
            print(f"担当者リスト取得エラー: {e}")
            return ["佐藤", "鈴木", "田中", "高橋"]
    
    def get_storage_places(self):
        """保管場所リストを取得（register_form.pyのSTORAGE_PLACEと同期）"""
        try:
            import json
            # register_form.pyのSTORAGE_PLACEから取得
            from apps.config import STORAGE_PLACE
            base_places = [item[0] for item in STORAGE_PLACE]  # タプルの最初の要素を取得
            
            settings = self.get_general_settings()
            storage_json = settings.get("storage_places", "[]")
            if not storage_json:
                # デフォルトの保管場所を設定（STORAGE_PLACEベース）
                self.save_storage_places(base_places)
                return base_places
            
            db_places = json.loads(storage_json)
            # ベースの項目とデータベースの項目をマージ（重複は除く）
            all_places = base_places.copy()
            for place in db_places:
                if place not in all_places:
                    all_places.append(place)
            return all_places
        except Exception as e:
            print(f"保管場所リスト取得エラー: {e}")
            # エラー時はSTORAGE_PLACEベースのリストを返す
            from apps.config import STORAGE_PLACE
            return [item[0] for item in STORAGE_PLACE]
    
    def get_find_places(self):
        """拾得場所リストを取得（register_form.pyの_load_find_placesと同期）"""
        try:
            import json
            import sqlite3
            from pathlib import Path
            DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"
            
            # register_form.pyと同じ方法でデータベースから取得
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            
            # settingsテーブルから拾得場所リストを取得
            cur.execute("SELECT value FROM settings WHERE key = 'find_places'")
            result = cur.fetchone()
            
            if result:
                find_places = json.loads(result[0])
            else:
                # デフォルトの拾得場所リスト
                find_places = ["1階 エントランス", "2階 トイレ前", "3階 会議室前"]
                # デフォルトをデータベースに保存
                self.save_find_places(find_places)
            
            conn.close()
            return find_places
        except Exception as e:
            print(f"拾得場所リスト取得エラー: {e}")
            # エラー時はデフォルトリストを返す
            return ["1階 エントランス", "2階 トイレ前", "3階 会議室前"]
    
    def save_storage_places(self, places):
        """保管場所リストを保存"""
        try:
            import json
            self.save_general_settings({"storage_places": json.dumps(places, ensure_ascii=False)})
        except Exception as e:
            print(f"保管場所保存エラー: {e}")
    
    def save_find_places(self, places):
        """拾得場所リストを保存"""
        try:
            import json
            self.save_general_settings({"find_places": json.dumps(places, ensure_ascii=False)})
        except Exception as e:
            print(f"拾得場所保存エラー: {e}")
    
    def save_general_settings(self, settings):
        """一般設定を保存"""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            for key, value in settings.items():
                cur.execute("""
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value))
            
            conn.commit()
            conn.close()
            
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("設定を保存しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            print(f"設定保存エラー: {e}")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"保存エラー: {e}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
    
    # ========================================
    # 保管場所管理ダイアログ
    # ========================================
    
    def show_add_storage_place_dialog(self, callback):
        """保管場所追加ダイアログ"""
        place_name = ft.TextField(label="保管場所名", width=300, hint_text="例: 貴重品置き場", hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        error_text = ft.Text("", color=ft.colors.RED)
        
        def add_place(e):
            if not place_name.value or not place_name.value.strip():
                error_text.value = "保管場所名を入力してください"
                self.page.update()
                return
            
            try:
                places = self.get_storage_places()
                if place_name.value in places:
                    error_text.value = "この保管場所は既に存在します"
                    self.page.update()
                    return
                
                places.append(place_name.value)
                self.save_storage_places(places)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("保管場所を追加しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                error_text.value = f"エラー: {ex}"
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("保管場所追加"),
            content=ft.Container(
                content=ft.Column([
                    place_name,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("追加", on_click=add_place, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_edit_storage_place_dialog(self, place_name, callback):
        """保管場所編集ダイアログ"""
        new_name = ft.TextField(label="保管場所名", value=place_name, width=300, hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        error_text = ft.Text("", color=ft.colors.RED)
        
        def edit_place(e):
            if not new_name.value or not new_name.value.strip():
                error_text.value = "保管場所名を入力してください"
                self.page.update()
                return
            
            try:
                places = self.get_storage_places()
                if new_name.value != place_name and new_name.value in places:
                    error_text.value = "この保管場所は既に存在します"
                    self.page.update()
                    return
                
                # 名前を更新
                index = places.index(place_name)
                places[index] = new_name.value
                self.save_storage_places(places)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("保管場所を更新しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                error_text.value = f"エラー: {ex}"
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("保管場所編集"),
            content=ft.Container(
                content=ft.Column([
                    new_name,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("更新", on_click=edit_place, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_delete_storage_place_dialog(self, place_name, callback):
        """保管場所削除確認ダイアログ"""
        def delete_place(e):
            try:
                places = self.get_storage_places()
                places.remove(place_name)
                self.save_storage_places(places)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("保管場所を削除しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {ex}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("保管場所削除の確認"),
            content=ft.Text(f"保管場所「{place_name}」を削除してもよろしいですか？"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("削除", on_click=delete_place, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    # ========================================
    # 拾得場所管理ダイアログ
    # ========================================
    
    def show_add_find_place_dialog(self, callback):
        """拾得場所追加ダイアログ"""
        place_name = ft.TextField(label="拾得場所名", width=300, hint_text="例: 2階 トイレ前", hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        error_text = ft.Text("", color=ft.colors.RED)
        
        def add_place(e):
            if not place_name.value or not place_name.value.strip():
                error_text.value = "拾得場所名を入力してください"
                self.page.update()
                return
            
            try:
                places = self.get_find_places()
                if place_name.value in places:
                    error_text.value = "この拾得場所は既に存在します"
                self.page.update()
                return
            
                places.append(place_name.value)
                self.save_find_places(places)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("拾得場所を追加しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                error_text.value = f"エラー: {ex}"
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("拾得場所追加"),
            content=ft.Container(
                content=ft.Column([
                    place_name,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("追加", on_click=add_place, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_edit_find_place_dialog(self, place_name, callback):
        """拾得場所編集ダイアログ"""
        new_name = ft.TextField(label="拾得場所名", value=place_name, width=300, hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        error_text = ft.Text("", color=ft.colors.RED)
        
        def edit_place(e):
            if not new_name.value or not new_name.value.strip():
                error_text.value = "拾得場所名を入力してください"
                self.page.update()
                return
            
            try:
                places = self.get_find_places()
                if new_name.value != place_name and new_name.value in places:
                    error_text.value = "この拾得場所は既に存在します"
                    self.page.update()
                    return
                
                # 名前を更新
                index = places.index(place_name)
                places[index] = new_name.value
                self.save_find_places(places)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("拾得場所を更新しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                error_text.value = f"エラー: {ex}"
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("拾得場所編集"),
            content=ft.Container(
                content=ft.Column([
                    new_name,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("更新", on_click=edit_place, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_delete_find_place_dialog(self, place_name, callback):
        """拾得場所削除確認ダイアログ"""
        def delete_place(e):
            try:
                places = self.get_find_places()
                places.remove(place_name)
                self.save_find_places(places)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("拾得場所を削除しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {ex}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("拾得場所削除の確認"),
            content=ft.Text(f"拾得場所「{place_name}」を削除してもよろしいですか？"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("削除", on_click=delete_place, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    # ========================================
    # 担当者管理ダイアログ
    # ========================================
    
    def show_add_staff_dialog(self, callback):
        """担当者追加ダイアログ"""
        staff_name = ft.TextField(label="担当者名（フルネーム）", width=300, hint_text="例: 田中太郎", hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        error_text = ft.Text("", color=ft.colors.RED)
        
        def add_staff(e):
            if not staff_name.value or not staff_name.value.strip():
                error_text.value = "担当者名を入力してください"
                self.page.update()
                return
            
            try:
                staff_list = self.get_staff_list()
                if staff_name.value in staff_list:
                    error_text.value = "この担当者は既に登録されています"
                    self.page.update()
                    return
                
                staff_list.append(staff_name.value)
                self.save_staff_list(staff_list)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("担当者を追加しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                error_text.value = f"エラー: {ex}"
                self.page.update()
    
        dlg = ft.AlertDialog(
            title=ft.Text("担当者追加"),
            content=ft.Container(
                content=ft.Column([
                    staff_name,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("追加", on_click=add_staff, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_edit_staff_dialog(self, staff_name, callback):
        """担当者編集ダイアログ"""
        new_name = ft.TextField(label="担当者名（フルネーム）", value=staff_name, width=300, hint_style=ft.TextStyle(color=ft.colors.GREY_400))
        error_text = ft.Text("", color=ft.colors.RED)
        
        def edit_staff(e):
            if not new_name.value or not new_name.value.strip():
                error_text.value = "担当者名を入力してください"
                self.page.update()
                return
            
            try:
                staff_list = self.get_staff_list()
                if new_name.value != staff_name and new_name.value in staff_list:
                    error_text.value = "この担当者は既に登録されています"
                    self.page.update()
                    return
                
                # 名前を更新
                index = staff_list.index(staff_name)
                staff_list[index] = new_name.value
                self.save_staff_list(staff_list)
            
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("担当者を更新しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
    
                if callback:
                    callback()
            except Exception as ex:
                error_text.value = f"エラー: {ex}"
            self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("担当者編集"),
            content=ft.Container(
                content=ft.Column([
                    new_name,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("更新", on_click=edit_staff, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_delete_staff_dialog(self, staff_name, callback):
        """担当者削除確認ダイアログ"""
        def delete_staff(e):
            try:
                staff_list = self.get_staff_list()
                staff_list.remove(staff_name)
                self.save_staff_list(staff_list)
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("担当者を削除しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {ex}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("担当者削除の確認"),
            content=ft.Text(f"担当者「{staff_name}」を削除してもよろしいですか？"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("削除", on_click=delete_staff, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def save_staff_list(self, staff_list):
        """担当者リストを保存"""
        try:
            import json
            self.save_general_settings({"staff_list": json.dumps(staff_list, ensure_ascii=False)})
        except Exception as e:
            print(f"担当者リスト保存エラー: {e}")