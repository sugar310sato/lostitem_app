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
        
        print("SettingsView.build(): タブオブジェクト作成")
        tabs = ft.Tabs(
            selected_index=self.selected_tab,
            animation_duration=300,
            tabs=[
                general_tab,
                user_management_tab,
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
        # 設定データを取得
        print("build_general_settings: get_general_settings()呼び出し前")
        settings = self.get_general_settings()
        print(f"build_general_settings: 設定取得完了 - {len(settings)}件")
        
        # 施設名設定
        facility_name = ft.TextField(
            label="施設名",
            value=self.current_user.get('store_name', '未設定'),
            width=400,
            hint_text="施設名を入力してください"
        )
        
        # 保管場所設定
        storage_places = self.get_storage_places()
        storage_places_list = ft.Column([], spacing=5, scroll=ft.ScrollMode.AUTO)
        
        def load_storage_places():
            storage_places_list.controls.clear()
            for place in storage_places:
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
            storage_places_list.update()
        
        load_storage_places()
        
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
            find_places_list.update()
        
        load_find_places()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("一般設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # 施設名設定
                ft.Text("施設名", size=16, weight=ft.FontWeight.BOLD),
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
            # build()内ではpage.update()を呼ばない（Fletが自動的に更新）
        
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
    
    def build_facility_settings(self):
        """施設情報設定"""
        settings = self.get_facility_settings()
        
        # 現在の店舗名を取得
        current_store_name = "未設定"
        if self.current_user and self.current_user.get('id'):
            current_store_name = get_user_store_name(self.current_user['id'])
        
        facility_name = ft.TextField(
            label="店舗名",
            value=current_store_name,
            width=400
        )
        
        facility_address = ft.TextField(
            label="住所",
            value=settings.get("facility_address", ""),
            multiline=True,
            min_lines=2,
            width=400
        )
        
        facility_tel = ft.TextField(
            label="電話番号",
            value=settings.get("facility_tel", ""),
            width=300
        )
        
        facility_fax = ft.TextField(
            label="FAX番号",
            value=settings.get("facility_fax", ""),
            width=300
        )
        
        facility_email = ft.TextField(
            label="メールアドレス",
            value=settings.get("facility_email", ""),
            width=400
        )
        
        manager_name = ft.TextField(
            label="担当者名",
            value=settings.get("manager_name", ""),
            width=300
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("施設情報", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                ft.Text("基本情報", size=16, weight=ft.FontWeight.BOLD),
                facility_name,
                facility_address,
                
                ft.Divider(),
                ft.Text("連絡先情報", size=16, weight=ft.FontWeight.BOLD),
                facility_tel,
                facility_fax,
                facility_email,
                
                ft.Divider(),
                ft.Text("担当者情報", size=16, weight=ft.FontWeight.BOLD),
                manager_name,
                
                ft.Container(height=20),
                ft.ElevatedButton(
                    "設定を保存",
                    icon=ft.icons.SAVE,
                    on_click=lambda e: self.save_facility_settings({
                        "facility_name": facility_name.value,
                        "facility_address": facility_address.value,
                        "facility_tel": facility_tel.value,
                        "facility_fax": facility_fax.value,
                        "facility_email": facility_email.value,
                        "manager_name": manager_name.value,
                    }, facility_name.value),
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                )
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True
        )
    
    def build_notification_settings(self):
        """通知設定"""
        settings = self.get_notification_settings()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("通知設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                ft.Text("期限通知", size=16, weight=ft.FontWeight.BOLD),
                ft.Checkbox(
                    label="警察届出期限の通知（7日前）",
                    value=settings.get("notify_police_deadline", True)
                ),
                ft.Checkbox(
                    label="保管期限の通知（3ヶ月前）",
                    value=settings.get("notify_storage_deadline", True)
                ),
                
                ft.Divider(),
                ft.Text("返還通知", size=16, weight=ft.FontWeight.BOLD),
                ft.Checkbox(
                    label="返還時の通知",
                    value=settings.get("notify_return", True)
                ),
                ft.Checkbox(
                    label="拾得者への報労金通知",
                    value=settings.get("notify_reward", False)
                ),
                
                ft.Divider(),
                ft.Text("システム通知", size=16, weight=ft.FontWeight.BOLD),
                ft.Checkbox(
                    label="データベースバックアップ完了通知",
                    value=settings.get("notify_backup", True)
                ),
                ft.Checkbox(
                    label="システムエラー通知",
                    value=settings.get("notify_error", True)
                ),
                
                ft.Container(height=20),
                ft.ElevatedButton(
                    "設定を保存",
                    icon=ft.icons.SAVE,
                    on_click=lambda e: self.save_notification_settings(settings),
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                )
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True
        )
    
    def build_account_settings(self):
        """アカウント設定"""
        return ft.Container(
            content=ft.Column([
                ft.Text("アカウント設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                ft.Text("アカウント情報", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"ユーザー名: {self.current_user.get('username', '未ログイン')}", size=14),
                ft.Text(f"表示名: {self.current_user.get('display_name', '未設定')}", size=14),
                ft.Text(f"権限: {('管理者' if self.current_user.get('role') == 'admin' else '一般ユーザー')}", size=14),
                
                ft.Divider(),
                ft.Text("パスワード変更", size=16, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(
                    "パスワードを変更",
                    icon=ft.icons.LOCK_RESET,
                    on_click=lambda e: self.show_change_password_dialog(),
                    bgcolor=ft.colors.ORANGE_700,
                    color=ft.colors.WHITE
                ),
                
                ft.Divider(),
                ft.Text("表示名変更", size=16, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(
                    "表示名を変更",
                    icon=ft.icons.EDIT,
                    on_click=lambda e: self.show_change_display_name_dialog(),
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True
        )
    
    def build_data_management(self):
        """データ管理"""
        # 管理者権限チェック
        if self.current_user.get("role") != "admin":
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.LOCK, size=60, color=ft.colors.GREY_400),
                    ft.Text("この機能は管理者のみ利用可能です", size=16, color=ft.colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                padding=50,
                alignment=ft.alignment.center,
                expand=True
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("データ管理", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                ft.Text("バックアップ", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("データベースのバックアップを作成します", size=12, color=ft.colors.GREY_700),
                ft.ElevatedButton(
                    "今すぐバックアップ",
                    icon=ft.icons.BACKUP,
                    on_click=lambda e: self.create_backup(),
                    bgcolor=ft.colors.GREEN_700,
                    color=ft.colors.WHITE
                ),
                
                ft.Divider(),
                ft.Text("データベース最適化", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("データベースを最適化してパフォーマンスを向上させます", size=12, color=ft.colors.GREY_700),
                ft.ElevatedButton(
                    "最適化を実行",
                    icon=ft.icons.SPEED,
                    on_click=lambda e: self.optimize_database(),
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                ),
                
                ft.Divider(),
                ft.Text("⚠️ 危険な操作", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED_700),
                ft.Text("以下の操作は取り消せません。実行前に必ずバックアップを作成してください。", 
                       size=12, color=ft.colors.RED_700, weight=ft.FontWeight.BOLD),
                
                ft.Container(height=10),
                ft.ElevatedButton(
                    "古いデータを削除（1年以上前）",
                    icon=ft.icons.DELETE_SWEEP,
                    on_click=lambda e: self.show_delete_old_data_dialog(),
                    bgcolor=ft.colors.ORANGE_700,
                    color=ft.colors.WHITE
                ),
                
                ft.Container(height=10),
                ft.ElevatedButton(
                    "データベースを初期化",
                    icon=ft.icons.RESTORE,
                    on_click=lambda e: self.show_reset_database_dialog(),
                    bgcolor=ft.colors.RED_700,
                    color=ft.colors.WHITE
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
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
        """保管場所リストを取得"""
        try:
            import json
            settings = self.get_general_settings()
            storage_json = settings.get("storage_places", "[]")
            if not storage_json:
                # デフォルトの保管場所を設定
                default_places = ["月～日", "冷蔵庫", "貴重品置き場", "かさ置き場", "小物置き場"]
                self.save_storage_places(default_places)
                return default_places
            return json.loads(storage_json)
        except Exception as e:
            print(f"保管場所リスト取得エラー: {e}")
            return ["月～日", "冷蔵庫", "貴重品置き場", "かさ置き場", "小物置き場"]
    
    def get_find_places(self):
        """拾得場所リストを取得"""
        try:
            import json
            settings = self.get_general_settings()
            find_json = settings.get("find_places", "[]")
            if not find_json:
                # デフォルトの拾得場所を設定
                default_places = ["1階 エントランス", "2階 トイレ前", "3階 会議室前"]
                self.save_find_places(default_places)
                return default_places
            return json.loads(find_json)
        except Exception as e:
            print(f"拾得場所リスト取得エラー: {e}")
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
    
    def get_facility_settings(self):
        """施設情報を取得"""
        settings = self.get_general_settings()
        return {
            "facility_name": settings.get("facility_name", ""),
            "facility_address": settings.get("facility_address", ""),
            "facility_tel": settings.get("facility_tel", ""),
            "facility_fax": settings.get("facility_fax", ""),
            "facility_email": settings.get("facility_email", ""),
            "manager_name": settings.get("manager_name", ""),
        }
    
    def save_facility_settings(self, settings, store_name=None):
        """施設情報を保存"""
        self.save_general_settings(settings)
        
        # 店舗名をデータベースに保存
        if store_name and self.current_user and self.current_user.get('id'):
            if update_user_store_name(self.current_user['id'], store_name):
                print(f"店舗名を更新しました: {store_name}")
            else:
                print("店舗名の更新に失敗しました")
    
    def get_notification_settings(self):
        """通知設定を取得"""
        settings = self.get_general_settings()
        return {
            "notify_police_deadline": settings.get("notify_police_deadline", "True") == "True",
            "notify_storage_deadline": settings.get("notify_storage_deadline", "True") == "True",
            "notify_return": settings.get("notify_return", "True") == "True",
            "notify_reward": settings.get("notify_reward", "False") == "True",
            "notify_backup": settings.get("notify_backup", "True") == "True",
            "notify_error": settings.get("notify_error", "True") == "True",
        }
    
    def save_notification_settings(self, settings):
        """通知設定を保存"""
        self.save_general_settings({
            k: str(v) for k, v in settings.items()
        })
    
    def get_all_users(self):
        """全ユーザーを取得"""
        print("get_all_users: 開始")
        conn = None
        try:
            print(f"get_all_users: DB接続開始 - {DB_PATH}")
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            print("get_all_users: DB接続成功")
            cur = conn.cursor()
            print("get_all_users: SELECT実行前")
            cur.execute("""
                SELECT id, username, display_name, role, last_login
                FROM users
                ORDER BY id
            """)
            print("get_all_users: SELECT実行成功")
            users = []
            for row in cur.fetchall():
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "display_name": row[2],
                    "role": row[3],
                    "last_login": row[4]
                })
            print(f"get_all_users: 取得完了 - {len(users)}件")
            return users
        except Exception as e:
            print(f"ユーザー取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            print("get_all_users: finally節")
            if conn:
                try:
                    conn.close()
                    print("get_all_users: DB接続クローズ完了")
                except Exception as ce:
                    print(f"get_all_users: DB接続クローズエラー: {ce}")
    
    def show_add_user_dialog(self, callback):
        """ユーザー追加ダイアログ"""
        username = ft.TextField(label="ユーザー名", width=300)
        password = ft.TextField(label="パスワード", password=True, can_reveal_password=True, width=300)
        display_name = ft.TextField(label="表示名", width=300)
        role = ft.RadioGroup(
            value="user",
            content=ft.Column([
                ft.Radio(value="user", label="一般ユーザー"),
                ft.Radio(value="admin", label="管理者"),
            ])
        )
        
        error_text = ft.Text("", color=ft.colors.RED)
        
        def add_user(e):
            if not username.value or not password.value:
                error_text.value = "ユーザー名とパスワードは必須です"
                self.page.update()
                return
            
            conn = None
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                
                # テーブル構造を確認
                cur.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cur.fetchall()]
                
                hashed_password = hash_password(password.value)
                
                # password_hashとpasswordの両方のカラムに対応
                if "email" in columns and "password_hash" in columns:
                    cur.execute("""
                        INSERT INTO users (username, password, password_hash, display_name, role, email)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (username.value, hashed_password, hashed_password, display_name.value or username.value, role.value, f"{username.value}@example.com"))
                elif "password_hash" in columns:
                    cur.execute("""
                        INSERT INTO users (username, password, password_hash, display_name, role)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username.value, hashed_password, hashed_password, display_name.value or username.value, role.value))
                elif "email" in columns:
                    cur.execute("""
                        INSERT INTO users (username, password, display_name, role, email)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username.value, hashed_password, display_name.value or username.value, role.value, f"{username.value}@example.com"))
                else:
                    cur.execute("""
                        INSERT INTO users (username, password, display_name, role)
                        VALUES (?, ?, ?, ?)
                    """, (username.value, hashed_password, display_name.value or username.value, role.value))
                
                conn.commit()
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("ユーザーを追加しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except sqlite3.IntegrityError as ie:
                print(f"IntegrityError: {ie}")
                error_text.value = "このユーザー名は既に使用されています"
                self.page.update()
            except Exception as ex:
                print(f"ユーザー追加エラー: {ex}")
                import traceback
                traceback.print_exc()
                error_text.value = f"エラー: {ex}"
                self.page.update()
            finally:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
        
        dlg = ft.AlertDialog(
            title=ft.Text("新規ユーザー追加"),
            content=ft.Container(
                content=ft.Column([
                    username,
                    password,
                    display_name,
                    ft.Text("権限", size=14, weight=ft.FontWeight.BOLD),
                    role,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("追加", on_click=add_user, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_edit_user_dialog(self, user, callback):
        """ユーザー編集ダイアログ"""
        display_name = ft.TextField(label="表示名", value=user["display_name"] or "", width=300)
        role = ft.RadioGroup(
            value=user["role"],
            content=ft.Column([
                ft.Radio(value="user", label="一般ユーザー"),
                ft.Radio(value="admin", label="管理者"),
            ])
        )
        
        def save_user(e):
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                cur.execute("""
                    UPDATE users SET display_name = ?, role = ?
                    WHERE id = ?
                """, (display_name.value, role.value, user["id"]))
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("ユーザー情報を更新しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {ex}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"ユーザー編集: {user['username']}"),
            content=ft.Container(
                content=ft.Column([
                    display_name,
                    ft.Text("権限", size=14, weight=ft.FontWeight.BOLD),
                    role,
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("保存", on_click=save_user, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_delete_user_dialog(self, user, callback):
        """ユーザー削除確認ダイアログ"""
        def delete_user(e):
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE id = ?", (user["id"],))
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("ユーザーを削除しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                
                if callback:
                    callback()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {ex}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("ユーザー削除の確認"),
            content=ft.Text(f"ユーザー「{user['username']}」を削除してもよろしいですか？\nこの操作は取り消せません。"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("削除", on_click=delete_user, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_change_password_dialog(self):
        """パスワード変更ダイアログ"""
        current_password = ft.TextField(label="現在のパスワード", password=True, width=300)
        new_password = ft.TextField(label="新しいパスワード", password=True, can_reveal_password=True, width=300)
        confirm_password = ft.TextField(label="新しいパスワード（確認）", password=True, width=300)
        error_text = ft.Text("", color=ft.colors.RED)
        
        def change_password(e):
            if not current_password.value or not new_password.value or not confirm_password.value:
                error_text.value = "すべての項目を入力してください"
                self.page.update()
                return
            
            if new_password.value != confirm_password.value:
                error_text.value = "新しいパスワードが一致しません"
                self.page.update()
                return
            
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                
                # 現在のパスワード確認
                hashed_current = hash_password(current_password.value)
                cur.execute("SELECT id FROM users WHERE id = ? AND password = ?", 
                          (self.current_user["id"], hashed_current))
                
                if not cur.fetchone():
                    error_text.value = "現在のパスワードが正しくありません"
                    self.page.update()
                    conn.close()
                    return
                
                # パスワード更新（password_hashカラムにも対応）
                hashed_new = hash_password(new_password.value)
                
                # テーブル構造を確認
                cur.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cur.fetchall()]
                
                if "password_hash" in columns:
                    # password_hashカラムがある場合は両方更新
                    cur.execute("UPDATE users SET password = ?, password_hash = ? WHERE id = ?", 
                              (hashed_new, hashed_new, self.current_user["id"]))
                else:
                    # passwordカラムのみ更新
                    cur.execute("UPDATE users SET password = ? WHERE id = ?", 
                              (hashed_new, self.current_user["id"]))
                
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("パスワードを変更しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                error_text.value = f"エラー: {ex}"
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("パスワード変更"),
            content=ft.Container(
                content=ft.Column([
                    current_password,
                    new_password,
                    confirm_password,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("変更", on_click=change_password, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_change_display_name_dialog(self):
        """表示名変更ダイアログ"""
        display_name = ft.TextField(
            label="表示名",
            value=self.current_user.get("display_name", ""),
            width=300
        )
        
        def change_name(e):
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                cur.execute("UPDATE users SET display_name = ? WHERE id = ?", 
                          (display_name.value, self.current_user["id"]))
                conn.commit()
                conn.close()
                
                # 現在のユーザー情報を更新
                self.current_user["display_name"] = display_name.value
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("表示名を変更しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {ex}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("表示名変更"),
            content=display_name,
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("変更", on_click=change_name, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def create_backup(self):
        """バックアップ作成"""
        try:
            import shutil
            backup_dir = Path(__file__).resolve().parent.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"lostitem_backup_{timestamp}.db"
            
            shutil.copy2(DB_PATH, backup_file)
            
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"バックアップを作成しました: {backup_file.name}"),
                    bgcolor=ft.colors.GREEN_700
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"バックアップエラー: {e}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
    
    def optimize_database(self):
        """データベース最適化"""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            conn.execute("VACUUM")
            conn.close()
            
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("データベースを最適化しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"最適化エラー: {e}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
    
    def show_delete_old_data_dialog(self):
        """古いデータ削除確認ダイアログ"""
        dlg = ft.AlertDialog(
            title=ft.Text("古いデータの削除", color=ft.colors.RED_700),
            content=ft.Text("1年以上前のデータを削除します。この操作は取り消せません。\n実行してもよろしいですか？"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("削除", on_click=lambda e: self.delete_old_data(), bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def delete_old_data(self):
        """古いデータを削除"""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            # 1年以上前のデータを削除
            cur.execute("DELETE FROM lost_items WHERE get_item < date('now', '-1 year')")
            deleted_count = cur.rowcount
            
            conn.commit()
            conn.close()
            
            self.page.dialog.open = False
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"{deleted_count}件のデータを削除しました"),
                bgcolor=ft.colors.GREEN_700
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"削除エラー: {e}"), bgcolor=ft.colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
    
    def show_reset_database_dialog(self):
        """データベース初期化確認ダイアログ"""
        confirmation = ft.TextField(label='確認のため「DELETE」と入力してください', width=300)
        error_text = ft.Text("", color=ft.colors.RED)
        
        def reset_db(e):
            if confirmation.value != "DELETE":
                error_text.value = "「DELETE」と正しく入力してください"
                self.page.update()
                return
            
            # この機能は危険なので実装を保留
            error_text.value = "この機能は現在無効化されています"
            self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("⚠️ データベース初期化", color=ft.colors.RED_700),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "警告: すべてのデータが完全に削除されます。\nこの操作は絶対に取り消せません。",
                        color=ft.colors.RED_700,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Divider(),
                    confirmation,
                    error_text
                ], tight=True, spacing=10),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("初期化", on_click=reset_db, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

