from flask_wtf import FlaskForm
from wtforms.fields import (BooleanField, DateField, IntegerField, SelectField,
                            StringField, SubmitField)


# 届出受理番号登録フォーム
class RegisterItem(FlaskForm):
    start_date = DateField("拾得日")
    end_date = DateField("拾得日")
    finder_choice = SelectField(
        label="拾得者",
        choices=[
            ("すべて", "すべて"),
            ("占有者拾得", "占有者拾得"),
            ("第三者拾得", "第三者拾得"),
        ]
    )
    waiver = SelectField(
        label="権利",
        choices=[
            ("すべて", "すべて"),
            ("権利行使", "権利行使"),
            ("権利放棄", "権利放棄"),
        ]
    )
    submit = SubmitField("検索")


# 受理番号登録フォーム
class RefundForm(FlaskForm):
    receiptnumber = IntegerField("受理番号")
    refund_expect = DateField("還付予定日")
    submit = SubmitField("登録")


# 還付処理フォーム
class PoliceRefundForm(FlaskForm):
    refund_date = DateField("還付日")
    refund_manager = StringField("担当者")
    submit = SubmitField("登録")


# 還付検索フォーム
class RefundItemForm(FlaskForm):
    receiptnumber = IntegerField("受理番号")
    refund_expect = DateField("還付予定日")
    start_date = DateField("拾得日")
    end_date = DateField("拾得日")
    returned = BooleanField("還付済・警察返還済も表示")
    item_plice = BooleanField("貴重品のみ表示")
    item_feature = StringField("特徴")
    submit = SubmitField("検索")


# 還付一覧印刷用フォーム
class RefundList(FlaskForm):
    refund_expect_year = IntegerField("還付予定")
    refund_situation = SelectField(
        label="還付状況",
        choices=[
            ("還付予定", "還付予定"),
            ("還付済み", "還付済み"),
        ]
    )
    submit = SubmitField("検索")
