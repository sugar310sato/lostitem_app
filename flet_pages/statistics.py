import flet as ft
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
from collections import defaultdict

DB_PATH = Path(__file__).resolve().parent.parent / "lostitem.db"


class StatisticsView(ft.UserControl):
    """統計画面"""
    
    def __init__(self):
        super().__init__()
        self.period = "month"  # day, month, year
        self.chart_type = "line"  # line, bar, pie
    
    def build(self):
        # ヘッダー
        header = ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=lambda e: self.page.go("/"),
                tooltip="ホームに戻る"
            ),
            ft.Text("統計・分析", size=28, weight=ft.FontWeight.BOLD),
        ], alignment=ft.MainAxisAlignment.START)
        
        # 期間選択
        self.period_selector = ft.Tabs(
            selected_index=1,
            on_change=self.on_period_change,
            tabs=[
                ft.Tab(text="日別", icon=ft.icons.TODAY),
                ft.Tab(text="月別", icon=ft.icons.CALENDAR_MONTH),
                ft.Tab(text="年別", icon=ft.icons.CALENDAR_TODAY),
            ],
        )
        
        # 統計カード
        self.stats_cards = ft.Row(
            controls=[],
            spacing=16,
            wrap=True,
        )
        
        # グラフエリア
        self.chart_area = ft.Container(
            content=ft.Column([
                ft.Text("データを読み込み中...", size=16),
            ]),
            padding=20,
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            expand=True,
        )
        
        # レポート出力ボタン
        export_buttons = ft.Row([
            ft.ElevatedButton(
                "月次レポート出力",
                icon=ft.icons.PICTURE_AS_PDF,
                on_click=self.export_monthly_report,
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                )
            ),
            ft.ElevatedButton(
                "CSVエクスポート",
                icon=ft.icons.TABLE_CHART,
                on_click=self.export_csv,
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.GREEN_700,
                    color=ft.colors.WHITE
                )
            ),
        ], spacing=16)
        
        # メインコンテンツ
        content = ft.Column([
            header,
            ft.Divider(),
            self.period_selector,
            ft.Container(height=10),
            self.stats_cards,
            ft.Container(height=20),
            ft.Text("詳細分析", size=20, weight=ft.FontWeight.BOLD),
            self.chart_area,
            ft.Container(height=20),
            export_buttons,
        ], expand=True, spacing=10)
        
        return ft.Container(
            content=content,
            padding=20,
            expand=True,
        )
    
    def did_mount(self):
        """マウント時にデータを読み込む"""
        self.load_statistics()
    
    def on_period_change(self, e):
        """期間変更時の処理"""
        periods = ["day", "month", "year"]
        self.period = periods[e.control.selected_index]
        self.load_statistics()
    
    def load_statistics(self):
        """統計データを読み込む"""
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
            cur = conn.cursor()
            
            # 基本統計
            stats = self.get_basic_stats(cur)
            
            # 統計カードを更新
            self.stats_cards.controls = [
                self.create_stat_card("拾得物総数", str(stats['total_items']), ft.icons.INVENTORY, ft.colors.BLUE_400),
                self.create_stat_card("返還済み", str(stats['returned_items']), ft.icons.CHECK_CIRCLE, ft.colors.GREEN_400),
                self.create_stat_card("返還率", f"{stats['return_rate']:.1f}%", ft.icons.PERCENT, ft.colors.TEAL_400),
                self.create_stat_card("遺失物", str(stats['notfound_items']), ft.icons.SEARCH_OFF, ft.colors.ORANGE_400),
            ]
            
            # グラフを更新
            self.update_charts(cur)
            
            conn.close()
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            print(f"統計読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
    
    def get_basic_stats(self, cur):
        """基本統計を取得"""
        stats = {}
        
        # 拾得物総数
        cur.execute("SELECT COUNT(*) FROM lost_items")
        stats['total_items'] = cur.fetchone()[0]
        
        # 返還済み件数
        cur.execute("SELECT COUNT(*) FROM lost_items WHERE refund_situation = '済'")
        stats['returned_items'] = cur.fetchone()[0]
        
        # 返還率
        if stats['total_items'] > 0:
            stats['return_rate'] = (stats['returned_items'] / stats['total_items']) * 100
        else:
            stats['return_rate'] = 0
        
        # 遺失物件数
        cur.execute("SELECT COUNT(*) FROM notfound_items")
        stats['notfound_items'] = cur.fetchone()[0]
        
        return stats
    
    def create_stat_card(self, title, value, icon, color):
        """統計カードを作成"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=40, color=color),
                    ft.Column([
                        ft.Text(title, size=12, color=ft.colors.GREY_700),
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ], spacing=0),
                ], spacing=15),
            ]),
            padding=20,
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            width=280,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.colors.BLACK12,
            ),
        )
    
    def update_charts(self, cur):
        """グラフを更新"""
        # 期間別のデータを取得
        if self.period == "day":
            data = self.get_daily_data(cur)
            title = "日別拾得物件数（過去30日）"
        elif self.period == "month":
            data = self.get_monthly_data(cur)
            title = "月別拾得物件数（過去12ヶ月）"
        else:
            data = self.get_yearly_data(cur)
            title = "年別拾得物件数"
        
        # 時間帯別データ
        hourly_data = self.get_hourly_distribution(cur)
        
        # カテゴリ別データ
        category_data = self.get_category_distribution(cur)
        
        # グラフを作成
        charts = ft.Column([
            ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
            self.create_line_chart(data),
            ft.Container(height=30),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("時間帯別分布", size=16, weight=ft.FontWeight.BOLD),
                        self.create_bar_chart(hourly_data),
                    ]),
                    expand=True,
                    padding=15,
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=8,
                ),
                ft.Container(width=20),
                ft.Container(
                    content=ft.Column([
                        ft.Text("物品カテゴリ別", size=16, weight=ft.FontWeight.BOLD),
                        self.create_pie_chart(category_data),
                    ]),
                    expand=True,
                    padding=15,
                    bgcolor=ft.colors.GREEN_50,
                    border_radius=8,
                ),
            ], expand=True),
        ], expand=True, spacing=10)
        
        self.chart_area.content = charts
    
    def get_daily_data(self, cur):
        """日別データを取得"""
        data = []
        for i in range(30, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM lost_items WHERE DATE(get_item) = ?", (date,))
            count = cur.fetchone()[0]
            data.append({"label": date[-5:], "value": count})
        return data
    
    def get_monthly_data(self, cur):
        """月別データを取得"""
        data = []
        for i in range(12, -1, -1):
            date = (datetime.now() - timedelta(days=i*30)).strftime("%Y-%m")
            cur.execute("SELECT COUNT(*) FROM lost_items WHERE strftime('%Y-%m', get_item) = ?", (date,))
            count = cur.fetchone()[0]
            data.append({"label": date[-5:], "value": count})
        return data
    
    def get_yearly_data(self, cur):
        """年別データを取得"""
        data = []
        cur.execute("SELECT strftime('%Y', get_item) as year, COUNT(*) FROM lost_items GROUP BY year ORDER BY year")
        for row in cur.fetchall():
            if row[0]:
                data.append({"label": row[0], "value": row[1]})
        return data
    
    def get_hourly_distribution(self, cur):
        """時間帯別分布を取得"""
        data = []
        for hour in range(0, 24, 3):
            cur.execute(
                "SELECT COUNT(*) FROM lost_items WHERE get_item_hour >= ? AND get_item_hour < ?",
                (hour, hour + 3)
            )
            count = cur.fetchone()[0]
            data.append({"label": f"{hour:02d}-{hour+3:02d}時", "value": count})
        return data
    
    def get_category_distribution(self, cur):
        """カテゴリ別分布を取得"""
        cur.execute("""
            SELECT item_class_L, COUNT(*) 
            FROM lost_items 
            WHERE item_class_L IS NOT NULL AND item_class_L != ''
            GROUP BY item_class_L 
            ORDER BY COUNT(*) DESC 
            LIMIT 6
        """)
        data = []
        for row in cur.fetchall():
            data.append({"label": row[0] or "未分類", "value": row[1]})
        return data
    
    def create_line_chart(self, data):
        """折れ線グラフを作成（シンプルな棒グラフで代用）"""
        if not data:
            return ft.Text("データがありません", color=ft.colors.GREY_600)
        
        max_value = max([d['value'] for d in data]) if data else 1
        if max_value == 0:
            max_value = 1
        
        bars = []
        for item in data:
            height = (item['value'] / max_value) * 150 if max_value > 0 else 0
            bars.append(
                ft.Column([
                    ft.Container(
                        height=150,
                        width=30,
                        alignment=ft.alignment.bottom_center,
                        content=ft.Container(
                            height=max(height, 2),
                            bgcolor=ft.colors.BLUE_400,
                            border_radius=4,
                            tooltip=f"{item['label']}: {item['value']}件",
                        ),
                    ),
                    ft.Text(item['label'], size=10, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
            )
        
        return ft.Container(
            content=ft.Row(bars, spacing=5, scroll=ft.ScrollMode.AUTO),
            padding=10,
        )
    
    def create_bar_chart(self, data):
        """棒グラフを作成"""
        if not data:
            return ft.Text("データがありません", color=ft.colors.GREY_600)
        
        max_value = max([d['value'] for d in data]) if data else 1
        if max_value == 0:
            max_value = 1
        
        bars = []
        for item in data:
            width_percent = (item['value'] / max_value) * 100 if max_value > 0 else 0
            bars.append(
                ft.Column([
                    ft.Row([
                        ft.Text(item['label'], size=12, width=80),
                        ft.Container(
                            width=width_percent * 2,
                            height=25,
                            bgcolor=ft.colors.TEAL_400,
                            border_radius=4,
                        ),
                        ft.Text(str(item['value']), size=12, color=ft.colors.GREY_700),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=5)
            )
        
        return ft.Column(bars, spacing=5)
    
    def create_pie_chart(self, data):
        """円グラフを作成（簡易版）"""
        if not data:
            return ft.Text("データがありません", color=ft.colors.GREY_600)
        
        total = sum([d['value'] for d in data])
        if total == 0:
            return ft.Text("データがありません", color=ft.colors.GREY_600)
        
        colors = [
            ft.colors.BLUE_400,
            ft.colors.GREEN_400,
            ft.colors.ORANGE_400,
            ft.colors.PURPLE_400,
            ft.colors.RED_400,
            ft.colors.TEAL_400,
        ]
        
        items = []
        for i, item in enumerate(data):
            percentage = (item['value'] / total) * 100
            items.append(
                ft.Row([
                    ft.Container(
                        width=20,
                        height=20,
                        bgcolor=colors[i % len(colors)],
                        border_radius=4,
                    ),
                    ft.Text(f"{item['label']}: {item['value']}件 ({percentage:.1f}%)", size=12),
                ], spacing=10)
            )
        
        return ft.Column(items, spacing=8)
    
    def export_monthly_report(self, e):
        """月次レポートを出力"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("月次レポート出力機能は開発中です"),
                bgcolor=ft.colors.ORANGE_700
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def export_csv(self, e):
        """CSVエクスポート"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("CSVエクスポート機能は開発中です"),
                bgcolor=ft.colors.ORANGE_700
            )
            self.page.snack_bar.open = True
            self.page.update()

