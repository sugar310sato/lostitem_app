from datetime import datetime

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import extract, func, or_

from apps.app import db
from apps.crud.models import User
from apps.refund.forms import (RefundedForm, RefundedPrint, RefundItemForm,
                               RefundList, RegisterItem)
# 関数の導入
from apps.refund.print_document import (make_pdf_refund_items,
                                        make_refunded_list_disposal,
                                        make_refunded_list_hold,
                                        make_refunded_list_HQ,
                                        make_refunded_list_manager,
                                        make_refunded_list_money,
                                        make_refunded_list_police)
from apps.register.models import LostItem

refund = Blueprint(
    "refund",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# 届出受理番号登録
@refund.route("/register_num", methods=["POST", "GET"])
def register_num():
    form = RegisterItem()
    search_results = session.get('search_register_num', None)
    if search_results is None:
        # 処理済みの物は最初から出さない
        query = db.session.query(LostItem)
        query = query.filter(LostItem.refund_situation != "処理済")
        query = query.filter(LostItem.refund_situation != "還付済")
        query = query.filter(LostItem.refund_situation != "対応済")
        search_results = query.all()
    else:
        start_date = search_results['start_date']
        end_date = search_results['end_date']
        finder_choice = search_results['finder_choice']
        waiver = search_results['waiver']
        # クエリの生成
        query = db.session.query(LostItem)
        if start_date and end_date:
            query = query.filter(LostItem.get_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(LostItem.get_item >= start_date)
        elif end_date:
            query = query.filter(LostItem.get_item <= end_date)
        if finder_choice == "占有者拾得":
            query = query.filter(LostItem.choice_finder == "占有者拾得")
        elif finder_choice == "第三者拾得":
            query = query.filter(LostItem.choice_finder == "第三者拾得")
        if waiver == "権利行使":
            query = query.filter(LostItem.own_waiver == "放棄しない")
        elif waiver == "権利放棄":
            query = query.filter(LostItem.own_waiver == "一切放棄")
        query = query.filter(LostItem.refund_situation != "処理済")
        query = query.filter(LostItem.refund_situation != "還付済")
        query = query.filter(LostItem.refund_situation != "対応済")
        search_results = query.all()

    # ページネーション処理
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1)*50: page*50]
    pagination = Pagination(page=page, total=len(search_results), per_page=50,
                            css_framework='bootstrap5')

    if form.submit.data:
        # セッション情報として絞り込み条件
        session['search_register_num'] = {
            'start_date': form.start_date.data.strftime('%Y-%m-%d')
            if form.start_date.data else None,
            'end_date': form.end_date.data.strftime('%Y-%m-%d')
            if form.end_date.data else None,
            'finder_choice': form.finder_choice.data,
            'waiver': form.waiver.data,
        }
        return redirect(url_for("refund.register_num"))

    if form.submit_register.data:
        item_ids = request.form.getlist('item_ids')
        session['item_ids'] = item_ids
        items = db.session.query(LostItem).filter(LostItem.id.in_(item_ids)).all()
        for item in items:
            item.receiptnumber = form.receiptnumber.data
            item.refund_expect = form.refund_expect.data
            item.refund_situation = "還付予定"
        db.session.commit()
        return redirect(url_for("refund.register_num"))
    return render_template("refund/index.html", all_lost_item=rows, form=form,
                           pagination=pagination)


