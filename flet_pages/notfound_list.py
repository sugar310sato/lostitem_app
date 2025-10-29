import flet as ft
import sqlite3
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import traceback


DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"

# サジェスト候補のデータ
SUGGESTIONS = {
    "しゃ": ["シャツ", "白"],
    "か": ["傘", "白"],
    "i": ["iphone", "黒", "iphone ケース"],
    "a": ["airpods", "airpods pro"],
    "し": ["財布", "長財布"],
    "け": ["携帯", "携帯電話"],
    "め": ["メガネ", "眼鏡"],
    "き": ["鍵", "キー"],
    "て": ["手帳", "手帳 革"],
}

def get_notfound_items(page=1, per_page=50, search_params=None, sort_order="date_desc"):
	"""遺失物一覧を取得（ページネーション対応）"""
	items = []
	total_count = 0
	
	try:
		print(f"get_notfound_items: Connecting to database...")
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		print(f"get_notfound_items: Connected successfully")
        
		# 検索条件を構築
		where_conditions = []
		params = []
        
		if search_params:
			if search_params.get("keyword"):
				keyword = search_params["keyword"].strip()
				if keyword:
					where_conditions.append("(name LIKE ? OR phone LIKE ? OR location LIKE ? OR item LIKE ?)")
					keyword_param = f"%{keyword}%"
					params.extend([keyword_param, keyword_param, keyword_param, keyword_param])
            
		if search_params.get("start_date") and search_params.get("end_date"):
			where_conditions.append("DATE(lost_date) BETWEEN ? AND ?")
			params.extend([search_params["start_date"], search_params["end_date"]])
		elif search_params.get("start_date"):
			where_conditions.append("DATE(lost_date) >= ?")
			params.append(search_params["start_date"])
		elif search_params.get("end_date"):
			where_conditions.append("DATE(lost_date) <= ?")
			params.append(search_params["end_date"])
		
		# 状態フィルター（すべてを選択した場合は何も表示しない問題を修正）
		if search_params and search_params.get("status") and search_params["status"] != "":
			if search_params["status"] == "未発見":
				# 未発見は status が空または null の場合
				where_conditions.append("(status IS NULL OR status = '' OR status = '連絡待ち')")
			else:
				where_conditions.append("status = ?")
				params.append(search_params["status"])
		
		# WHERE句を構築
		where_clause = ""
		if where_conditions:
			where_clause = "WHERE " + " AND ".join(where_conditions)
		
		# 並び替え条件を構築
		order_clause = "ORDER BY "
		if sort_order == "date_asc":
			order_clause += "lost_date ASC"
		elif sort_order == "date_desc":
			order_clause += "lost_date DESC"
		elif sort_order == "name_asc":
			order_clause += "name ASC"
		elif sort_order == "name_desc":
			order_clause += "name DESC"
		else:
			order_clause += "lost_date DESC"
		
		# 総件数を取得
		count_query = f"SELECT COUNT(*) FROM notfound_items {where_clause}"
		cur.execute(count_query, params)
		total_count = cur.fetchone()[0]
		
		# データを取得（ページネーション）
		offset = (page - 1) * per_page
		query = f"""
			SELECT 
				id, name, phone, lost_date, location, item,
				status, contact_date, return_date, created_at, updated_at
			FROM notfound_items 
			{where_clause}
			{order_clause}
			LIMIT ? OFFSET ?
		"""
		cur.execute(query, params + [per_page, offset])
		
		rows = cur.fetchall()
		for row in rows:
			items.append({
				"id": row[0],
				"name": row[1] or "",
				"phone": row[2] or "",
				"lost_date": row[3] or "",
				"location": row[4] or "",
				"item": row[5] or "",
				"status": row[6] or "連絡待ち",
				"contact_date": row[7] or "",
				"return_date": row[8] or "",
				"created_at": row[9] or "",
				"updated_at": row[10] or ""
			})
		
		conn.close()
		print(f"get_notfound_items: Retrieved {len(items)} items (total: {total_count})")
		
	except Exception as e:
		print(f"get_notfound_items error: {e}")
		traceback.print_exc()
	
	return items, total_count

