import flet as ft
import json
from datetime import date, datetime
from pathlib import Path
import sqlite3
import traceback

DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"


def get_all_items(page=1, per_page=20, search_params=None, sort_order="date_desc"):
    """すべての拾得物を取得（ページネーション対応）"""
    items = []
    total_count = 0
    
    try:
        print(f"get_all_items: Connecting to database...")
        conn = sqlite3.connect(str(DB_PATH), timeout=10.0)  # 10秒のタイムアウトを設定
        cur = conn.cursor()
        print(f"get_all_items: Connected successfully")
        
        # 検索条件を構築
        where_conditions = []
        params = []
        
        if search_params:
            if search_params.get("id"):
                where_conditions.append("id = ?")
                params.append(search_params["id"])
            
            if search_params.get("item_feature"):
                where_conditions.append("item_feature LIKE ?")
                params.append(f"%{search_params['item_feature']}%")
            
            if search_params.get("find_area"):
                where_conditions.append("find_area LIKE ?")
                params.append(f"%{search_params['find_area']}%")
            
            if search_params.get("item_color") and search_params["item_color"] != "未選択":
                where_conditions.append("item_color LIKE ?")
                params.append(f"%{search_params['item_color']}%")
            
            if search_params.get("start_date") and search_params.get("end_date"):
                where_conditions.append("DATE(get_item) BETWEEN ? AND ?")
                params.extend([search_params["start_date"], search_params["end_date"]])
            elif search_params.get("start_date"):
                where_conditions.append("DATE(get_item) >= ?")
                params.append(search_params["start_date"])
            elif search_params.get("end_date"):
                where_conditions.append("DATE(get_item) <= ?")
                params.append(search_params["end_date"])
            
            if search_params.get("item_class_L") and search_params["item_class_L"] != "選択してください":
                where_conditions.append("item_class_L = ?")
                params.append(search_params["item_class_L"])
            
            if search_params.get("item_class_M") and search_params["item_class_M"] != "選択してください":
                where_conditions.append("item_class_M = ?")
                params.append(search_params["item_class_M"])
            
            if search_params.get("item_class_S") and search_params["item_class_S"] != "選択してください":
                where_conditions.append("item_class_S = ?")
                params.append(search_params["item_class_S"])
            
            if search_params.get("item_not_yet"):
                where_conditions.append("item_situation != '返還済み'")
            
            if search_params.get("valuable_only"):
                where_conditions.append("item_value = 1")
            
            if not search_params.get("show_refunded", False):
                where_conditions.append("item_situation != '返還済み'")
            
            if not search_params.get("show_disposed", False):
                where_conditions.append("item_situation NOT IN ('廃棄', '売却済み')")
        
        # 総件数を取得
        count_query = "SELECT COUNT(*) FROM lost_items"
        if where_conditions:
            count_query += " WHERE " + " AND ".join(where_conditions)
        
        cur.execute(count_query, params)
        total_count = cur.fetchone()[0]
        
        # 並べ替え順を決定
        order_by_clause = "ORDER BY "
        if sort_order == "date_desc":
            order_by_clause += "get_item DESC, id DESC"
        elif sort_order == "date_asc":
            order_by_clause += "get_item ASC, id ASC"
        elif sort_order == "id_desc":
            order_by_clause += "id DESC"
        elif sort_order == "id_asc":
            order_by_clause += "id ASC"
        elif sort_order == "update_desc":
            order_by_clause += "recep_item DESC, id DESC"
        elif sort_order == "update_asc":
            order_by_clause += "recep_item ASC, id ASC"
        else:
            order_by_clause += "get_item DESC, id DESC"
        
        # データを取得（削除済みを除外）
        query = """
        SELECT id, item_image, get_item, get_item_hour, get_item_minute, 
               item_feature, find_area, item_color, item_situation, item_class_L, item_class_M, item_class_S,
               recep_item, recep_item_hour, recep_item_minute
        FROM lost_items
        WHERE item_situation != '削除済み'
        """
        
        if where_conditions:
            query += " AND " + " AND ".join(where_conditions)
        
        query += f" {order_by_clause} LIMIT ? OFFSET ?"
        
        offset = (page - 1) * per_page
        cur.execute(query, params + [per_page, offset])
        
        for row in cur.fetchall():
            item_id, item_image, get_item, hour, minute, feature, area, color, situation, class_l, class_m, class_s, recep_item, recep_hour, recep_min = row
            
            # 画像パスを取得
            img_path = None
            if isinstance(item_image, str) and item_image:
                try:
                    data = json.loads(item_image)
                    if isinstance(data, dict):
                        if data.get("main_photos") and len(data["main_photos"]) > 0:
                            img_path = data["main_photos"][0]
                        elif data.get("photos") and len(data["photos"]) > 0:
                            img_path = data["photos"][0]
                    elif isinstance(data, list) and len(data) > 0:
                        img_path = data[0]
                    else:
                        img_path = item_image
                except Exception:
                    img_path = item_image
            
            # 日時をフォーマット
            if get_item:
                if isinstance(get_item, str):
                    get_item = datetime.fromisoformat(get_item.replace('Z', '+00:00'))
                date_str = get_item.strftime("%Y/%m/%d")
                time_str = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}" if hour is not None and minute is not None else ""
            else:
                date_str = ""
                time_str = ""
            
            # 受付日時をフォーマット
            if recep_item:
                if isinstance(recep_item, str):
                    recep_item = datetime.fromisoformat(recep_item.replace('Z', '+00:00'))
                recep_date_str = recep_item.strftime("%Y/%m/%d")
                recep_time_str = f"{str(recep_hour).zfill(2)}:{str(recep_min).zfill(2)}" if recep_hour is not None and recep_min is not None else ""
            else:
                recep_date_str = ""
                recep_time_str = ""
            
            items.append({
                "id": item_id,
                "image": img_path,
                "date": date_str,
                "time": time_str,
                "recep_date": recep_date_str,
                "recep_time": recep_time_str,
                "feature": feature or "",
                "area": area or "",
                "color": color or "",
                "situation": situation or "",
                "class_l": class_l or "",
                "class_m": class_m or "",
                "class_s": class_s or "",
            })
        
        conn.close()
        print(f"get_all_items: Returned {len(items)} items, total_count: {total_count}")
    except Exception as e:
        print(f"データベースエラー in get_all_items: {e}")
        traceback.print_exc()
        # エラーが発生した場合は空のリストを返す
        items = []
        total_count = 0
    
    return items, total_count


