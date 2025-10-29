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
# from flet_pages.ai_classification import AIClassificationView
from flet_pages.search_management import SearchManagementView
from flet_pages.home import build_home_content, build_sidebar, build_sidebar_compact
from flet_pages.items_list import build_items_list_content
from flet_pages.login_page import LoginDialog
from flet_pages.initial_setup import InitialSetupDialog
from flet_pages.settings import SettingsView
from flet_pages.statistics import StatisticsView

# グローバル変数で撮影データとユーザー情報を管理
captured_photos_data = {}
# 開発中のためログインをバイパス - ダミーユーザーを設定
current_user = {
	"id": 999,
	"username": "dev_user",
	"display_name": "開発ユーザー",
	"role": "admin"
}

DB_PATH = Path(__file__).parent / "lostitem.db"

def initialize_database():
	"""データベースの初期化 - 必要なテーブルをすべて作成"""
	try:
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
		cur = conn.cursor()
		
		print("データベース初期化開始...")
		
		# usersテーブル
		cur.execute("""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT UNIQUE NOT NULL,
				password_hash TEXT NOT NULL,
				role TEXT DEFAULT 'user',
				store_name TEXT DEFAULT '未設定',
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
		""")
		
		# lost_itemsテーブル（拾得物）
		cur.execute("""
			CREATE TABLE IF NOT EXISTS lost_items (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				main_id TEXT NOT NULL,
				current_year INTEGER NOT NULL,
				choice_finder TEXT NOT NULL,
				notify TEXT,
				get_item DATE,
				get_item_hour INTEGER,
				get_item_minute INTEGER,
				recep_item DATE,
				recep_item_hour INTEGER,
				recep_item_minute INTEGER,
				recep_manager TEXT,
				find_area TEXT,
				find_area_police TEXT,
				own_waiver TEXT,
				finder_name TEXT,
				own_name_note TEXT,
				finder_age INTEGER,
				finder_sex TEXT,
				finder_post TEXT,
				finder_address TEXT,
				finder_tel1 TEXT,
				finder_tel2 TEXT,
				item_class_L TEXT,
				item_class_M TEXT,
				item_class_S TEXT,
				item_value INTEGER,
				item_feature TEXT,
				item_color TEXT,
				item_storage TEXT,
				item_storage_place TEXT,
				item_maker TEXT,
				item_expiration DATE,
				item_num INTEGER,
				item_unit TEXT,
				item_plice TEXT,
				item_money INTEGER,
				item_remarks TEXT,
				item_image TEXT,
				finder_affiliation TEXT,
				item_situation TEXT DEFAULT '保管中',
				refund_situation TEXT DEFAULT '未',
				card_campany TEXT,
				card_tel TEXT,
				card_name TEXT,
				card_person TEXT,
				thirdparty_waiver TEXT,
				thirdparty_name_note TEXT,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
		""")
		
		# notfound_itemsテーブル（遺失物）
		cur.execute("""
			CREATE TABLE IF NOT EXISTS notfound_items (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				phone TEXT,
				lost_date TEXT,
				location TEXT,
				item TEXT,
				status TEXT DEFAULT '連絡待ち',
				contact_date TEXT,
				return_date TEXT,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
		""")
		
		# settingsテーブル（各種設定）
		cur.execute("""
			CREATE TABLE IF NOT EXISTS settings (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				key TEXT UNIQUE NOT NULL,
				value TEXT,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
		""")
		
		conn.commit()
		conn.close()
		print("データベース初期化完了")
		
	except Exception as e:
		print(f"データベース初期化エラー: {e}")
		import traceback
		traceback.print_exc()

