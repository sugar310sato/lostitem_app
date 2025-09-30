import flet as ft
from datetime import datetime, date
from apps.config import CHOICES_FINDER_POLICE

MINUTES_15 = ["00", "15", "30", "45"]
HOURS = [f"{h:02d}" for h in range(0, 24)]


def nearest_15min(dt: datetime):
	m = dt.minute
	closest = min([0, 15, 30, 45], key=lambda x: abs(x - m))
	return f"{dt.hour:02d}", f"{closest:02d}"


class PoliceManagementView(ft.UserControl):
	def __init__(self, on_submit=None, on_temp_save=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_temp_save = on_temp_save
		self.start_date_value = date.today().isoformat()
		self.end_date_value = date.today().isoformat()
		# ダイアログ管理
		self.current_dialog = None
		self.submit_date_value = date.today().isoformat()
		self._date_pickers_added = False
		# 日付表示用のTextコントロール
		self.start_date_text = None
		self.end_date_text = None
		self.submit_date_text = None

	def build(self):
		# 初期時刻
		nh, nm = nearest_15min(datetime.now())

		# 日付ピッカー（ページオーバーレイに追加してから使用）
		self.start_date = ft.DatePicker(on_change=self._on_start_date_change)
		self.end_date = ft.DatePicker(on_change=self._on_end_date_change)
		self.submit_date = ft.DatePicker(on_change=self._on_submit_date_change)

		# 日付表示用のTextコントロールを作成
		self.start_date_text = ft.Text(f"{self.start_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.end_date_text = ft.Text(f"{self.end_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.submit_date_text = ft.Text(f"{self.submit_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)

		# 検索条件
		self.item_plice = ft.Checkbox(label="貴重品のみ表示")
		self.item_finder = ft.Dropdown(
			label="拾得者",
			options=[ft.dropdown.Option(x[0]) for x in CHOICES_FINDER_POLICE],
			width=200
		)
		self.item_police = ft.Checkbox(label="届け出済みも表示")
		self.item_return = ft.Checkbox(label="返却済みも表示")

		# 書類選択
		self.document = ft.Dropdown(
			label="書類",
			options=[
				ft.dropdown.Option("占有者拾得物提出書", "占有者拾得物提出書"),
				ft.dropdown.Option("第三者拾得物提出書", "第三者拾得物提出書"),
			],
			width=300
		)

		# フレキシブルディスク提出票用
		self.info = ft.TextField(
			label="フレキシブルディスクに記載された事項",
			width=400,
			multiline=True,
			min_lines=3
		)
		self.documents = ft.TextField(
			label="フレキシブルディスクとあわせて提出される書類",
			width=400,
			multiline=True,
			min_lines=3
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
			self.item_finder,
			self.info,
			self.documents,
		])

		# レイアウト
		section_search_style = dict(padding=10, bgcolor=ft.colors.BLUE_50, border_radius=8, border=ft.border.all(1, ft.colors.BLUE_100))
		section_document_style = dict(padding=10, bgcolor=ft.colors.GREEN_50, border_radius=8, border=ft.border.all(1, ft.colors.GREEN_100))
		section_disk_style = dict(padding=10, bgcolor=ft.colors.ORANGE_50, border_radius=8, border=ft.border.all(1, ft.colors.ORANGE_100))

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
				ft.Row([ft.Text("貴重品のみ", width=120), self.item_plice], wrap=True),
				ft.Row([ft.Text("拾得者", width=120), self.item_finder], wrap=True),
				ft.Row([ft.Text("届け出済み", width=120), self.item_police], wrap=True),
				ft.Row([ft.Text("返却済み", width=120), self.item_return], wrap=True),
			]),
			**section_search_style
		)

		# 書類作成
		section_document = ft.Container(
			content=ft.Column([
				ft.Text("書類作成", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([
					ft.Text("警察届出日", width=120),
					ft.GestureDetector(
						content=ft.Container(
							content=self.submit_date_text,
							padding=5,
							border_radius=4,
							border=ft.border.all(1, ft.colors.BLACK),
							width=120,
							height=55
						),
						on_tap=lambda e: self.submit_date.pick_date()
					),
				], wrap=True),
				ft.Row([ft.Text("書類", width=120), self.document], wrap=True),
			]),
			**section_document_style
		)

		# フレキシブルディスク提出票
		section_disk = ft.Container(
			content=ft.Column([
				ft.Text("フレキシブルディスク提出票", size=18, weight=ft.FontWeight.BOLD),
				ft.Row([ft.Text("記載事項", width=120), self.info], wrap=True),
				ft.Row([ft.Text("提出書類", width=120), self.documents], wrap=True),
			]),
			**section_disk_style
		)

		layout = ft.Column([
			ft.Text("警察届け出処理", size=22, weight=ft.FontWeight.BOLD),
			section_search,
			section_document,
			section_disk,
			ft.Row([
				ft.ElevatedButton("絞り込み", on_click=lambda e: self.submit()),
				ft.OutlinedButton("警察届出所出力", on_click=lambda e: self.output_police_report()),
				ft.OutlinedButton("提出書類の作成", on_click=lambda e: self.create_document()),
				ft.OutlinedButton("印刷", on_click=lambda e: self.print_document()),
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
				self.page.overlay.append(self.submit_date)
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

	def _on_submit_date_change(self, e):
		if e.control.value:
			self.submit_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.submit_date_text.value = date_str
			# UIを更新
			self.update()

	def submit(self):
		if callable(self.on_submit):
			self.on_submit(self.collect())
	
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

	def output_police_report(self):
		# 警察届出所出力の処理
		data = self.collect()
		print("警察届出所出力:", data)
		if self.page:
			self.page.snack_bar.content = ft.Text("警察届出所出力を実行しました")
			self.page.snack_bar.open = True
			self.page.update()

	def create_document(self):
		# 提出書類の作成処理
		data = self.collect()
		print("提出書類作成:", data)
		if self.page:
			self.page.snack_bar.content = ft.Text("提出書類を作成しました")
			self.page.snack_bar.open = True
			self.page.update()

	def print_document(self):
		# 印刷処理
		data = self.collect()
		print("印刷実行:", data)
		if self.page:
			self.page.snack_bar.content = ft.Text("印刷を実行しました")
			self.page.snack_bar.open = True
			self.page.update()

	def collect(self):
		return {
			"start_date": self.start_date_value,
			"end_date": self.end_date_value,
			"submit_date": self.submit_date_value,
			"item_plice": self.item_plice.value,
			"item_finder": self.item_finder.value,
			"item_police": self.item_police.value,
			"item_return": self.item_return.value,
			"document": self.document.value,
			"info": self.info.value,
			"documents": self.documents.value,
		}
