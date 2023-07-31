import os
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from apps.app import db
from apps.police.forms import MakeDocument, OptionDocument, PoliceForm
from apps.register.models import Denomination, LostItem

police = Blueprint(
    "police",
    __name__,
    template_folder="templates",
    static_folder="static",
)

basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "PDFfile"))


# 警察届出
@police.route("/items", methods=["POST", "GET"])
def item():
    # 一応返還済みでないすべての物品を出しています
    # 遺失者連絡済みの物を除外するためのFormなどは用意してあります
    all_lostitem = db.session.query(LostItem).all()
    form = PoliceForm()

    if form.submit.data:
        start_date = form.start_date.data
        end_date = form.end_date.data
        item_plice = form.item_plice.data
        item_finder = form.item_finder.data

        query = db.session.query(LostItem)
        if start_date and end_date:
            query = query.filter(LostItem.get_item.between(start_date, end_date))
        elif start_date:
            query = query.filter(LostItem.get_item >= start_date)
        elif end_date:
            query = query.filter(LostItem.get_item <= end_date)
        if item_plice is True:
            query = query.filter(LostItem.item_value is True)
        if item_finder != "すべて":
            if item_finder == "占有者":
                query = query.filter(LostItem.choice_finder == "占有者")
            else:
                query = query.filter(LostItem.choice_finder == "第三者")
        # 警察未届けの物のみ
        query = query.filter(LostItem.item_situation != "届出済み")
        search_results = query.all()
        session['search_results'] = [item.to_dict() for item in search_results]
        return redirect(url_for("police.item_search"))
    return render_template("police/index.html", all_lostitem=all_lostitem, form=form)


# 検索結果
@police.route("/items/search", methods=["POST", "GET"])
def item_search():
    search_results = session.get('search_results', [])

    form = MakeDocument()
    if form.submit.data:
        item_ids = request.form.getlist('item_ids')
        session['item_ids'] = item_ids
        return redirect(url_for('police.choice_document'))
    return render_template("police/search.html", search_results=search_results,
                           form=form)


# 作成書類選択
@police.route("/choice/document", methods=["POST", "GET"])
def choice_document():
    form = OptionDocument()
    if form.submit.data:
        if form.document.data == "占有者拾得物提出書":
            return redirect(url_for('police.make_data'))
        else:
            return redirect(url_for('police.make_data_third'))
    return render_template("police/choice_document.html", form=form)


# 警察届出用データ作成（占有者）
@police.route("/make/data", methods=["POST", "GET"])
def make_data():
    item_ids = session.get('item_ids', [])
    item_ids = [int(i) for i in item_ids]
    # Use in_ to filter rows where LostItem.id is in item_ids
    items = db.session.query(LostItem).filter(LostItem.id.in_(item_ids)).all()
    make_pdf_police(items)
    print(len(items))
    return "making PDF!"


# 警察届出用データ作成（第三者）
@police.route("/make/data/third", methods=["POST", "GET"])
def make_data_third():
    item_ids = session.get('item_ids', [])
    item_ids = [int(i) for i in item_ids]
    # Use in_ to filter rows where LostItem.id is in item_ids
    items = db.session.query(LostItem).filter(LostItem.id.in_(item_ids)).all()
    make_pdf_police_third(items)
    print(len(items))
    return "making PDF!"


