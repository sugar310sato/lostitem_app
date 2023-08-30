from flask import Blueprint, redirect, render_template, request, url_for

from apps.app import db
from apps.bundleditems.forms import BundledItemForm, CardNote, MoneyForm
from apps.config import ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S
from apps.crud.models import User
from apps.register.models import BundledItems, Denomination, LostItem

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
            item_situation="保管中",

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
        return redirect(url_for("items.detail", item_id=bundleditem.lostitem_id))
    return render_template("bundleditems/register_item.html", form=form,
                           lostitem=lostitem, ITEM_CLASS_L=ITEM_CLASS_L,
                           ITEM_CLASS_M=ITEM_CLASS_M, ITEM_CLASS_S=ITEM_CLASS_S)


# カード会社連絡
@bundleditems.route("/card/<item_id>", methods=["POST", "GET"])
def card(item_id):
    lostitem = LostItem.query.filter_by(id=item_id).first()
    bundleditems = BundledItems.query.filter_by(lostitem_id=item_id).all()
    # Userの一覧取得
    users = User.query.all()
    user_choice = [(user.username) for user in users]
    form = CardNote()
    form.card_manager.choices = user_choice
    if form.submit.data:
        renew_lostitem = request.form.getlist('main')
        renew_bundleds = request.form.getlist('item')
        if renew_lostitem:
            lostitem.item_situation = "連絡済み"
            lostitem.card_return = form.card_return.data
            lostitem.card_item = form.card_item.data
            lostitem.card_item_hour = form.card_item_hour.data
            lostitem.card_item_minute = form.card_item_minute.data
            lostitem.card_manager = form.card_manager.data
            db.session.add(lostitem)
            db.session.commit()
        for renew_bundled in renew_bundleds:
            renew_bundled = BundledItems.query.filter_by(id=renew_bundled).first()
            renew_bundled.item_situation = "連絡済み"
            renew_bundled.card_return = form.card_return.data
            renew_bundled.card_item = form.card_item.data
            renew_bundled.card_item_hour = form.card_item_hour.data
            renew_bundled.card_item_minute = form.card_item_minute.data
            renew_bundled.card_manager = form.card_manager.data
            db.session.add(renew_bundled)
            db.session.commit()
        return redirect(url_for("bundleditems.card", item_id=item_id))
    return render_template("/bundleditems/card.html", lostitem=lostitem,
                           bundleditems=bundleditems, form=form)


# 同梱物編集
@bundleditems.route("/edit/<item_id>", methods=["POST", "GET"])
def edit(item_id):
    form = BundledItemForm()
    bundleditem = BundledItems.query.filter_by(id=item_id).first()
    if form.submit.data:
        # 大中小項目の実装
        bundleditem.item_class_L = request.form.get('item_class_L')
        bundleditem.item_class_M = request.form.get('item_class_M')
        bundleditem.item_class_S = request.form.get('item_class_S')

        bundleditem.item_value = form.item_value.data
        bundleditem.item_feature = form.item_feature.data
        bundleditem.item_color = form.item_color.data
        bundleditem.item_storage = form.item_storage.data
        bundleditem.item_storage_place = form.item_storage_place.data
        bundleditem.item_maker = form.item_maker.data
        bundleditem.item_expiration = form.item_expiration.data
        bundleditem.item_num = form.item_num.data
        bundleditem.item_unit = form.item_unit.data
        bundleditem.item_plice = form.item_plice.data
        bundleditem.item_money = form.item_money.data
        bundleditem.item_remarks = form.item_remarks.data

        # カード情報
        bundleditem.card_campany = form.card_campany.data
        bundleditem.card_tel = form.card_tel.data
        bundleditem.card_name = form.card_name.data
        bundleditem.card_person = form.card_person.data
        bundleditem.card_return = form.card_return.data
        bundleditem.card_item = form.card_item.data
        bundleditem.card_item_hour = form.card_item_hour.data
        bundleditem.card_item_minute = form.card_item_minute.data
        bundleditem.card_item_minute = form.card_item_minute.data
        db.session.add(bundleditem)
        db.session.commit()
        return redirect(url_for("items.detail", item_id=bundleditem.lostitem_id))
    return render_template("bundleditems/edit.html", form=form, item=bundleditem,
                           ITEM_CLASS_L=ITEM_CLASS_L,
                           ITEM_CLASS_M=ITEM_CLASS_M, ITEM_CLASS_S=ITEM_CLASS_S)


