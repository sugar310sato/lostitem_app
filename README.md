# lostitem_app
## アプリの概要
拾得物の管理を行うアプリです。

## セットアップ方法
### 仮想環境の作成
以下のコマンドで任意の仮想環境を作成し、ライブラリのインストールを行います。  
`python -m venv   任意の名前`  
`./仮想環境名/Script/activate`  
`pip install -r requirements.txt`

### config.pyの作成
apps直下にconfig.pyというファイルを作成し、config.sampleの内容をコピーします。  
シークレットキー、CSRFのシークレットキーの内容を任意の20桁の英数字に変更してください。

### .envの作成
lost_item直下に、.envというファイルを作成してください。ファイルの中身は、次の通りです。  
```
FLASK_APP=apps.app:create_app("local")
FLASK_ENV=development
FLASK_DEBUG=1
```

### images、renamed_imagesの作成
apps直下に、images、renamed_imagesフォルダを作ってください。
[2023/08/23追記]
apps直下にPDFFileというフォルダを作り、さらにその下に、
disposal_pdf、police_pdf、refund_list_pdf、return_item_pdfというフォルダを作成してください。
これらのフォルダには、作成したPDFファイルが格納されます。


### DBの作成
以下のコマンドを入力し、DBを作成してください。  
`flask db migrate`    
`flaks db upgrade`  
DBを初期化したい場合は、以下のコマンドを入力してください。  
`flask db downgrade`  
`flask db upgrade`  

DBの作成がうまくいかない場合、migrationsフォルダを削除して、以下のコマンドを入力してください。  
`flask db init`  
`flask db migrate`  
`flask db upgrade`  

### アプリの実行
以下のコマンドでアプリを実行してください。
`flask run`
