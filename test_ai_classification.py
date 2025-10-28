#!/usr/bin/env python3
"""
AI分類機能のテストスクリプト
"""

import flet as ft
from flet_pages.ai_classification import AIClassificationView

def main(page: ft.Page):
    page.title = "AI分類テスト"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # AI分類ビューを作成
    ai_view = AIClassificationView()
    
    page.add(ai_view)

if __name__ == "__main__":
    ft.app(target=main)
