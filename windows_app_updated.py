#!/usr/bin/env python3
"""
拾得物管理システム - Windowsアプリケーション版（更新版）
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QMessageBox, QFrame,
    QGridLayout, QScrollArea, QSizePolicy, QFileDialog, QListWidget,
    QListWidgetItem, QLineEdit, QFormLayout, QGroupBox, QComboBox,
    QDateEdit, QTimeEdit, QSpinBox, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent, QLibraryInfo, QCoreApplication, QDate, QTime
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QImage
import sqlite3  
from datetime import datetime
import json
import time
import cv2


def ensure_qt_platform_plugin() -> bool:
    """Qtのplatformsディレクトリを自動検出し、環境変数に設定する。

    Windows上で "Could not find the Qt platform plugin 'windows'" を防ぐため。
    """
    try:
        candidates = []

        # QLibraryInfoからの取得
        try:
            plugin_root = QLibraryInfo.location(QLibraryInfo.PluginsPath)
            if plugin_root:
                candidates.append(Path(plugin_root) / 'platforms')
        except Exception:
            pass

        # site-packagesの典型パス
        base = Path(sys.prefix) / 'Lib' / 'site-packages' / 'PyQt5'
        candidates.extend([
            base / 'Qt' / 'plugins' / 'platforms',
            base / 'Qt5' / 'plugins' / 'platforms',
        ])

        # venv外のベース（念のため）
        base2 = Path(sys.base_prefix) / 'Lib' / 'site-packages' / 'PyQt5'
        candidates.extend([
            base2 / 'Qt' / 'plugins' / 'platforms',
            base2 / 'Qt5' / 'plugins' / 'platforms',
        ])

        for path in candidates:
            try:
                if path.exists() and (path / 'qwindows.dll').exists():
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(path)
                    # ライブラリパスにも追加
                    try:
                        QCoreApplication.addLibraryPath(str(path.parent))
                        QCoreApplication.addLibraryPath(str(path))
                    except Exception:
                        pass
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# インポート
from register_form import RegisterForm
from login_dialog import LoginDialog
from user_widget import UserWidget
from today_items_widget import TodayItemsWidget

# カメラウィジェット定義
class CameraCaptureWidget(QWidget):
    photosCaptured = pyqtSignal(list)
    bundlePhotosCaptured = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, save_dir: Path, parent=None):
        super().__init__(parent)
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.is_bundle_mode = False
        self.captured_count = 0
        self.captured_paths = []
        self.captured_bundle_paths = []
        self.cap = None

        layout = QVBoxLayout(); self.setLayout(layout)

        title = QLabel("ステップ1: カメラで撮影（Enterで撮影、2回目のEnterで入力へ）")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        self.video_label = QLabel("カメラ起動中...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(360)
        self.video_label.setStyleSheet("QLabel { background:#000; color:#fff; border-radius:8px; }")
        layout.addWidget(self.video_label)

        controls = QHBoxLayout()
        self.toggle_btn = QPushButton("同梱物モード: OFF")
        self.capture_btn = QPushButton("撮影 (Enter)")
        self.no_image_btn = QPushButton("画像なし")
        self.next_btn = QPushButton("入力に進む (Enter) ※撮影済み時")
        for b in (self.toggle_btn, self.capture_btn, self.no_image_btn, self.next_btn):
            b.setStyleSheet("QPushButton { background:#2ecc71; color:white; padding:8px 14px; border:none; border-radius:8px; font-weight:bold; }")
        controls.addWidget(self.toggle_btn)
        controls.addWidget(self.capture_btn)
        controls.addWidget(self.no_image_btn)
        controls.addWidget(self.next_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.capture_btn.setDefault(True)

        self.toggle_btn.clicked.connect(self.toggle_bundle_mode)
        self.capture_btn.clicked.connect(self.capture_photo)
        self.no_image_btn.clicked.connect(self.set_no_image)
        self.next_btn.clicked.connect(self.finish_and_emit)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def start_camera(self, index: int = 0):
        try:
            self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.timer.start(30)
        except Exception as e:
            QMessageBox.critical(self, "カメラエラー", f"カメラを起動できません: {e}")

    def stop_camera(self):
        try:
            self.timer.stop()
        except Exception:
            pass
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def update_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(pix)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.captured_count == 0:
                self.capture_photo()
            else:
                self.finish_and_emit()
            return
        return super().keyPressEvent(event)

    def toggle_bundle_mode(self):
        self.is_bundle_mode = not self.is_bundle_mode
        self.toggle_btn.setText(f"同梱物モード: {'ON' if self.is_bundle_mode else 'OFF'}")

    def capture_photo(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        ts = time.strftime('%Y%m%d-%H%M%S')
        fname = f"{'bundle_' if self.is_bundle_mode else ''}capture_{ts}_{self.captured_count+1}.jpg"
        out_path = str(self.save_dir / fname)
        try:
            cv2.imwrite(out_path, frame)
        except Exception as e:
            QMessageBox.critical(self, "保存エラー", f"画像保存に失敗しました: {e}")
            return
        if self.is_bundle_mode:
            self.captured_bundle_paths.append(out_path)
        else:
            self.captured_paths.append(out_path)
        self.captured_count += 1

    def finish_and_emit(self):
        if self.captured_paths:
            self.photosCaptured.emit(self.captured_paths)
        if self.captured_bundle_paths:
            self.bundlePhotosCaptured.emit(self.captured_bundle_paths)
        self.finished.emit()
    
    def set_no_image(self):
        """画像なしを選択した場合の処理"""
        self.captured_count = 1  # 撮影済みとして扱う
        self.captured_paths = ["no_image"]
        if self.is_bundle_mode:
            self.captured_bundle_paths = ["no_image"]

class MainWindow(QMainWindow):
    """メインウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("拾得物管理システム")
        self.setGeometry(100, 100, 1400, 900)
        
        # 現在のユーザー
        self.current_user = {
            'id': None,
            'username': 'ゲスト',
            'email': None,
            'is_guest': True
        }
        
        # データベース初期化
        self.init_database()
        
        # UI初期化
        self.init_ui()
        
    def init_database(self):
        """データベースの初期化"""
        try:
            # SQLiteデータベースのパス
            db_path = project_root / "lostitem.db"
            
            # データベース接続
            self.conn = sqlite3.connect(str(db_path))
            self.cursor = self.conn.cursor()
            
            # テーブルが存在しない場合は作成
            self.create_tables()
            
        except Exception as e:
            error_box = QMessageBox()
            error_box.setWindowTitle("エラー")
            error_box.setText(f"データベース初期化エラー: {str(e)}")
            error_box.setIcon(QMessageBox.Critical)
            error_box.setStyleSheet("""
                QMessageBox {
                    font-size: 18px;
                }
                QMessageBox QLabel {
                    font-size: 18px;
                    padding: 15px;
                }
                QMessageBox QPushButton {
                    font-size: 16px;
                    padding: 10px 20px;
                    min-width: 100px;
                }
            """)
            error_box.exec_()
    
    def create_tables(self):
        """必要なテーブルを作成"""
        # ユーザーテーブル
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 拾得物テーブル
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lost_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                main_id TEXT NOT NULL,
                current_year INTEGER NOT NULL,
                choice_finder TEXT NOT NULL,
                notify TEXT,
                get_item DATE,
                get_item_hour INTEGER,
                get_item_minute INTEGER,
                recep_item DATE,
                recep_item_hour INTEGER,
                recep_item_minute INTEGER,
                recep_manager TEXT,
                find_area TEXT,
                find_area_police TEXT,
                own_waiver TEXT,
                finder_name TEXT,
                own_name_note TEXT,
                finder_age INTEGER,
                finder_sex TEXT,
                finder_post TEXT,
                finder_address TEXT,
                finder_tel1 TEXT,
                finder_tel2 TEXT,
                item_class_L TEXT,
                item_class_M TEXT,
                item_class_S TEXT,
                item_value INTEGER,
                item_feature TEXT,
                item_color TEXT,
                item_storage TEXT,
                item_storage_place TEXT,
                item_maker TEXT,
                item_expiration DATE,
                item_num INTEGER,
                item_unit TEXT,
                item_plice TEXT,
                item_money INTEGER,
                item_remarks TEXT,
                item_image TEXT,
                finder_affiliation TEXT,
                item_situation TEXT DEFAULT '保管中',
                refund_situation TEXT DEFAULT '未',
                card_campany TEXT,
                card_tel TEXT,
                card_name TEXT,
                card_person TEXT,
                thirdparty_waiver TEXT,
                thirdparty_name_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()

        # 設定テーブル（地域名・施設名など）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        self.conn.commit()

    def get_setting(self, key: str, default_value: str = "") -> str:
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = self.cursor.fetchone()
            if row and row[0] is not None:
                return row[0]
            return default_value
        except Exception:
            return default_value

    def set_setting(self, key: str, value: str) -> None:
        self.cursor.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()
    
    def init_ui(self):
        """UIの初期化"""
        # メインウジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # メインレイアウト
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # サイドバー（ナビゲーション）
        self.create_sidebar(main_layout)
        
        # メインコンテンツエリア
        self.create_main_content(main_layout)
        
        # スタイル設定
        self.apply_styles()
    
    def create_sidebar(self, main_layout):
        """サイドバーの作成"""
        sidebar = QFrame()
        sidebar.setMaximumWidth(280)
        sidebar.setMinimumWidth(280)
        sidebar.setFrameStyle(QFrame.Box)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: none;
                border-right: 1px solid #34495e;
            }
        """)
        
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)
        
        # タイトル
        title_label = QLabel("拾得物管理システム")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                border-bottom: 1px solid #34495e;
            }
        """)
        sidebar_layout.addWidget(title_label)
        
        # ナビゲーションボタン
        nav_buttons = [
            ("🏠 ホーム", self.show_home),
            ("📝 拾得物登録", self.show_register),
            ("📋 拾得物一覧", self.show_items),
            ("📊 統計", self.show_statistics),
            ("📦 遺失物管理", self.show_lost_management),
            ("💰 還付管理", self.show_refund_management),
            ("👮 警察届け出処理", self.show_police_report),
            ("🤖 AI画像分類テスト", self.show_ai_test),
            ("❓ ヘルプ", self.show_help),
            ("⚙️ 設定", self.show_settings),
        ]
        
        for text, callback in nav_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    padding: 15px;
                    text-align: left;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(callback)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # ユーザー管理ウィジェット
        self.user_widget = UserWidget(self)
        self.user_widget.set_main_window(self)  # メインウィンドウの参照を設定
        self.user_widget.set_user(self.current_user)
        self.user_widget.user_changed.connect(self.on_user_changed)
        self.user_widget.logout_requested.connect(self.on_logout)
        sidebar_layout.addWidget(self.user_widget)
        
        main_layout.addWidget(sidebar)
    
    def create_main_content(self, main_layout):
        """メインコンテンツエリアの作成"""
        # スタックウィジェット（ページ切り替え用）
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #ecf0f1;
            }
        """)
        
        # 各ページを作成
        self.create_home_page()
        self.create_photo_page()
        self.create_register_page()
        self.create_items_page()
        self.create_search_page()
        self.create_statistics_page()
        self.create_lost_management_page()
        self.create_refund_management_page()
        self.create_police_report_page()
        self.create_ai_test_page()
        self.create_help_page()
        self.create_settings_page()
        
        main_layout.addWidget(self.stacked_widget)
    
    def create_home_page(self):
        """ホームページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        # タイトル
        title = QLabel("拾得物管理システム")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        layout.addWidget(title)

        # 地域・施設名の表示
        self.home_place_label = QLabel("")
        self.home_place_label.setAlignment(Qt.AlignCenter)
        self.home_place_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #34495e;
                padding-bottom: 6px;
            }
        """)
        layout.addWidget(self.home_place_label)
        self.update_home_place_label()
        
        # メインアクションボタン（均等配置・色分け）
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
        """)
        actions_layout = QHBoxLayout()
        actions_frame.setLayout(actions_layout)
        
        # アクションボタン（均等配置・色分け）
        action_buttons = [
            ("📷 新しい拾得物を登録", self.show_register, "#1abc9c"),     # ティール
            ("🔍 拾得物を検索", self.show_search, "#e67e22"),           # オレンジ
            ("📊 統計を確認", self.show_statistics, "#9b59b6"),        # パープル
        ]
        
        for text, callback, color in action_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 30px 20px;
                    border-radius: 12px;
                    font-size: 18px;
                    font-weight: bold;
                    margin: 10px;
                    min-height: 120px;
                    font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                }}
            """)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        
        layout.addWidget(actions_frame)
        
        # 本日の拾得物一覧
        today_frame = QFrame()
        today_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
        """)
        today_layout = QVBoxLayout()
        today_frame.setLayout(today_layout)
        
        # 本日の拾得物ウィジェット
        self.today_items_widget = TodayItemsWidget()
        self.today_items_widget.item_clicked.connect(self.on_today_item_clicked)
        today_layout.addWidget(self.today_items_widget)
        
        layout.addWidget(today_frame)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
        
        # 初期データ読み込み
        self.load_today_items()
    
    def load_today_items(self):
        """本日の拾得物を読み込み"""
        try:
            from datetime import date
            today = date.today()
            
            # 本日の拾得物を取得
            self.cursor.execute("""
                SELECT id, main_id, item_class_L, item_class_M, item_class_S,
                       find_area, get_item, item_image, item_feature
                FROM lost_items 
                WHERE DATE(get_item) = ?
                ORDER BY get_item DESC
            """, (today.isoformat(),))
            
            items = []
            for row in self.cursor.fetchall():
                item = {
                    'id': row[0],
                    'main_id': row[1],
                    'item_class_L': row[2],
                    'item_class_M': row[3],
                    'item_class_S': row[4],
                    'find_area': row[5],
                    'get_item': row[6],
                    'item_image': row[7],
                    'item_feature': row[8]
                }
                items.append(item)
            
            self.today_items_widget.update_items(items)
            
        except Exception as e:
            print(f"本日の拾得物読み込みエラー: {e}")
    
    def create_stat_card(self, label, value, color):
        """統計カードの作成"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }}
        """)
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
            }
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)
        
        return card
    
    def create_photo_page(self):
        """写真撮影ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("写真撮影")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # カメラ機能は後で実装
        camera_label = QLabel("カメラ機能は後で実装予定")
        camera_label.setAlignment(Qt.AlignCenter)
        camera_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(camera_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_register_page(self):
        """拾得物登録ページの作成"""
        # 写真パス保存用
        self.register_photo_paths = []
        self.register_bundle_photo_paths = []

        # 登録用スタック（カメラ→フォーム）
        self.register_stack = QStackedWidget()

        # 1) カメラウィジェット
        self.camera_widget = CameraCaptureWidget(save_dir=project_root / 'images')
        self.camera_widget.photosCaptured.connect(self.on_photos_captured)
        self.camera_widget.bundlePhotosCaptured.connect(self.on_bundle_photos_captured)
        self.camera_widget.finished.connect(self.on_camera_finished)
        self.register_stack.addWidget(self.camera_widget)

        # 2) 入力フォーム（単一スクロール）
        form_container = QWidget()
        form_layout = QVBoxLayout(); form_container.setLayout(form_layout)
        
        # 大きなタイトル
        title = QLabel("拾得物登録フォーム")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                padding: 30px;
                margin-bottom: 20px;
                background-color: #ecf0f1;
                border-radius: 15px;
            }
        """)
        form_layout.addWidget(title)
        
        # 注意事項
        note_label = QLabel("※ 第三者拾得の場合、「拾得者氏名」と「住所」は必須項目です")
        note_label.setAlignment(Qt.AlignCenter)
        note_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #e74c3c;
                font-weight: bold;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #fdf2f2;
                border: 2px solid #e74c3c;
                border-radius: 10px;
            }
        """)
        form_layout.addWidget(note_label)
        
        # 単一のスクロール可能なフォーム
        self.register_form = self.create_single_scroll_form()
        self.register_scroll = QScrollArea()
        self.register_scroll.setWidget(self.register_form)
        self.register_scroll.setWidgetResizable(True)
        self.register_scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #ecf0f1; 
            }
            QScrollBar:vertical {
                background-color: #bdc3c7;
                width: 16px;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #7f8c8d;
                border-radius: 8px;
                min-height: 20px;
            }
        """)
        form_layout.addWidget(self.register_scroll)

        # 自動フォーカススクロール
        self.register_form.installEventFilter(self)
        if QApplication.instance() is not None:
            QApplication.instance().installEventFilter(self)

        self.register_stack.addWidget(form_container)

        # 画面に追加（初期はカメラフェーズのみ表示）
        page = QWidget(); layout = QVBoxLayout(); page.setLayout(layout)
        layout.addWidget(self.register_stack)
        self.stacked_widget.addWidget(page)
    
    def create_single_scroll_form(self):
        """単一スクロール可能なフォームの作成（Google Forms風）"""
        form = QWidget()
        layout = QVBoxLayout()
        form.setLayout(layout)
        
        # フォーム送信シグナルを追加
        form.form_submitted = pyqtSignal(dict)
        
        # 基本情報セクション
        basic_group = self.create_form_section("基本情報", [
            ("拾得者区分", "QRadioButton", ["占有者拾得", "第三者拾得"]),
            ("届出区分", "QComboBox", ["届出あり", "届出なし"]),
            ("拾得日", "QDateEdit", None),
            ("拾得時刻", "QTimeEdit", None),
            ("受付日", "QDateEdit", None),
            ("受付時刻", "QTimeEdit", None),
            ("受付担当者", "QLineEdit", None),
            ("拾得場所", "QLineEdit", None),
            ("警察届出", "QComboBox", ["あり", "なし"])
        ])
        layout.addWidget(basic_group)
        
        # 拾得者情報セクション
        finder_group = self.create_form_section("拾得者情報", [
            ("拾得者氏名 *", "QLineEdit", None),
            ("年齢", "QSpinBox", None),
            ("性別", "QComboBox", ["男性", "女性", "その他"]),
            ("郵便番号", "QLineEdit", None),
            ("住所 *", "QLineEdit", None),
            ("電話番号1", "QLineEdit", None),
            ("電話番号2", "QLineEdit", None)
        ])
        layout.addWidget(finder_group)
        
        # 拾得物品情報セクション
        item_group = self.create_form_section("拾得物品情報", [
            ("物品名", "QLineEdit", None),
            ("物品詳細", "QTextEdit", None),
            ("色", "QLineEdit", None),
            ("ブランド", "QLineEdit", None),
            ("サイズ", "QLineEdit", None),
            ("数量", "QSpinBox", None),
            ("価格", "QSpinBox", None),
            ("備考", "QTextEdit", None)
        ])
        layout.addWidget(item_group)
        
        # 管理情報セクション
        management_group = self.create_form_section("管理情報", [
            ("保管場所", "QLineEdit", None),
            ("保管担当者", "QLineEdit", None),
            ("返還予定日", "QDateEdit", None),
            ("処分予定日", "QDateEdit", None),
            ("管理備考", "QTextEdit", None)
        ])
        layout.addWidget(management_group)
        
        # 送信ボタン
        submit_btn = QPushButton("登録完了")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 20px 40px;
                border: none;
                border-radius: 15px;
                margin: 30px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        submit_btn.clicked.connect(self.on_form_submit)
        layout.addWidget(submit_btn)
        
        # スペーサー
        layout.addStretch()
        
        return form
    
    def create_form_section(self, title, fields):
        """フォームセクションの作成"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 15px;
                margin-top: 20px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px 0 15px;
                background-color: white;
            }
        """)
        
        layout = QFormLayout()
        group.setLayout(layout)
        layout.setSpacing(25)  # フィールド間の間隔
        layout.setLabelAlignment(Qt.AlignLeft)
        
        for label_text, widget_type, options in fields:
            label = QLabel(label_text)
            label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #34495e;
                    padding: 10px 0;
                    min-width: 200px;
                }
            """)
            
            if widget_type == "QLineEdit":
                widget = QLineEdit()
                widget.setStyleSheet("""
                    QLineEdit {
                        font-size: 16px;
                        padding: 15px;
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        background-color: white;
                        min-height: 25px;
                    }
                    QLineEdit:focus {
                        border-color: #3498db;
                        background-color: #f8f9fa;
                    }
                """)
                layout.addRow(label, widget)
                
                # ウィジェットを保存して後でデータ収集できるようにする
                if not hasattr(self, 'form_widgets'):
                    self.form_widgets = {}
                self.form_widgets[label_text] = widget
                
            elif widget_type == "QComboBox":
                widget = QComboBox()
                widget.addItems(options)
                widget.setStyleSheet("""
                    QComboBox {
                        font-size: 16px;
                        padding: 15px;
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        background-color: white;
                        min-height: 25px;
                    }
                    QComboBox:focus {
                        border-color: #3498db;
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 30px;
                    }
                    QComboBox::down-arrow {
                        image: none;
                        border-left: 5px solid transparent;
                        border-right: 5px solid transparent;
                        border-top: 5px solid #7f8c8d;
                        margin-right: 10px;
                    }
                """)
                layout.addRow(label, widget)
                
                # ウィジェットを保存して後でデータ収集できるようにする
                if not hasattr(self, 'form_widgets'):
                    self.form_widgets = {}
                self.form_widgets[label_text] = widget
                
            elif widget_type == "QRadioButton":
                # ラジオボタンの説明を追加
                explanation_label = QLabel()
                if label_text == "拾得者区分":
                    explanation_label.setText("占有者拾得：店舗従業者による拾得\n第三者拾得：お客様による拾得")
                explanation_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #7f8c8d;
                        font-style: italic;
                        padding: 5px 0;
                    }
                """)
                explanation_label.setWordWrap(True)
                
                # ラジオボタンコンテナ
                radio_container = QWidget()
                radio_layout = QVBoxLayout()
                radio_container.setLayout(radio_layout)
                
                # 説明を追加
                radio_layout.addWidget(explanation_label)
                
                # ラジオボタンを作成
                radio_group = QButtonGroup()
                radio_group.setExclusive(True)
                
                radio_buttons = []
                for option in options:
                    radio_button = QRadioButton(option)
                    radio_button.setStyleSheet("""
                        QRadioButton {
                            font-size: 16px;
                            padding: 10px;
                            margin: 5px 0;
                        }
                        QRadioButton::indicator {
                            width: 20px;
                            height: 20px;
                        }
                    """)
                    radio_group.addButton(radio_button)
                    radio_buttons.append(radio_button)
                    radio_layout.addWidget(radio_button)
                
                # デフォルトで最初のボタンを選択
                if radio_buttons:
                    radio_buttons[0].setChecked(True)
                
                layout.addRow(label, radio_container)
                
                # ウィジェットを保存して後でデータ収集できるようにする
                if not hasattr(self, 'form_widgets'):
                    self.form_widgets = {}
                self.form_widgets[label_text] = radio_group
                
            elif widget_type == "QDateEdit":
                widget = QDateEdit()
                widget.setDate(QDate.currentDate())
                widget.setStyleSheet("""
                    QDateEdit {
                        font-size: 16px;
                        padding: 15px;
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        background-color: white;
                        min-height: 25px;
                    }
                    QDateEdit:focus {
                        border-color: #3498db;
                    }
                """)
                layout.addRow(label, widget)
                
                # ウィジェットを保存して後でデータ収集できるようにする
                if not hasattr(self, 'form_widgets'):
                    self.form_widgets = {}
                self.form_widgets[label_text] = widget
                
            elif widget_type == "QTimeEdit":
                widget = QTimeEdit()
                widget.setTime(QTime.currentTime())
                widget.setStyleSheet("""
                    QTimeEdit {
                        font-size: 16px;
                        padding: 15px;
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        background-color: white;
                        min-height: 25px;
                    }
                    QTimeEdit:focus {
                        border-color: #3498db;
                    }
                """)
                layout.addRow(label, widget)
                
                # ウィジェットを保存して後でデータ収集できるようにする
                if not hasattr(self, 'form_widgets'):
                    self.form_widgets = {}
                self.form_widgets[label_text] = widget
                
            elif widget_type == "QSpinBox":
                widget = QSpinBox()
                widget.setRange(0, 999999)
                widget.setStyleSheet("""
                    QSpinBox {
                        font-size: 16px;
                        padding: 15px;
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        background-color: white;
                        min-height: 25px;
                    }
                    QSpinBox:focus {
                        border-color: #3498db;
                    }
                """)
                layout.addRow(label, widget)
                
                # ウィジェットを保存して後でデータ収集できるようにする
                if not hasattr(self, 'form_widgets'):
                    self.form_widgets = {}
                self.form_widgets[label_text] = widget
                
            elif widget_type == "QTextEdit":
                widget = QTextEdit()
                widget.setMaximumHeight(100)
                widget.setStyleSheet("""
                    QTextEdit {
                        font-size: 16px;
                        padding: 15px;
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        background-color: white;
                    }
                    QTextEdit:focus {
                        border-color: #3498db;
                        background-color: #f8f9fa;
                    }
                """)
                layout.addRow(label, widget)
                
                # ウィジェットを保存して後でデータ収集できるようにする
                if not hasattr(self, 'form_widgets'):
                    self.form_widgets = {}
                self.form_widgets[label_text] = widget
        
        return group
    
    def collect_form_data(self):
        """フォームデータの収集"""
        data = {}
        if hasattr(self, 'form_widgets'):
            for label, widget in self.form_widgets.items():
                if isinstance(widget, QLineEdit):
                    data[label] = widget.text()
                elif isinstance(widget, QComboBox):
                    data[label] = widget.currentText()
                elif isinstance(widget, QDateEdit):
                    data[label] = widget.date().toString("yyyy-MM-dd")
                elif isinstance(widget, QTimeEdit):
                    data[label] = widget.time().toString("HH:mm")
                elif isinstance(widget, QSpinBox):
                    data[label] = widget.value()
                elif isinstance(widget, QTextEdit):
                    data[label] = widget.toPlainText()
                elif isinstance(widget, QButtonGroup):
                    # QButtonGroupの場合は、選択されたボタンのテキストを取得
                    data[label] = widget.checkedButton().text()
        return data
    
    def on_form_submit(self):
        """フォーム送信時の処理"""
        form_data = self.collect_form_data()
        
        # 第三者拾得の場合の必須項目チェック
        if form_data.get("拾得者区分") == "第三者拾得":
            required_fields = ["拾得者氏名", "住所"]
            missing_fields = []
            
            for field in required_fields:
                if not form_data.get(field) or form_data.get(field).strip() == "":
                    missing_fields.append(field)
            
            if missing_fields:
                QMessageBox.warning(
                    self,
                    "必須項目が未入力",
                    f"第三者拾得の場合、以下の項目は必須です：\n{', '.join(missing_fields)}"
                )
                return
        
        self.handle_form_submission(form_data)
    
    def create_items_page(self):
        """拾得物一覧ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("拾得物一覧")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 一覧表示は後で実装
        list_label = QLabel("拾得物一覧は後で実装予定")
        list_label.setAlignment(Qt.AlignCenter)
        list_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(list_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_search_page(self):
        """検索ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("検索")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 検索機能は後で実装
        search_label = QLabel("検索機能は後で実装予定")
        search_label.setAlignment(Qt.AlignCenter)
        search_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(search_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_statistics_page(self):
        """統計ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("統計")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 統計機能は後で実装
        stats_label = QLabel("統計機能は後で実装予定")
        stats_label.setAlignment(Qt.AlignCenter)
        stats_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(stats_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_lost_management_page(self):
        """遺失物管理ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("遺失物管理")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 遺失物管理機能は後で実装
        lost_label = QLabel("遺失物管理機能は後で実装予定")
        lost_label.setAlignment(Qt.AlignCenter)
        lost_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(lost_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_refund_management_page(self):
        """還付管理ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("還付管理")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 還付管理機能は後で実装
        refund_label = QLabel("還付管理機能は後で実装予定")
        refund_label.setAlignment(Qt.AlignCenter)
        refund_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(refund_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_police_report_page(self):
        """警察届け出処理ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("警察届け出処理")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 警察届け出処理機能は後で実装
        police_label = QLabel("警察届け出処理機能は後で実装予定")
        police_label.setAlignment(Qt.AlignCenter)
        police_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(police_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_ai_test_page(self):
        """AI画像分類テストページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("AI画像分類テスト")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # AI画像分類テスト機能は後で実装
        ai_label = QLabel("AI画像分類テスト機能は後で実装予定")
        ai_label.setAlignment(Qt.AlignCenter)
        ai_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(ai_label)
        
        self.stacked_widget.addWidget(page)
    
    def create_settings_page(self):
        """設定ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        title = QLabel("設定（管理者）")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)

        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background:white; border-radius:10px; padding:20px; margin:20px; }")
        form_layout = QFormLayout()
        form_frame.setLayout(form_layout)

        self.input_region = QLineEdit(self.get_setting("region_name", ""))
        self.input_facility = QLineEdit(self.get_setting("facility_name", ""))
        form_layout.addRow("地域名", self.input_region)
        form_layout.addRow("施設名", self.input_facility)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("QPushButton { background:#2980b9; color:white; padding:8px 16px; border:none; border-radius:6px; font-weight:bold; }")
        def on_save():
            self.set_setting("region_name", self.input_region.text().strip())
            self.set_setting("facility_name", self.input_facility.text().strip())
            QMessageBox.information(self, "保存", "設定を保存しました。ホームに反映されます。")
            # ホームの表示更新
            self.update_home_place_label()
        save_btn.clicked.connect(on_save)
        form_layout.addRow("", save_btn)

        layout.addWidget(form_frame)
        self.stacked_widget.addWidget(page)

    def create_help_page(self):
        """ヘルプページ"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        title = QLabel("ヘルプ・説明")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)

        help_frame = QFrame()
        help_frame.setStyleSheet("QFrame { background:white; border-radius:10px; padding:20px; margin:20px; }")
        v = QVBoxLayout(); help_frame.setLayout(v)
        text = QLabel(
            """
            ・ホームのクイックアクションから、登録・検索・統計へすばやく移動できます。<br/>
            ・拾得物登録は、まず写真を撮影・選択し、その後で詳細を入力します。<br/>
            ・スクロールは自動でフォーカス位置へ追従します。<br/>
            ・設定（管理者）から地域名・施設名を登録できます。
            """
        )
        text.setWordWrap(True)
        v.addWidget(text)
        layout.addWidget(help_frame)
        self.stacked_widget.addWidget(page)
    
    def apply_styles(self):
        """アプリケーション全体のスタイル適用"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                font-size: 12px;
            }
            QLabel {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QPushButton {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QLineEdit {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QTextEdit {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QComboBox {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QSpinBox {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QDateEdit {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QTimeEdit {
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QMessageBox {
                font-size: 18px;
            }
            QMessageBox QLabel {
                font-size: 18px;
                padding: 15px;
            }
            QMessageBox QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                min-width: 100px;
            }
            QScrollArea {
                border: none;
                background-color: #ecf0f1;
            }
        """)
    
    # ナビゲーション関数
    def show_home(self):
        self.stacked_widget.setCurrentIndex(0)
        self.load_today_items()  # ホーム画面に戻った時に最新データを読み込み
    
    def show_photo(self):
        self.stacked_widget.setCurrentIndex(1)
    
    def show_register(self):
        self.stacked_widget.setCurrentIndex(2)
        # 登録スタックをカメラにしてカメラ開始
        try:
            if hasattr(self, 'register_stack'):
                self.register_stack.setCurrentIndex(0)
            if hasattr(self, 'camera_widget'):
                self.camera_widget.start_camera()
        except Exception:
            pass
    
    def on_photos_captured(self, photo_paths):
        """通常写真が撮影された時の処理"""
        self.register_photo_paths = photo_paths
        print(f"通常写真が撮影されました: {photo_paths}")
    
    def on_bundle_photos_captured(self, bundle_photo_paths):
        """同梱物写真が撮影された時の処理"""
        self.register_bundle_photo_paths = bundle_photo_paths
        print(f"同梱物写真が撮影されました: {bundle_photo_paths}")
    
    def on_camera_finished(self):
        """カメラフェーズが完了した時の処理"""
        # 入力フォームに切り替え
        if hasattr(self, 'register_stack'):
            self.register_stack.setCurrentIndex(1)
        print("カメラフェーズが完了し、入力フォームに切り替わりました")
    
    def show_items(self):
        self.stacked_widget.setCurrentIndex(3)
    
    def show_search(self):
        self.stacked_widget.setCurrentIndex(4)
    
    def show_statistics(self):
        self.stacked_widget.setCurrentIndex(5)
    
    def show_lost_management(self):
        self.stacked_widget.setCurrentIndex(6)
    
    def show_refund_management(self):
        self.stacked_widget.setCurrentIndex(7)
    
    def show_police_report(self):
        self.stacked_widget.setCurrentIndex(8)
    
    def show_ai_test(self):
        self.stacked_widget.setCurrentIndex(9)
    
    def show_settings(self):
        self.stacked_widget.setCurrentIndex(11)
    
    def show_help(self):
        # ページ作成順: home(0) photo(1) register(2) items(3) search(4) stats(5) lost(6) refund(7) police(8) ai(9) help(10) settings(11)
        self.stacked_widget.setCurrentIndex(10)

    def update_home_place_label(self):
        region_name = self.get_setting("region_name", "未設定")
        facility_name = self.get_setting("facility_name", "未設定")
        if hasattr(self, 'home_place_label') and self.home_place_label is not None:
            self.home_place_label.setText(f"地域・施設: {region_name} / {facility_name}")
    
    def on_user_changed(self, user_data):
        """ユーザー変更時の処理"""
        self.current_user = user_data
        print(f"ユーザーが変更されました: {user_data['username']}")
    
    def on_logout(self):
        """ログアウト時の処理"""
        self.current_user = {
            'id': None,
            'username': 'ゲスト',
            'email': None,
            'is_guest': True
        }
        print("ログアウトしました")
    
    def on_today_item_clicked(self, item_id):
        """本日の拾得物クリック時の処理"""
        print(f"本日の拾得物ID {item_id} がクリックされました")
        # 詳細画面に遷移する処理をここに実装
    
    def handle_form_submission(self, form_data):
        """フォーム送信の処理"""
        try:
            # データベースに保存
            # 写真情報を統合
            form_data = dict(form_data)
            form_data["photo_paths"] = list(self.register_photo_paths)
            form_data["bundle_photo_paths"] = list(self.register_bundle_photo_paths)
            self.save_lost_item(form_data)
            
            msg_box = QMessageBox()
            msg_box.setWindowTitle("成功")
            msg_box.setText("拾得物の登録が完了しました")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStyleSheet("""
                QMessageBox {
                    font-size: 18px;
                }
                QMessageBox QLabel {
                    font-size: 18px;
                    padding: 15px;
                }
                QMessageBox QPushButton {
                    font-size: 16px;
                    padding: 10px 20px;
                    min-width: 100px;
                }
            """)
            msg_box.exec_()
            
            # ホーム画面に戻る
            self.show_home()
            # 次回のために写真バッファをクリア
            self.register_photo_paths.clear()
            self.register_bundle_photo_paths.clear()
            
        except Exception as e:
            error_box = QMessageBox()
            error_box.setWindowTitle("エラー")
            error_box.setText(f"登録中にエラーが発生しました: {str(e)}")
            error_box.setIcon(QMessageBox.Critical)
            error_box.setStyleSheet("""
                QMessageBox {
                    font-size: 18px;
                }
                QMessageBox QLabel {
                    font-size: 18px;
                    padding: 15px;
                }
                QMessageBox QPushButton {
                    font-size: 16px;
                    padding: 10px 20px;
                    min-width: 100px;
                }
            """)
            error_box.exec_()
    
    def save_lost_item(self, form_data):
        """拾得物をデータベースに保存"""
        # メインIDの生成
        current_year = datetime.now().year % 100
        main_id = self.generate_main_id(form_data["finder_type"], current_year)
        
        # SQL文の作成
        sql = '''
            INSERT INTO lost_items (
                main_id, current_year, choice_finder, notify,
                get_item, get_item_hour, get_item_minute,
                recep_item, recep_item_hour, recep_item_minute,
                recep_manager, find_area, find_area_police,
                finder_name, finder_age, finder_sex, finder_post,
                finder_address, finder_tel1, finder_tel2,
                finder_affiliation, item_class_L, item_class_M,
                item_class_S, item_feature, item_color,
                item_storage, item_storage_place, item_maker,
                item_expiration, item_num, item_unit,
                item_value, item_money, item_remarks,
                item_image, item_situation, refund_situation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # データの準備
        data = (
            main_id, current_year, form_data["finder_type"], form_data["notify"],
            form_data["get_date"], form_data["get_time"].hour, form_data["get_time"].minute,
            form_data["recep_date"], form_data["recep_time"].hour, form_data["recep_time"].minute,
            form_data["recep_manager"], form_data["find_area"], form_data["find_area_police"],
            form_data["finder_name"], form_data["finder_age"], form_data["finder_sex"], form_data["finder_post"],
            form_data["finder_address"], form_data["finder_tel1"], form_data["finder_tel2"],
            form_data["finder_affiliation"], form_data["item_class_L"], form_data["item_class_M"],
            form_data["item_class_S"], form_data["item_feature"], form_data["item_color"],
            form_data["item_storage"], form_data["item_storage_place"], form_data["item_maker"],
            form_data["item_expiration"], form_data["item_num"], form_data["item_unit"],
            form_data["item_value"], form_data["item_money"], form_data["item_remarks"],
            json.dumps({
                "photos": form_data.get("photo_paths", []),
                "bundle_photos": form_data.get("bundle_photo_paths", []),
            }, ensure_ascii=False),
            "保管中", "未"
        )
        
        # データベースに保存
        self.cursor.execute(sql, data)
        self.conn.commit()
    
    def generate_main_id(self, choice_finder, current_year):
        """メインIDの生成"""
        # 既存のレコード数をカウント
        self.cursor.execute(
            "SELECT COUNT(*) FROM lost_items WHERE choice_finder = ? AND current_year = ?",
            (choice_finder, current_year)
        )
        count = self.cursor.fetchone()[0]
        
        # IDの生成
        if choice_finder == "占有者拾得":
            identifier = f"1{current_year:02}{count+1:05}"
        else:
            identifier = f"2{current_year:02}{count+1:05}"
        
        return identifier

    def eventFilter(self, obj, event):
        # 登録フォームのオートスクロール（フォーカス移動のたびに該当フィールドへスクロール）
        if event.type() == QEvent.FocusIn:
            try:
                if hasattr(self, 'register_form') and self.register_form is not None:
                    # obj が登録フォーム内の子ウィジェットならスクロール
                    if isinstance(obj, QWidget) and self.register_form.isAncestorOf(obj):
                        self.register_scroll.ensureWidgetVisible(obj)
            except Exception:
                pass
        if event.type() == QEvent.KeyPress and getattr(event, 'key', lambda: None)() in (Qt.Key_Return, Qt.Key_Enter):
            try:
                if hasattr(self, 'register_form') and self.register_form.isAncestorOf(self.focusWidget()):
                    self.focusNextChild()
                    if self.focusWidget() is not None:
                        self.register_scroll.ensureWidgetVisible(self.focusWidget())
                    return True
            except Exception:
                pass
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event):
        """アプリケーション終了時の処理"""
        if hasattr(self, 'conn'):
            self.conn.close()
        try:
            if hasattr(self, 'camera_widget'):
                self.camera_widget.stop_camera()
        except Exception:
            pass
        event.accept()


def main():
    """メイン関数"""
    # Qtプラットフォームプラグイン対策
    ensure_qt_platform_plugin()

    app = QApplication(sys.argv)
    
    # アプリケーション情報設定
    app.setApplicationName("拾得物管理システム")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LostItem Management")
    
    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()
    
    # アプリケーション実行
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 