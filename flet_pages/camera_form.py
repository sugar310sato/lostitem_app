import flet as ft
import cv2
import base64
import io
from PIL import Image
import threading
import time


class CameraFormView(ft.UserControl):
    """カメラ撮影専用ビュー"""
    def __init__(self, on_capture_complete=None, on_back=None):
        super().__init__()
        self.on_capture_complete = on_capture_complete
        self.on_back = on_back
        self.cap = None
        self.is_capturing = False
        self.captured_photos = []
        self.bundle_photos = []
        self.is_bundle_mode = False
        self.camera_running = False
        
        # ダイアログ管理
        self.current_dialog = None
        
        # カメラ設定
        self.camera_index = 0
        self.frame_width = 640
        self.frame_height = 480
        
        # 利用可能なカメラを確認
        self.check_available_cameras()
    
    def check_available_cameras(self):
        """利用可能なカメラを確認"""
        print("利用可能なカメラを確認中...")
        available_cameras = []
        
        for i in range(5):  # 0-4のカメラインデックスを確認
            cap = None
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                        print(f"カメラ {i}: 利用可能")
                        available_cameras.append(i)
                    else:
                        print(f"カメラ {i}: 開けますがフレーム取得不可")
                else:
                    print(f"カメラ {i}: 利用不可")
            except Exception as e:
                print(f"カメラ {i}: エラー - {e}")
            finally:
                if cap:
                    cap.release()
        
        if available_cameras:
            print(f"利用可能なカメラ: {available_cameras}")
            # 最初の利用可能なカメラを使用
            self.camera_index = available_cameras[0]
            print(f"カメラ {self.camera_index} を使用します")
        else:
            print("利用可能なカメラが見つかりませんでした")
        
    def build(self):
        # カメラ映像表示用のImageコントロール
        self.camera_image = ft.Image(
            width=self.frame_width,
            height=self.frame_height,
            fit=ft.ImageFit.COVER,
            border_radius=8,
            src="",  # 初期は空
        )
        
        # カメラ映像表示用のコンテナ
        self.camera_container = ft.Container(
            content=self.camera_image,
            width=self.frame_width,
            height=self.frame_height,
            bgcolor=ft.colors.BLACK,
            alignment=ft.alignment.center,
            border_radius=8,
            border=ft.border.all(2, ft.colors.GREY_400)
        )
        
        # 撮影ガイドフレーム（70%サイズ、中央配置）
        guide_frame_size = int(min(self.frame_width, self.frame_height) * 0.7)
        self.guide_frame = ft.Container(
            width=guide_frame_size,
            height=guide_frame_size,
            border=ft.border.all(3, ft.colors.RED),
            border_radius=8,
            bgcolor=ft.colors.TRANSPARENT,
        )
        
        # 撮影された写真の表示用
        self.photo_grid = ft.GridView(
            runs_count=3,
            max_extent=120,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        # 撮影枚数表示用
        self.photo_count_text = ft.Text(
            f"撮影済み写真: メイン{len(self.captured_photos)}/3枚, 同梱物{len(self.bundle_photos)}/3枚", 
            size=16, 
            weight=ft.FontWeight.BOLD
        )
        
        # ボタン群
        self.capture_button = ft.ElevatedButton(
            "撮影",
            icon=ft.icons.CAMERA_ALT,
            on_click=self.capture_photo,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )
        
        self.bundle_button = ft.ElevatedButton(
            "同梱物撮影",
            icon=ft.icons.ADD_BOX,
            on_click=self.toggle_bundle_mode,
            bgcolor=ft.colors.ORANGE,
            color=ft.colors.WHITE
        )
        
        self.retake_button = ft.ElevatedButton(
            "取り直し",
            icon=ft.icons.REFRESH,
            on_click=self.retake_last_photo,
            bgcolor=ft.colors.RED,
            color=ft.colors.WHITE
        )
        
        self.next_button = ft.ElevatedButton(
            "入力に進む",
            icon=ft.icons.ARROW_FORWARD,
            on_click=self.proceed_to_form,
            bgcolor=ft.colors.GREEN,
            color=ft.colors.WHITE
        )
        
        self.back_button = ft.TextButton(
            "戻る",
            icon=ft.icons.ARROW_BACK,
            on_click=self.go_back
        )
        
        return ft.Column([
            ft.Text("ステップ1: カメラで撮影", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Stack([
                    self.camera_container,
                    ft.Container(
                        content=self.guide_frame,
                        alignment=ft.alignment.center,  # ガイドフレームを中央に配置
                        width=self.frame_width,
                        height=self.frame_height
                    )
                ], alignment=ft.alignment.center),
                alignment=ft.alignment.center,
                padding=10
            ),
            ft.Row([
                self.capture_button,
                self.bundle_button,
                self.retake_button,
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            self.photo_count_text,
            ft.Container(
                content=self.photo_grid,
                height=150,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                padding=10
            ),
            ft.Row([
                self.back_button,
                self.next_button,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
    
    def did_mount(self):
        """コンポーネントがマウントされた時にカメラを起動"""
        self.start_camera()
    
    def will_unmount(self):
        """コンポーネントがアンマウントされる時にカメラを停止"""
        self.camera_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def start_camera(self):
        """カメラを起動"""
        try:
            # 複数のバックエンドを試行
            backends = [
                cv2.CAP_DSHOW,  # DirectShow
                cv2.CAP_MSMF,   # Microsoft Media Foundation
                cv2.CAP_ANY     # 自動選択
            ]
            
            self.cap = None
            for backend in backends:
                try:
                    print(f"バックエンド {backend} を試行中...")
                    self.cap = cv2.VideoCapture(self.camera_index, backend)
                    
                    if self.cap.isOpened():
                        print(f"カメラ {self.camera_index} が開きました")
                        
                        # フレームサイズを設定
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                        
                        # バッファサイズを設定（フレーム遅延を防ぐ）
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # 実際にフレームを読み取ってテスト（複数回試行）
                        success = False
                        for attempt in range(3):
                            ret, frame = self.cap.read()
                            if ret and frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                                print(f"カメラ初期化成功: バックエンド {backend} (試行 {attempt + 1})")
                                success = True
                                break
                            else:
                                print(f"フレーム取得失敗 (試行 {attempt + 1})")
                                time.sleep(0.1)  # 少し待ってから再試行
                        
                        if success:
                            break
                        else:
                            print(f"バックエンド {backend} でフレーム取得に失敗")
                            self.cap.release()
                            self.cap = None
                    else:
                        print(f"カメラ {self.camera_index} を開けませんでした")
                        if self.cap:
                            self.cap.release()
                            self.cap = None
                            
                except Exception as e:
                    print(f"バックエンド {backend} でエラー: {e}")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
                    continue
            
            if self.cap is None or not self.cap.isOpened():
                self.show_error("カメラを起動できませんでした。他のアプリケーションでカメラを使用していないか確認してください。")
                return
            
            print("カメラ初期化完了")
            self.camera_running = True
            self.update_camera_feed()
            
        except Exception as e:
            print(f"カメラ初期化エラー: {e}")
            self.show_error(f"カメラエラー: {str(e)}")
    
    def stop_camera(self):
        """カメラを停止"""
        self.camera_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        # スレッドの終了を待つ
        import time
        time.sleep(0.1)
    
    def update_camera_feed(self):
        """カメラ映像を更新"""
        if not self.camera_running or self.cap is None:
            return
        
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None and hasattr(self, 'camera_image') and self.page:
                # フレームサイズを確認
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
                        
                        # 既存のImageコントロールのsrc_base64を更新（点滅を防ぐ）
                        self.camera_image.src_base64 = img_base64
                        self.camera_image.update()
                    except Exception as e:
                        print(f"フレーム処理エラー: {e}")
                        # フレーム処理でエラーが発生した場合はスキップ
                        pass
            else:
                # フレームが取得できない場合、少し待ってから再試行
                print("フレーム取得失敗、再試行中...")
                # 連続して失敗した場合はカメラを停止
                if not hasattr(self, 'frame_fail_count'):
                    self.frame_fail_count = 0
                self.frame_fail_count += 1
                if self.frame_fail_count > 10:  # 10回連続で失敗した場合
                    print("フレーム取得が連続して失敗したため、カメラを停止します")
                    self.camera_running = False
                    return
        except Exception as e:
            print(f"カメラフレーム更新エラー: {e}")
            # エラーが続く場合はカメラを停止
            if "can't grab frame" in str(e) or "OnReadSample" in str(e):
                print("カメラエラーが発生したため、カメラを停止します")
                self.camera_running = False
                return
        
        # フレーム取得成功時は失敗カウンターをリセット
        if hasattr(self, 'frame_fail_count'):
            self.frame_fail_count = 0
        
        # 次のフレームを取得するためにタイマーを設定
        if self.camera_running:
            threading.Timer(0.033, self.update_camera_feed).start()  # 約30FPS
    
    def capture_photo(self, e):
        """写真を撮影"""
        if self.cap is None or not self.camera_running:
            self.show_error("カメラが起動していません")
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.show_error("撮影に失敗しました")
            return
        
        # 撮影枚数制限チェック
        if self.is_bundle_mode:
            if len(self.bundle_photos) >= 3:
                self.show_error("同梱物写真は最大3枚までです")
                return
        else:
            if len(self.captured_photos) >= 3:
                self.show_error("メイン写真は最大3枚までです")
                return
        
        # タイムスタンプでファイル名を生成
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        photo_data = {
            'timestamp': timestamp,
            'frame': frame,
            'is_bundle': self.is_bundle_mode
        }
        
        if self.is_bundle_mode:
            self.bundle_photos.append(photo_data)
        else:
            self.captured_photos.append(photo_data)
        
        self.update_photo_grid()
    
    def toggle_bundle_mode(self, e):
        """同梱物撮影モードを切り替え"""
        self.is_bundle_mode = not self.is_bundle_mode
        if self.is_bundle_mode:
            self.bundle_button.bgcolor = ft.colors.GREEN
            self.bundle_button.text = "同梱物撮影中"
        else:
            self.bundle_button.bgcolor = ft.colors.ORANGE
            self.bundle_button.text = "同梱物撮影"
        self.bundle_button.update()
    
    def retake_last_photo(self, e):
        """最後の写真を取り直し"""
        if self.is_bundle_mode and self.bundle_photos:
            self.bundle_photos.pop()
        elif not self.is_bundle_mode and self.captured_photos:
            self.captured_photos.pop()
        else:
            self.show_error("取り直す写真がありません")
            return
        
        self.update_photo_grid()
    
    def update_photo_grid(self):
        """撮影済み写真のグリッドを更新"""
        self.photo_grid.controls.clear()
        
        # メイン写真を表示
        for i, photo in enumerate(self.captured_photos):
            thumbnail = self.create_thumbnail(photo['frame'])
            photo_container = ft.Container(
                content=ft.Column([
                    thumbnail,
                    ft.Text(f"メイン{i+1}", size=10, text_align=ft.TextAlign.CENTER)
                ]),
                border=ft.border.all(2, ft.colors.BLUE),
                border_radius=8,
                padding=5
            )
            self.photo_grid.controls.append(photo_container)
        
        # 同梱物写真を表示
        for i, photo in enumerate(self.bundle_photos):
            thumbnail = self.create_thumbnail(photo['frame'])
            photo_container = ft.Container(
                content=ft.Column([
                    thumbnail,
                    ft.Text(f"同梱{i+1}", size=10, text_align=ft.TextAlign.CENTER)
                ]),
                border=ft.border.all(2, ft.colors.ORANGE),
                border_radius=8,
                padding=5
            )
            self.photo_grid.controls.append(photo_container)
        
        self.photo_grid.update()
        
        # 撮影枚数表示を更新
        self.photo_count_text.value = f"撮影済み写真: メイン{len(self.captured_photos)}/3枚, 同梱物{len(self.bundle_photos)}/3枚"
        self.photo_count_text.update()
    
    def create_thumbnail(self, frame):
        """フレームからサムネイルを作成（正方形1:1）"""
        # フレームを正方形にリサイズ
        small_frame = cv2.resize(frame, (100, 100))
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # PIL Imageに変換
        pil_image = Image.fromarray(rgb_frame)
        
        # 解像度を下げる（JPEGの品質を下げる）
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG', quality=60, optimize=True)  # 品質を60に下げる
        img_byte_arr = img_byte_arr.getvalue()
        
        # Base64エンコード
        img_base64 = base64.b64encode(img_byte_arr).decode()
        
        return ft.Image(
            src_base64=img_base64,
            width=100,
            height=100,
            fit=ft.ImageFit.COVER,  # 正方形で余白をなくす
            border_radius=4
        )
    
    def proceed_to_form(self, e):
        """フォーム入力画面に進む"""
        # 撮影データを保存（撮影なしでも進める）
        photo_data = {
            'main_photos': self.captured_photos,
            'bundle_photos': self.bundle_photos
        }
        
        if callable(self.on_capture_complete):
            self.on_capture_complete(photo_data)
    
    def go_back(self, e):
        """前の画面に戻る"""
        if callable(self.on_back):
            self.on_back()
    
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
