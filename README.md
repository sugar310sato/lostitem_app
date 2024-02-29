# lostitem_app

## アプリの概要

拾得物の管理を行うアプリです。

## セットアップ方法

### 仮想環境の作成

以下のコマンドで任意の仮想環境を作成し、ライブラリのインストールを行います。

```
python -m venv   任意の名前
./仮想環境名/Script/activate
pip install -r requirements.txt
```

### config.py の作成

apps 直下に config.py というファイルを作成し、config.sample の内容をコピーします。  
シークレットキー、CSRF のシークレットキーの内容を任意の 20 桁の英数字に変更してください。
また、6 行目の LAMBDA_ENDPOINT に lambda への URL を張り付けてください。

### .env の作成

lost_item 直下に、.env というファイルを作成してください。ファイルの中身は、次の通りです。

```
FLASK_APP=apps.app:create_app("local")
FLASK_ENV=test
```

### データベース構築場所の選択

初期値では、DB を lostitem_app 直下に製作するようになっています。これを変更するために、

### img2txt の導入

img2txt のモデルである Coca を利用します。register/model_folder 直下に model.pth として保存してください。

### DB の作成

以下のコマンドを入力し、DB を作成してください。

```
flask db migrate
flaks db upgrade
```

DB を初期化したい場合は、以下のコマンドを入力してください。

```
flask db downgrade
flask db upgrade
```

DB の作成がうまくいかない場合、migrations フォルダを削除して、以下のコマンドを入力してください。

```
flask db init
flask db migrate
flask db upgrade
```

### アプリの実行

以下のコマンドでアプリを実行してください。

```
flask run
```
