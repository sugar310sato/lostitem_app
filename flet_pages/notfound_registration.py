import flet as ft
from datetime import datetime, date

MINUTES_15 = ["00", "15", "30", "45"]
HOURS = [f"{h:02d}" for h in range(0, 24)]

def nearest_15min(dt: datetime):
	"""15分刻みに丸める"""
	m = dt.minute
	closest = min([0, 15, 30, 45], key=lambda x: abs(x - m))
	return f"{dt.hour:02d}", f"{closest:02d}"

class NotFoundRegistrationView(ft.UserControl):
	"""遺失物登録フォーム専用ビュー"""
	def __init__(self, on_submit=None, on_cancel=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_cancel = on_cancel
		self.lost_date_value = date.today().isoformat()
		self.recep_date_value = date.today().isoformat()
		self._date_pickers_added = False
		
		# バリデーション状態を保持
		self.validation_states = {}
		# エラーメッセージ表示用のTextコントロール
		self.error_texts = {}
		
		# エラーメッセージ表示用
		self.error_banner = None
	
	def build(self):
		return self.create_form_view()
	
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
	
	def create_form_view(self):
		# 初期時刻
		nh, nm = nearest_15min(datetime.now())

		# 日付ピッカー
		self.lost_date = ft.DatePicker(
			on_change=self._on_lost_date_change
		)
		self.recep_date = ft.DatePicker(
			on_change=self._on_recep_date_change
		)
		
		# 時刻選択
		self.lost_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.lost_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)
		self.recep_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.recep_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)

		# 日付入力フィールド
		self.lost_date_field = ft.TextField(
			value=self.lost_date_value.replace("-", "/"),
			hint_text="yyyy/mm/dd",
			width=140,
			keyboard_type=ft.KeyboardType.TEXT,
			max_length=10,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._on_lost_date_field_change(e),
			on_focus=lambda e: self._on_date_field_focus(e, "lost_date")
		)
		self.recep_date_field = ft.TextField(
			value=self.recep_date_value.replace("-", "/"),
			hint_text="yyyy/mm/dd",
			width=140,
			keyboard_type=ft.KeyboardType.TEXT,
			max_length=10,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._on_recep_date_field_change(e),
			on_focus=lambda e: self._on_date_field_focus(e, "recep_date")
		)
		
		# バリデーション用アイコン
		self.lost_date_icon = ft.Container(width=24, height=24)
		self.recep_date_icon = ft.Container(width=24, height=24)
		
		# 必須項目
		self.customer_name = ft.TextField(
			hint_text="例: 山田太郎",
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_customer_name(e)
		)
		self.customer_name_icon = ft.Container(width=24, height=24)
		
		self.customer_tel = ft.TextField(
			hint_text="例: 090-1234-5678",
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_customer_tel(e)
		)
		self.customer_tel_icon = ft.Container(width=24, height=24)
		
		self.lost_place = ft.TextField(
			hint_text="例: 2階エントランス",
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_lost_place(e)
		)
		self.lost_place_icon = ft.Container(width=24, height=24)
		
		self.item_info = ft.TextField(
			hint_text="例: 黒い財布、ルイヴィトン",
			multiline=True,
			min_lines=2,
			max_lines=3,
			width=400,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_item_info(e)
		)
		self.item_info_icon = ft.Container(width=24, height=24)
		
		self.recep_staff = ft.TextField(
			hint_text="例: 田中",
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE,
			on_change=lambda e: self._validate_recep_staff(e)
		)
		self.recep_staff_icon = ft.Container(width=24, height=24)
		
		# 任意項目
		self.customer_address = ft.TextField(
			hint_text="例: 東京都千代田区...",
			multiline=True,
			min_lines=2,
			max_lines=3,
			width=400,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		self.remarks = ft.TextField(
			hint_text="備考",
			multiline=True,
			min_lines=2,
			max_lines=4,
			width=400,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		# エラーバナーの作成
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
			visible=False
		)
		
		# セクションスタイル
		section_style = dict(
			padding=15,
			bgcolor=ft.colors.WHITE,
			border_radius=8,
			border=ft.border.all(1, ft.colors.GREY_300)
		)
		
		# 基本情報セクション
		basic_section = ft.Container(
			content=ft.Column([
				ft.Text("基本情報", size=18, weight=ft.FontWeight.BOLD),
				
				# お客様ご氏名（必須）
				ft.Column([
					self.create_required_label("お客様ご氏名"),
					ft.Row([
						self.customer_name,
						self.customer_name_icon
					], spacing=10),
					self.create_error_text("customer_name")
				], spacing=5),
				
				# 電話（必須）
				ft.Column([
					self.create_required_label("電話"),
					ft.Row([
						self.customer_tel,
						self.customer_tel_icon
					], spacing=10),
					self.create_error_text("customer_tel")
				], spacing=5),
				
				# ご住所（任意）
				ft.Column([
					ft.Text("ご住所", size=14, weight=ft.FontWeight.BOLD),
					self.customer_address
				], spacing=5),
				
			], spacing=15),
			**section_style
		)
		
		# 遺失情報セクション
		lost_section = ft.Container(
			content=ft.Column([
				ft.Text("遺失情報", size=18, weight=ft.FontWeight.BOLD),
				
				# 遺失日時（必須）
				ft.Row([
					ft.Column([
						self.create_required_label("遺失日"),
						ft.Row([
							self.lost_date_field,
							ft.IconButton(
								icon=ft.icons.CALENDAR_MONTH,
								on_click=lambda e: self.lost_date.pick_date(),
								tooltip="カレンダーから選択"
							),
							self.lost_date_icon
						], spacing=5),
						self.create_error_text("lost_date")
					], spacing=5),
					
					ft.Column([
						self.create_required_label("遺失時刻"),
						ft.Row([
							self.lost_hour,
							ft.Text(":"),
							self.lost_min,
							ft.Text(" 頃", size=12, color=ft.colors.GREY_600)
						], spacing=5),
						self.create_error_text("lost_time")
					], spacing=5),
				], spacing=40),
				
				# 遺失場所（必須）
				ft.Column([
					self.create_required_label("遺失場所"),
					ft.Row([
						self.lost_place,
						self.lost_place_icon
					], spacing=10),
					self.create_error_text("lost_place")
				], spacing=5),
				
				# 金品情報（必須）
				ft.Column([
					self.create_required_label("金品情報"),
					ft.Row([
						self.item_info,
						self.item_info_icon
					], spacing=10),
					self.create_error_text("item_info")
				], spacing=5),
				
			], spacing=15),
			**section_style
		)
		
		# 受付情報セクション
		recep_section = ft.Container(
			content=ft.Column([
				ft.Text("受付情報", size=18, weight=ft.FontWeight.BOLD),
				
				# 受付日時（必須）
				ft.Row([
					ft.Column([
						self.create_required_label("受付日"),
						ft.Row([
							self.recep_date_field,
							ft.IconButton(
								icon=ft.icons.CALENDAR_MONTH,
								on_click=lambda e: self.recep_date.pick_date(),
								tooltip="カレンダーから選択"
							),
							self.recep_date_icon
						], spacing=5),
						self.create_error_text("recep_date")
					], spacing=5),
					
					ft.Column([
						self.create_required_label("受付時刻"),
						ft.Row([
							self.recep_hour,
							ft.Text(":"),
							self.recep_min
						], spacing=5),
						self.create_error_text("recep_time")
					], spacing=5),
				], spacing=40),
				
				# 受付者氏名（必須）
				ft.Column([
					self.create_required_label("受付者氏名"),
					ft.Row([
						self.recep_staff,
						self.recep_staff_icon
					], spacing=10),
					self.create_error_text("recep_staff")
				], spacing=5),
				
			], spacing=15),
			**section_style
		)
		
		# 備考セクション（任意）
		remarks_section = ft.Container(
			content=ft.Column([
				ft.Text("備考", size=18, weight=ft.FontWeight.BOLD),
				self.remarks
			], spacing=10),
			**section_style
		)
		
		# ボタン行
		button_row = ft.Container(
			content=ft.Row([
				# キャンセルボタン
				ft.OutlinedButton(
					"キャンセル", 
					on_click=lambda e: self.go_back(),
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
			padding=10
		)
		
		# フォーム全体
		form_content = ft.Column([
			# エラーバナー
			self.error_banner,
			
			# タイトル
			ft.Text("遺失物登録", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
			ft.Divider(),
			
			# 基本情報
			basic_section,
			
			# 遺失情報
			lost_section,
			
			# 受付情報
			recep_section,
			
			# 備考
			remarks_section,
			
			# ボタン
			button_row
		], 
		scroll=ft.ScrollMode.AUTO,
		spacing=15
		)
		
		return ft.Container(
			content=form_content,
			padding=20,
			bgcolor=ft.colors.GREY_100
		)
	
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
	
	def _on_lost_date_field_change(self, e):
		"""遺失日フィールドの変更"""
		value = e.control.value
		value_clean = value.replace("/", "")
		if len(value_clean) == 8 and value_clean.isdigit():
			try:
				year = int(value_clean[0:4])
				month = int(value_clean[4:6])
				day = int(value_clean[6:8])
				from datetime import datetime
				datetime(year, month, day)
				self.lost_date_value = f"{year:04d}-{month:02d}-{day:02d}"
				self.lost_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			except ValueError:
				self.lost_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
		else:
			self.lost_date_icon.content = None
		self.update()
	
	def _on_recep_date_field_change(self, e):
		"""受付日フィールドの変更"""
		value = e.control.value
		value_clean = value.replace("/", "")
		if len(value_clean) == 8 and value_clean.isdigit():
			try:
				year = int(value_clean[0:4])
				month = int(value_clean[4:6])
				day = int(value_clean[6:8])
				from datetime import datetime
				datetime(year, month, day)
				self.recep_date_value = f"{year:04d}-{month:02d}-{day:02d}"
				self.recep_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			except ValueError:
				self.recep_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
		else:
			self.recep_date_icon.content = None
		self.update()
	
	def _on_lost_date_change(self, e):
		"""カレンダーから遺失日を選択"""
		if e.control.value:
			self.lost_date_value = str(e.control.value).split()[0]
			self.lost_date_field.value = self.lost_date_value.replace("-", "/")
			self.lost_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.update()
	
	def _on_recep_date_change(self, e):
		"""カレンダーから受付日を選択"""
		if e.control.value:
			self.recep_date_value = str(e.control.value).split()[0]
			self.recep_date_field.value = self.recep_date_value.replace("-", "/")
			self.recep_date_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.update()
	
	def _validate_customer_name(self, e):
		"""お客様ご氏名のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["customer_name"] = is_valid
		
		if is_valid:
			self.customer_name_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.customer_name.border_color = ft.colors.GREEN
			self.error_texts["customer_name"].visible = False
		elif value:
			self.customer_name_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.customer_name.border_color = ft.colors.RED
			self.error_texts["customer_name"].value = "お客様ご氏名を入力してください"
			self.error_texts["customer_name"].visible = True
		else:
			self.customer_name_icon.content = None
			self.customer_name.border_color = None
			self.error_texts["customer_name"].visible = False
		self.update()
	
	def _validate_customer_tel(self, e):
		"""電話のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["customer_tel"] = is_valid
		
		if is_valid:
			self.customer_tel_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.customer_tel.border_color = ft.colors.GREEN
			self.error_texts["customer_tel"].visible = False
		elif value:
			self.customer_tel_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.customer_tel.border_color = ft.colors.RED
			self.error_texts["customer_tel"].value = "電話番号を入力してください"
			self.error_texts["customer_tel"].visible = True
		else:
			self.customer_tel_icon.content = None
			self.customer_tel.border_color = None
			self.error_texts["customer_tel"].visible = False
		self.update()
	
	def _validate_lost_place(self, e):
		"""遺失場所のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["lost_place"] = is_valid
		
		if is_valid:
			self.lost_place_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.lost_place.border_color = ft.colors.GREEN
			self.error_texts["lost_place"].visible = False
		elif value:
			self.lost_place_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.lost_place.border_color = ft.colors.RED
			self.error_texts["lost_place"].value = "遺失場所を入力してください"
			self.error_texts["lost_place"].visible = True
		else:
			self.lost_place_icon.content = None
			self.lost_place.border_color = None
			self.error_texts["lost_place"].visible = False
		self.update()
	
	def _validate_item_info(self, e):
		"""金品情報のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["item_info"] = is_valid
		
		if is_valid:
			self.item_info_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.item_info.border_color = ft.colors.GREEN
			self.error_texts["item_info"].visible = False
		elif value:
			self.item_info_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.item_info.border_color = ft.colors.RED
			self.error_texts["item_info"].value = "金品情報を入力してください"
			self.error_texts["item_info"].visible = True
		else:
			self.item_info_icon.content = None
			self.item_info.border_color = None
			self.error_texts["item_info"].visible = False
		self.update()
	
	def _validate_recep_staff(self, e):
		"""受付者氏名のバリデーション"""
		value = e.control.value
		is_valid = bool(value and value.strip())
		self.validation_states["recep_staff"] = is_valid
		
		if is_valid:
			self.recep_staff_icon.content = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=24)
			self.recep_staff.border_color = ft.colors.GREEN
			self.error_texts["recep_staff"].visible = False
		elif value:
			self.recep_staff_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.recep_staff.border_color = ft.colors.RED
			self.error_texts["recep_staff"].value = "受付者氏名を入力してください"
			self.error_texts["recep_staff"].visible = True
		else:
			self.recep_staff_icon.content = None
			self.recep_staff.border_color = None
			self.error_texts["recep_staff"].visible = False
		self.update()
	
	def submit(self):
		"""登録ボタン押下時の処理"""
		has_error = False
		
		# 必須項目のバリデーション
		if not self.customer_name.value or not self.customer_name.value.strip():
			self.customer_name_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.customer_name.border_color = ft.colors.RED
			self.error_texts["customer_name"].value = "お客様ご氏名を入力してください"
			self.error_texts["customer_name"].visible = True
			has_error = True
		
		if not self.customer_tel.value or not self.customer_tel.value.strip():
			self.customer_tel_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.customer_tel.border_color = ft.colors.RED
			self.error_texts["customer_tel"].value = "電話番号を入力してください"
			self.error_texts["customer_tel"].visible = True
			has_error = True
		
		if not self.lost_date_value or not self.lost_date_field.value:
			self.lost_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.error_texts["lost_date"].value = "遺失日を入力してください"
			self.error_texts["lost_date"].visible = True
			has_error = True
		
		if not self.lost_place.value or not self.lost_place.value.strip():
			self.lost_place_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.error_texts["lost_place"].value = "遺失場所を入力してください"
			self.error_texts["lost_place"].visible = True
			has_error = True
		
		if not self.item_info.value or not self.item_info.value.strip():
			self.item_info_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.error_texts["item_info"].value = "金品情報を入力してください"
			self.error_texts["item_info"].visible = True
			has_error = True
		
		if not self.recep_date_value or not self.recep_date_field.value:
			self.recep_date_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.error_texts["recep_date"].value = "受付日を入力してください"
			self.error_texts["recep_date"].visible = True
			has_error = True
		
		if not self.recep_staff.value or not self.recep_staff.value.strip():
			self.recep_staff_icon.content = ft.Icon(ft.icons.CANCEL, color=ft.colors.RED, size=24)
			self.error_texts["recep_staff"].value = "受付者氏名を入力してください"
			self.error_texts["recep_staff"].visible = True
			has_error = True
		
		if has_error:
			# エラーバナーを表示
			if self.error_banner:
				self.error_banner.visible = True
			self.update()
			return
		
		# バリデーション成功時は通常の処理
		if callable(self.on_submit):
			# エラーバナーを非表示
			if self.error_banner:
				self.error_banner.visible = False
			
			data = self.collect()
			self.on_submit(data)
			
			# 登録成功メッセージを表示
			if self.page:
				self.page.snack_bar = ft.SnackBar(
					content=ft.Text("遺失物の登録が完了しました", color=ft.colors.WHITE),
					bgcolor=ft.colors.GREEN_700
				)
				self.page.snack_bar.open = True
				self.page.update()
	
	def collect(self):
		"""入力データを収集"""
		return {
			"customer_name": self.customer_name.value,
			"customer_tel": self.customer_tel.value,
			"customer_address": self.customer_address.value,
			"lost_date": self.lost_date_value,
			"lost_hour": self.lost_hour.value,
			"lost_min": self.lost_min.value,
			"lost_place": self.lost_place.value,
			"item_info": self.item_info.value,
			"recep_date": self.recep_date_value,
			"recep_hour": self.recep_hour.value,
			"recep_min": self.recep_min.value,
			"recep_staff": self.recep_staff.value,
			"remarks": self.remarks.value
		}
	
	def go_back(self):
		"""キャンセルボタン押下時の処理"""
		if callable(self.on_cancel):
			self.on_cancel()
		elif self.page:
			self.page.go("/")
	
	def did_mount(self):
		"""マウント時の処理"""
		# DatePicker をページオーバーレイに追加
		try:
			if not self._date_pickers_added and self.page is not None:
				self.page.overlay.append(self.lost_date)
				self.page.overlay.append(self.recep_date)
				self.page.update()
				self._date_pickers_added = True
		except Exception:
			pass
