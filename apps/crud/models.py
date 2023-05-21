from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from apps.app import db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"
    # カラム
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, index=True)
    password_hash = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # パスワードセットのプロパティ
    @property
    def password(self):
        raise AttributeError("読み取り不可")

    # パスワードをセット
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # パスワードチェック
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 名前の重複チェック
    def is_duplicate_username(self):
        return User.query.filter_by(username=self.username).first() is not None


# ログインしているユーザー情報を取得する関数を作成
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