# 還付処理
@refund.route("/refund_item", methods=["POST", "GET"])
def refund_item():
    # Userの一覧取得
    users = User.query.all()
    user_choice = [(user.username) for user in users]
    form = RefundItemForm()
    form.refund_manager.choices = [("選択してください")] + user_choice
    search_results = session.get('search_refund_item', None)
    if search_results is None:
        query = db.session.query(LostItem)
        query = query.filter(LostItem.refund_situation != "対応済")
        query = query.filter(LostItem.refund_situation != "還付済")
        query = query.filter(LostItem.refund_situation == "還付予定")
        query = query.filter(LostItem.item_situation != "返還済み")
        search_results = query.all()
    else:
        start_date = search_results['start_date']
        end_date = search_results['end_date']
        receiptnumber = search_results['receiptnumber']
        refund_expect = search_results['refund_expect']
        returned = search_results['returned']
        item_plice = search_results['item_plice']
        item_feature = search_results['item_feature']
        # クエリの生成
        query = db.session.query(LostItem)
        if start_date and end_date:
            query = query.filter(LostItem.get_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(LostItem.get_item >= start_date)
        elif end_date:
            query = query.filter(LostItem.get_item <= end_date)
        if receiptnumber:
            query = query.filter(LostItem.receiptnumber == receiptnumber)
        if refund_expect:
            query = query.filter(func.date(LostItem.refund_expect) == refund_expect)
        if not returned:
            query = query.filter(LostItem.refund_situation != "対応済")
            query = query.filter(LostItem.refund_situation != "還付済")
            query = query.filter(LostItem.refund_situation == "還付予定")
        else:
            query = query.filter(LostItem.refund_situation != "NULL")
        if item_plice:
            query = query.filter(LostItem.item_value is True)
        if item_feature:
            query = query.filter(LostItem.item_feature.ilike(f"%{item_feature}%"))
        query = query.filter(LostItem.item_situation != "返還済み")
        search_results = query.all()

    # ページネーション処理
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1)*50: page*50]
    pagination = Pagination(page=page, total=len(search_results), per_page=50,
                            css_framework='bootstrap5')

    if form.submit.data:
        # セッション情報として絞り込み条件
        session['search_refund_item'] = {
            'start_date': form.start_date.data.strftime('%Y-%m-%d')
            if form.start_date.data else None,
            'end_date': form.end_date.data.strftime('%Y-%m-%d')
            if form.end_date.data else None,
            'receiptnumber': form.receiptnumber.data,
            'refund_expect': form.refund_expect.data.strftime('%Y-%m-%d')
            if form.refund_expect.data else None,
            'returned': form.returned.data,
            'item_plice': form.item_plice.data,
            'item_feature': form.item_feature.data,
        }
        return redirect(url_for("refund.refund_item"))

    if form.submit_register.data:
        if form.refund_manager.data != "選択してください":
            item_ids = request.form.getlist('item_ids')
            session['item_ids'] = item_ids
            police_item_ids = request.form.getlist('police_item_ids')
            session['police_item_ids'] = police_item_ids
            items = db.session.query(LostItem).filter(LostItem.id.in_(item_ids)).all()
            police_items = (
                db.session.query(LostItem)
                .filter(LostItem.id.in_(police_item_ids)).all()
                )
            for item in items:
                item.refund_situation = "還付済"
                item.refund_date = form.refund_date.data
                item.refund_manager = form.refund_manager.data
            db.session.commit()
            for item in police_items:
                item.refund_date = form.refund_date.data
                item.refund_manager = form.refund_manager.data
                item.refund_situation = "対応済"
            db.session.commit()
            return redirect(url_for("refund.refund_item"))
        else:
            errors = "担当者を選択してください"
            return render_template("refund/refund_item.html",
                                   form=form, search_results=rows,
                                   pagination=pagination, errors=errors)
    return render_template("refund/refund_item.html",
                           form=form, search_results=rows, pagination=pagination)


# 還付済物件処理
@refund.route("/refunded", methods=["POST", "GET"])
def refunded():
    # Userの一覧取得
    users = User.query.all()
    user_choice = [(user.username) for user in users]
    form = RefundedForm()
    form.refunded_process_manager.choices = [("選択してください")] + user_choice
    form.refunded_process_sub_manager.choices = [("選択してください")] + user_choice
    search_results = session.get('search_refunded', None)
    if search_results is None:
        # クエリの生成
        query = db.session.query(LostItem)
        query = query.filter(LostItem.refund_situation == "還付済")
        query = query.filter(LostItem.item_situation != "返還済み")
        search_results = query.all()
    else:
        start_date = search_results['start_date']
        end_date = search_results['end_date']
        refund_date = search_results['refund_date']
        police_date = search_results['police_date']
        refunded_process = search_results['refunded_process']
        refunded_bool = search_results['refunded_bool']
        # クエリの生成
        query = db.session.query(LostItem)
        if start_date and end_date:
            query = query.filter(LostItem.get_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(LostItem.get_item >= start_date)
        elif end_date:
            query = query.filter(LostItem.get_item <= end_date)
        if refund_date:
            query = query.filter(func.date(LostItem.refund_date) == refund_date)
        if police_date:
            query = query.filter(LostItem.police_date == police_date)
        if refunded_process != '':
            query = query.filter(LostItem.refunded_process == refunded_process)
        if not refunded_bool:
            query = query.filter(LostItem.refund_situation != "処理済")
            query = query.filter(LostItem.refund_situation == "還付済")
        else:
            query = query.filter(or_(LostItem.refund_situation == "処理済",
                                     LostItem.refund_situation == "還付済"))
        query = query.filter(LostItem.item_situation != "返還済み")
        search_results = query.all()

    # ページネーション処理
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1)*50: page*50]
    pagination = Pagination(page=page, total=len(search_results), per_page=50,
                            css_framework='bootstrap5')

    if form.submit.data:
        # セッション情報として絞り込み条件
        session['search_refunded'] = {
            'start_date': form.start_date.data.strftime('%Y-%m-%d')
            if form.start_date.data else None,
            'end_date': form.end_date.data.strftime('%Y-%m-%d')
            if form.end_date.data else None,
            'refund_date': form.refund_date.data.strftime('%Y-%m-%d')
            if form.refund_date.data else None,
            'police_date': form.police_date.data.strftime('%Y-%m-%d')
            if form.police_date.data else None,
            'refunded_process': form.refunded_process.data,
            'refunded_bool': form.refunded_bool.data,
        }
        return redirect(url_for("refund.refunded"))
    if form.submit2.data:
        if (form.refunded_process_manager.data != "選択してください" and
                form.refunded_process_sub_manager.data != "選択してください"):
            item_ids = request.form.getlist('item_ids')
            items = db.session.query(LostItem).filter(LostItem.id.in_(item_ids)).all()
            for item in items:
                select_value = request.form.get(f'item_select_{item.id}')
                item.refund_situation = "処理済"
                item.refunded_process = select_value
                item.refunded_process_manager = form.refunded_process_manager.data
                item.refunded_process_sub_manager = \
                    form.refunded_process_sub_manager.data
                item.refunded_date = datetime.now().date()
            db.session.commit()
            return redirect(url_for('refund.refunded'))
        else:
            flash("担当者を入力してください")
            return redirect(url_for('refund.refunded'))
    if form.submit3.data:
        if form.choice_refunded_process.data != "":
            session['choice_process'] = form.choice_refunded_process.data
            return redirect(url_for('refund.refunded_print'))
        return redirect(url_for('refund.refunded'))
    return render_template("refund/refunded.html", form=form,
                           search_results=rows, pagination=pagination)


