#!/usr/bin/env python3
"""
カメラ撮影とフォーム入力のテスト用アプリケーション
"""

import flet as ft
from flet_pages.register_form import RegisterFlowView

def main(page: ft.Page):
    """メインアプリケーション"""
    page.title = "拾得物登録システム - カメラ撮影テスト"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    def on_submit(data):
        """登録完了時の処理"""
        print("登録データ:", data)
        page.snack_bar = ft.SnackBar(
            content=ft.Text("登録が完了しました！"),
            bgcolor=ft.colors.GREEN
        )
        page.snack_bar.open = True
        page.update()
    
    def on_temp_save(data):
        """一時保存時の処理"""
        print("一時保存データ:", data)
        page.snack_bar = ft.SnackBar(
            content=ft.Text("一時保存しました"),
            bgcolor=ft.colors.BLUE
        )
        page.snack_bar.open = True
        page.update()
    
    # RegisterFlowViewを作成（カメラ画面から開始）
    register_flow = RegisterFlowView(
        on_submit=on_submit,
        on_temp_save=on_temp_save
    )
    
    # ページに追加
    page.add(register_flow)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
