from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_paginate import Pagination, get_page_parameter

from apps.app import db
from apps.config import ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S
from apps.crud.models import User
from apps.items.forms import SearchItems
from apps.register.forms import OwnerLostItemForm, ThirdPartyLostItemForm
from apps.register.models import BundledItems, Denomination, LostItem

items = Blueprint(
    "items",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# 拾得物一覧画面
@items.route("/", methods=["POST", "GET"])
def index():
    # すべての拾得物を表示
    form = SearchItems()
    search_results = session.get("search_item", None)
    if search_results is None:
        search_results = db.session.query(LostItem).all()
    else:
        id = search_results["id"]
        start_date = search_results["start_date"]
        end_date = search_results["end_date"]
        item_feature = search_results["item_feature"]
        find_area = search_results["find_area"]
        item_color = search_results["item_color"]
        item_value = search_results["item_value"]
        item_not_yet = search_results["item_not_yet"]
        item_class_L = search_results["item_class_L"]
        item_class_M = search_results["item_class_M"]
        item_class_S = search_results["item_class_S"]
        # 拾得物を検索するクエリを作成
        query = db.session.query(LostItem)
        # 入力された情報に基づいてクエリを絞り込む
        if item_class_L != "選択してください":
            if item_class_L:
                item_class = item_class_L
                query = query.filter(LostItem.item_class_L == item_class)
            if item_class_M != "選択してください":
                item_class = item_class_M
                query = query.filter(LostItem.item_class_M == item_class)
            if item_class_S != "選択してください":
                item_class = item_class_S
                query = query.filter(LostItem.item_class_S == item_class)

        if id:
            query = query.filter(LostItem.id == id)
        if start_date and end_date:
            query = query.filter(LostItem.get_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(LostItem.get_item >= start_date)
        elif end_date:
            query = query.filter(LostItem.get_item <= end_date)
        if item_feature:
            query = query.filter(LostItem.item_feature.ilike(f"%{item_feature}%"))
        if find_area:
            query = query.filter(LostItem.find_area.ilike(f"%{find_area}%"))
        if item_color != "未選択":
            query = query.filter(LostItem.item_color.ilike(f"%{item_color}%"))
        if not item_value:
            query = query.filter(LostItem.item_value == False)
        if item_not_yet:
            query = query.filter(LostItem.item_situation != "返還済み")
        # 結果を取得
        search_results = query.all()

    # ページネーション処理
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1) * 50 : page * 50]
    pagination = Pagination(
        page=page, total=len(search_results), per_page=50, css_framework="bootstrap5"
    )

    if form.submit.data:
        # セッション情報として絞り込み条件
        session["search_item"] = {
            "id": form.id.data,
            "start_date": form.start_date.data.strftime("%Y-%m-%d")
            if form.start_date.data
            else None,
            "end_date": form.end_date.data.strftime("%Y-%m-%d")
            if form.end_date.data
            else None,
            "item_feature": form.item_feature.data,
            "find_area": form.find_area.data,
            "item_color": form.item_color.data,
            "item_value": form.item_value.data,
            "item_not_yet": form.item_not_yet.data,
            "item_class_L": request.form.get("item_class_L"),
            "item_class_M": request.form.get("item_class_M"),
            "item_class_S": request.form.get("item_class_S"),
        }
        return redirect(url_for("items.index"))

    return render_template(
        "items/index.html",
        all_lost_item=rows,
        form=form,
        pagination=pagination,
        ITEM_CLASS_L=ITEM_CLASS_L,
        ITEM_CLASS_M=ITEM_CLASS_M,
        ITEM_CLASS_S=ITEM_CLASS_S,
    )


