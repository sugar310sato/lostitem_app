import flet as ft
from datetime import datetime, date
from apps.config import REFUNDED_PROCESS

MINUTES_15 = ["00", "15", "30", "45"]
HOURS = [f"{h:02d}" for h in range(0, 24)]


def nearest_15min(dt: datetime):
	m = dt.minute
	closest = min([0, 15, 30, 45], key=lambda x: abs(x - m))
	return f"{dt.hour:02d}", f"{closest:02d}"


class RefundManagementView(ft.UserControl):
	def __init__(self, on_submit=None, on_temp_save=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_temp_save = on_temp_save
		self.start_date_value = date.today().isoformat()
		self.end_date_value = date.today().isoformat()
		# ダイアログ管理
		self.current_dialog = None
		self.refund_date_value = date.today().isoformat()
		self.police_date_value = date.today().isoformat()
		self.refund_expect_value = date.today().isoformat()
		self._date_pickers_added = False
		# 日付表示用のTextコントロール
		self.start_date_text = None
		self.end_date_text = None
		self.refund_date_text = None
		self.police_date_text = None
		self.refund_expect_text = None

	def build(self):
		# 初期時刻
		nh, nm = nearest_15min(datetime.now())

		# 日付ピッカー（ページオーバーレイに追加してから使用）
		self.start_date = ft.DatePicker(on_change=self._on_start_date_change)
		self.end_date = ft.DatePicker(on_change=self._on_end_date_change)
		self.refund_date = ft.DatePicker(on_change=self._on_refund_date_change)
		self.police_date = ft.DatePicker(on_change=self._on_police_date_change)
		self.refund_expect = ft.DatePicker(on_change=self._on_refund_expect_change)

		# 日付表示用のTextコントロールを作成
		self.start_date_text = ft.Text(f"{self.start_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.end_date_text = ft.Text(f"{self.end_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.refund_date_text = ft.Text(f"{self.refund_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.police_date_text = ft.Text(f"{self.police_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.refund_expect_text = ft.Text(f"{self.refund_expect_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)

		# 基本情報
		self.receipt_number = ft.TextField(label="受理番号", width=150, keyboard_type=ft.KeyboardType.NUMBER)
		self.finder_choice = ft.Dropdown(
			label="拾得者",
			options=[
				ft.dropdown.Option("すべて", "すべて"),
				ft.dropdown.Option("占有者拾得", "占有者拾得"),
				ft.dropdown.Option("第三者拾得", "第三者拾得"),
			],
			width=200
		)
		self.waiver = ft.Dropdown(
			label="権利",
			options=[
				ft.dropdown.Option("すべて", "すべて"),
				ft.dropdown.Option("権利行使", "権利行使"),
				ft.dropdown.Option("権利放棄", "権利放棄"),
			],
			width=200
		)
		self.refund_expect_year = ft.TextField(label="還付予定年", width=150, keyboard_type=ft.KeyboardType.NUMBER)
		self.refund_situation = ft.Dropdown(
			label="還付状況",
			options=[
				ft.dropdown.Option("還付予定", "還付予定"),
				ft.dropdown.Option("還付済み", "還付済み"),
			],
			width=200
		)

		# 還付処理関連
		self.returned = ft.Checkbox(label="還付済・警察返還済も表示")
		self.item_price = ft.Checkbox(label="貴重品のみ表示")
		self.item_feature = ft.TextField(label="特徴", width=300, multiline=True, min_lines=2)
		self.refund_manager = ft.Dropdown(
			label="担当者",
			options=[
				ft.dropdown.Option("選択してください", "選択してください"),
				ft.dropdown.Option("担当者A", "担当者A"),
				ft.dropdown.Option("担当者B", "担当者B"),
			],
			width=200
		)

		# 還付済物件処理
		self.refunded_process = ft.Dropdown(
			label="還付後処理",
			options=[ft.dropdown.Option(x[0]) for x in REFUNDED_PROCESS],
			width=200
		)
		self.refunded_bool = ft.Checkbox(label="処理済も表示")
		self.refunded_process_manager = ft.Dropdown(
			label="担当者1",
			options=[
				ft.dropdown.Option("選択してください", "選択してください"),
				ft.dropdown.Option("担当者A", "担当者A"),
				ft.dropdown.Option("担当者B", "担当者B"),
			],
			width=200
		)
		self.refunded_process_sub_manager = ft.Dropdown(
			label="担当者2",
			options=[
				ft.dropdown.Option("選択してください", "選択してください"),
				ft.dropdown.Option("担当者A", "担当者A"),
				ft.dropdown.Option("担当者B", "担当者B"),
			],
			width=200
		)

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
			self.receipt_number,
			self.finder_choice,
			self.waiver,
			self.refund_expect_year,
			self.item_feature,
			self.refund_manager,
		])

		# レイアウト
		section_basic_style = dict(padding=10, bgcolor=ft.colors.BLUE_50, border_radius=8, border=ft.border.all(1, ft.colors.BLUE_100))
		section_search_style = dict(padding=10, bgcolor=ft.colors.GREEN_50, border_radius=8, border=ft.border.all(1, ft.colors.GREEN_100))
		section_process_style = dict(padding=10, bgcolor=ft.colors.ORANGE_50, border_radius=8, border=ft.border.all(1, ft.colors.ORANGE_100))
		section_refunded_style = dict(padding=10, bgcolor=ft.colors.PURPLE_50, border_radius=8, border=ft.border.all(1, ft.colors.PURPLE_100))

		# 基本情報
		section_basic = ft.Container(
			content=ft.Column([
				ft.Text("基本情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([ft.Text("受理番号", width=120), self.receipt_number], wrap=True),
				ft.Row([ft.Text("拾得者", width=120), self.finder_choice], wrap=True),
				ft.Row([ft.Text("権利", width=120), self.waiver], wrap=True),
				ft.Row([ft.Text("還付予定年", width=120), self.refund_expect_year], wrap=True),
				ft.Row([ft.Text("還付状況", width=120), self.refund_situation], wrap=True),
			]),
			**section_basic_style
		)

		# 検索条件
		section_search = ft.Container(
			content=ft.Column([
				ft.Text("検索条件", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([
					ft.Text("開始日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.start_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.start_date.pick_date()
					),
					ft.Text("終了日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.end_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.end_date.pick_date()
					),
				], wrap=True),
				ft.Row([ft.Text("特徴", width=120), self.item_feature], wrap=True),
				ft.Row([ft.Text("還付済表示", width=120), self.returned], wrap=True),
				ft.Row([ft.Text("貴重品のみ", width=120), self.item_price], wrap=True),
			]),
			**section_search_style
		)

		# 還付処理
		section_process = ft.Container(
			content=ft.Column([
				ft.Text("還付処理", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([
					ft.Text("還付日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.refund_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.refund_date.pick_date()
					),
					ft.Text("担当者", width=120), self.refund_manager,
				], wrap=True),
				ft.Row([
					ft.Text("還付予定日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.refund_expect_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.refund_expect.pick_date()
					),
				], wrap=True),
			]),
			**section_process_style
		)

		# 還付済物件処理
		section_refunded = ft.Container(
			content=ft.Column([
				ft.Text("還付済物件処理", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([
					ft.Text("警察届出日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.police_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.police_date.pick_date()
					),
					ft.Text("還付後処理", width=120), self.refunded_process,
				], wrap=True),
				ft.Row([ft.Text("処理済表示", width=120), self.refunded_bool], wrap=True),
				ft.Row([ft.Text("担当者1", width=120), self.refunded_process_manager], wrap=True),
				ft.Row([ft.Text("担当者2", width=120), self.refunded_process_sub_manager], wrap=True),
			]),
			**section_refunded_style
		)

		layout = ft.Column([
			ft.Text("還付管理", size=22, weight=ft.FontWeight.BOLD),
			section_basic,
			section_search,
			section_process,
			section_refunded,
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
				self.page.overlay.append(self.start_date)
				self.page.overlay.append(self.end_date)
				self.page.overlay.append(self.refund_date)
				self.page.overlay.append(self.police_date)
				self.page.overlay.append(self.refund_expect)
				self.page.update()
				self._date_pickers_added = True
		except Exception:
			pass

	def _on_start_date_change(self, e):
		if e.control.value:
			self.start_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.start_date_text.value = date_str
			# UIを更新
			self.update()

	def _on_end_date_change(self, e):
		if e.control.value:
			self.end_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.end_date_text.value = date_str
			# UIを更新
			self.update()

	def _on_refund_date_change(self, e):
		if e.control.value:
			self.refund_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.refund_date_text.value = date_str
			# UIを更新
			self.update()

	def _on_police_date_change(self, e):
		if e.control.value:
			self.police_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.police_date_text.value = date_str
			# UIを更新
			self.update()

	def _on_refund_expect_change(self, e):
		if e.control.value:
			self.refund_expect_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.refund_expect_text.value = date_str
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
			"start_date": self.start_date_value,
			"end_date": self.end_date_value,
			"receipt_number": self.receipt_number.value,
			"finder_choice": self.finder_choice.value,
			"waiver": self.waiver.value,
			"refund_expect_year": self.refund_expect_year.value,
			"refund_situation": self.refund_situation.value,
			"returned": self.returned.value,
			"item_price": self.item_price.value,
			"item_feature": self.item_feature.value,
			"refund_date": self.refund_date_value,
			"refund_manager": self.refund_manager.value,
			"refunded_process": self.refunded_process.value,
			"refunded_bool": self.refunded_bool.value,
			"refunded_process_manager": self.refunded_process_manager.value,
			"refunded_process_sub_manager": self.refunded_process_sub_manager.value,
			"police_date": self.police_date_value,
			"refund_expect": self.refund_expect_value,
		}
