from datetime import datetime

from flask_wtf.form import FlaskForm
from wtforms.fields import (
    BooleanField,
    DateField,
    IntegerField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired

from apps.config import (
    CHOICES_FINDER,
    COLOR,
    MINUTE,
    NOTE,
    OWN_WAIVER,
    SEX,
    STORAGE_PLACE,
    TIMES,
)


# 拾得者選択クラス
class ChoicesFinderForm(FlaskForm):
    choice_finder = RadioField(
        label="拾得者",
        choices=CHOICES_FINDER,
    )
    submit = SubmitField("選択")


# 拾得物基本クラス
class LostItemForm(FlaskForm):
    track_num = IntegerField(label="問い合わせ番号")
    notify = BooleanField(label="届出要否")
    get_item = DateField("拾得日", default=datetime.today)
    get_item_hour = SelectField(
        label="拾得時間",
        choices=TIMES,
    )
    get_item_minute = SelectField(
        label="拾得時間(分)",
        choices=MINUTE,
    )
    recep_item = DateField("受付日", default=datetime.now)
    recep_item_hour = SelectField(
        label="受付時間",
        choices=TIMES,
    )
    recep_item_minute = SelectField(
        label="受付時間(分)",
        choices=MINUTE,
    )
    recep_manager = SelectField("受付担当者", choices=[])
    find_area = StringField("拾得場所", validators=[DataRequired(message="必須項目です")])
    find_area_police = StringField(
        "警察届出用拾得場所", validators=[DataRequired(message="必須項目です")]
    )
    own_waiver = SelectField(
        label="占有者権利放棄",
        choices=OWN_WAIVER,
    )
    finder_name = StringField("拾得者氏名", validators=[DataRequired(message="必須項目です")])
    own_name_note = SelectField(
        label="占有者氏名等告知",
        choices=NOTE,
    )
    finder_age = IntegerField("年齢")
    finder_sex = RadioField(
        label="性別",
        choices=SEX,
    )
    finder_post = IntegerField("郵便番号")
    finder_address = StringField("住所")
    finder_tel1 = StringField("連絡先1")
    finder_tel2 = StringField("連絡先2")

    item_value = BooleanField(label="貴重な物品に該当")
    item_feature = TextAreaField("物品の特徴", validators=[DataRequired(message="必須項目です")])
    item_color = SelectField(
        label="色",
        choices=COLOR,
    )
    item_storage = StringField("保管施設", validators=[DataRequired(message="必須項目です")])
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
    item_situation = BooleanField("届出済")

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


# 占有者拾得物クラス
class OwnerLostItemForm(LostItemForm):
    finder_class = StringField("拾得者属性")
    finder_affiliation = StringField(
        "拾得者所属", validators=[DataRequired(message="必須項目です")]
    )
    submit = SubmitField("登録")


# 第三者拾得物クラス
class ThirdPartyLostItemForm(LostItemForm):
    thirdparty_waiver = SelectField(
        label="権利放棄",
        choices=OWN_WAIVER,
    )
    thirdparty_name_note = SelectField(
        label="氏名等告知",
        choices=NOTE,
    )
    submit = SubmitField("登録")
