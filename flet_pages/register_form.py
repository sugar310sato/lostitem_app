import flet as ft
from datetime import datetime, date
import requests
import cv2
import base64
import io
import json
from pathlib import Path
from PIL import Image
from apps.config import OWN_WAIVER, NOTE, COLOR, STORAGE_PLACE, ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S, REPORT_NECESSITY, STORE
from flet_pages.money_registration import MoneyRegistrationView

MINUTES_15 = ["00", "15", "30", "45"]
HOURS = [f"{h:02d}" for h in range(0, 24)]




def nearest_15min(dt: datetime):
	m = dt.minute
	closest = min([0, 15, 30, 45], key=lambda x: abs(x - m))
	return f"{dt.hour:02d}", f"{closest:02d}"






class RegisterFormView(ft.UserControl):
	"""フォーム入力専用ビュー"""
	def __init__(self, on_submit=None, on_temp_save=None, on_back_to_camera=None, captured_photos_data=None, existing_data=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_temp_save = on_temp_save
		self.on_back_to_camera = on_back_to_camera
		self.get_date_value = date.today().isoformat()
		self.recep_date_value = date.today().isoformat()
		self.expiry_date_value = None
		self._date_pickers_added = False
		# 日付表示用のTextコントロール
		self.get_date_text = None
		self.recep_date_text = None
		self.expiry_date_text = None
		# ダイアログ管理
		self.current_dialog = None
		
		# カメラ撮影データ
		self.captured_photos_data = captured_photos_data or {}
		
		# 既存データ（編集時）
		self.existing_data = existing_data or {}
		
		# バリデーション状態を保持
		self.validation_states = {}
		# エラーメッセージ表示用のTextコントロール
		self.error_texts = {}
		
		# 金種登録データ
		self.money_data = {}
		self.is_money_mode = False  # 金種登録モードかどうか
		
		# 現在の画面モード（"form" or "money"）
		self.current_screen = "form"
		
		# 金種登録ボタンの参照
		self.money_button_container = None
		
		# エラーメッセージ表示用
		self.error_banner = None
		
		# 分類データの読み込み
		self.classification_data = self._load_classification_data()
		
		# 拾得場所データの読み込み
		self.find_places_data = self._load_find_places()
		
		# 保管場所データの読み込み
		self.storage_places_data = self._load_storage_places()
	
	def build(self):
		# 初回はフォーム画面を表示
		# 金種登録画面はopen_money_registration()で別途設定される
		form_view = self.create_form_view()
		
		# 既存データがある場合はフォームに設定
		if self.existing_data:
			self._load_existing_data()
		
		return form_view
	
	def _load_existing_data(self):
		"""既存データをフォームに読み込む"""
		data = self.existing_data
		print(f"Loading existing data: {data}")
		
		# AI分類結果がある場合は適用
		self._apply_ai_classification()
		
		# 基本情報（choice_finder -> finder_type）
		if data.get("choice_finder"):
			self.finder_type.value = data["choice_finder"]
		
		# 日付・時刻の処理
		if data.get("get_item"):
			# 日付文字列を処理
			date_str = str(data["get_item"])
			if "T" in date_str:
				date_str = date_str.split("T")[0]
			self.get_date_value = date_str
			self.get_date_field.value = date_str.replace("-", "/")
		
		# 時刻の処理（数値で保存されている場合）
		if data.get("get_item_hour") is not None:
			hour_val = str(data["get_item_hour"]).zfill(2)
			self.get_hour.value = hour_val + "時"
		if data.get("get_item_minute") is not None:
			min_val = str(data["get_item_minute"]).zfill(2)
			self.get_min.value = min_val + "分"
		
		if data.get("recep_item"):
			# 受付日付の処理
			date_str = str(data["recep_item"])
			if "T" in date_str:
				date_str = date_str.split("T")[0]
			self.recep_date_value = date_str
			self.recep_date_field.value = date_str.replace("-", "/")
		
		if data.get("recep_item_hour") is not None:
			hour_val = str(data["recep_item_hour"]).zfill(2)
			self.recep_hour.value = hour_val + "時"
		if data.get("recep_item_minute") is not None:
			min_val = str(data["recep_item_minute"]).zfill(2)
			self.recep_min.value = min_val + "分"
		
		# 拾得場所（find_area）
		if data.get("find_area"):
			self.find_place.value = str(data["find_area"])
		
		# 拾得者情報
		if data.get("finder_name"):
			self.finder_name.value = str(data["finder_name"])
		if data.get("finder_sex"):  # gender -> finder_sex
			self.gender.value = str(data["finder_sex"])
		if data.get("finder_age"):  # age -> finder_age
			self.age.value = str(data["finder_age"])
		if data.get("finder_address"):  # address -> finder_address
			self.address.value = str(data["finder_address"])
		if data.get("finder_post"):  # postal_code -> finder_post
			self.postal_code.value = str(data["finder_post"])
		if data.get("finder_tel1"):  # tel1 -> finder_tel1
			self.tel1.value = str(data["finder_tel1"])
		if data.get("finder_tel2"):  # tel2 -> finder_tel2
			self.tel2.value = str(data["finder_tel2"])
		
		# 住所不明チェックボックスの処理
		if data.get("finder_address") and str(data["finder_address"]).strip():
			self.address_unknown.value = False
		else:
			self.address_unknown.value = True
		
		# 権利放棄・告示
		if data.get("own_waiver"):
			self.own_waiver.value = str(data["own_waiver"])
		if data.get("own_name_note"):  # note -> own_name_note
			self.note.value = str(data["own_name_note"])
		
		# 所有者情報の権利放棄・告示
		if data.get("thirdparty_waiver"):
			self.own_waiver_owner.value = str(data["thirdparty_waiver"])
		if data.get("thirdparty_name_note"):
			self.note_owner.value = str(data["thirdparty_name_note"])
		
		# 拾得物情報
		if data.get("item_class_L"):
			self.item_class_L.value = str(data["item_class_L"])
		if data.get("item_class_M"):
			self.item_class_M.value = str(data["item_class_M"])
		if data.get("item_class_S"):
			self.item_class_S.value = str(data["item_class_S"])
		if data.get("item_color"):
			self.color.value = str(data["item_color"])
		if data.get("item_feature"):
			self.feature.value = str(data["item_feature"])
		
		# 保管場所（item_storage_place）
		if data.get("item_storage_place"):
			self.storage_place.value = str(data["item_storage_place"])
		
		# 所有者情報（finder_affiliation）
		if data.get("finder_affiliation"):
			self.owner_affiliation.value = str(data["finder_affiliation"])
		# 所有者名は拾得者名と同じ（データベースには所有者専用のカラムがない）
		if data.get("finder_name"):
			self.owner_name.value = str(data["finder_name"])
		# 所有者性別は拾得者性別と同じ（データベースには所有者専用のカラムがない）
		if data.get("finder_sex"):
			self.owner_gender.value = str(data["finder_sex"])
		
		# 新規フィールド（データベースに存在しない場合はデフォルト値）
		# report_necessity は新規フィールドなので既存データにはない
		if data.get("find_area_police"):  # police_find_place -> find_area_police
			self.police_find_place.value = str(data["find_area_police"])
		if data.get("recep_manager"):  # staff -> recep_manager
			self.staff.value = str(data["recep_manager"])
		if data.get("item_value") is not None:  # is_valuable -> item_value
			self.is_valuable.value = bool(data["item_value"])
		if data.get("item_expiration"):  # expiry_date -> item_expiration
			expiry_str = str(data["item_expiration"])
			if "T" in expiry_str:
				expiry_str = expiry_str.split("T")[0]
			self.expiry_date_value = expiry_str
			self.expiry_date_field.value = expiry_str.replace("-", "/")
		if data.get("item_remarks"):  # remarks -> item_remarks
			self.remarks.value = str(data["item_remarks"])
		
		# カード情報（データベースに存在する場合）
		if data.get("card_campany"):
			# カード会社情報の処理（後日実装）
			pass
		if data.get("card_tel"):
			# カード電話番号の処理（後日実装）
			pass
		if data.get("card_name"):
			# カード名の処理（後日実装）
			pass
		if data.get("card_person"):
			# カード人物の処理（後日実装）
			pass
		
		# 金種データ（item_money）
		if data.get("item_money"):
			try:
				import json
				if isinstance(data["item_money"], str):
					self.money_data = json.loads(data["item_money"])
				else:
					self.money_data = data["item_money"]
				self.is_money_mode = bool(self.money_data)
			except:
				pass
		
		# 画像データ
		if data.get("item_image"):
			try:
				import json
				if isinstance(data["item_image"], str):
					image_data = json.loads(data["item_image"])
				else:
					image_data = data["item_image"]
				self.captured_photos_data = image_data
			except Exception as e:
				print(f"画像データ読み込みエラー: {e}")
				pass
		
		# フォームを更新
		self.update()
	
	def _apply_ai_classification(self):
		"""AI分類結果をフォームに適用"""
		try:
			# グローバル変数からAI分類結果を取得
			import sys
			ai_module = sys.modules.get('flet_pages.ai_classification')
			if ai_module and hasattr(ai_module, 'ai_classification_result'):
				ai_result = ai_module.ai_classification_result
				if ai_result:
					# 分類結果をフォームに適用
					if ai_result.get("large_category"):
						self.item_class_L.value = ai_result["large_category"]
						self._check_if_money()
						self._validate_item_class()
					
					if ai_result.get("medium_category"):
						# 中分類のオプションを更新
						large_val = ai_result["large_category"]
						if large_val in self.classification_data.get("medium_categories", {}):
							medium_opts = self.classification_data["medium_categories"][large_val]
							self.item_class_M.options = [ft.dropdown.Option(x) for x in medium_opts]
							self.item_class_M.value = ai_result["medium_category"]
							self._check_if_money()
							self._validate_item_class()
					
					if ai_result.get("small_category"):
						# 小分類のオプションを更新
						medium_val = ai_result["medium_category"]
						if medium_val in self.classification_data.get("small_categories", {}):
							small_opts = self.classification_data["small_categories"][medium_val]
							self.item_class_S.options = [ft.dropdown.Option(x) for x in small_opts]
							self.item_class_S.value = ai_result["small_category"]
							self._check_if_money()
							self._validate_item_class()
					
					print(f"AI分類結果を適用しました: {ai_result}")
		except Exception as e:
			print(f"AI分類結果適用エラー: {e}")
	
	def _load_classification_data(self):
		"""分類データを読み込み"""
		try:
			# item_classification.jsonを読み込み
			json_path = Path(__file__).parent.parent / "item_classification.json"
			with open(json_path, 'r', encoding='utf-8') as f:
				json_data = json.load(f)
			
			# config.pyの分類データを読み込み
			from apps.config import ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S
			
			# 統合された分類データを作成
			classification_data = {
				"large_categories": [],
				"medium_categories": {},
				"small_categories": {}
			}
			
			# 大分類の統合
			large_categories = set(ITEM_CLASS_L)
			
			# JSONからも大分類を追加
			for item in json_data:
				large_categories.add(item["large_category_name_ja"])
			
			classification_data["large_categories"] = sorted(list(large_categories))
			
			# 中分類の統合
			for item in ITEM_CLASS_M:
				large = item["data-val"]
				medium = item["value"]
				if large not in classification_data["medium_categories"]:
					classification_data["medium_categories"][large] = []
				classification_data["medium_categories"][large].append(medium)
			
			# JSONからも中分類を追加
			for item in json_data:
				large = item["large_category_name_ja"]
				for medium_item in item["medium_categories"]:
					medium = medium_item["medium_category_name_ja"]
					if large not in classification_data["medium_categories"]:
						classification_data["medium_categories"][large] = []
					if medium not in classification_data["medium_categories"][large]:
						classification_data["medium_categories"][large].append(medium)
			
			# 小分類の統合
			for item in ITEM_CLASS_S:
				medium = item["data-val"]
				small = item["value"]
				if medium not in classification_data["small_categories"]:
					classification_data["small_categories"][medium] = []
				classification_data["small_categories"][medium].append(small)
			
			return classification_data
			
		except Exception as e:
			print(f"分類データ読み込みエラー: {e}")
			# エラー時はデフォルトの分類データを使用
			return {
				"large_categories": ["現金", "かばん類", "財布類", "その他"],
				"medium_categories": {
					"現金": ["現金"],
					"かばん類": ["手提げかばん", "肩掛けかばん", "その他かばん類"],
					"財布類": ["財布", "がま口", "小銭入れ"],
					"その他": ["その他"]
				},
				"small_categories": {
					"現金": ["現金"],
					"手提げかばん": ["ハンドバッグ", "ビジネスバッグ", "トートバッグ"],
					"肩掛けかばん": ["ショルダーバッグ", "リュックサック"],
					"財布": ["札入れ", "財布"],
					"その他": ["その他"]
				}
			}
	
	def _load_find_places(self):
		"""拾得場所データを読み込み（設定画面と同期）"""
		try:
			import sqlite3
			import json
			from pathlib import Path
			DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"
			
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
				cur.execute("""
					INSERT OR REPLACE INTO settings (key, value, updated_at)
					VALUES (?, ?, CURRENT_TIMESTAMP)
				""", ('find_places', json.dumps(find_places, ensure_ascii=False)))
				conn.commit()
			
			conn.close()
			return find_places
		except Exception as e:
			print(f"拾得場所リスト取得エラー: {e}")
			# エラー時はデフォルトリストを返す
			return ["1階 エントランス", "2階 トイレ前", "3階 会議室前"]
	
	def _load_storage_places(self):
		"""保管場所データを読み込み（設定画面と同期）"""
		try:
			import sqlite3
			import json
			from pathlib import Path
			DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"
			
			# まずconfig.pyのSTORAGE_PLACEを取得
			from apps.config import STORAGE_PLACE
			base_places = [item[0] for item in STORAGE_PLACE]
			
			conn = sqlite3.connect(str(DB_PATH))
			cur = conn.cursor()
			
			# settingsテーブルから保管場所リストを取得
			cur.execute("SELECT value FROM settings WHERE key = 'storage_places'")
			result = cur.fetchone()
			
			if result:
				db_places = json.loads(result[0])
			else:
				# デフォルトの保管場所リスト（STORAGE_PLACEベース）
				db_places = base_places.copy()
				# デフォルトをデータベースに保存
				cur.execute("""
					INSERT OR REPLACE INTO settings (key, value, updated_at)
					VALUES (?, ?, CURRENT_TIMESTAMP)
				""", ('storage_places', json.dumps(db_places, ensure_ascii=False)))
				conn.commit()
			
			# ベースの項目とデータベースの項目をマージ（重複は除く）
			all_places = base_places.copy()
			for place in db_places:
				if place not in all_places:
					all_places.append(place)
			
			conn.close()
			return all_places
		except Exception as e:
			print(f"保管場所リスト取得エラー: {e}")
			# エラー時はSTORAGE_PLACEベースのリストを返す
			from apps.config import STORAGE_PLACE
			return [item[0] for item in STORAGE_PLACE]
	
	def _toggle_find_place_custom(self, e):
		"""拾得場所の手入力切り替え"""
		is_custom = e.control.value
		self.find_place.visible = is_custom
		self.find_place_custom.visible = not is_custom
		self.find_place_custom_icon.visible = not is_custom
		
		# バリデーションをリセット
		if is_custom:
			self.find_place_custom.value = ""
			self.find_place_custom_icon.content = None
		else:
			self.find_place.value = None
			self.find_place_icon.content = None
		
		self.update()
	
	def _validate_find_place_custom(self, e):
		"""拾得場所手入力のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["find_place"] = is_valid
		
		if is_valid:
			self.find_place_custom_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.find_place_custom.border_color = ft.colors.GREEN
			self.error_texts["find_place"].visible = False
		elif value:
			self.find_place_custom_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.find_place_custom.border_color = ft.colors.RED
			self.error_texts["find_place"].value = "拾得場所を入力してください"
			self.error_texts["find_place"].visible = True
		else:
			self.find_place_custom_icon.content = None
			self.find_place_custom.border_color = None
			self.error_texts["find_place"].visible = False
		
		self.update()
	
	def create_required_label(self, text):
		"""必須ラベル付きのテキストを作成"""
		return ft.Row([
			ft.Text(text, size=14, weight=ft.FontWeight.BOLD),
			ft.Container(
				content=ft.Text("必須", size=10, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
				bgcolor=ft.colors.RED,
				padding=ft.padding.symmetric(horizontal=6, vertical=2),
				border_radius=4
			)
		], spacing=8)
	
	def create_validation_icon(self, field_key):
		"""バリデーションアイコン（チェックまたは×）を作成"""
		if field_key not in self.validation_states:
			return ft.Container(width=24, height=24)
		
		is_valid = self.validation_states.get(field_key, None)
		if is_valid is True:
			return ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
		elif is_valid is False:
			return ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
		else:
			return ft.Container(width=24, height=24)
	
	def create_error_text(self, field_key):
		"""エラーメッセージ用のTextコントロールを作成"""
		error_text = ft.Text(
			"",
			size=12,
			color=ft.colors.RED,
			visible=False
		)
		self.error_texts[field_key] = error_text
		return error_text
	
	def validate_field(self, field_key, value, validation_func=None, error_message=""):
		"""フィールドのバリデーションを実行"""
		if validation_func:
			is_valid = validation_func(value)
		else:
			# デフォルトは空文字チェック
			is_valid = bool(value and value.strip())
		
		self.validation_states[field_key] = is_valid
		
		# エラーテキストの更新
		if field_key in self.error_texts:
			if not is_valid and value:  # 値が入力されているが無効な場合
				self.error_texts[field_key].value = error_message
				self.error_texts[field_key].visible = True
			else:
				self.error_texts[field_key].visible = False
		
		# 登録ボタン押下後もバリデーションアイコンを更新
		self._update_validation_icon(field_key, is_valid)
		
		return is_valid
	
	def _update_validation_icon(self, field_key, is_valid):
		"""バリデーションアイコンを更新"""
		icon_attr = f"{field_key}_icon"
		if hasattr(self, icon_attr):
			icon = getattr(self, icon_attr)
			if is_valid:
				icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			elif hasattr(self, field_key):
				field = getattr(self, field_key)
				if hasattr(field, 'value') and field.value:
					icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				else:
					icon.content = None
			else:
				icon.content = None
			self.update()
	
	def create_form_view(self):
		# 初期時刻
		nh, nm = nearest_15min(datetime.now())

		self.finder_type = ft.RadioGroup(value="占有者拾得", content=ft.Row([
			ft.Radio(value="占有者拾得", label="占有者拾得"),
			ft.Radio(value="第三者拾得", label="第三者拾得"),
		], spacing=16))

		# 日付ピッカー（ページオーバーレイに追加してから使用）
		self.get_date = ft.DatePicker(
			on_change=self._on_get_date_change
		)
		self.recep_date = ft.DatePicker(
			on_change=self._on_recep_date_change
		)
		self.expiry_date = ft.DatePicker(
			on_change=self._on_expiry_date_change
		)
		self.get_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.get_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)
		self.recep_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.recep_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)

		# 日付入力用のTextFieldを作成（yyyy/mm/dd形式で入力可能）
		self.get_date_field = ft.TextField(
			value=self.get_date_value.replace("-", "/"),
			hint_text="yyyy/mm/dd",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=140,
			keyboard_type=ft.KeyboardType.TEXT,
			max_length=10,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._on_get_date_field_change(e),
			on_focus=lambda e: self._on_date_field_focus(e, "get_date")
		)
		self.recep_date_field = ft.TextField(
			value=self.recep_date_value.replace("-", "/"),
			hint_text="yyyy/mm/dd",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=140,
			keyboard_type=ft.KeyboardType.TEXT,
			max_length=10,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._on_recep_date_field_change(e),
			on_focus=lambda e: self._on_date_field_focus(e, "recep_date")
		)
		self.expiry_date_field = ft.TextField(
			hint_text="yyyy/mm/dd",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=140,
			keyboard_type=ft.KeyboardType.TEXT,
			max_length=10,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._on_expiry_date_field_change(e),
			on_focus=lambda e: self._on_date_field_focus(e, "expiry_date")
		)
		
		# バリデーション用アイコン
		self.get_date_icon = ft.Container(width=24, height=24)
		self.recep_date_icon = ft.Container(width=24, height=24)

		# 第三者関連
		self.finder_name = ft.TextField(
			hint_text="例: 田中太郎",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_finder_name(e)
		)
		self.finder_name_icon = ft.Container(width=24, height=24)
		self.gender = ft.RadioGroup(value="男性", content=ft.Row([
			ft.Radio(value="男性", label="男性"),
			ft.Radio(value="女性", label="女性"),
			ft.Radio(value="その他", label="その他"),
		]))
		self.address_unknown = ft.Checkbox(label="住所 不明")
		self.address = ft.TextField(
			hint_text="例: 東京都千代田区麹町2-14",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			multiline=True, 
			min_lines=2,
			max_lines=3,
			width=400,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.postal_code = ft.TextField(
			hint_text="例: 1020083(ハイフンなし)",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=150,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.tel1 = ft.TextField(
			hint_text="例: 012-234-4567",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.tel2 = ft.TextField(
			hint_text="例: 090-1234-5678",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		# 年齢（直接入力+ボタンで増減）
		self.age = ft.TextField(
			hint_text=" ",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			value="",
			width=60,
			keyboard_type=ft.KeyboardType.NUMBER,
			text_align=ft.TextAlign.CENTER,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		# 占有者の所属
		self.owner_affiliation = ft.TextField(
			hint_text="例: アイング株式会社",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		# 占有者の氏名と性別
		self.owner_name = ft.TextField(
			hint_text="例: 山田太郎",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_owner_name(e)
		)
		self.owner_name_icon = ft.Container(width=24, height=24)
		self.owner_gender = ft.RadioGroup(value="男性", content=ft.Row([
			ft.Radio(value="男性", label="男性"),
			ft.Radio(value="女性", label="女性"),
			ft.Radio(value="その他", label="その他"),
		]))

		# 拾得場所の手入力フィールド（デフォルト表示）
		self.find_place_custom = ft.TextField(
			hint_text="拾得場所を入力（例: 2階男子トイレ前）",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_find_place_custom(e)
		)
		self.find_place_custom_icon = ft.Container(width=24, height=24)
		
		# 拾得場所のプルダウン（ボタンで表示）
		self.find_place = ft.Dropdown(
			hint_text="拾得場所を選択",
			options=[ft.dropdown.Option(x) for x in self.find_places_data],
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			visible=False,
			on_change=lambda e: self._validate_find_place(e)
		)
		self.find_place_icon = ft.Container(width=24, height=24)
		
		# 新規フィールド：届出要否（必須）
		self.report_necessity = ft.Dropdown(
			hint_text="未選択",
			options=[ft.dropdown.Option(x[0]) for x in REPORT_NECESSITY],
			width=150,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_report_necessity(e)
		)
		self.report_necessity_icon = ft.Container(width=24, height=24)
		
		# 新規フィールド：警察届出用拾得場所（必須）
		self.police_find_place = ft.TextField(
			hint_text="例: 2階男子トイレ前",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_police_find_place(e)
		)
		self.police_find_place_icon = ft.Container(width=24, height=24)
		
		# 店舗名（アカウント情報から取得、表示のみ）
		self.store_name = ft.Text("", size=14, color=ft.colors.GREY_700)
		
		# 担当者（アカウント情報から取得）
		self.staff = ft.Text("", size=14, color=ft.colors.GREY_700)
		
		# 新規フィールド：貴重な物件に該当（必須、チェックボックス）
		self.is_valuable = ft.Checkbox(
			label="貴重な物件に該当",
			value=False
		)
		
		# 新規フィールド：備考（任意）
		self.remarks = ft.TextField(
			hint_text="備考を入力",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			multiline=True,
			min_lines=2,
			max_lines=4,
			width=400,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		self.own_waiver = ft.Dropdown(
			hint_text="権利放棄を選択",
			options=[ft.dropdown.Option(x[0]) for x in OWN_WAIVER],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_own_waiver(e)
		)
		self.own_waiver_icon = ft.Container(width=24, height=24)
		
		self.note = ft.Dropdown(
			hint_text="未選択",
			options=[ft.dropdown.Option(x[0]) for x in NOTE],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_note(e)
		)
		self.note_icon = ft.Container(width=24, height=24)
		
		self.own_waiver_owner = ft.Dropdown(
			hint_text="未選択",
			options=[ft.dropdown.Option(x[0]) for x in OWN_WAIVER],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_own_waiver_owner(e)
		)
		self.own_waiver_owner_icon = ft.Container(width=24, height=24)
		
		self.note_owner = ft.Dropdown(
			hint_text="未選択",
			options=[ft.dropdown.Option(x[0]) for x in NOTE],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_note_owner(e)
		)
		self.note_owner_icon = ft.Container(width=24, height=24)

		# 物件分類・色・保管
		self.item_class_L = ft.Dropdown(
			hint_text="分類（大）を選択",
			options=[ft.dropdown.Option(x) for x in ITEM_CLASS_L],
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_item_class_L(e)
		)
		self.item_class_L_icon = ft.Container(width=24, height=24)
		
		self.item_class_M = ft.Dropdown(
			hint_text="分類（中）を選択",
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.item_class_S = ft.Dropdown(
			hint_text="分類（小）を選択",
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.color = ft.Dropdown(
			hint_text="色を選択",
			options=[ft.dropdown.Option(x[0]) for x in COLOR],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		self.feature = ft.TextField(
			hint_text="例: 黒い革製の長財布、ルイヴィトン",
			hint_style=ft.TextStyle(color=ft.colors.GREY_400),
			multiline=True, 
			min_lines=2,
			width=400,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		self.storage_place = ft.Dropdown(
			hint_text="未選択",
			options=[ft.dropdown.Option(x) for x in self.storage_places_data],
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_storage_place(e)
		)
		self.storage_place_icon = ft.Container(width=24, height=24)

		# 分類全体のバリデーションアイコン
		self.item_class_icon = ft.Container(width=24, height=24)
		
		# L→M→S の連動とバリデーション
		def on_L_change(e):
			val = self.item_class_L.value
			m_opts = [m["value"] for m in ITEM_CLASS_M if m.get("data-val") == val]
			self.item_class_M.options = [ft.dropdown.Option(x) for x in m_opts]
			self.item_class_M.value = None
			self.item_class_M.update()
			self.item_class_S.options = []
			self.item_class_S.value = None
			self.item_class_S.update()
			
			# 現金かどうかチェック
			self._check_if_money()
			# 分類全体のバリデーション
			self._validate_item_class()
		self.item_class_L.on_change = on_L_change

		def on_M_change(e):
			val = self.item_class_M.value
			s_opts = [s["value"] for s in ITEM_CLASS_S if s.get("data-val") == val]
			self.item_class_S.options = [ft.dropdown.Option(x) for x in s_opts]
			self.item_class_S.value = None
			self.item_class_S.update()
			
			# 現金かどうかチェック
			self._check_if_money()
			# 分類全体のバリデーション
			self._validate_item_class()
		self.item_class_M.on_change = on_M_change
		
		def on_S_change(e):
			# 現金かどうかチェック
			self._check_if_money()
			# 分類全体のバリデーション
			self._validate_item_class()
		self.item_class_S.on_change = on_S_change

		# 拾得者区分の変更を監視
		def on_finder_type_change(e):
			is_third_party = e.control.value == "第三者拾得"
			
			# コンテナの表示/非表示を切り替え
			third_party_container.visible = is_third_party
			owner_container.visible = not is_third_party
			
			# 非表示項目の値をクリア
			if not is_third_party:
				# 第三者拾得の項目をクリア
				self.finder_name.value = ""
				self.gender.value = "男性"
				self.postal_code.value = ""
				self.address.value = ""
				self.address_unknown.value = False
				self.own_waiver.value = None
				self.note.value = None
				self.tel1.value = ""
				self.tel2.value = ""
			else:
				# 占有者拾得の項目をクリア
				self.owner_affiliation.value = ""
				self.owner_name.value = ""
				self.owner_gender.value = "男性"
				self.own_waiver_owner.value = None
				self.note_owner.value = None
			
			# UIを更新
			self.update()
		
		self.finder_type.on_change = on_finder_type_change
		
		# 初期状態は占有者拾得がデフォルト（コンテナで制御）

		# Enterで次の項目へ（順番にfocusを移動）
		def wire_enter_navigation(order):
			for i, ctrl in enumerate(order):
				def handler(e, _i=i, _order=order):
					nxt = _order[_i + 1] if _i + 1 < len(_order) else None
					if hasattr(nxt, "focus") and callable(getattr(nxt, "focus")):
						nxt.focus()
						if hasattr(nxt, "update"):
							nxt.update()
					elif self.page is not None:
						self.page.update()
				if hasattr(ctrl, "on_submit"):
					ctrl.on_submit = handler

		wire_enter_navigation([
			self.finder_name,
			self.find_place,
			self.address,
			self.postal_code,
			self.tel1,
			self.tel2,
		])

		# レイアウト（余白を狭く）
		section_manage_style = dict(padding=5, bgcolor=ft.colors.WHITE, border_radius=6, border=ft.border.all(1, ft.colors.GREY_300))
		section_finder_style = dict(padding=5, bgcolor=ft.colors.WHITE, border_radius=6, border=ft.border.all(1, ft.colors.GREY_300))
		section_item_style = dict(padding=5, bgcolor=ft.colors.WHITE, border_radius=6, border=ft.border.all(1, ft.colors.GREY_300))

		# ========================================
		# 管理情報セクションの構築
		# ========================================
		# 拾得物の管理に必要な基本情報を入力するセクション
		section_manage = ft.Container(
			content=ft.Column([
				# セクションタイトルと店舗・担当者表示（同じ行に）
				ft.Row([
					ft.Text("管理情報", size=18, weight=ft.FontWeight.BOLD),
					ft.Container(expand=True),  # スペーサー
					ft.Text("店舗: ", size=12, color=ft.colors.GREY_600),
					self.store_name,
					ft.Container(width=20),  # スペーサー
					ft.Text("担当者: ", size=12, color=ft.colors.GREY_600),
					self.staff
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
				
				# ========================================
				# 保管場所の入力
				# ========================================
				ft.Column([
					self.create_required_label("保管場所"),
					ft.Row([
						self.storage_place,  # ドロップダウンで保管場所を選択
						self.storage_place_icon
					], spacing=10),
					self.create_error_text("storage_place")
				], spacing=5),
				
				# ========================================
				# 届出要否の入力（新規）貴重な物件に該当（新規）
				# ========================================
				ft.Row([
					ft.Column([
						self.create_required_label("届出要否"),
						ft.Row([
							self.report_necessity,
							self.report_necessity_icon
						], spacing=20),
						self.create_error_text("report_necessity")
					], spacing=5),
					ft.Column([
						self.create_required_label("貴重な物件"),
						self.is_valuable
					], spacing=5),
				], spacing=45),
				
				
				
				# ========================================
				# 拾得日時の入力（横並び）
				# ========================================
				ft.Row([
					# 拾得日の入力
					ft.Column([
						self.create_required_label("拾得日"),
						ft.Row([
							self.get_date_field,  # yyyymmdd形式の入力フィールド
							ft.IconButton(
								icon=ft.icons.CALENDAR_MONTH,
								on_click=lambda e: self.get_date.pick_date(),
								tooltip="カレンダーから選択"
							),
							self.get_date_icon
						], spacing=5),
						self.create_error_text("get_date")
					], spacing=5),
					
					# 拾得時刻の入力
					ft.Column([
						self.create_required_label("拾得時刻"),
						ft.Row([
							self.get_hour,    # 時（00-23）
							ft.Text(":"),     # 区切り文字
							self.get_min      # 分（00, 15, 30, 45）
						], spacing=5),
						self.create_error_text("get_time")
					], spacing=5),
				], spacing=40),  # 拾得日と拾得時刻の間隔
				
				# ========================================
				# 受付日時の入力（横並び）
				# ========================================
				ft.Row([
					# 受付日の入力
					ft.Column([
						self.create_required_label("受付日"),
						ft.Row([
							self.recep_date_field,  # yyyymmdd形式の入力フィールド
							ft.IconButton(
								icon=ft.icons.CALENDAR_MONTH,
								on_click=lambda e: self.recep_date.pick_date(),
								tooltip="カレンダーから選択"
							),
							self.recep_date_icon
						], spacing=5),
						self.create_error_text("recep_date")
					], spacing=5),
					
					# 受付時刻の入力
					ft.Column([
						self.create_required_label("受付時刻"),
						ft.Row([
							self.recep_hour,  # 時（00-23）
							ft.Text(":"),     # 区切り文字
							self.recep_min    # 分（00, 15, 30, 45）
						], spacing=5),
						self.create_error_text("recep_time")
					], spacing=5),
				], spacing=40),  # 受付日と受付時刻の間隔
				
				# ========================================
				# 拾得場所の入力
				# ========================================
				ft.Column([
					ft.Row([
						self.create_required_label("拾得場所"),
						ft.Container(expand=True),
						ft.Checkbox(
							label="プルダウンから選択する",
							on_change=lambda e: self._toggle_find_place_custom(e)
						)
					], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
					ft.Row([
						self.find_place_custom,  # 手入力フィールド（デフォルト表示）
						self.find_place_custom_icon
					], spacing=10),
					ft.Row([
						self.find_place,  # ドロップダウンで拾得場所を選択
						self.find_place_icon
					], spacing=10),
					self.create_error_text("find_place")
				], spacing=5),
				
				# ========================================
				# 警察届出用拾得場所の入力（任意）
				# ========================================
				ft.Column([
					ft.Text("警察届出用拾得場所", size=14, weight=ft.FontWeight.BOLD),
					ft.Row([
						self.police_find_place,
						self.police_find_place_icon
					], spacing=10),
					self.create_error_text("police_find_place")
				], spacing=5),
			], spacing=8),  # 各要素間の縦の間隔（余白を狭く）
			**section_manage_style  # セクション全体のスタイル（背景色、枠線など）
		)

		# ========================================
		# 住所検索機能
		# ========================================
		# 郵便番号から住所を自動取得する機能
		def search_address(e):
			# 郵便番号フィールドから値を取得（空の場合は空文字列）
			postal_val = self.postal_code.value or ""
			
			# 郵便番号の前処理：ハイフンとスペースを除去して数字のみにする
			zip_raw = postal_val.replace("-", "").replace(" ", "")
			
			# 郵便番号の形式チェック：7桁の数字かどうか
			if len(zip_raw) == 7 and zip_raw.isdigit():
				try:
					# ========================================
					# 郵便番号検索APIの呼び出し
					# ========================================
					# zipcloud APIを使用して郵便番号から住所を検索
					r = requests.get(
						"https://zipcloud.ibsnet.co.jp/api/search", 
						params={"zipcode": zip_raw}, 
						timeout=5  # 5秒でタイムアウト
					)
					js = r.json()  # JSONレスポンスを解析
					
					# APIレスポンスの成功チェック
					if js.get("status") == 200 and js.get("results"):
						# 検索結果の最初の住所情報を取得
						res = js["results"][0]
						pref = res.get("address1") or ""  # 都道府県
						city = res.get("address2") or ""  # 市区町村
						town = res.get("address3") or ""  # 町域
						
						# 住所を結合して住所フィールドに設定
						base = f"{pref}{city}{town}"
						self.address.value = base
						self.address.update()  # UIを更新
					else:
						# 住所が見つからない場合のエラー処理
						if self.page:
							self.page.snack_bar.content = ft.Text("郵便番号が見つかりませんでした。")
							self.page.snack_bar.open = True
							self.page.update()
				except Exception as ex:
					# ネットワークエラーやAPIエラーの処理
					if self.page:
						self.page.snack_bar.content = ft.Text(f"住所検索エラー: {ex}")
						self.page.snack_bar.open = True
						self.page.update()
			else:
				# 郵便番号の形式が正しくない場合のエラー処理
				if self.page:
					self.page.snack_bar.content = ft.Text("郵便番号は7桁の数字で入力してください。")
					self.page.snack_bar.open = True
					self.page.update()

		# 第三者拾得用のコンテナ
		third_party_container = ft.Container(
			content=ft.Column([
				# 氏名
				ft.Column([
					self.create_required_label("拾得者氏名"),
					ft.Row([
						self.finder_name,
						self.finder_name_icon,
					], spacing=10),
					self.create_error_text("finder_name")
				], spacing=5),
				# 性別と年齢を同じ行に
				ft.Row([
					ft.Column([
						ft.Text("性別", size=14, weight=ft.FontWeight.BOLD),
						self.gender,
					], spacing=5),
					ft.Column([
						ft.Text("年齢", size=14, weight=ft.FontWeight.BOLD),
						ft.Row([
							ft.IconButton(
								icon=ft.icons.REMOVE,
								icon_size=20,
								tooltip="年齢を減らす",
								on_click=lambda e: self._decrease_age()
							),
							self.age,
							ft.IconButton(
								icon=ft.icons.ADD,
								icon_size=20,
								tooltip="年齢を増やす",
								on_click=lambda e: self._increase_age()
							),
						], spacing=5)
					], spacing=5),
				], spacing=20),
				ft.Row([
					ft.Column([
						ft.Text("郵便番号", size=14, weight=ft.FontWeight.BOLD),
						self.postal_code
					], spacing=5),
					ft.Column([
						ft.Text("", size=14),  # 空のラベルで位置合わせ
						ft.ElevatedButton("住所検索", on_click=search_address, width=80, height=40)
					], spacing=5),
				], spacing=10),
				ft.Column([
					ft.Text("住所", size=14, weight=ft.FontWeight.BOLD),
					self.address,
					self.address_unknown
				], spacing=5),
				ft.Row([
					ft.Column([
						ft.Text("所属", size=14, weight=ft.FontWeight.BOLD),
						self.owner_affiliation
					], spacing=5),
				], spacing=10),
				ft.Row([
					ft.Column([
						ft.Text("連絡先1", size=14, weight=ft.FontWeight.BOLD),
						self.tel1
					], spacing=5),
					ft.Column([
						ft.Text("連絡先2", size=14, weight=ft.FontWeight.BOLD),
						self.tel2
					], spacing=5),
				], spacing=45),
				ft.Row([
					ft.Column([
						self.create_required_label("権利放棄"),
						ft.Row([
							self.own_waiver,
							self.own_waiver_icon
						], spacing=10),
						self.create_error_text("own_waiver")
					], spacing=5),
					ft.Column([
						self.create_required_label("氏名等告示"),
						ft.Row([
							self.note,
							self.note_icon
						], spacing=10),
						self.create_error_text("note")
					], spacing=5),
				], spacing=10),
			], spacing=15),
			visible=False
		)	

		# 占有者拾得用のコンテナ
		owner_container = ft.Container(
			content=ft.Column([
				# 氏名
				ft.Column([
					self.create_required_label("占有者の氏名"),
					ft.Row([
						self.owner_name,
						self.owner_name_icon,
					], spacing=10),
					self.create_error_text("owner_name")
				], spacing=5),
				# 性別
				ft.Column([
					ft.Text("性別", size=14, weight=ft.FontWeight.BOLD),
					self.owner_gender,
				], spacing=5),
				ft.Column([
					ft.Text("占有者の所属", size=14, weight=ft.FontWeight.BOLD),
					self.owner_affiliation
				], spacing=5),	
				ft.Row([
					ft.Column([
						self.create_required_label("占有者権利放棄"),
						ft.Row([
							self.own_waiver_owner,
							self.own_waiver_owner_icon
						], spacing=10),
						self.create_error_text("own_waiver_owner")
					], spacing=5),
					ft.Column([
						self.create_required_label("占有者氏名等告示"),
						ft.Row([
							self.note_owner,
							self.note_owner_icon
						], spacing=10),
						self.create_error_text("note_owner")
					], spacing=5),
				], spacing=20),
			], spacing=15),
			visible=True
		)

		section_finder = ft.Container(
			content=ft.Column([
				ft.Text("拾得者情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Column([
					self.create_required_label("拾得者区分"),
					self.finder_type,
					self.create_error_text("finder_type")
				], spacing=5),
				third_party_container,
				owner_container,
			], spacing=8),
			**section_finder_style
		)

		# 金種登録ボタンのコンテナを作成（分類の下に表示）
		self.money_button_in_form = ft.Container(
			content=ft.Column([
				ft.Container(height=10),
				ft.ElevatedButton(
					"金種登録", 
					on_click=lambda e: self.open_money_registration(),
					bgcolor=ft.colors.ORANGE_700,
					color=ft.colors.WHITE,
					height=45,
					width=180,
					icon=ft.icons.ATTACH_MONEY
				),
				ft.Text("※現金の場合は金種登録が必要です", size=11, color=ft.colors.ORANGE_700)
			], spacing=5),
			visible=False  # デフォルトは非表示
		)
		
		# 拾得物詳細
		section_item = ft.Container(
			content=ft.Column([
				ft.Text("拾得物詳細", size=18, weight=ft.FontWeight.BOLD),
				ft.Column([
					ft.Row([
						ft.Row([
							ft.Text("分類", size=14, weight=ft.FontWeight.BOLD),
							ft.Container(
								content=ft.Text("必須", size=10, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
								bgcolor=ft.colors.RED,
								padding=ft.padding.symmetric(horizontal=6, vertical=2),
								border_radius=4
							)
						], spacing=8),
						self.item_class_icon
					], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
					ft.Row([
						ft.Column([
							ft.Text("大", size=12, weight=ft.FontWeight.BOLD),
							self.item_class_L
						], spacing=5, expand=True),
						ft.Column([
							ft.Text("中", size=12, weight=ft.FontWeight.BOLD),
							self.item_class_M
						], spacing=5, expand=True),
						ft.Column([
							ft.Text("小", size=12, weight=ft.FontWeight.BOLD),
							self.item_class_S
						], spacing=5, expand=True),
					], spacing=10),
					self.create_error_text("item_class"),
					# 金種登録ボタンをここに配置
					self.money_button_in_form
				], spacing=5),
				ft.Column([
					ft.Text("色", size=14, weight=ft.FontWeight.BOLD),
					self.color
				], spacing=5),
				ft.Column([
					ft.Text("特徴", size=14, weight=ft.FontWeight.BOLD),
					self.feature
				], spacing=5),
				ft.Column([
					ft.Text("消費期限", size=14, weight=ft.FontWeight.BOLD),
					ft.Row([
						self.expiry_date_field,
						ft.IconButton(
							icon=ft.icons.CALENDAR_MONTH,
							on_click=lambda e: self.expiry_date.pick_date(),
							tooltip="カレンダーから選択"
						)
					], spacing=5)
				], spacing=5),
				ft.Column([
					ft.Text("備考", size=14, weight=ft.FontWeight.BOLD),
					self.remarks
				], spacing=5),
			], spacing=8),
			**section_item_style
		)

		# ========================================
		# 写真表示セクションの作成
		# ========================================
		# 右側に表示する撮影済み写真のセクションを作成
		# メイン写真の大きな表示と写真一覧のグリッドを含む
		photo_section = self.create_photo_section()
		
		# ========================================
		# エラーバナーの作成
		# ========================================
		self.error_banner = ft.Container(
			content=ft.Row([
				ft.Icon(ft.icons.ERROR_OUTLINE, color=ft.colors.WHITE, size=24),
				ft.Text("未記入項目があります。赤く表示されている項目を確認してください。", 
				       color=ft.colors.WHITE, 
				       size=16,
				       weight=ft.FontWeight.BOLD)
			], spacing=10),
			bgcolor=ft.colors.RED_700,
			padding=15,
			border_radius=8,
			visible=False  # デフォルトは非表示
		)
		
		# ========================================
		# フォームコンテンツの構築
		# ========================================
		# 左側に表示するフォーム入力部分を縦方向に配置
		form_content = ft.Column([
			# エラーバナー
			self.error_banner,
			
			# タイトル：現在のステップを表示
			ft.Text("ステップ2: 詳細を入力", size=22, weight=ft.FontWeight.BOLD),
			
			# 管理情報セクション（保管場所、拾得日時、受付日時、拾得場所）
			section_manage,
			
			# 拾得者情報セクション（拾得者区分、氏名、住所、連絡先など）
			section_finder,
			
			# 拾得物詳細セクション（分類、色、特徴など）
			section_item,
		], 
		expand=True,                    # 縦方向に全高を拡張
		scroll=ft.ScrollMode.AUTO,      # 内容が多くなった場合にスクロール可能
		spacing=10                      # 各要素間の間隔を狭く
		)
		
		# ========================================
		# アクションボタン群
		# ========================================
		button_row = ft.Container(
			content=ft.Row([
				# ホームに戻るボタン
				ft.OutlinedButton(
					"ホームに戻る", 
					on_click=lambda e: self.page.go("/") if self.page else None,
					style=ft.ButtonStyle(
						color=ft.colors.RED_400,
					),
					icon=ft.icons.HOME
				),
				
				# 撮影画面に戻るボタン
				ft.TextButton(
					"撮影画面に戻る", 
					on_click=lambda e: self.go_back_to_camera(),
					style=ft.ButtonStyle(
						color=ft.colors.GREY_600,
					)
				),
				
				# 一時保存ボタン
				ft.OutlinedButton(
					"一時保存", 
					on_click=lambda e: self.temp_save(),
					style=ft.ButtonStyle(
						color=ft.colors.GREY_700,
					)
				),
				
				# スペーサー
				ft.Container(expand=True),
				
				# 登録ボタン
				ft.Container(
					content=ft.Text("登録", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
					bgcolor=ft.colors.GREEN_700,
					height=60,
					width=200,
					border_radius=5,
					alignment=ft.alignment.center,
					on_click=lambda e: self.submit(),
					ink=True
				),
			], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
			padding=5
		)
		
		# フォームコンテンツにボタン行を追加
		form_content.controls.append(button_row)

		# ========================================
		# 左右分割レイアウトの構築
		# ========================================
		# 画面を左右2つのエリアに分割して表示
		# 左側：拾得物登録フォーム（入力フィールド群）
		# 右側：撮影済み写真の表示エリア
		layout = ft.Row([
			# ========================================
			# 左側エリア：フォーム入力部分
			# ========================================
			ft.Container(
				content=form_content,  # 上で作成したフォームコンテンツを配置
				expand=4,              # 左側の幅比率を4に設定（全体の4/5程度）
				padding=5              # コンテナ内側の余白を狭く
			),
			# ========================================
			# 右側エリア：写真表示部分
			# ========================================
			ft.Container(
				content=photo_section,           # 撮影済み写真を表示するセクション
				expand=2,                      # 右側の幅を400pxに固定
				padding=5,                      # コンテナ内側の余白を狭く
				bgcolor=ft.colors.GREY_100,     # 背景色を薄いグレーに設定
				border_radius=8                 # 角を丸くする（8pxの半径）
			)
		], expand=True)  # Row全体を親コンテナの全幅に拡張

		return layout
	
	def create_photo_section(self):
		"""撮影済み写真を表示するセクションを作成"""
		# メイン写真（最初の写真）を大きく表示
		main_photo_display = self.create_main_photo_display()
		
		# 写真一覧のグリッド
		photo_grid = ft.GridView(
			runs_count=2,  # 2列表示
			max_extent=100,  # サムネイルサイズを縮小（150→100）
			child_aspect_ratio=1.0,  # 正方形の比率（1:1）
			spacing=8,
			run_spacing=8,
		)
		
		# 撮影済み写真がある場合、表示
		if self.captured_photos_data:
			# メイン写真を表示（赤枠で強調）
			for i, photo in enumerate(self.captured_photos_data.get('main_photos', [])):
				if photo and 'frame' in photo:
					thumbnail = self.create_photo_thumbnail(photo['frame'], size=80)
					photo_container = ft.Container(
						content=ft.Column([
							thumbnail,
							ft.Text(f"メイン", size=9, text_align=ft.TextAlign.CENTER, color=ft.colors.RED, weight=ft.FontWeight.BOLD)
						], spacing=2),
						border=ft.border.all(2, ft.colors.RED),
						border_radius=6,
						padding=3,
						on_click=lambda e, photo_data=photo: self.show_photo_dialog(photo_data, f"メイン写真")
					)
					photo_grid.controls.append(photo_container)
			
			# サブ写真を表示
			for i, photo in enumerate(self.captured_photos_data.get('sub_photos', [])):
				if photo and 'frame' in photo:
					thumbnail = self.create_photo_thumbnail(photo['frame'], size=80)
					photo_container = ft.Container(
						content=ft.Column([
							thumbnail,
							ft.Text(f"サブ{i+1}", size=9, text_align=ft.TextAlign.CENTER)
						], spacing=2),
						border=ft.border.all(2, ft.colors.BLUE),
						border_radius=6,
						padding=3,
						on_click=lambda e, photo_data=photo: self.show_photo_dialog(photo_data, f"サブ写真 {i+1}")
					)
					photo_grid.controls.append(photo_container)
			
			# 同梱物写真を表示
			for i, photo in enumerate(self.captured_photos_data.get('bundle_photos', [])):
				if photo and 'frame' in photo:
					thumbnail = self.create_photo_thumbnail(photo['frame'], size=80)
					photo_container = ft.Container(
						content=ft.Column([
							thumbnail,
							ft.Text(f"同梱{i+1}", size=9, text_align=ft.TextAlign.CENTER)
						], spacing=2),
						border=ft.border.all(2, ft.colors.ORANGE),
						border_radius=6,
						padding=3,
						on_click=lambda e, photo_data=photo: self.show_photo_dialog(photo_data, f"同梱物写真 {i+1}")
					)
					photo_grid.controls.append(photo_container)
		
		# 撮影済み写真がない場合のメッセージ
		if not photo_grid.controls:
			photo_grid.controls.append(
				ft.Container(
					content=ft.Text("撮影された写真はありません", 
					              color=ft.colors.GREY_600, 
					              size=12,
					              text_align=ft.TextAlign.CENTER),
					width=150,
					height=150,
					bgcolor=ft.colors.GREY_100,
					border_radius=8,
					alignment=ft.alignment.center
				)
			)
		
		return ft.Container(
			content=ft.Column([
				ft.Text("撮影済み写真", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
				ft.Divider(),
				# メイン写真の大きな表示
				main_photo_display,
				ft.Divider(),
				# 写真一覧
				ft.Text("写真一覧", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
				ft.Container(
					content=photo_grid,
					height=350,  # 写真一覧の高さを調整
					border=ft.border.all(1, ft.colors.GREY_300),
					border_radius=8,
					padding=5  # パディングを削減
				),
			], spacing=5),  # 間隔を削減
			width=400,  # 右側の幅を調整
			height=600,  # 右側の高さを調整
			padding=5,  # パディングを削減
			bgcolor=ft.colors.GREY_100,
			border_radius=8
		)
	
	def create_main_photo_display(self):
		"""メイン写真（最初の写真）を大きく表示"""
		if self.captured_photos_data and self.captured_photos_data.get('main_photos'):
			first_photo = self.captured_photos_data['main_photos'][0]
			if first_photo and 'frame' in first_photo:
				# 正方形のサイズで表示
				display_size = 250
				large_thumbnail = self.create_photo_thumbnail(first_photo['frame'], size=display_size)
				return ft.Container(
					content=ft.Column([
						ft.Text("メイン写真", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
						ft.Container(
							content=large_thumbnail,
							width=display_size,
							height=display_size,
							border=ft.border.all(3, ft.colors.RED),
							border_radius=8,
							padding=0,
							alignment=ft.alignment.center,
							on_click=lambda e: self.show_photo_dialog(first_photo, "メイン写真")
						)
					], spacing=5),
					width=display_size,
					height=display_size + 30,  # ラベル分の高さを追加
					bgcolor=ft.colors.WHITE,
					border_radius=8,
					padding=5
				)
		
		# 写真がない場合
		display_size = 250
		return ft.Container(
			content=ft.Text("撮影された写真はありません", 
			              color=ft.colors.GREY_600, 
			              size=14,
			              text_align=ft.TextAlign.CENTER),
			width=display_size,
			height=display_size,
			bgcolor=ft.colors.GREY_100,
			border_radius=8,
			alignment=ft.alignment.center
		)
	
	def show_photo_dialog(self, photo_data, title):
		"""写真をダイアログで大きく表示"""
		if photo_data and 'frame' in photo_data:
			# 大きなサイズでサムネイルを作成
			large_thumbnail = self.create_photo_thumbnail(photo_data['frame'], size=550)
			
			dialog = ft.AlertDialog(
				title=ft.Text(title),
				content=ft.Container(
					content=large_thumbnail,
					width=600,
					height=450,
					border_radius=8,
					alignment=ft.alignment.center  # 中央揃えを追加
				),
				actions=[
					ft.TextButton("閉じる", on_click=lambda e: self.close_photo_dialog())
				],
				actions_alignment=ft.MainAxisAlignment.END
			)
			
			if self.page:
				self.page.dialog = dialog
				dialog.open = True
				self.page.update()
	
	def close_photo_dialog(self):
		"""写真ダイアログを閉じる"""
		if self.page and self.page.dialog:
			self.page.dialog.open = False
			self.page.update()
	
	def show_error(self, message):
		"""エラーメッセージを表示"""
		if self.page:
			# 既存のダイアログをクリア
			if hasattr(self, 'current_dialog') and self.current_dialog:
				self.close_dialog()
			
			# 画面上部にエラーダイアログを表示
			self.current_dialog = ft.AlertDialog(
				title=ft.Text("エラー", color=ft.colors.RED),
				content=ft.Text(message),
				actions=[
					ft.TextButton("OK", on_click=lambda e: self.close_dialog())
				],
				modal=True,
				open=True
			)
			self.page.overlay.append(self.current_dialog)
			self.page.update()
	
	def show_success(self, message):
		"""成功メッセージを表示"""
		if self.page:
			# 既存のダイアログをクリア
			if hasattr(self, 'current_dialog') and self.current_dialog:
				self.close_dialog()
			
			# 画面上部に成功ダイアログを表示
			self.current_dialog = ft.AlertDialog(
				title=ft.Text("成功", color=ft.colors.GREEN),
				content=ft.Text(message),
				actions=[
					ft.TextButton("OK", on_click=lambda e: self.close_dialog())
				],
				modal=True,
				open=True
			)
			self.page.overlay.append(self.current_dialog)
			self.page.update()
	
	def close_dialog(self):
		"""ダイアログを閉じる"""
		if self.page and hasattr(self, 'current_dialog') and self.current_dialog:
			if self.current_dialog in self.page.overlay:
				self.page.overlay.remove(self.current_dialog)
			self.current_dialog = None
			self.page.update()
	
	def create_photo_thumbnail(self, frame, size=80):
		"""フレームからサムネイルを作成（1:1正方形、左右トリミング）"""
		# 正方形のサムネイルサイズ
		target_size = size
		
		# フレームの中心部分を正方形にクロップ
		h, w = frame.shape[:2]
		if w > h:
			# 横長の場合：左右をトリミング
			start_x = (w - h) // 2
			cropped_frame = frame[:, start_x:start_x + h]
		else:
			# 縦長の場合：上下をトリミング
			start_y = (h - w) // 2
			cropped_frame = frame[start_y:start_y + w, :]
		
		# 正方形にリサイズ
		small_frame = cv2.resize(cropped_frame, (target_size, target_size), interpolation=cv2.INTER_AREA)
		rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
		
		# PIL Imageに変換
		pil_image = Image.fromarray(rgb_frame)
		
		# 解像度を下げる（JPEGの品質を下げる）
		img_byte_arr = io.BytesIO()
		pil_image.save(img_byte_arr, format='JPEG', quality=60, optimize=True)
		img_byte_arr = img_byte_arr.getvalue()
		
		# Base64エンコード
		img_base64 = base64.b64encode(img_byte_arr).decode()
		
		return ft.Image(
			src_base64=img_base64,
			width=target_size,
			height=target_size,
			fit=ft.ImageFit.COVER,  # 正方形で余白をなくす
			border_radius=4
		)
	
	def on_camera_capture_complete(self, photo_data):
		"""カメラ撮影完了時の処理"""
		self.captured_photos_data = photo_data
		self.current_mode = "form"
		
		# フォーム画面に切り替えるためにbuildメソッドを再実行
		self.content = self.create_form_view()
		self.update()
	
	def on_camera_back(self):
		"""カメラ画面から戻る時の処理"""
		# ホーム画面に戻るなどの処理
		if self.page:
			self.page.go("/")
	
	def go_back_to_camera(self):
		"""フォーム画面からカメラ画面に戻る"""
		if self.on_back_to_camera and callable(self.on_back_to_camera):
			self.on_back_to_camera()

	def _get_staff_list(self):
		"""設定から担当者リストを取得"""
		try:
			import sqlite3
			import json
			from pathlib import Path
			DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"
			
			conn = sqlite3.connect(str(DB_PATH))
			cur = conn.cursor()
			
			# settingsテーブルから担当者リストを取得
			cur.execute("SELECT value FROM settings WHERE key = 'staff_list'")
			result = cur.fetchone()
			
			if result:
				staff_list = json.loads(result[0])
			else:
				# デフォルトの担当者リスト
				staff_list = ["佐藤", "鈴木", "田中", "高橋"]
			
			conn.close()
			return staff_list
		except Exception as e:
			print(f"担当者リスト取得エラー: {e}")
			# エラー時はデフォルトリストを返す
			return ["佐藤", "鈴木", "田中", "高橋"]
	
	def did_mount(self):
		# DatePicker をページオーバーレイに追加
		try:
			if not self._date_pickers_added and self.page is not None:
				self.page.overlay.append(self.get_date)
				self.page.overlay.append(self.recep_date)
				self.page.overlay.append(self.expiry_date)
				self.page.update()
				self._date_pickers_added = True
		except Exception:
			pass

	def _on_date_field_focus(self, e, field_type):
		"""日付フィールドフォーカス時の自動スラッシュ挿入"""
		field = e.control
		value = field.value or ""
		
		# 数字のみの場合は自動でスラッシュを挿入
		if value.isdigit():
			if len(value) == 8:  # yyyymmdd形式
				formatted = f"{value[:4]}/{value[4:6]}/{value[6:8]}"
				field.value = formatted
				field.update()
			elif len(value) == 6:  # yymmdd形式
				formatted = f"20{value[:2]}/{value[2:4]}/{value[4:6]}"
				field.value = formatted
				field.update()
			elif len(value) == 4:  # mmdd形式
				from datetime import datetime
				current_year = datetime.now().year
				formatted = f"{current_year}/{value[:2]}/{value[2:4]}"
				field.value = formatted
				field.update()

	def _increase_age(self):
		"""年齢を1増やす"""
		try:
			current = int(self.age.value or 0)
			self.age.value = str(current + 1)
			self.update()
		except:
			self.age.value = "1"
			self.update()
	
	def _decrease_age(self):
		"""年齢を1減らす"""
		try:
			current = int(self.age.value or 0)
			if current > 0:
				self.age.value = str(current - 1)
				self.update()
		except:
			pass
	
	def _on_get_date_field_change(self, e):
		"""拾得日フィールドの変更（yyyy/mm/dd形式）"""
		value = e.control.value
		# スラッシュを除去して8桁の数字かチェック
		value_clean = value.replace("/", "")
		if len(value_clean) == 8 and value_clean.isdigit():
			try:
				year = int(value_clean[0:4])
				month = int(value_clean[4:6])
				day = int(value_clean[6:8])
				
				# 日付の存在チェック
				from datetime import datetime
				datetime(year, month, day)  # 存在しない日付の場合は例外が発生
				
				self.get_date_value = f"{year:04d}-{month:02d}-{day:02d}"
				self.get_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
				self.get_date_field.border_color = ft.colors.GREEN
			except ValueError:
				self.get_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.get_date_field.border_color = ft.colors.RED
				if "get_date" in self.error_texts:
					self.error_texts["get_date"].value = "存在しない日付です"
					self.error_texts["get_date"].visible = True
			except:
				self.get_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.get_date_field.border_color = ft.colors.RED
		else:
			self.get_date_icon.content = None
			self.get_date_field.border_color = None
			if "get_date" in self.error_texts:
				self.error_texts["get_date"].visible = False
		self.update()
	
	def _on_recep_date_field_change(self, e):
		"""受付日フィールドの変更（yyyy/mm/dd形式）"""
		value = e.control.value
		# スラッシュを除去して8桁の数字かチェック
		value_clean = value.replace("/", "")
		if len(value_clean) == 8 and value_clean.isdigit():
			try:
				year = int(value_clean[0:4])
				month = int(value_clean[4:6])
				day = int(value_clean[6:8])
				
				# 日付の存在チェック
				from datetime import datetime
				datetime(year, month, day)  # 存在しない日付の場合は例外が発生
				
				self.recep_date_value = f"{year:04d}-{month:02d}-{day:02d}"
				self.recep_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
				self.recep_date_field.border_color = ft.colors.GREEN
			except ValueError:
				self.recep_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.recep_date_field.border_color = ft.colors.RED
				if "recep_date" in self.error_texts:
					self.error_texts["recep_date"].value = "存在しない日付です"
					self.error_texts["recep_date"].visible = True
			except:
				self.recep_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.recep_date_field.border_color = ft.colors.RED
		else:
			self.recep_date_icon.content = None
			self.recep_date_field.border_color = None
			if "recep_date" in self.error_texts:
				self.error_texts["recep_date"].visible = False
		self.update()
	
	def _on_expiry_date_field_change(self, e):
		"""消費期限フィールドの変更（yyyy/mm/dd形式）"""
		value = e.control.value
		# スラッシュを除去して8桁の数字かチェック
		value_clean = value.replace("/", "")
		if len(value_clean) == 8 and value_clean.isdigit():
			try:
				year = int(value_clean[0:4])
				month = int(value_clean[4:6])
				day = int(value_clean[6:8])
				
				# 日付の存在チェック
				from datetime import datetime
				datetime(year, month, day)  # 存在しない日付の場合は例外が発生
				
				self.expiry_date_value = f"{year:04d}-{month:02d}-{day:02d}"
				self.expiry_date_field.border_color = ft.colors.GREEN
			except ValueError:
				self.expiry_date_field.border_color = ft.colors.RED
				if self.page:
					self.page.snack_bar.content = ft.Text("存在しない日付です", color=ft.colors.WHITE)
					self.page.snack_bar.bgcolor = ft.colors.RED_700
					self.page.snack_bar.open = True
			except:
				self.expiry_date_field.border_color = ft.colors.RED
		else:
			self.expiry_date_field.border_color = None
		self.update()
	
	def _on_get_date_change(self, e):
		"""カレンダーから拾得日を選択"""
		if e.control.value:
			self.get_date_value = str(e.control.value).split()[0]
			# フィールドにも反映（yyyy/mm/dd形式）
			self.get_date_field.value = self.get_date_value.replace("-", "/")
			self.get_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			# UIを更新
			self.update()

	def _on_recep_date_change(self, e):
		"""カレンダーから受付日を選択"""
		if e.control.value:
			self.recep_date_value = str(e.control.value).split()[0]
			# フィールドにも反映（yyyy/mm/dd形式）
			self.recep_date_field.value = self.recep_date_value.replace("-", "/")
			self.recep_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			# UIを更新
			self.update()
	
	def _on_expiry_date_change(self, e):
		"""カレンダーから消費期限を選択"""
		if e.control.value:
			self.expiry_date_value = str(e.control.value).split()[0]
			# フィールドにも反映（yyyy/mm/dd形式）
			self.expiry_date_field.value = self.expiry_date_value.replace("-", "/")
			# UIを更新
			self.update()
	
	def _check_if_money(self):
		"""現金かどうかをチェックして、金種登録ボタンの表示を切り替え"""
		is_money = False
		
		# 大、中、小のいずれかに「現金」が含まれているかチェック
		if self.item_class_L.value and "現金" in self.item_class_L.value:
			is_money = True
		elif self.item_class_M.value and "現金" in self.item_class_M.value:
			is_money = True
		elif self.item_class_S.value and "現金" in self.item_class_S.value:
			is_money = True
		
		# 金種登録ボタンの表示を切り替え
		if hasattr(self, 'money_button_in_form') and self.money_button_in_form:
			self.money_button_in_form.visible = is_money
			self.is_money_mode = is_money
			self.update()
	
	def _validate_item_class(self):
		"""分類全体のバリデーション（大中小すべて入力されている必要あり）"""
		has_L = bool(self.item_class_L.value)
		has_M = bool(self.item_class_M.value)
		has_S = bool(self.item_class_S.value)
		
		is_valid = has_L and has_M and has_S
		self.validation_states["item_class"] = is_valid
		
		# アイコンの更新
		if is_valid:
			self.item_class_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.item_class_L.border_color = ft.colors.GREEN
			self.item_class_M.border_color = ft.colors.GREEN
			self.item_class_S.border_color = ft.colors.GREEN
			if "item_class" in self.error_texts:
				self.error_texts["item_class"].visible = False
		else:
			# 少なくとも1つ入力されている場合はエラー表示
			if has_L or has_M or has_S:
				self.item_class_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.item_class_L.border_color = ft.colors.RED if not has_L else None
				self.item_class_M.border_color = ft.colors.RED if not has_M else None
				self.item_class_S.border_color = ft.colors.RED if not has_S else None
				if "item_class" in self.error_texts:
					self.error_texts["item_class"].value = "分類（大・中・小）すべて選択してください"
					self.error_texts["item_class"].visible = True
			else:
				self.item_class_icon.content = None
				self.item_class_L.border_color = None
				self.item_class_M.border_color = None
				self.item_class_S.border_color = None
				if "item_class" in self.error_texts:
					self.error_texts["item_class"].visible = False
		
		self.update()

	def submit(self):
		# バリデーションチェック
		has_error = False
		
		# 拾得者区分が選択されているかチェック（必須）
		if not self.finder_type.value:
			if "finder_type" in self.error_texts:
				self.error_texts["finder_type"].value = "拾得者区分を選択してください"
				self.error_texts["finder_type"].visible = True
			has_error = True
		
		# 新規必須項目のチェック
		# 届出要否
		if not self.report_necessity.value:
			self.report_necessity_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.report_necessity.border_color = ft.colors.RED
			self.error_texts["report_necessity"].value = "届出要否を選択してください"
			self.error_texts["report_necessity"].visible = True
			has_error = True
		
		# 警察届出用拾得場所（任意項目なのでバリデーションなし）
		
		# 担当者（アカウント情報から取得するためバリデーションなし）
		
		# 拾得日・時刻（必須）
		if not self.get_date_value or not self.get_date_field.value:
			self.get_date_field.border_color = ft.colors.RED
			self.get_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			if "get_date" in self.error_texts:
				self.error_texts["get_date"].value = "拾得日を入力してください"
				self.error_texts["get_date"].visible = True
			has_error = True
		
		if not self.get_hour.value or not self.get_min.value:
			self.get_hour.border_color = ft.colors.RED
			self.get_min.border_color = ft.colors.RED
			if "get_time" in self.error_texts:
				self.error_texts["get_time"].value = "拾得時刻を入力してください"
				self.error_texts["get_time"].visible = True
			has_error = True
		
		# 受付日・時刻（必須）
		if not self.recep_date_value or not self.recep_date_field.value:
			self.recep_date_field.border_color = ft.colors.RED
			self.recep_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			if "recep_date" in self.error_texts:
				self.error_texts["recep_date"].value = "受付日を入力してください"
				self.error_texts["recep_date"].visible = True
			has_error = True
		
		if not self.recep_hour.value or not self.recep_min.value:
			self.recep_hour.border_color = ft.colors.RED
			self.recep_min.border_color = ft.colors.RED
			if "recep_time" in self.error_texts:
				self.error_texts["recep_time"].value = "受付時刻を入力してください"
				self.error_texts["recep_time"].visible = True
			has_error = True
		
		# 拾得者区分が選択されているかチェック
		if not self.finder_type.value:
			has_error = True
		elif self.finder_type.value == "第三者拾得":
			# 第三者拾得の必須項目をチェック
			if not self.finder_name.value or not self.finder_name.value.strip():
				self.finder_name_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.finder_name.border_color = ft.colors.RED
				self.error_texts["finder_name"].value = "拾得者氏名を入力してください"
				self.error_texts["finder_name"].visible = True
				has_error = True
			
			if not self.own_waiver.value:
				self.own_waiver_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.own_waiver.border_color = ft.colors.RED
				self.error_texts["own_waiver"].value = "権利放棄を選択してください"
				self.error_texts["own_waiver"].visible = True
				has_error = True
			
			if not self.note.value:
				self.note_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.note.border_color = ft.colors.RED
				self.error_texts["note"].value = "氏名等告示を選択してください"
				self.error_texts["note"].visible = True
				has_error = True
				
		elif self.finder_type.value == "占有者拾得":
			# 占有者拾得の必須項目をチェック
			if not self.owner_name.value or not self.owner_name.value.strip():
				self.owner_name_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.owner_name.border_color = ft.colors.RED
				self.error_texts["owner_name"].value = "占有者の氏名を入力してください"
				self.error_texts["owner_name"].visible = True
				has_error = True
			
			if not self.own_waiver_owner.value:
				self.own_waiver_owner_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.own_waiver_owner.border_color = ft.colors.RED
				self.error_texts["own_waiver_owner"].value = "占有者権利放棄を選択してください"
				self.error_texts["own_waiver_owner"].visible = True
				has_error = True
			
			if not self.note_owner.value:
				self.note_owner_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.note_owner.border_color = ft.colors.RED
				self.error_texts["note_owner"].value = "占有者氏名等告示を選択してください"
				self.error_texts["note_owner"].visible = True
				has_error = True
		
		# 共通の必須項目
		# 拾得場所のバリデーション（手入力またはドロップダウン）
		if self.find_place.visible:
			# ドロップダウンモードの場合
			if not self.find_place.value or not self.find_place.value.strip():
				self.find_place_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.find_place.border_color = ft.colors.RED
				self.error_texts["find_place"].value = "拾得場所を選択してください"
				self.error_texts["find_place"].visible = True
				has_error = True
		else:
			# 手入力モードの場合（デフォルト）
			if not self.find_place_custom.value or not self.find_place_custom.value.strip():
				self.find_place_custom_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
				self.find_place_custom.border_color = ft.colors.RED
				self.error_texts["find_place"].value = "拾得場所を入力してください"
				self.error_texts["find_place"].visible = True
				has_error = True
		
		if not self.storage_place.value:
			self.storage_place_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.storage_place.border_color = ft.colors.RED
			self.error_texts["storage_place"].value = "保管場所を選択してください"
			self.error_texts["storage_place"].visible = True
			has_error = True
		
		# 分類（大中小すべて必須）
		has_L = bool(self.item_class_L.value)
		has_M = bool(self.item_class_M.value)
		has_S = bool(self.item_class_S.value)
		
		if not (has_L and has_M and has_S):
			self.item_class_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.item_class_L.border_color = ft.colors.RED if not has_L else None
			self.item_class_M.border_color = ft.colors.RED if not has_M else None
			self.item_class_S.border_color = ft.colors.RED if not has_S else None
			self.error_texts["item_class"].value = "分類（大・中・小）すべて選択してください"
			self.error_texts["item_class"].visible = True
			has_error = True
		
		# 現金の場合、金種登録が必須
		if self.is_money_mode and not self.money_data:
			if self.page:
				self.page.snack_bar = ft.SnackBar(
					content=ft.Text("現金の場合は金種登録が必須です。", color=ft.colors.WHITE),
					bgcolor=ft.colors.RED_700
				)
				self.page.snack_bar.open = True
			has_error = True
		
		if has_error:
			# エラーバナーを表示
			if self.error_banner:
				self.error_banner.visible = True
			
			# ページの先頭にスクロール（フォームコンテンツを再構築）
			self.update()
			
			# スクロール位置をトップに戻す
			if self.page:
				self.page.scroll = "always"
				# コンテンツを更新してページトップに移動
				self.content = self.create_form_view()
				self.update()
			
			# スナックバーは表示しない（エラーバナーで代替）
			return
		
		# バリデーション成功時は通常の処理
		if callable(self.on_submit):
			# エラーバナーを非表示
			if self.error_banner:
				self.error_banner.visible = False
			
			self.on_submit(self.collect())
			
			# 登録成功メッセージを表示してホームに戻る
			if self.page:
				self.page.snack_bar = ft.SnackBar(
					content=ft.Text("拾得物の登録が完了しました", color=ft.colors.WHITE),
					bgcolor=ft.colors.GREEN_700
				)
				self.page.snack_bar.open = True
				self.page.update()
				
				# 少し遅延してからホームに戻る
				import threading
				import time
				def go_home():
					time.sleep(1.0)  # 1秒待機
					if self.page:
						self.page.go("/")
				threading.Thread(target=go_home, daemon=True).start()

	def temp_save(self):
		if callable(self.on_temp_save):
			self.on_temp_save(self.collect())

	def _validate_finder_name(self, e):
		"""拾得者氏名のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["finder_name"] = is_valid
		
		# アイコンの更新
		if is_valid:
			self.finder_name_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.finder_name.border_color = ft.colors.GREEN
			self.error_texts["finder_name"].visible = False
		elif value:  # 値がある but 無効
			self.finder_name_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.finder_name.border_color = ft.colors.RED
			self.error_texts["finder_name"].value = "拾得者氏名を入力してください"
			self.error_texts["finder_name"].visible = True
		else:
			self.finder_name_icon.content = None
			self.finder_name.border_color = None
			self.error_texts["finder_name"].visible = False
		
		self.update()
	
	def _validate_owner_name(self, e):
		"""占有者氏名のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["owner_name"] = is_valid
		
		if is_valid:
			self.owner_name_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.owner_name.border_color = ft.colors.GREEN
			self.error_texts["owner_name"].visible = False
		elif value:
			self.owner_name_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.owner_name.border_color = ft.colors.RED
			self.error_texts["owner_name"].value = "占有者の氏名を入力してください"
			self.error_texts["owner_name"].visible = True
		else:
			self.owner_name_icon.content = None
			self.owner_name.border_color = None
			self.error_texts["owner_name"].visible = False
		
		self.update()
	
	def _validate_find_place(self, e):
		"""拾得場所のバリデーション（ドロップダウン）"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["find_place"] = is_valid
		
		if is_valid:
			self.find_place_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.find_place.border_color = ft.colors.GREEN
			self.error_texts["find_place"].visible = False
		elif value:
			self.find_place_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.find_place.border_color = ft.colors.RED
			self.error_texts["find_place"].value = "拾得場所を選択してください"
			self.error_texts["find_place"].visible = True
		else:
			self.find_place_icon.content = None
			self.find_place.border_color = None
			self.error_texts["find_place"].visible = False
		
		self.update()
	
	def _validate_own_waiver(self, e):
		"""権利放棄のバリデーション"""
		value = e.control.value
		is_valid = bool(value)
		self.validation_states["own_waiver"] = is_valid
		
		if is_valid:
			self.own_waiver_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.own_waiver.border_color = ft.colors.GREEN
			self.error_texts["own_waiver"].visible = False
		else:
			self.own_waiver_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.own_waiver.border_color = ft.colors.RED
			self.error_texts["own_waiver"].value = "権利放棄を選択してください"
			self.error_texts["own_waiver"].visible = True
		
		self.update()
	
	def _validate_note(self, e):
		"""氏名等告示のバリデーション"""
		value = e.control.value
		is_valid = bool(value)
		self.validation_states["note"] = is_valid
		
		if is_valid:
			self.note_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.note.border_color = ft.colors.GREEN
			self.error_texts["note"].visible = False
		else:
			self.note_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.note.border_color = ft.colors.RED
			self.error_texts["note"].value = "氏名等告示を選択してください"
			self.error_texts["note"].visible = True
		
		self.update()
	
	def _validate_own_waiver_owner(self, e):
		"""占有者権利放棄のバリデーション"""
		value = e.control.value
		is_valid = bool(value)
		self.validation_states["own_waiver_owner"] = is_valid
		
		if is_valid:
			self.own_waiver_owner_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.own_waiver_owner.border_color = ft.colors.GREEN
			self.error_texts["own_waiver_owner"].visible = False
		else:
			self.own_waiver_owner_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.own_waiver_owner.border_color = ft.colors.RED
			self.error_texts["own_waiver_owner"].value = "占有者権利放棄を選択してください"
			self.error_texts["own_waiver_owner"].visible = True
		
		self.update()
	
	def _validate_note_owner(self, e):
		"""占有者氏名等告示のバリデーション"""
		value = e.control.value
		is_valid = bool(value)
		self.validation_states["note_owner"] = is_valid
		
		if is_valid:
			self.note_owner_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.note_owner.border_color = ft.colors.GREEN
			self.error_texts["note_owner"].visible = False
		else:
			self.note_owner_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.note_owner.border_color = ft.colors.RED
			self.error_texts["note_owner"].value = "占有者氏名等告示を選択してください"
			self.error_texts["note_owner"].visible = True
		
		self.update()
	
	def _validate_storage_place(self, e):
		"""保管場所のバリデーション"""
		value = e.control.value
		is_valid = bool(value)
		self.validation_states["storage_place"] = is_valid
		
		if is_valid:
			self.storage_place_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.storage_place.border_color = ft.colors.GREEN
			self.error_texts["storage_place"].visible = False
		else:
			self.storage_place_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.storage_place.border_color = ft.colors.RED
			self.error_texts["storage_place"].value = "保管場所を選択してください"
			self.error_texts["storage_place"].visible = True
		
		self.update()
	
	def _validate_feature(self, e):
		"""特徴のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["feature"] = is_valid
		
		if is_valid:
			self.feature_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.feature.border_color = ft.colors.GREEN
			self.error_texts["feature"].visible = False
		elif value:
			self.feature_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.feature.border_color = ft.colors.RED
			self.error_texts["feature"].value = "特徴を入力してください"
			self.error_texts["feature"].visible = True
		else:
			self.feature_icon.content = None
			self.feature.border_color = None
			self.error_texts["feature"].visible = False
		
		self.update()
	
	def _validate_report_necessity(self, e):
		"""届出要否のバリデーション"""
		value = e.control.value
		is_valid = bool(value)
		self.validation_states["report_necessity"] = is_valid
		
		if is_valid:
			self.report_necessity_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.report_necessity.border_color = ft.colors.GREEN
			self.error_texts["report_necessity"].visible = False
		else:
			self.report_necessity_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.report_necessity.border_color = ft.colors.RED
			self.error_texts["report_necessity"].value = "届出要否を選択してください"
			self.error_texts["report_necessity"].visible = True
		
		self.update()
	
	def _validate_police_find_place(self, e):
		"""警察届出用拾得場所のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["police_find_place"] = is_valid
		
		if is_valid:
			self.police_find_place_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.police_find_place.border_color = ft.colors.GREEN
			self.error_texts["police_find_place"].visible = False
		elif value:
			self.police_find_place_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.police_find_place.border_color = ft.colors.RED
			self.error_texts["police_find_place"].value = "警察届出用拾得場所を入力してください"
			self.error_texts["police_find_place"].visible = True
		else:
			self.police_find_place_icon.content = None
			self.police_find_place.border_color = None
			self.error_texts["police_find_place"].visible = False
		
		self.update()
	
	def open_money_registration(self):
		"""金種登録画面を開く"""
		# 現在の入力内容を一時保存（collectは呼ばない）
		
		money_view = MoneyRegistrationView(
			on_complete=self._on_money_complete,
			on_cancel=self._on_money_cancel,
			initial_data=self.money_data if self.money_data else {}
		)
		
		self.current_screen = "money"
		
		# 画面を差し替える
		if self.page:
			# 現在のページのコンテンツを差し替える
			parent = self.parent()
			if parent:
				parent.content = money_view
				parent.update()
		
		self.update()
	
	def _on_money_complete(self, money_data):
		"""金種登録完了時の処理"""
		self.money_data = money_data
		self.is_money_mode = True
		self.current_screen = "form"
		
		# フォーム画面に戻す
		if self.page:
			parent = self.parent()
			if parent:
				form_view = self.create_form_view()
				parent.content = form_view
				parent.update()
		
		self.update()
	
	def _on_money_cancel(self):
		"""金種登録キャンセル時の処理"""
		self.current_screen = "form"
		
		# フォーム画面に戻す
		if self.page:
			parent = self.parent()
			if parent:
				form_view = self.create_form_view()
				parent.content = form_view
				parent.update()
		
		self.update()
	
	def collect(self):
		return {
			"finder_type": self.finder_type.value,
			"get_date": self.get_date_value,
			"get_hour": self.get_hour.value,
			"get_min": self.get_min.value,
			"recep_date": self.recep_date_value,
			"recep_hour": self.recep_hour.value,
			"recep_min": self.recep_min.value,
			"find_place": self.find_place_custom.value if self.find_place_custom.visible else self.find_place.value,
			"finder_name": self.finder_name.value,
			"gender": self.gender.value,
			"age": self.age.value,
			"address": None if self.address_unknown.value else self.address.value,
			"postal_code": self.postal_code.value,
			"tel1": self.tel1.value,
			"tel2": self.tel2.value,
			"own_waiver": self.own_waiver.value,
			"note": self.note.value,
			"own_waiver_owner": self.own_waiver_owner.value,
			"note_owner": self.note_owner.value,
			"item_class_L": self.item_class_L.value,
			"item_class_M": self.item_class_M.value,
			"item_class_S": self.item_class_S.value,
			"color": self.color.value,
			"feature": self.feature.value,
			"storage_place": self.storage_place.value,
			"owner_affiliation": self.owner_affiliation.value,
			"owner_name": self.owner_name.value,
			"owner_gender": self.owner_gender.value,
			"captured_photos": self.captured_photos_data,
			# 新規フィールド
			"report_necessity": self.report_necessity.value,
			"police_find_place": self.police_find_place.value,
			"staff": self.staff.value,
			"store_name": self.store_name.value if hasattr(self.store_name, 'value') else "店舗A",
			"is_valuable": self.is_valuable.value,
			"expiry_date": self.expiry_date_value,
			"remarks": self.remarks.value,
			"money_data": self.money_data if self.is_money_mode else None,
		}


# 使用例:
# カメラ撮影とフォーム入力の統合ビューを使用する場合:
# register_flow = RegisterFlowView(
#     on_submit=lambda data: print("登録完了:", data),
#     on_temp_save=lambda data: print("一時保存:", data)
# )
# 
# 注意: RegisterFlowViewはカメラ画面から開始されます
# RegisterFormViewを直接使用するとフォーム画面から開始されるため注意してください
