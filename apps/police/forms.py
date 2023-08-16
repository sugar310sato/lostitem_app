from flask_wtf import FlaskForm
from wtforms.fields import (BooleanField, DateField, SelectField, SubmitField,
                            TextAreaField)

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


# 届出出力用フォーム
class MakeDocument(FlaskForm):
    submit = SubmitField("警察届出所出力")


# 届出日、書類設定フォーム
class OptionDocument(FlaskForm):
    submit_date = DateField("警察届出日")
    document = SelectField(
        label="書類",
        choices=[
            ("占有者拾得物提出書", "占有者拾得物提出書"),
            ("第三者拾得物提出書", "第三者拾得物提出書"),
        ]
    )
    submit = SubmitField("提出書類の作成")


# フレキシブルディスク提出票用フォーム
class SubmitData(FlaskForm):
    info = TextAreaField("フレキシブルディスクに記載された事項")
    documents = TextAreaField("フレキシブルディスクとあわせて提出される書類")
    submit = SubmitField("印刷")
