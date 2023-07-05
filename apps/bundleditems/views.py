from flask import Blueprint, redirect, render_template, request, url_for

from apps.app import db
from apps.bundleditems.forms import BundledItemForm
from apps.register.models import BundledItems, LostItem

bundleditems = Blueprint(
    "bundleditems",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# 同梱物登録
@bundleditems.route("/register/<item_id>", methods=["POST", "GET"])
def register(item_id):
    form = BundledItemForm()
    lostitem = LostItem.query.filter_by(id=item_id).first()
    if form.submit.data:
        bundleditem = BundledItems(
            item_class_L=request.form.get('item_class_L'),
            item_class_M=request.form.get('item_class_M'),
            item_class_S=request.form.get('item_class_S'),

            item_value=form.item_value.data,
            item_feature=form.item_feature.data,
            item_color=form.item_color.data,
            item_storage=form.item_storage.data,
            item_storage_place=form.item_storage_place.data,
            item_maker=form.item_maker.data,
            item_expiration=form.item_expiration.data,
            item_num=form.item_num.data,
            item_unit=form.item_unit.data,
            item_plice=form.item_plice.data,
            item_money=form.item_money.data,
            item_remarks=form.item_remarks.data,
            lostitem_id=lostitem.id,

            # カードの場合は、カード情報の登録
            card_campany=form.card_campany.data,
            card_tel=form.card_tel.data,
            card_name=form.card_name.data,
            card_person=form.card_person.data,
            card_return=form.card_return.data,
            card_item=form.card_item.data,
            card_item_hour=form.card_item_hour.data,
            card_item_minute=form.card_item_minute.data,
            card_manager=form.card_manager.data,
        )
        db.session.add(bundleditem)
        db.session.commit()
        return redirect(url_for("bundleditems.detail"))
    return render_template("bundleditems/register_item.html", form=form,
                           lostitem=lostitem)
