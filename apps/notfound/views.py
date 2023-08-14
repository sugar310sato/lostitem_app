from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)
from sqlalchemy import func

from apps.app import db
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
            lost_item_hour=form.lost_item_hour.data,
            lost_item_minute=form.lost_item_minute.data,
            recep_item=form.recep_item.data,
            recep_item_hour=form.recep_item_hour.data,
            recep_item_minute=form.recep_item_minute.data,
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
            item_class_L=request.form.get('item_class_L'),
            item_class_M=request.form.get('item_class_M'),
            item_class_S=request.form.get('item_class_S'),

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
    return render_template("notfound/register.html", form=form)


# 一覧、検索
@notfound.route("/search", methods=["POST", "GET"])
def notfound_search():
    form = SearchNotFoundForm()
    search_results = session.get('search_results', None)
    if search_results is None:
        search_results = db.session.query(NotFound).all()

    if form.submit.data:
        start_date = form.start_date.data
        end_date = form.end_date.data
        item_feature = form.item_feature.data
        start_expiration_date = form.start_expiration_date.data
        end_expiration_date = form.end_expiration_date.data
        # クエリの生成
        query = db.session.query(NotFound)
        if start_date and end_date:
            query = query.filter(NotFound.lost_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(func.date(NotFound.lost_item) >= start_date)
        elif end_date:
            query = query.filter(func.date(NotFound.lost_item) <= end_date)
        if item_feature:
            query = query.filter(NotFound.item_feature.ilike(f"%{item_feature}%"))
        if start_expiration_date and end_expiration_date:
            query = query.filter(NotFound.item_expiration.between(start_expiration_date,
                                                                  end_expiration_date))
        elif start_expiration_date:
            query = query.filter(func.date(NotFound.item_expiration) >=
                                 start_expiration_date)
        elif end_expiration_date:
            query = query.filter(func.date(NotFound.item_expiration) <=
                                 end_expiration_date)
        search_results = query.all()
        session['search_results'] = [item.to_dict() for item in search_results]
        return redirect(url_for("notfound.notfound_search"))
    return render_template("notfound/search.html", form=form,
                           search_results=search_results)
