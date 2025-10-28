import flet as ft
from flet_pages.money_registration import MoneyRegistrationView


def main(page: ft.Page):
    page.title = "金種登録プレビュー"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 900
    page.window_height = 700
    
    def on_complete(money_data):
        """金種登録完了時の処理"""
        print("=" * 50)
        print("金種登録が完了しました")
        print("=" * 50)
        
        total = 0
        for key, value in money_data.items():
            if key == "memorial_coins":
                print("\n【記念硬貨】")
                for coin in value:
                    print(f"  - {coin['name']}: ¥{coin['amount']:,}")
                    total += coin['amount']
            else:
                from apps.config import MONEY_TYPES
                for name, unit_value in MONEY_TYPES:
                    if name == key:
                        amount = value * unit_value
                        print(f"{name}: {value}枚 = ¥{amount:,}")
                        total += amount
                        break
        
        print(f"\n合計金額: ¥{total:,}")
        print("=" * 50)
        
        # 成功メッセージを表示
        page.snack_bar = ft.SnackBar(
            ft.Text(f"金種登録完了！合計: ¥{total:,}"),
            bgcolor=ft.colors.GREEN_700
        )
        page.snack_bar.open = True
        page.update()
    
    def on_cancel():
        """キャンセル時の処理"""
        print("金種登録がキャンセルされました")
        page.snack_bar = ft.SnackBar(
            ft.Text("金種登録をキャンセルしました"),
            bgcolor=ft.colors.ORANGE_700
        )
        page.snack_bar.open = True
        page.update()
    
    # 初期データ（既存の金種データがある場合）
    initial_data = {
        "一万円札": 2,
        "千円札": 5,
        "百円硬貨": 10,
        "十円硬貨": 5,
    }
    
    # 金種登録ビューを作成
    money_view = MoneyRegistrationView(
        on_complete=on_complete,
        on_cancel=on_cancel,
        initial_data=initial_data  # 既存データをロード
    )
    
    # ページにコンテンツを追加（スクロールなし）
    page.add(money_view)


if __name__ == "__main__":
    ft.app(target=main)

