from flask import Blueprint, redirect, render_template, url_for

from apps.app import db
from apps.crud.forms import UserForm
from apps.crud.models import User

crud = Blueprint(
    "crud",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# indexエンドポイント
@crud.route("/")
def index():
    return render_template("crud/index.html")


# ユーザー新規登録
@crud.route("/users/new", methods=["GET", "POST"])
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password=form.password.data,
        )
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("crud.users"))
    return render_template("crud/create.html", form=form)


# ユーザー一覧
@crud.route("/users")
def users():
    users = User.query.all()
    return render_template("crud/index.html", users=users)


# ユーザー編集
@crud.route("/users/<user_id>", methods=["POST", "GET"])
def edit_user(user_id):
    form = UserForm()
    user = User.query.filter_by(id=user_id).first()

    if form.validate_on_submit():
        user.username = form.username.data
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("crud.users"))
    return render_template("crud/edit.html", user=user, form=form)
