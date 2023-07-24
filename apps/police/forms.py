from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, DateField, SelectField, SubmitField

from apps.config import CHOICES_FINDER_POLICE


# 警察届出用フォーム
class PoliceForm(FlaskForm):
    start_date = DateField("拾得日")
    end_date = DateField("拾得日")
    item_plice = BooleanField("貴重品のみ表示")
    item_finder = SelectField(
        label="拾得者",
        choices=CHOICES_FINDER_POLICE,
    )
    submit = SubmitField("絞り込み")