def create_borderless_dropdown(label, options, value, on_change, width=150):
    """シンプルなプルダウンを作成"""
    return ft.Container(
        content=ft.Row([
            ft.Text(label, size=13, color=ft.colors.BLACK),
            ft.Dropdown(
                options=options,
                value=value,
                on_change=on_change,
                width=width,
                height=36,
                text_size=13,
                border_color=ft.colors.GREY_400,
                bgcolor=ft.colors.WHITE,
                color=ft.colors.BLACK,
                focused_border_color=ft.colors.BLUE_400,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            ),
        ], spacing=8, alignment=ft.MainAxisAlignment.START),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=ft.colors.WHITE,
        border_radius=6,
    )


def create_photo_card(page, item):
    """写真表示用のカードを作成"""
    # 画像のサムネイルを作成
    if item["image"] and Path(item["image"]).exists():
        img = ft.Image(
            src=item["image"],
            width=100,
            height=100,
            fit=ft.ImageFit.COVER,
            border_radius=8
        )
    else:
        # 画像がない場合は分類に応じたアイコンを表示
        icon_name = ft.icons.QUESTION_MARK
        icon_color = ft.colors.GREY_600
        
        if "現金" in item["class_l"] or "現金" in item["class_m"] or "現金" in item["class_s"]:
            icon_name = ft.icons.ATTACH_MONEY
            icon_color = ft.colors.GREEN_600
        elif "財布" in item["class_m"]:
            icon_name = ft.icons.ACCOUNT_BALANCE_WALLET
            icon_color = ft.colors.BROWN_600
        elif "鍵" in item["class_m"]:
            icon_name = ft.icons.VPN_KEY
            icon_color = ft.colors.ORANGE_600
        elif "携帯" in item["class_m"] or "スマートフォン" in item["class_m"]:
            icon_name = ft.icons.PHONE_ANDROID
            icon_color = ft.colors.BLUE_600
        elif "時計" in item["class_m"]:
            icon_name = ft.icons.ACCESS_TIME
            icon_color = ft.colors.PURPLE_600
        elif "眼鏡" in item["class_m"]:
            icon_name = ft.icons.VISIBILITY
            icon_color = ft.colors.CYAN_600
        elif "カバン" in item["class_m"] or "バッグ" in item["class_m"]:
            icon_name = ft.icons.WORK_BAG
            icon_color = ft.colors.INDIGO_600
        elif "帽子" in item["class_m"]:
            icon_name = ft.icons.HEADSET
            icon_color = ft.colors.RED_600
        elif "靴" in item["class_m"]:
            icon_name = ft.icons.DIRECTIONS_WALK
            icon_color = ft.colors.BROWN_600
        elif "傘" in item["class_m"]:
            icon_name = ft.icons.UMBRELLA
            icon_color = ft.colors.BLUE_600
        
        img = ft.Container(
            width=100,
            height=100,
            bgcolor=ft.colors.GREY_300,
            border_radius=8,
            content=ft.Icon(icon_name, size=40, color=icon_color),
            alignment=ft.alignment.center
        )
    
    # 日付をyyyy/mm/dd形式で表示
    date_display = item['date'] if item['date'] else "未設定"
    time_display = item['time'] if item['time'] else "00:00"
    
    # 3点リーダーメニュー（小さく）
    def show_context_menu(e):
        menu = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(
                    text="編集",
                    icon=ft.icons.EDIT,
                    on_click=lambda e: open_edit_form(page, item["id"])
                ),
                ft.PopupMenuItem(
                    text="ゴミ箱に移動",
                    icon=ft.icons.DELETE,
                    on_click=lambda e: delete_item(page, item["id"])
                ),
                ft.PopupMenuItem(
                    text="すべて選択",
                    icon=ft.icons.SELECT_ALL,
                    on_click=lambda e: select_all_items(page)
                ),
                ft.PopupMenuItem(
                    text="遺失物照合",
                    icon=ft.icons.SEARCH,
                    on_click=lambda e: search_lost_item(page, item["id"])
                ),
            ],
            icon=ft.icons.MORE_VERT,
            icon_size=16,
            tooltip="メニュー"
        )
        return menu
    
    return ft.Container(
        content=ft.Column([
            # 画像と3点メニュー
            ft.Stack([
                img,
                ft.Container(
                    content=show_context_menu(None),
                    right=2,
                    top=2,
                    bgcolor=ft.colors.WHITE,
                    border_radius=4,
                    width=24,
                    height=24,
                )
            ]),
            ft.Text(f"ID: {item['id']}", size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text(f"{date_display}", size=10, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
            ft.Text(f"{time_display}", size=10, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=12,
        border=ft.border.all(1, ft.colors.GREY_300),
        border_radius=12,
        bgcolor=ft.colors.WHITE,
        width=120,
        height=160,
        on_click=lambda e, item_id=item["id"]: open_edit_form(page, item_id),
        on_hover=lambda e: setattr(e.control, 'bgcolor', ft.colors.GREY_50 if e.data == "true" else ft.colors.WHITE) or e.control.update(),
    )


def create_detail_row(page, item):
    """詳細表示用の行を作成"""
    # 状況の色分け
    situation_color = ft.colors.BLUE_500 if item["situation"] == "保管中" else ft.colors.GREEN_500
    
    # アクションボタン
    action_buttons = ft.Row([
        ft.IconButton(
            ft.icons.EDIT,
            icon_size=16,
            tooltip="編集",
            on_click=lambda e, item_id=item["id"]: open_edit_form(page, item_id),
        ),
        ft.IconButton(
            ft.icons.DELETE,
            icon_size=16,
            tooltip="ゴミ箱に移動",
            icon_color=ft.colors.ORANGE,
            on_click=lambda e, item_id=item["id"]: delete_item(page, item_id),
        ),
    ], spacing=4)
    
    return ft.Container(
        content=ft.Row([
            # ID
            ft.Container(
                content=ft.Text(str(item["id"]), size=12, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
                width=80,
                padding=8,
                alignment=ft.alignment.center,
            ),
            # 拾得日時
            ft.Container(
                content=ft.Text(f"{item['date']}\n{item['time']}", size=11, text_align=ft.TextAlign.CENTER),
                width=120,
                padding=8,
                alignment=ft.alignment.center,
            ),
            # 受付日時
            ft.Container(
                content=ft.Text(f"{item['recep_date']}\n{item['recep_time']}", size=11, text_align=ft.TextAlign.CENTER),
                width=120,
                padding=8,
                alignment=ft.alignment.center,
            ),
            # 拾得物名/特徴
            ft.Container(
                content=ft.Text(f"{item['class_m']} {item['class_s']}\n{item['feature'][:30]}{'...' if len(item['feature']) > 30 else ''}", 
                                size=11, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                width=200,
                padding=8,
                alignment=ft.alignment.center_left,
            ),
            # 拾得場所
            ft.Container(
                content=ft.Text(item["area"], size=11, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                width=150,
                padding=8,
                alignment=ft.alignment.center_left,
            ),
            # 状況
            ft.Container(
                content=ft.Container(
                    content=ft.Text(item["situation"], size=10, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=situation_color,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4)
                ),
                width=100,
                padding=8,
                alignment=ft.alignment.center,
            ),
            # アクションボタン
            ft.Container(
                content=action_buttons,
                width=80,
                padding=8,
                alignment=ft.alignment.center,
            ),
        ], spacing=0),
        bgcolor=ft.colors.WHITE,
        border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        on_hover=lambda e: setattr(e.control, 'bgcolor', ft.colors.GREY_50 if e.data == "true" else ft.colors.WHITE) or e.control.update(),
    )


def get_item_data(item_id):
    """指定されたIDの拾得物データを取得"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM lost_items WHERE id = ?
        """, (item_id,))
        
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        
        # カラム名を取得
        columns = [description[0] for description in cur.description]
        
        # データを辞書に変換
        item_data = dict(zip(columns, row))
        
        conn.close()
        return item_data
        
    except Exception as e:
        print(f"データ取得エラー: {e}")
        return None


def open_edit_form(page, item_id):
    """編集フォームを開く"""
    try:
        # register_form.pyのRegisterFormViewを開く
        from flet_pages.register_form import RegisterFormView
        from flet_pages.home import build_sidebar_compact
        
        def on_submit(data):
            # 編集完了時の処理
            page.go("/items")
        
        def on_cancel():
            # キャンセル時の処理
            page.go("/items")
        
        # 既存データを取得
        item_data = get_item_data(item_id)
        if not item_data:
            print(f"ID {item_id} のデータが見つかりません")
            page.go("/items")
            return
    except Exception as e:
        print(f"編集フォームを開く際にエラーが発生しました: {e}")
        page.go("/items")
        return
    
    try:
        # 編集フォームを開く（既存データを読み込む）
        edit_form = RegisterFormView(
            on_submit=on_submit,
            on_temp_save=on_cancel,
            on_back_to_camera=on_cancel,
            existing_data=item_data  # 既存データを渡す
        )
        
        # サイドバーを作成
        sidebar = build_sidebar_compact(page, current_user=page.data.get("current_user"))
        
        # メインコンテンツエリア
        main_content = ft.Container(
            content=ft.Column([
                # ヘッダー
                ft.Row([
                    ft.ElevatedButton(
                        "← 一覧に戻る",
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda e: page.go("/items"),
                        bgcolor=ft.colors.GREY_500,
                        color=ft.colors.WHITE,
                        height=36,
                    ),
                    ft.Text(f"拾得物編集 (ID: {item_id})", size=24, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # 編集フォーム
                ft.Container(
                    content=edit_form,
                    expand=True,
                    padding=16,
                ),
            ], expand=True, spacing=16),
            expand=True,
            padding=16,
        )
        
        # ページのコンテンツを編集フォームに変更
        page.views.clear()
        page.views.append(
            ft.View(
                route=f"/edit_item/{item_id}",
                controls=[
                    ft.Row([
                        sidebar,
                        main_content,
                    ], expand=True, spacing=0)
                ],
                padding=0
            )
        )
        page.update()
        
    except Exception as e:
        print(f"編集フォームの表示中にエラーが発生しました: {e}")
        page.go("/items")


def build_items_list_content(page: ft.Page) -> ft.Control:
    """拾得物情報一覧のコンテンツを構築"""
    
    # 表示モード切り替えプルダウン
    view_mode_dropdown = create_borderless_dropdown(
        "表示",
        [
            ft.dropdown.Option("photo", "写真"),
            ft.dropdown.Option("detail", "詳細"),
        ],
        "photo",
        lambda e: change_view_mode(page, e.control.value),
        120
    )
    
    # 並べ替えプルダウン
    sort_dropdown = create_borderless_dropdown(
        "並べ替え",
        [
            ft.dropdown.Option("id_asc", "ID（昇順）"),
            ft.dropdown.Option("id_desc", "ID（降順）"),
            ft.dropdown.Option("date_asc", "拾得日時（昇順）"),
            ft.dropdown.Option("date_desc", "拾得日時（降順）"),
            ft.dropdown.Option("update_asc", "更新日時（昇順）"),
            ft.dropdown.Option("update_desc", "更新日時（降順）"),
        ],
        "date_desc",
        lambda e: change_sort(page, e.control.value),
        180
    )
    
    # 絞り込みボタン
    filter_button = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.FILTER_ALT, size=20, color=ft.colors.BLUE_700),
            ft.Text("絞り込み", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        bgcolor=ft.colors.WHITE,
        border_radius=8,
        on_click=lambda e: toggle_filter_panel(page),
        on_hover=lambda e: setattr(e.control, 'bgcolor', ft.colors.GREY_50 if e.data == "true" else ft.colors.WHITE) or e.control.update(),
    )
    
    # ツールバー
    toolbar = ft.Container(
        content=ft.Row([
            view_mode_dropdown,
            sort_dropdown,
            ft.Container(expand=True),
            filter_button,
        ], alignment=ft.MainAxisAlignment.START, spacing=16),
        padding=ft.padding.symmetric(vertical=8, horizontal=16),
        bgcolor=ft.colors.WHITE,
        border_radius=8,
        border=ft.border.all(1, ft.colors.GREY_200),
    )
    
    # 絞り込みパネル（初期状態は非表示）
    filter_panel = create_filter_panel(page)
    
    # 写真表示エリア
    photo_grid = ft.GridView(
        [],
        runs_count=6,
        max_extent=120,
        child_aspect_ratio=0.85,
        spacing=16,
        run_spacing=16,
        expand=True
    )
    
    # 詳細表示エリア（シンプルな構造）
    detail_container = ft.Container(
        content=ft.Column([
            # ヘッダー
            ft.Container(
                content=ft.Row([
                    ft.Text("管理番号", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=80),
                    ft.Text("拾得日時", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=120),
                    ft.Text("受付日時", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=120),
                    ft.Text("拾得物名/特徴", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=200),
                    ft.Text("拾得場所", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=150),
                    ft.Text("状況", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=100),
                    ft.Text("操作", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=80),
                ], spacing=0),
                bgcolor=ft.colors.BLUE_700,
                padding=12,
                border_radius=ft.border_radius.only(top_left=8, top_right=8),
            ),
            # データ行（直接Columnで管理）
            ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
        ], spacing=0),
        expand=True,
        border=ft.border.all(1, ft.colors.GREY_200),
        border_radius=8,
        visible=False  # 初期状態は非表示
    )
    
    # ページネーション
    pagination_info = ft.Text("", size=12, color=ft.colors.GREY_700)
    prev_button = ft.ElevatedButton(
        "前へ",
        icon=ft.icons.ARROW_BACK,
        on_click=lambda e: change_page(page, -1),
        disabled=True,
        height=32,
        width=60
    )
    next_button = ft.ElevatedButton(
        "次へ",
        icon=ft.icons.ARROW_FORWARD,
        on_click=lambda e: change_page(page, 1),
        disabled=True,
        height=32,
        width=60
    )
    pagination_controls = ft.Container(
        content=ft.Row([
            prev_button,
            pagination_info,
            next_button,
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        padding=12,
        bgcolor=ft.colors.WHITE,
        border_radius=8,
        border=ft.border.all(1, ft.colors.GREY_200),
        margin=ft.margin.only(top=16)
    )
    
    # メインコンテンツ
    content = ft.Column([
        # ヘッダー
        ft.Row([
            ft.ElevatedButton(
                "← ホームに戻る",
                icon=ft.icons.HOME,
                on_click=lambda e: page.go("/"),
                bgcolor=ft.colors.GREY_500,
                color=ft.colors.WHITE,
                height=36,
            ),
            ft.Text("拾得物情報一覧", size=24, weight=ft.FontWeight.BOLD),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
        # ツールバー
        toolbar,
        
        # 絞り込みパネル
        filter_panel,
        
        # 表示エリア
        photo_grid,
        detail_container,
        
        # ページネーション
        pagination_controls,
    ], expand=True, spacing=16)
    
    # ページの状態を初期化
    page.data = {
        "current_page": 1,
        "per_page": 20,
        "search_params": None,
        "sort_order": "date_desc",
        "view_mode": "photo",
        "photo_grid": photo_grid,
        "detail_container": detail_container,
        "pagination_info": pagination_info,
        "prev_button": prev_button,
        "next_button": next_button,
        "filter_panel": filter_panel,
    }
    
    # 初期データを読み込み
    load_items(page)
    
    return content


def create_filter_panel(page):
    """絞り込みパネルを作成"""
    # 検索フィールド
    id_field = ft.TextField(label="ID", width=100, height=36)
    feature_field = ft.TextField(label="特徴", width=200, height=36)
    area_field = ft.TextField(label="拾得場所", width=200, height=36)
    color_dropdown = ft.Dropdown(
        label="色",
        width=120,
        height=36,
        options=[
            ft.dropdown.Option("未選択", "未選択"),
            ft.dropdown.Option("赤", "赤"),
            ft.dropdown.Option("青", "青"),
            ft.dropdown.Option("緑", "緑"),
            ft.dropdown.Option("黄", "黄"),
            ft.dropdown.Option("黒", "黒"),
            ft.dropdown.Option("白", "白"),
            ft.dropdown.Option("その他", "その他"),
        ],
        value="未選択"
    )
    
    # 分類フィルター
    class_l_dropdown = ft.Dropdown(
        label="大分類", width=150, height=36,
        options=[ft.dropdown.Option("選択してください", "選択してください")],
        value="選択してください"
    )
    class_m_dropdown = ft.Dropdown(
        label="中分類", width=150, height=36,
        options=[ft.dropdown.Option("選択してください", "選択してください")],
        value="選択してください"
    )
    class_s_dropdown = ft.Dropdown(
        label="小分類", width=150, height=36,
        options=[ft.dropdown.Option("選択してください", "選択してください")],
        value="選択してください"
    )
    
    # 日時フィルター
    start_date_field = ft.TextField(label="拾得日時（開始）", width=150, height=36)
    end_date_field = ft.TextField(label="拾得日時（終了）", width=150, height=36)
    
    # チェックボックス
    valuable_checkbox = ft.Checkbox(label="貴重品のみ表示", value=False)
    refunded_checkbox = ft.Checkbox(label="返還済みも表示", value=False)
    disposed_checkbox = ft.Checkbox(label="廃棄・売却済みも表示", value=False)
    
    filter_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                id_field,
                feature_field,
                area_field,
                color_dropdown,
            ], spacing=12, wrap=True),
            ft.Row([
                class_l_dropdown,
                class_m_dropdown,
                class_s_dropdown,
            ], spacing=12, wrap=True),
            ft.Row([
                start_date_field,
                end_date_field,
            ], spacing=12),
            ft.Row([
                valuable_checkbox,
                refunded_checkbox,
                disposed_checkbox,
            ], spacing=20),
            ft.Row([
                ft.ElevatedButton(
                    "絞り込み実行",
                    icon=ft.icons.FILTER_ALT,
                    on_click=lambda e: apply_filter(page, {
                        "id_field": id_field,
                        "feature_field": feature_field,
                        "area_field": area_field,
                        "color_dropdown": color_dropdown,
                        "class_l_dropdown": class_l_dropdown,
                        "class_m_dropdown": class_m_dropdown,
                        "class_s_dropdown": class_s_dropdown,
                        "start_date_field": start_date_field,
                        "end_date_field": end_date_field,
                        "valuable_checkbox": valuable_checkbox,
                        "refunded_checkbox": refunded_checkbox,
                        "disposed_checkbox": disposed_checkbox,
                    }),
                    bgcolor=ft.colors.BLUE_500,
                    color=ft.colors.WHITE,
                    height=36,
                ),
                ft.OutlinedButton(
                    "リセット",
                    icon=ft.icons.REFRESH,
                    on_click=lambda e: reset_filter(page, {
                        "id_field": id_field,
                        "feature_field": feature_field,
                        "area_field": area_field,
                        "color_dropdown": color_dropdown,
                        "class_l_dropdown": class_l_dropdown,
                        "class_m_dropdown": class_m_dropdown,
                        "class_s_dropdown": class_s_dropdown,
                        "start_date_field": start_date_field,
                        "end_date_field": end_date_field,
                        "valuable_checkbox": valuable_checkbox,
                        "refunded_checkbox": refunded_checkbox,
                        "disposed_checkbox": disposed_checkbox,
                    }),
                    height=36,
                ),
            ], spacing=12, alignment=ft.MainAxisAlignment.END),
        ], spacing=16),
        padding=20,
        bgcolor=ft.colors.GREY_50,
        border_radius=8,
        border=ft.border.all(1, ft.colors.GREY_300),
        visible=False,
        animate=ft.animation.Animation(200, "easeOut"),
    )
    
    return filter_panel


def load_items(page: ft.Page):
    """アイテムを読み込んで表示"""
    try:
        print(f"=== load_items START ===")
        page_data = page.data
        current_page = page_data["current_page"]
        per_page = page_data["per_page"]
        search_params = page_data["search_params"]
        sort_order = page_data.get("sort_order", "date_desc")
        view_mode = page_data["view_mode"]
        
        print(f"Loading items - view_mode: {view_mode}, page: {current_page}, sort: {sort_order}")
        
        items, total_count = get_all_items(current_page, per_page, search_params, sort_order)
        print(f"Got {len(items)} items from database")
        
        # 表示形式に応じて更新
        if view_mode == "photo":
            print("Loading photo view...")
            load_photo_view(page, items)
        else:
            print("Loading detail view...")
            load_detail_view(page, items)
            
        print("View loaded, updating pagination...")
        
        # ページネーション情報を更新
        total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 0
        pagination_info = page_data["pagination_info"]
        pagination_info.value = f"ページ {current_page} / {total_pages} (全 {total_count} 件)"
        
        # ボタンの有効/無効を更新
        prev_button = page_data["prev_button"]
        next_button = page_data["next_button"]
        
        if prev_button:
            prev_button.disabled = current_page <= 1
        if next_button:
            next_button.disabled = current_page >= total_pages
        
        print("Calling page.update()...")
        page.update()
        print(f"=== load_items END ===")

    except Exception as e:
        print(f"ERROR in load_items: {e}")
        traceback.print_exc()


def load_photo_view(page: ft.Page, items):
    """写真表示でアイテムを読み込み"""
    page_data = page.data
    photo_grid = page_data["photo_grid"]
    detail_container = page_data["detail_container"]
    
    # コントロールをクリア
    photo_grid.controls.clear()
    
    # 写真表示を表示、詳細表示を非表示
    photo_grid.visible = True
    detail_container.visible = False
    
    for item in items:
        photo_card = create_photo_card(page, item)
        photo_grid.controls.append(photo_card)
    
    print(f"Added {len(photo_grid.controls)} items to photo grid")
    
    # ページを更新して表示を反映
    page.update()


def load_detail_view(page: ft.Page, items):
    """詳細表示でアイテムを読み込み"""
    page_data = page.data
    photo_grid = page_data["photo_grid"]
    detail_container = page_data["detail_container"]
    
    print(f"Loading detail view with {len(items)} items")
    print(f"Detail container structure: {type(detail_container.content)}")
    
    # コントロールをクリア
    photo_grid.controls.clear()
    
    # 詳細表示を表示、写真表示を非表示
    photo_grid.visible = False
    detail_container.visible = True
    
    print(f"Set photo_grid.visible = False, detail_container.visible = True")
    
    # データ行を取得（直接Columnで管理）
    try:
        data_column = detail_container.content.controls[1]  # 2番目の要素がデータColumn
        print(f"Data column type: {type(data_column)}")
        data_column.controls.clear()
        
        for item in items:
            detail_row = create_detail_row(page, item)
            data_column.controls.append(detail_row)
        
        print(f"Added {len(items)} items to detail view")
        print(f"Detail container visible: {detail_container.visible}")
        print(f"Photo grid visible: {photo_grid.visible}")
        
        # ページを更新して表示を反映
        page.update()
        
    except Exception as e:
        print(f"Error loading detail view: {e}")
        traceback.print_exc()
        # エラーが発生した場合は空の詳細表示を作成
        detail_container.content.controls[1].controls.clear()
        detail_container.content.controls[1].controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("詳細表示の読み込み中にエラーが発生しました", color=ft.colors.RED),
                    ft.Text(f"エラー: {str(e)}", size=12, color=ft.colors.GREY_600)
                ]),
                padding=16,
                alignment=ft.alignment.center
            )
        )


def toggle_filter_panel(page: ft.Page):
    """絞り込みパネルの表示/非表示を切り替え"""
    page_data = page.data
    filter_panel = page_data["filter_panel"]
    filter_panel.visible = not filter_panel.visible
    filter_panel.update()


def apply_filter(page: ft.Page, fields):
    """絞り込みを実行"""
    page_data = page.data
    
    # 検索パラメータを取得
    search_params = {}
    
    search_params["id"] = fields["id_field"].value if fields["id_field"].value else None
    search_params["item_feature"] = fields["feature_field"].value if fields["feature_field"].value else None
    search_params["find_area"] = fields["area_field"].value if fields["area_field"].value else None
    search_params["item_color"] = fields["color_dropdown"].value if fields["color_dropdown"].value else "未選択"
    search_params["start_date"] = fields["start_date_field"].value if fields["start_date_field"].value else None
    search_params["end_date"] = fields["end_date_field"].value if fields["end_date_field"].value else None
    search_params["item_class_L"] = fields["class_l_dropdown"].value if fields["class_l_dropdown"].value else "選択してください"
    search_params["item_class_M"] = fields["class_m_dropdown"].value if fields["class_m_dropdown"].value else "選択してください"
    search_params["item_class_S"] = fields["class_s_dropdown"].value if fields["class_s_dropdown"].value else "選択してください"
    search_params["valuable_only"] = fields["valuable_checkbox"].value
    search_params["show_refunded"] = fields["refunded_checkbox"].value
    search_params["show_disposed"] = fields["disposed_checkbox"].value
    
    page_data["search_params"] = search_params
    page_data["current_page"] = 1
    
    load_items(page)


def reset_filter(page: ft.Page, fields):
    """絞り込みをリセット"""
    page_data = page.data
    
    # フォームをクリア
    fields["id_field"].value = ""
    fields["feature_field"].value = ""
    fields["area_field"].value = ""
    fields["color_dropdown"].value = "未選択"
    fields["class_l_dropdown"].value = "選択してください"
    fields["class_m_dropdown"].value = "選択してください"
    fields["class_s_dropdown"].value = "選択してください"
    fields["start_date_field"].value = ""
    fields["end_date_field"].value = ""
    fields["valuable_checkbox"].value = False
    fields["refunded_checkbox"].value = False
    fields["disposed_checkbox"].value = False
    
    page_data["search_params"] = None
    page_data["current_page"] = 1
    
    # フォームを更新
    for field in fields.values():
        field.update()
    
    load_items(page)


def change_sort(page: ft.Page, sort_order):
    """並べ替え順を変更"""
    page_data = page.data
    page_data["sort_order"] = sort_order
    page_data["current_page"] = 1
    load_items(page)


def change_view_mode(page: ft.Page, mode):
    """表示形式を切り替え"""
    try:
        print(f"=== change_view_mode START: {mode} ===")
        page_data = page.data
        
        # 既に同じモードの場合は何もしない
        if page_data.get("view_mode") == mode:
            print(f"Already in {mode} mode, skipping")
            return
        
        page_data["view_mode"] = mode
        
        # 表示エリアの可視性を設定
        photo_grid = page_data["photo_grid"]
        detail_container = page_data["detail_container"]
        
        print(f"Before change - photo_grid.visible: {photo_grid.visible}, detail_container.visible: {detail_container.visible}")
        
        if mode == "photo":
            photo_grid.visible = True
            detail_container.visible = False
        else:  # detail
            photo_grid.visible = False
            detail_container.visible = True
        
        print(f"After change - photo_grid.visible: {photo_grid.visible}, detail_container.visible: {detail_container.visible}")
        
        # アイテムを再読み込み
        print("Calling load_items...")
        load_items(page)
        print("load_items completed")
        
        print(f"=== change_view_mode END ===")
        
    except Exception as e:
        print(f"ERROR in change_view_mode: {e}")
        traceback.print_exc()


def change_page(page: ft.Page, direction):
    """ページを変更"""
    page_data = page.data
    current_page = page_data["current_page"]
    
    if direction == 1:  # 次へ
        page_data["current_page"] = current_page + 1
    elif direction == -1:  # 前へ
        page_data["current_page"] = max(1, current_page - 1)
    
    load_items(page)


def delete_item(page: ft.Page, item_id):
    """アイテムをゴミ箱に移動（論理削除）"""
    def confirm_delete(e):
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            # 論理削除：item_situationを'削除済み'に変更
            cur.execute("UPDATE lost_items SET item_situation = '削除済み' WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            
            print(f"アイテム ID {item_id} をゴミ箱に移動しました")
            
            # ダイアログを閉じる
            page.overlay.pop()
            page.update()
            
            # 一覧を再読み込み
            load_items(page)
            
        except Exception as e:
            print(f"削除エラー: {e}")
            # エラーダイアログを表示
            error_dialog = ft.AlertDialog(
                title=ft.Text("エラー"),
                content=ft.Text(f"削除に失敗しました: {str(e)}"),
                actions=[ft.TextButton("OK", on_click=lambda e: (page.overlay.pop(), page.update()))],
            )
            page.overlay.append(error_dialog)
            page.update()
    
    def cancel_delete(e):
        page.overlay.pop()
        page.update()

    # 確認ダイアログ
    dialog = ft.AlertDialog(
        title=ft.Text("ゴミ箱に移動"),
        content=ft.Text(f"ID {item_id} の拾得物をゴミ箱に移動しますか？\n後で復元することができます。"),
        actions=[
            ft.TextButton("キャンセル", on_click=cancel_delete),
            ft.TextButton("ゴミ箱に移動", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.ORANGE)),
        ],
    )
    
    page.overlay.append(dialog)
    page.update()


def select_all_items(page: ft.Page):
    """すべてのアイテムを選択"""
    # 後日実装
    print("すべて選択機能（後日実装）")
    pass


def search_lost_item(page: ft.Page, item_id):
    """遺失物照合"""
    # 後日実装
    print(f"遺失物照合機能（後日実装） - ID: {item_id}")
    pass