def check_initial_setup_needed():
	"""初回セットアップが必要かどうかをチェック"""
	try:
		conn = sqlite3.connect(str(DB_PATH))
		cur = conn.cursor()
		
		# usersテーブルが存在するかチェック
		cur.execute("""
			SELECT name FROM sqlite_master 
			WHERE type='table' AND name='users'
		""")
		if not cur.fetchone():
			conn.close()
			print("usersテーブルが存在しないため、初期セットアップが必要です")
			return True
		
		# roleカラムが存在するかチェック
		cur.execute("PRAGMA table_info(users)")
		columns = [column[1] for column in cur.fetchall()]
		
		if 'role' not in columns:
			conn.close()
			print("roleカラムが存在しないため、初期セットアップが必要です")
			return True
		
		# 管理者アカウントが存在するかチェック
		try:
			cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
			admin_count = cur.fetchone()[0]
			conn.close()
			
			if admin_count == 0:
				print("管理者アカウントが存在しないため、初期セットアップが必要です")
				return True
			else:
				print(f"管理者アカウントが存在します（count: {admin_count}）")
				return False
		except Exception as e:
			print(f"管理者アカウントチェックエラー: {e}")
			conn.close()
			return True
		
	except Exception as e:
		print(f"初回セットアップチェックエラー: {e}")
		import traceback
		traceback.print_exc()
		return True


def on_camera_complete(photo_data, page):
	"""カメラ撮影完了時の処理"""
	global captured_photos_data
	captured_photos_data = photo_data
	page.go("/register-form")


def get_counts():
	"""DBから件数を取得（なければ0）"""
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


def get_today_items():
	"""本日の拾得物（画像パスと日時）を取得"""
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
			# 画像の決定（JSON/文字列どちらにも対応）
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


def add_store_name_column():
	"""ユーザーテーブルに店舗名カラムを追加"""
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
		conn.close()
	except Exception as e:
		print(f"店舗名カラム追加エラー: {e}")

