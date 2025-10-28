# フリーズ問題のデバッグ - 修正サマリー

## 追加したデバッグログ

設定画面でフリーズする問題を特定するため、以下の箇所に詳細なデバッグログを追加しました。

### 1. flet_app.py
- `/settings`ルートへの遷移時
  - `current_user`の値
  - `SettingsView`作成前後
  - `View`追加後
  - `page.update()`前後

### 2. flet_pages/settings.py

#### SettingsViewクラス
- `__init__()` - インスタンス作成時のユーザー情報
- `build()` - ビルド処理の各ステップ
- `build_general_settings()` - 一般設定タブの構築
- `build_user_management()` - ユーザー管理タブの構築

#### データベースアクセス
- `get_general_settings()` - 設定取得
  - DB接続
  - テーブル作成
  - カラムチェック
  - データ取得
  - 接続クローズ

- `get_all_users()` - ユーザー一覧取得
  - DB接続
  - SELECT実行
  - データ取得
  - 接続クローズ

#### UI更新
- `load_users()` - ユーザー一覧の表示
  - データ取得
  - UI構築
  - page.update()

## デバッグ手順

### 1. アプリケーションの起動

```bash
python flet_app.py
```

ターミナルのログを注意深く確認してください。

### 2. ログインとテスト

1. **ログイン**
   - ユーザー名: `admin`
   - パスワード: `Admin1`
   - ログ: `ログイン成功: {'id': X, 'username': 'admin', ...}`

2. **設定画面へ移動**
   - サイドバーから「設定」をクリック
   - ログの流れを確認

### 3. ログ確認のポイント

**正常な場合:**
```
route_change: /settings - current_user = {'id': 2, 'username': 'admin', ...}
route_change: SettingsView作成前
SettingsView.__init__(): current_user = {'id': 2, 'username': 'admin', ...}
SettingsView.build(): 開始
SettingsView.build(): タブ作成開始
SettingsView.build(): 一般設定タブ作成
build_general_settings: 開始
build_general_settings: get_general_settings()呼び出し前
get_general_settings: 開始
get_general_settings: DB接続開始 - C:\...\lostitem.db
get_general_settings: DB接続成功
...
SettingsView.build(): 完了
route_change: SettingsView作成完了
route_change: /settings View追加完了
route_change: page.update()前 - route = /settings
route_change: page.update()完了
```

**フリーズの場合:**
最後に表示されたログを確認してください。

## 想定される問題と対処

### 問題1: データベース接続でフリーズ

**症状:**
```
get_general_settings: DB接続開始 - C:\...\lostitem.db
(ここで止まる)
```

**原因:** データベースファイルがロックされている

**対処:**
1. 他のPythonプロセスを終了
   ```bash
   taskkill /F /IM python.exe
   ```

2. ジャーナルファイルを削除
   ```bash
   del lostitem.db-journal
   del lostitem.db-wal
   ```

3. データベースを整合性チェック
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('lostitem.db'); print(conn.execute('PRAGMA integrity_check').fetchone()); conn.close()"
   ```

### 問題2: テーブル操作でフリーズ

**症状:**
```
get_general_settings: settingsテーブル作成
(ここで止まる)
```

**原因:** テーブル作成/ALTER文でロック

**対処:**
1. WALモードを無効化
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('lostitem.db'); conn.execute('PRAGMA journal_mode=DELETE'); conn.commit(); conn.close()"
   ```

2. データベースのバックアップと再作成
   ```bash
   copy lostitem.db lostitem_backup.db
   python -c "import sqlite3; conn = sqlite3.connect('lostitem.db'); conn.execute('VACUUM'); conn.close()"
   ```

### 問題3: page.update()でフリーズ

**症状:**
```
route_change: page.update()前 - route = /settings
(ここで止まる)
```

**原因:** Fletの描画処理でデッドロック

**対処:**
1. Fletを最新版に更新
   ```bash
   pip install --upgrade flet
   ```

2. 非同期更新に変更（コード修正が必要）

### 問題4: 即座にフリーズ

**症状:** 設定ボタンを押した瞬間にフリーズ、ログが何も出ない

**原因:** route_change自体が呼ばれていない、または別の問題

**対処:**
1. `route_change`の最初にログ追加
   ```python
   def route_change(route):
       print(f"route_change: 開始 - route = {page.route}")
       page.views.clear()
       ...
   ```

## ログ出力のファイル保存

ログをファイルに保存して詳細に分析する場合：

```bash
# 標準出力とエラー出力の両方をファイルに保存
python flet_app.py > debug_log.txt 2>&1

# ログファイルを確認
type debug_log.txt
```

## 次のステップ

ログを確認して、以下の情報を報告してください：

1. **最後に表示されたログメッセージ**
2. **エラーメッセージ（あれば）**
3. **フリーズまでの時間**
4. **タスクマネージャーでのCPU/メモリ使用状況**

この情報を元に、具体的な修正を行います。

## 一時的な回避策

設定画面を使わずに直接データベースを操作する方法：

### パスワード変更
```bash
python -c "import sqlite3, hashlib; conn = sqlite3.connect('lostitem.db'); hashed = hashlib.sha256(b'NewPassword1').hexdigest(); conn.execute('UPDATE users SET password = ?, password_hash = ? WHERE username = ?', (hashed, hashed, 'admin')); conn.commit(); conn.close(); print('パスワード変更完了')"
```

### ユーザー追加
```bash
python -c "import sqlite3, hashlib; conn = sqlite3.connect('lostitem.db'); hashed = hashlib.sha256(b'Password1').hexdigest(); conn.execute('INSERT INTO users (username, password, password_hash, display_name, role, email) VALUES (?, ?, ?, ?, ?, ?)', ('testuser', hashed, hashed, 'テストユーザー', 'user', 'test@example.com')); conn.commit(); conn.close(); print('ユーザー追加完了')"
```

## 関連ファイル

- `flet_app.py` - メインアプリ（デバッグログ追加）
- `flet_pages/settings.py` - 設定画面（デバッグログ追加）
- `DEBUG_INSTRUCTIONS.md` - 詳細なデバッグ手順
- `FREEZE_DEBUG_SUMMARY.md` - このファイル