# 警察届出用データ作成関数（占有者）
def make_pdf_police(items):
    file_name = "police_" + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    p = canvas.Canvas(file_path, pagesize=letter)
    # ヘッダー部分(表までのテンプレ)
    p.setFont('HeiseiMin-W3', 20)
    p.drawString(200, 750, "占有者拾得物　提出書")
    p.setFont('HeiseiMin-W3', 10)
    p.drawString(20, 710, "遺失物法第4条又は第13条の規定により、次の通り物件を提出します。")
    p.drawString(250, 690, "警察署長殿")
    p.drawRightString(550, 690, datetime.now().strftime("%Y年%m月%d日"))
    p.drawString(250, 670, "氏名又は名称")
    p.drawString(250, 650, "住所又は所在地")
    p.drawString(250, 620, "電話番号　その他連絡先")

    # 表の部分
    p.rect(20, 590, 100, 20), p.drawString(30, 595, "受理番号"), p.rect(120, 590, 100, 20)
    p.rect(20, 550, 100, 40), p.drawString(30, 565, "拾得者の名称等")
    p.rect(120, 550, 300, 40)
    p.rect(420, 550, 50, 40), p.drawString(430, 565, "権利"), p.rect(470, 550, 80, 40)
    p.drawString(480, 575, "1. 有権"), p.drawString(480, 555, "2. 失権"),
    p.setFont('HeiseiMin-W3', 15)
    p.drawString(476, 573, "〇")
    p.setFont('HeiseiMin-W3', 10)

    # 拾得物
    p.rect(20, 530, 40, 20), p.rect(60, 530, 300, 20), p.rect(360, 530, 80, 20),
    p.rect(440, 530, 70, 20), p.rect(510, 530, 70, 20)
    p.drawString(30, 535, "番号"), p.drawString(70, 535, "物件の種類及び特徴"),
    p.drawString(365, 535, "拾得日時・場所"), p.drawString(450, 535, "交付日時")
    p.drawString(520, 535, "管理番号")
    start_num = 460
    cnt = 1
    # 6個の枠の準備
    for i in range(6):
        if i >= len(items):
            p.line(20, start_num, 580, start_num+70)
        p.rect(20, start_num, 40, 70), p.rect(60, start_num+30, 300, 40)
        p.rect(360, start_num+30, 80, 40), p.rect(440, start_num+30, 70, 40)
        p.rect(510, start_num+30, 70, 40)
        p.drawString(40, start_num+30, str(cnt))
        cnt += 1

        p.drawString(70, start_num+17, "一万")
        p.drawString(70+42, start_num+17, "五千")
        p.drawString(70+42*2, start_num+17, "二千")
        p.drawString(73+42*3, start_num+17, "千")
        p.drawString(70+42*4, start_num+17, "五百")
        p.drawString(73+42*5, start_num+17, "百")
        p.drawString(70+42*6, start_num+17, "五十")
        p.drawString(73+42*7, start_num+17, "十")
        p.drawString(73+42*8, start_num+17, "五")
        p.drawString(73+42*9, start_num+17, "一")
        p.drawString(500, start_num+17, "合計金額")
        p.rect(480, start_num+15, 100, 15), p.rect(480, start_num, 100, 15)
        num = 0
        for i in range(10):
            p.rect(60+num, start_num+15, 42, 15), p.rect(60+num, start_num, 42, 15)
            num += 42
        start_num -= 70

    start_num = 460
    cnt = 0
    # 選択された拾得物の記入
    for item in items:
        denomination = Denomination.query.filter_by(lostitem_id=item.id).first()
        if denomination is not None:
            p.drawString(75, start_num+3, str(denomination.ten_thousand_yen))
            p.drawString(75+42, start_num+3, str(denomination.five_thousand_yen))
            p.drawString(75+42*2, start_num+3, str(denomination.two_thousand_yen))
            p.drawString(75+42*3, start_num+3, str(denomination.one_thousand_yen))
            p.drawString(75+42*4, start_num+3, str(denomination.five_hundred_yen))
            p.drawString(75+42*5, start_num+3, str(denomination.one_hundred_yen))
            p.drawString(75+42*6, start_num+3, str(denomination.fifty_yen))
            p.drawString(75+42*7, start_num+3, str(denomination.ten_yen))
            p.drawString(75+42*8, start_num+3, str(denomination.five_yen))
            p.drawString(75+42*9, start_num+3, str(denomination.one_yen))
            p.drawString(500, start_num+3, str(denomination.total_yen))
        p.drawString(70, start_num+55, item.item_class_S)
        p.drawString(70, start_num+40, item.item_feature)
        if item.get_item:
            p.drawString(370, start_num+55, item.get_item.strftime('%Y/%m/%d'))
        else:
            p.drawString(370, start_num+55, "")
        p.drawString(370, start_num+40, item.find_area)
        p.drawString(520, start_num+55, str(item.id))
        start_num -= 70

    # 備考欄
    p.drawString(30, 60, "備考")
    p.rect(20, 20, 40, 90), p.rect(60, 20, 520, 90)
    p.drawString(70, 50, "権利放棄：報労金の放棄"), p.drawString(70, 30, "告知区分：同意する")

    # Close the PDF object cleanly.
    p.showPage()
    p.save()

    return "PDF receipt saved as " + file_name


