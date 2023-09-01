from flask_wtf import FlaskForm
from wtforms.fields import (BooleanField, DateField, IntegerField, SelectField,
                            StringField, SubmitField)

from apps.config import REFUNDED_PROCESS


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
    receiptnumber = IntegerField("受理番号")
    refund_expect = DateField("還付予定日")
    submit_register = SubmitField("登録")
    submit = SubmitField("検索")


# 還付済物件処理用フォーム
class RefundedForm(FlaskForm):
    refund_date = DateField("還付日")
    police_date = DateField("警察届出日")
    start_date = DateField("拾得日")
    end_date = DateField("拾得日")
    refunded_process = SelectField(
        label="還付後処理",
        choices=REFUNDED_PROCESS,
    )
    refunded_bool = BooleanField("処理済も表示")
    refunded_process_manager = SelectField(
        "担当者1",
        choices=[])
    refunded_process_sub_manager = SelectField(
        "担当者2",
        choices=[])
    submit = SubmitField("検索")
    submit2 = SubmitField("登録")
    submit3 = SubmitField("印刷")


# 還付検索フォーム
class RefundItemForm(FlaskForm):
    receiptnumber = IntegerField("受理番号")
    refund_expect = DateField("還付予定日")
    start_date = DateField("拾得日")
    end_date = DateField("拾得日")
    returned = BooleanField("還付済・警察返還済も表示")
    item_plice = BooleanField("貴重品のみ表示")
    item_feature = StringField("特徴")
    refund_date = DateField("還付日")
    refund_manager = SelectField(
        "担当者",
        choices=[])
    submit_register = SubmitField("登録")
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
    submit_list = SubmitField("印刷")
