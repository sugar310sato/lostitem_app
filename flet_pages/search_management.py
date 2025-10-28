import flet as ft
import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
import cv2
import base64
import io
from PIL import Image

# データベースパス
DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"

# 定数定義
ITEM_CLASS_L = [
    "衣類・履物", "貴重品", "電化製品", "文房具・書籍", 
    "化粧品・日用品", "食品・飲料", "その他"
]

ITEM_CLASS_M = [
    {"value": "財布", "data-val": "貴重品"},
    {"value": "鍵", "data-val": "貴重品"},
    {"value": "携帯電話", "data-val": "電化製品"},
    {"value": "スマートフォン", "data-val": "電化製品"},
    {"value": "時計", "data-val": "貴重品"},
    {"value": "眼鏡", "data-val": "その他"},
    {"value": "カバン・バッグ", "data-val": "衣類・履物"},
    {"value": "帽子", "data-val": "衣類・履物"},
    {"value": "靴", "data-val": "衣類・履物"},
    {"value": "傘", "data-val": "その他"},
]

ITEM_CLASS_S = [
    {"value": "革製", "data-val": "財布"},
    {"value": "布製", "data-val": "財布"},
    {"value": "金属製", "data-val": "鍵"},
    {"value": "プラスチック製", "data-val": "鍵"},
]

COLOR = [
    ("黒", "黒"), ("白", "白"), ("赤", "赤"), ("青", "青"), ("緑", "緑"),
    ("黄", "黄"), ("茶", "茶"), ("灰", "灰"), ("紫", "紫"), ("ピンク", "ピンク"),
    ("オレンジ", "オレンジ"), ("その他", "その他")
]

STORAGE_PLACE = [
    ("事務所", "事務所"), ("倉庫", "倉庫"), ("受付", "受付"), ("その他", "その他")
]

