import flet as ft
from apps.config import MONEY_TYPES


class MoneyRegistrationView(ft.UserControl):
	"""金種登録専用ビュー"""
	def __init__(self, on_complete=None, on_cancel=None, initial_data=None):
		super().__init__()
		self.on_complete = on_complete  # 金種登録完了時のコールバック
		self.on_cancel = on_cancel  # キャンセル時のコールバック
		self.money_data = initial_data.copy() if initial_data else {}
		self.money_fields = {}
		self.memorial_fields = []
		self.money_amount_texts = {}
		self.total_amount_text = None
	
	def build(self):
		return self.create_money_registration_view()
	
	def create_money_registration_view(self):
		"""金種登録画面を作成"""
		money_inputs = []
		total_amount = 0
		
		# 現在の金種データを保持
		current_money_data = self.money_data.copy() if self.money_data else {}
		
		# 通常の金種入力欄（紙幣と硬貨を分ける）
		bills = []  # 紙幣
		coins = []  # 硬貨
		
		for name, value in MONEY_TYPES:
			# 現在の枚数を取得
			current_count = int(current_money_data.get(name, 0))
			
			# 金額表示用テキスト
			amount_text = ft.Text(f"¥{current_count * value:,}", size=12, color=ft.colors.BLUE_700, weight=ft.FontWeight.BOLD)
			self.money_amount_texts[name] = (amount_text, value)
			
			# 枚数入力フィールド（コンパクト）
			field = ft.TextField(
				value=str(current_count),
				width=60,
				height=40,
				text_size=14,
				keyboard_type=ft.KeyboardType.NUMBER,
				on_change=lambda e, n=name: self._update_money_amount(n, e.control.value),
				border_color=ft.colors.GREY_400,
				focused_border_color=ft.colors.BLUE_400,
			)
			self.money_fields[name] = field
			
			# 現在の金額を計算
			total_amount += current_count * value
			
			row = ft.Container(
				content=ft.Row([
					ft.Text(name, size=13, width=90, weight=ft.FontWeight.W_500),
					field,
					ft.Text("枚", size=12, width=25, color=ft.colors.GREY_600),
					amount_text
				], spacing=8, alignment=ft.MainAxisAlignment.START),
				padding=ft.padding.symmetric(vertical=4, horizontal=8),
				bgcolor=ft.colors.WHITE,
				border_radius=6,
			)
			
			# 紙幣と硬貨を分類
			if "円札" in name:
				bills.append(row)
			else:
				coins.append(row)
		
		# 合計金額表示
		self.total_amount_text = ft.Text(
			f"¥{total_amount:,}",
			size=32,
			weight=ft.FontWeight.BOLD,
			color=ft.colors.GREEN_700
		)
		
		return ft.Container(
			content=ft.Column([
				# ヘッダー
				ft.Container(
					content=ft.Row([
						ft.Icon(ft.icons.ATTACH_MONEY, size=28, color=ft.colors.GREEN_700),
						ft.Text("金種登録", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800),
					], spacing=12),
					margin=ft.margin.only(bottom=16)
				),
				
				# メインコンテンツ（2カラム）
				ft.Row([
					# 左カラム：紙幣
					ft.Container(
						content=ft.Column([
							ft.Container(
								content=ft.Text("紙幣", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
								margin=ft.margin.only(bottom=8)
							),
							ft.Column(bills, spacing=4)
						]),
						expand=1,
						padding=12,
						bgcolor=ft.colors.GREY_50,
						border_radius=8,
					),
					
					# 右カラム：硬貨
					ft.Container(
						content=ft.Column([
							ft.Container(
								content=ft.Text("硬貨", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
								margin=ft.margin.only(bottom=8)
							),
							ft.Column(coins, spacing=4)
						]),
						expand=1,
						padding=12,
						bgcolor=ft.colors.GREY_50,
						border_radius=8,
					),
				], spacing=16, expand=True),
				
				# 合計金額表示
				ft.Container(
					content=ft.Row([
						ft.Text("合計金額", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
						ft.Container(expand=True),
						self.total_amount_text
					], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
					padding=16,
					bgcolor=ft.colors.GREEN_50,
					border_radius=8,
					border=ft.border.all(2, ft.colors.GREEN_200),
					margin=ft.margin.symmetric(vertical=16)
				),
				
				# ボタン
				ft.Row([
					ft.OutlinedButton(
						"キャンセル",
						on_click=lambda e: self._on_cancel_click(),
						icon=ft.icons.CLOSE,
						height=45,
						style=ft.ButtonStyle(
							color=ft.colors.GREY_700,
						)
					),
					ft.Container(expand=True),
					ft.ElevatedButton(
						"登録完了",
						on_click=lambda e: self._on_complete_click(),
						bgcolor=ft.colors.GREEN_600,
						color=ft.colors.WHITE,
						height=45,
						width=180,
						icon=ft.icons.CHECK_CIRCLE,
						style=ft.ButtonStyle(
							shape=ft.RoundedRectangleBorder(radius=8),
						)
					),
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
			], spacing=0),
			padding=24,
			expand=True
		)
	
	def _update_money_amount(self, money_name, value_str):
		"""個別の金種の金額を更新"""
		try:
			count = int(value_str) if value_str else 0
			if money_name in self.money_amount_texts:
				amount_text, unit_value = self.money_amount_texts[money_name]
				amount_text.value = f"= ¥{count * unit_value:,}"
		except:
			pass
		
		# 合計金額も更新
		self._update_money_total()
	
	def _update_money_total(self):
		"""合計金額を更新"""
		total = 0
		
		# 通常の金種
		for name, value in MONEY_TYPES:
			if name in self.money_fields:
				try:
					count = int(self.money_fields[name].value or 0)
					total += count * value
				except:
					pass
		
		# 記念硬貨
		if hasattr(self, 'memorial_fields'):
			for item in self.memorial_fields:
				total += item.get("amount", 0)
		
		if hasattr(self, 'total_amount_text') and self.total_amount_text:
			self.total_amount_text.value = f"合計金額: ¥{total:,}"
			if hasattr(self, 'update'):
				self.update()
	
	def _add_memorial_coin(self):
		"""記念硬貨追加ダイアログを表示"""
		name_field = ft.TextField(label="種類（例: 東京オリンピック記念硬貨）", width=300)
		amount_field = ft.TextField(label="金額（円）", width=150, keyboard_type=ft.KeyboardType.NUMBER)
		
		def save_memorial(e):
			if name_field.value and amount_field.value:
				self._add_memorial_coin_field(name_field.value, int(amount_field.value))
				dialog.open = False
				self.page.update()
		
		dialog = ft.AlertDialog(
			title=ft.Text("記念硬貨を追加"),
			content=ft.Column([name_field, amount_field], tight=True),
			actions=[
				ft.TextButton("キャンセル", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
				ft.ElevatedButton("追加", on_click=save_memorial)
			]
		)
		
		self.page.dialog = dialog
		dialog.open = True
		self.page.update()
	
	def _add_memorial_coin_field(self, name, amount):
		"""記念硬貨フィールドを追加"""
		field = {
			"name": name,
			"amount": amount
		}
		self.memorial_fields.append(field)
		self._update_money_total()
	
	def _on_complete_click(self):
		"""金種登録完了ボタンがクリックされた"""
		# 金種データを収集
		result_data = {}
		for name, value in MONEY_TYPES:
			if name in self.money_fields:
				try:
					count = int(self.money_fields[name].value or 0)
					if count > 0:
						result_data[name] = count
				except:
					pass
		
		# 記念硬貨データを保存
		if self.memorial_fields:
			result_data["memorial_coins"] = self.memorial_fields
		
		# コールバック呼び出し
		if callable(self.on_complete):
			self.on_complete(result_data)
	
	def _on_cancel_click(self):
		"""キャンセルボタンがクリックされた"""
		if callable(self.on_cancel):
			self.on_cancel()

