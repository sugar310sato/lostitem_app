from flask_wtf.form import FlaskForm
from wtforms.fields import DateField, SelectField, StringField, SubmitField

from apps.config import DOCUMENT, MINUTE, TIMES


# 遺失者連絡フォーム
class LostNote(FlaskForm):
    lost_date = DateField("遺失日")
    lost_hour = SelectField(
        label="遺失時間",
        choices=TIMES,
    )
    lost_minute = SelectField(
        label="受付時間(分)",
        choices=MINUTE,
    )
    lost_area = StringField("遺失場所")
    recep_item = DateField("受付日")
    recep_item_hour = SelectField(
        label="受付時間",
        choices=TIMES,
    )
    recep_item_minute = SelectField(
        label="受付時間(分)",
        choices=MINUTE,
    )
    recep_manager = StringField("受付者")
    lost_person = StringField("遺失者氏名")
    lost_class = StringField("遺失者属性")
    lost_affiliation = StringField("遺失者所属")
    lost_tel1 = StringField("連絡先1")
    lost_tel2 = StringField("連絡先2")
    lost_post = StringField("郵便番号")
    lost_address = StringField("住所")
    note_date = DateField("連絡日")
    note_hour = SelectField(
        label="連絡時間",
        choices=TIMES,
    )
    note_minute = SelectField(
        label="連絡時間",
        choices=MINUTE,
    )
    note_process = StringField("連絡手段/相手")
    note_manager = StringField("連絡担当者")
    response_date = DateField("返答日")
    response_hour = SelectField(
        label="返答時間",
        choices=TIMES,
    )
    response_minute = SelectField(
        label="返答時間",
        choices=MINUTE,
    )
    response_expect = DateField("返還予定日")
    response_content = StringField("返答内容")
    response_remarks = StringField("備考")
    submit = SubmitField("連絡完了")


# 返還フォーム
class ReturnItemForm(FlaskForm):
    return_date = DateField("返還日")
    return_check = SelectField(
        label="返答時間",
        choices=DOCUMENT,
    )
    return_person = StringField("返還者")
    return_address = StringField("住所")
    return_tel = StringField("連絡先")
    return_manager = StringField("返還担当者")
    submit = SubmitField("返還")
