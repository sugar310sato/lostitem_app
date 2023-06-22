from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField


class SearchItems(FlaskForm):
    item_storage = StringField("保管施設")
    submit = SubmitField("検索")


class AllItems(FlaskForm):
    submit = SubmitField("一覧表示")
