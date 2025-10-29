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
        # 現在の通知設定を取得
        notification_settings = self.get_notification_settings()
        
        # 通知オン/オフスイッチ
        notifications_enabled = ft.Switch(
            label="通知を有効にする",
            value=notification_settings.get("enabled", True),
            on_change=lambda e: self.save_notification_setting("enabled", e.control.value)
        )
        
        # 通知音設定
        sound_enabled = ft.Switch(
            label="通知音を有効にする",
            value=notification_settings.get("sound_enabled", True),
            on_change=lambda e: self.save_notification_setting("sound_enabled", e.control.value)
        )
        
        # 通知音の種類選択
        sound_type = ft.Dropdown(
            label="通知音の種類",
            value=notification_settings.get("sound_type", "default"),
            options=[
                ft.dropdown.Option("default", "デフォルト"),
                ft.dropdown.Option("beep", "ビープ音"),
                ft.dropdown.Option("chime", "チャイム"),
                ft.dropdown.Option("bell", "ベル")
            ],
            width=200,
            on_change=lambda e: self.save_notification_setting("sound_type", e.control.value)
        )
        
        # 通知表示時間
        display_duration = ft.Dropdown(
            label="通知表示時間",
            value=str(notification_settings.get("display_duration", 5)),
            options=[
                ft.dropdown.Option("3", "3秒"),
                ft.dropdown.Option("5", "5秒"),
                ft.dropdown.Option("10", "10秒"),
                ft.dropdown.Option("15", "15秒")
            ],
            width=150,
            on_change=lambda e: self.save_notification_setting("display_duration", int(e.control.value))
        )
        
        # デスクトップ通知
        desktop_notifications = ft.Switch(
            label="デスクトップ通知を有効にする",
            value=notification_settings.get("desktop_enabled", False),
            on_change=lambda e: self.save_notification_setting("desktop_enabled", e.control.value)
        )
        
        # 通知条件設定
        notify_new_item = ft.Switch(
            label="新規アイテム登録時に通知",
            value=notification_settings.get("notify_new_item", True),
            on_change=lambda e: self.save_notification_setting("notify_new_item", e.control.value)
        )
        
        notify_return = ft.Switch(
            label="アイテム返却時に通知", 
            value=notification_settings.get("notify_return", True),
            on_change=lambda e: self.save_notification_setting("notify_return", e.control.value)
        )
        
        notify_disposal = ft.Switch(
            label="アイテム処分時に通知",
            value=notification_settings.get("notify_disposal", True),
            on_change=lambda e: self.save_notification_setting("notify_disposal", e.control.value)
        )
        
        # テスト通知ボタン
        def test_notification(e):
            self.show_test_notification()
        
        test_button = ft.ElevatedButton(
            "テスト通知を表示",
            icon=ft.icons.NOTIFICATIONS_ACTIVE,
            on_click=test_notification,
            bgcolor=ft.colors.BLUE_700,
            color=ft.colors.WHITE
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("通知設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # 基本設定
                ft.Container(
                    content=ft.Column([
                        ft.Text("基本設定", size=16, weight=ft.FontWeight.BOLD),
                        notifications_enabled,
                        sound_enabled,
                        ft.Row([sound_type], visible=sound_enabled.value),
                        ft.Row([display_duration]),
                        desktop_notifications,
                    ], spacing=15),
                    padding=ft.padding.all(15),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.colors.GREY_50
                ),
                
                ft.Container(height=20),
                
                # 通知条件設定
                ft.Container(
                    content=ft.Column([
                        ft.Text("通知条件", size=16, weight=ft.FontWeight.BOLD),
                        notify_new_item,
                        notify_return,
                        notify_disposal,
                    ], spacing=15),
                    padding=ft.padding.all(15),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.colors.GREY_50
                ),
                
                ft.Container(height=20),
                
                # テスト機能
                ft.Container(
                    content=ft.Column([
                        ft.Text("テスト機能", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([test_button]),
                    ], spacing=15),
                    padding=ft.padding.all(15),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.colors.GREY_50
                ),
                
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True
        )
    
    def build_account_settings(self):
        """アカウント設定"""
        # 現在のユーザー情報
        user_info = ft.Column([
            ft.Text("現在のアカウント情報", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.PERSON, size=40, color=ft.colors.BLUE_700),
                        ft.Column([
                            ft.Text(f"ユーザー名: {self.current_user.get('username', '不明')}", size=14),
                            ft.Text(f"権限: {'管理者' if self.current_user.get('role') == 'admin' else '一般ユーザー'}", size=14),
                            ft.Text(f"店舗名: {self.current_user.get('store_name', '未設定')}", size=14),
                        ], spacing=5),
                    ]),
                ], spacing=10),
                padding=15,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                bgcolor=ft.colors.WHITE
            )
        ], spacing=15)
        
        # ユーザー名変更セクション
        username_field = ft.TextField(
            label="新しいユーザー名",
            width=300,
            hint_text="新しいユーザー名を入力",
            read_only=True
        )
        
        def edit_username():
            username_field.value = self.current_user.get('username', '')
            username_field.read_only = False
            username_field.focus()
            self.page.update()
        
        def save_username():
            if not username_field.value or not username_field.value.strip():
                self.page.snack_bar = ft.SnackBar(ft.Text("ユーザー名を入力してください"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            if self.update_username(username_field.value.strip()):
                username_field.read_only = True
                self.current_user['username'] = username_field.value.strip()
                self.page.snack_bar = ft.SnackBar(ft.Text("ユーザー名を更新しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                # 情報表示を更新
                self.page.go("/settings")
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("ユーザー名の更新に失敗しました"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        def cancel_username_edit():
            username_field.value = ""
            username_field.read_only = True
            self.page.update()
        
        username_section = ft.Column([
            ft.Text("ユーザー名変更", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    username_field,
                    ft.Row([
                        ft.ElevatedButton(
                            "編集",
                            icon=ft.icons.EDIT,
                            on_click=lambda e: edit_username(),
                            bgcolor=ft.colors.BLUE_700,
                            color=ft.colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "保存",
                            icon=ft.icons.SAVE,
                            on_click=lambda e: save_username(),
                            bgcolor=ft.colors.GREEN_700,
                            color=ft.colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "キャンセル",
                            icon=ft.icons.CANCEL,
                            on_click=lambda e: cancel_username_edit(),
                            bgcolor=ft.colors.GREY_700,
                            color=ft.colors.WHITE
                        ),
                    ], spacing=10),
                ], spacing=15),
                padding=15,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                bgcolor=ft.colors.GREY_50
            )
        ], spacing=15)
        
        # パスワード変更セクション
        current_password = ft.TextField(
            label="現在のパスワード",
            width=300,
            password=True,
            can_reveal_password=True
        )
        new_password = ft.TextField(
            label="新しいパスワード",
            width=300,
            password=True,
            can_reveal_password=True,
            hint_text="8文字以上で入力してください"
        )
        confirm_password = ft.TextField(
            label="新しいパスワード（確認）",
            width=300,
            password=True,
            can_reveal_password=True
        )
        
        def change_password():
            if not all([current_password.value, new_password.value, confirm_password.value]):
                self.page.snack_bar = ft.SnackBar(ft.Text("すべてのフィールドを入力してください"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            if len(new_password.value) < 8:
                self.page.snack_bar = ft.SnackBar(ft.Text("新しいパスワードは8文字以上で入力してください"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            if new_password.value != confirm_password.value:
                self.page.snack_bar = ft.SnackBar(ft.Text("新しいパスワードが一致しません"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            if self.update_password(current_password.value, new_password.value):
                current_password.value = ""
                new_password.value = ""
                confirm_password.value = ""
                self.page.snack_bar = ft.SnackBar(ft.Text("パスワードを変更しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("現在のパスワードが正しくありません"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
        
        password_section = ft.Column([
            ft.Text("パスワード変更", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    current_password,
                    new_password,
                    confirm_password,
                    ft.ElevatedButton(
                        "パスワードを変更",
                        icon=ft.icons.LOCK_RESET,
                        on_click=lambda e: change_password(),
                        bgcolor=ft.colors.ORANGE_700,
                        color=ft.colors.WHITE
                    ),
                ], spacing=15),
                padding=15,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                bgcolor=ft.colors.GREY_50
            )
        ], spacing=15)
        
        # ログアウトセクション
        def logout():
            # ログアウト確認ダイアログ
            def confirm_logout(e):
                self.page.dialog.open = False
                self.page.update()
                # ログイン画面に戻る
                self.page.go("/login")
            
            dlg = ft.AlertDialog(
                title=ft.Text("ログアウト確認"),
                content=ft.Text("ログアウトしてもよろしいですか？"),
                actions=[
                    ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                    ft.ElevatedButton("ログアウト", on_click=confirm_logout, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
                ]
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
        
        logout_section = ft.Column([
            ft.Text("アカウント操作", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    ft.ElevatedButton(
                        "ログアウト",
                        icon=ft.icons.LOGOUT,
                        on_click=lambda e: logout(),
                        bgcolor=ft.colors.RED_700,
                        color=ft.colors.WHITE,
                        width=200
                    ),
                ], spacing=15),
                padding=15,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                bgcolor=ft.colors.GREY_50
            )
        ], spacing=15)
        
        return ft.Container(
            content=ft.Column([
                ft.Text("アカウント設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                user_info,
                ft.Container(height=20),
                username_section,
                ft.Container(height=20),
                password_section,
                ft.Container(height=20),
                logout_section,
                
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
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                alignment=ft.alignment.center,
                expand=True
            )
        
        # データベース情報の表示
        db_info = self.get_database_info()
        info_section = ft.Container(
            content=ft.Column([
                ft.Text("データベース情報", size=16, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Text(f"拾得物件数: {db_info.get('items_count', 0):,}件", size=14),
                    ft.Text(f"ユーザー数: {db_info.get('users_count', 0):,}人", size=14),
                    ft.Text(f"データベースサイズ: {db_info.get('db_size', 0):.2f} MB", size=14),
                    ft.Text(f"最終更新: {db_info.get('last_updated', '不明')}", size=14),
                ], spacing=5),
            ], spacing=15),
            padding=15,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
            bgcolor=ft.colors.WHITE
        )
        
        # バックアップセクション
        backup_section = ft.Container(
            content=ft.Column([
                ft.Text("データバックアップ", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("データベース全体をバックアップします", size=12, color=ft.colors.GREY_600),
                ft.Row([
                    ft.ElevatedButton(
                        "バックアップ作成",
                        icon=ft.icons.BACKUP,
                        on_click=lambda e: self.create_backup(),
                        bgcolor=ft.colors.GREEN_700,
                        color=ft.colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "バックアップから復元",
                        icon=ft.icons.RESTORE,
                        on_click=lambda e: self.show_restore_dialog(),
                        bgcolor=ft.colors.BLUE_700,
                        color=ft.colors.WHITE
                    ),
                ], spacing=10),
            ], spacing=15),
            padding=15,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
            bgcolor=ft.colors.GREY_50
        )
        
        # データエクスポートセクション
        export_section = ft.Container(
            content=ft.Column([
                ft.Text("データエクスポート", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("データをCSV形式でエクスポートします", size=12, color=ft.colors.GREY_600),
                ft.Row([
                    ft.ElevatedButton(
                        "拾得物データエクスポート",
                        icon=ft.icons.DOWNLOAD,
                        on_click=lambda e: self.export_items_data(),
                        bgcolor=ft.colors.PURPLE_700,
                        color=ft.colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "ユーザーデータエクスポート",
                        icon=ft.icons.DOWNLOAD,
                        on_click=lambda e: self.export_users_data(),
                        bgcolor=ft.colors.PURPLE_700,
                        color=ft.colors.WHITE
                    ),
                ], spacing=10),
            ], spacing=15),
            padding=15,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
            bgcolor=ft.colors.GREY_50
        )
        
        # データインポートセクション
        import_section = ft.Container(
            content=ft.Column([
                ft.Text("データインポート", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("CSV形式のデータをインポートします", size=12, color=ft.colors.GREY_600),
                ft.Text("※既存データに追加されます", size=10, color=ft.colors.ORANGE_700),
                ft.Row([
                    ft.ElevatedButton(
                        "拾得物データインポート",
                        icon=ft.icons.UPLOAD,
                        on_click=lambda e: self.show_import_items_dialog(),
                        bgcolor=ft.colors.ORANGE_700,
                        color=ft.colors.WHITE
                    ),
                ], spacing=10),
            ], spacing=15),
            padding=15,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
            bgcolor=ft.colors.GREY_50
        )
        
        # データ削除セクション（危険エリア）
        delete_section = ft.Container(
            content=ft.Column([
                ft.Text("危険エリア", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED_700),
                ft.Text("以下の操作は元に戻せません", size=12, color=ft.colors.RED_600),
                ft.Row([
                    ft.ElevatedButton(
                        "古いデータを削除",
                        icon=ft.icons.DELETE_SWEEP,
                        on_click=lambda e: self.show_delete_old_data_dialog(),
                        bgcolor=ft.colors.ORANGE_700,
                        color=ft.colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "全データ初期化",
                        icon=ft.icons.DELETE_FOREVER,
                        on_click=lambda e: self.show_reset_database_dialog(),
                        bgcolor=ft.colors.RED_700,
                        color=ft.colors.WHITE
                    ),
                ], spacing=10),
            ], spacing=15),
            padding=15,
            border=ft.border.all(2, ft.colors.RED_300),
            border_radius=8,
            bgcolor=ft.colors.RED_50
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("データ管理", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                info_section,
                ft.Container(height=20),
                backup_section,
                ft.Container(height=20),
                export_section,
                ft.Container(height=20),
                import_section,
                ft.Container(height=20),
                delete_section,
                
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
            
            # 設定画面を更新して即座に反映
            if self.page:
                self.page.go("/settings")
        except Exception as e:
            print(f"保管場所保存エラー: {e}")
    
    def save_find_places(self, places):
        """拾得場所リストを保存"""
        try:
            import json
            self.save_general_settings({"find_places": json.dumps(places, ensure_ascii=False)})
            
            # 設定画面を更新して即座に反映
            if self.page:
                self.page.go("/settings")
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
            
            # 設定画面を更新して即座に反映
            if self.page:
                self.page.go("/settings")
        except Exception as e:
            print(f"担当者リスト保存エラー: {e}")
    
    # ========================================
    # 通知設定メソッド
    # ========================================
    
    def get_notification_settings(self):
        """通知設定を取得"""
        try:
            settings = self.get_general_settings()
            import json
            
            # デフォルトの通知設定
            default_settings = {
                "enabled": True,
                "sound_enabled": True,
                "sound_type": "default",
                "display_duration": 5,
                "desktop_enabled": False,
                "notify_new_item": True,
                "notify_return": True,
                "notify_disposal": True
            }
            
            notification_json = settings.get("notification_settings", "")
            if notification_json:
                try:
                    notification_settings = json.loads(notification_json)
                    # デフォルト設定とマージ
                    for key, value in default_settings.items():
                        if key not in notification_settings:
                            notification_settings[key] = value
                    return notification_settings
                except json.JSONDecodeError:
                    pass
            
            return default_settings
        except Exception as e:
            print(f"通知設定取得エラー: {e}")
            return {
                "enabled": True,
                "sound_enabled": True,
                "sound_type": "default",
                "display_duration": 5,
                "desktop_enabled": False,
                "notify_new_item": True,
                "notify_return": True,
                "notify_disposal": True
            }
    
    def save_notification_setting(self, key, value):
        """個別の通知設定を保存"""
        try:
            current_settings = self.get_notification_settings()
            current_settings[key] = value
            
            import json
            self.save_general_settings({
                "notification_settings": json.dumps(current_settings, ensure_ascii=False)
            })
            
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("通知設定を保存しました"), bgcolor=ft.colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            print(f"通知設定保存エラー: {e}")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"保存エラー: {e}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
    
    def show_test_notification(self):
        """テスト通知を表示"""
        try:
            notification_settings = self.get_notification_settings()
            
            if notification_settings.get("enabled", True):
                # 通知音が有効な場合
                if notification_settings.get("sound_enabled", True):
                    sound_type = notification_settings.get("sound_type", "default")
                    # 実際の通知音再生（プラットフォーム依存）
                    try:
                        import winsound
                        if sound_type == "beep":
                            winsound.MessageBeep(winsound.MB_OK)
                        elif sound_type == "chime":
                            winsound.MessageBeep(winsound.MB_ICONASTERISK)
                        elif sound_type == "bell":
                            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                        else:
                            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                    except ImportError:
                        # winsoundが利用できない場合は無視
                        pass
                
                # 通知メッセージの表示
                display_duration = notification_settings.get("display_duration", 5)
                self.page.snack_bar = ft.SnackBar(
                    ft.Row([
                        ft.Icon(ft.icons.NOTIFICATIONS_ACTIVE, color=ft.colors.WHITE),
                        ft.Text("これはテスト通知です", color=ft.colors.WHITE),
                    ]),
                    bgcolor=ft.colors.BLUE_700,
                    duration=display_duration * 1000
                )
                self.page.snack_bar.open = True
                self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("通知が無効になっています", color=ft.colors.WHITE),
                    bgcolor=ft.colors.ORANGE_700
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            print(f"テスト通知エラー: {e}")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"通知エラー: {e}"), bgcolor=ft.colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
    
    # ========================================
    # アカウント設定メソッド
    # ========================================
    
    def update_username(self, new_username):
        """ユーザー名を更新"""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            # 同じユーザー名が既に存在するかチェック
            cur.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, self.current_user.get('id')))
            if cur.fetchone():
                conn.close()
                return False
            
            # ユーザー名を更新
            cur.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, self.current_user.get('id')))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"ユーザー名更新エラー: {e}")
            return False
    
    def update_password(self, current_password, new_password):
        """パスワードを更新"""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            # 現在のパスワードを確認
            current_password_hash = hash_password(current_password)
            cur.execute("SELECT id FROM users WHERE id = ? AND password = ?", 
                       (self.current_user.get('id'), current_password_hash))
            if not cur.fetchone():
                conn.close()
                return False
            
            # 新しいパスワードをハッシュ化して更新
            new_password_hash = hash_password(new_password)
            cur.execute("UPDATE users SET password = ? WHERE id = ?", 
                       (new_password_hash, self.current_user.get('id')))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"パスワード更新エラー: {e}")
            return False
    
    # ========================================
    # データ管理メソッド
    # ========================================
    
    def get_database_info(self):
        """データベース情報を取得"""
        try:
            import os
            from datetime import datetime
            
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            # 拾得物件数を取得
            cur.execute("SELECT COUNT(*) FROM items")
            items_count = cur.fetchone()[0]
            
            # ユーザー数を取得
            cur.execute("SELECT COUNT(*) FROM users")
            users_count = cur.fetchone()[0]
            
            # データベースファイルサイズを取得
            db_size = os.path.getsize(str(DB_PATH)) / (1024 * 1024)  # MB
            
            # 最終更新日時を取得（itemsテーブルから）
            cur.execute("SELECT MAX(received_date) FROM items")
            last_updated_result = cur.fetchone()
            last_updated = last_updated_result[0] if last_updated_result[0] else "不明"
            
            conn.close()
            
            return {
                "items_count": items_count,
                "users_count": users_count,
                "db_size": db_size,
                "last_updated": last_updated
            }
        except Exception as e:
            print(f"データベース情報取得エラー: {e}")
            return {
                "items_count": 0,
                "users_count": 0,
                "db_size": 0,
                "last_updated": "不明"
            }
    
    def create_backup(self):
        """データベースバックアップを作成"""
        try:
            import shutil
            from datetime import datetime
            from pathlib import Path
            
            # バックアップフォルダを作成
            backup_dir = Path(__file__).resolve().parent.parent / "data" / "backups" / "database"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # バックアップファイル名を生成（日時付き）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"lostitem_backup_{timestamp}.db"
            
            # データベースファイルをコピー
            shutil.copy2(str(DB_PATH), str(backup_file))
            
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"バックアップを作成しました: {backup_file.name}"),
                bgcolor=ft.colors.GREEN_700
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            print(f"バックアップ作成エラー: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"バックアップ作成エラー: {e}"),
                bgcolor=ft.colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def export_items_data(self):
        """拾得物データをCSVエクスポート"""
        try:
            import csv
            from datetime import datetime
            from pathlib import Path
            
            # エクスポートフォルダを作成
            export_dir = Path(__file__).resolve().parent.parent / "data" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # CSVファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = export_dir / f"items_export_{timestamp}.csv"
            
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            # 拾得物データを取得
            cur.execute("""
                SELECT 
                    item_number, category, subcategory, description, color,
                    brand, material, size_info, find_location, storage_location,
                    finder_name, received_date, staff_name, status, notes
                FROM items
                ORDER BY received_date DESC
            """)
            
            items = cur.fetchall()
            
            # CSVファイルに書き込み
            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # ヘッダー行
                writer.writerow([
                    '拾得番号', 'カテゴリ', 'サブカテゴリ', '詳細説明', '色',
                    'ブランド', '素材', 'サイズ情報', '拾得場所', '保管場所',
                    '拾得者名', '受付日時', '担当者', 'ステータス', '備考'
                ])
                # データ行
                writer.writerows(items)
            
            conn.close()
            
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"拾得物データをエクスポートしました: {csv_file.name}"),
                bgcolor=ft.colors.GREEN_700
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            print(f"エクスポートエラー: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"エクスポートエラー: {e}"),
                bgcolor=ft.colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def export_users_data(self):
        """ユーザーデータをCSVエクスポート"""
        try:
            import csv
            from datetime import datetime
            from pathlib import Path
            
            # エクスポートフォルダを作成
            export_dir = Path(__file__).resolve().parent.parent / "data" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # CSVファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = export_dir / f"users_export_{timestamp}.csv"
            
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            # ユーザーデータを取得（パスワードは除外）
            cur.execute("""
                SELECT 
                    id, username, role, store_name, created_at
                FROM users
                ORDER BY created_at
            """)
            
            users = cur.fetchall()
            
            # CSVファイルに書き込み
            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # ヘッダー行
                writer.writerow(['ID', 'ユーザー名', '権限', '店舗名', '作成日時'])
                # データ行
                writer.writerows(users)
            
            conn.close()
            
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"ユーザーデータをエクスポートしました: {csv_file.name}"),
                bgcolor=ft.colors.GREEN_700
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            print(f"エクスポートエラー: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"エクスポートエラー: {e}"),
                bgcolor=ft.colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def show_delete_old_data_dialog(self):
        """古いデータ削除ダイアログ"""
        months_dropdown = ft.Dropdown(
            label="削除対象期間",
            value="12",
            options=[
                ft.dropdown.Option("6", "6ヶ月より古いデータ"),
                ft.dropdown.Option("12", "1年より古いデータ"),
                ft.dropdown.Option("24", "2年より古いデータ"),
                ft.dropdown.Option("36", "3年より古いデータ"),
            ],
            width=250
        )
        
        def delete_old_data(e):
            try:
                months = int(months_dropdown.value)
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                
                # 削除対象のデータ数を確認
                cur.execute("""
                    SELECT COUNT(*) FROM items 
                    WHERE received_date < datetime('now', '-{} months')
                """.format(months))
                count = cur.fetchone()[0]
                
                if count == 0:
                    self.page.dialog.open = False
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("削除対象のデータはありません"),
                        bgcolor=ft.colors.ORANGE_700
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return
                
                # 古いデータを削除
                cur.execute("""
                    DELETE FROM items 
                    WHERE received_date < datetime('now', '-{} months')
                """.format(months))
                
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"{count}件の古いデータを削除しました"),
                    bgcolor=ft.colors.GREEN_700
                )
                self.page.snack_bar.open = True
                self.page.update()
                
            except Exception as ex:
                print(f"古いデータ削除エラー: {ex}")
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"削除エラー: {ex}"),
                    bgcolor=ft.colors.RED_700
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("古いデータの削除"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("指定した期間より古いデータを削除します。", size=14),
                    ft.Text("この操作は元に戻せません。", size=12, color=ft.colors.RED_600),
                    months_dropdown,
                ], tight=True, spacing=15),
                width=350
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("削除実行", on_click=delete_old_data, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_reset_database_dialog(self):
        """データベース初期化確認ダイアログ"""
        confirmation_field = ft.TextField(
            label="確認のため「RESET」と入力してください",
            width=300
        )
        
        def reset_database(e):
            if confirmation_field.value != "RESET":
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("確認文字列が正しくありません"),
                    bgcolor=ft.colors.RED_700
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                
                # 全テーブルのデータを削除（構造は残す）
                cur.execute("DELETE FROM items")
                cur.execute("DELETE FROM settings WHERE key != 'facility_name'")  # 施設名は保持
                # ユーザーテーブルは管理者アカウント以外を削除
                cur.execute("DELETE FROM users WHERE role != 'admin' OR id != ?", (self.current_user.get('id'),))
                
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("データベースを初期化しました"),
                    bgcolor=ft.colors.GREEN_700
                )
                self.page.snack_bar.open = True
                self.page.update()
                
            except Exception as ex:
                print(f"データベース初期化エラー: {ex}")
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"初期化エラー: {ex}"),
                    bgcolor=ft.colors.RED_700
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("データベース初期化"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("全てのデータが削除されます！", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED_700),
                    ft.Text("この操作は元に戻せません。", size=14, color=ft.colors.RED_600),
                    ft.Text("現在のユーザーアカウントと施設名のみ保持されます。", size=12, color=ft.colors.GREY_600),
                    confirmation_field,
                ], tight=True, spacing=15),
                width=400
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("初期化実行", on_click=reset_database, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_restore_dialog(self):
        """バックアップ復元ダイアログ"""
        try:
            from pathlib import Path
            
            # バックアップフォルダからファイル一覧を取得
            backup_dir = Path(__file__).resolve().parent.parent / "data" / "backups" / "database"
            backup_files = []
            
            if backup_dir.exists():
                backup_files = [f.name for f in backup_dir.glob("*.db") if f.is_file()]
                backup_files.sort(reverse=True)  # 新しい順
            
            if not backup_files:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("バックアップファイルが見つかりません"),
                    bgcolor=ft.colors.ORANGE_700
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            backup_dropdown = ft.Dropdown(
                label="復元するバックアップファイル",
                options=[ft.dropdown.Option(f, f) for f in backup_files],
                value=backup_files[0] if backup_files else None,
                width=400
            )
            
            def restore_backup(e):
                if not backup_dropdown.value:
                    return
                
                try:
                    import shutil
                    
                    backup_file = backup_dir / backup_dropdown.value
                    
                    # 現在のデータベースをバックアップ
                    current_backup = backup_dir / f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    shutil.copy2(str(DB_PATH), str(current_backup))
                    
                    # バックアップから復元
                    shutil.copy2(str(backup_file), str(DB_PATH))
                    
                    self.page.dialog.open = False
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"バックアップから復元しました: {backup_dropdown.value}"),
                        bgcolor=ft.colors.GREEN_700
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    
                    # アプリケーションの再起動を推奨
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("復元完了。アプリケーションを再起動してください。"),
                        bgcolor=ft.colors.BLUE_700
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    
                except Exception as ex:
                    print(f"復元エラー: {ex}")
                    self.page.dialog.open = False
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"復元エラー: {ex}"),
                        bgcolor=ft.colors.RED_700
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            
            dlg = ft.AlertDialog(
                title=ft.Text("バックアップから復元"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("現在のデータは自動でバックアップされます", size=12, color=ft.colors.GREY_600),
                        backup_dropdown,
                    ], tight=True, spacing=15),
                    width=450
                ),
                actions=[
                    ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                    ft.ElevatedButton("復元実行", on_click=restore_backup, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
                ]
            )
            
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
            
        except Exception as e:
            print(f"復元ダイアログエラー: {e}")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"復元ダイアログエラー: {e}"),
                bgcolor=ft.colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def show_import_items_dialog(self):
        """拾得物データインポートダイアログ"""
        file_path_field = ft.TextField(
            label="CSVファイルパス",
            width=400,
            hint_text="CSVファイルのパスを入力してください"
        )
        
        def import_items_data(e):
            if not file_path_field.value:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("CSVファイルパスを入力してください"),
                    bgcolor=ft.colors.RED_700
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            try:
                import csv
                from pathlib import Path
                
                csv_file = Path(file_path_field.value)
                if not csv_file.exists():
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("指定されたファイルが見つかりません"),
                        bgcolor=ft.colors.RED_700
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return
                
                conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
                cur = conn.cursor()
                
                imported_count = 0
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # CSVデータをデータベースに挿入
                        cur.execute("""
                            INSERT INTO items (
                                item_number, category, subcategory, description, color,
                                brand, material, size_info, find_location, storage_location,
                                finder_name, received_date, staff_name, status, notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('拾得番号', ''),
                            row.get('カテゴリ', ''),
                            row.get('サブカテゴリ', ''),
                            row.get('詳細説明', ''),
                            row.get('色', ''),
                            row.get('ブランド', ''),
                            row.get('素材', ''),
                            row.get('サイズ情報', ''),
                            row.get('拾得場所', ''),
                            row.get('保管場所', ''),
                            row.get('拾得者名', ''),
                            row.get('受付日時', ''),
                            row.get('担当者', ''),
                            row.get('ステータス', '受付中'),
                            row.get('備考', '')
                        ))
                        imported_count += 1
                
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"{imported_count}件のデータをインポートしました"),
                    bgcolor=ft.colors.GREEN_700
                )
                self.page.snack_bar.open = True
                self.page.update()
                
            except Exception as ex:
                print(f"インポートエラー: {ex}")
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"インポートエラー: {ex}"),
                    bgcolor=ft.colors.RED_700
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("拾得物データインポート"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("CSV形式のファイルをインポートします", size=14),
                    ft.Text("※既存データに追加されます", size=12, color=ft.colors.ORANGE_700),
                    file_path_field,
                ], tight=True, spacing=15),
                width=450
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("インポート実行", on_click=import_items_data, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()