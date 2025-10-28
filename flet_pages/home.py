import flet as ft
import json
from datetime import date, datetime
from pathlib import Path
import sqlite3
import threading
import time

DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"


def get_counts():
	"""基本統計を取得"""
	stored = refunded = total = 0
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM lost_items WHERE item_situation = '保管中'")
		stored = cur.fetchone()[0]
		cur.execute("SELECT COUNT(*) FROM lost_items WHERE refund_situation = '済'")
		refunded = cur.fetchone()[0]
		cur.execute("SELECT COUNT(*) FROM lost_items")
		total = cur.fetchone()[0]
		conn.close()
	except Exception:
		pass
	return stored, refunded, total


def get_daily_stats():
	"""本日の統計と先日比を取得"""
	today = date.today()
	yesterday = date.fromordinal(today.toordinal() - 1)
	
	# 本日の拾得物件数
	today_found = 0
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM lost_items WHERE DATE(get_item) = ?", (today.isoformat(),))
		today_found = cur.fetchone()[0]
		conn.close()
	except Exception:
		pass
	
	# 昨日の拾得物件数
	yesterday_found = 0
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM lost_items WHERE DATE(get_item) = ?", (yesterday.isoformat(),))
		yesterday_found = cur.fetchone()[0]
		conn.close()
	except Exception:
		pass
	
	# 本日の遺失物届出件数（notfoundテーブルから取得）
	today_notfound = 0
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM notfound WHERE DATE(created_at) = ?", (today.isoformat(),))
		today_notfound = cur.fetchone()[0]
		conn.close()
	except Exception:
		pass
	
	# 昨日の遺失物届出件数
	yesterday_notfound = 0
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM notfound WHERE DATE(created_at) = ?", (yesterday.isoformat(),))
		yesterday_notfound = cur.fetchone()[0]
		conn.close()
	except Exception:
		pass
	
	# 総保管数（現在保管中の件数）
	total_stored = 0
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM lost_items WHERE item_situation = '保管中'")
		total_stored = cur.fetchone()[0]
		conn.close()
	except Exception:
		pass
	
	# 先日比を計算
	found_diff = today_found - yesterday_found
	notfound_diff = today_notfound - yesterday_notfound
	# 総保管数は前日比ではなく、前週比で計算
	week_ago = date.fromordinal(today.toordinal() - 7)
	week_ago_stored = 0
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM lost_items WHERE item_situation = '保管中' AND DATE(get_item) <= ?", (week_ago.isoformat(),))
		week_ago_stored = cur.fetchone()[0]
		conn.close()
	except Exception:
		pass
	
	stored_diff = total_stored - week_ago_stored
	
	return {
		'today_found': today_found,
		'found_diff': found_diff,
		'today_notfound': today_notfound,
		'notfound_diff': notfound_diff,
		'total_stored': total_stored,
		'stored_diff': stored_diff
	}


