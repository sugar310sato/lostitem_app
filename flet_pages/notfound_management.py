import flet as ft
from datetime import datetime, date
from apps.config import COLOR, SEX, ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S

MINUTES_15 = ["00", "15", "30", "45"]
HOURS = [f"{h:02d}" for h in range(0, 24)]


def nearest_15min(dt: datetime):
	m = dt.minute
	closest = min([0, 15, 30, 45], key=lambda x: abs(x - m))
	return f"{dt.hour:02d}", f"{closest:02d}"


class NotFoundManagementView(ft.UserControl):
	def __init__(self, on_submit=None, on_temp_save=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_temp_save = on_temp_save
		self.lost_date_value = date.today().isoformat()
		self.recep_date_value = date.today().isoformat()
		self._date_pickers_added = False
		# 日付表示用のTextコントロール
		self.lost_date_text = None
		self.recep_date_text = None
		# ダイアログ管理
		self.current_dialog = None

	def build(self):
		# 初期時刻
		nh, nm = nearest_15min(datetime.now())

		# 日付ピッカー（ページオーバーレイに追加してから使用）
		self.lost_date = ft.DatePicker(
			on_change=self._on_lost_date_change
		)
		self.recep_date = ft.DatePicker(
			on_change=self._on_recep_date_change
		)
		self.lost_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.lost_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)
		self.recep_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.recep_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)

		# 日付表示用のTextコントロールを作成
		self.lost_date_text = ft.Text(f"{self.lost_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.recep_date_text = ft.Text(f"{self.recep_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)

		# 基本情報
		self.recep_manager = ft.TextField(label="受付者", width=200)
		self.lost_area = ft.TextField(label="遺失場所", width=300)
		self.lost_name = ft.TextField(label="遺失者名", width=200)
		self.lost_age = ft.TextField(label="年齢", width=100, keyboard_type=ft.KeyboardType.NUMBER)
		self.lost_sex = ft.RadioGroup(value="男性", content=ft.Row([
			ft.Radio(value="男性", label="男性"),
			ft.Radio(value="女性", label="女性"),
			ft.Radio(value="その他", label="その他"),
		]))
		self.lost_post = ft.TextField(label="郵便番号", width=150)
		self.lost_address = ft.TextField(label="住所", width=300, multiline=True, min_lines=1)
		self.lost_tel1 = ft.TextField(label="連絡先1", width=200)
		self.lost_tel2 = ft.TextField(label="連絡先2", width=200)

		# 物品情報
		self.item_value = ft.Checkbox(label="貴重な物品に該当")
		self.item_feature = ft.TextField(label="物品の特徴", width=300, multiline=True, min_lines=2)
		self.item_color = ft.Dropdown(label="色", options=[ft.dropdown.Option(x[0]) for x in COLOR], width=200)
		self.item_maker = ft.TextField(label="メーカー", width=200)
		self.item_expiration = ft.DatePicker(on_change=self._on_expiration_date_change)
		self.item_expiration_text = ft.Text(f"", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.item_num = ft.TextField(label="数量", width=100, keyboard_type=ft.KeyboardType.NUMBER)
		self.item_unit = ft.TextField(label="単位", width=100)
		self.item_price = ft.TextField(label="値段", width=150)
		self.item_money = ft.TextField(label="金額", width=150)
		self.item_remarks = ft.TextField(label="備考", width=300, multiline=True, min_lines=2)

		# カード情報
		self.card_company = ft.TextField(label="カード発行会社名", width=200)
		self.card_tel = ft.TextField(label="カード発行会社連絡先", width=200)
		self.card_name = ft.TextField(label="カード名", width=200)
		self.card_person = ft.TextField(label="カード記載人名", width=200)
		self.card_contact_date = ft.DatePicker(on_change=self._on_card_contact_date_change)
		self.card_contact_date_text = ft.Text(f"", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.card_return_date = ft.DatePicker(on_change=self._on_card_return_date_change)
		self.card_return_date_text = ft.Text(f"", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.card_contact_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.card_contact_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)
		self.card_manager = ft.TextField(label="連絡者", width=200)

		# 物件分類
		self.item_class_L = ft.Dropdown(label="---", options=[ft.dropdown.Option(x) for x in ITEM_CLASS_L], width=150)
		self.item_class_M = ft.Dropdown(label="---", width=150)
		self.item_class_S = ft.Dropdown(label="---", width=150)

		# L→M→S の連動
		def on_L_change(e):
			val = self.item_class_L.value
			m_opts = [m["value"] for m in ITEM_CLASS_M if m.get("data-val") == val]
			self.item_class_M.options = [ft.dropdown.Option(x) for x in m_opts]
			self.item_class_M.value = None
			self.item_class_M.update()
			self.item_class_S.options = []
			self.item_class_S.value = None
			self.item_class_S.update()
		self.item_class_L.on_change = on_L_change

		def on_M_change(e):
			val = self.item_class_M.value
			s_opts = [s["value"] for s in ITEM_CLASS_S if s.get("data-val") == val]
			self.item_class_S.options = [ft.dropdown.Option(x) for x in s_opts]
			self.item_class_S.value = None
			self.item_class_S.update()
		self.item_class_M.on_change = on_M_change

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
			self.recep_manager,
			self.lost_area,
			self.lost_name,
			self.lost_age,
			self.lost_post,
			self.lost_address,
			self.lost_tel1,
			self.lost_tel2,
			self.item_feature,
			self.item_maker,
			self.item_num,
			self.item_unit,
			self.item_price,
			self.item_money,
			self.item_remarks,
		])

		# レイアウト
		section_basic_style = dict(padding=10, bgcolor=ft.colors.BLUE_50, border_radius=8, border=ft.border.all(1, ft.colors.BLUE_100))
		section_person_style = dict(padding=10, bgcolor=ft.colors.GREEN_50, border_radius=8, border=ft.border.all(1, ft.colors.GREEN_100))
		section_item_style = dict(padding=10, bgcolor=ft.colors.ORANGE_50, border_radius=8, border=ft.border.all(1, ft.colors.ORANGE_100))
		section_card_style = dict(padding=10, bgcolor=ft.colors.PURPLE_50, border_radius=8, border=ft.border.all(1, ft.colors.PURPLE_100))

		# 基本情報
		section_basic = ft.Container(
			content=ft.Column([
				ft.Text("基本情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([ft.Text("受付者", width=120), self.recep_manager], wrap=True),
				ft.Row([
					ft.Text("遺失日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.lost_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.lost_date.pick_date()
					),
					ft.Text("遺失時刻", width=120), self.lost_hour, ft.Text(":"), self.lost_min,
				], wrap=True),
				ft.Row([
					ft.Text("受付日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.recep_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.recep_date.pick_date()
					),
					ft.Text("受付時刻", width=120), self.recep_hour, ft.Text(":"), self.recep_min,
				], wrap=True),
				ft.Row([ft.Text("遺失場所", width=120), self.lost_area], wrap=True),
			]),
			**section_basic_style
		)

		# 遺失者情報
		section_person = ft.Container(
			content=ft.Column([
				ft.Text("遺失者情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([ft.Text("遺失者名", width=120), self.lost_name], wrap=True),
				ft.Row([ft.Text("年齢", width=120), self.lost_age, ft.Text("性別", width=120), self.lost_sex], wrap=True),
				ft.Row([ft.Text("郵便番号", width=120), self.lost_post], wrap=True),
				ft.Row([ft.Text("住所", width=120), self.lost_address], wrap=True),
				ft.Row([ft.Text("連絡先", width=120), self.lost_tel1, self.lost_tel2], wrap=True),
			]),
			**section_person_style
		)

		# 物品情報
		section_item = ft.Container(
			content=ft.Column([
				ft.Text("物品情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([ft.Text("分類", width=120), ft.Text("大", width=30), self.item_class_L, ft.Text("中", width=30), self.item_class_M, ft.Text("小", width=30), self.item_class_S]),
				ft.Row([ft.Text("色", width=120), self.item_color], wrap=True),
				ft.Row([ft.Text("特徴", width=120), self.item_feature], wrap=True),
				ft.Row([ft.Text("メーカー", width=120), self.item_maker], wrap=True),
				ft.Row([
					ft.Text("消費期限", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.item_expiration_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.item_expiration.pick_date()
					),
				], wrap=True),
				ft.Row([ft.Text("数量", width=120), self.item_num, ft.Text("単位", width=120), self.item_unit], wrap=True),
				ft.Row([ft.Text("値段", width=120), self.item_price, ft.Text("金額", width=120), self.item_money], wrap=True),
				ft.Row([ft.Text("貴重品", width=120), self.item_value], wrap=True),
				ft.Row([ft.Text("備考", width=120), self.item_remarks], wrap=True),
			]),
			**section_item_style
		)

		# カード情報
		section_card = ft.Container(
			content=ft.Column([
				ft.Text("カード情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([ft.Text("発行会社名", width=120), self.card_company], wrap=True),
				ft.Row([ft.Text("会社連絡先", width=120), self.card_tel], wrap=True),
				ft.Row([ft.Text("カード名", width=120), self.card_name], wrap=True),
				ft.Row([ft.Text("記載人名", width=120), self.card_person], wrap=True),
				ft.Row([
					ft.Text("連絡日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.card_contact_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.card_contact_date.pick_date()
					),
					ft.Text("連絡時刻", width=120), self.card_contact_hour, ft.Text(":"), self.card_contact_min,
				], wrap=True),
				ft.Row([
					ft.Text("返還日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.card_return_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.card_return_date.pick_date()
					),
				], wrap=True),
				ft.Row([ft.Text("連絡者", width=120), self.card_manager], wrap=True),
			]),
			**section_card_style
		)

		layout = ft.Column([
			ft.Text("遺失物登録", size=22, weight=ft.FontWeight.BOLD),
			section_basic,
			section_person,
			section_item,
			section_card,
			ft.Row([
				ft.ElevatedButton("登録", on_click=lambda e: self.submit()),
				ft.OutlinedButton("一時保存", on_click=lambda e: self.temp_save()),
				ft.TextButton("ホームに戻る", on_click=lambda e: self.page.go("/")),
			])
		], expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)

		return layout

	def did_mount(self):
		# DatePicker をページオーバーレイに追加
		try:
			if not self._date_pickers_added and self.page is not None:
				self.page.overlay.append(self.lost_date)
				self.page.overlay.append(self.recep_date)
				self.page.overlay.append(self.item_expiration)
				self.page.overlay.append(self.card_contact_date)
				self.page.overlay.append(self.card_return_date)
				self.page.update()
				self._date_pickers_added = True
		except Exception:
			pass

	def _on_lost_date_change(self, e):
		if e.control.value:
			self.lost_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.lost_date_text.value = date_str
			# UIを更新
			self.update()

	def _on_recep_date_change(self, e):
		if e.control.value:
			self.recep_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.recep_date_text.value = date_str
			# UIを更新
			self.update()

	def _on_expiration_date_change(self, e):
		if e.control.value:
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.item_expiration_text.value = date_str
			# UIを更新
			self.update()

	def _on_card_contact_date_change(self, e):
		if e.control.value:
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.card_contact_date_text.value = date_str
			# UIを更新
			self.update()

	def _on_card_return_date_change(self, e):
		if e.control.value:
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.card_return_date_text.value = date_str
			# UIを更新
			self.update()

	def submit(self):
		if callable(self.on_submit):
			self.on_submit(self.collect())

	def temp_save(self):
		if callable(self.on_temp_save):
			self.on_temp_save(self.collect())
	
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
	
	def close_dialog(self):
		"""ダイアログを閉じる"""
		if self.page and hasattr(self, 'current_dialog') and self.current_dialog:
			if self.current_dialog in self.page.overlay:
				self.page.overlay.remove(self.current_dialog)
			self.current_dialog = None
			self.page.update()
	
	def show_success(self, message):
		"""成功メッセージを表示"""
		if self.page:
			self.page.snack_bar.content = ft.Text(message, color=ft.colors.GREEN)
			self.page.snack_bar.open = True
			self.page.update()

	def collect(self):
		return {
			"lost_date": self.lost_date_value,
			"lost_hour": self.lost_hour.value,
			"lost_min": self.lost_min.value,
			"recep_date": self.recep_date_value,
			"recep_hour": self.recep_hour.value,
			"recep_min": self.recep_min.value,
			"recep_manager": self.recep_manager.value,
			"lost_area": self.lost_area.value,
			"lost_name": self.lost_name.value,
			"lost_age": self.lost_age.value,
			"lost_sex": self.lost_sex.value,
			"lost_post": self.lost_post.value,
			"lost_address": self.lost_address.value,
			"lost_tel1": self.lost_tel1.value,
			"lost_tel2": self.lost_tel2.value,
			"item_value": self.item_value.value,
			"item_feature": self.item_feature.value,
			"item_color": self.item_color.value,
			"item_maker": self.item_maker.value,
			"item_expiration": self.item_expiration_text.value,
			"item_num": self.item_num.value,
			"item_unit": self.item_unit.value,
			"item_price": self.item_price.value,
			"item_money": self.item_money.value,
			"item_remarks": self.item_remarks.value,
			"item_class_L": self.item_class_L.value,
			"item_class_M": self.item_class_M.value,
			"item_class_S": self.item_class_S.value,
			"card_company": self.card_company.value,
			"card_tel": self.card_tel.value,
			"card_name": self.card_name.value,
			"card_person": self.card_person.value,
			"card_contact_date": self.card_contact_date_text.value,
			"card_return_date": self.card_return_date_text.value,
			"card_contact_hour": self.card_contact_hour.value,
			"card_contact_min": self.card_contact_min.value,
			"card_manager": self.card_manager.value,
		}
