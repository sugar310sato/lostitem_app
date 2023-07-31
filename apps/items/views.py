from flask import (Blueprint, current_app, redirect, render_template, request,
                   send_from_directory, session, url_for)

from apps.app import db
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

    if form.submit.data:
        id = form.id.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        item_feature = form.item_feature.data
        find_area = form.find_area.data
        item_color = form.item_color.data
        item_value = form.item_value.data
        item_not_yet = form.item_not_yet.data
        # 拾得物を検索するクエリを作成
        query = db.session.query(LostItem)
        # 入力された情報に基づいてクエリを絞り込む
        if request.form.get('item_class_L') != "選択してください":
            if request.form.get('item_class_L'):
                item_class = request.form.get('item_class_L')
                query = query.filter(LostItem.item_class_L == item_class)
            if request.form.get('item_class_M'):
                item_class = request.form.get('item_class_M')
                query = query.filter(LostItem.item_class_M == item_class)
            if request.form.get('item_class_S'):
                item_class = request.form.get('item_class_S')
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
        if item_color:
            query = query.filter(LostItem.item_color.ilike(f"%{item_color}%"))
        if not item_value:
            query = query.filter(LostItem.item_value == False)
        if item_not_yet:
            query = query.filter(LostItem.item_situation != "返還済み")
        # 結果を取得
        search_results = query.all()
        session['search_results'] = [item.to_dict() for item in search_results]
        return redirect(url_for("items.item_search"))

    all_lost_item = db.session.query(LostItem).all()
    return render_template("items/index.html", all_lost_item=all_lost_item, form=form)


# 拾得物一覧画面
@items.route("/photo_arange", methods=["POST", "GET"])
def photo_arange():
    # すべての拾得物を表示
    form = SearchItems()

    if form.submit.data:
        id = form.id.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        item_feature = form.item_feature.data
        find_area = form.find_area.data
        item_color = form.item_color.data
        item_value = form.item_value.data
        item_not_yet = form.item_not_yet.data
        # 拾得物を検索するクエリを作成
        query = db.session.query(LostItem)
        # 入力された情報に基づいてクエリを絞り込む
        if request.form.get('item_class_L') != "選択してください":
            if request.form.get('item_class_L'):
                item_class = request.form.get('item_class_L')
                query = query.filter(LostItem.item_class_L == item_class)
            if request.form.get('item_class_M'):
                item_class = request.form.get('item_class_M')
                query = query.filter(LostItem.item_class_M == item_class)
            if request.form.get('item_class_S'):
                item_class = request.form.get('item_class_S')
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
        if item_color:
            query = query.filter(LostItem.item_color.ilike(f"%{item_color}%"))
        # SQLAlchemyに合わせているので==を使用
        if not item_value:
            query = query.filter(LostItem.item_value == False)
        if item_not_yet:
            query = query.filter(LostItem.item_situation != "返還済み")
        # 結果を取得
        search_results = query.all()
        print(search_results)
        session['search_results'] = [item.to_dict() for item in search_results]
        return redirect(url_for("items.item_search_photo"))

    all_lost_item = db.session.query(LostItem).all()
    return render_template("items/photo_arange.html", all_lost_item=all_lost_item,
                           form=form)


# 詳細画面
@items.route("/detail/<item_id>", methods=["POST", "GET"])
def detail(item_id):
    item = LostItem.query.filter_by(id=item_id).first()
    bundleditem = BundledItems.query.filter_by(lostitem_id=item_id).all()
    denomination = Denomination.query.filter_by(lostitem_id=item_id).all()
    return render_template("items/detail.html", item=item, bundleditem=bundleditem,
                           denomination=denomination)


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
            item.finder_address = form.finder_address.data
            item.finder_tel1 = form.finder_tel1.data
            item.finder_tel2 = form.finder_tel2.data

            # 大中小項目の実装
            item.item_class_L = request.form.get('item_class_L')
            item.item_class_M = request.form.get('item_class_M')
            item.item_class_S = request.form.get('item_class_S')

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
            item.item_class_L = request.form.get('item_class_L')
            item.item_class_M = request.form.get('item_class_M')
            item.item_class_S = request.form.get('item_class_S')

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
    return render_template("items/edit.html", form=form, item=item,
                           choice_finder=item.choice_finder)


# 拾得物の検索
@items.route("/items/search", methods=["POST", "GET"])
def item_search():
    search_results = session.get('search_results', [])
    print(search_results)
    return render_template("items/search.html", search_results=search_results)


# 検索結果の写真表示
@items.route("/items/search/photo", methods=["POST", "GET"])
def item_search_photo():
    search_results = session.get('search_results', [])
    return render_template("items/search_photo.html", search_results=search_results)


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
