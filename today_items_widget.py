#!/usr/bin/env python3
"""
本日の拾得物一覧ウィジェット
"""

import sys
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon

class TodayItemsWidget(QWidget):
    """本日の拾得物一覧ウィジェット"""
    
    item_clicked = pyqtSignal(int)  # アイテムクリック時のシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # タイトル
        title = QLabel("本日の拾得物")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        layout.addWidget(title)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # アイテム表示エリア
        self.items_widget = QWidget()
        self.items_layout = QGridLayout()
        self.items_widget.setLayout(self.items_layout)
        
        scroll_area.setWidget(self.items_widget)
        layout.addWidget(scroll_area)
        
    def update_items(self, items):
        """アイテム一覧を更新"""
        self.items = items
        self.refresh_display()
        
    def refresh_display(self):
        """表示を更新"""
        # 既存のウィジェットをクリア
        for i in reversed(range(self.items_layout.count())):
            widget = self.items_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        if not self.items:
            # アイテムがない場合
            no_items_label = QLabel("本日の拾得物はありません")
            no_items_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 14px;
                    padding: 20px;
                }
            """)
            no_items_label.setAlignment(Qt.AlignCenter)
            self.items_layout.addWidget(no_items_label, 0, 0)
            return
        
        # アイテムを4列で表示
        for i, item in enumerate(self.items):
            row = i // 4
            col = i % 4
            
            item_card = self.create_item_card(item)
            self.items_layout.addWidget(item_card, row, col)
    
    def create_item_card(self, item):
        """アイテムカードを作成"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
                border: 1px solid #ecf0f1;
            }
            QFrame:hover {
                border: 2px solid #3498db;
            }
        """)
        card.setFixedSize(200, 250)
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 写真エリア
        photo_label = QLabel()
        photo_label.setFixedSize(180, 120)
        photo_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                border-radius: 5px;
                border: 1px solid #bdc3c7;
            }
        """)
        photo_label.setAlignment(Qt.AlignCenter)
        
        # 写真がある場合は表示
        if item.get('item_image'):
            try:
                pixmap = QPixmap(item['item_image'])
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    photo_label.setPixmap(pixmap)
                else:
                    photo_label.setText("📷")
            except:
                photo_label.setText("📷")
        else:
            photo_label.setText("📷")
        
        layout.addWidget(photo_label)
        
        # アイテム情報
        info_layout = QVBoxLayout()
        
        # メインID
        main_id_label = QLabel(f"ID: {item.get('main_id', 'N/A')}")
        main_id_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                font-size: 14px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        info_layout.addWidget(main_id_label)
        
        # 物品分類
        item_class = f"{item.get('item_class_L', '')} - {item.get('item_class_M', '')}"
        if item.get('item_class_S'):
            item_class += f" - {item['item_class_S']}"
        
        class_label = QLabel(item_class)
        class_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                font-size: 13px;
                font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
            }
        """)
        class_label.setWordWrap(True)
        info_layout.addWidget(class_label)
        
        # 拾得場所
        find_area = item.get('find_area', '')
        if find_area:
            area_label = QLabel(f"拾得場所: {find_area}")
            area_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 12px;
                    font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                }
            """)
            area_label.setWordWrap(True)
            info_layout.addWidget(area_label)
        
        # 拾得時間
        get_time = item.get('get_item')
        if get_time:
            time_label = QLabel(f"拾得時間: {get_time}")
            time_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 12px;
                    font-family: "Yu Gothic", "游ゴシック", "メイリオ", "Meiryo", sans-serif;
                }
            """)
            info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        
        # クリックイベント
        card.mousePressEvent = lambda event, item_id=item.get('id'): self.on_item_clicked(item_id)
        
        return card
    
    def on_item_clicked(self, item_id):
        """アイテムクリック時の処理"""
        if item_id:
            self.item_clicked.emit(item_id)


class TodayItemsPage(QWidget):
    """本日の拾得物ページ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cursor = parent.cursor if parent else None
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # タイトル
        title = QLabel("本日の拾得物一覧")
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
        
        # 本日の拾得物ウィジェット
        self.today_items = TodayItemsWidget()
        self.today_items.item_clicked.connect(self.on_item_clicked)
        layout.addWidget(self.today_items)
        
        # 初期データ読み込み
        self.load_today_items()
        
    def load_today_items(self):
        """本日の拾得物を読み込み"""
        if not self.cursor:
            return
        
        try:
            today = date.today()
            
            # 本日の拾得物を取得
            self.cursor.execute("""
                SELECT id, main_id, item_class_L, item_class_M, item_class_S,
                       find_area, get_item, item_image, item_feature
                FROM lost_items 
                WHERE DATE(get_item) = ?
                ORDER BY get_item DESC
            """, (today,))
            
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
            
            self.today_items.update_items(items)
            
        except Exception as e:
            print(f"本日の拾得物読み込みエラー: {e}")
    
    def on_item_clicked(self, item_id):
        """アイテムクリック時の処理"""
        # 詳細画面に遷移する処理をここに実装
        print(f"アイテムID {item_id} がクリックされました")
    
    def refresh(self):
        """ページを更新"""
        self.load_today_items() 