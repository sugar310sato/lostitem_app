# デバッグ手順

## フリーズ問題の調査

設定画面でフリーズする問題を調査するため、詳細なデバッグログを追加しました。

## 実行方法

1. **アプリを起動**
   ```bash
   python flet_app.py
   ```

2. **管理者でログイン**
   - ユーザー名: `admin`
   - パスワード: `Admin1`

3. **設定ボタンをクリック**
   - サイドバーから「設定」を選択

4. **ターミナルのログを確認**
   - どこまで実行されているか確認
   - エラーメッセージを確認

## ログの見方

### 正常な場合の流れ

```
SettingsView.build(): 開始
SettingsView.build(): タブ作成開始
SettingsView.build(): 一般設定タブ作成
build_general_settings: 開始
build_general_settings: get_general_settings()呼び出し前
get_general_settings: 開始
get_general_settings: DB接続開始 - C:\...\lostitem.db
get_general_settings: DB接続成功
get_general_settings: settingsテーブル作成
get_general_settings: settingsテーブル作成完了
get_general_settings: updated_atカラムチェック
get_general_settings: updated_atカラム存在
get_general_settings: staff_listチェック
get_general_settings: staff_list存在
get_general_settings: 全設定取得
get_general_settings: 設定取得完了 - X件
get_general_settings: DB接続クローズ完了
build_general_settings: 設定取得完了 - X件
SettingsView.build(): ユーザー管理タブ作成
build_user_management: 開始
build_user_management: 管理者権限あり、ユーザー一覧取得開始
build_user_management: load_users()呼び出し前
load_users: 開始
load_users: get_all_users() 呼び出し前
get_all_users: 開始
get_all_users: DB接続開始 - C:\...\lostitem.db
get_all_users: DB接続成功
get_all_users: SELECT実行前
get_all_users: SELECT実行成功
get_all_users: 取得完了 - X件
get_all_users: finally節
get_all_users: DB接続クローズ完了
load_users: ユーザー数 = X
load_users: UI更新前
load_users: self.page存在、更新実行
load_users: UI更新完了
build_user_management: load_users()呼び出し完了
SettingsView.build(): タブオブジェクト作成
SettingsView.build(): Columnコンテナ作成
SettingsView.build(): 完了
```

### フリーズ箇所の特定

最後に表示されたログメッセージを確認してください。

#### 例1: DB接続でフリーズ
```
get_general_settings: DB接続開始 - C:\...\lostitem.db
(ここで止まる)
```
→ データベースファイルがロックされている可能性

#### 例2: SELECT実行でフリーズ
```
get_all_users: SELECT実行前
(ここで止まる)
```
→ データベーステーブルに問題がある可能性

#### 例3: UI更新でフリーズ
```
load_users: self.page存在、更新実行
(ここで止まる)
```
→ Fletの更新処理に問題がある可能性

## 対処方法

### データベースロックの解消

1. **他のプロセスを終了**
   ```bash
   # Pythonプロセスをすべて終了
   taskkill /F /IM python.exe
   ```

2. **データベースファイルの確認**
   - `lostitem.db-journal`ファイルが存在する場合は削除
   - `lostitem.db-wal`ファイルが存在する場合は削除

3. **データベースのバックアップ**
   ```bash
   copy lostitem.db lostitem_backup.db
   ```

### データベースの整合性チェック

```bash
python -c "import sqlite3; conn = sqlite3.connect('lostitem.db'); print(conn.execute('PRAGMA integrity_check').fetchone()); conn.close()"
```

### WALモードの無効化（一時的）

```bash
python -c "import sqlite3; conn = sqlite3.connect('lostitem.db'); conn.execute('PRAGMA journal_mode=DELETE'); conn.close()"
```

## ログ出力の保存

ログをファイルに保存する場合：

```bash
python flet_app.py > debug_log.txt 2>&1
```

## トラブルシューティング

### 問題1: データベースが見つからない
**症状:** `DB接続開始`の後にエラー

**対処:**
1. `lostitem.db`ファイルが存在するか確認
2. パスが正しいか確認
3. 権限があるか確認

### 問題2: タイムアウト
**症状:** `DB接続開始`の後、10秒後にタイムアウトエラー

**対処:**
1. データベースファイルのロックを解除
2. ウイルス対策ソフトを一時的に無効化
3. データベースファイルを別の場所にコピーして試す

### 問題3: メモリ不足
**症状:** アプリ全体がフリーズ

**対処:**
1. タスクマネージャーでメモリ使用量を確認
2. 他のアプリケーションを終了
3. PCを再起動

## 次のステップ

ログを確認後、以下の情報を提供してください：

1. **最後に表示されたログメッセージ**
2. **エラーメッセージ（あれば）**
3. **フリーズまでの時間（即座 / 数秒後 / 10秒後など）**

この情報を元に、より具体的な修正を行います。