# 警察届出用データ作成関数（第三者）
def make_pdf_police_third(items):
    pages = 1
    for item in items:
        file_name = "test" + '.pdf'
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        p = canvas.Canvas(file_path, pagesize=letter)
        # ヘッダー部分(表までのテンプレ)
        p.setFont('HeiseiMin-W3', 20)
        p.drawString(200, 750, "第三者拾得物　提出書")
        p.setFont('HeiseiMin-W3', 10)
        p.drawString(20, 710, "遺失物法第4条又は第13条の規定により、次の通り物件を提出します。")
        p.drawString(250, 690, "警察署長殿")
        p.drawRightString(550, 690, datetime.now().strftime("%Y年%m月%d日"))
        p.drawString(250, 670, "氏名又は名称")
        p.drawString(250, 650, "住所又は所在地")
        p.drawString(250, 620, "電話番号　その他連絡先")

        # 表の部分
        p.rect(20, 590, 100, 20), p.drawString(30, 595, "受理番号"),
        p.rect(120, 590, 100, 20)
        p.rect(20, 550, 100, 40), p.drawString(30, 565, "拾得者の名称等")
        p.rect(120, 550, 300, 40)
        p.rect(420, 550, 50, 40), p.drawString(430, 565, "権利"), p.rect(470, 550, 80, 40)
        p.drawString(480, 575, "1. 有権"), p.drawString(480, 555, "2. 失権"),
        p.setFont('HeiseiMin-W3', 15)
        p.drawString(476, 573, "〇")
        p.setFont('HeiseiMin-W3', 10)

        # 拾得物
        p.rect(20, 530, 40, 20), p.rect(60, 530, 300, 20), p.rect(360, 530, 80, 20),
        p.rect(440, 530, 70, 20), p.rect(510, 530, 70, 20)
        p.drawString(30, 535, "番号"), p.drawString(70, 535, "物件の種類及び特徴"),
        p.drawString(365, 535, "拾得日時・場所"), p.drawString(450, 535, "交付日時")
        p.drawString(520, 535, "管理番号")
        start_num = 460
        cnt = 1
        # 6個の枠の準備
        for i in range(6):
            if i >= 1:
                p.line(20, start_num, 580, start_num+70)
            p.rect(20, start_num, 40, 70), p.rect(60, start_num+30, 300, 40)
            p.rect(360, start_num+30, 80, 40), p.rect(440, start_num+30, 70, 40)
            p.rect(510, start_num+30, 70, 40)
            p.drawString(40, start_num+30, str(cnt))
            cnt += 1

            p.drawString(70, start_num+17, "一万")
            p.drawString(70+42, start_num+17, "五千")
            p.drawString(70+42*2, start_num+17, "二千")
            p.drawString(73+42*3, start_num+17, "千")
            p.drawString(70+42*4, start_num+17, "五百")
            p.drawString(73+42*5, start_num+17, "百")
            p.drawString(70+42*6, start_num+17, "五十")
            p.drawString(73+42*7, start_num+17, "十")
            p.drawString(73+42*8, start_num+17, "五")
            p.drawString(73+42*9, start_num+17, "一")
            p.drawString(500, start_num+17, "合計金額")
            p.rect(480, start_num+15, 100, 15), p.rect(480, start_num, 100, 15)
            num = 0
            for i in range(10):
                p.rect(60+num, start_num+15, 42, 15), p.rect(60+num, start_num, 42, 15)
                num += 42
            start_num -= 70

        start_num = 460
        cnt = 0
        # 選択された拾得物の記入
        denomination = Denomination.query.filter_by(lostitem_id=item.id).first()
        if denomination is not None:
            p.drawString(75, start_num+3, str(denomination.ten_thousand_yen))
            p.drawString(75+42, start_num+3, str(denomination.five_thousand_yen))
            p.drawString(75+42*2, start_num+3, str(denomination.two_thousand_yen))
            p.drawString(75+42*3, start_num+3, str(denomination.one_thousand_yen))
            p.drawString(75+42*4, start_num+3, str(denomination.five_hundred_yen))
            p.drawString(75+42*5, start_num+3, str(denomination.one_hundred_yen))
            p.drawString(75+42*6, start_num+3, str(denomination.fifty_yen))
            p.drawString(75+42*7, start_num+3, str(denomination.ten_yen))
            p.drawString(75+42*8, start_num+3, str(denomination.five_yen))
            p.drawString(75+42*9, start_num+3, str(denomination.one_yen))
            p.drawString(500, start_num+3, str(denomination.total_yen))
        p.drawString(70, start_num+55, item.item_class_S)
        p.drawString(70, start_num+40, item.item_feature)
        if item.get_item:
            p.drawString(370, start_num+55, item.get_item.strftime('%Y/%m/%d'))
        else:
            p.drawString(370, start_num+55, "")
        p.drawString(370, start_num+40, item.find_area)
        p.drawString(520, start_num+55, str(item.id))
        start_num -= 70

        # 備考欄
        p.drawString(30, 60, "備考")
        p.rect(20, 20, 40, 90), p.rect(60, 20, 520, 90)
        p.drawString(70, 95, "氏名："), p.drawString(100, 95, item.finder_name)
        if item.finder_post:
            p.drawString(70, 80, "住所："), p.drawString(100, 80, item.finder_post)
        if item.finder_tel1:
            p.drawString(70, 65, "連絡先："), p.drawString(110, 65, item.finder_tel1)
        p.drawString(70, 50, "権利放棄：報労金の放棄"), p.drawString(70, 30, "告知区分：同意する")

        # Close the PDF object cleanly.
        p.showPage()
        p.save()
        pages += 1

    return "PDF receipt saved as " + file_name
