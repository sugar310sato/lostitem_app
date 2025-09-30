from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import json

from apps.config import config

# 各種インスタンス化
db = SQLAlchemy()
csrf = CSRFProtect()

# ログインマネージャーのインスタンス化、設定
login_manager = LoginManager()
login_manager.login_view = "auth.signup"
login_manager.login_message = ""


def create_app(config_key):
    app = Flask(__name__)

    app.config.from_object(config[config_key])

    # カスタムフィルターの追加
    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    
    @app.template_filter('nl2br')
    def nl2br_filter(value):
        if value:
            return value.replace('\n', '<br>')
        return value

    # 各種連携
    db.init_app(app)
    Migrate(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # registerアプリ(ホーム)
    from apps.register import views as register_views

    app.register_blueprint(register_views.register, url_prefix="/")

    # crudアプリ
    from apps.crud import views as crud_views

    app.register_blueprint(crud_views.crud, url_prefix="/crud")

    # authアプリ
    from apps.auth import views as auth_views

    app.register_blueprint(auth_views.auth, url_prefix="/auth")

    # itemsアプリ
    from apps.items import views as items_views

    app.register_blueprint(items_views.items, url_prefix="/items")

    # 同梱物用アプリ
    from apps.bundleditems import views as bundleditems_views

    app.register_blueprint(bundleditems_views.bundleditems, url_prefix="/bundled")

    # 返還関連アプリ
    from apps.return_item import views as return_item_views

    app.register_blueprint(return_item_views.return_item, url_prefix="/return_item")

    # 警察届出
    from apps.police import views as police_views

    app.register_blueprint(police_views.police, url_prefix="/police")

    # 還付処理
    from apps.refund import views as refund_views

    app.register_blueprint(refund_views.refund, url_prefix="/refund")

    # 廃棄処理
    from apps.disposal import views as disposal_views

    app.register_blueprint(disposal_views.disposal, url_prefix="/disposal")

    # 遺失物管理
    from apps.notfound import views as notfound_views

    app.register_blueprint(notfound_views.notfound, url_prefix="/notfound")

    return app
