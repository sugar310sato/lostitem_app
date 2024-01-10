from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import func

from apps.app import db
from apps.config import ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S
from apps.notfound.forms import NotFoundForm, SearchNotFoundForm
from apps.register.models import NotFound

notfound = Blueprint(
    "notfound",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# 登録
@notfound.route("/register", methods=["POST", "GET"])
def notfound_register():
    form = NotFoundForm()
    if form.submit.data:
        item_data = NotFound(
            lost_item=form.lost_item.data,
            lost_item_hour=request.form.get("get_item_hours"),
            lost_item_minute=request.form.get("get_item_minutes"),
            recep_item=form.recep_item.data,
            recep_item_hour=request.form.get("recep_item_hours"),
            recep_item_minute=request.form.get("recep_item_minutes"),
            recep_manager=form.recep_manager.data,
            lost_area=form.lost_area.data,
            lost_name=form.lost_name.data,
            lost_age=form.lost_age.data,
            lost_sex=form.lost_sex.data,
            lost_post=form.lost_post.data,
            lost_address=form.lost_address.data,
            lost_tel1=form.lost_tel1.data,
            lost_tel2=form.lost_tel2.data,
            # 大中小項目の実装
            item_class_L=request.form.get("item_class_L"),
            item_class_M=request.form.get("item_class_M"),
            item_class_S=request.form.get("item_class_S"),
            item_value=form.item_value.data,
            item_feature=form.item_feature.data,
            item_color=form.item_color.data,
            item_maker=form.item_maker.data,
            item_expiration=form.item_expiration.data,
            item_num=form.item_num.data,
            item_unit=form.item_unit.data,
            item_plice=form.item_plice.data,
            item_money=form.item_money.data,
            item_remarks=form.item_remarks.data,
            item_situation="未対応",
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
        db.session.add(item_data)
        db.session.commit()
        return redirect(url_for("notfound.notfound_search"))
    return render_template(
        "notfound/register.html",
        form=form,
        ITEM_CLASS_L=ITEM_CLASS_L,
        ITEM_CLASS_M=ITEM_CLASS_M,
        ITEM_CLASS_S=ITEM_CLASS_S,
    )


# 一覧、検索
@notfound.route("/search", methods=["POST", "GET"])
def notfound_search():
    form = SearchNotFoundForm()
    search_results = session.get("not_found_search", None)
    if search_results is None:
        # クエリの生成
        query = db.session.query(NotFound)
        query = query.filter(NotFound.item_situation != "対応済")
        search_results = query.all()
    else:
        start_date = search_results["start_date"]
        end_date = search_results["end_date"]
        item_feature = search_results["item_feature"]
        start_expiration_date = search_results["start_expiration_date"]
        end_expiration_date = search_results["end_expiration_date"]
        taiou_bool = search_results["taiou_bool"]
        item_class_L = search_results["item_class_L"]
        item_class_M = search_results["item_class_M"]
        item_class_S = search_results["item_class_S"]

        # クエリの生成
        query = db.session.query(NotFound)
        if item_class_L != "選択してください":
            if item_class_L:
                item_class = item_class_L
                query = query.filter(NotFound.item_class_L == item_class)
            if item_class_M:
                item_class = item_class_M
                query = query.filter(NotFound.item_class_M == item_class)
            if item_class_S:
                item_class = item_class_S
                query = query.filter(NotFound.item_class_S == item_class)

        if start_date and end_date:
            query = query.filter(NotFound.lost_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(func.date(NotFound.lost_item) >= start_date)
        elif end_date:
            query = query.filter(func.date(NotFound.lost_item) <= end_date)
        if item_feature:
            query = query.filter(NotFound.item_feature.ilike(f"%{item_feature}%"))
        if start_expiration_date and end_expiration_date:
            query = query.filter(
                NotFound.item_expiration.between(
                    start_expiration_date, end_expiration_date
                )
            )
        elif start_expiration_date:
            query = query.filter(
                func.date(NotFound.item_expiration) >= start_expiration_date
            )
        elif end_expiration_date:
            query = query.filter(
                func.date(NotFound.item_expiration) <= end_expiration_date
            )
        if not taiou_bool:
            query = query.filter(NotFound.item_situation != "対応済")
        search_results = query.all()

    # ページネーション処理
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1) * 50 : page * 50]
    pagination = Pagination(
        page=page, total=len(search_results), per_page=50, css_framework="bootstrap5"
    )

    if form.submit.data:
        # セッション情報として絞り込み条件
        session["not_found_search"] = {
            "start_date": form.start_date.data.strftime("%Y-%m-%d")
            if form.start_date.data
            else None,
            "end_date": form.end_date.data.strftime("%Y-%m-%d")
            if form.end_date.data
            else None,
            "item_feature": form.item_feature.data,
            "start_expiration_date": form.start_expiration_date.data.strftime(
                "%Y-%m-%d"
            )
            if form.start_expiration_date.data
            else None,
            "end_expiration_date": form.end_expiration_date.data.strftime("%Y-%m-%d")
            if form.end_expiration_date.data
            else None,
            "taiou_bool": form.taiou_bool.data,
            "item_class_L": request.form.get("item_class_L"),
            "item_class_M": request.form.get("item_class_M"),
            "item_class_S": request.form.get("item_class_S"),
        }
        return redirect(url_for("notfound.notfound_search"))

    if form.submit_taiou.data:
        item_ids = request.form.getlist("item_ids")
        items = db.session.query(NotFound).filter(NotFound.id.in_(item_ids)).all()
        for item in items:
            item.item_situation = "対応済"
        db.session.commit()
        return redirect(url_for("notfound.notfound_search"))
    return render_template(
        "notfound/search.html",
        form=form,
        search_results=rows,
        pagination=pagination,
        ITEM_CLASS_L=ITEM_CLASS_L,
        ITEM_CLASS_M=ITEM_CLASS_M,
        ITEM_CLASS_S=ITEM_CLASS_S,
    )


# 詳細
@notfound.route("/detail/<item_id>", methods=["POST", "GET"])
def detail(item_id):
    item = NotFound.query.filter_by(id=item_id).first()
    return render_template("notfound/detail.html", item=item)
