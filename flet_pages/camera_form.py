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
        self.main_photos = []  # メイン写真（最大1枚）
        self.sub_photos = []   # サブ写真（最大2枚）
        self.bundle_photos = []  # 同梱物写真（最大3枚）
        self.is_bundle_mode = False
        self.camera_running = False
        self.selected_photo_index = -1  # 選択された写真のインデックス
        self.selected_photo_type = None  # 選択された写真のタイプ（main/sub/bundle）
        self.dragged_photo = None  # ドラッグ中の写真
        
        # ダイアログ管理
        self.current_dialog = None
        
        # カメラ設定
        self.camera_index = 0
        self.frame_width = 480
        self.frame_height = 360
        
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
            max_extent=100,
            child_aspect_ratio=0.8,  # 縦長にしてテキスト表示領域を確保
            spacing=8,
            run_spacing=8,
        )
        
        # 撮影枚数表示用
        self.photo_count_text = ft.Text(
            f"撮影済み写真: メイン{len(self.main_photos)}/1枚, サブ{len(self.sub_photos)}/2枚, 同梱物{len(self.bundle_photos)}/3枚", 
            size=16, 
            weight=ft.FontWeight.BOLD
        )
        
        # ボタン群
        self.capture_button = ft.ElevatedButton(
            "撮影 (Enter)",
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
        
        self.clear_all_button = ft.ElevatedButton(
            "すべて削除",
            icon=ft.icons.DELETE_FOREVER,
            on_click=self.clear_all_photos,
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
            # ========================================
            # 上部ナビゲーションボタン
            # ========================================
            ft.Row([
                self.back_button,
                ft.Text("ステップ1: カメラで撮影", size=24, weight=ft.FontWeight.BOLD),
                self.next_button,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # ========================================
            # 注意事項（小さく表示）
            # ========================================
            ft.Text(
                "⚠️ 対象物をガイドフレームに収めて撮影してください (Enterキーまたは撮影ボタン) 最大3枚まで",
                size=10,
                color=ft.colors.RED,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            ),
            
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
                self.clear_all_button,
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            self.photo_count_text,
            ft.Container(
                content=self.photo_grid,
                height=150,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                padding=8
            ),
        ], spacing=15)
    
    def did_mount(self):
        """コンポーネントがマウントされた時にカメラを起動"""
        self.start_camera()
        # Enterキーでの撮影機能を追加
        if self.page:
            self.page.on_keyboard_event = self.on_keyboard_event
    
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
    
    def on_keyboard_event(self, e):
        """キーボードイベントハンドラー"""
        if e.key == "Enter":
            # ダイアログが開いている時は撮影を無効にする
            if self.page and self.page.dialog and self.page.dialog.open:
                return
            self.capture_photo(None)
        elif e.key == "Arrow Left":
            # 写真が存在する場合のみ選択可能
            total_photos = len(self.main_photos) + len(self.sub_photos) + len(self.bundle_photos)
            if total_photos > 0:
                self.select_previous_photo()
        elif e.key == "Arrow Right":
            # 写真が存在する場合のみ選択可能
            total_photos = len(self.main_photos) + len(self.sub_photos) + len(self.bundle_photos)
            if total_photos > 0:
                self.select_next_photo()
        elif e.key == "Delete":
            # 写真が選択されている場合のみ削除可能
            if self.selected_photo_index >= 0:
                self.delete_selected_photo()
    
    def capture_photo(self, e):
        """写真を撮影"""
        if self.cap is None or not self.camera_running:
            self.show_error("カメラが起動していません")
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.show_error("撮影に失敗しました")
            return
        
        # タイムスタンプでファイル名を生成
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        photo_data = {
            'timestamp': timestamp,
            'frame': frame,
            'is_bundle': self.is_bundle_mode
        }
        
        if self.is_bundle_mode:
            if len(self.bundle_photos) < 3:
                self.bundle_photos.append(photo_data)
        else:
            # メイン写真が空の場合はメインに、そうでなければサブに追加
            if len(self.main_photos) == 0:
                self.main_photos.append(photo_data)
            elif len(self.sub_photos) < 2:
                self.sub_photos.append(photo_data)
            
        
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
    
    def clear_all_photos(self, e):
        """すべての写真を削除"""
        self.main_photos.clear()
        self.sub_photos.clear()
        self.bundle_photos.clear()
        self.selected_photo_index = -1
        self.selected_photo_type = None
        self.update_photo_grid()
    
    def select_previous_photo(self):
        """前の写真を選択"""
        total_photos = len(self.main_photos) + len(self.sub_photos) + len(self.bundle_photos)
        if total_photos == 0:
            return
        
        if self.selected_photo_index <= 0:
            self.selected_photo_index = total_photos - 1
        else:
            self.selected_photo_index -= 1
        
        self.update_photo_grid()
    
    def select_next_photo(self):
        """次の写真を選択"""
        total_photos = len(self.main_photos) + len(self.sub_photos) + len(self.bundle_photos)
        if total_photos == 0:
            return
        
        if self.selected_photo_index >= total_photos - 1:
            self.selected_photo_index = 0
        else:
            self.selected_photo_index += 1
        
        self.update_photo_grid()
    
    def delete_selected_photo(self):
        """選択された写真を削除"""
        if self.selected_photo_index < 0:
            return
        
        if self.selected_photo_index < len(self.main_photos):
            # メイン写真を削除
            self.main_photos.pop(self.selected_photo_index)
            self.selected_photo_type = "main"
            # メイン写真が削除された場合、サブ写真1をメイン写真に昇格
            if len(self.main_photos) == 0 and len(self.sub_photos) > 0:
                promoted_photo = self.sub_photos.pop(0)
                self.main_photos.append(promoted_photo)
        elif self.selected_photo_index < len(self.main_photos) + len(self.sub_photos):
            # サブ写真を削除
            sub_index = self.selected_photo_index - len(self.main_photos)
            self.sub_photos.pop(sub_index)
            self.selected_photo_type = "sub"
        else:
            # 同梱物写真を削除
            bundle_index = self.selected_photo_index - len(self.main_photos) - len(self.sub_photos)
            self.bundle_photos.pop(bundle_index)
            self.selected_photo_type = "bundle"
        
        # 選択インデックスを調整
        total_photos = len(self.main_photos) + len(self.sub_photos) + len(self.bundle_photos)
        if self.selected_photo_index >= total_photos:
            self.selected_photo_index = max(0, total_photos - 1)
        
        self.update_photo_grid()
    
    def update_photo_grid(self):
        """撮影済み写真のグリッドを更新"""
        self.photo_grid.controls.clear()
        current_index = 0
        
        # メイン写真を表示（赤枠で強調）
        for i, photo in enumerate(self.main_photos):
            is_selected = (current_index == self.selected_photo_index)
            thumbnail = self.create_thumbnail(photo['frame'])
            
            # メイン写真は赤枠で強調表示
            border_color = ft.colors.RED_700 if is_selected else ft.colors.RED
            border_width = 4 if is_selected else 3
            
            photo_container = ft.GestureDetector(
                content=ft.Container(
                    content=ft.Stack([
                        # 写真とラベル
                        ft.Column([
                            ft.Container(
                                content=thumbnail,
                                width=80,
                                height=80,
                                border_radius=4,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"メイン写真", 
                                    size=10, 
                                    text_align=ft.TextAlign.CENTER, 
                                    color=ft.colors.RED, 
                                    weight=ft.FontWeight.BOLD
                                ),
                                width=80,
                                height=20,
                                alignment=ft.alignment.center,
                                bgcolor=ft.colors.WHITE,
                                border_radius=2
                            )
                        ], spacing=2),
                        # 削除ボタン（右上の×）
                        ft.Container(
                            content=ft.Text(
                                "×",
                                size=16,
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            alignment=ft.alignment.top_right,
                            width=24,
                            height=24,
                            bgcolor=ft.colors.RED_600 if is_selected else ft.colors.RED,
                            border_radius=12,
                            on_click=lambda e, idx=i: self.delete_photo(idx, "main")
                        )
                    ]),
                    border=ft.border.all(border_width, border_color),
                    border_radius=6,
                    padding=4,
                    width=100,
                    height=120
                ),
                on_tap=lambda e, photo_data=photo, idx=current_index: self.select_photo(idx, "main"),
                on_double_tap=lambda e, photo_data=photo: self.show_photo_dialog(photo_data)
            )
            self.photo_grid.controls.append(photo_container)
            current_index += 1
        
        # サブ写真を表示
        for i, photo in enumerate(self.sub_photos):
            is_selected = (current_index == self.selected_photo_index)
            thumbnail = self.create_thumbnail(photo['frame'])
            
            # 選択状態に応じてボーダー色を変更
            border_color = ft.colors.BLUE_700 if is_selected else ft.colors.BLUE
            border_width = 3 if is_selected else 1
            
            photo_container = ft.GestureDetector(
                content=ft.Container(
                    content=ft.Stack([
                        # 写真とラベル
                        ft.Column([
                            ft.Container(
                                content=thumbnail,
                                width=80,
                                height=80,
                                border_radius=4,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"サブ写真{i+1}", 
                                    size=10, 
                                    text_align=ft.TextAlign.CENTER, 
                                    color=ft.colors.BLUE, 
                                    weight=ft.FontWeight.BOLD
                                ),
                                width=80,
                                height=20,
                                alignment=ft.alignment.center,
                                bgcolor=ft.colors.WHITE,
                                border_radius=2
                            )
                        ], spacing=2),
                        # 削除ボタン（右上の×）
                        ft.Container(
                            content=ft.Text(
                                "×",
                                size=16,
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            alignment=ft.alignment.top_right,
                            width=24,
                            height=24,
                            bgcolor=ft.colors.RED_600 if is_selected else ft.colors.RED,
                            border_radius=12,
                            on_click=lambda e, idx=i: self.delete_photo(idx, "sub")
                        )
                    ]),
                    border=ft.border.all(border_width, border_color),
                    border_radius=6,
                    padding=4,
                    width=100,
                    height=120
                ),
                on_tap=lambda e, photo_data=photo, idx=current_index: self.select_photo(idx, "sub"),
                on_double_tap=lambda e, photo_data=photo: self.show_photo_dialog(photo_data)
            )
            self.photo_grid.controls.append(photo_container)
            current_index += 1
        
        # 同梱物写真を表示
        for i, photo in enumerate(self.bundle_photos):
            is_selected = (current_index == self.selected_photo_index)
            thumbnail = self.create_thumbnail(photo['frame'])
            
            # 選択状態に応じてボーダー色を変更
            border_color = ft.colors.ORANGE_700 if is_selected else ft.colors.ORANGE
            border_width = 3 if is_selected else 1
            
            photo_container = ft.GestureDetector(
                content=ft.Container(
                    content=ft.Stack([
                        # 写真とラベル
                        ft.Column([
                            ft.Container(
                                content=thumbnail,
                                width=80,
                                height=80,
                                border_radius=4,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"同梱物写真{i+1}", 
                                    size=10, 
                                    text_align=ft.TextAlign.CENTER, 
                                    color=ft.colors.ORANGE, 
                                    weight=ft.FontWeight.BOLD
                                ),
                                width=80,
                                height=20,
                                alignment=ft.alignment.center,
                                bgcolor=ft.colors.WHITE,
                                border_radius=2
                            )
                        ], spacing=2),
                        # 削除ボタン（右上の×）
                        ft.Container(
                            content=ft.Text(
                                "×",
                                size=16,
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            alignment=ft.alignment.top_right,
                            width=24,
                            height=24,
                            bgcolor=ft.colors.RED_600 if is_selected else ft.colors.RED,
                            border_radius=12,
                            on_click=lambda e, idx=i: self.delete_photo(idx, "bundle")
                        )
                    ]),
                    border=ft.border.all(border_width, border_color),
                    border_radius=6,
                    padding=4,
                    width=100,
                    height=120
                ),
                on_tap=lambda e, photo_data=photo, idx=current_index: self.select_photo(idx, "bundle"),
                on_double_tap=lambda e, photo_data=photo: self.show_photo_dialog(photo_data)
            )
            self.photo_grid.controls.append(photo_container)
            current_index += 1
        
        self.photo_grid.update()
        
        # 撮影枚数表示を更新
        self.photo_count_text.value = f"撮影済み写真: メイン{len(self.main_photos)}/1枚, サブ{len(self.sub_photos)}/2枚, 同梱物{len(self.bundle_photos)}/3枚"
        self.photo_count_text.update()
    
    def select_photo(self, index, photo_type):
        """写真を選択"""
        self.selected_photo_index = index
        self.selected_photo_type = photo_type
        self.update_photo_grid()
    
    def on_photo_hover(self, e, index, photo_type):
        """写真のホバーイベント"""
        # ホバー時の処理（必要に応じて実装）
        pass
    
    def delete_photo(self, index, photo_type):
        """写真を削除"""
        if photo_type == "main":
            if 0 <= index < len(self.main_photos):
                self.main_photos.pop(index)
                # メイン写真が削除された場合、サブ写真1をメイン写真に昇格
                if len(self.main_photos) == 0 and len(self.sub_photos) > 0:
                    promoted_photo = self.sub_photos.pop(0)
                    self.main_photos.append(promoted_photo)
        elif photo_type == "sub":
            if 0 <= index < len(self.sub_photos):
                self.sub_photos.pop(index)
        elif photo_type == "bundle":
            if 0 <= index < len(self.bundle_photos):
                self.bundle_photos.pop(index)
        
        self.update_photo_grid()
    
    
    def show_photo_dialog(self, photo_data):
        """写真をダイアログで大きく表示"""
        if photo_data and 'frame' in photo_data:
            # カメラの比率（4:3）に合わせてサムネイルを作成
            large_thumbnail = self.create_large_thumbnail(photo_data['frame'], width=600, height=450)
            
            photo_type = "同梱物写真" if photo_data.get('is_bundle', False) else "メイン写真"
            timestamp = photo_data.get('timestamp', '')
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"{photo_type} - {timestamp}"),
                content=ft.Container(
                    content=large_thumbnail,
                    width=600,
                    height=450,
                    border_radius=8,
                    alignment=ft.alignment.center
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
    
    def create_thumbnail(self, frame):
        """フレームからサムネイルを作成（1:1正方形、左右トリミング）"""
        # 正方形のサムネイルサイズ
        target_size = 80
        
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
        small_frame = cv2.resize(cropped_frame, (target_size, target_size))
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
    
    def create_large_thumbnail(self, frame, width=600, height=450):
        """フレームから大きなサムネイルを作成（ダイアログ用）"""
        # フレームを指定サイズにリサイズ（4:3の比率を維持）
        large_frame = cv2.resize(frame, (width, height))
        rgb_frame = cv2.cvtColor(large_frame, cv2.COLOR_BGR2RGB)
        
        # PIL Imageに変換
        pil_image = Image.fromarray(rgb_frame)
        
        # 解像度を下げる（JPEGの品質を下げる）
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG', quality=80, optimize=True)
        img_byte_arr = img_byte_arr.getvalue()
        
        # Base64エンコード
        img_base64 = base64.b64encode(img_byte_arr).decode()
        
        return ft.Image(
            src_base64=img_base64,
            width=width,
            height=height,
            fit=ft.ImageFit.COVER,
            border_radius=8
        )
    
    def proceed_to_form(self, e):
        """フォーム入力画面に進む"""
        # 登録時の枚数制限チェック
        if len(self.main_photos) > 1:
            self.show_error("メイン写真は最大1枚まで登録できます。余分な写真を削除してください。")
            return
        
        if len(self.sub_photos) > 2:
            self.show_error("サブ写真は最大2枚まで登録できます。余分な写真を削除してください。")
            return
        
        if len(self.bundle_photos) > 3:
            self.show_error("同梱物写真は最大3枚まで登録できます。余分な写真を削除してください。")
            return
        
        # 撮影データを保存（撮影なしでも進める）
        photo_data = {
            'main_photos': self.main_photos,
            'sub_photos': self.sub_photos,
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
            
            # エラーダイアログを表示
            self.current_dialog = ft.AlertDialog(
                title=ft.Text("エラー", color=ft.colors.RED),
                content=ft.Text(message),
                actions=[
                    ft.TextButton("OK", on_click=lambda e: self.close_dialog())
                ],
                modal=True,
                open=True
            )
            self.page.dialog = self.current_dialog
            self.page.update()
    
    def show_success(self, message):
        """成功メッセージを表示"""
        if self.page:
            # 既存のダイアログをクリア
            if hasattr(self, 'current_dialog') and self.current_dialog:
                self.close_dialog()
            
            # 成功ダイアログを表示
            self.current_dialog = ft.AlertDialog(
                title=ft.Text("成功", color=ft.colors.GREEN),
                content=ft.Text(message),
                actions=[
                    ft.TextButton("OK", on_click=lambda e: self.close_dialog())
                ],
                modal=True,
                open=True
            )
            self.page.dialog = self.current_dialog
            self.page.update()
    
    def close_dialog(self):
        """ダイアログを閉じる"""
        if self.page and hasattr(self, 'current_dialog') and self.current_dialog:
            self.current_dialog.open = False
            self.current_dialog = None
            self.page.dialog = None
            self.page.update()