def get_today_items():
	items = []
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT id, item_image, get_item, get_item_hour, get_item_minute
			FROM lost_items
			WHERE DATE(get_item) = ?
			ORDER BY get_item DESC
			""",
			(date.today().isoformat(),),
		)
		for row in cur.fetchall():
			item_id, item_image, d, hh, mm = row
			img_path = None
			if isinstance(item_image, str) and item_image:
				try:
					data = json.loads(item_image)
					if isinstance(data, dict):
						# 新しいデータ構造に対応
						if data.get("main_photos") and len(data["main_photos"]) > 0:
							img_path = data["main_photos"][0]
						elif data.get("photos") and len(data["photos"]) > 0:
							# 旧データ構造のフォールバック
							img_path = data["photos"][0]
					elif isinstance(data, list) and len(data) > 0:
						# 旧データ構造のフォールバック
						img_path = data[0]
					else:
						img_path = item_image
				except Exception:
					img_path = item_image
			items.append({
				"id": item_id,
				"image": img_path,
				"date": d,
				"hour": hh,
				"minute": mm,
			})
		conn.close()
	except Exception:
		pass
	return items


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

def build_home_content(page: ft.Page, current_user=None) -> ft.Control:
	daily_stats = get_daily_stats()
	
	# 現在の日時を表示するテキストコントロール
	datetime_text = ft.Text(
		datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"),
		size=14,
		color=ft.colors.GREY_600,
		weight=ft.FontWeight.NORMAL
	)
	
	# 店舗名を表示するテキストコントロール
	store_name = "未設定"
	if current_user and current_user.get('id'):
		store_name = get_user_store_name(current_user['id'])
	
	store_text = ft.Text(
		f"店舗: {store_name}",
		size=14,
		color=ft.colors.BLUE_700,
		weight=ft.FontWeight.BOLD
	)
	
	# ログイン情報と担当者表示
	login_info_text = ft.Text(
		f"ログイン中: {current_user.get('display_name', '未設定')} ({current_user.get('role', 'user')})" if current_user else "未ログイン",
		size=12,
		color=ft.colors.GREY_600
	)
	
	# 現在の担当者表示（編集可能）
	current_staff_text = ft.Text(
		f"現在の担当者: {current_user.get('display_name', '未設定')}" if current_user else "現在の担当者: 未設定",
		size=14,
		color=ft.colors.GREEN_700,
		weight=ft.FontWeight.BOLD
	)
	
	def show_staff_change_dialog():
		"""担当者変更ダイアログを表示"""
		staff_dropdown = ft.Dropdown(
			label="担当者を選択",
			width=300,
			hint_text="担当者を選択してください"
		)
		
		# 担当者リストを取得
		try:
			conn = sqlite3.connect(str(DB_PATH))
			cur = conn.cursor()
			cur.execute("SELECT display_name FROM users WHERE role != 'admin' ORDER BY display_name")
			staff_list = [row[0] for row in cur.fetchall()]
			conn.close()
			
			staff_dropdown.options = [ft.dropdown.Option(name) for name in staff_list]
		except Exception as e:
			print(f"担当者リスト取得エラー: {e}")
			staff_dropdown.options = []
		
		def change_staff():
			"""担当者を変更"""
			if not staff_dropdown.value:
				page.snack_bar = ft.SnackBar(ft.Text("担当者を選択してください"), bgcolor=ft.colors.RED_700)
				page.snack_bar.open = True
				page.update()
				return
			
			try:
				# グローバル変数のcurrent_userを更新
				global current_user
				if current_user:
					current_user['display_name'] = staff_dropdown.value
					current_staff_text.value = f"現在の担当者: {staff_dropdown.value}"
					page.snack_bar = ft.SnackBar(ft.Text(f"担当者を {staff_dropdown.value} に変更しました"), bgcolor=ft.colors.GREEN_700)
					page.snack_bar.open = True
					page.update()
				
				# ダイアログを閉じる
				page.dialog.open = False
				page.update()
				
			except Exception as e:
				print(f"担当者変更エラー: {e}")
				page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {e}"), bgcolor=ft.colors.RED_700)
				page.snack_bar.open = True
				page.update()
		
		dialog = ft.AlertDialog(
			title=ft.Text("担当者変更"),
			content=ft.Container(
				content=ft.Column([
					ft.Text("現在の担当者を変更します"),
					staff_dropdown
				], spacing=15),
				width=350,
				height=150
			),
			actions=[
				ft.TextButton("キャンセル", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()),
				ft.ElevatedButton("変更", on_click=lambda e: change_staff(), bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
			]
		)
		
		page.dialog = dialog
		dialog.open = True
		page.update()
	
	# 日時更新のタイマー
	def update_datetime():
		while True:
			try:
				datetime_text.value = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
				if page:
					page.update()
			except:
				break
			time.sleep(1)
	
	# バックグラウンドで日時更新を開始
	datetime_thread = threading.Thread(target=update_datetime, daemon=True)
	datetime_thread.start()
	
	# ヘッダー部分（ホーム文字と日時・店舗名）
	header = ft.Row([
		ft.Text("ホーム", size=28, weight=ft.FontWeight.BOLD),
		ft.Container(expand=True),  # Spacerの代わり
		ft.Column([
			datetime_text,
			store_text,
		], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2)
	], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
	
	actions = ft.Row([
		ft.ElevatedButton(
			"📷 拾得物の登録",
			style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.BLUE_500, color=ft.colors.WHITE),
			on_click=lambda e: page.go("/register"),
		),
		ft.ElevatedButton(
			"📝 遺失物の登録",
			style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.PURPLE_500, color=ft.colors.WHITE),
			on_click=lambda e: page.go("/notfound-register"),
		),
		ft.ElevatedButton(
			"🔍 拾得物の検索",
			style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.GREEN_500, color=ft.colors.WHITE),
			on_click=lambda e: page.go("/search"),
		),
		ft.ElevatedButton(
			"📋 拾得物情報一覧",
			style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.ORANGE_500, color=ft.colors.WHITE),
			on_click=lambda e: page.go("/items"),
		),
	], spacing=16, alignment=ft.MainAxisAlignment.CENTER)

	# 前日比の表示用関数
	def format_diff(diff):
		if diff > 0:
			return f"+{diff}", ft.colors.BLACK
		elif diff < 0:
			return str(diff), ft.colors.BLACK
		else:
			return "±0", ft.colors.BLACK
	
	# 統計カードを作成
	found_diff_text, found_diff_color = format_diff(daily_stats['found_diff'])
	notfound_diff_text, notfound_diff_color = format_diff(daily_stats['notfound_diff'])
	stored_diff_text, stored_diff_color = format_diff(daily_stats['stored_diff'])
	
	stats = ft.Row([
		ft.Container(
			content=ft.Column([
				ft.Text("本日の拾得物件数", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
				ft.Text(f"{daily_stats['today_found']}件", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
				ft.Text(f"前日比 {found_diff_text}", size=12, color=found_diff_color),
			], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
			bgcolor=ft.colors.PINK_200,
			padding=20,
			border_radius=12,
			expand=1
		),
		ft.Container(
			content=ft.Column([
				ft.Text("本日の遺失物届出件数", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
				ft.Text(f"{daily_stats['today_notfound']}件", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
				ft.Text(f"前日比 {notfound_diff_text}", size=12, color=notfound_diff_color),
			], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
			bgcolor=ft.colors.LIGHT_BLUE_200,
			padding=20,
			border_radius=12,
			expand=1
		),
		ft.Container(
			content=ft.Column([
				ft.Text("総保管数", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
				ft.Text(f"{daily_stats['total_stored']}件", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
				ft.Text(f"前日比 {stored_diff_text}", size=12, color=stored_diff_color),
			], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
			bgcolor=ft.colors.LIGHT_GREEN_200,
			padding=20,
			border_radius=12,
			expand=1
		),
	], spacing=16, alignment=ft.MainAxisAlignment.CENTER)

	# メッセージバー
	message_bar = ft.Container(
		content=ft.Row([
			ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE_600, size=20),
			ft.Text(
				"これはプロトタイプです！完成をお待ちください！",
				size=14,
				color=ft.colors.BLUE_800,
				expand=True
			),
			ft.IconButton(
				ft.icons.CLOSE,
				icon_size=16,
				icon_color=ft.colors.GREY_600,
				on_click=lambda e: setattr(message_bar, 'visible', False) or page.update()
			)
		], spacing=8, alignment=ft.MainAxisAlignment.START),
		bgcolor=ft.colors.BLUE_50,
		padding=ft.padding.symmetric(horizontal=16, vertical=12),
		border_radius=8,
		border=ft.border.all(1, ft.colors.BLUE_200),
		margin=ft.margin.symmetric(horizontal=0, vertical=8)
	)

	today_items = get_today_items()
	
	# サムネイル画像のグリッドを作成
	thumbnail_controls = []
	for it in today_items:
		when = f"{str(it['hour']).zfill(2)}:{str(it['minute']).zfill(2)}"
		
		# 画像のサムネイルを作成
		if it["image"] and Path(it["image"]).exists():
			img = ft.Image(
				src=it["image"], 
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
		
		thumbnail_controls.append(
			ft.Container(
				content=ft.Column([
					img,
					ft.Text(f"ID: {it['id']}", size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
					ft.Text(when, size=10, color=ft.colors.GREY_700, text_align=ft.TextAlign.CENTER),
				], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
				padding=8,
				border=ft.border.all(1, ft.colors.GREY_300),
				border_radius=12,
				bgcolor=ft.colors.WHITE,
				width=140,
				height=160,
			)
		)
	
	# グリッドビューでサムネイルを表示
	grid_view = ft.GridView(
		thumbnail_controls,
		runs_count=4,  # 4列表示
		max_extent=150,
		child_aspect_ratio=0.9,  # 少し縦長
		spacing=10,
		run_spacing=10,
		expand=True
	)

	return ft.Column([
		header,
		ft.Container(height=20),
		stats,
		ft.Container(height=20),
		actions,
		message_bar,
		ft.Text("本日の拾得物", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
		ft.Container(height=10),
		ft.Container(
			content=grid_view,
			expand=True,
			padding=10,
			bgcolor=ft.colors.GREY_50,
			border_radius=12
		),
		# ログイン情報と担当者セクション（左下）
		ft.Container(
			content=ft.Row([
				ft.Column([
					login_info_text,
					ft.Row([
						current_staff_text,
						ft.IconButton(
							icon=ft.icons.EDIT,
							tooltip="担当者を変更",
							on_click=lambda e: show_staff_change_dialog(),
							icon_size=16
						) if current_user else ft.Container()
					], alignment=ft.MainAxisAlignment.START)
				], horizontal_alignment=ft.CrossAxisAlignment.START),
				ft.Container(expand=True)  # 右側を空ける
			], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
			padding=10,
			bgcolor=ft.colors.GREY_100,
			border_radius=8,
			margin=ft.margin.only(top=20)
		)
	], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)


def build_sidebar_compact(page: ft.Page, current_user=None, on_login=None, on_logout=None) -> ft.Control:
	"""ホーム以外のページ用：ホバーで展開するサイドバー"""
	menu_buttons = [
		("ホーム", "/", ft.icons.HOME),
		("拾得物の登録", "/register", ft.icons.NOTE_ADD),
		("遺失物の登録", "/notfound-register", ft.icons.DESCRIPTION),
		("遺失物一覧", "/notfound-list", ft.icons.LIST),
		("還付管理", "/refund", ft.icons.ATTACH_MONEY),
		("警察届け出処理", "/police", ft.icons.GAVEL),
		("統計", "/stats", ft.icons.INSIGHTS),
		("AI画像分類テスト", "/ai", ft.icons.SCIENCE),
		("ヘルプ", "/help", ft.icons.HELP_OUTLINE),
		("設定", "/settings", ft.icons.SETTINGS),
	]

	# サイドバーのコンテナを作成（ホバーで展開）
	sidebar_container = ft.Container(
		width=60,  # 初期状態はアイコンのみの幅
		bgcolor=ft.colors.GREY_100,
		padding=5,
		shadow=ft.BoxShadow(
			spread_radius=1,
			blur_radius=15,
			color=ft.colors.BLACK12,
			offset=ft.Offset(2, 2),
		),
		animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
	)
	
	# メニューアイテムを作成
	menu = []
	for text, route, icon in menu_buttons:
		is_current = route == page.route
		menu.append(
			ft.Container(
				content=ft.Row([
					ft.Icon(icon, size=24, color=ft.colors.BLUE_700 if is_current else None),
					ft.Text(text, size=14, weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL, visible=False),
				], spacing=10),
				padding=10,
				border_radius=8,
				ink=True,
				on_click=(lambda r=route: (lambda e: page.go(r)))(),
				bgcolor=ft.colors.BLUE_50 if is_current else None,
			)
		)
	
	# ログイン情報エリア
	if current_user:
		login_icon = ft.Container(
			content=ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=32, color=ft.colors.BLUE_700),
			padding=10,
			border_radius=8,
		)
		login_detail = ft.Column([
			ft.Text(current_user.get("display_name", current_user.get("username")), 
				   size=12, weight=ft.FontWeight.BOLD, visible=False),
			ft.Container(
				content=ft.Text(
					"管理者" if current_user.get("role") == "admin" else "一般",
					size=9,
					color=ft.colors.WHITE
				),
				bgcolor=ft.colors.RED_700 if current_user.get("role") == "admin" else ft.colors.BLUE_700,
				padding=ft.padding.symmetric(horizontal=4, vertical=1),
				border_radius=4,
				visible=False
			),
			ft.TextButton(
				"ログアウト",
				icon=ft.icons.LOGOUT,
				on_click=lambda e: on_logout() if on_logout else None,
				style=ft.ButtonStyle(
					padding=5,
					bgcolor=ft.colors.GREY_700,
					color=ft.colors.WHITE
				),
				visible=False
			),
		], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.START)
	else:
		login_icon = ft.Container(
			content=ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=32, color=ft.colors.GREY_400),
			padding=10,
			border_radius=8,
		)
		login_detail = ft.Column([
			ft.Text("未ログイン", size=10, color=ft.colors.GREY_600, visible=False),
			ft.TextButton(
				"ログイン",
				icon=ft.icons.LOGIN,
				on_click=lambda e: on_login() if on_login else None,
				style=ft.ButtonStyle(
					padding=5,
					bgcolor=ft.colors.BLUE_700,
					color=ft.colors.WHITE
				),
				visible=False
			),
		], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.START)
	
	def expand_sidebar(e):
		"""サイドバーを展開"""
		sidebar_container.width = 280
		# すべてのテキストを表示
		for item in menu:
			if isinstance(item.content, ft.Row):
				for child in item.content.controls:
					if isinstance(child, ft.Text):
						child.visible = True
		# ログイン詳細を表示
		for child in login_detail.controls:
			child.visible = True
		page.update()
	
	def collapse_sidebar(e):
		"""サイドバーを縮小"""
		sidebar_container.width = 60
		# すべてのテキストを非表示
		for item in menu:
			if isinstance(item.content, ft.Row):
				for child in item.content.controls:
					if isinstance(child, ft.Text):
						child.visible = False
		# ログイン詳細を非表示
		for child in login_detail.controls:
			child.visible = False
		page.update()
	
	# サイドバーコンテンツ
	sidebar_content = ft.Column([
		ft.Container(height=10),
		ft.Column(menu, scroll=ft.ScrollMode.AUTO, expand=True, spacing=2),
		ft.Divider(),
		ft.Row([login_icon, login_detail], spacing=10),
		ft.Container(height=10),
	], expand=True, spacing=5)
	
	sidebar_container.content = sidebar_content
	sidebar_container.on_hover = lambda e: expand_sidebar(e) if e.data == "true" else collapse_sidebar(e)
	
	return sidebar_container


def build_sidebar(page: ft.Page, current_user=None, on_login=None, on_logout=None) -> ft.Control:
	"""ホーム画面用：常に展開されたサイドバー"""
	menu_buttons = [
		("ホーム", "/", ft.icons.HOME),
		("拾得物の登録", "/register", ft.icons.NOTE_ADD),
		("遺失物の登録", "/notfound-register", ft.icons.DESCRIPTION),
		("遺失物一覧", "/notfound-list", ft.icons.LIST),
		("還付管理", "/refund", ft.icons.ATTACH_MONEY),
		("警察届け出処理", "/police", ft.icons.GAVEL),
		("統計", "/stats", ft.icons.INSIGHTS),
		("AI画像分類テスト", "/ai", ft.icons.SCIENCE),
		("ヘルプ", "/help", ft.icons.HELP_OUTLINE),
		("設定", "/settings", ft.icons.SETTINGS),
	]

	# サイドバーのコンテナを作成（常に展開状態で固定）
	sidebar_container = ft.Container(
		width=280,  # 常に展開状態
		bgcolor=ft.colors.GREY_100,
		padding=5,
		shadow=ft.BoxShadow(
			spread_radius=1,
			blur_radius=15,
			color=ft.colors.BLACK12,
			offset=ft.Offset(2, 2),
		),
	)
	
	# メニューアイテムを作成
	menu = []
	for text, route, icon in menu_buttons:
		is_current = route == page.route
		menu_item = ft.Container(
			content=ft.Row([
				ft.Icon(icon, size=24, color=ft.colors.BLUE_700 if is_current else None),
				ft.Text(text, size=14, weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL),
			], spacing=10),
			padding=10,
			border_radius=8,
			ink=True,
			on_click=(lambda r=route: (lambda e: page.go(r)))(),
			bgcolor=ft.colors.BLUE_50 if is_current else None,
		)
		menu.append(menu_item)
	
	print(f"build_sidebar: メニュー項目数 = {len(menu)}, current_user = {current_user}")
	for i, item in enumerate(menu):
		print(f"  メニュー{i}: {menu_buttons[i][0]}")
	
	# ログイン情報エリア（常に表示）
	print(f"build_sidebar: ログイン情報構築開始 - current_user = {current_user}")
	if current_user:
		print(f"build_sidebar: ログインユーザー情報 - username={current_user.get('username')}, role={current_user.get('role')}")
		login_section = ft.Container(
			content=ft.Column([
				ft.Row([
					ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=40, color=ft.colors.BLUE_700),
					ft.Column([
						ft.Text(
							current_user.get("display_name", current_user.get("username")), 
							size=14,
							weight=ft.FontWeight.BOLD
						),
						ft.Container(
							content=ft.Text(
								"管理者" if current_user.get("role") == "admin" else "一般ユーザー",
								size=10,
								color=ft.colors.WHITE
							),
							bgcolor=ft.colors.RED_700 if current_user.get("role") == "admin" else ft.colors.BLUE_700,
							padding=ft.padding.symmetric(horizontal=8, vertical=2),
							border_radius=4,
						),
					], spacing=2, expand=True),
				], spacing=10),
				ft.ElevatedButton(
					"ログアウト",
					icon=ft.icons.LOGOUT,
					on_click=lambda e: on_logout() if on_logout else None,
					style=ft.ButtonStyle(
						bgcolor=ft.colors.GREY_700,
						color=ft.colors.WHITE
					),
					expand=True,
				),
			], spacing=10),
			padding=10,
			bgcolor=ft.colors.WHITE,
			border_radius=8,
			border=ft.border.all(1, ft.colors.GREY_300),
		)
		print(f"build_sidebar: ログインセクション構築完了（ログイン済み）")
	else:
		print(f"build_sidebar: 未ログイン状態のログインセクション構築")
		login_section = ft.Container(
			content=ft.Column([
				ft.Row([
					ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=40, color=ft.colors.GREY_400),
					ft.Text("未ログイン", size=14, color=ft.colors.GREY_600, expand=True),
				], spacing=10),
				ft.ElevatedButton(
					"ログイン",
					icon=ft.icons.LOGIN,
					on_click=lambda e: on_login() if on_login else None,
					style=ft.ButtonStyle(
						bgcolor=ft.colors.BLUE_700,
						color=ft.colors.WHITE
					),
					expand=True,
				),
			], spacing=10),
			padding=10,
			bgcolor=ft.colors.WHITE,
			border_radius=8,
			border=ft.border.all(1, ft.colors.GREY_300),
		)
	
	# サイドバーコンテンツ（常に展開状態で固定）
	all_controls = [
		# タイトル
		ft.Text("拾得物管理システム", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
		ft.Divider(height=1, color=ft.colors.GREY_400),
	]
	
	# メニュー項目を追加
	all_controls.extend(menu)
	
	# 下部にログイン情報を追加
	all_controls.extend([
		ft.Divider(height=1, color=ft.colors.GREY_400),
		login_section,
	])
	
	sidebar_content = ft.Column(
		controls=all_controls,
		spacing=2,
		scroll=None,  # スクロール禁止
		expand=True,
	)
	
	sidebar_container.content = sidebar_content
	print(f"build_sidebar: サイドバー構築完了 - 合計コントロール{len(all_controls)}個")
	
	return sidebar_container
