from datetime import datetime

from werkzeug.security import generate_password_hash

from apps.app import db


class User(db.Model):
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
