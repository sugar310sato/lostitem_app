import flet as ft
import json
from datetime import date
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"


def get_counts():
	stored = refunded = total = 0
	try:
		conn = sqlite3.connect(str(DB_PATH))
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


def get_today_items():
	items = []
	try:
		conn = sqlite3.connect(str(DB_PATH))
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
					if isinstance(data, dict) and data.get("photos"):
						img_path = (data.get("photos") or [None])[0]
					elif isinstance(data, list) and len(data) > 0:
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


def build_home_content(page: ft.Page) -> ft.Control:
	stored, refunded, total = get_counts()
	actions = ft.Row([
		ft.ElevatedButton(
			"📷 拾得物の登録",
			style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.BLUE_500, color=ft.colors.WHITE),
			on_click=lambda e: page.go("/register"),
		),
		ft.ElevatedButton(
			"🔍 拾得物の検索",
			style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.GREEN_500, color=ft.colors.WHITE),
			on_click=lambda e: page.go("/search"),
		),
	], spacing=16)

	stats = ft.Row([
		ft.Container(ft.Column([ft.Text("保管中"), ft.Text(str(stored), size=26, weight=ft.FontWeight.BOLD)]), bgcolor=ft.colors.RED_400, padding=20, border_radius=12, expand=1),
		ft.Container(ft.Column([ft.Text("返還済み"), ft.Text(str(refunded), size=26, weight=ft.FontWeight.BOLD)]), bgcolor=ft.colors.TEAL_400, padding=20, border_radius=12, expand=1),
		ft.Container(ft.Column([ft.Text("総件数"), ft.Text(str(total), size=26, weight=ft.FontWeight.BOLD)]), bgcolor=ft.colors.BLUE_400, padding=20, border_radius=12, expand=1),
	], spacing=16)

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
		ft.Text("ホーム", size=28, weight=ft.FontWeight.BOLD),
		stats,
		actions,
		ft.Text("本日の拾得物", size=20, weight=ft.FontWeight.BOLD),
		ft.Container(
			content=grid_view,
			expand=True,
			padding=10,
			bgcolor=ft.colors.GREY_50,
			border_radius=12
		),
	], expand=True)


def build_sidebar(page: ft.Page) -> ft.Control:
	menu_buttons = [
		("ホーム", "/", ft.icons.HOME),
		("拾得物の登録", "/register", ft.icons.NOTE_ADD),
		("遺失物管理", "/notfound", ft.icons.INBOX),
		("還付管理", "/refund", ft.icons.ATTACH_MONEY),
		("警察届け出処理", "/police", ft.icons.GAVEL),
		("統計", "/stats", ft.icons.INSIGHTS),
		("AI画像分類テスト", "/ai", ft.icons.SCIENCE),
		("ヘルプ", "/help", ft.icons.HELP_OUTLINE),
		("設定", "/settings", ft.icons.SETTINGS),
	]

	menu = []
	for text, route, icon in menu_buttons:
		menu.append(
			ft.ListTile(
				leading=ft.Icon(icon),
				title=ft.Text(text),
				on_click=(lambda r=route: (lambda e: page.go(r)))(),
			)
		)

	login_area = ft.Column([
		ft.Text("ログイン情報", weight=ft.FontWeight.BOLD),
		ft.Text("未ログイン"),
		ft.ElevatedButton("ログイン", on_click=lambda e: page.snack_bar.open()),
	])

	return ft.Container(
		ft.Column([
			ft.Text("メニュー", size=18, weight=ft.FontWeight.BOLD),
			ft.Column(menu, scroll=ft.ScrollMode.AUTO, expand=True),
			ft.Divider(),
			login_area,
		], expand=True),
		width=280,
		padding=15,
		bgcolor=ft.colors.GREY_100,
		border_radius=8,
		shadow=ft.BoxShadow(
			spread_radius=1,
			blur_radius=15,
			color=ft.colors.BLACK12,
			offset=ft.Offset(2, 2),
		),
	)
