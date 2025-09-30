import flet as ft
from pathlib import Path
import sqlite3
import json
from datetime import date
from flet_pages.camera_form import CameraFormView
from flet_pages.register_form import RegisterFormView
from flet_pages.notfound_management import NotFoundManagementView
from flet_pages.refund_management import RefundManagementView
from flet_pages.police_management import PoliceManagementView
from flet_pages.ai_classification import AIClassificationView
from flet_pages.search_management import SearchManagementView
from flet_pages.home import build_home_content, build_sidebar

# グローバル変数で撮影データを管理
captured_photos_data = {}

DB_PATH = Path(__file__).parent / "lostitem.db"


def on_camera_complete(photo_data, page):
	"""カメラ撮影完了時の処理"""
	global captured_photos_data
	captured_photos_data = photo_data
	page.go("/register-form")


def get_counts():
	"""DBから件数を取得（なければ0）"""
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
	"""本日の拾得物（画像パスと日時）を取得"""
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
			# 画像の決定（JSON/文字列どちらにも対応）
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


def main(page: ft.Page):
	page.title = "拾得物管理システム (Flet)"
	page.theme_mode = ft.ThemeMode.LIGHT
	page.padding = 10
	page.snack_bar = ft.SnackBar(ft.Text("未実装です"))

	def generate_main_id(choice_finder: str, current_year: int) -> str:
		try:
			conn = sqlite3.connect(str(DB_PATH))
			cur = conn.cursor()
			cur.execute(
				"SELECT COUNT(*) FROM lost_items WHERE choice_finder = ? AND current_year = ?",
				(choice_finder, current_year),
			)
			count = cur.fetchone()[0]
			conn.close()
		except Exception:
			count = 0
		prefix = "1" if choice_finder == "占有者拾得" else "2"
		return f"{prefix}{current_year:02}{count+1:05}"

	def save_lost_item(form_data: dict) -> None:
		from datetime import datetime as _dt
		import os
		current_year = _dt.now().year % 100
		choice = form_data.get("finder_type") or "占有者拾得"
		main_id = generate_main_id(choice, current_year)
		
		# 撮影データの処理
		captured_photos = form_data.get("captured_photos_data", {})
		saved_photo_paths = {"main_photos": [], "bundle_photos": []}
		
		# 画像保存ディレクトリの作成
		images_dir = Path(__file__).parent / "images"
		images_dir.mkdir(exist_ok=True)
		
		# メイン写真の保存
		if captured_photos and captured_photos.get("main_photos"):
			for i, photo_data in enumerate(captured_photos.get("main_photos", [])):
				if photo_data and "frame" in photo_data:
					try:
						frame = photo_data["frame"]
						timestamp = photo_data.get("timestamp", "")
						filename = f"main_{main_id}_{i+1}_{timestamp}.jpg"
						filepath = images_dir / filename
						
						# OpenCVで画像を保存
						import cv2
						cv2.imwrite(str(filepath), frame)
						saved_photo_paths["main_photos"].append(str(filepath))
					except Exception as e:
						print(f"メイン写真保存エラー: {e}")
		
		# 同梱物写真の保存
		if captured_photos and captured_photos.get("bundle_photos"):
			for i, photo_data in enumerate(captured_photos.get("bundle_photos", [])):
				if photo_data and "frame" in photo_data:
					try:
						frame = photo_data["frame"]
						timestamp = photo_data.get("timestamp", "")
						filename = f"bundle_{main_id}_{i+1}_{timestamp}.jpg"
						filepath = images_dir / filename
						
						# OpenCVで画像を保存
						import cv2
						cv2.imwrite(str(filepath), frame)
						saved_photo_paths["bundle_photos"].append(str(filepath))
					except Exception as e:
						print(f"同梱物写真保存エラー: {e}")
		
		try:
			conn = sqlite3.connect(str(DB_PATH))
			cur = conn.cursor()
			sql = '''
				INSERT INTO lost_items (
					main_id, current_year, choice_finder, notify,
					get_item, get_item_hour, get_item_minute,
					recep_item, recep_item_hour, recep_item_minute,
					recep_manager, find_area, find_area_police,
					finder_name, finder_age, finder_sex, finder_post,
					finder_address, finder_tel1, finder_tel2,
					finder_affiliation, item_class_L, item_class_M,
					item_class_S, item_feature, item_color,
					item_storage, item_storage_place, item_maker,
					item_expiration, item_num, item_unit,
					item_value, item_money, item_remarks,
					item_image, item_situation, refund_situation
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			'''
			data = (
				main_id, current_year, choice, "",
				form_data.get("get_date"), int(form_data.get("get_hour") or 0), int(form_data.get("get_min") or 0),
				form_data.get("recep_date"), int(form_data.get("recep_hour") or 0), int(form_data.get("recep_min") or 0),
				None,
				form_data.get("find_place"), None,
				form_data.get("finder_name"),  # 修正: finder_nameを直接使用
				None,
				form_data.get("gender"), form_data.get("postal_code"),
				form_data.get("address"), form_data.get("tel1"), form_data.get("tel2"),
				form_data.get("owner_affiliation"),
				form_data.get("item_class_L"), form_data.get("item_class_M"),
				form_data.get("item_class_S"), form_data.get("feature"), form_data.get("color"),
				form_data.get("storage_place"), None, None,
				None, 1, "個",
				0, 0, "",
				json.dumps(saved_photo_paths, ensure_ascii=False) if saved_photo_paths else "{}",
				"保管中", "未",
			)
			cur.execute(sql, data)
			conn.commit()
			conn.close()
			
			# 成功メッセージを表示
			print("拾得物を登録しました")
				
		except Exception as e:
			print(f"データベース保存エラー: {e}")
			raise e

	def save_notfound_item_to_db(form_data: dict):
		conn = sqlite3.connect(str(DB_PATH))
		cursor = conn.cursor()
		
		sql = '''
			INSERT INTO notfound (
				lost_item, lost_item_hour, lost_item_minute,
				recep_item, recep_item_hour, recep_item_minute,
				recep_manager, lost_area, lost_name, lost_age,
				lost_sex, lost_post, lost_address, lost_tel1, lost_tel2,
				item_value, item_feature, item_color, item_maker,
				item_expiration, item_num, item_unit, item_price,
				item_money, item_remarks, item_class_L, item_class_M,
				item_class_S, card_company, card_tel, card_name,
				card_person, card_contact_date, card_return_date,
				card_contact_hour, card_contact_minute, card_manager,
				item_situation
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		'''
		
		data = (
			form_data.get("lost_date"), form_data.get("lost_hour"), form_data.get("lost_min"),
			form_data.get("recep_date"), form_data.get("recep_hour"), form_data.get("recep_min"),
			form_data.get("recep_manager"), form_data.get("lost_area"), form_data.get("lost_name"), form_data.get("lost_age"),
			form_data.get("lost_sex"), form_data.get("lost_post"), form_data.get("lost_address"), form_data.get("lost_tel1"), form_data.get("lost_tel2"),
			form_data.get("item_value"), form_data.get("item_feature"), form_data.get("item_color"), form_data.get("item_maker"),
			form_data.get("item_expiration"), form_data.get("item_num"), form_data.get("item_unit"), form_data.get("item_price"),
			form_data.get("item_money"), form_data.get("item_remarks"), form_data.get("item_class_L"), form_data.get("item_class_M"),
			form_data.get("item_class_S"), form_data.get("card_company"), form_data.get("card_tel"), form_data.get("card_name"),
			form_data.get("card_person"), form_data.get("card_contact_date"), form_data.get("card_return_date"),
			form_data.get("card_contact_hour"), form_data.get("card_contact_min"), form_data.get("card_manager"),
			"未対応"
		)
		
		cursor.execute(sql, data)
		conn.commit()
		conn.close()
		
		# 成功メッセージを表示
		if page:
			page.snack_bar.content = ft.Text("遺失物を登録しました")
			page.snack_bar.open = True
			page.go("/")

	def save_refund_item_to_db(form_data: dict):
		conn = sqlite3.connect(str(DB_PATH))
		cursor = conn.cursor()
		
		# 還付管理の処理を実装
		# ここでは基本的な情報をログに出力
		print("還付管理データ:", form_data)
		
		# 成功メッセージを表示
		if page:
			page.snack_bar.content = ft.Text("還付管理情報を保存しました")
			page.snack_bar.open = True
			page.go("/")
		
		conn.close()

	def save_police_item_to_db(form_data: dict):
		conn = sqlite3.connect(str(DB_PATH))
		cursor = conn.cursor()
		
		# 警察届け出処理の処理を実装
		# ここでは基本的な情報をログに出力
		print("警察届け出処理データ:", form_data)
		
		# 成功メッセージを表示
		if page:
			page.snack_bar.content = ft.Text("警察届け出処理情報を保存しました")
			page.snack_bar.open = True
			page.go("/")
		
		conn.close()

	def save_ai_classification_data(form_data: dict):
		conn = sqlite3.connect(str(DB_PATH))
		cursor = conn.cursor()
		
		# AI画像分類テストの処理を実装
		# ここでは基本的な情報をログに出力
		print("AI画像分類テストデータ:", form_data)
		
		# 成功メッセージを表示
		if page:
			page.snack_bar.content = ft.Text("AI画像分類テスト情報を保存しました")
			page.snack_bar.open = True
			page.go("/")
		
		conn.close()

	# 右側メインエリアのコンテナ（ルーティングで差し替え）
	main_container = ft.Container(expand=True)

	def route_change(route):
		page.views.clear()
		if page.route == "/":
			# ホーム画面
			page.views.append(
				ft.View(
					"/",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=build_home_content(page),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/register":
			# 拾得物登録画面（カメラ撮影から開始）
			page.views.append(
				ft.View(
					"/register",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=CameraFormView(
									on_capture_complete=lambda photo_data: on_camera_complete(photo_data, page),
									on_back=lambda: page.go("/")
								),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/register-form":
			# フォーム入力画面
			page.views.append(
				ft.View(
					"/register-form",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=RegisterFormView(
									on_submit=save_lost_item,
									on_temp_save=lambda data: print("一時保存:", data),
									on_back_to_camera=lambda: page.go("/register"),
									captured_photos_data=captured_photos_data
								),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/notfound":
			# 遺失物管理画面
			page.views.append(
				ft.View(
					"/notfound",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=NotFoundManagementView(
									on_submit=save_notfound_item_to_db,
									on_temp_save=lambda data: print("一時保存:", data)
								),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/refund":
			# 還付管理画面
			page.views.append(
				ft.View(
					"/refund",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=RefundManagementView(
									on_submit=save_refund_item_to_db,
									on_temp_save=lambda data: print("一時保存:", data)
								),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/police":
			# 警察届け出処理画面
			page.views.append(
				ft.View(
					"/police",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=PoliceManagementView(
									on_submit=save_police_item_to_db,
									on_temp_save=lambda data: print("一時保存:", data)
								),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/search":
			# 拾得物検索画面
			page.views.append(
				ft.View(
					"/search",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=SearchManagementView(),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/ai":
			# AI画像分類テスト画面
			page.views.append(
				ft.View(
					"/ai",
					[
						ft.Row([
							build_sidebar(page),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=AIClassificationView(
									on_submit=save_ai_classification_data,
									on_temp_save=lambda data: print("一時保存:", data)
								),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		page.update()

	# 初期レイアウト: 左サイド + 右メイン
	layout = ft.Row([
		build_sidebar(page),
		main_container,
	], expand=True)

	page.on_route_change = route_change
	page.add(layout)
	page.go(page.route or "/")


if __name__ == "__main__":
	ft.app(target=main)
