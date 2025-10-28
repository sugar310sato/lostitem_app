# ログイン後の即時UI更新修正

## 問題

ログイン後すぐにホーム画面でログイン者情報やログアウトボタンが表示されない。
他のページに一度遷移しないとサイドバーが更新されない。

## 原因

1. **初期レイアウトの二重構築**
   - アプリ起動時に初期レイアウトでサイドバーを作成
   - `route_change`でも毎回サイドバーを作成
   - 初期レイアウトが残っているため、ログイン後も古いサイドバーが表示される

2. **グローバル変数の更新タイミング**
   - `current_user`は更新されるが、既に描画済みのUIは更新されない
   - `page.go("/")`を呼んでも、既存のビューが残っている

## 修正内容

### 1. 初期レイアウトの削除

**修正前（flet_app.py）:**
```python
# 初期レイアウト: 左サイド + 右メイン
layout = ft.Row([
    build_sidebar(page, current_user=current_user, on_login=show_login_dialog, on_logout=logout),
    main_container,
], expand=True)

page.on_route_change = route_change
page.add(layout)  # ← 初期レイアウトを追加
page.go(page.route or "/")
```

**修正後（flet_app.py）:**
```python
# ルーティング設定
page.on_route_change = route_change

# 初期表示（route_changeでレイアウトが構築される）
page.go(page.route or "/")
```

### 2. 不要なコンテナの削除

```python
# 削除: main_container = ft.Container(expand=True)
```

### 3. ログイン・ログアウト処理の簡素化

**ログイン成功時:**
```python
def on_login_success(user):
    global current_user
    current_user = user
    print(f"ログイン成功: {user}")
    page.snack_bar = ft.SnackBar(
        ft.Text(f"ようこそ、{user.get('display_name', user.get('username'))}さん"),
        bgcolor=ft.colors.GREEN_700
    )
    page.snack_bar.open = True
    # ログイン成功後、ホームに戻る（route_changeが呼ばれて最新のcurrent_userでサイドバーが再構築される）
    page.go("/")
```

**ログアウト時:**
```python
def logout():
    global current_user
    current_user = None
    page.snack_bar = ft.SnackBar(ft.Text("ログアウトしました"), bgcolor=ft.colors.BLUE_700)
    page.snack_bar.open = True
    # ログアウト後、ホームに戻る（route_changeが呼ばれて最新のcurrent_userでサイドバーが再構築される）
    page.go("/")
```

### 4. デバッグログの改善

```python
def route_change(route):
    print(f"route_change: {page.route} - current_user: {current_user.get('username') if current_user else 'None'}")
    page.views.clear()
    # ... 各ルートの処理 ...
    page.update()
    print(f"route_change: 完了 - {page.route}")
```

## 動作の流れ

### 修正前
```
1. アプリ起動
2. 初期レイアウト作成（current_user=None でサイドバー構築）
3. route_change("/") 実行（新しいビューを追加）
4. ログイン成功
5. current_user 更新
6. page.go("/") 実行
7. route_change("/") 実行（新しいサイドバーを作成）
8. ❌ 初期レイアウトのサイドバーが残っているため、古い状態が表示される
```

### 修正後
```
1. アプリ起動
2. route_change("/") 実行（current_user=None でサイドバー構築）
3. ログイン成功
4. current_user 更新
5. page.go("/") 実行
6. route_change("/") 実行
   - page.views.clear() で既存のビューをクリア
   - 最新の current_user でサイドバーを再構築
7. ✅ 最新のログイン状態が即座に反映される
```

## 重要なポイント

### route_change の動作
```python
def route_change(route):
    page.views.clear()  # ← 重要：既存のビューをすべてクリア
    
    if page.route == "/":
        page.views.append(
            ft.View("/", [
                ft.Row([
                    # 最新の current_user でサイドバーを構築
                    build_sidebar(page, current_user=current_user, ...),
                    # ...
                ])
            ])
        )
    # ...
    page.update()
```

### なぜ修正が有効か

1. **ビューのクリア**: `page.views.clear()`で古いUIをすべて削除
2. **再構築**: 最新の`current_user`で新しいサイドバーを構築
3. **一貫性**: すべてのページ遷移で同じ仕組みを使用

## テスト結果

### 期待される動作

1. **ログイン時**
   ```
   route_change: / - current_user: None
   ログイン成功: {'id': 2, 'username': 'admin', ...}
   route_change: / - current_user: admin  ← current_userが更新されている
   route_change: 完了 - /
   ```
   → サイドバーに「管理者」とログアウトボタンが即座に表示される

2. **ログアウト時**
   ```
   route_change: / - current_user: None  ← current_userがNoneに戻っている
   route_change: 完了 - /
   ```
   → サイドバーに「未ログイン」とログインボタンが即座に表示される

## ベストプラクティス

### ✅ 推奨される方法

```python
# ルーティングでUIを管理
page.on_route_change = route_change
page.go("/")

# ルートチェンジで常に最新の状態でUIを構築
def route_change(route):
    page.views.clear()  # 既存のビューをクリア
    # ... 最新のグローバル変数を使ってUIを構築 ...
    page.update()
```

### ❌ 避けるべき方法

```python
# 初期レイアウトを別途作成
initial_layout = build_ui()
page.add(initial_layout)  # ← これが残り続ける

# 後でroute_changeで新しいUIを追加
def route_change(route):
    # 初期レイアウトは削除されない
    page.views.append(...)  # ← 二重構築
```

## 修正日時

2024-10-13

## 関連ファイル

- `flet_app.py` - メインアプリケーション
- `flet_pages/home.py` - ホーム画面・サイドバー
- `flet_pages/login_page.py` - ログイン機能

