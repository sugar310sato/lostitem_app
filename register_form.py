#!/usr/bin/env python3
"""
拾得物登録フォーム - Windowsアプリケーション版
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit,
    QPushButton, QFrame, QScrollArea, QMessageBox, QFileDialog,
    QSpinBox, QCheckBox, QGroupBox, QTabWidget
)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from datetime import datetime, date
import os
from pathlib import Path

class RegisterForm(QWidget):
    """拾得物登録フォーム"""
    
    # シグナル定義
    form_submitted = pyqtSignal(dict)  # フォーム送信時のシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # タイトル
        title = QLabel("拾得物登録")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
        """)
        
        # 基本情報タブ
        self.create_basic_info_tab()
        
        # 拾得者情報タブ
        self.create_finder_info_tab()
        
        # 物品情報タブ
        self.create_item_info_tab()
        
        # 写真・備考タブ
        self.create_photo_remarks_tab()
        
        layout.addWidget(self.tab_widget)
        
        # ボタンエリア
        self.create_button_area(layout)
        
    def create_basic_info_tab(self):
        """基本情報タブの作成"""
        tab = QWidget()
        layout = QFormLayout()
        tab.setLayout(layout)
        
        # 拾得者区分
        self.finder_type_combo = QComboBox()
        self.finder_type_combo.addItems(["占有者拾得", "第三者拾得"])
        layout.addRow("拾得者区分:", self.finder_type_combo)
        
        # 届出区分
        self.notify_combo = QComboBox()
        self.notify_combo.addItems(["届出あり", "届出なし"])
        layout.addRow("届出区分:", self.notify_combo)
        
        # 拾得日時
        self.get_date_edit = QDateEdit()
        self.get_date_edit.setDate(QDate.currentDate())
        self.get_date_edit.setCalendarPopup(True)
        layout.addRow("拾得日:", self.get_date_edit)
        
        self.get_time_edit = QTimeEdit()
        self.get_time_edit.setTime(QTime.currentTime())
        layout.addRow("拾得時刻:", self.get_time_edit)
        
        # 受付日時
        self.recep_date_edit = QDateEdit()
        self.recep_date_edit.setDate(QDate.currentDate())
        self.recep_date_edit.setCalendarPopup(True)
        layout.addRow("受付日:", self.recep_date_edit)
        
        self.recep_time_edit = QTimeEdit()
        self.recep_time_edit.setTime(QTime.currentTime())
        layout.addRow("受付時刻:", self.recep_time_edit)
        
        # 受付担当者
        self.recep_manager_edit = QLineEdit()
        layout.addRow("受付担当者:", self.recep_manager_edit)
        
        # 拾得場所
        self.find_area_edit = QLineEdit()
        layout.addRow("拾得場所:", self.find_area_edit)
        
        # 警察署管轄区域
        self.find_area_police_edit = QLineEdit()
        layout.addRow("警察署管轄区域:", self.find_area_police_edit)
        
        self.tab_widget.addTab(tab, "基本情報")
        
    def create_finder_info_tab(self):
        """拾得者情報タブの作成"""
        tab = QWidget()
        layout = QFormLayout()
        tab.setLayout(layout)
        
        # 拾得者氏名
        self.finder_name_edit = QLineEdit()
        layout.addRow("拾得者氏名:", self.finder_name_edit)
        
        # 拾得者年齢
        self.finder_age_spin = QSpinBox()
        self.finder_age_spin.setRange(0, 120)
        layout.addRow("拾得者年齢:", self.finder_age_spin)
        
        # 拾得者性別
        self.finder_sex_combo = QComboBox()
        self.finder_sex_combo.addItems(["男性", "女性", "その他"])
        layout.addRow("拾得者性別:", self.finder_sex_combo)
        
        # 郵便番号
        self.finder_post_edit = QLineEdit()
        self.finder_post_edit.setPlaceholderText("例: 123-4567")
        layout.addRow("郵便番号:", self.finder_post_edit)
        
        # 住所
        self.finder_address_edit = QTextEdit()
        self.finder_address_edit.setMaximumHeight(60)
        layout.addRow("住所:", self.finder_address_edit)
        
        # 電話番号1
        self.finder_tel1_edit = QLineEdit()
        self.finder_tel1_edit.setPlaceholderText("例: 03-1234-5678")
        layout.addRow("電話番号1:", self.finder_tel1_edit)
        
        # 電話番号2
        self.finder_tel2_edit = QLineEdit()
        self.finder_tel2_edit.setPlaceholderText("例: 090-1234-5678")
        layout.addRow("電話番号2:", self.finder_tel2_edit)
        
        # 所属
        self.finder_affiliation_edit = QLineEdit()
        layout.addRow("所属:", self.finder_affiliation_edit)
        
        self.tab_widget.addTab(tab, "拾得者情報")
        
    def create_item_info_tab(self):
        """物品情報タブの作成"""
        tab = QWidget()
        layout = QFormLayout()
        tab.setLayout(layout)
        
        # 物品分類（大）
        self.item_class_L_combo = QComboBox()
        self.item_class_L_combo.addItems([
            "現金", "有価証券類", "貴金属類", "時計類", "めがね類", 
            "かばん類", "衣類・履物類", "書類・紙類", "電気製品類",
            "携帯電話類", "カメラ類", "証明書類・カード類", "鍵類",
            "趣味娯楽用品類", "スポーツ用品類", "医療・化粧品類",
            "食料品類", "生活用品類", "手帳文具類", "小包・箱類",
            "かさ類", "財布類", "著作品類", "カードケース類",
            "動植物類", "その他"
        ])
        layout.addRow("物品分類（大）:", self.item_class_L_combo)
        
        # 物品分類（中）
        self.item_class_M_combo = QComboBox()
        self.item_class_M_combo.addItems(["選択してください"])
        layout.addRow("物品分類（中）:", self.item_class_M_combo)
        
        # 物品分類（小）
        self.item_class_S_combo = QComboBox()
        self.item_class_S_combo.addItems(["選択してください"])
        layout.addRow("物品分類（小）:", self.item_class_S_combo)
        
        # 物品の特徴
        self.item_feature_edit = QTextEdit()
        self.item_feature_edit.setMaximumHeight(80)
        layout.addRow("物品の特徴:", self.item_feature_edit)
        
        # 物品の色
        self.item_color_edit = QLineEdit()
        layout.addRow("物品の色:", self.item_color_edit)
        
        # 保管場所
        self.item_storage_edit = QLineEdit()
        layout.addRow("保管場所:", self.item_storage_edit)
        
        # 保管場所詳細
        self.item_storage_place_edit = QLineEdit()
        layout.addRow("保管場所詳細:", self.item_storage_place_edit)
        
        # 製造者
        self.item_maker_edit = QLineEdit()
        layout.addRow("製造者:", self.item_maker_edit)
        
        # 有効期限
        self.item_expiration_edit = QDateEdit()
        self.item_expiration_edit.setCalendarPopup(True)
        layout.addRow("有効期限:", self.item_expiration_edit)
        
        # 数量
        self.item_num_spin = QSpinBox()
        self.item_num_spin.setRange(1, 999)
        self.item_num_spin.setValue(1)
        layout.addRow("数量:", self.item_num_spin)
        
        # 単位
        self.item_unit_edit = QLineEdit()
        self.item_unit_edit.setText("個")
        layout.addRow("単位:", self.item_unit_edit)
        
        # 価格
        self.item_value_spin = QSpinBox()
        self.item_value_spin.setRange(0, 9999999)
        self.item_value_spin.setSuffix(" 円")
        layout.addRow("価格:", self.item_value_spin)
        
        # 現金金額
        self.item_money_spin = QSpinBox()
        self.item_money_spin.setRange(0, 9999999)
        self.item_money_spin.setSuffix(" 円")
        layout.addRow("現金金額:", self.item_money_spin)
        
        self.tab_widget.addTab(tab, "物品情報")
        
    def create_photo_remarks_tab(self):
        """写真・備考タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # 写真エリア
        photo_group = QGroupBox("写真")
        photo_layout = QVBoxLayout()
        photo_group.setLayout(photo_layout)
        
        # 写真表示エリア
        self.photo_label = QLabel()
        self.photo_label.setMinimumSize(300, 200)
        self.photo_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                background-color: #f8f9fa;
            }
        """)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setText("写真がありません")
        photo_layout.addWidget(self.photo_label)
        
        # 写真ボタン
        photo_button_layout = QHBoxLayout()
        self.load_photo_btn = QPushButton("写真を選択")
        self.load_photo_btn.clicked.connect(self.load_photo)
        self.take_photo_btn = QPushButton("カメラで撮影")
        self.take_photo_btn.clicked.connect(self.take_photo)
        photo_button_layout.addWidget(self.load_photo_btn)
        photo_button_layout.addWidget(self.take_photo_btn)
        photo_layout.addLayout(photo_button_layout)
        
        layout.addWidget(photo_group)
        
        # 備考エリア
        remarks_group = QGroupBox("備考")
        remarks_layout = QVBoxLayout()
        remarks_group.setLayout(remarks_layout)
        
        self.item_remarks_edit = QTextEdit()
        self.item_remarks_edit.setPlaceholderText("備考を入力してください...")
        remarks_layout.addWidget(self.item_remarks_edit)
        
        layout.addWidget(remarks_group)
        
        # AI認識結果エリア
        ai_group = QGroupBox("AI認識結果")
        ai_layout = QVBoxLayout()
        ai_group.setLayout(ai_layout)
        
        self.ai_result_label = QLabel("AI認識結果がここに表示されます")
        self.ai_result_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e8f4fd;
                border: 1px solid #b3d9ff;
                border-radius: 5px;
            }
        """)
        ai_layout.addWidget(self.ai_result_label)
        
        layout.addWidget(ai_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "写真・備考")
        
    def create_button_area(self, main_layout):
        """ボタンエリアの作成"""
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 10px;
            }
        """)
        
        button_layout = QHBoxLayout()
        button_frame.setLayout(button_layout)
        
        # 左側のボタン
        left_buttons = QHBoxLayout()
        
        self.clear_btn = QPushButton("クリア")
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        left_buttons.addWidget(self.clear_btn)
        
        button_layout.addLayout(left_buttons)
        button_layout.addStretch()
        
        # 右側のボタン
        right_buttons = QHBoxLayout()
        
        self.cancel_btn = QPushButton("キャンセル")
        self.cancel_btn.clicked.connect(self.cancel_form)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        right_buttons.addWidget(self.cancel_btn)
        
        self.submit_btn = QPushButton("登録")
        self.submit_btn.clicked.connect(self.submit_form)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        right_buttons.addWidget(self.submit_btn)
        
        button_layout.addLayout(right_buttons)
        main_layout.addWidget(button_frame)
        
    def load_photo(self):
        """写真を選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "写真を選択", "", "画像ファイル (*.jpg *.jpeg *.png *.bmp)"
        )
        if file_path:
            self.display_photo(file_path)
            
    def take_photo(self):
        """カメラで撮影"""
        # カメラ機能は後で実装
        QMessageBox.information(self, "情報", "カメラ機能は後で実装予定です")
        
    def display_photo(self, file_path):
        """写真を表示"""
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # サイズ調整
            scaled_pixmap = pixmap.scaled(
                300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.photo_label.setPixmap(scaled_pixmap)
            self.photo_path = file_path
        else:
            QMessageBox.warning(self, "エラー", "画像の読み込みに失敗しました")
            
    def clear_form(self):
        """フォームをクリア"""
        reply = QMessageBox.question(
            self, "確認", "フォームをクリアしますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 各フィールドをリセット
            self.finder_type_combo.setCurrentIndex(0)
            self.notify_combo.setCurrentIndex(0)
            self.get_date_edit.setDate(QDate.currentDate())
            self.get_time_edit.setTime(QTime.currentTime())
            self.recep_date_edit.setDate(QDate.currentDate())
            self.recep_time_edit.setTime(QTime.currentTime())
            self.recep_manager_edit.clear()
            self.find_area_edit.clear()
            self.find_area_police_edit.clear()
            self.finder_name_edit.clear()
            self.finder_age_spin.setValue(0)
            self.finder_sex_combo.setCurrentIndex(0)
            self.finder_post_edit.clear()
            self.finder_address_edit.clear()
            self.finder_tel1_edit.clear()
            self.finder_tel2_edit.clear()
            self.finder_affiliation_edit.clear()
            self.item_class_L_combo.setCurrentIndex(0)
            self.item_feature_edit.clear()
            self.item_color_edit.clear()
            self.item_storage_edit.clear()
            self.item_storage_place_edit.clear()
            self.item_maker_edit.clear()
            self.item_num_spin.setValue(1)
            self.item_unit_edit.setText("個")
            self.item_value_spin.setValue(0)
            self.item_money_spin.setValue(0)
            self.item_remarks_edit.clear()
            
            # 写真をリセット
            self.photo_label.clear()
            self.photo_label.setText("写真がありません")
            self.photo_path = None
            
    def cancel_form(self):
        """フォームをキャンセル"""
        reply = QMessageBox.question(
            self, "確認", "登録をキャンセルしますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 親ウィンドウに戻る
            if self.parent():
                self.parent().show_home()
                
    def submit_form(self):
        """フォームを送信"""
        # バリデーション
        if not self.validate_form():
            return
            
        # フォームデータを収集
        form_data = self.collect_form_data()
        
        # 送信
        self.form_submitted.emit(form_data)
        
    def validate_form(self):
        """フォームのバリデーション"""
        errors = []
        
        # 必須項目のチェック
        if not self.finder_name_edit.text().strip():
            errors.append("拾得者氏名は必須です")
            
        if not self.find_area_edit.text().strip():
            errors.append("拾得場所は必須です")
            
        if not self.item_feature_edit.toPlainText().strip():
            errors.append("物品の特徴は必須です")
            
        if errors:
            error_msg = "\n".join(errors)
            QMessageBox.warning(self, "入力エラー", error_msg)
            return False
            
        return True
        
    def collect_form_data(self):
        """フォームデータを収集"""
        return {
            # 基本情報
            "finder_type": self.finder_type_combo.currentText(),
            "notify": self.notify_combo.currentText(),
            "get_date": self.get_date_edit.date().toPyDate(),
            "get_time": self.get_time_edit.time().toPyTime(),
            "recep_date": self.recep_date_edit.date().toPyDate(),
            "recep_time": self.recep_time_edit.time().toPyTime(),
            "recep_manager": self.recep_manager_edit.text(),
            "find_area": self.find_area_edit.text(),
            "find_area_police": self.find_area_police_edit.text(),
            
            # 拾得者情報
            "finder_name": self.finder_name_edit.text(),
            "finder_age": self.finder_age_spin.value(),
            "finder_sex": self.finder_sex_combo.currentText(),
            "finder_post": self.finder_post_edit.text(),
            "finder_address": self.finder_address_edit.toPlainText(),
            "finder_tel1": self.finder_tel1_edit.text(),
            "finder_tel2": self.finder_tel2_edit.text(),
            "finder_affiliation": self.finder_affiliation_edit.text(),
            
            # 物品情報
            "item_class_L": self.item_class_L_combo.currentText(),
            "item_class_M": self.item_class_M_combo.currentText(),
            "item_class_S": self.item_class_S_combo.currentText(),
            "item_feature": self.item_feature_edit.toPlainText(),
            "item_color": self.item_color_edit.text(),
            "item_storage": self.item_storage_edit.text(),
            "item_storage_place": self.item_storage_place_edit.text(),
            "item_maker": self.item_maker_edit.text(),
            "item_expiration": self.item_expiration_edit.date().toPyDate(),
            "item_num": self.item_num_spin.value(),
            "item_unit": self.item_unit_edit.text(),
            "item_value": self.item_value_spin.value(),
            "item_money": self.item_money_spin.value(),
            "item_remarks": self.item_remarks_edit.toPlainText(),
            
            # 写真
            "photo_path": getattr(self, 'photo_path', None),
        }
        
    def set_ai_result(self, result):
        """AI認識結果を設定"""
        if result:
            self.ai_result_label.setText(f"AI認識結果: {result}")
        else:
            self.ai_result_label.setText("AI認識結果がありません") 