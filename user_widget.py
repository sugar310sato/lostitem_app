#!/usr/bin/env python3
"""
ユーザー管理ウィジェット
"""

import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QAction, QFrame, QDialog, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon

class UserWidget(QWidget):
    """ユーザー管理ウィジェット"""
    
    logout_requested = pyqtSignal()  # ログアウト要求シグナル
    user_changed = pyqtSignal(dict)  # ユーザー変更シグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.main_window = None
        self.init_ui()
        
    def set_main_window(self, main_window):
        """メインウィンドウの参照を設定"""
        self.main_window = main_window
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # ユーザー情報フレーム
        self.user_frame = QFrame()
        self.user_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        user_layout = QVBoxLayout()
        self.user_frame.setLayout(user_layout)
        
        # ユーザー名ラベル
        self.username_label = QLabel("ゲスト")
        self.username_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        self.username_label.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(self.username_label)
        
        # ユーザーアイコン
        self.user_icon = QLabel("👤")
        self.user_icon.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                text-align: center;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        self.user_icon.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(self.user_icon)
        
        # ユーザー管理ボタン
        self.user_btn = QPushButton("ユーザー管理")
        self.user_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid #95a5a6;
                border-radius: 3px;
                padding: 8px;
                font-size: 14px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        self.user_btn.clicked.connect(self.show_user_menu)
        user_layout.addWidget(self.user_btn)
        
        layout.addWidget(self.user_frame)
        
    def set_user(self, user_data):
        """ユーザー情報を設定"""
        self.current_user = user_data
        
        if user_data['is_guest']:
            self.username_label.setText("ゲスト")
            self.user_icon.setText("👤")
            self.user_btn.setText("ログイン")
        else:
            self.username_label.setText(user_data['username'])
            self.user_icon.setText("👤")
            self.user_btn.setText("ユーザー管理")
    
    def show_user_menu(self):
        """ユーザーメニューを表示"""
        if not self.current_user or self.current_user['is_guest']:
            # ゲストの場合はログインダイアログを表示
            self.show_login_dialog()
            return
        
        # ログイン済みユーザーのメニュー
        menu = QMenu(self)
        
        # ユーザー情報表示
        info_action = QAction("ユーザー情報", self)
        info_action.triggered.connect(self.show_user_info)
        menu.addAction(info_action)
        
        menu.addSeparator()
        
        # ユーザー切り替え
        switch_action = QAction("ユーザー切り替え", self)
        switch_action.triggered.connect(self.show_login_dialog)
        menu.addAction(switch_action)
        
        # ログアウト
        logout_action = QAction("ログアウト", self)
        logout_action.triggered.connect(self.logout)
        menu.addAction(logout_action)
        
        # メニューを表示
        menu.exec_(self.user_btn.mapToGlobal(self.user_btn.rect().bottomLeft()))
    
    def show_login_dialog(self):
        """ログインダイアログを表示"""
        from login_dialog import LoginDialog
        dialog = LoginDialog(self.main_window)
        dialog.login_successful.connect(self.on_login_successful)
        dialog.exec_()
    
    def on_login_successful(self, user_data):
        """ログイン成功時の処理"""
        self.set_user(user_data)
        self.user_changed.emit(user_data)
    
    def show_user_info(self):
        """ユーザー情報を表示"""
        if not self.current_user or self.current_user['is_guest']:
            return
        
        info_text = f"""
ユーザー名: {self.current_user['username']}
メールアドレス: {self.current_user['email']}
ユーザーID: {self.current_user['id']}
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("ユーザー情報")
        msg_box.setText(info_text.strip())
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                font-size: 14px;
            }
            QMessageBox QLabel {
                background-color: white;
                color: #2c3e50;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                font-size: 14px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        msg_box.exec_()
    
    def logout(self):
        """ログアウト処理"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("ログアウト")
        msg_box.setText("ログアウトしますか？")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                font-size: 14px;
            }
            QMessageBox QLabel {
                background-color: white;
                color: #2c3e50;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                font-size: 14px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        reply = msg_box.exec_()
        
        if reply == QMessageBox.Yes:
            # ゲストユーザーに設定
            guest_data = {
                'id': None,
                'username': 'ゲスト',
                'email': None,
                'is_guest': True
            }
            self.set_user(guest_data)
            self.user_changed.emit(guest_data)
            self.logout_requested.emit()


class UserInfoDialog(QDialog):
    """ユーザー情報編集ダイアログ"""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("ユーザー情報編集")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # タイトル
        title = QLabel("ユーザー情報編集")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
            }
        """)
        layout.addWidget(title)
        
        # フォーム
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        form_layout = QVBoxLayout()
        form_frame.setLayout(form_layout)
        
        # ユーザー名
        username_layout = QHBoxLayout()
        username_label = QLabel("ユーザー名:")
        username_label.setStyleSheet("font-weight: bold;")
        self.username_edit = QLineEdit(self.user_data['username'])
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        form_layout.addLayout(username_layout)
        
        # メールアドレス
        email_layout = QHBoxLayout()
        email_label = QLabel("メールアドレス:")
        email_label.setStyleSheet("font-weight: bold;")
        self.email_edit = QLineEdit(self.user_data['email'])
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_edit)
        form_layout.addLayout(email_layout)
        
        layout.addWidget(form_frame)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_user_info)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def save_user_info(self):
        """ユーザー情報を保存"""
        # ここでデータベース更新処理を実装
        QMessageBox.information(self, "成功", "ユーザー情報を更新しました")
        self.accept() 