def build_notfound_list_content(page: ft.Page) -> ft.Control:
	"""遺失物一覧のコンテンツを構築"""
	
	# 状態管理
	current_page = 1
	per_page = 50
	
	# 日付の初期値
	start_date_value = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
	end_date_value = datetime.now().strftime("%Y-%m-%d")
	
	# 検索フィールド
	search_keyword = ft.TextField(
		hint_text="キーワード検索",
		hint_style=ft.TextStyle(color=ft.colors.GREY_400),
		width=300,
		autofocus=False,
		on_submit=lambda e: refresh_data()
	)
	
	# DatePickerの作成
	start_date_picker = ft.DatePicker(
		on_change=lambda e: _on_start_date_change(e)
	)
	
	end_date_picker = ft.DatePicker(
		on_change=lambda e: _on_end_date_change(e)
	)
	
	# 期間フィルター（カレンダー機能付き）
	start_date_field = ft.TextField(
		hint_text="yyyy/mm/dd",
		hint_style=ft.TextStyle(color=ft.colors.GREY_400),
		width=140,
		value=start_date_value.replace("-", "/"),
		keyboard_type=ft.KeyboardType.TEXT,
		max_length=10,
		focused_color=ft.colors.BLUE,
		bgcolor=ft.colors.WHITE,
		on_change=lambda e: _on_start_date_field_change(e)
	)
	
	end_date_field = ft.TextField(
		hint_text="yyyy/mm/dd",
		hint_style=ft.TextStyle(color=ft.colors.GREY_400),
		width=140,
		value=end_date_value.replace("-", "/"),
		keyboard_type=ft.KeyboardType.TEXT,
		max_length=10,
		focused_color=ft.colors.BLUE,
		bgcolor=ft.colors.WHITE,
		on_change=lambda e: _on_end_date_field_change(e)
	)
	
	# 状態フィルター
	status_filter = ft.Dropdown(
		hint_text="状態",
		hint_style=ft.TextStyle(color=ft.colors.GREY_400),
		options=[
			ft.dropdown.Option("", "すべて"),
			ft.dropdown.Option("未発見", "未発見"),
			ft.dropdown.Option("連絡待ち", "連絡待ち"),
			ft.dropdown.Option("連絡済み", "連絡済み"),
			ft.dropdown.Option("返還済み", "返還済み"),
		],
		width=120
	)
	
	# 表示件数
	per_page_dropdown = ft.Dropdown(
		hint_text="表示件数",
		options=[
			ft.dropdown.Option("10", "10件"),
			ft.dropdown.Option("20", "20件"),
			ft.dropdown.Option("50", "50件"),
			ft.dropdown.Option("100", "100件"),
		],
		value="50",
		width=120,
		on_change=lambda e: change_per_page()
	)
	
	# 並び替え
	sort_dropdown = ft.Dropdown(
		hint_text="並び替え",
		options=[
			ft.dropdown.Option("date_desc", "日時（新しい順）"),
			ft.dropdown.Option("date_asc", "日時（古い順）"),
			ft.dropdown.Option("name_asc", "氏名（昇順）"),
			ft.dropdown.Option("name_desc", "氏名（降順）"),
		],
		value="date_desc",
		width=180,
		on_change=lambda e: change_sort()
	)
	
	# 総件数テキスト
	total_count_text = ft.Text("総件数: 0件", size=16, weight=ft.FontWeight.BOLD)
	
	# データ表示エリア
	data_container = ft.Container(
		content=ft.Column([], spacing=0),
		height=600,
		bgcolor=ft.colors.WHITE,
		border=ft.border.all(1, ft.colors.GREY_200),
		border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8)
	)
	page_controls = ft.Row([], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
	
	# ヘッダー
	header_row = ft.Container(
		content=ft.Row([
			ft.Text("遺失日", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=150),
			ft.Text("お客様", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=150),
			ft.Text("遺失場所", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=150),
			ft.Text("金品情報", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=250),
			ft.Text("状態", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=100),
			ft.Text("操作", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.WHITE, width=80),
		], spacing=10),
		bgcolor=ft.colors.BLUE_700,
		padding=ft.padding.symmetric(horizontal=12, vertical=12),
		border_radius=ft.border_radius.only(top_left=8, top_right=8)
	)
	
	# 日付変更のハンドラー関数
	def _on_start_date_change(e):
		"""開始日のカレンダー選択"""
		nonlocal start_date_value
		if e.control.value:
			start_date_value = str(e.control.value).split()[0]
			start_date_field.value = start_date_value.replace("-", "/")
			start_date_field.update()
	
	def _on_end_date_change(e):
		"""終了日のカレンダー選択"""
		nonlocal end_date_value
		if e.control.value:
			end_date_value = str(e.control.value).split()[0]
			end_date_field.value = end_date_value.replace("-", "/")
			end_date_field.update()
	
	def _on_start_date_field_change(e):
		"""開始日フィールドの変更（yyyy/mm/dd形式）"""
		nonlocal start_date_value
		value = e.control.value
		value_clean = value.replace("/", "")
		if len(value_clean) == 8 and value_clean.isdigit():
			try:
				year = int(value_clean[0:4])
				month = int(value_clean[4:6])
				day = int(value_clean[6:8])
				datetime(year, month, day)  # 日付の存在チェック
				start_date_value = f"{year:04d}-{month:02d}-{day:02d}"
				e.control.border_color = ft.colors.GREEN
			except ValueError:
				e.control.border_color = ft.colors.RED
		else:
			e.control.border_color = None
		e.control.update()
	
	def _on_end_date_field_change(e):
		"""終了日フィールドの変更（yyyy/mm/dd形式）"""
		nonlocal end_date_value
		value = e.control.value
		value_clean = value.replace("/", "")
		if len(value_clean) == 8 and value_clean.isdigit():
			try:
				year = int(value_clean[0:4])
				month = int(value_clean[4:6])
				day = int(value_clean[6:8])
				datetime(year, month, day)  # 日付の存在チェック  
				end_date_value = f"{year:04d}-{month:02d}-{day:02d}"
				e.control.border_color = ft.colors.GREEN
			except ValueError:
				e.control.border_color = ft.colors.RED
		else:
			e.control.border_color = None
		e.control.update()

	def get_suggestions(text):
		"""キーワードのサジェストを取得"""
		if not text or len(text) < 1:
			return []
		
		text_lower = text.lower()
		suggestions = []
		
		for key, values in SUGGESTIONS.items():
			if key in text_lower:
				for value in values:
					if value not in suggestions:
						suggestions.append(value)
		
		return suggestions[:5]
	
	def on_keyword_change(e):
		"""キーワード変更時のサジェスト表示"""
		keyword = e.control.value
		suggestions = get_suggestions(keyword)
		
		if suggestions:
			suggest_text = "　".join(suggestions)
			page.banner.content = ft.Text(f"💡 サジェスト: {suggest_text}", size=14)
			page.banner.open = True
		else:
			page.banner.open = False
		page.update()
	
	def refresh_data():
		"""データを更新"""
		nonlocal current_page
		
		# 検索パラメータを構築
		search_params = {}
		
		if search_keyword.value and search_keyword.value.strip():
			search_params["keyword"] = search_keyword.value.strip()
		
		if start_date_value and end_date_value:
			search_params["start_date"] = start_date_value
			search_params["end_date"] = end_date_value
		
		if status_filter.value:
			search_params["status"] = status_filter.value
		
		# データを取得
		items, total = get_notfound_items(
			page=current_page,
			per_page=int(per_page_dropdown.value),
			search_params=search_params if search_params else None,
			sort_order=sort_dropdown.value
		)
		
		# 総件数を更新
		total_count_text.value = f"総件数: {total}件"
		
		# データ表示を更新
		data_container.content.controls = []
		
		if items:
			# データ行を作成
			for item in items:
				# 状態に応じた背景色と表示テキスト
				bg_color = ft.colors.WHITE
				status_color = ft.colors.GREY_700
				status_text = item["status"]
				
				if item["status"] == "連絡待ち":
					bg_color = ft.colors.ORANGE_50
					status_color = ft.colors.ORANGE_700
					status_text = "連絡待ち"
				elif item["status"] == "連絡済み":
					bg_color = ft.colors.BLUE_50
					status_color = ft.colors.BLUE_700
					status_text = "連絡済み"
				elif item["status"] == "返還済み":
					bg_color = ft.colors.GREEN_50
					status_color = ft.colors.GREEN_700
					status_text = "返還済み"
				else:
					# デフォルト状態（未発見）
					status_text = "未発見"
					status_color = ft.colors.GREY_700
				
				# 遺失日の表示形式を変更（yyyy/mm/dd(曜日) 00:00頃）
				lost_date_display = ""
				if item.get('lost_date'):
					try:
						from datetime import datetime
						date_obj = datetime.strptime(item['lost_date'], '%Y-%m-%d %H:%M:%S')
						weekdays = ['月', '火', '水', '木', '金', '土', '日']
						weekday = weekdays[date_obj.weekday()]
						lost_date_display = f"{date_obj.strftime('%Y/%m/%d')}({weekday}) {date_obj.strftime('%H:%M')}頃"
					except:
						lost_date_display = item.get('lost_date', '')
				
				# 金品情報を品名と内容に分離
				item_info = item.get('item', '')
				item_name = ""
				item_content = ""
				if item_info and " - " in item_info:
					parts = item_info.split(" - ", 1)
					item_name = parts[0] if len(parts) > 0 else ""
					item_content = parts[1] if len(parts) > 1 else ""
				else:
					item_name = item_info
				
				# データ行
				row = ft.Container(
					content=ft.Row([
						# 遺失日
						ft.Text(lost_date_display, size=12, color=ft.colors.BLACK, width=150, weight=ft.FontWeight.NORMAL),
						
						# お客様（氏名+様、電話を2段表示）
						ft.Column([
							ft.Text(f"{item.get('name', '')}様", size=12, color=ft.colors.BLACK, weight=ft.FontWeight.BOLD),
							ft.Text(f"{item.get('phone', '')}", size=11, color=ft.colors.GREY_600)
						], spacing=2, width=150),
						
						# 遺失場所
						ft.Text(f"{item.get('location', '')}", size=12, color=ft.colors.BLACK, width=150, weight=ft.FontWeight.NORMAL),
						
						# 金品情報（品名と内容を2段表示）
						ft.Column([
							ft.Text(f"品名: {item_name}", size=11, color=ft.colors.BLACK, weight=ft.FontWeight.BOLD),
							ft.Text(f"内容: {item_content}", size=11, color=ft.colors.GREY_600)
						], spacing=2, width=250),
						
						# 状態
						ft.Container(
							content=ft.Text(status_text, size=12, weight=ft.FontWeight.BOLD, color=status_color),
							width=100,
							alignment=ft.alignment.center
						),
						
						# 操作列スペース
						ft.Container(width=80)
					], spacing=10),
					bgcolor=bg_color,
					padding=ft.padding.symmetric(horizontal=12, vertical=12),
				)
				
				data_container.content.controls.append(row)
		else:
			data_container.content.controls.append(
				ft.Container(
					content=ft.Column([
						ft.Icon(ft.icons.INFO_OUTLINE, size=60, color=ft.colors.GREY_400),
						ft.Text("該当する遺失物がありません", size=16, color=ft.colors.GREY_500),
						ft.Text("検索条件を変更してお試しください", size=12, color=ft.colors.GREY_400)
					], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
					padding=50,
					alignment=ft.alignment.center
				)
			)
		
		# ページネーションを更新
		update_pagination(total)
		
		page.update()
	
	def update_pagination(total_items):
		"""ページネーションを更新"""
		nonlocal current_page
		
		total_pages = (total_items + int(per_page_dropdown.value) - 1) // int(per_page_dropdown.value)
		
		page_controls.controls = []
		
		if total_pages > 0:
			# 前へボタン
			if current_page > 1:
				page_controls.controls.append(
					ft.ElevatedButton(
						"前へ",
						on_click=lambda e: go_to_page(current_page - 1)
					)
				)
			
			# ページ番号表示
			start_page = max(1, current_page - 2)
			end_page = min(total_pages, current_page + 2)
			
			if start_page > 1:
				page_controls.controls.append(ft.TextButton(f"1", on_click=lambda e: go_to_page(1)))
				if start_page > 2:
					page_controls.controls.append(ft.Text("..."))
			
			for p in range(start_page, end_page + 1):
				if p == current_page:
					page_controls.controls.append(
						ft.Container(
							content=ft.Text(f"{p}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
							bgcolor=ft.colors.BLUE_700,
							padding=ft.padding.symmetric(horizontal=12, vertical=6),
							border_radius=5
						)
					)
				else:
					page_controls.controls.append(
						ft.TextButton(f"{p}", on_click=lambda e, p=p: go_to_page(p))
					)
			
			if end_page < total_pages:
				if end_page < total_pages - 1:
					page_controls.controls.append(ft.Text("..."))
				page_controls.controls.append(
					ft.TextButton(f"{total_pages}", on_click=lambda e: go_to_page(total_pages))
				)
			
			# 次へボタン
			if current_page < total_pages:
				page_controls.controls.append(
					ft.ElevatedButton(
						"次へ",
						on_click=lambda e: go_to_page(current_page + 1)
					)
				)
	
	def go_to_page(p):
		"""指定ページに移動"""
		nonlocal current_page
		current_page = p
		refresh_data()
	
	def change_per_page():
		"""表示件数を変更"""
		nonlocal current_page
		current_page = 1
		refresh_data()
	
	def change_sort():
		"""並び替えを変更"""
		nonlocal current_page
		current_page = 1
		refresh_data()
	
	# 検索ボタン
	search_button = ft.ElevatedButton(
		"検索",
		icon=ft.icons.SEARCH,
		on_click=lambda e: refresh_data(),
		bgcolor=ft.colors.BLUE_700,
		color=ft.colors.WHITE
	)
	
	# 初期データを読み込み
	def load_initial_data():
		refresh_data()
	
	# サジェスト用バナー
	page.banner = ft.Banner(
		bgcolor=ft.colors.BLUE_50,
		content=ft.Text(""),
		leading=ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE_700, size=20),
		actions=[
			ft.TextButton("閉じる", on_click=lambda e: setattr(page.banner, "open", False) or page.update())
		]
	)
	
	# キーワード検索の変更イベントを設定
	search_keyword.on_change = on_keyword_change
	
	# レイアウトを構築
	layout = ft.Container(
		content=ft.Column([
			# タイトル
			ft.Container(
				content=ft.Text("遺失物一覧", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
				alignment=ft.alignment.center,
				padding=ft.padding.only(top=20, bottom=20)
			),
			
			# 検索エリア
			ft.Container(
				content=ft.Column([
					ft.Row([
						search_keyword,
						search_button
					], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
					
					ft.Row([
						ft.Row([
							start_date_field,
							ft.IconButton(
								icon=ft.icons.CALENDAR_MONTH,
								on_click=lambda e: start_date_picker.pick_date(),
								tooltip="カレンダーから選択",
								icon_size=20
							)
						], spacing=5),
						ft.Text(" ～ ", size=14, color=ft.colors.GREY_600),
						ft.Row([
							end_date_field,
							ft.IconButton(
								icon=ft.icons.CALENDAR_MONTH,
								on_click=lambda e: end_date_picker.pick_date(),
								tooltip="カレンダーから選択",
								icon_size=20
							)
						], spacing=5),
						status_filter,
						per_page_dropdown,
						sort_dropdown
					], spacing=10, alignment=ft.MainAxisAlignment.CENTER)
				], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
				padding=20,
				bgcolor=ft.colors.GREY_100,
				border_radius=8
			),
			
			# 総件数
			ft.Container(
				content=total_count_text,
				padding=ft.padding.only(top=10, bottom=10)
			),
			
			# データ表示エリア（ヘッダー付き）
			ft.Container(
				content=ft.Column([
					header_row,
					data_container
				], spacing=0)
			),
			
			# ページネーション
			page_controls
			
		], spacing=15, scroll=ft.ScrollMode.AUTO),
		padding=20,
		bgcolor=ft.colors.GREY_50
	)
	
	# DatePickerをページオーバーレイに追加
	try:
		if page and not hasattr(page, '_notfound_datepickers_added'):
			page.overlay.extend([start_date_picker, end_date_picker])
			page._notfound_datepickers_added = True
			page.update()
	except Exception as e:
		print(f"DatePicker追加エラー: {e}")
	
	# 初回データを読み込み
	load_initial_data()
	
	return layout
