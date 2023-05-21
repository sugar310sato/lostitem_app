from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user

from apps.app import db
from apps.auth.forms import LoginForm, SignUpForm
from apps.crud.models import User

auth = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# indexエンドポイント
@auth.route("/")
def index():
    return render_template("auth/index.html")


# signup
@auth.route("/signup", methods=["POST", "GET"])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password=form.password.data,
        )

        # 名前の重複チェック
        if user.is_duplicate_username():
            flash("指定のユーザー名は登録済みです。")
            return redirect(url_for("auth.signup"))

        # 情報の登録
        db.session.add(user)
        db.session.commit()
        # ユーザー情報のセッションへの格納
        login_user(user)

        # nextキーが存在し、値がない場合はユーザー一覧へ
        next_ = request.args.get("next")
        if next_ is None or not next_.startswith("/"):
            next_ = url_for("crud.users")
        return redirect(next_)

    return render_template("auth/signup.html", form=form)


# ログイン
@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for("crud.users"))

        flash("名前かパスワードが不正です。")
    return render_template("auth/login.html", form=form)
