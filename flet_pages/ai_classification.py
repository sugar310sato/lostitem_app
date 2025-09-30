import flet as ft
import cv2
import numpy as np
from PIL import Image
import io
import base64
from datetime import datetime
import os

class AIClassificationView(ft.UserControl):
	def __init__(self, on_submit=None, on_temp_save=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_temp_save = on_temp_save
		self.camera = None
		self.is_camera_active = False
		self.captured_image = None
		self.detection_results = None
		self.classification_results = None
		self._camera_initialized = False

	def build(self):
		# カメラ制御
		self.camera_button = ft.ElevatedButton(
			"カメラ開始",
			on_click=self.toggle_camera,
			icon=ft.icons.CAMERA_ALT
		)
		
		self.capture_button = ft.ElevatedButton(
			"画像キャプチャ",
			on_click=self.capture_image,
			icon=ft.icons.CAMERA,
			disabled=True
		)

		# 画像表示エリア
		self.image_display = ft.Image(
			src=None,
			width=400,
			height=300,
			fit=ft.ImageFit.CONTAIN,
			border_radius=8
		)
		
		# 画像表示用のコンテナ（ボーダー付き）
		self.image_container = ft.Container(
			content=self.image_display,
			border=ft.border.all(1, ft.colors.GREY_400),
			border_radius=8,
			padding=5
		)

		# 処理ステップ表示
		self.step_display = ft.Text(
			"ステップ1: カメラから画像を取得してください",
			size=16,
			color=ft.colors.BLUE_700,
			weight=ft.FontWeight.BOLD
		)

		# 処理ボタン
		self.yolo_button = ft.ElevatedButton(
			"YOLOv11 物体検出",
			on_click=self.run_yolo_detection,
			icon=ft.icons.SEARCH,
			disabled=True
		)

		self.sam_button = ft.ElevatedButton(
			"SAM2 領域抽出",
			on_click=self.run_sam_segmentation,
			icon=ft.icons.CROP,
			disabled=True
		)

		self.classifier_button = ft.ElevatedButton(
			"専用分類器実行",
			on_click=self.run_classifier,
			icon=ft.icons.CLASS,
			disabled=True
		)

		# 結果表示エリア
		self.results_area = ft.Container(
			content=ft.Column([
				ft.Text("検出・分類結果", size=18, weight=ft.FontWeight.BOLD),
				ft.Divider(),
				ft.Text("結果がここに表示されます", color=ft.colors.GREY_600)
			]),
			padding=15,
			bgcolor=ft.colors.GREY_50,
			border_radius=8,
			border=ft.border.all(1, ft.colors.GREY_300)
		)

		# 設定エリア
		self.settings_area = ft.Container(
			content=ft.Column([
				ft.Text("AI設定", size=18, weight=ft.FontWeight.BOLD),
				ft.Divider(),
				ft.Row([
					ft.Text("YOLO信頼度閾値:", width=150),
					ft.Slider(
						min=0.1,
						max=0.9,
						divisions=8,
						value=0.5,
						label="{value}",
						width=200
					)
				]),
				ft.Row([
					ft.Text("SAM2精度:", width=150),
					ft.Dropdown(
						options=[
							ft.dropdown.Option("高速", "fast"),
							ft.dropdown.Option("標準", "standard"),
							ft.dropdown.Option("高精度", "high")
						],
						value="standard",
						width=200
					)
				]),
				ft.Row([
					ft.Text("分類器モデル:", width=150),
					ft.Dropdown(
						options=[
							ft.dropdown.Option("ResNet50", "resnet50"),
							ft.dropdown.Option("EfficientNet-B0", "efficientnet_b0"),
							ft.dropdown.Option("ViT-Base", "vit_base")
						],
						value="resnet50",
						width=200
					)
				])
			]),
			padding=15,
			bgcolor=ft.colors.BLUE_50,
			border_radius=8,
			border=ft.border.all(1, ft.colors.BLUE_300)
		)

		# レイアウト
		layout = ft.Column([
			ft.Text("AI画像分類テスト", size=22, weight=ft.FontWeight.BOLD),
			
			# カメラ制御エリア
			ft.Container(
				content=ft.Column([
					ft.Text("画像取得", size=18, weight=ft.FontWeight.BOLD),
					ft.Row([
						self.camera_button,
						self.capture_button
					]),
					self.image_container,
					self.step_display
				]),
				padding=15,
				bgcolor=ft.colors.GREEN_50,
				border_radius=8,
				border=ft.border.all(1, ft.colors.GREEN_300)
			),

			# 処理ステップエリア
			ft.Container(
				content=ft.Column([
					ft.Text("AI処理ステップ", size=18, weight=ft.FontWeight.BOLD),
					ft.Row([
						self.yolo_button,
						self.sam_button,
						self.classifier_button
					])
				]),
				padding=15,
				bgcolor=ft.colors.ORANGE_50,
				border_radius=8,
				border=ft.border.all(1, ft.colors.ORANGE_300)
			),

			# 設定エリア
			self.settings_area,

			# 結果表示エリア
			self.results_area,

			# 操作ボタン
			ft.Row([
				ft.ElevatedButton("学習データ追加", on_click=self.add_training_data, icon=ft.icons.ADD),
				ft.OutlinedButton("精度改善ループ", on_click=self.improve_accuracy, icon=ft.icons.LOOP),
				ft.TextButton("ホームに戻る", on_click=lambda e: self.page.go("/")),
			])
		], expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)

		return layout

	def toggle_camera(self, e):
		if not self.is_camera_active:
			self.start_camera()
		else:
			self.stop_camera()

	def start_camera(self):
		try:
			# カメラ初期化
			self.camera = cv2.VideoCapture(0)
			if self.camera.isOpened():
				self.is_camera_active = True
				self.camera_button.text = "カメラ停止"
				self.capture_button.disabled = False
				self.step_display.value = "ステップ2: 画像をキャプチャしてください"
				self.step_display.color = ft.colors.GREEN_700
				self._camera_initialized = True
				self.update()
				
				# カメラプレビュー開始
				self.start_camera_preview()
			else:
				self.show_error("カメラを開けませんでした")
		except Exception as e:
			self.show_error(f"カメラ初期化エラー: {str(e)}")

	def stop_camera(self):
		if self.camera:
			self.camera.release()
		self.is_camera_active = False
		self.camera_button.text = "カメラ開始"
		self.capture_button.disabled = True
		self.step_display.value = "ステップ1: カメラから画像を取得してください"
		self.step_display.color = ft.colors.BLUE_700
		self.update()

	def start_camera_preview(self):
		# カメラプレビューを開始（実際の実装では別スレッドで実行）
		pass

	def capture_image(self, e):
		if self.camera and self.is_camera_active:
			try:
				ret, frame = self.camera.read()
				if ret:
					# OpenCV画像をPIL画像に変換
					frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
					pil_image = Image.fromarray(frame_rgb)
					
					# 画像を保存
					self.captured_image = pil_image
					
					# 画像をbase64エンコードして表示
					buffer = io.BytesIO()
					pil_image.save(buffer, format='PNG')
					img_str = base64.b64encode(buffer.getvalue()).decode()
					self.image_display.src = f"data:image/png;base64,{img_str}"
					
					# ステップ更新
					self.step_display.value = "ステップ3: YOLOv11で物体検出を実行してください"
					self.step_display.color = ft.colors.ORANGE_700
					self.yolo_button.disabled = False
					
					self.update()
					self.show_success("画像をキャプチャしました")
				else:
					self.show_error("画像の取得に失敗しました")
			except Exception as e:
				self.show_error(f"画像キャプチャエラー: {str(e)}")

	def run_yolo_detection(self, e):
		if self.captured_image:
			try:
				# YOLOv11物体検出のシミュレーション
				self.step_display.value = "YOLOv11実行中..."
				self.step_display.color = ft.colors.YELLOW_700
				self.update()
				
				# 実際の実装ではYOLOv11モデルを実行
				# ここではシミュレーション結果
				self.detection_results = {
					"objects": [
						{"class": "bag", "confidence": 0.85, "bbox": [100, 100, 200, 300]},
						{"class": "phone", "confidence": 0.92, "bbox": [300, 150, 400, 250]}
					]
				}
				
				# 結果表示
				self.update_detection_results()
				
				# ステップ更新
				self.step_display.value = "ステップ4: SAM2で領域抽出を実行してください"
				self.step_display.color = ft.colors.PURPLE_700
				self.sam_button.disabled = False
				
				self.update()
				self.show_success("YOLOv11物体検出完了")
			except Exception as e:
				self.show_error(f"YOLO検出エラー: {str(e)}")

	def run_sam_segmentation(self, e):
		if self.detection_results:
			try:
				# SAM2領域抽出のシミュレーション
				self.step_display.value = "SAM2実行中..."
				self.step_display.color = ft.colors.YELLOW_700
				self.update()
				
				# 実際の実装ではSAM2モデルを実行
				# ここではシミュレーション結果
				self.segmentation_results = {
					"masks": [
						{"object_id": 0, "mask": "mask_data_1", "area": 15000},
						{"object_id": 1, "mask": "mask_data_2", "area": 8000}
					]
				}
				
				# 結果表示
				self.update_segmentation_results()
				
				# ステップ更新
				self.step_display.value = "ステップ5: 専用分類器を実行してください"
				self.step_display.color = ft.colors.RED_700
				self.classifier_button.disabled = False
				
				self.update()
				self.show_success("SAM2領域抽出完了")
			except Exception as e:
				self.show_error(f"SAM2抽出エラー: {str(e)}")

	def run_classifier(self, e):
		if self.segmentation_results:
			try:
				# 専用分類器のシミュレーション
				self.step_display.value = "分類器実行中..."
				self.step_display.color = ft.colors.YELLOW_700
				self.update()
				
				# 実際の実装では専用分類器モデルを実行
				# ここではシミュレーション結果
				self.classification_results = {
					"classifications": [
						{
							"object_id": 0,
							"main_class": "bag",
							"confidence": 0.95,
							"attributes": {
								"color": "black",
								"material": "leather",
								"size": "medium"
							}
						},
						{
							"object_id": 1,
							"main_class": "phone",
							"confidence": 0.98,
							"attributes": {
								"brand": "iPhone",
								"color": "white",
								"condition": "good"
							}
						}
					]
				}
				
				# 結果表示
				self.update_classification_results()
				
				# ステップ完了
				self.step_display.value = "完了: 画像分類・特徴抽出が完了しました"
				self.step_display.color = ft.colors.GREEN_700
				
				self.update()
				self.show_success("専用分類器実行完了")
			except Exception as e:
				self.show_error(f"分類器エラー: {str(e)}")

	def update_detection_results(self):
		if self.detection_results:
			content = ft.Column([
				ft.Text("YOLOv11 検出結果", size=16, weight=ft.FontWeight.BOLD),
				ft.Divider()
			])
			
			for obj in self.detection_results["objects"]:
				content.controls.append(
					ft.Text(f"クラス: {obj['class']}, 信頼度: {obj['confidence']:.2f}")
				)
			
			self.results_area.content = content
			self.update()

	def update_segmentation_results(self):
		if self.segmentation_results:
			content = ft.Column([
				ft.Text("SAM2 領域抽出結果", size=16, weight=ft.FontWeight.BOLD),
				ft.Divider()
			])
			
			for mask in self.segmentation_results["masks"]:
				content.controls.append(
					ft.Text(f"オブジェクトID: {mask['object_id']}, 面積: {mask['area']}")
				)
			
			self.results_area.content = content
			self.update()

	def update_classification_results(self):
		if self.classification_results:
			content = ft.Column([
				ft.Text("専用分類器 結果", size=16, weight=ft.FontWeight.BOLD),
				ft.Divider()
			])
			
			for cls in self.classification_results["classifications"]:
				content.controls.append(
					ft.Text(f"オブジェクトID: {cls['object_id']}")
				)
				content.controls.append(
					ft.Text(f"  メインクラス: {cls['main_class']} (信頼度: {cls['confidence']:.2f})")
				)
				for attr_name, attr_value in cls['attributes'].items():
					content.controls.append(
						ft.Text(f"  {attr_name}: {attr_value}")
					)
				content.controls.append(ft.Divider())
			
			self.results_area.content = content
			self.update()

	def add_training_data(self, e):
		# 学習データ追加の処理
		self.show_info("学習データ追加機能は開発中です")

	def improve_accuracy(self, e):
		# 精度改善ループの処理
		self.show_info("精度改善ループ機能は開発中です")

	def show_success(self, message):
		if self.page:
			self.page.snack_bar.content = ft.Text(message, color=ft.colors.GREEN)
			self.page.snack_bar.open = True
			self.page.update()

	def show_error(self, message):
		if self.page:
			self.page.snack_bar.content = ft.Text(message, color=ft.colors.RED)
			self.page.snack_bar.open = True
			self.page.update()

	def show_info(self, message):
		if self.page:
			self.page.snack_bar.content = ft.Text(message, color=ft.colors.BLUE)
			self.page.snack_bar.open = True
			self.page.update()

	def did_mount(self):
		# 初期化処理
		pass

	def will_unmount(self):
		# カメラリソースの解放
		if self.camera:
			self.camera.release()