class SearchManagementView(ft.UserControl):
    def __init__(self, on_item_click=None):
        super().__init__()
        self.on_item_click = on_item_click
        self.search_results = []
        self.current_view_mode = "thumbnail"  # "thumbnail" or "list"
        self.current_dialog = None
        
        # 検索条件
        self.search_word = ""
        self.search_date_from = None
        self.search_date_to = None
        self.search_color = None
        self.search_class_l = None
        self.search_class_m = None
        self.search_class_s = None
        self.search_storage = None
        self.search_status = "all"  # "all", "stored", "refunded"
        
    def build(self):
        return self.create_search_view()
    
    def create_search_view(self):
        """検索画面を作成"""
        # 検索フィルター部分（折りたたみ可能）
        search_filters = self.create_search_filters()
        
        # 検索フィルターコンテナ（初期状態は展開、検索後は収納）
        self.filter_container = ft.Container(
            content=search_filters,
            padding=20,
            bgcolor=ft.colors.GREY_50,
            border_radius=12,
            border=ft.border.all(1, ft.colors.GREY_300),
            animate=ft.animation.Animation(300, "easeInOut"),
            visible=True,
        )
        
        # フィルター展開/収納ボタン
        self.filter_toggle_button = ft.IconButton(
            icon=ft.icons.FILTER_ALT,
            tooltip="検索フィルター",
            icon_color=ft.colors.BLUE_700,
            bgcolor=ft.colors.BLUE_50,
            on_click=self.toggle_search_filter,
        )
        
        # 表示モード切り替えボタン
        self.view_mode_buttons = ft.Row([
            ft.ElevatedButton(
                "サムネイル",
                icon=ft.icons.GRID_VIEW,
                on_click=lambda e: self.switch_view_mode("thumbnail"),
                bgcolor=ft.colors.BLUE_500 if self.current_view_mode == "thumbnail" else ft.colors.GREY_300,
                color=ft.colors.WHITE,
                height=36,
            ),
            ft.ElevatedButton(
                "リスト",
                icon=ft.icons.LIST,
                on_click=lambda e: self.switch_view_mode("list"),
                bgcolor=ft.colors.BLUE_500 if self.current_view_mode == "list" else ft.colors.GREY_300,
                color=ft.colors.WHITE,
                height=36,
            )
        ], spacing=10)
        
        # 検索結果表示部分
        results_container = self.create_results_container()
        
        return ft.Column([
            # ヘッダー
            ft.Row([
                ft.Text("拾得物検索", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                ft.Container(expand=True),
                self.filter_toggle_button,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(height=2, color=ft.colors.GREY_400),
            
            # 検索フィルター（折りたたみ可能）
            self.filter_container,
            
            # ツールバー
            ft.Container(
                content=ft.Row([
                    ft.Text("検索結果", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    ft.Container(expand=True),
                    self.view_mode_buttons,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(vertical=8),
            ),
            
            # 検索結果
            ft.Container(
                content=results_container,
                expand=True,
                padding=0,
            )
        ], expand=True, spacing=12)
    
    def create_search_filters(self):
        """検索フィルターを作成（ゆとりあるデザイン）"""
        # 検索ワード
        self.search_word_field = ft.TextField(
            label="検索ワード",
            hint_text="特徴、メーカー、備考など",
            width=400,
            height=45,
            border_radius=8,
        )
        
        # 日付範囲
        self.date_from_field = ft.TextField(
            label="拾得日（開始）",
            hint_text="YYYY-MM-DD",
            width=180,
            height=45,
            border_radius=8,
        )
        self.date_to_field = ft.TextField(
            label="拾得日（終了）",
            hint_text="YYYY-MM-DD",
            width=180,
            height=45,
            border_radius=8,
        )
        
        # 色
        self.color_dropdown = ft.Dropdown(
            label="色",
            options=[ft.dropdown.Option(x[0]) for x in COLOR],
            width=180,
            height=45,
            border_radius=8,
        )
        
        # 分類
        self.class_l_dropdown = ft.Dropdown(
            label="分類（大）",
            options=[ft.dropdown.Option(x) for x in ITEM_CLASS_L],
            width=180,
            height=45,
            border_radius=8,
        )
        self.class_m_dropdown = ft.Dropdown(
            label="分類（中）",
            width=180,
            height=45,
            border_radius=8,
        )
        self.class_s_dropdown = ft.Dropdown(
            label="分類（小）",
            width=180,
            height=45,
            border_radius=8,
        )
        
        # 保管場所
        self.storage_dropdown = ft.Dropdown(
            label="保管場所",
            options=[ft.dropdown.Option(x[0]) for x in STORAGE_PLACE],
            width=180,
            height=45,
            border_radius=8,
        )
        
        # ステータス
        self.status_dropdown = ft.Dropdown(
            label="ステータス",
            options=[
                ft.dropdown.Option("all", "すべて"),
                ft.dropdown.Option("stored", "保管中"),
                ft.dropdown.Option("refunded", "返還済み")
            ],
            value="all",
            width=180,
            height=45,
            border_radius=8,
        )
        
        # 分類の連動
        def on_class_l_change(e):
            val = self.class_l_dropdown.value
            m_opts = [m["value"] for m in ITEM_CLASS_M if m.get("data-val") == val]
            self.class_m_dropdown.options = [ft.dropdown.Option(x) for x in m_opts]
            self.class_m_dropdown.value = None
            self.class_m_dropdown.update()
            self.class_s_dropdown.options = []
            self.class_s_dropdown.value = None
            self.class_s_dropdown.update()
        self.class_l_dropdown.on_change = on_class_l_change
        
        def on_class_m_change(e):
            val = self.class_m_dropdown.value
            s_opts = [s["value"] for s in ITEM_CLASS_S if s.get("data-val") == val]
            self.class_s_dropdown.options = [ft.dropdown.Option(x) for x in s_opts]
            self.class_s_dropdown.value = None
            self.class_s_dropdown.update()
        self.class_m_dropdown.on_change = on_class_m_change
        
        # 検索ボタン
        search_button = ft.ElevatedButton(
            "検索実行",
            icon=ft.icons.SEARCH,
            on_click=self.perform_search,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            height=45,
            width=140,
        )
        
        # リセットボタン
        reset_button = ft.OutlinedButton(
            "リセット",
            icon=ft.icons.REFRESH,
            on_click=self.reset_filters,
            height=45,
            width=120,
        )
        
        return ft.Column([
            # 検索ワード行
            ft.Container(
                content=ft.Column([
                    ft.Text("キーワード検索", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    self.search_word_field,
                ], spacing=8),
                padding=ft.padding.only(bottom=16),
            ),
            
            # 日付範囲行
            ft.Container(
                content=ft.Column([
                    ft.Text("拾得日で絞り込み", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    ft.Row([
                        self.date_from_field,
                        ft.Text("〜", size=16),
                        self.date_to_field,
                    ], spacing=12),
                ], spacing=8),
                padding=ft.padding.only(bottom=16),
            ),
            
            # 分類フィルター行
            ft.Container(
                content=ft.Column([
                    ft.Text("分類で絞り込み", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    ft.Row([
                        self.class_l_dropdown,
                        self.class_m_dropdown,
                        self.class_s_dropdown,
                    ], spacing=16, wrap=True),
                ], spacing=8),
                padding=ft.padding.only(bottom=16),
            ),
            
            # その他のフィルター行
            ft.Container(
                content=ft.Column([
                    ft.Text("その他の条件", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    ft.Row([
                        self.color_dropdown,
                        self.storage_dropdown,
                        self.status_dropdown,
                    ], spacing=16, wrap=True),
                ], spacing=8),
                padding=ft.padding.only(bottom=20),
            ),
            
            # ボタン行
            ft.Row([
                search_button,
                reset_button,
            ], spacing=16, alignment=ft.MainAxisAlignment.END),
        ], spacing=0)
    
    def create_results_container(self):
        """検索結果表示コンテナを作成"""
        self.results_container = ft.Container(
            content=ft.Text("検索を実行してください", size=16, color=ft.colors.GREY_600),
            expand=True,
            padding=20,
            alignment=ft.alignment.center
        )
        return self.results_container
    
    def toggle_search_filter(self, e=None):
        """検索フィルターの表示/非表示を切り替え"""
        self.filter_container.visible = not self.filter_container.visible
        self.filter_container.update()
    
    def switch_view_mode(self, mode):
        """表示モードを切り替え"""
        self.current_view_mode = mode
        
        # ボタンの色を更新
        for btn in self.view_mode_buttons.controls:
            if isinstance(btn, ft.ElevatedButton):
                if (mode == "thumbnail" and btn.text == "サムネイル") or (mode == "list" and btn.text == "リスト"):
                    btn.bgcolor = ft.colors.BLUE_500
                else:
                    btn.bgcolor = ft.colors.GREY_300
                btn.update()
        
        if self.search_results:
            self.update_results_display()
        self.update()
    
    def perform_search(self, e):
        """検索を実行"""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            
            # 検索条件を構築
            where_conditions = []
            params = []
            
            # 検索ワード
            if self.search_word_field.value:
                search_word = f"%{self.search_word_field.value}%"
                where_conditions.append("""
                    (feature LIKE ? OR maker LIKE ? OR remarks LIKE ? OR 
                     item_class_l LIKE ? OR item_class_m LIKE ? OR item_class_s LIKE ?)
                """)
                params.extend([search_word] * 6)
            
            # 日付範囲
            if self.date_from_field.value:
                where_conditions.append("DATE(get_item) >= ?")
                params.append(self.date_from_field.value)
            
            if self.date_to_field.value:
                where_conditions.append("DATE(get_item) <= ?")
                params.append(self.date_to_field.value)
            
            # 色
            if self.color_dropdown.value:
                where_conditions.append("color = ?")
                params.append(self.color_dropdown.value)
            
            # 分類
            if self.class_l_dropdown.value:
                where_conditions.append("item_class_l = ?")
                params.append(self.class_l_dropdown.value)
            
            if self.class_m_dropdown.value:
                where_conditions.append("item_class_m = ?")
                params.append(self.class_m_dropdown.value)
            
            if self.class_s_dropdown.value:
                where_conditions.append("item_class_s = ?")
                params.append(self.class_s_dropdown.value)
            
            # 保管場所
            if self.storage_dropdown.value:
                where_conditions.append("storage_place = ?")
                params.append(self.storage_dropdown.value)
            
            # ステータス
            if self.status_dropdown.value == "stored":
                where_conditions.append("item_situation = '保管中'")
            elif self.status_dropdown.value == "refunded":
                where_conditions.append("refund_situation = '済'")
            
            # SQLクエリを構築
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
                SELECT id, item_image, get_item, get_item_hour, get_item_minute,
                       item_class_l, item_class_m, item_class_s, color, feature,
                       item_situation, refund_situation, storage_place
                FROM lost_items
                WHERE {where_clause}
                ORDER BY get_item DESC
            """
            
            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()
            
            # 検索結果を処理
            self.search_results = []
            for row in rows:
                item_id, item_image, get_date, hour, minute, class_l, class_m, class_s, color, feature, item_situation, refund_situation, storage_place = row
                
                # 画像パスを取得
                img_path = None
                if item_image:
                    try:
                        data = json.loads(item_image)
                        if isinstance(data, dict) and data.get("photos"):
                            img_path = data["photos"][0] if data["photos"] else None
                        elif isinstance(data, list) and len(data) > 0:
                            img_path = data[0]
                    except:
                        img_path = item_image
                
                self.search_results.append({
                    "id": item_id,
                    "image": img_path,
                    "date": get_date,
                    "hour": hour,
                    "minute": minute,
                    "class_l": class_l,
                    "class_m": class_m,
                    "class_s": class_s,
                    "color": color,
                    "feature": feature,
                    "item_situation": item_situation,
                    "refund_situation": refund_situation,
                    "storage_place": storage_place
                })
            
            # 結果を表示
            self.update_results_display()
            
            # 検索後、フィルターを自動的に収納
            if self.filter_container.visible:
                self.filter_container.visible = False
                self.filter_container.update()
            
        except Exception as e:
            self.show_error(f"検索エラー: {str(e)}")
    
    def update_results_display(self):
        """検索結果の表示を更新"""
        if not self.search_results:
            self.results_container.content = ft.Text("検索結果がありません", size=16, color=ft.colors.GREY_600)
        elif self.current_view_mode == "thumbnail":
            self.results_container.content = self.create_thumbnail_grid()
        else:
            self.results_container.content = self.create_list_view()
        
        self.results_container.update()
    
    def create_thumbnail_grid(self):
        """サムネイルグリッドを作成"""
        thumbnail_controls = []
        for item in self.search_results:
            # ステータスに応じた色
            status_color = self.get_status_color(item)
            
            # 画像のサムネイルを作成
            if item["image"] and Path(item["image"]).exists():
                img = ft.Image(
                    src=item["image"],
                    width=120,
                    height=120,
                    fit=ft.ImageFit.COVER,
                    border_radius=8
                )
            else:
                img = ft.Container(
                    width=120,
                    height=120,
                    bgcolor=ft.colors.GREY_300,
                    border_radius=8,
                    content=ft.Icon(ft.icons.IMAGE, size=40, color=ft.colors.GREY_600),
                    alignment=ft.alignment.center
                )
            
            # ステータス表示
            status_text = self.get_status_text(item)
            
            thumbnail_controls.append(
                ft.Container(
                    content=ft.Column([
                        img,
                        ft.Text(f"ID: {item['id']}", size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{item['date']} {str(item['hour']).zfill(2)}:{str(item['minute']).zfill(2)}", 
                               size=10, color=ft.colors.GREY_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(status_text, size=10, color=status_color, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{item['class_l']} - {item['color']}", size=9, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER)
                    ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=8,
                    border=ft.border.all(2, status_color),
                    border_radius=12,
                    bgcolor=ft.colors.WHITE,
                    width=140,
                    height=180,
                    on_click=lambda e, item=item: self.show_item_detail(item)
                )
            )
        
        return ft.GridView(
            thumbnail_controls,
            runs_count=4,
            max_extent=150,
            child_aspect_ratio=0.8,
            spacing=10,
            run_spacing=10,
            expand=True
        )
    
    def create_list_view(self):
        """リスト表示を作成"""
        list_controls = []
        for item in self.search_results:
            status_color = self.get_status_color(item)
            status_text = self.get_status_text(item)
            
            # 画像のサムネイル
            if item["image"] and Path(item["image"]).exists():
                img = ft.Image(
                    src=item["image"],
                    width=80,
                    height=80,
                    fit=ft.ImageFit.COVER,
                    border_radius=8
                )
            else:
                img = ft.Container(
                    width=80,
                    height=80,
                    bgcolor=ft.colors.GREY_300,
                    border_radius=8,
                    content=ft.Icon(ft.icons.IMAGE, size=30, color=ft.colors.GREY_600),
                    alignment=ft.alignment.center
                )
            
            list_controls.append(
                ft.Container(
                    content=ft.Row([
                        img,
                        ft.Column([
                            ft.Row([
                                ft.Text(f"ID: {item['id']}", size=14, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    content=ft.Text(status_text, size=10, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=12
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(f"拾得日: {item['date']} {str(item['hour']).zfill(2)}:{str(item['minute']).zfill(2)}", 
                                   size=12, color=ft.colors.GREY_700),
                            ft.Text(f"分類: {item['class_l']} - {item['class_m']} - {item['class_s']}", 
                                   size=12, color=ft.colors.GREY_600),
                            ft.Text(f"色: {item['color']} | 保管場所: {item['storage_place']}", 
                                   size=11, color=ft.colors.GREY_600),
                            ft.Text(f"特徴: {item['feature'][:50]}{'...' if len(item['feature']) > 50 else ''}", 
                                   size=11, color=ft.colors.GREY_600)
                        ], expand=True, spacing=2),
                        ft.Icon(ft.icons.EDIT, color=ft.colors.BLUE_600)
                    ], alignment=ft.MainAxisAlignment.START, spacing=12),
                    padding=12,
                    border=ft.border.all(1, status_color),
                    border_radius=8,
                    bgcolor=ft.colors.WHITE,
                    on_click=lambda e, item=item: self.show_item_detail(item)
                )
            )
        
        return ft.ListView(list_controls, expand=True, spacing=8, padding=0)
    
    def get_status_color(self, item):
        """ステータスに応じた色を取得"""
        if item["refund_situation"] == "済":
            return ft.colors.GREEN_500
        elif item["item_situation"] == "保管中":
            return ft.colors.RED_500
        else:
            return ft.colors.GREY_500
    
    def get_status_text(self, item):
        """ステータステキストを取得"""
        if item["refund_situation"] == "済":
            return "返還済み"
        elif item["item_situation"] == "保管中":
            return "保管中"
        else:
            return "不明"
    
    def show_item_detail(self, item):
        """アイテム詳細を表示"""
        # 詳細ダイアログを作成
        detail_dialog = ft.AlertDialog(
            title=ft.Text(f"拾得物詳細 - ID: {item['id']}"),
            content=ft.Container(
                content=self.create_detail_content(item),
                width=600,
                height=500
            ),
            actions=[
                ft.TextButton("編集", on_click=lambda e: self.edit_item(item)),
                ft.TextButton("閉じる", on_click=lambda e: self.close_dialog())
            ]
        )
        
        if self.page:
            self.current_dialog = detail_dialog
            self.page.dialog = detail_dialog
            detail_dialog.open = True
            self.page.update()
    
    def create_detail_content(self, item):
        """詳細コンテンツを作成"""
        # メイン画像
        if item["image"] and Path(item["image"]).exists():
            main_img = ft.Image(
                src=item["image"],
                width=200,
                height=200,
                fit=ft.ImageFit.COVER,
                border_radius=8
            )
        else:
            main_img = ft.Container(
                width=200,
                height=200,
                bgcolor=ft.colors.GREY_300,
                border_radius=8,
                content=ft.Icon(ft.icons.IMAGE, size=60, color=ft.colors.GREY_600),
                alignment=ft.alignment.center
            )
        
        # ステータス表示
        status_color = self.get_status_color(item)
        status_text = self.get_status_text(item)
        
        return ft.Row([
            main_img,
            ft.Column([
                ft.Text("基本情報", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"ID: {item['id']}", size=14),
                ft.Text(f"拾得日: {item['date']} {str(item['hour']).zfill(2)}:{str(item['minute']).zfill(2)}", size=12),
                ft.Text(f"分類: {item['class_l']} - {item['class_m']} - {item['class_s']}", size=12),
                ft.Text(f"色: {item['color']}", size=12),
                ft.Text(f"保管場所: {item['storage_place']}", size=12),
                ft.Divider(),
                ft.Text("特徴", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(item['feature'], size=12, color=ft.colors.GREY_700),
                ft.Divider(),
                ft.Container(
                    content=ft.Text(status_text, size=14, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border_radius=16
                )
            ], spacing=8, expand=True)
        ], spacing=20)
    
    def edit_item(self, item):
        """アイテムを編集"""
        # 編集機能は後で実装
        self.show_success("編集機能は準備中です")
    
    def reset_filters(self, e):
        """フィルターをリセット"""
        self.search_word_field.value = ""
        self.date_from_field.value = ""
        self.date_to_field.value = ""
        self.color_dropdown.value = None
        self.class_l_dropdown.value = None
        self.class_m_dropdown.value = None
        self.class_s_dropdown.value = None
        self.storage_dropdown.value = None
        self.status_dropdown.value = "all"
        
        # 分類の連動をリセット
        self.class_m_dropdown.options = []
        self.class_s_dropdown.options = []
        
        self.update()
    
    def close_dialog(self):
        """ダイアログを閉じる"""
        if self.page and self.current_dialog:
            self.current_dialog.open = False
            self.current_dialog = None
            self.page.update()
    
    def show_error(self, message):
        """エラーメッセージを表示"""
        if self.page:
            if hasattr(self, 'current_dialog') and self.current_dialog:
                self.close_dialog()
            
            self.current_dialog = ft.AlertDialog(
                title=ft.Text("エラー", color=ft.colors.RED),
                content=ft.Text(message),
                actions=[ft.TextButton("OK", on_click=lambda e: self.close_dialog())],
                modal=True,
                open=True
            )
            self.page.overlay.append(self.current_dialog)
            self.page.update()
    
    def show_success(self, message):
        """成功メッセージを表示"""
        if self.page:
            if hasattr(self, 'current_dialog') and self.current_dialog:
                self.close_dialog()
            
            self.current_dialog = ft.AlertDialog(
                title=ft.Text("成功", color=ft.colors.GREEN),
                content=ft.Text(message),
                actions=[ft.TextButton("OK", on_click=lambda e: self.close_dialog())],
                modal=True,
                open=True
            )
            self.page.overlay.append(self.current_dialog)
            self.page.update()
