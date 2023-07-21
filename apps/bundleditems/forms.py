from flask_wtf.form import FlaskForm
from wtforms.fields import (BooleanField, DateField, HiddenField, IntegerField,
                            SelectField, StringField, SubmitField,
                            TextAreaField)

from apps.config import COLOR, MINUTE, STORAGE_PLACE, TIMES


# 同梱物登録クラス
class BundledItemForm(FlaskForm):
    item_value = BooleanField(label="貴重な物品に該当")
    item_feature = TextAreaField("物品の特徴")
    item_color = SelectField(
        label="色",
        choices=COLOR,
    )
    item_storage = StringField("保管施設")
    item_storage_place = SelectField(
        label="保管場所",
        choices=STORAGE_PLACE,
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

    submit = SubmitField("同梱物登録")


# 金種登録クラス
class MoneyForm(FlaskForm):
    # 金種情報
    ten_thousand_yen = IntegerField("一万円")
    five_thousand_yen = IntegerField("五千円")
    two_thousand_yen = IntegerField("二千円")
    one_thousand_yen = IntegerField("千円")
    five_hundred_yen = IntegerField("五百円")
    one_hundred_yen = IntegerField("百円")
    fifty_yen = IntegerField("五十円")
    ten_yen = IntegerField("十円")
    five_yen = IntegerField("五円")
    one_yen = IntegerField("一円")
    total_yen = IntegerField("合計金額")

    # 記念硬貨
    commemorative_coin_1 = StringField("記念硬貨名")
    commemorative_coin_1_value = StringField("金額")
    commemorative_coin_2 = StringField("記念硬貨名")
    commemorative_coin_2_value = StringField("金額")
    submit = SubmitField("金種登録")


# カード会社連絡フォーム
class CardNote(FlaskForm):
    form_type = HiddenField(default="Main")
    card_return = DateField("返還（還付）日")
    card_item = DateField("連絡日")
    card_item_hour = SelectField(
        label="連絡時間",
        choices=TIMES,
    )
    card_item_minute = SelectField(
        label="連絡時間(分)",
        choices=MINUTE,
    )
    card_manager = StringField("連絡担当者")
    submit = SubmitField("連絡済みにする")
