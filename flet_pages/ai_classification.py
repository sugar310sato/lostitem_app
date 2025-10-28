import flet as ft
import cv2
import numpy as np
from PIL import Image
import io
import base64
from datetime import datetime
import os
import json
from pathlib import Path
import torch
from ultralytics import YOLO
import threading
import time
from .camera_form import CameraFormView

class AIClassificationView(ft.UserControl):
	def __init__(self, on_submit=None, on_temp_save=None):
		super().__init__()
		self.on_submit = on_submit
		self.on_temp_save = on_temp_save
		self.captured_image = None
		self.classification_results = None
		self.yolo_model = None
		self.classification_data = None
		
		# camera_form.pyのカメラ機能を統合（正式採用）
		self.camera_form = None
		
		# 分類データの読み込み
		self._load_classification_data()

	def _create_ai_camera_form(self):
		"""AIテスト用のカスタムカメラフォームを作成（カメラ画面のみ）"""
		# camera_form.pyからカメラ機能のみを抽出
		ai_camera_form = ft.UserControl()
		
		# カメラ映像表示用のImageコントロール
		ai_camera_form.camera_image = ft.Image(
			width=480,
			height=360,
			fit=ft.ImageFit.COVER,
			border_radius=8,
			src="",  # 初期は空
		)
		
		# カメラ映像表示用のコンテナ
		ai_camera_form.camera_container = ft.Container(
			content=ai_camera_form.camera_image,
			width=480,
			height=360,
			bgcolor=ft.colors.BLACK,
			alignment=ft.alignment.center,
			border_radius=8,
			border=ft.border.all(2, ft.colors.GREY_400)
		)
		
		# 撮影ガイドフレーム（70%サイズ、中央配置）
		guide_frame_size = int(min(480, 360) * 0.7)
		ai_camera_form.guide_frame = ft.Container(
			width=guide_frame_size,
			height=guide_frame_size,
			border=ft.border.all(3, ft.colors.RED),
			border_radius=8,
			bgcolor=ft.colors.TRANSPARENT,
		)
		
		# カメラ関連の変数
		ai_camera_form.cap = None
		ai_camera_form.camera_running = False
		ai_camera_form.camera_index = 0
		ai_camera_form.frame_width = 480
		ai_camera_form.frame_height = 360
		
		# カメラ機能のメソッドを追加
		ai_camera_form.start_camera = self._start_camera
		ai_camera_form.stop_camera = self._stop_camera
		ai_camera_form.update_camera_feed = self._update_camera_feed
		ai_camera_form.capture_photo = self._capture_photo
		
		# カメラ画面のUI
		ai_camera_form.build = lambda: ft.Container(
			content=ft.Stack([
				ai_camera_form.camera_container,
				ft.Container(
					content=ai_camera_form.guide_frame,
					alignment=ft.alignment.center,
					width=480,
					height=360
				)
			], alignment=ft.alignment.center),
			alignment=ft.alignment.center,
			padding=10
		)
		
		return ai_camera_form

	def _load_classification_data(self):
		"""item_classification.jsonとconfig.pyの分類データを統合して読み込み"""
		try:
			# item_classification.jsonを読み込み
			json_path = Path(__file__).parent.parent / "item_classification.json"
			with open(json_path, 'r', encoding='utf-8') as f:
				json_data = json.load(f)
			
			# config.pyの分類データを読み込み
			from apps.config import ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S
			
			# 統合された分類データを作成
			self.classification_data = {
				"large_categories": [],
				"medium_categories": [],
				"small_categories": []
			}
			
			# 大分類の統合
			large_categories = set()
			for item in ITEM_CLASS_L:
				large_categories.add(item)
			
			# JSONからも大分類を追加
			for item in json_data:
				large_categories.add(item["large_category_name_ja"])
			
			self.classification_data["large_categories"] = sorted(list(large_categories))
			
			# 中分類の統合
			medium_categories = {}
			for item in ITEM_CLASS_M:
				large = item["data-val"]
				medium = item["value"]
				if large not in medium_categories:
					medium_categories[large] = []
				medium_categories[large].append(medium)
			
			# JSONからも中分類を追加
			for item in json_data:
				large = item["large_category_name_ja"]
				for medium_item in item["medium_categories"]:
					medium = medium_item["medium_category_name_ja"]
					if large not in medium_categories:
						medium_categories[large] = []
					if medium not in medium_categories[large]:
						medium_categories[large].append(medium)
			
			self.classification_data["medium_categories"] = medium_categories
			
			# 小分類の統合
			small_categories = {}
			for item in ITEM_CLASS_S:
				medium = item["data-val"]
				small = item["value"]
				if medium not in small_categories:
					small_categories[medium] = []
				small_categories[medium].append(small)
			
			self.classification_data["small_categories"] = small_categories
			
			print(f"分類データ読み込み完了: 大分類{len(self.classification_data['large_categories'])}個")
			
		except Exception as e:
			print(f"分類データ読み込みエラー: {e}")
			# エラー時はデフォルトの分類データを使用
			self.classification_data = {
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

	def build(self):
		# 戻るボタン
		self.back_button = ft.TextButton(
			"戻る",
			icon=ft.icons.ARROW_BACK,
			on_click=lambda e: self.page.go("/")
		)

		# AIテスト用のカスタムカメラフォームを作成
		self.camera_form = self._create_ai_camera_form()

		# 撮影ボタン（camera_formの機能を使用）
		self.capture_button = ft.ElevatedButton(
			"撮影 (Enter)",
			icon=ft.icons.CAMERA_ALT,
			on_click=self._trigger_camera_form_capture,
			bgcolor=ft.colors.BLUE,
			color=ft.colors.WHITE,
			disabled=True
		)

		# リセットボタン（新しい撮影用）
		self.reset_button = ft.ElevatedButton(
			"新しい撮影",
			icon=ft.icons.REFRESH,
			on_click=self._reset_capture,
			bgcolor=ft.colors.ORANGE,
			color=ft.colors.WHITE,
			disabled=True
		)

		# プレビューボタン（撮影した写真を表示）
		self.preview_button = ft.ElevatedButton(
			"撮影写真プレビュー",
			icon=ft.icons.VISIBILITY,
			on_click=self._show_preview_dialog,
			bgcolor=ft.colors.PURPLE,
			color=ft.colors.WHITE,
			disabled=True
		)


		# 処理ステップ表示
		self.step_display = ft.Text(
			"ステップ1: カメラから画像を取得してください",
			size=16,
			color=ft.colors.BLUE_700,
			weight=ft.FontWeight.BOLD
		)

		# AI処理ボタン
		self.ai_button = ft.ElevatedButton(
			"AI分類実行",
			on_click=self.run_ai_classification,
			icon=ft.icons.SMART_TOY,
			disabled=True,
			bgcolor=ft.colors.BLUE_600,
			color=ft.colors.WHITE
		)

		# 結果表示エリア
		self.results_area = ft.Container(
			content=ft.Column([
				ft.Text("AI分類結果", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
				ft.Divider(),
				ft.Text("結果がここに表示されます", color=ft.colors.GREY_600)
			]),
			padding=20,
			bgcolor=ft.colors.WHITE,
			border_radius=8,
			border=ft.border.all(1, ft.colors.GREY_300)
		)

		# レイアウト（白基調のシンプルデザイン）
		layout = ft.Column([
			# 上部ナビゲーション
			ft.Row([
				self.back_button,
				ft.Text("AI画像分類テスト", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800),
				ft.Container()  # 右側のスペーサー
			], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
			
			# カメラ制御エリア（camera_form.pyを使用）
			ft.Container(
				content=ft.Column([
					ft.Text("画像取得", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
					self.camera_form,
					ft.Row([
						self.capture_button,
						self.preview_button,
						self.reset_button,
					], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
					self.step_display
				]),
				padding=20,
				bgcolor=ft.colors.WHITE,
				border_radius=8,
				border=ft.border.all(1, ft.colors.GREY_300)
			),

			# AI処理エリア
			ft.Container(
				content=ft.Column([
					ft.Text("AI処理", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
					ft.Row([
						self.ai_button
					])
				]),
				padding=20,
				bgcolor=ft.colors.WHITE,
				border_radius=8,
				border=ft.border.all(1, ft.colors.GREY_300)
			),

			# 結果表示エリア
			self.results_area,
		], expand=True, scroll=ft.ScrollMode.AUTO, spacing=15)

		return layout

	def did_mount(self):
		"""コンポーネントがマウントされた時にカメラを起動"""
		# Enterキーでの撮影機能を追加
		if self.page:
			self.page.on_keyboard_event = self.on_keyboard_event
		
		# camera_form.pyのカメラ機能を初期化
		threading.Timer(2.0, self._init_camera_form).start()
	
	def will_unmount(self):
		"""コンポーネントがアンマウントされる時にカメラを停止"""
		if self.camera_form and hasattr(self.camera_form, 'stop_camera'):
			self.camera_form.stop_camera()

	def _init_camera_form(self):
		"""カメラ機能を初期化"""
		try:
			# カメラを開始
			self._start_camera()
			
			# 撮影ボタンを有効にする
			self.capture_button.disabled = False
			self.step_display.value = "ステップ2: 画像をキャプチャしてください"
			self.step_display.color = ft.colors.GREEN_700
			self.update()
				
			print("✅ カメラ機能が初期化されました")
			
		except Exception as e:
			print(f"❌ カメラ初期化エラー: {e}")
			self.show_error(f"カメラ初期化エラー: {str(e)}")

	def _start_camera(self):
		"""カメラを起動"""
		try:
			# 複数のバックエンドを試行
			backends = [
				cv2.CAP_DSHOW,  # DirectShow
				cv2.CAP_MSMF,   # Microsoft Media Foundation
				cv2.CAP_ANY     # 自動選択
			]
			
			self.camera_form.cap = None
			for backend in backends:
				try:
					print(f"バックエンド {backend} を試行中...")
					self.camera_form.cap = cv2.VideoCapture(self.camera_form.camera_index, backend)
					
					if self.camera_form.cap.isOpened():
						print(f"カメラ {self.camera_form.camera_index} が開きました")
						
						# フレームサイズを設定
						self.camera_form.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_form.frame_width)
						self.camera_form.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_form.frame_height)
						
						# バッファサイズを設定（フレーム遅延を防ぐ）
						self.camera_form.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
						
						# 実際にフレームを読み取ってテスト
						success = False
						for attempt in range(3):
							ret, frame = self.camera_form.cap.read()
							if ret and frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
								print(f"カメラ初期化成功: バックエンド {backend} (試行 {attempt + 1})")
								success = True
								break
							else:
								print(f"フレーム取得失敗 (試行 {attempt + 1})")
								time.sleep(0.1)
						
						if success:
							break
						else:
							print(f"バックエンド {backend} でフレーム取得に失敗")
							self.camera_form.cap.release()
							self.camera_form.cap = None
					else:
						print(f"カメラ {self.camera_form.camera_index} を開けませんでした")
						if self.camera_form.cap:
							self.camera_form.cap.release()
							self.camera_form.cap = None
							
				except Exception as e:
					print(f"バックエンド {backend} でエラー: {e}")
					if self.camera_form.cap:
						self.camera_form.cap.release()
						self.camera_form.cap = None
					continue
			
			if self.camera_form.cap is None or not self.camera_form.cap.isOpened():
				self.show_error("カメラを起動できませんでした。他のアプリケーションでカメラを使用していないか確認してください。")
				return
			
			print("カメラ初期化完了")
			self.camera_form.camera_running = True
			self._update_camera_feed()
			
		except Exception as e:
			print(f"カメラ初期化エラー: {e}")
			self.show_error(f"カメラエラー: {str(e)}")

	def _stop_camera(self):
		"""カメラを停止"""
		self.camera_form.camera_running = False
		if self.camera_form.cap is not None:
			self.camera_form.cap.release()
			self.camera_form.cap = None
		time.sleep(0.1)

	def _update_camera_feed(self):
		"""カメラ映像を更新"""
		if not self.camera_form.camera_running or self.camera_form.cap is None:
			return
		
		try:
			ret, frame = self.camera_form.cap.read()
			if ret and frame is not None and hasattr(self.camera_form, 'camera_image') and self.page:
				if frame.shape[0] > 0 and frame.shape[1] > 0:
					try:
						# OpenCVのBGRをRGBに変換
						rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
						
						# PIL Imageに変換
						pil_image = Image.fromarray(rgb_frame)
						
						# バイト配列に変換
						img_byte_arr = io.BytesIO()
						pil_image.save(img_byte_arr, format='JPEG', quality=85)
						img_byte_arr = img_byte_arr.getvalue()
						
						# Base64エンコード
						img_base64 = base64.b64encode(img_byte_arr).decode()
						
						# カメラ画像を更新
						self.camera_form.camera_image.src_base64 = img_base64
						self.camera_form.camera_image.update()
					except Exception as e:
						print(f"フレーム処理エラー: {e}")
						pass
			else:
				print("フレーム取得失敗、再試行中...")
				if not hasattr(self, 'frame_fail_count'):
					self.frame_fail_count = 0
				self.frame_fail_count += 1
				if self.frame_fail_count > 10:
					print("フレーム取得が連続して失敗したため、カメラを停止します")
					self.camera_form.camera_running = False
					return
		except Exception as e:
			print(f"カメラフレーム更新エラー: {e}")
			if "can't grab frame" in str(e) or "OnReadSample" in str(e):
				print("カメラエラーが発生したため、カメラを停止します")
				self.camera_form.camera_running = False
				return
		
		# フレーム取得成功時は失敗カウンターをリセット
		if hasattr(self, 'frame_fail_count'):
			self.frame_fail_count = 0
		
		# 次のフレームを取得するためにタイマーを設定
		if self.camera_form.camera_running:
			threading.Timer(0.033, self._update_camera_feed).start()  # 約30FPS

	def _capture_photo(self, e):
		"""写真を撮影"""
		if self.camera_form.cap is None or not self.camera_form.camera_running:
			self.show_error("カメラが起動していません")
			return
		
		ret, frame = self.camera_form.cap.read()
		if not ret:
			self.show_error("撮影に失敗しました")
			return
		
		try:
			# OpenCVフレームをPIL画像に変換
			frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			pil_image = Image.fromarray(frame_rgb)
			
			# 画像を保存
			self.captured_image = pil_image
					
			# ステップ更新（撮影完了→AI分類実行可能）
			self.step_display.value = "ステップ3: AI分類を実行してください"
			self.step_display.color = ft.colors.ORANGE_700
			self.ai_button.disabled = False
			
			# 撮影ボタンを無効化（1枚撮影済み）
			self.capture_button.disabled = True
			self.capture_button.text = "撮影完了"
			
			# リセットボタンとプレビューボタンを有効化
			self.reset_button.disabled = False
			self.preview_button.disabled = False
					
			self.update()
			self.show_success("画像をキャプチャしました。AI分類を実行してください。")
			print("✅ AIテスト用画像を取得しました")
			
		except Exception as e:
			self.show_error(f"画像キャプチャエラー: {str(e)}")

	def _trigger_camera_form_capture(self, e):
		"""撮影機能をトリガー（1枚制限）"""
		if self.captured_image is not None:
			self.show_error("既に1枚撮影済みです。AI分類を実行してください。")
			return
			
		self._capture_photo(None)

	def _show_preview_dialog(self, e):
		"""撮影した写真のプレビューダイアログを表示"""
		if self.captured_image is None:
			self.show_error("撮影された写真がありません")
			return
		
		try:
			# 画像をBase64に変換
			img_byte_arr = io.BytesIO()
			self.captured_image.save(img_byte_arr, format='JPEG', quality=90)
			img_byte_arr = img_byte_arr.getvalue()
			img_base64 = base64.b64encode(img_byte_arr).decode()
			
			# プレビュー画像を作成
			preview_image = ft.Image(
				src_base64=img_base64,
				width=600,
				height=450,
				fit=ft.ImageFit.CONTAIN,
				border_radius=8
			)
			
			# ダイアログを作成
			dialog = ft.AlertDialog(
				title=ft.Text("撮影写真プレビュー", size=18, weight=ft.FontWeight.BOLD),
				content=ft.Container(
					content=preview_image,
					width=600,
					height=450,
					alignment=ft.alignment.center
				),
				actions=[
					ft.TextButton("閉じる", on_click=lambda e: self._close_preview_dialog())
				],
				actions_alignment=ft.MainAxisAlignment.END
			)
			
			# ダイアログを表示
			if self.page:
				self.page.dialog = dialog
				dialog.open = True
				self.page.update()
				
		except Exception as e:
			self.show_error(f"プレビュー表示エラー: {str(e)}")

	def _close_preview_dialog(self):
		"""プレビューダイアログを閉じる"""
		if self.page and self.page.dialog:
			self.page.dialog.open = False
			self.page.update()

	def _reset_capture(self, e):
		"""撮影をリセットして新しい撮影を可能にする"""
		self.captured_image = None
		self.classification_results = None
		
		# ボタン状態をリセット
		self.capture_button.disabled = False
		self.capture_button.text = "撮影 (Enter)"
		self.reset_button.disabled = True
		self.preview_button.disabled = True
		self.ai_button.disabled = True
		
		# ステップ表示をリセット
		self.step_display.value = "ステップ2: 画像をキャプチャしてください"
		self.step_display.color = ft.colors.GREEN_700
		
		# 結果表示をクリア
		self.results_area.content = ft.Column([
			ft.Text("AI分類結果", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
			ft.Divider(),
			ft.Text("結果がここに表示されます", color=ft.colors.GREY_600)
		])
				
		self.update()
		self.show_success("撮影をリセットしました。新しい画像を撮影してください。")
		print("🔄 AIテスト撮影をリセットしました")

	def on_keyboard_event(self, e):
		"""キーボードイベントハンドラー"""
		if e.key == "Enter":
			# 撮影機能を使用
			self._trigger_camera_form_capture(None)

	def run_ai_classification(self, e):
		if self.captured_image:
			try:
				# AI分類実行
				self.step_display.value = "AI分類実行中..."
				self.step_display.color = ft.colors.YELLOW_700
				self.update()
				
				# カスタムYOLOモデルを使用（優先順位付き）
				if self.yolo_model is None:
					print("🔄 カスタムYOLOモデルを読み込み中...")
					
					# モデル優先順位: yolov8x_seg_custom.pt > yolov11x_seg_custom.pt > yolov8n.pt
					model_candidates = [
						("yolov8x_seg_custom.pt", "YOLOv8x カスタムモデル"),
						("yolo11x_seg_custom.pt", "YOLOv11x カスタムモデル"),
						("yolov8n.pt", "YOLOv8n デフォルトモデル")
					]
					
					model_loaded = False
					for model_file, model_name in model_candidates:
						model_path = Path(__file__).parent.parent / model_file
						if model_path.exists():
							try:
								print(f"🔄 {model_name}を読み込み中... ({model_file})")
								print(f"📁 ファイルサイズ: {model_path.stat().st_size / (1024*1024):.1f} MB")
								
								self.yolo_model = YOLO(str(model_path))
								print(f"✅ {model_name}読み込み成功")
								model_loaded = True
								break
								
							except Exception as model_error:
								print(f"❌ {model_name}読み込みエラー: {model_error}")
								if "C3k2" in str(model_error):
									print("💡 互換性エラー: 次のモデルを試行します")
								continue
						else:
							print(f"❌ {model_file}が見つかりません")
					
					if not model_loaded:
						print("❌ すべてのカスタムモデルが読み込めませんでした")
						print("🔄 デフォルトモデルにフォールバック...")
						self.yolo_model = YOLO('yolov8n.pt')
				
				# 画像をOpenCV形式に変換
				cv_image = cv2.cvtColor(np.array(self.captured_image), cv2.COLOR_RGB2BGR)
				
				# YOLOで物体検出・分類実行
				results = self.yolo_model(cv_image)
				
				# 結果の解析
				self.classification_results = self._analyze_yolo_results(results)
				
				# 結果表示
				self.update_classification_results()
				
				# ステップ完了
				self.step_display.value = "完了: AI分類が完了しました"
				self.step_display.color = ft.colors.GREEN_700
				
				self.update()
				self.show_success("AI分類完了")
			except Exception as e:
				self.show_error(f"AI分類エラー: {str(e)}")
				import traceback
				traceback.print_exc()

	def _analyze_yolo_results(self, results):
		"""YOLOの結果を解析して分類結果を作成"""
		classification_results = {
			"large_category": "その他",
			"medium_category": "その他",
			"small_category": "その他",
			"confidence": 0.0,
			"detected_objects": []
		}
		
		try:
			for result in results:
				if result.boxes is not None and len(result.boxes) > 0:
					# 最も信頼度の高い検出結果を取得
					best_box = result.boxes[0]
					confidence = float(best_box.conf[0])
					class_id = int(best_box.cls[0])
					
					# クラス名を取得（モデルのクラス名を使用）
					class_names = result.names
					detected_class = class_names[class_id] if class_id < len(class_names) else "unknown"
					
					classification_results["confidence"] = confidence
					classification_results["detected_objects"].append({
						"class": detected_class,
						"confidence": confidence
					})
					
					# 検出されたクラス名から分類を推定
					estimated_classification = self._estimate_classification(detected_class)
					classification_results.update(estimated_classification)
					
		except Exception as e:
			print(f"YOLO結果解析エラー: {e}")
		
		return classification_results

	def _estimate_classification(self, detected_class):
		"""検出されたクラス名から大・中・小分類を推定（カスタムモデル対応）"""
		# キーワードベースの分類推定
		detected_class_lower = detected_class.lower()
		
		# 大分類の推定
		large_category = "その他"
		medium_category = "その他"
		small_category = "その他"
		
		# カスタムモデル用の詳細分類（拾得物に特化）
		print(f"🔍 検出クラス: {detected_class} -> 分類推定中...")
		
		# 現金の検出（カスタムモデル対応）
		if any(keyword in detected_class_lower for keyword in ["cash", "money", "現金", "金", "coin", "coins", "硬貨", "紙幣"]):
			large_category = "現金"
			medium_category = "現金"
			small_category = "現金"
			print("💰 現金として分類")
		
		# かばん類の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["bag", "handbag", "backpack", "かばん", "バッグ", "tote", "purse", "briefcase", "suitcase"]):
			large_category = "かばん類"
			if any(keyword in detected_class_lower for keyword in ["hand", "手提げ", "handbag", "tote"]):
				medium_category = "手提げかばん"
				small_category = "ハンドバッグ"
			elif any(keyword in detected_class_lower for keyword in ["shoulder", "肩掛け", "shoulder"]):
				medium_category = "肩掛けかばん"
				small_category = "ショルダーバッグ"
			elif any(keyword in detected_class_lower for keyword in ["backpack", "リュック", "rucksack"]):
				medium_category = "肩掛けかばん"
				small_category = "リュックサック"
			else:
				medium_category = "手提げかばん"
				small_category = "ハンドバッグ"
			print("👜 かばん類として分類")
		
		# 財布類の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["wallet", "purse", "財布", "がま口", "coin_purse", "card_case"]):
			large_category = "財布類"
			if any(keyword in detected_class_lower for keyword in ["がま口", "coin_purse"]):
				medium_category = "がま口"
				small_category = "がま口"
			else:
				medium_category = "財布"
				small_category = "財布"
			print("👛 財布類として分類")
		
		# 携帯電話の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["phone", "mobile", "携帯", "スマホ", "smartphone", "iphone", "android"]):
			large_category = "携帯電話類"
			medium_category = "携帯電話機"
			small_category = "携帯電話機"
			print("📱 携帯電話類として分類")
		
		# 時計の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["watch", "clock", "時計", "腕時計", "wristwatch"]):
			large_category = "時計類"
			medium_category = "腕時計"
			small_category = "腕時計男性（金属製ベルト）"
			print("⌚ 時計類として分類")
		
		# めがねの検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["glasses", "eyeglasses", "めがね", "眼鏡", "sunglasses", "サングラス"]):
			large_category = "めがね類"
			medium_category = "めがね"
			small_category = "めがね（ケースあり）"
			print("👓 めがね類として分類")
		
		# 鍵の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["key", "keys", "鍵", "キー", "keychain", "キーホルダー"]):
			large_category = "鍵類"
			medium_category = "鍵"
			small_category = "自動車用鍵"
			print("🗝️ 鍵類として分類")
		
		# 傘の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["umbrella", "傘", "かさ", "parasol", "日傘"]):
			large_category = "かさ類"
			medium_category = "かさ"
			small_category = "長傘"
			print("☂️ かさ類として分類")
		
		# 衣類の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["clothes", "clothing", "shirt", "jacket", "衣類", "服", "coat", "blouse", "dress"]):
			large_category = "衣類・履物類"
			medium_category = "上着類"
			small_category = "Tシャツ"
			print("👕 衣類として分類")
		
		# 靴の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["shoe", "shoes", "boot", "靴", "履物", "sneaker", "sandal"]):
			large_category = "衣類・履物類"
			medium_category = "履物類"
			small_category = "ランニングシューズ"
			print("👟 履物類として分類")
		
		# 帽子の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["hat", "cap", "帽子", "beanie", "cap"]):
			large_category = "衣類・履物類"
			medium_category = "帽子類"
			small_category = "帽子"
			print("🧢 帽子類として分類")
		
		# 手袋の検出（カスタムモデル対応）
		elif any(keyword in detected_class_lower for keyword in ["glove", "gloves", "手袋", "mittens"]):
			large_category = "衣類・履物類"
			medium_category = "手袋"
			small_category = "手袋（両手）"
			print("🧤 手袋として分類")
		
		# カスタムモデル特有の分類を追加
		else:
			# カスタムモデルが返す可能性のあるクラス名を直接マッピング
			if detected_class_lower in ["lost_item", "拾得物", "遺失物"]:
				large_category = "その他"
				medium_category = "その他"
				small_category = "その他"
				print("📦 拾得物として分類")
			else:
				print(f"❓ 未知のクラス: {detected_class} -> その他として分類")
		
		return {
			"large_category": large_category,
			"medium_category": medium_category,
			"small_category": small_category
		}

	def update_classification_results(self):
		"""分類結果を表示エリアに更新（横並び表示）"""
		if self.classification_results:
			content = ft.Column([
				ft.Text("AI分類結果", size=16, weight=ft.FontWeight.BOLD),
				ft.Divider(),
				
				# 分類結果を横並びで表示
				ft.Row([
					# 大分類
					ft.Container(
						content=ft.Column([
							ft.Text("大分類", size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
							ft.Text(self.classification_results["large_category"], 
							       size=16, color=ft.colors.BLUE_700, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
						], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
						padding=15,
						bgcolor=ft.colors.BLUE_50,
						border_radius=8,
						expand=True,
						height=80
					),
					
					# 中分類
					ft.Container(
						content=ft.Column([
							ft.Text("中分類", size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
							ft.Text(self.classification_results["medium_category"], 
							       size=16, color=ft.colors.GREEN_700, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
						], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
						padding=15,
						bgcolor=ft.colors.GREEN_50,
						border_radius=8,
						expand=True,
						height=80
					),
					
					# 小分類
					ft.Container(
						content=ft.Column([
							ft.Text("小分類", size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
							ft.Text(self.classification_results["small_category"], 
							       size=16, color=ft.colors.ORANGE_700, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
						], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
						padding=15,
						bgcolor=ft.colors.ORANGE_50,
						border_radius=8,
						expand=True,
						height=80
					),
				], spacing=10),
				
				ft.Divider(),
				
				# 信頼度と検出オブジェクトの表示
				ft.Row([
					ft.Text(f"信頼度: {self.classification_results['confidence']:.2f}", 
					       size=14, color=ft.colors.GREY_700, expand=True),
					ft.Text(f"検出オブジェクト: {len(self.classification_results['detected_objects'])}個", 
					       size=14, color=ft.colors.GREY_700, expand=True),
				]),
				
				# 検出されたオブジェクトの詳細表示
				*([ft.Text(f"  • {obj['class']} (信頼度: {obj['confidence']:.2f})", 
				         size=12, color=ft.colors.GREY_600) 
				  for obj in self.classification_results["detected_objects"]] if self.classification_results["detected_objects"] else [])
			], spacing=10)
			
			self.results_area.content = content
			self.update()


	def show_success(self, message):
		if self.page:
			self.page.snack_bar.content = ft.Text(message, color=ft.colors.WHITE)
			self.page.snack_bar.bgcolor = ft.colors.GREEN_700
			self.page.snack_bar.open = True
			self.page.update()

	def show_error(self, message):
		if self.page:
			self.page.snack_bar.content = ft.Text(message, color=ft.colors.WHITE)
			self.page.snack_bar.bgcolor = ft.colors.RED_700
			self.page.snack_bar.open = True
			self.page.update()


# グローバル変数でAI分類結果を管理
ai_classification_result = None