def main(page: ft.Page):
	page.title = "拾得物管理システム (Flet)"
	page.theme_mode = ft.ThemeMode.LIGHT
	page.padding = 10
	page.transitions = [ft.PageTransitionTheme.NONE]
	page.snack_bar = ft.SnackBar(ft.Text("未実装です"))
	
	# データベースの初期化
	initialize_database()
	
	# データベース構造を更新
	add_store_name_column()
	
	# グローバル変数にアクセス
	global current_user
	
	# ログイン状態を確認（開発中のため無効化）
	def check_login():
		"""ログインチェック"""
		# 開発中はダミーユーザーが設定されているため、常にTrueを返す
		return True
		# if current_user is None:
		#     show_login_dialog()
		#     return False
		# return True
	
	def show_initial_setup_dialog():
		"""初回セットアップダイアログを表示"""
		print("初回セットアップダイアログを表示")
		
		def on_setup_complete(user):
			global current_user
			current_user = user
			print(f"セットアップ完了: {user}")
			
			# ダイアログを閉じる
			page.dialog.open = False
			page.update()
			
			# サイドバーを更新
			page.snack_bar = ft.SnackBar(
				ft.Text(f"セットアップ完了！ようこそ、{user.get('display_name', user.get('username'))}さん"),
				bgcolor=ft.colors.GREEN_700
			)
			page.snack_bar.open = True
			
			# 店舗名を即座に反映させるため、少し遅延してからホーム画面を更新
			import threading
			import time
			def delayed_update():
				time.sleep(0.5)  # 0.5秒待機してから更新
				if page: 
					page.go("/")  # ホーム画面に移動（店舗名が反映される）
			threading.Thread(target=delayed_update, daemon=True).start()
		
		setup_dialog = InitialSetupDialog(on_setup_complete=on_setup_complete)
		# ページを設定
		setup_dialog.page = page
		login_control = setup_dialog.build()
		page.dialog = login_control
		login_control.open = True
		page.update()

	def show_login_dialog():
		"""ログインダイアログを表示"""
		# 現在のルートを保存
		original_route = page.route
		print(f"ログインダイアログ表示: 元のルート = {original_route}")
		
		def on_login_success(user):
			global current_user
			current_user = user
			print(f"ログイン成功: {user}")  # デバッグ用
			
			# ダイアログを閉じる
			page.dialog.open = False
			page.update()
			
			# サイドバーを更新
			page.snack_bar = ft.SnackBar(
				ft.Text(f"ようこそ、{user.get('display_name', user.get('username'))}さん"),
				bgcolor=ft.colors.GREEN_700
			)
			page.snack_bar.open = True
			
			# ログイン成功後、元のページに戻る（route_changeが呼ばれて最新のcurrent_userでサイドバーが再構築される）
			print(f"ログイン後、元のページに戻る: {original_route}")
			page.go(original_route)
		
		login_dialog = LoginDialog(on_login_success=on_login_success)
		# ページを設定
		login_dialog.page = page
		login_control = login_dialog.build()
		page.dialog = login_control
		login_control.open = True
		page.update()
	
	def logout():
		"""ログアウト"""
		global current_user
		current_user = None
		page.snack_bar = ft.SnackBar(ft.Text("ログアウトしました"), bgcolor=ft.colors.BLUE_700)
		page.snack_bar.open = True
		# ログアウト後、ホームに戻る（route_changeが呼ばれて最新のcurrent_userでサイドバーが再構築される）
		page.go("/")

	def generate_main_id(choice_finder: str, current_year: int) -> str:
		try:
			conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
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
		try:
			print(f"save_lost_item called with form_data: {form_data.keys()}")
			from datetime import datetime as _dt
			import os
			current_year = _dt.now().year % 100
			choice = form_data.get("finder_type") or "占有者拾得"
			main_id = generate_main_id(choice, current_year)
			
			# 撮影データの処理（register_form.py の collect() メソッドから "captured_photos" というキーで渡される）
			captured_photos = form_data.get("captured_photos", {})
			saved_photo_paths = {"main_photos": [], "sub_photos": [], "bundle_photos": []}
			
			# 画像保存ディレクトリの作成
			images_dir = Path(__file__).parent / "images"
			images_dir.mkdir(exist_ok=True)
			
			print(f"captured_photos: {captured_photos}")
			
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
							print(f"メイン写真を保存しました: {filepath}")
						except Exception as e:
							print(f"メイン写真保存エラー: {e}")
			
			# サブ写真の保存
			if captured_photos and captured_photos.get("sub_photos"):
				for i, photo_data in enumerate(captured_photos.get("sub_photos", [])):
					if photo_data and "frame" in photo_data:
						try:
							frame = photo_data["frame"]
							timestamp = photo_data.get("timestamp", "")
							filename = f"sub_{main_id}_{i+1}_{timestamp}.jpg"
							filepath = images_dir / filename
							
							# OpenCVで画像を保存
							import cv2
							cv2.imwrite(str(filepath), frame)
							saved_photo_paths["sub_photos"].append(str(filepath))
							print(f"サブ写真を保存しました: {filepath}")
						except Exception as e:
							print(f"サブ写真保存エラー: {e}")
			
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
							print(f"同梱物写真を保存しました: {filepath}")
						except Exception as e:
							print(f"同梱物写真保存エラー: {e}")
			
			# 保存されたパスをデバッグ出力
			print(f"保存された写真パス: {saved_photo_paths}")
			
			conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
			cur = conn.cursor()
			
			# lost_itemsテーブルが存在するかチェックし、存在しない場合は作成
			cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lost_items'")
			if not cur.fetchone():
				cur.execute("""
					CREATE TABLE IF NOT EXISTS lost_items (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						main_id TEXT,
						current_year INTEGER,
						choice_finder TEXT,
						notify TEXT,
						get_item TEXT,
						get_item_hour INTEGER,
						get_item_minute INTEGER,
						recep_item TEXT,
						recep_item_hour INTEGER,
						recep_item_minute INTEGER,
						recep_manager TEXT,
						find_area TEXT,
						find_area_police TEXT,
						finder_name TEXT,
						finder_age INTEGER,
						finder_sex TEXT,
						finder_post TEXT,
						finder_address TEXT,
						finder_tel1 TEXT,
						finder_tel2 TEXT,
						finder_affiliation TEXT,
						item_class_L TEXT,
						item_class_M TEXT,
						item_class_S TEXT,
						item_feature TEXT,
						item_color TEXT,
						item_storage TEXT,
						item_storage_place TEXT,
						item_maker TEXT,
						item_expiration TEXT,
						item_num INTEGER,
						item_unit TEXT,
						item_value INTEGER,
						item_money TEXT,
						item_remarks TEXT,
						item_image TEXT,
						item_situation TEXT,
						refund_situation TEXT,
						created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
					)
				""")
				conn.commit()
				print("lost_itemsテーブルを作成しました")
			
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
			# JSONデータを作成
			image_json = json.dumps(saved_photo_paths, ensure_ascii=False) if saved_photo_paths else "{}"
			print(f"データベースに保存するJSONデータ: {image_json}")
			
			# 時刻データの変換（"時"、"分"を削除して数値に変換）
			get_hour = form_data.get("get_hour", "0")
			get_min = form_data.get("get_min", "0")
			recep_hour = form_data.get("recep_hour", "0")
			recep_min = form_data.get("recep_min", "0")
			
			# 数値に変換
			try:
				get_hour_int = int(get_hour.replace("時", "")) if get_hour else 0
				get_min_int = int(get_min.replace("分", "")) if get_min else 0
				recep_hour_int = int(recep_hour.replace("時", "")) if recep_hour else 0
				recep_min_int = int(recep_min.replace("分", "")) if recep_min else 0
			except:
				get_hour_int = 0
				get_min_int = 0
				recep_hour_int = 0
				recep_min_int = 0
			
			data = (
				main_id, current_year, choice, "",
				form_data.get("get_date"), get_hour_int, get_min_int,
				form_data.get("recep_date"), recep_hour_int, recep_min_int,
				None,
				form_data.get("find_place"), None,
				form_data.get("finder_name"),
				None,
				form_data.get("gender"), form_data.get("postal_code"),
				form_data.get("address"), form_data.get("tel1"), form_data.get("tel2"),
				form_data.get("owner_affiliation"),
				form_data.get("item_class_L"), form_data.get("item_class_M"),
				form_data.get("item_class_S"), form_data.get("feature"), form_data.get("color"),
				form_data.get("storage_place"), None, None,
				None, 1, "個",
				0, "", "",
				image_json,
				"保管中", "未",
			)
			cur.execute(sql, data)
			conn.commit()
			conn.close()
			
			# 成功メッセージを表示
			print(f"拾得物を登録しました (ID: {main_id})")
			
			# ページに成功メッセージを表示
			if page:
				page.snack_bar = ft.SnackBar(
					content=ft.Text("拾得物を登録しました", color=ft.colors.WHITE),
					bgcolor=ft.colors.GREEN_700
				)
				page.snack_bar.open = True
				page.update()
				
		except Exception as e:
			print(f"データベース保存エラー: {e}")
			import traceback
			traceback.print_exc()
			if page:
				page.snack_bar = ft.SnackBar(
					content=ft.Text(f"エラー: {str(e)}", color=ft.colors.WHITE),
					bgcolor=ft.colors.RED_700
				)
				page.snack_bar.open = True
				page.update()
			raise e

	def save_notfound_item_to_db(form_data: dict):
		try:
			print(f"save_notfound_item_to_db called with form_data: {form_data.keys()}")
			conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
			cursor = conn.cursor()
			
			# notfound_itemsテーブルが存在するかチェックし、存在しない場合は作成
			cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notfound_items'")
			if not cursor.fetchone():
				cursor.execute("""
					CREATE TABLE IF NOT EXISTS notfound_items (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						name TEXT NOT NULL,
						phone TEXT,
						lost_date TEXT,
						location TEXT,
						item TEXT,
						status TEXT DEFAULT '連絡待ち',
						contact_date TEXT,
						return_date TEXT,
						created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
						updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
					)
				""")
				conn.commit()
				print("notfound_itemsテーブルを作成しました")
			
			# 遺失日時の結合
			lost_date_str = form_data.get("lost_date", "")
			lost_hour = form_data.get("lost_hour", "00")
			lost_min = form_data.get("lost_min", "00")
			
			# 時刻データの正規化
			try:
				lost_hour_clean = lost_hour.replace("時", "") if lost_hour else "00"
				lost_min_clean = lost_min.replace("分", "") if lost_min else "00"
				if lost_date_str:
					lost_datetime = f"{lost_date_str} {lost_hour_clean.zfill(2)}:{lost_min_clean.zfill(2)}:00"
				else:
					lost_datetime = ""
			except:
				lost_datetime = lost_date_str
			
			sql = '''
				INSERT INTO notfound_items (
					name, phone, lost_date, location, item, status
				) VALUES (?, ?, ?, ?, ?, ?)
			'''
			
			# 品物情報の結合（貴重品名 + 内容）
			valuables_name = form_data.get("valuables_name", "")
			valuables_content = form_data.get("valuables_content", "")
			item_description = f"{valuables_name} - {valuables_content}".strip(" -")
			
			data = (
				form_data.get("customer_name", ""),      # name
				form_data.get("customer_tel", ""),       # phone
				lost_datetime,                            # lost_date
				form_data.get("lost_place", ""),         # location
				item_description,                         # item
				"連絡待ち"                                # status (デフォルト)
			)
			
			cursor.execute(sql, data)
			conn.commit()
			conn.close()
			
			# 成功メッセージを表示
			if page:
				page.snack_bar = ft.SnackBar(
					content=ft.Text("遺失物を登録しました", color=ft.colors.WHITE),
					bgcolor=ft.colors.GREEN_700
				)
				page.snack_bar.open = True
				page.update()
		except Exception as e:
			print(f"遺失物登録エラー: {e}")
			import traceback
			traceback.print_exc()
			if page:
				page.snack_bar = ft.SnackBar(
					content=ft.Text(f"エラー: {str(e)}", color=ft.colors.WHITE),
					bgcolor=ft.colors.RED_700
				)
				page.snack_bar.open = True
				page.update()
			raise e

	def save_refund_item_to_db(form_data: dict):
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
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
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
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
		conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
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

	def route_change(route):
		print(f"route_change: {page.route} - current_user: {current_user.get('username') if current_user else 'None'}")
		page.views.clear()
		
		# ログインが必要なページのチェック（開発中のため無効化）
		login_required_routes = ["/register", "/register-form", "/notfound", "/notfound-list", "/refund", "/police", "/search", "/settings", "/statistics"]
		if False and page.route in login_required_routes and not current_user:  # 開発中はログインチェックを無効化
			print(f"ログインが必要なページにアクセス: {page.route}")
			# まずホーム画面を表示
			page.views.append(
				ft.View(
					"/",
					[
						ft.Row([
							build_sidebar(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=build_home_content(page, current_user=current_user),
								expand=True,
							),
						], expand=True)
					],
				)
			)
			# ログインダイアログを表示
			show_login_dialog()
			return
		
		if page.route == "/":
			# ホーム画面
			page.views.append(
				ft.View(
					"/",
					[
						ft.Row([
							build_sidebar(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=build_home_content(page, current_user=current_user),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/register":
			# 拾得物登録画面（カメラ撮影から開始）
			print("register画面を表示中...")
			page.views.append(
				ft.View(
					"/register",
					[
						ft.Row([
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
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
			print("register-form画面を表示中...")
			try:
				register_form = RegisterFormView(
					on_submit=save_lost_item,
					on_temp_save=lambda data: print("一時保存:", data),
					on_back_to_camera=lambda: page.go("/register"),
					captured_photos_data=captured_photos_data
				)
				print("RegisterFormView作成成功")
				
				# アカウント情報を設定
				if current_user:
					print(f"ユーザー情報を設定: {current_user}")
					# store_nameとstaffの値を設定
					if hasattr(register_form, 'store_name'):
						register_form.store_name.value = current_user.get('store_name', '未設定')
						register_form.store_name.update()
					if hasattr(register_form, 'staff'):
						register_form.staff.value = current_user.get('display_name', current_user.get('username', '未設定'))
						register_form.staff.update()
				else:
					print("ユーザー情報なし")
				
				page.views.append(
					ft.View(
						"/register-form",
						[
							ft.Row([
								build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
								ft.VerticalDivider(width=1),
								ft.Container(
									content=register_form,
									expand=True,
								),
							], expand=True)
						],
					)
				)
			except Exception as e:
				print(f"RegisterFormView作成エラー: {e}")
				import traceback
				traceback.print_exc()
				# エラーが発生した場合でもページを表示
				page.views.append(
					ft.View(
						"/register-form",
						[
							ft.Row([
								build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
								ft.VerticalDivider(width=1),
								ft.Container(
									content=ft.Column([
										ft.Icon(ft.icons.ERROR_OUTLINE, size=100, color=ft.colors.RED_400),
										ft.Text("エラーが発生しました", size=24, weight=ft.FontWeight.BOLD),
										ft.Text(f"エラー詳細: {str(e)}", size=16, color=ft.colors.GREY_600),
										ft.ElevatedButton(
											"ホームに戻る",
											on_click=lambda e: page.go("/"),
											icon=ft.icons.HOME
										)
									], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
									alignment=ft.alignment.center,
									expand=True
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
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
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
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
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
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
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
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
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
			# AI画像分類テスト画面（一時的に無効化）
			page.views.append(
				ft.View(
					"/ai",
					[
						ft.Container(
							content=ft.Column([
								ft.Icon(ft.icons.WARNING, size=100, color=ft.colors.ORANGE_400),
								ft.Text("AI画像分類機能は一時的に無効化されています", size=18, weight=ft.FontWeight.BOLD),
								ft.Text("エクスポート環境での動作を確認中です", size=14, color=ft.colors.GREY_600),
								ft.ElevatedButton("ホームに戻る", on_click=lambda e: page.go("/"))
							], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, expand=True),
							alignment=ft.alignment.center,
							expand=True,
							bgcolor=ft.colors.GREY_100
						)
					],
				)
			)
		elif page.route == "/items":
			# 拾得物一覧画面
			page.views.append(
				ft.View(
					"/items",
					[
						ft.Row([
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=build_items_list_content(page),
								expand=True,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/settings":
			# 設定画面
			print("settings画面を表示中...")
			print(f"設定画面用ユーザー情報: {current_user}")
			try:
				settings_view = SettingsView(current_user=current_user)
				print("SettingsView作成成功")
				
				page.views.append(
					ft.View(
						"/settings",
						[
							ft.Row([
								build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
								ft.VerticalDivider(width=1),
								ft.Container(
									content=settings_view,
									expand=True,
								),
							], expand=True)
						],
					)
				)
			except Exception as e:
				print(f"SettingsView作成エラー: {e}")
				import traceback
				traceback.print_exc()
				# エラーが発生した場合でもページを表示
				page.views.append(
					ft.View(
						"/settings",
						[
							ft.Row([
								build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
								ft.VerticalDivider(width=1),
								ft.Container(
									content=ft.Column([
										ft.Icon(ft.icons.ERROR_OUTLINE, size=100, color=ft.colors.RED_400),
										ft.Text("エラーが発生しました", size=24, weight=ft.FontWeight.BOLD),
										ft.Text(f"エラー詳細: {str(e)}", size=16, color=ft.colors.GREY_600),
										ft.ElevatedButton(
											"ホームに戻る",
											on_click=lambda e: page.go("/"),
											icon=ft.icons.HOME
										)
									], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
									alignment=ft.alignment.center,
									expand=True
								),
							], expand=True)
						],
					)
				)
		elif page.route == "/stats":
			# 統計画面
			stats_view = StatisticsView()
			page.views.append(
				ft.View(
					"/stats",
					[
						ft.Row([
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=stats_view,
								expand=True,
								bgcolor=ft.colors.GREY_50,
							),
						], expand=True)
					],
				)
			)
		elif page.route == "/notfound-register":
			# 遺失物登録画面
			from flet_pages.notfound_registration import NotFoundRegistrationView
			
			def on_notfound_submit(form_data):
				"""遺失物登録データを保存"""
				try:
					# データベースに保存
					conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
					cur = conn.cursor()
					
					# 遺失日時を結合
					lost_datetime = f"{form_data.get('lost_date', '')} {form_data.get('lost_hour', '00')}:{form_data.get('lost_min', '00')}:00"
					
					sql = '''
						INSERT INTO notfound_items (
							name, phone, lost_date, location, item, status
						) VALUES (?, ?, ?, ?, ?, ?)
					'''
					
					data = (
						form_data.get("customer_name"),
						form_data.get("customer_tel"),
						lost_datetime,
						form_data.get("lost_place"),
						form_data.get("item_info"),
						'連絡待ち'
					)
					cur.execute(sql, data)
					conn.commit()
					conn.close()
					
					# 成功メッセージ
					page.snack_bar = ft.SnackBar(
						content=ft.Text("遺失物を登録しました", color=ft.colors.WHITE),
						bgcolor=ft.colors.GREEN_700
					)
					page.snack_bar.open = True
					
					# ホームに戻る
					import threading
					import time
					def go_home():
						time.sleep(1.0)
						if page:
							page.go("/")
					threading.Thread(target=go_home, daemon=True).start()
					
					page.update()
				except Exception as e:
					print(f"遺失物登録エラー: {e}")
					page.snack_bar = ft.SnackBar(
						content=ft.Text(f"エラー: {e}", color=ft.colors.WHITE),
						bgcolor=ft.colors.RED_700
					)
					page.snack_bar.open = True
					page.update()
			
			notfound_view = NotFoundRegistrationView(
				on_submit=on_notfound_submit,
				on_cancel=lambda: page.go("/")
			)
			
			page.views.append(
				ft.View(
					"/notfound-register",
					[
						ft.Row([
							build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
							ft.VerticalDivider(width=1),
							ft.Container(
								content=notfound_view,
								expand=True,
								bgcolor=ft.colors.GREY_50,
							),
						], expand=True)
					],
				)
			)
		
		elif page.route == "/notfound-list":
			# 遺失物一覧画面
			print("notfound-list画面を表示中...")
			try:
				from flet_pages.notfound_list import build_notfound_list_content
				notfound_list_content = build_notfound_list_content(page)
				
				page.views.append(
					ft.View(
						"/notfound-list",
						[
							ft.Row([
								build_sidebar_compact(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
								ft.VerticalDivider(width=1),
								ft.Container(
									content=notfound_list_content,
									expand=True,
								),
							], expand=True)
						],
					)
				)
			except Exception as e:
				print(f"notfound-list画面表示エラー: {e}")
				page.views.append(
					ft.View(
						"/notfound-list",
						[
							ft.Container(
								content=ft.Column([
									ft.Icon(ft.icons.ERROR_OUTLINE, size=100, color=ft.colors.RED_400),
									ft.Text("遺失物一覧の読み込み中にエラーが発生しました", size=18, weight=ft.FontWeight.BOLD),
									ft.Text(f"エラー: {str(e)}", size=14, color=ft.colors.GREY_600),
									ft.ElevatedButton("ホームに戻る", on_click=lambda e: page.go("/"))
								], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
								alignment=ft.alignment.center,
								expand=True
							)
						],
					)
				)
		
		else:
			# デフォルトのルート処理（404エラー）
			print(f"未知のルート: {page.route}")
			page.views.append(
				ft.View(
					page.route,
					[
						ft.Container(
							content=ft.Column([
								ft.Icon(ft.icons.ERROR_OUTLINE, size=100, color=ft.colors.RED_400),
								ft.Text("ページが見つかりません", size=24, weight=ft.FontWeight.BOLD),
								ft.Text(f"ルート: {page.route}", size=16, color=ft.colors.GREY_600),
								ft.ElevatedButton(
									"ホームに戻る",
									on_click=lambda e: page.go("/"),
									icon=ft.icons.HOME
								)
							], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
							alignment=ft.alignment.center,
							expand=True
						)
					]
				)
			)
		
		# 画面を更新
		try:
			page.update()
			print(f"route_change: 完了 - {page.route}")
		except Exception as ue:
			print(f"route_change: エラー: {ue}")
			import traceback
			traceback.print_exc()

	# ルーティング設定
	page.on_route_change = route_change
	
	# 初期表示（route_changeでレイアウトが構築される）
	page.go(page.route or "/")
	
	# 初期表示時にセットアップまたはログインをチェック（開発中のため無効化）
	# 開発中はダミーユーザーが設定されているため、セットアップ・ログインチェックをスキップ
	print("開発モード: ログイン認証をバイパス中")
	# if current_user is None:
	#     if check_initial_setup_needed():
	#         print("初回セットアップが必要です")
	#         show_initial_setup_dialog()
	#     else:
	#         print("ログインが必要です")
	#         show_login_dialog()


if __name__ == "__main__":
	ft.app(target=main)