# 拾得物一覧画面(写真)
@items.route("/photo_arange", methods=["POST", "GET"])
def photo_arange():
    # すべての拾得物を表示
    form = SearchItems()
    search_results = session.get("search_item", None)
    if search_results is None:
        search_results = db.session.query(LostItem).all()
    else:
        id = search_results["id"]
        start_date = search_results["start_date"]
        end_date = search_results["end_date"]
        item_feature = search_results["item_feature"]
        find_area = search_results["find_area"]
        item_color = search_results["item_color"]
        item_value = search_results["item_value"]
        item_not_yet = search_results["item_not_yet"]
        item_class_L = search_results["item_class_L"]
        item_class_M = search_results["item_class_M"]
        item_class_S = search_results["item_class_S"]
        # 拾得物を検索するクエリを作成
        query = db.session.query(LostItem)
        # 入力された情報に基づいてクエリを絞り込む
        if item_class_L != "選択してください":
            if item_class_L:
                item_class = item_class_L
                query = query.filter(LostItem.item_class_L == item_class)
            if item_class_M != "選択してください":
                item_class = item_class_M
                query = query.filter(LostItem.item_class_M == item_class)
            if item_class_S != "選択してください":
                item_class = item_class_S
                query = query.filter(LostItem.item_class_S == item_class)

        if id:
            query = query.filter(LostItem.id == id)
        if start_date and end_date:
            query = query.filter(LostItem.get_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(LostItem.get_item >= start_date)
        elif end_date:
            query = query.filter(LostItem.get_item <= end_date)
        if item_feature:
            query = query.filter(LostItem.item_feature.ilike(f"%{item_feature}%"))
        if find_area:
            query = query.filter(LostItem.find_area.ilike(f"%{find_area}%"))
        if item_color != "未選択":
            query = query.filter(LostItem.item_color.ilike(f"%{item_color}%"))
        if not item_value:
            query = query.filter(LostItem.item_value == False)
        if item_not_yet:
            query = query.filter(LostItem.item_situation != "返還済み")
        # 結果を取得
        search_results = query.all()

    # ページネーション処理
    # デモのため、5枚に設定
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1) * 5 : page * 5]
    pagination = Pagination(
        page=page, total=len(search_results), per_page=5, css_framework="bootstrap5"
    )

    if form.submit.data:
        # セッション情報として絞り込み条件
        session["search_item"] = {
            "id": form.id.data,
            "start_date": form.start_date.data.strftime("%Y-%m-%d")
            if form.start_date.data
            else None,
            "end_date": form.end_date.data.strftime("%Y-%m-%d")
            if form.end_date.data
            else None,
            "item_feature": form.item_feature.data,
            "find_area": form.find_area.data,
            "item_color": form.item_color.data,
            "item_value": form.item_value.data,
            "item_not_yet": form.item_not_yet.data,
            "item_class_L": request.form.get("item_class_L"),
            "item_class_M": request.form.get("item_class_M"),
            "item_class_S": request.form.get("item_class_S"),
        }
        return redirect(url_for("items.photo_arange"))

    return render_template(
        "items/photo_arange.html",
        all_lost_item=rows,
        form=form,
        pagination=pagination,
        ITEM_CLASS_L=ITEM_CLASS_L,
        ITEM_CLASS_M=ITEM_CLASS_M,
        ITEM_CLASS_S=ITEM_CLASS_S,
    )


# 詳細画面
@items.route("/detail/<item_id>", methods=["POST", "GET"])
def detail(item_id):
    item = LostItem.query.filter_by(id=item_id).first()
    bundleditem = BundledItems.query.filter_by(lostitem_id=item_id).all()
    denomination = Denomination.query.filter_by(lostitem_id=item_id).all()
    return render_template(
        "items/detail.html",
        item=item,
        bundleditem=bundleditem,
        denomination=denomination,
    )


# 編集物選択画面（メインor同梱物）
@items.route("/edit/select/<item_id>", methods=["POST", "GET"])
def edit_select(item_id):
    # 現状は、メインの拾得物のみ
    item = LostItem.query.filter_by(id=item_id).first()
    bundleditem = BundledItems.query.filter_by(lostitem_id=item_id).all()
    return render_template("items/edit_select.html", item=item, bundleditem=bundleditem)


