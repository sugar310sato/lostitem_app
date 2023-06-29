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
