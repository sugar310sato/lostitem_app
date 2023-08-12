from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, IntegerField, StringField,
                     SubmitField)


# 廃棄・売却用フォーム
class GroceriesForm(FlaskForm):
    start_date = DateField("拾得日")
    end_date = DateField("拾得日")
    item_feature = StringField("特徴")
    start_dispoal_date = DateField("売却・廃棄日")
    end_dispoal_date = DateField("売却・廃棄日")
    start_expiration_date = DateField("消費期限")
    end_expiration_date = DateField("消費期限")
    start_id = IntegerField("管理番号")
    end_id = IntegerField("管理番号")
    item_situation_sale = BooleanField("売却済も表示")
    item_situation_disposal = BooleanField("廃棄済も表示")
    selling_price = IntegerField("売却価格")
    disposal_date = DateField("廃棄日")
    selling_date = DateField("売却日")
    submit = SubmitField("検索")
    submit_print = SubmitField("印刷")
    submit_register = SubmitField("売却")
    submit_disposal = SubmitField("廃棄")
