# 統計・分析機能

## 概要

拾得物管理システムに統計・分析機能を追加しました。
データを視覚的に分析し、月次レポートの出力が可能です。

## 主な機能

### 1. 基本統計カード
- **拾得物総数**: 全拾得物の件数
- **返還済み**: 返還完了した件数
- **返還率**: 返還率のパーセンテージ
- **遺失物**: 遺失物の件数

### 2. 期間別表示
- **日別**: 過去30日間のデータ
- **月別**: 過去12ヶ月のデータ
- **年別**: 年単位のデータ

### 3. 視覚的なグラフ

#### 折れ線グラフ（棒グラフ表示）
- 期間別の拾得物件数の推移を表示
- 日/月/年で切り替え可能

#### 時間帯別分布（横棒グラフ）
- 3時間ごとの拾得物件数
- どの時間帯に多く拾得されるかを分析

#### 物品カテゴリ別（円グラフ風）
- 上位6カテゴリを表示
- カテゴリごとの件数と割合を表示

### 4. レポート機能
- **月次レポート出力**: PDF形式での出力（開発中）
- **CSVエクスポート**: データのCSV出力（開発中）

## 使い方

### 統計画面へのアクセス
1. サイドバーから「統計」をクリック
2. 統計画面が表示されます

### 期間の切り替え
- 画面上部のタブで「日別」「月別」「年別」を切り替え
- グラフが自動的に更新されます

### ホームへ戻る
- 左上の「←」ボタンでホーム画面に戻ります

## デザインの特徴

### シンプル&モダン
- **カード形式**: 統計情報を見やすいカードで表示
- **アイコン**: 直感的なアイコンを使用
- **カラー**: ブルー、グリーン、オレンジの配色

### レスポンシブ
- グラフは横スクロール対応
- 画面サイズに応じて調整

### ユーザーフレンドリー
- ツールチップでデータ詳細を表示
- クリーンで読みやすいレイアウト

## 実装詳細

### ファイル構成
```
flet_pages/
├── statistics.py      # 統計画面のメインコード
├── home.py           # サイドバー（統計メニュー追加）
└── ...

flet_app.py           # ルーティング（/stats追加）
```

### データ取得

#### 基本統計
```python
def get_basic_stats(self, cur):
    # 拾得物総数
    cur.execute("SELECT COUNT(*) FROM lost_items")
    
    # 返還済み件数
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE refund_situation = '済'")
    
    # 返還率計算
    return_rate = (returned / total) * 100
```

#### 期間別データ
```python
# 日別（過去30日）
for i in range(30, -1, -1):
    date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE DATE(get_item) = ?", (date,))

# 月別（過去12ヶ月）
cur.execute("SELECT COUNT(*) FROM lost_items WHERE strftime('%Y-%m', get_item) = ?", (date,))

# 年別
cur.execute("SELECT strftime('%Y', get_item) as year, COUNT(*) FROM lost_items GROUP BY year")
```

#### 時間帯別分布
```python
# 3時間ごとに集計
for hour in range(0, 24, 3):
    cur.execute(
        "SELECT COUNT(*) FROM lost_items WHERE get_item_hour >= ? AND get_item_hour < ?",
        (hour, hour + 3)
    )
```

#### カテゴリ別分布
```python
cur.execute("""
    SELECT item_class_L, COUNT(*) 
    FROM lost_items 
    WHERE item_class_L IS NOT NULL AND item_class_L != ''
    GROUP BY item_class_L 
    ORDER BY COUNT(*) DESC 
    LIMIT 6
""")
```

### グラフの種類

#### 1. 折れ線グラフ（棒グラフ表示）
```python
def create_line_chart(self, data):
    # データの最大値を取得
    max_value = max([d['value'] for d in data])
    
    # 各データポイントを棒グラフで表示
    for item in data:
        height = (item['value'] / max_value) * 150
        # 棒を描画
```

#### 2. 横棒グラフ
```python
def create_bar_chart(self, data):
    # ラベル + 横棒 + 数値の行を作成
    for item in data:
        width_percent = (item['value'] / max_value) * 100
        # 横棒を描画
```

#### 3. 円グラフ風（リスト表示）
```python
def create_pie_chart(self, data):
    # カテゴリごとにカラーボックス + ラベル + パーセンテージ
    for i, item in enumerate(data):
        percentage = (item['value'] / total) * 100
        # 色付きボックスとテキストを表示
```

## カスタマイズ

### グラフの色を変更
```python
colors = [
    ft.colors.BLUE_400,
    ft.colors.GREEN_400,
    ft.colors.ORANGE_400,
    ft.colors.PURPLE_400,
    ft.colors.RED_400,
    ft.colors.TEAL_400,
]
```

### 統計カードのカスタマイズ
```python
def create_stat_card(self, title, value, icon, color):
    return ft.Container(
        content=ft.Column([...]),
        padding=20,
        bgcolor=ft.colors.WHITE,
        border_radius=12,
        width=280,
        shadow=ft.BoxShadow(...),
    )
```

### 期間の変更
```python
# 日別の日数を変更
for i in range(30, -1, -1):  # 30日 → 60日など

# 月別の月数を変更
for i in range(12, -1, -1):  # 12ヶ月 → 24ヶ月など
```

## 今後の拡張

### Phase 1（開発中）
- [x] 基本統計の表示
- [x] 期間別グラフ
- [x] 時間帯別分布
- [x] カテゴリ別分布
- [ ] 月次レポートPDF出力
- [ ] CSVエクスポート

### Phase 2（予定）
- [ ] より高度なグラフライブラリの導入
  - Plotlyなどの本格的なグラフライブラリ
  - インタラクティブなグラフ
- [ ] フィルター機能
  - カテゴリでフィルター
  - 日付範囲の指定
- [ ] 比較機能
  - 前月との比較
  - 前年同月との比較

### Phase 3（将来）
- [ ] ダッシュボード機能
  - リアルタイム更新
  - 重要指標のアラート
- [ ] 予測分析
  - 拾得物の傾向予測
  - 季節性の分析
- [ ] カスタムレポート
  - ユーザー定義のレポート
  - スケジュール自動出力

## トラブルシューティング

### グラフが表示されない
1. データベースにデータがあるか確認
2. ターミナルのエラーログを確認
3. `did_mount()`が呼ばれているか確認

### 期間切り替えが動かない
- `on_period_change`イベントハンドラを確認
- `self.period`の値を確認

### レポート出力エラー
- 現在は開発中の機能です
- スナックバーで通知されます

## 使用例

```python
# 統計画面を表示
page.go("/stats")

# 期間を月別に変更
self.period = "month"
self.load_statistics()

# 月次レポートを出力
self.export_monthly_report(None)
```

## パフォーマンス

- データベースクエリは効率的に設計
- グラフは軽量な実装
- ページング未実装（データ量が多い場合は要改善）

## セキュリティ

- SQLインジェクション対策済み（パラメータ化クエリ）
- データベースタイムアウト設定
- エラーハンドリング実装

## 修正履歴

### 2024-10-14
- 統計機能の初期実装
- 日/月/年別の表示機能
- 時間帯別・カテゴリ別グラフ
- 基本統計カード
- ホームに戻るボタン追加
- サイドバーのスクロール無効化

