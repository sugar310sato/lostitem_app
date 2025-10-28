import flet as ft
from flet_pages.statistics import StatisticsView


def main(page: ft.Page):
    page.title = "統計画面プレビュー"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1200
    page.window_height = 800
    page.bgcolor = ft.colors.GREY_50
    
    # 統計ビューを作成
    stats_view = StatisticsView()
    
    # ページにコンテンツを追加
    page.add(stats_view)


if __name__ == "__main__":
    ft.app(target=main)

