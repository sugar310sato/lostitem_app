@echo off
echo 拾得物管理システム (Flask) を起動しています...
echo.

REM 仮想環境をアクティベート
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo 仮想環境をアクティベートしました
) else (
    echo 警告: 仮想環境が見つかりません
)

echo.
echo 環境変数を設定中...
set FLASK_APP=run_flask_app:app
set FLASK_ENV=development

echo.
echo Flaskアプリケーションを起動中...
flask run --host=0.0.0.0 --port=5000

pause