# 金種登録
@bundleditems.route("/money/register/<item_id>", methods=["POST", "GET"])
def money_register(item_id):
    form = MoneyForm()
    lostitem = LostItem.query.filter_by(id=item_id).first()
    if form.submit.data:
        total_yen = (
            (form.ten_thousand_yen.data or 0) * 10000 +
            (form.five_thousand_yen.data or 0) * 5000 +
            (form.two_thousand_yen.data or 0) * 2000 +
            (form.one_thousand_yen.data or 0) * 1000 +
            (form.five_hundred_yen.data or 0) * 500 +
            (form.one_hundred_yen.data or 0) * 100 +
            (form.fifty_yen.data or 0) * 50 +
            (form.ten_yen.data or 0) * 10 +
            (form.five_yen.data or 0) * 5 +
            (form.one_yen.data or 0) * 1
        )
        denomination = Denomination(
            ten_thousand_yen=form.ten_thousand_yen.data,
            five_thousand_yen=form.five_thousand_yen.data,
            two_thousand_yen=form.two_thousand_yen.data,
            one_thousand_yen=form.one_thousand_yen.data,
            five_hundred_yen=form.five_hundred_yen.data,
            one_hundred_yen=form.one_hundred_yen.data,
            fifty_yen=form.fifty_yen.data,
            ten_yen=form.ten_yen.data,
            five_yen=form.five_yen.data,
            one_yen=form.one_yen.data,
            total_yen=total_yen,
            item_situation="保管中",

            # 記念硬貨
            commemorative_coin_1=form.commemorative_coin_1.data,
            commemorative_coin_1_value=form.commemorative_coin_1_value.data,
            commemorative_coin_2=form.commemorative_coin_2.data,
            commemorative_coin_2_value=form.commemorative_coin_2_value.data,
            lostitem_id=lostitem.id,
        )
        db.session.add(denomination)
        db.session.commit()
        return redirect(url_for("items.detail", item_id=denomination.lostitem_id))
    return render_template("bundleditems/register_money.html", form=form,
                           lostitem=lostitem)


# 金種編集
@bundleditems.route("/money/edit/<item_id>", methods=["POST", "GET"])
def money_edit(item_id):
    form = MoneyForm()
    denomination = Denomination.query.filter_by(lostitem_id=item_id).first()
    if form.submit.data:
        total_yen = (
            (form.ten_thousand_yen.data or 0) * 10000 +
            (form.five_thousand_yen.data or 0) * 5000 +
            (form.two_thousand_yen.data or 0) * 2000 +
            (form.one_thousand_yen.data or 0) * 1000 +
            (form.five_hundred_yen.data or 0) * 500 +
            (form.one_hundred_yen.data or 0) * 100 +
            (form.fifty_yen.data or 0) * 50 +
            (form.ten_yen.data or 0) * 10 +
            (form.five_yen.data or 0) * 5 +
            (form.one_yen.data or 0) * 1
        )
        denomination.ten_thousand_yen = form.ten_thousand_yen.data
        denomination.five_thousand_yen = form.five_thousand_yen.data
        denomination.two_thousand_yen = form.two_thousand_yen.data
        denomination.one_thousand_yen = form.one_thousand_yen.data
        denomination.five_hundred_yen = form.five_hundred_yen.data
        denomination.one_hundred_yen = form.one_hundred_yen.data
        denomination.fifty_yen = form.fifty_yen.data
        denomination.ten_yen = form.ten_yen.data
        denomination.five_yen = form.five_yen.data
        denomination.one_yen = form.one_yen.data
        denomination.total_yen = total_yen

        # 記念硬貨
        denomination.commemorative_coin_1 = form.commemorative_coin_1.data
        denomination.commemorative_coin_1_value = form.commemorative_coin_1_value.data
        denomination.commemorative_coin_2 = form.commemorative_coin_2.data
        denomination.commemorative_coin_2_value = form.commemorative_coin_2_value.data
        db.session.add(denomination)
        db.session.commit()
        return redirect(url_for("items.detail", item_id=denomination.lostitem_id))
    return render_template("bundleditems/money_edit.html", form=form,
                           denomination=denomination)


# 金種削除
@bundleditems.route("/delete/<item_id>", methods=["POST", "GET"])
def delete(item_id):
    denomination = Denomination.query.filter_by(id=item_id).first()
    main_item_id = denomination.lostitem_id
    db.session.delete(denomination)
    db.session.commit()
    return redirect(url_for("items.detail", item_id=main_item_id))


# 同梱物削除
@bundleditems.route("/delete/bundled/<item_id>", methods=["POST", "GET"])
def delete_bundled(item_id):
    bundleditem = BundledItems.query.filter_by(id=item_id).first()
    main_item_id = bundleditem.lostitem_id
    db.session.delete(bundleditem)
    db.session.commit()
    return redirect(url_for("items.detail", item_id=main_item_id))
