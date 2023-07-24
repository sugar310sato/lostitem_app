from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

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

    return app
