@echo off
chcp 65001 >nul
echo ====================================
echo 拾得物管理システム - インストーラービルド
echo ====================================
echo.

:: 仮想環境のアクティベート
if exist "venv\Scripts\activate.bat" (
    echo [1/5] 仮想環境をアクティベート中...
    call venv\Scripts\activate.bat
    echo OK
) else (
    echo ERROR: venvフォルダが見つかりません
    pause
    exit /b 1
)
echo.

:: PyInstallerで再ビルド
echo [2/5] PyInstallerでEXEファイルをビルド中...
pyinstaller --clean flet_app.spec
if errorlevel 1 (
    echo ERROR: ビルドに失敗しました
    pause
    exit /b 1
)
echo OK
echo.

:: Inno Setupの確認
echo [3/5] Inno Setupの確認...
set "INNO_COMPILER="

:: 一般的なInno Setupパスをチェック
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_COMPILER=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "%INNO_COMPILER%"=="" (
    echo WARNING: Inno Setupが見つかりません
    echo.
    echo Inno Setupをインストールしてください:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo インストール後、このスクリプトを再実行してください。
    echo.
    echo または、手動でInno Setupコンパイラーを開いて
    echo installer.issをビルドしてください。
    pause
    exit /b 0
) else (
    echo Inno Setupが見つかりました: %INNO_COMPILER%
    echo OK
)
echo.

:: インストーラーディレクトリの作成
echo [4/5] インストーラーディレクトリを作成中...
if not exist "installer" mkdir installer
echo OK
echo.

:: Inno Setupでインストーラーをビルド
echo [5/5] インストーラーをビルド中...
"%INNO_COMPILER%" installer.iss
if errorlevel 1 (
    echo ERROR: インストーラーのビルドに失敗しました
    pause
    exit /b 1
)
echo OK
echo.

echo ====================================
echo ビルド完了！
echo ====================================
echo.
echo インストーラー: installer\拾得物管理システム_Setup_1.0.0.exe
echo.
echo 次のステップ:
echo 1. インストーラーの動作を確認
echo 2. 必要に応じてバージョンを更新
echo 3. 配布用にインストーラーを圧縮またはパッケージ化
echo.
pause

