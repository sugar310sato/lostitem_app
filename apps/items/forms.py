from flask_wtf import FlaskForm
from wtforms.fields import (DateField, IntegerField, SelectField, StringField,
                            SubmitField)

from apps.config import COLOR


class AllItems(FlaskForm):
    submit = SubmitField("一覧表示")


class SearchItems(FlaskForm):
    id = IntegerField("管理番号")
    start_date = DateField("拾得日")
    end_date = DateField("拾得日")
    item_feature = StringField("特徴")
    find_area = StringField("拾得場所")
    item_color = SelectField(
        label="色",
        choices=COLOR,
    )
    submit = SubmitField("検索")