# 印刷選択画面
# 還付後処理によって印刷する書類を分ける
@refund.route("/refunded/print", methods=["POST", "GET"])
def refunded_print():
    choice_process = session.get('choice_process', None)
    form = RefundedPrint()
    search_results = session.get('search_print', None)
    if search_results is None:
        # クエリの生成
        query = db.session.query(LostItem)
        query = query.filter(LostItem.refunded_process == choice_process)
        search_results = query.all()
    else:
        start_date = search_results['start_date']
        end_date = search_results['end_date']
        # クエリの生成
        query = db.session.query(LostItem)
        if start_date and end_date:
            query = query.filter(LostItem.get_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(LostItem.get_item >= start_date)
        elif end_date:
            query = query.filter(LostItem.get_item <= end_date)
        query = query.filter(LostItem.refunded_process == choice_process)
        search_results = query.all()

    # ページネーション処理
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1)*50: page*50]
    pagination = Pagination(page=page, total=len(search_results), per_page=50,
                            css_framework='bootstrap5')

    if form.submit_search.data:
        session['search_print'] = {
            'start_date': form.start_date.data.strftime('%Y-%m-%d')
            if form.start_date.data else None,
            'end_date': form.end_date.data.strftime('%Y-%m-%d')
            if form.end_date.data else None,
        }
        return redirect(url_for("refund.refunded_print"))

    if form.submit.data:
        item_ids = request.form.getlist('item_ids')
        session['item_ids'] = item_ids
        items = db.session.query(LostItem).filter(LostItem.id.in_(item_ids)).all()
        if choice_process == "店長":
            make_refunded_list_manager(items)
        elif choice_process == "廃棄":
            make_refunded_list_disposal(items)
        elif choice_process == "入金":
            make_refunded_list_money(items)
        elif choice_process == "本部":
            make_refunded_list_HQ(items)
        elif choice_process == "保留":
            make_refunded_list_hold(items)
        elif choice_process == "警処":
            make_refunded_list_police(items)
        return redirect(url_for("refund.refunded_print"))
    return render_template("refund/refunded_print.html", search_results=rows,
                           form=form, pagination=pagination)


# 還付請求一覧
@refund.route("/refund_list", methods=["POST", "GET"])
def refund_list():
    search_results = session.get('search_refund_list', None)
    if search_results is None:
        # クエリの生成
        query = db.session.query(LostItem)
        query = query.filter(LostItem.refund_situation == "還付予定")
        query = query.filter(LostItem.item_situation != "返還済み")
        search_results = query.all()
    else:
        refund_expect_year = search_results['refund_expect_year']
        refund_situation = search_results['refund_situation']
        # クエリの生成
        query = db.session.query(LostItem)
        if refund_expect_year:
            query = query.filter(extract('year', LostItem.refund_expect) ==
                                 refund_expect_year)
        if refund_situation == "還付予定":
            query = query.filter(LostItem.refund_situation == "還付予定")
        else:
            query = query.filter(LostItem.refund_situation == "還付済")
        query = query.filter(LostItem.item_situation != "返還済み")
        search_results = query.all()

    # ページネーション処理
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = search_results[(page - 1)*50: page*50]
    pagination = Pagination(page=page, total=len(search_results), per_page=50,
                            css_framework='bootstrap5')

    form = RefundList()
    if form.submit.data:
        # セッション情報として絞り込み条件
        session['search_refund_list'] = {
            'refund_expect_year': form.refund_expect_year.data,
            'refund_situation': form.refund_situation.data,
        }
        return redirect(url_for("refund.refund_list"))

    if form.submit_list.data:
        item_ids = request.form.getlist('item_ids')
        session['item_ids'] = item_ids
        items = db.session.query(LostItem).filter(LostItem.id.in_(item_ids)).all()
        make_pdf_refund_items(items)
        return redirect(url_for("refund.refund_list", items=items))
    return render_template("refund/refund_list.html", search_results=rows,
                           form=form, pagination=pagination)
