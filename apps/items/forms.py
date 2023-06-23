from flask_wtf import FlaskForm
from wtforms.fields import (BooleanField, DateField, IntegerField, RadioField,
                            SelectField, StringField, SubmitField,
                            TextAreaField)

from apps.config import (COLOR, MINUTE, NOTE, OWN_WAIVER, SEX, STORAGE_PLACE,
                         TIMES)


class SearchItems(FlaskForm):
    item_storage = StringField("保管施設")
    submit = SubmitField("検索")


class AllItems(FlaskForm):
    submit = SubmitField("一覧表示")
