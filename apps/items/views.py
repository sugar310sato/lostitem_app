from flask import Blueprint, redirect, render_template, url_for

from apps.app import db
from apps.register.forms import OwnerLostItemForm, ThirdPartyLostItemForm
from apps.register.models import LostItem

items = Blueprint(
    "items",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# 拾得物一覧画面
@items.route("/")
def index():
    # すべての拾得物を表示
    all_lost_item = db.session.query(LostItem).all()
    return render_template("items/index.html", all_lost_item=all_lost_item)


# 詳細画面
@items.route("/detail/<item_id>", methods=["POST", "GET"])
def detail(item_id):
    item = LostItem.query.filter_by(id=item_id).first()
    return render_template("items/detail.html", item=item)


# 編集物選択画面（メインor同梱物）
@items.route("/edit/select/<item_id>", methods=["POST", "GET"])
def edit_select(item_id):
    # 現状は、メインの拾得物のみ
    item = LostItem.query.filter_by(id=item_id).first()
    return render_template("items/edit_select.html", item=item)


# 編集画面
@items.route("/edit/<item_id>", methods=["POST", "GET"])
def edit(item_id):
    item = LostItem.query.filter_by(id=item_id).first()
    if item.choice_finder == "占有者拾得":
        form = OwnerLostItemForm()
        if form.submit.data:
            item.choice_finder = item.choice_finder
            item.track_num = form.track_num.data
            item.notify = form.notify.data
            item.get_item = form.get_item.data
            item.get_item_hour = form.get_item_hour.data
            item.get_item_minute = form.get_item_minute.data
            item.recep_item = form.recep_item.data
            item.recep_item_hour = form.recep_item_hour.data
            item.recep_item_minute = form.recep_item_minute.data
            item.recep_manager = form.recep_manager.data
            item.find_area = form.find_area.data
            item.find_area_police = form.find_area_police.data
            item.own_waiver = form.own_waiver.data
            item.finder_name = form.finder_name.data
            item.own_name_note = form.own_name_note.data
            item.finder_age = form.finder_age.data
            item.finder_sex = form.finder_sex.data
            item.finder_post = form.finder_post.data
            item.finder_tel1 = form.finder_tel1.data
            item.finder_tel2 = form.finder_tel2.data

            # 大中小項目の実装

            item.item_value = form.item_value.data
            item.item_feature = form.item_feature.data
            item.item_color = form.item_color.data
            item.item_storage = form.item_storage.data
            item.item_storage_place = form.item_storage_place.data
            item.item_maker = form.item_maker.data
            item.item_expiration = form.item_expiration.data
            item.item_num = form.item_num.data
            item.item_unit = form.item_unit.data
            item.item_plice = form.item_plice.data
            item.item_money = form.item_money.data
            item.item_remarks = form.item_remarks.data
            item.item_situation = form.item_situation.data
            item.finder_class = form.finder_class.data
            item.finder_affiliation = form.finder_affiliation.data
            db.session.add(item)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=item.id))
    else:
        form = ThirdPartyLostItemForm()
        if form.submit.data:
            item.choice_finder = item.choice_finder
            item.track_num = form.track_num.data
            item.notify = form.notify.data
            item.get_item = form.get_item.data
            item.get_item_hour = form.get_item_hour.data
            item.get_item_minute = form.get_item_minute.data
            item.recep_item = form.recep_item.data
            item.recep_item_hour = form.recep_item_hour.data
            item.recep_item_minute = form.recep_item_minute.data
            item.recep_manager = form.recep_manager.data
            item.find_area = form.find_area.data
            item.find_area_police = form.find_area_police.data
            item.own_waiver = form.own_waiver.data
            item.finder_name = form.finder_name.data
            item.own_name_note = form.own_name_note.data
            item.finder_age = form.finder_age.data
            item.finder_sex = form.finder_sex.data
            item.finder_post = form.finder_post.data
            item.finder_tel1 = form.finder_tel1.data
            item.finder_tel2 = form.finder_tel2.data

            # 大中小項目の実装

            item.item_value = form.item_value.data
            item.item_feature = form.item_feature.data
            item.item_color = form.item_color.data
            item.item_storage = form.item_storage.data
            item.item_storage_place = form.item_storage_place.data
            item.item_maker = form.item_maker.data
            item.item_expiration = form.item_expiration.data
            item.item_num = form.item_num.data
            item.item_unit = form.item_unit.data
            item.item_plice = form.item_plice.data
            item.item_money = form.item_money.data
            item.item_remarks = form.item_remarks.data
            item.item_situation = form.item_situation.data
            item.thirdparty_waiver = form.thirdparty_waiver.data
            item.thirdparty_name_note = form.thirdparty_name_note.data
            db.session.add(item)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=item.id))
    return render_template("items/edit.html", form=form, item=item)