# 編集画面
@items.route("/edit/<item_id>", methods=["POST", "GET"])
def edit(item_id):
    item = LostItem.query.filter_by(id=item_id).first()
    get_item_date = item.get_item.strftime("%Y-%m-%d") if item.get_item else ""
    recep_item_date = item.recep_item.strftime("%Y-%m-%d") if item.recep_item else ""
    # Userの一覧取得
    users = User.query.all()
    user_choice = [(user.username) for user in users]
    if item.choice_finder == "占有者拾得":
        form = OwnerLostItemForm()
        form.recep_manager.choices = user_choice
        if form.submit.data:
            item.choice_finder = item.choice_finder
            item.track_num = form.track_num.data
            item.notify = form.notify.data
            item.get_item = form.get_item.data
            item.get_item_hour = request.form.get("get_item_hours")
            item.get_item_minute = request.form.get("get_item_minutes")
            item.recep_item = form.recep_item.data
            item.recep_item_hour = request.form.get("recep_item_hours")
            item.recep_item_minute = request.form.get("recep_item_minutes")
            item.recep_manager = form.recep_manager.data
            item.find_area = form.find_area.data
            item.find_area_police = form.find_area_police.data
            item.own_waiver = form.own_waiver.data
            item.finder_name = form.finder_name.data
            item.own_name_note = form.own_name_note.data
            item.finder_age = form.finder_age.data
            item.finder_sex = form.finder_sex.data
            item.finder_post = form.finder_post.data
            item.finder_address = form.finder_address.data
            item.finder_tel1 = form.finder_tel1.data
            item.finder_tel2 = form.finder_tel2.data

            # 大中小項目の実装
            item.item_class_L = request.form.get("item_class_L")
            item.item_class_M = request.form.get("item_class_M")
            item.item_class_S = request.form.get("item_class_S")

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

            # カード情報
            item.card_campany = form.card_campany.data
            item.card_tel = form.card_tel.data
            item.card_name = form.card_name.data
            item.card_person = form.card_person.data
            item.card_return = form.card_return.data
            item.card_item = form.card_item.data
            item.card_item_hour = form.card_item_hour.data
            item.card_item_minute = form.card_item_minute.data
            item.card_item_minute = form.card_item_minute.data

            item.finder_class = form.finder_class.data
            item.finder_affiliation = form.finder_affiliation.data
            db.session.add(item)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=item.id))
    else:
        form = ThirdPartyLostItemForm()
        form.recep_manager.choices = user_choice
        if form.submit.data:
            item.choice_finder = item.choice_finder
            item.track_num = form.track_num.data
            item.notify = form.notify.data
            item.get_item = form.get_item.data
            item.get_item_hour = request.form.get("get_item_hours")
            item.get_item_minute = request.form.get("get_item_minutes")
            item.recep_item = form.recep_item.data
            item.recep_item_hour = request.form.get("recep_item_hours")
            item.recep_item_minute = request.form.get("recep_item_minutes")
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
            item.item_class_L = request.form.get("item_class_L")
            item.item_class_M = request.form.get("item_class_M")
            item.item_class_S = request.form.get("item_class_S")

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

            # カード情報
            item.card_campany = form.card_campany.data
            item.card_tel = form.card_tel.data
            item.card_name = form.card_name.data
            item.card_person = form.card_person.data
            item.card_return = form.card_return.data
            item.card_item = form.card_item.data
            item.card_item_hour = form.card_item_hour.data
            item.card_item_minute = form.card_item_minute.data
            item.card_item_minute = form.card_item_minute.data

            item.thirdparty_waiver = form.thirdparty_waiver.data
            item.thirdparty_name_note = form.thirdparty_name_note.data
            db.session.add(item)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=item.id))
    return render_template(
        "items/edit.html",
        form=form,
        item=item,
        choice_finder=item.choice_finder,
        get_item_date=get_item_date,
        recep_item_date=recep_item_date,
        ITEM_CLASS_L=ITEM_CLASS_L,
        ITEM_CLASS_M=ITEM_CLASS_M,
        ITEM_CLASS_S=ITEM_CLASS_S,
    )


# 拾得物の削除
@items.route("/delete/<item_id>", methods=["POST", "GET"])
def delete(item_id):
    item = LostItem.query.filter_by(id=item_id).first()
    bundleditems = BundledItems.query.filter_by(lostitem_id=item_id).all()
    denomination = Denomination.query.filter_by(lostitem_id=item_id).first()
    if bundleditems:
        for bundleditem in bundleditems:
            db.session.delete(bundleditem)

    if denomination:
        db.session.delete(denomination)

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("items.index"))


# 画像表示用関数
@items.route("/images/<item_id>")
def image_file(item_id):
    item = LostItem.query.filter_by(id=item_id).first()
    return send_from_directory(current_app.config["LENAMED_FOLDER"], item.item_image)
