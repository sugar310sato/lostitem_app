@echo off
echo 拾得物管理システム - Windowsアプリケーション版
echo ================================================
echo.

REM Pythonの仮想環境をアクティベート（存在する場合）
if exist "venv\Scripts\activate.bat" (
    echo 仮想環境をアクティベート中...
    call venv\Scripts\activate.bat
)

REM 必要な依存関係をインストール
echo 依存関係をチェック中...
pip install -r requirements.txt

REM アプリケーションを実行
echo.
echo アプリケーションを起動中...
python windows_app_updated.py

pause 