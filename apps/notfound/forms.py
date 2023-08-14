from flask_wtf.form import FlaskForm
from wtforms.fields import (BooleanField, DateField, IntegerField, RadioField,
                            SelectField, StringField, SubmitField,
                            TextAreaField)

from apps.config import COLOR, MINUTE, SEX, TIMES


# 拾得物基本クラス
class NotFoundForm(FlaskForm):
    lost_item = DateField("遺失日")
    lost_item_hour = SelectField(
        label="遺失時間",
        choices=TIMES,
    )
    lost_item_minute = SelectField(
        label="遺失時間(分)",
        choices=MINUTE,
    )
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
    lost_area = StringField("遺失場所")
    lost_name = StringField("遺失者名")
    lost_age = IntegerField("年齢")
    lost_sex = RadioField(
        label="性別",
        choices=SEX,
    )
    lost_post = IntegerField("郵便番号")
    lost_address = StringField("住所")
    lost_tel1 = StringField("連絡先1")
    lost_tel2 = StringField("連絡先2")

    item_value = BooleanField(label="貴重な物品に該当")
    item_feature = TextAreaField("物品の特徴")
    item_color = SelectField(
        label="色",
        choices=COLOR,
    )
    item_maker = StringField("メーカー")
    item_expiration = DateField("消費期限")
    item_num = IntegerField("数量")
    item_unit = StringField("単位")
    item_plice = StringField("値段")
    item_money = StringField("金額")
    item_remarks = TextAreaField("備考")

    # カード情報
    card_campany = StringField("カード発行会社名")
    card_tel = StringField("カード発行会社連絡先")
    card_name = StringField("カード名")
    card_person = StringField("カード記載人名")
    card_item = DateField("連絡日")
    card_return = DateField("返還日")
    card_item_hour = SelectField(
        label="連絡時間",
        choices=TIMES,
    )
    card_item_minute = SelectField(
        label="連絡時間(分)",
        choices=MINUTE,
    )
    card_manager = StringField("連絡者")
    submit = SubmitField("登録")


# 検索フォーム
class SearchNotFoundForm(FlaskForm):
    start_date = DateField("遺失日")
    end_date = DateField("遺失日")
    item_feature = StringField("特徴")
    start_expiration_date = DateField("消費期限")
    end_expiration_date = DateField("消費期限")
    submit = SubmitField("検索")
