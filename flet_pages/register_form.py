import flet as ft
from datetime import datetime, date
import requests
import cv2
import base64
import io
from PIL import Image
from apps.config import OWN_WAIVER, NOTE, COLOR, STORAGE_PLACE, ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S

MINUTES_15 = ["00", "15", "30", "45"]
HOURS = [f"{h:02d}" for h in range(0, 24)]




def nearest_15min(dt: datetime):
	m = dt.minute
	closest = min([0, 15, 30, 45], key=lambda x: abs(x - m))
	return f"{dt.hour:02d}", f"{closest:02d}"






class RegisterFormView(ft.UserControl):
	"""フォーム入力専用ビュー"""
	def __init__(self, on_submit=None, on_temp_save=None, on_back_to_camera=None, captured_photos_data=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_temp_save = on_temp_save
		self.on_back_to_camera = on_back_to_camera
		self.get_date_value = date.today().isoformat()
		self.recep_date_value = date.today().isoformat()
		self._date_pickers_added = False
		# 日付表示用のTextコントロール
		self.get_date_text = None
		self.recep_date_text = None
		# ダイアログ管理
		self.current_dialog = None
		
		# カメラ撮影データ
		self.captured_photos_data = captured_photos_data or {}
	
	def build(self):
		return self.create_form_view()
	
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
		self.get_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.get_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)
		self.recep_hour = ft.Dropdown(options=[ft.dropdown.Option(x) for x in HOURS], value=nh, width=90)
		self.recep_min = ft.Dropdown(options=[ft.dropdown.Option(x) for x in MINUTES_15], value=nm, width=90)

		# 日付表示用のTextコントロールを作成
		self.get_date_text = ft.Text(f"{self.get_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)
		self.recep_date_text = ft.Text(f"{self.recep_date_value}", color=ft.colors.BLACK, size=17, text_align=ft.TextAlign.CENTER)

		# 第三者関連
		self.finder_name = ft.TextField(
			hint_text="例: 田中太郎",
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.gender = ft.RadioGroup(value="男性", content=ft.Row([
			ft.Radio(value="男性", label="男性"),
			ft.Radio(value="女性", label="女性"),
			ft.Radio(value="その他", label="その他"),
		]))
		self.address_unknown = ft.Checkbox(label="住所 不明")
		self.address = ft.TextField(
			hint_text="例: 東京都渋谷区道玄坂1-2-3",
			multiline=True, 
			min_lines=1,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.postal_code = ft.TextField(
			hint_text="例: 150-0042",
			width=150,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.tel1 = ft.TextField(
			hint_text="例: 03-1234-5678",
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.tel2 = ft.TextField(
			hint_text="例: 090-1234-5678",
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		# 占有者の所属
		self.owner_affiliation = ft.TextField(
			hint_text="例: 株式会社サンプル",
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		
		# 占有者の氏名と性別
		self.owner_name = ft.TextField(
			hint_text="例: 山田花子",
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.owner_gender = ft.RadioGroup(value="男性", content=ft.Row([
			ft.Radio(value="男性", label="男性"),
			ft.Radio(value="女性", label="女性"),
			ft.Radio(value="その他", label="その他"),
		]))

		# 区分・届出等
		self.find_place = ft.TextField(
			hint_text="例: 渋谷駅前",
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.own_waiver = ft.Dropdown(
			hint_text="権利放棄を選択",
			options=[ft.dropdown.Option(x[0]) for x in OWN_WAIVER],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.note = ft.Dropdown(
			hint_text="氏名等告示を選択",
			options=[ft.dropdown.Option(x[0]) for x in NOTE],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.own_waiver_owner = ft.Dropdown(
			hint_text="占有者権利放棄を選択",
			options=[ft.dropdown.Option(x[0]) for x in OWN_WAIVER],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.note_owner = ft.Dropdown(
			hint_text="占有者氏名等告示を選択",
			options=[ft.dropdown.Option(x[0]) for x in NOTE],
			width=200,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)

		# 物件分類・色・保管
		self.item_class_L = ft.Dropdown(
			hint_text="分類（大）を選択",
			options=[ft.dropdown.Option(x) for x in ITEM_CLASS_L],
			width=150,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.item_class_M = ft.Dropdown(
			hint_text="分類（中）を選択",
			width=150,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.item_class_S = ft.Dropdown(
			hint_text="分類（小）を選択",
			width=150,
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
			hint_text="例: 黒い革製の財布、ブランドロゴ入り",
			multiline=True, 
			min_lines=2,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)
		self.storage_place = ft.Dropdown(
			hint_text="保管場所を選択",
			options=[ft.dropdown.Option(x[0]) for x in STORAGE_PLACE],
			width=300,
			focused_color=ft.colors.BLUE,
			bgcolor=ft.colors.WHITE
		)

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

		# レイアウト
		section_manage_style = dict(padding=10, bgcolor=ft.colors.WHITE, border_radius=8, border=ft.border.all(1, ft.colors.GREY_300))
		section_finder_style = dict(padding=10, bgcolor=ft.colors.WHITE, border_radius=8, border=ft.border.all(1, ft.colors.GREY_300))
		section_item_style = dict(padding=10, bgcolor=ft.colors.WHITE, border_radius=8, border=ft.border.all(1, ft.colors.GREY_300))

		# 管理情報（保管場所 上部）
		section_manage = ft.Container(
			content=ft.Column([
				ft.Text("管理情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Column([
					ft.Text("保管場所", size=14, weight=ft.FontWeight.BOLD),
					self.storage_place
				], spacing=5),
				ft.Row([
					ft.Column([
						ft.Text("拾得日", size=14, weight=ft.FontWeight.BOLD),
						ft.GestureDetector(
							content=ft.Container(
								content=self.get_date_text,
								padding=5,
								border_radius=4,
								border=ft.border.all(1, ft.colors.BLACK),
								width=120,
								height=55
							),
							on_tap=lambda e: self.get_date.pick_date()
						)
					], spacing=5),
					ft.Column([
						ft.Text("拾得時刻", size=14, weight=ft.FontWeight.BOLD),
						ft.Row([self.get_hour, ft.Text(":"), self.get_min], spacing=5)
					], spacing=5),
				], spacing=20),
				ft.Row([
					ft.Column([
						ft.Text("受付日", size=14, weight=ft.FontWeight.BOLD),
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
						)
					], spacing=5),
					ft.Column([
						ft.Text("受付時刻", size=14, weight=ft.FontWeight.BOLD),
						ft.Row([self.recep_hour, ft.Text(":"), self.recep_min], spacing=5)
					], spacing=5),
				], spacing=20),
				ft.Column([
					ft.Text("拾得場所", size=14, weight=ft.FontWeight.BOLD),
					self.find_place
				], spacing=5),
			], spacing=15),
			**section_manage_style
		)

		# 拾得者情報（姓・名 同一行 / 郵便番号→住所自動）
		def search_address(e):
			# 住所検索ボタンが押されたときの処理
			postal_val = self.postal_code.value or ""
			# ハイフンを除去して数字のみにする
			zip_raw = postal_val.replace("-", "").replace(" ", "")
			if len(zip_raw) == 7 and zip_raw.isdigit():
				try:
					r = requests.get("https://zipcloud.ibsnet.co.jp/api/search", params={"zipcode": zip_raw}, timeout=5)
					js = r.json()
					if js.get("status") == 200 and js.get("results"):
						res = js["results"][0]
						pref = res.get("address1") or ""
						city = res.get("address2") or ""
						town = res.get("address3") or ""
						base = f"{pref}{city}{town}"
						self.address.value = base
						self.address.update()
					else:
						# エラーメッセージを表示
						if self.page:
							self.page.snack_bar.content = ft.Text("郵便番号が見つかりませんでした。")
							self.page.snack_bar.open = True
							self.page.update()
				except Exception as ex:
					if self.page:
						self.page.snack_bar.content = ft.Text(f"住所検索エラー: {ex}")
						self.page.snack_bar.open = True
						self.page.update()
			else:
				# エラーメッセージを表示
				if self.page:
					self.page.snack_bar.content = ft.Text("郵便番号は7桁の数字で入力してください。")
					self.page.snack_bar.open = True
					self.page.update()

		# 第三者拾得用のコンテナ
		third_party_container = ft.Container(
			content=ft.Column([
				ft.Column([
					ft.Text("拾得者氏名", size=14, weight=ft.FontWeight.BOLD),
					self.finder_name
				], spacing=5),
				ft.Column([
					ft.Text("性別", size=14, weight=ft.FontWeight.BOLD),
					self.gender
				], spacing=5),
				ft.Row([
					ft.Column([
						ft.Text("郵便番号", size=14, weight=ft.FontWeight.BOLD),
						self.postal_code
					], spacing=5),
					ft.Column([
						ft.Text("", size=14),  # 空のラベルで位置合わせ
						ft.ElevatedButton("住所検索", on_click=search_address, width=80)
					], spacing=5),
				], spacing=10),
				ft.Column([
					ft.Text("住所", size=14, weight=ft.FontWeight.BOLD),
					ft.Row([self.address, self.address_unknown], spacing=10)
				], spacing=5),
				ft.Row([
					ft.Column([
						ft.Text("連絡先1", size=14, weight=ft.FontWeight.BOLD),
						self.tel1
					], spacing=5),
					ft.Column([
						ft.Text("連絡先2", size=14, weight=ft.FontWeight.BOLD),
						self.tel2
					], spacing=5),
				], spacing=10),
				ft.Row([
					ft.Column([
						ft.Text("権利放棄", size=14, weight=ft.FontWeight.BOLD),
						self.own_waiver
					], spacing=5),
					ft.Column([
						ft.Text("氏名等告示", size=14, weight=ft.FontWeight.BOLD),
						self.note
					], spacing=5),
				], spacing=10),
			], spacing=15),
			visible=False
		)

		# 占有者拾得用のコンテナ
		owner_container = ft.Container(
			content=ft.Column([
				ft.Column([
					ft.Text("占有者の氏名", size=14, weight=ft.FontWeight.BOLD),
					self.owner_name
				], spacing=5),
				ft.Column([
					ft.Text("占有者の性別", size=14, weight=ft.FontWeight.BOLD),
					self.owner_gender
				], spacing=5),
				ft.Column([
					ft.Text("占有者の所属", size=14, weight=ft.FontWeight.BOLD),
					self.owner_affiliation
				], spacing=5),	
				ft.Row([
					ft.Column([
						ft.Text("占有者権利放棄", size=14, weight=ft.FontWeight.BOLD),
						self.own_waiver_owner
					], spacing=5),
					ft.Column([
						ft.Text("占有者氏名等告示", size=14, weight=ft.FontWeight.BOLD),
						self.note_owner
					], spacing=5),
				], spacing=10),
			], spacing=15),
			visible=True
		)

		section_finder = ft.Container(
			content=ft.Column([
				ft.Text("拾得者情報", size=18, weight=ft.FontWeight.BOLD),
				ft.Column([
					ft.Text("拾得者区分", size=14, weight=ft.FontWeight.BOLD),
					self.finder_type
				], spacing=5),
				third_party_container,
				owner_container,
			], spacing=15),
			**section_finder_style
		)

		# 拾得物詳細
		section_item = ft.Container(
			content=ft.Column([
				ft.Text("拾得物詳細", size=18, weight=ft.FontWeight.BOLD),
				ft.Column([
					ft.Text("分類", size=14, weight=ft.FontWeight.BOLD),
					ft.Row([
						ft.Column([
							ft.Text("大", size=12, weight=ft.FontWeight.BOLD),
							self.item_class_L
						], spacing=5),
						ft.Column([
							ft.Text("中", size=12, weight=ft.FontWeight.BOLD),
							self.item_class_M
						], spacing=5),
						ft.Column([
							ft.Text("小", size=12, weight=ft.FontWeight.BOLD),
							self.item_class_S
						], spacing=5),
					], spacing=10)
				], spacing=5),
				ft.Column([
					ft.Text("色", size=14, weight=ft.FontWeight.BOLD),
					self.color
				], spacing=5),
				ft.Column([
					ft.Text("特徴", size=14, weight=ft.FontWeight.BOLD),
					self.feature
				], spacing=5),
			], spacing=15),
			**section_item_style
		)

		# 撮影済み写真の表示（右側固定）
		photo_section = self.create_photo_section()
		
		# フォーム部分（左側、スクロール可能）
		form_content = ft.Column([
			ft.Text("ステップ2: 詳細を入力", size=22, weight=ft.FontWeight.BOLD),
			section_manage,
			section_finder,
			section_item,
			ft.Row([
				ft.ElevatedButton("登録", on_click=lambda e: self.submit()),
				ft.OutlinedButton("一時保存", on_click=lambda e: self.temp_save()),
				ft.TextButton("撮影画面に戻る", on_click=lambda e: self.go_back_to_camera()),
				ft.TextButton("ホームに戻る", on_click=lambda e: self.page.go("/")),
			])
		], expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)

		# 左右分割レイアウト
		layout = ft.Row([
			# 左側：フォーム入力（スクロール可能）
			ft.Container(
				content=form_content,
				expand=3,
				padding=10
			),
			# 右側：写真表示（固定）
			ft.Container(
				content=photo_section,
				width=400,
				padding=10,
				bgcolor=ft.colors.GREY_100,
				border_radius=8
			)
		], expand=True)

		return layout
	
	def create_photo_section(self):
		"""撮影済み写真を表示するセクションを作成"""
		# メイン写真（最初の写真）を大きく表示
		main_photo_display = self.create_main_photo_display()
		
		# 写真一覧のグリッド
		photo_grid = ft.GridView(
			runs_count=2,  # 2列表示
			max_extent=150,  # サムネイルサイズ
			child_aspect_ratio=1.0,  # 正方形の比率（1:1）
			spacing=10,
			run_spacing=10,
		)
		
		# 撮影済み写真がある場合、表示
		if self.captured_photos_data:
			# メイン写真を表示
			for i, photo in enumerate(self.captured_photos_data.get('main_photos', [])):
				if photo and 'frame' in photo:
					thumbnail = self.create_photo_thumbnail(photo['frame'], size=120)
					photo_container = ft.Container(
						content=ft.Column([
							thumbnail,
							ft.Text(f"メイン{i+1}", size=10, text_align=ft.TextAlign.CENTER)
						]),
						border=ft.border.all(2, ft.colors.BLUE),
						border_radius=8,
						padding=5,
						on_click=lambda e, photo_data=photo: self.show_photo_dialog(photo_data, f"メイン写真 {i+1}")
					)
					photo_grid.controls.append(photo_container)
			
			# 同梱物写真を表示
			for i, photo in enumerate(self.captured_photos_data.get('bundle_photos', [])):
				if photo and 'frame' in photo:
					thumbnail = self.create_photo_thumbnail(photo['frame'], size=120)
					photo_container = ft.Container(
						content=ft.Column([
							thumbnail,
							ft.Text(f"同梱{i+1}", size=10, text_align=ft.TextAlign.CENTER)
						]),
						border=ft.border.all(2, ft.colors.ORANGE),
						border_radius=8,
						padding=5,
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
					height=400,  # 写真一覧の高さを増加
					border=ft.border.all(1, ft.colors.GREY_300),
					border_radius=8,
					padding=10
				),
			], spacing=10),  # scroll=ft.ScrollMode.AUTO を削除
			width=350,  # 右側の幅を固定
			height=700,  # 右側の高さを増加
			padding=10,
			bgcolor=ft.colors.GREY_100,
			border_radius=8
		)
	
	def create_main_photo_display(self):
		"""メイン写真（最初の写真）を大きく表示"""
		if self.captured_photos_data and self.captured_photos_data.get('main_photos'):
			first_photo = self.captured_photos_data['main_photos'][0]
			if first_photo and 'frame' in first_photo:
				# 大きなサイズで表示（右側幅に合わせる）
				large_thumbnail = self.create_photo_thumbnail(first_photo['frame'], size=290)
				return ft.Container(
					content=ft.Column([
						ft.Text("メイン写真", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
						ft.Container(
							content=large_thumbnail,
							width=290,   # コンテナの幅を画像サイズに合わせる
							height=290,  # コンテナの高さを画像サイズに合わせる
							border=ft.border.all(3, ft.colors.BLUE),
							border_radius=8,
							padding=0,  # パディングを0にして余白をなくす
							alignment=ft.alignment.center,
							on_click=lambda e: self.show_photo_dialog(first_photo, "メイン写真")
						)
					], spacing=5),
					width=300,  # 右側幅に合わせる
					height=320, # 高さを調整（テキスト分も含む）
					bgcolor=ft.colors.WHITE,
					border_radius=8,
					padding=5
				)
		
		# 写真がない場合
		return ft.Container(
			content=ft.Text("撮影された写真はありません", 
			              color=ft.colors.GREY_600, 
			              size=14,
			              text_align=ft.TextAlign.CENTER),
			width=300,
			height=300,
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
					height=600,
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
		"""フレームからサムネイルを作成（正方形1:1）"""
		# フレームを正方形にリサイズ
		small_frame = cv2.resize(frame, (size, size), interpolation=cv2.INTER_AREA)
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
			width=size,
			height=size,
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

	def did_mount(self):
		# DatePicker をページオーバーレイに追加
		try:
			if not self._date_pickers_added and self.page is not None:
				self.page.overlay.append(self.get_date)
				self.page.overlay.append(self.recep_date)
				self.page.update()
				self._date_pickers_added = True
		except Exception:
			pass

	def _on_get_date_change(self, e):
		if e.control.value:
			self.get_date_value = e.control.value
			# 日付のみを表示（時刻部分を除去）
			date_str = str(e.control.value).split()[0]
			self.get_date_text.value = date_str
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

	def submit(self):
		# バリデーションチェック
		errors = []
		
		# 拾得者区分が選択されているかチェック
		if not self.finder_type.value:
			errors.append("拾得者区分を選択してください")
		elif self.finder_type.value == "第三者拾得":
			if not self.finder_name.value:
				errors.append("拾得者氏名は必須です")
			if not self.own_waiver.value:
				errors.append("権利放棄は必須です")
			if not self.note.value:
				errors.append("氏名等告示は必須です")
		elif self.finder_type.value == "占有者拾得":
			if not self.owner_name.value:
				errors.append("占有者の氏名は必須です")
			if not self.own_waiver_owner.value:
				errors.append("占有者権利放棄は必須です")
			if not self.note_owner.value:
				errors.append("占有者氏名等告示は必須です")
		
		if not self.find_place.value:
			errors.append("拾得場所は必須です")
		if not self.storage_place.value:
			errors.append("保管場所は必須です")
		if not self.item_class_L.value:
			errors.append("物品分類（大）は必須です")
		if not self.color.value:
			errors.append("色は必須です")
		if not self.feature.value:
			errors.append("特徴は必須です")
		
		if errors:
			# エラーメッセージを赤文字で表示
			if self.page:
				self.page.snack_bar.content = ft.Text("必須項目が未入力です:\n" + "\n".join(errors), color=ft.colors.RED)
				self.page.snack_bar.open = True
				self.page.update()
			return
		
		# バリデーション成功時は通常の処理
		if callable(self.on_submit):
			self.on_submit(self.collect())
			# 登録成功後、ホームに戻る
			if self.page:
				self.show_success("拾得物の登録が完了しました")
				# 少し遅延してからホームに戻る
				import threading
				def go_home():
					import time
					time.sleep(1.5)  # 1.5秒待機
					if self.page:
						self.page.go("/")
				threading.Thread(target=go_home, daemon=True).start()

	def temp_save(self):
		if callable(self.on_temp_save):
			self.on_temp_save(self.collect())

	def collect(self):
		return {
			"finder_type": self.finder_type.value,
			"get_date": self.get_date_value,
			"get_hour": self.get_hour.value,
			"get_min": self.get_min.value,
			"recep_date": self.recep_date_value,
			"recep_hour": self.recep_hour.value,
			"recep_min": self.recep_min.value,
			"find_place": self.find_place.value,
			"finder_name": self.finder_name.value,
			"gender": self.gender.value,
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
