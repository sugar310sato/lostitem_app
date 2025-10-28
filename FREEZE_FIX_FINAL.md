# フリーズ問題の最終修正

## 問題の特定

ターミナルログから、以下の箇所でフリーズしていることが判明：

```
load_users: ユーザー数 = 2
load_users: UI更新前
load_users: self.page存在、更新実行
(ここでフリーズ)
```

## 根本原因

**Fletの制約違反:** `build()`メソッドの実行中に`self.page.update()`を呼び出していた

### 問題のコード構造

```python
def build(self):
    # タブを作成
    user_management_tab = ft.Tab(
        content=self.build_user_management()  # ← ここでbuild_user_management()が実行される
    )
    # ...

def build_user_management(self):
    def load_users():
        # ユーザー一覧を取得してUIを構築
        # ...
        self.page.update()  # ← build()実行中にupdate()を呼ぶとデッドロック！
    
    load_users()  # ← build()の中で呼ばれる
    # ...
```

### なぜデッドロックするのか

1. Fletが`build()`メソッドを呼び出す（UIツリー構築中）
2. `build()`内で`build_user_management()`が呼ばれる
3. `build_user_management()`内で`load_users()`が呼ばれる
4. `load_users()`内で`self.page.update()`を呼ぶ
5. Fletが**既にUIツリー構築中なのに、さらに更新を試みる** → デッドロック

### Fletの正しい動作

- `build()`メソッドはUIコンポーネントを返すだけ
- Fletが`build()`の**完了後**に自動的にUIを更新
- `build()`内で`page.update()`を呼ぶ必要はない（呼んではいけない）

## 修正内容

### 修正前（flet_pages/settings.py）

```python
def load_users():
    # ... ユーザー一覧を構築 ...
    
    if self.page:
        self.page.update()  # ← これが原因！
```

### 修正後（flet_pages/settings.py）

```python
def load_users():
    # ... ユーザー一覧を構築 ...
    
    # build()内ではpage.update()を呼ばない（Fletが自動的に更新）
```

## 修正ファイル

- **flet_pages/settings.py** - 241-260行目
  - `load_users()`関数内の`self.page.update()`を削除

## テスト結果

### 期待されるログ

```
SettingsView.build(): 開始
SettingsView.build(): タブ作成開始
SettingsView.build(): 一般設定タブ作成
build_general_settings: 開始
build_general_settings: 設定取得完了 - 1件
SettingsView.build(): ユーザー管理タブ作成
build_user_management: 開始
build_user_management: 管理者権限あり、ユーザー一覧取得開始
build_user_management: load_users()呼び出し前
load_users: 開始
load_users: get_all_users() 呼び出し前
get_all_users: 開始
get_all_users: DB接続成功
get_all_users: SELECT実行成功
get_all_users: 取得完了 - 2件
get_all_users: DB接続クローズ完了
load_users: ユーザー数 = 2
load_users: UI構築完了  ← 修正後はここまで来る
build_user_management: load_users()呼び出し完了
SettingsView.build(): タブオブジェクト作成
SettingsView.build(): Columnコンテナ作成
SettingsView.build(): 完了
route_change: page.update()完了  ← 成功！
```

## Fletのベストプラクティス

### ❌ やってはいけないこと

```python
class MyControl(ft.UserControl):
    def build(self):
        # build()内でpage.update()を呼ぶ
        self.page.update()  # ← NG
        return ft.Container(...)
```

### ✅ 正しい方法

```python
class MyControl(ft.UserControl):
    def build(self):
        # UIコンポーネントを返すだけ
        return ft.Container(...)
    
    def update_data(self):
        # イベントハンドラなど、build()の外でupdate()を呼ぶ
        self.data = new_data
        self.page.update()  # ← OK
```

### ✅ 動的データの読み込み

```python
class MyControl(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.data = []
    
    def build(self):
        # 初期状態のUIを返す
        return ft.Column(self.data_view)
    
    def did_mount(self):
        # マウント後にデータを読み込む
        self.load_data()
        self.update()
    
    def load_data(self):
        # データベースからデータ取得
        self.data = fetch_from_db()
        # UIコンポーネントを更新
        self.data_view.controls = [...]
```

## 他の注意点

### イベントハンドラ内のupdate()はOK

以下のようなケースは問題ありません：

```python
def on_button_click(e):
    # ボタンクリックなどのイベントハンドラ内
    self.page.update()  # ← OK

ft.ElevatedButton("保存", on_click=on_button_click)
```

### ダイアログ表示時のupdate()もOK

```python
def show_dialog(self):
    dlg = ft.AlertDialog(...)
    self.page.dialog = dlg
    dlg.open = True
    self.page.update()  # ← OK（イベントハンドラから呼ばれる）
```

## まとめ

| 状況 | page.update() | 理由 |
|------|--------------|------|
| `build()`内 | ❌ NG | Fletが既にUIツリー構築中 |
| イベントハンドラ内 | ✅ OK | イベントループから呼ばれる |
| `did_mount()`内 | ✅ OK | コンポーネントマウント後 |
| 非同期処理完了後 | ✅ OK | データ取得完了時など |

## 参考資料

- Flet公式ドキュメント: https://flet.dev/docs/
- UserControl: https://flet.dev/docs/controls/usercontrol

## 修正日時

2024-10-13

---

## 今後の改善提案

1. **遅延読み込みの実装**
   - ユーザー一覧を初期表示せず、タブ選択時に読み込む
   - `did_mount()`を使ってマウント後にデータ取得

2. **ローディング表示**
   - データ取得中はローディングインジケーターを表示
   - ユーザーエクスペリエンスの向上

3. **エラーハンドリングの強化**
   - データ取得失敗時のフォールバック表示
   - リトライ機能の実装

