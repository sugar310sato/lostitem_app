from flask_wtf import FlaskForm
from wtforms.fields import DateField, SelectField, SubmitField


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
