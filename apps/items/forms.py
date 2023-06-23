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


# 拾得物基本クラス
class LostItemForm(FlaskForm):
    track_num = IntegerField(label="問い合わせ番号")
    notify = BooleanField(label="届出要否")
    get_item = DateField("拾得日")
    get_item_hour = SelectField(
        label="拾得時間",
        choices=TIMES,
    )
    get_item_minute = SelectField(
        label="拾得時間(分)",
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
    find_area = StringField("拾得場所")
    find_area_police = StringField("警察届出用拾得場所")
    own_waiver = SelectField(
        label="占有者権利放棄",
        choices=OWN_WAIVER,
    )
    finder_name = StringField("拾得者氏名")
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
    finder_tel1 = StringField("連絡先1")
    finder_tel2 = StringField("連絡先2")

    # 大中小項目の選択肢
    # かなりの作業なので、後日実装

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
    item_situation = BooleanField("届出済")


# 占有者拾得物クラス
class OwnerLostItemForm(LostItemForm):
    finder_class = StringField("拾得者属性")
    finder_affiliation = StringField("拾得者所属")
    submit = SubmitField("編集")


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
    submit = SubmitField("編集")
