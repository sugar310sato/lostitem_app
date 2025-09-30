#!/usr/bin/env python3
"""
拾得物管理システム - Windowsアプリケーション版（簡易版）
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QMessageBox, QFrame,
    QGridLayout, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
import sqlite3
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# YOLO関連のインポートを一時的にコメントアウト
# from apps.register.model_folder.yolo_predict import YOLOPredictor
# from apps.crud.models import User
# from apps.register.models import LostItem
from register_form import RegisterForm

class MainWindow(QMainWindow):
    """メインウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("拾得物管理システム")
        self.setGeometry(100, 100, 1200, 800)
        
        # データベース初期化
        self.init_database()
        
        # UI初期化
        self.init_ui()
        
        # YOLOモデルの初期化を一時的に無効化
        # self.yolo_predictor = None
        # self.init_yolo_model()
        
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
            QMessageBox.critical(self, "エラー", f"データベース初期化エラー: {str(e)}")
    
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
    
    def init_ui(self):
        """UIの初期化"""
        # メインウィジェット
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
        sidebar.setMaximumWidth(250)
        sidebar.setMinimumWidth(250)
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
            ("📷 写真撮影", self.show_photo),
            ("📝 拾得物登録", self.show_register),
            ("📋 拾得物一覧", self.show_items),
            ("🔍 検索", self.show_search),
            ("📊 統計", self.show_statistics),
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
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
            }
        """)
        layout.addWidget(title)
        
        # 統計情報
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
        """)
        stats_layout = QGridLayout()
        stats_frame.setLayout(stats_layout)
        
        # 統計データを取得
        try:
            self.cursor.execute("SELECT COUNT(*) FROM lost_items WHERE item_situation = '保管中'")
            stored_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM lost_items WHERE refund_situation = '済'")
            refunded_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM lost_items")
            total_count = self.cursor.fetchone()[0]
            
        except Exception as e:
            stored_count = refunded_count = total_count = 0
        
        # 統計カード
        stats_cards = [
            ("保管中", str(stored_count), "#e74c3c"),
            ("返還済み", str(refunded_count), "#27ae60"),
            ("総件数", str(total_count), "#3498db"),
        ]
        
        for i, (label, value, color) in enumerate(stats_cards):
            card = self.create_stat_card(label, value, color)
            stats_layout.addWidget(card, 0, i)
        
        layout.addWidget(stats_frame)
        
        # クイックアクション
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
        """)
        actions_layout = QVBoxLayout()
        actions_frame.setLayout(actions_layout)
        
        actions_title = QLabel("クイックアクション")
        actions_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        actions_layout.addWidget(actions_title)
        
        # アクションボタン
        action_buttons = [
            ("📷 新しい拾得物を登録", self.show_register),
            ("🔍 拾得物を検索", self.show_search),
            ("📊 統計を確認", self.show_statistics),
        ]
        
        for text, callback in action_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 15px;
                    border-radius: 5px;
                    font-size: 14px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        
        layout.addWidget(actions_frame)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
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
        # 登録フォームを作成
        self.register_form = RegisterForm()
        self.register_form.form_submitted.connect(self.handle_form_submission)
        
        # スクロールエリアでラップ
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.register_form)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ecf0f1;
            }
        """)
        
        self.stacked_widget.addWidget(scroll_area)
    
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
    
    def create_settings_page(self):
        """設定ページの作成"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        title = QLabel("設定")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 設定機能は後で実装
        settings_label = QLabel("設定機能は後で実装予定")
        settings_label.setAlignment(Qt.AlignCenter)
        settings_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        layout.addWidget(settings_label)
        
        self.stacked_widget.addWidget(page)
    
    def apply_styles(self):
        """アプリケーション全体のスタイル適用"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
        """)
    
    # ナビゲーション関数
    def show_home(self):
        self.stacked_widget.setCurrentIndex(0)
    
    def show_photo(self):
        self.stacked_widget.setCurrentIndex(1)
    
    def show_register(self):
        self.stacked_widget.setCurrentIndex(2)
    
    def show_items(self):
        self.stacked_widget.setCurrentIndex(3)
    
    def show_search(self):
        self.stacked_widget.setCurrentIndex(4)
    
    def show_statistics(self):
        self.stacked_widget.setCurrentIndex(5)
    
    def show_settings(self):
        self.stacked_widget.setCurrentIndex(6)
    
    def handle_form_submission(self, form_data):
        """フォーム送信の処理"""
        try:
            # データベースに保存
            self.save_lost_item(form_data)
            
            QMessageBox.information(
                self, "成功", "拾得物の登録が完了しました"
            )
            
            # ホーム画面に戻る
            self.show_home()
            
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", f"登録中にエラーが発生しました: {str(e)}"
            )
    
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
            form_data.get("photo_path", ""), "保管中", "未"
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
    
    def closeEvent(self, event):
        """アプリケーション終了時の処理"""
        if hasattr(self, 'conn'):
            self.conn.close()
        event.accept()


def main():
    """メイン関数"""
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