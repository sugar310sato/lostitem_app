from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, length


class SignUpForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired("ユーザー名は必須です。"),
            length(1, 30, "30文字以内で入力してください。"),
        ],
    )
    password = PasswordField(
        "パスワード",
        validators=[
            DataRequired("パスワードは必須です。"),
        ],
    )
    submit = SubmitField("新規登録")


# ログインフォーム
class LoginForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired("ユーザー名は必須です。"),
            length(1, 30, "30文字以内で入力してください。"),
        ],
    )
    password = PasswordField(
        "パスワード",
        validators=[
            DataRequired("パスワードは必須です。"),
        ],
    )
    submit = SubmitField("ログイン")
