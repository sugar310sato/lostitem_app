# アプリケーションの強制終了方法

## 状況
ターミナルがCtrl+CやCtrl+Zで終了できない場合の対処方法

## 方法1: タスクマネージャーで終了（推奨）

### 手順
1. **タスクマネージャーを開く**
   - `Ctrl + Shift + Esc` を押す
   - または `Ctrl + Alt + Delete` → タスクマネージャー

2. **Pythonプロセスを見つける**
   - 「プロセス」タブを選択
   - 「Python」または「python.exe」を探す
   - 複数ある場合は、CPU使用率やメモリ使用量が高いものを選択

3. **プロセスを終了**
   - プロセスを右クリック → 「タスクの終了」
   - または選択して「タスクの終了」ボタンをクリック

## 方法2: PowerShellで強制終了

### 新しいPowerShellウィンドウを開く
`Win + X` → `Windows PowerShell (管理者)` または `ターミナル (管理者)`

### コマンド実行

#### すべてのPythonプロセスを終了
```powershell
taskkill /F /IM python.exe
```

#### 特定のPythonプロセスを終了
```powershell
# プロセスIDを確認
Get-Process python

# プロセスIDを指定して終了（例: PID 12345）
taskkill /F /PID 12345
```

## 方法3: ターミナルウィンドウを閉じる

### 手順
1. **ターミナルウィンドウの×ボタンをクリック**
2. 「実行中のプロセスを終了しますか？」と聞かれたら「はい」

## 方法4: コマンドプロンプトから終了

### 新しいコマンドプロンプトを開く
`Win + R` → `cmd` → Enter

### コマンド実行
```cmd
taskkill /F /IM python.exe
```

## 完全クリーンアップ（すべての関連プロセスを終了）

新しいPowerShellウィンドウで：

```powershell
# すべてのPythonプロセスを終了
taskkill /F /IM python.exe

# Fletが使用する可能性のあるプロセスも終了
taskkill /F /IM pythonw.exe

# プロセスが終了したか確認
Get-Process python -ErrorAction SilentlyContinue
Get-Process pythonw -ErrorAction SilentlyContinue
```

## データベースのクリーンアップ

プロセス終了後、データベースロックファイルを削除：

```powershell
# プロジェクトディレクトリに移動
cd C:\Users\sato\Documents\github\lostitem_app

# ロックファイルを削除
Remove-Item lostitem.db-journal -ErrorAction SilentlyContinue
Remove-Item lostitem.db-wal -ErrorAction SilentlyContinue
Remove-Item lostitem.db-shm -ErrorAction SilentlyContinue

# 削除したファイルを確認
Write-Host "クリーンアップ完了"
```

## 次回の起動前チェック

```powershell
# Pythonプロセスが残っていないか確認
Get-Process python -ErrorAction SilentlyContinue

# 何も表示されなければOK
# プロセスが表示された場合は再度終了
```

## トラブルシューティング

### 問題: タスクマネージャーでPythonが見つからない
**対処:**
- 「詳細」タブを確認
- 「python.exe」または「pythonw.exe」を探す
- CPU列でソートして使用率の高いものを探す

### 問題: プロセスが終了しない
**対処:**
```powershell
# より強力な終了コマンド
Stop-Process -Name python -Force
Stop-Process -Name pythonw -Force

# または管理者権限で
taskkill /F /T /IM python.exe
```

### 問題: ターミナルが完全にフリーズ
**対処:**
1. ターミナルウィンドウを右クリック
2. 「閉じる」を選択
3. 強制終了の確認が出たら「はい」

## 予防策

### 1. 適切な終了処理の追加

アプリに終了ボタンを追加する場合：

```python
def on_close(e):
    # カメラを解放
    if hasattr(page, 'camera'):
        page.camera.release()
    
    # データベース接続をクローズ
    # ...
    
    # アプリを終了
    page.window_destroy()

ft.ElevatedButton("終了", on_click=on_close)
```

### 2. タイムアウトの設定

```python
# すべてのDB接続にタイムアウトを設定（既に実装済み）
conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
```

### 3. 例外処理の強化

```python
try:
    # 処理
except KeyboardInterrupt:
    print("Ctrl+Cで終了")
    cleanup()
    sys.exit(0)
except Exception as e:
    print(f"エラー: {e}")
    cleanup()
    raise
```

## クイックコマンド集

### PowerShellで実行

```powershell
# すべて終了してクリーンアップ
taskkill /F /IM python.exe; taskkill /F /IM pythonw.exe; Remove-Item C:\Users\sato\Documents\github\lostitem_app\lostitem.db-* -ErrorAction SilentlyContinue
```

### 1行で実行（コピペ用）

```powershell
taskkill /F /IM python.exe /T 2>$null; Remove-Item lostitem.db-journal,lostitem.db-wal,lostitem.db-shm -ErrorAction SilentlyContinue; Write-Host "クリーンアップ完了"
```

## 参考: Windowsのキーボードショートカット

| ショートカット | 動作 |
|---------------|------|
| `Ctrl + C` | プロセス中断（SIGINT） |
| `Ctrl + Z` | プロセス一時停止（Unix系のみ、Windowsでは無効） |
| `Ctrl + Shift + Esc` | タスクマネージャー起動 |
| `Alt + F4` | ウィンドウを閉じる |
| `Ctrl + W` | タブ/ウィンドウを閉じる（ターミナルによる） |

## 注意事項

⚠️ **データ保護**
- 強制終了するとデータが失われる可能性があります
- 重要な作業中は、できるだけ正常終了を試みてください

⚠️ **データベース整合性**
- 強制終了後は必ずロックファイルを削除してください
- データベースの整合性チェックを推奨：
  ```powershell
  python -c "import sqlite3; conn = sqlite3.connect('lostitem.db'); print(conn.execute('PRAGMA integrity_check').fetchone()); conn.close()"
  ```

