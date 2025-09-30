#!/usr/bin/env python3
"""
ログインダイアログ
"""

import sys
import hashlib
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

class LoginDialog(QDialog):
    """ログインダイアログクラス"""
    
    login_successful = pyqtSignal(dict)  # ログイン成功時のシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ログイン")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # データベース接続
        self.conn = parent.conn if parent else None
        self.cursor = parent.cursor if parent else None
        
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # タイトル
        title = QLabel("拾得物管理システム")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        layout.addWidget(title)
        
        # ログインフォーム
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        form_layout = QGridLayout()
        form_frame.setLayout(form_layout)
        
        # ユーザー名
        username_label = QLabel("ユーザー名:")
        username_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("ユーザー名を入力")
        self.username_edit.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_edit, 0, 1)
        
        # パスワード
        password_label = QLabel("パスワード:")
        password_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("パスワードを入力")
        self.password_edit.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.password_edit, 1, 1)
        
        layout.addWidget(form_frame)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        # ログインボタン
        login_btn = QPushButton("ログイン")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        login_btn.clicked.connect(self.login)
        button_layout.addWidget(login_btn)
        
        # ゲストログインボタン
        guest_btn = QPushButton("ゲストとして使用")
        guest_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        guest_btn.clicked.connect(self.guest_login)
        button_layout.addWidget(guest_btn)
        
        layout.addLayout(button_layout)
        
        # 新規ユーザー登録リンク
        register_link = QLabel("新規ユーザー登録")
        register_link.setAlignment(Qt.AlignCenter)
        register_link.setStyleSheet("""
            QLabel {
                color: #3498db;
                text-decoration: underline;
                cursor: pointer;
                padding: 10px;
                font-size: 14px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        register_link.mousePressEvent = self.show_register_dialog
        layout.addWidget(register_link)
        
        # Enterキーでログイン
        self.password_edit.returnPressed.connect(self.login)
        
    def login(self):
        """ログイン処理"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "ユーザー名とパスワードを入力してください")
            return
        
        # パスワードのハッシュ化
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            # ユーザー認証
            self.cursor.execute(
                "SELECT id, username, email FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            user = self.cursor.fetchone()
            
            if user:
                user_data = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'is_guest': False
                }
                self.login_successful.emit(user_data)
                self.accept()
            else:
                QMessageBox.warning(self, "エラー", "ユーザー名またはパスワードが正しくありません")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ログイン中にエラーが発生しました: {str(e)}")
    
    def guest_login(self):
        """ゲストログイン"""
        user_data = {
            'id': None,
            'username': 'ゲスト',
            'email': None,
            'is_guest': True
        }
        self.login_successful.emit(user_data)
        self.accept()
    
    def show_register_dialog(self, event):
        """新規ユーザー登録ダイアログを表示"""
        dialog = RegisterDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "成功", "ユーザー登録が完了しました")


class RegisterDialog(QDialog):
    """新規ユーザー登録ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新規ユーザー登録")
        self.setFixedSize(400, 350)
        self.setModal(True)
        
        self.conn = parent.conn
        self.cursor = parent.cursor
        
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # タイトル
        title = QLabel("新規ユーザー登録")
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
        
        # 登録フォーム
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        form_layout = QGridLayout()
        form_frame.setLayout(form_layout)
        
        # ユーザー名
        username_label = QLabel("ユーザー名:")
        username_label.setStyleSheet("font-weight: bold;")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("ユーザー名を入力")
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_edit, 0, 1)
        
        # メールアドレス
        email_label = QLabel("メールアドレス:")
        email_label.setStyleSheet("font-weight: bold;")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("メールアドレスを入力")
        form_layout.addWidget(email_label, 1, 0)
        form_layout.addWidget(self.email_edit, 1, 1)
        
        # パスワード
        password_label = QLabel("パスワード:")
        password_label.setStyleSheet("font-weight: bold;")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("パスワードを入力")
        form_layout.addWidget(password_label, 2, 0)
        form_layout.addWidget(self.password_edit, 2, 1)
        
        # パスワード確認
        confirm_label = QLabel("パスワード確認:")
        confirm_label.setStyleSheet("font-weight: bold;")
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setPlaceholderText("パスワードを再入力")
        form_layout.addWidget(confirm_label, 3, 0)
        form_layout.addWidget(self.confirm_edit, 3, 1)
        
        layout.addWidget(form_frame)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        register_btn = QPushButton("登録")
        register_btn.setStyleSheet("""
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
        register_btn.clicked.connect(self.register)
        button_layout.addWidget(register_btn)
        
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
    
    def register(self):
        """ユーザー登録処理"""
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        
        # 入力チェック
        if not username or not email or not password:
            QMessageBox.warning(self, "警告", "すべての項目を入力してください")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "警告", "パスワードが一致しません")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "警告", "パスワードは6文字以上で入力してください")
            return
        
        try:
            # パスワードのハッシュ化
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # ユーザー登録
            self.cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            self.conn.commit()
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ユーザー登録中にエラーが発生しました: {str(e)}") 