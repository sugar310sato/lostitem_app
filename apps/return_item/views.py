import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, redirect, render_template, url_for
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from apps.app import db
from apps.register.models import LostItem
from apps.return_item.forms import LostNote, ReturnItemForm

basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "PDFfile"))

return_item = Blueprint(
    "return_item",
    __name__,
    template_folder="templates",
    static_folder="static",
)

basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "PDFfile", "return_item_file"))

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))


# 受領書印刷
@return_item.route("/makepdf/<item_id>", methods=["POST", "GET"])
def make_pdf(item_id):
    lostitem = LostItem.query.filter_by(id=item_id).first()
    make_return_pdf(lostitem)
    return redirect(url_for("return_item.item", item_id=lostitem.id))


def make_return_pdf(item):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "return" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    p = canvas.Canvas(file_path, pagesize=A4)
    p.setFont('HeiseiMin-W3', 20)
    p.drawString(220, 800, "遺失物受領確認書")
    p.setFont('HeiseiMin-W3', 10)
    p.drawString(225, 790, "Confirmation receipt of Lost article")
    p.drawString(20, 770, "下記の遺失物確かに受領いたしました。")
    p.drawString(20, 758, "[I received the following lost article]")
    p.drawString(20, 730, "問い合わせ番号"), p.drawString(20, 718, "[Inquiry number]")
    p.drawString(30, 700, "受領日（返還日）"), p.drawString(30, 688,
                                                    "[Date recieved(Date of return)]")
    p.drawString(200, 695, "______年 ______月 ______日 ( ______ 曜日 )")
    p.drawString(30, 670, "受領時間"), p.drawString(30, 658, "[Time recieved]")
    p.drawString(200, 665, "______時 ______分")
    p.drawString(30, 640, "氏名"), p.drawString(30, 628, "[Name]")
    p.drawString(200, 635, "_______________________様       印")
    p.drawString(30, 610, "郵便番号"), p.drawString(30, 598, "[Post code]")
    p.drawString(200, 605, "〒_________ー_________")
    p.drawString(30, 580, "住所"), p.drawString(30, 568, "[Address]")
    p.drawString(200, 575, "__________________________________________________________")
    p.drawString(30, 550, "電話番号"), p.drawString(30, 538, "[Telephone number]")
    p.drawString(200, 545, "__________________________________")

    # 拾得物詳細
    p.drawString(20, 500, "拾得物詳細")
    p.drawString(30, 480, "管理No"), p.drawString(100, 480, str(item.main_id))
    p.drawString(30, 460, "拾得日")
    if item.get_item:
        p.drawString(100, 460, item.get_item.strftime('%Y/%m/%d'))
    p.drawString(30, 440, "拾得時間"), p.drawString(100, 440, item.get_item_hour)
    p.drawString(120, 440, item.get_item_minute)
    p.drawString(30, 420, "拾得場所"), p.drawString(100, 420, item.find_area)
    p.drawString(30, 400, "拾得物名"), p.drawString(100, 400, item.item_class_L + " " +
                                                item.item_class_M + " " +
                                                item.item_class_S)

    p.drawString(20, 300, "※記載された個人情報は、お客様へのご連絡以外の目的には利用いたしません。")

    # 担当者記入欄
    p.drawString(20, 120, "担当者記入欄")
    p.drawString(30, 95, "本人確認書類    □運転免許証   □パスポート   □保険証   □その他(______________)")
    p.drawString(30, 70, "返還担当者署名    ______________________________________     印")
    p.showPage()
    p.save()

    return "making PDF"


# 拾得物の返還/遺失者連絡
@return_item.route("/item/<item_id>", methods=["POST", "GET"])
def item(item_id):
    lostitem = LostItem.query.filter_by(id=item_id).first()
    return render_template("return_item/index.html", lostitem=lostitem)


# 遺失者連絡
@return_item.route("/item/<item_id>/note", methods=["POST", "GET"])
def note(item_id):
    lostitem = LostItem.query.filter_by(id=item_id).first()
    form = LostNote()

    if form.submit.data:
        lostitem.item_situation = "遺失者連絡済み"
        lostitem.lost_date = form.lost_date.data
        lostitem.lost_hour = form.lost_hour.data
        lostitem.lost_minute = form.lost_minute.data
        lostitem.lost_area = form.lost_area.data
        lostitem.recep_item = form.recep_item.data
        lostitem.recep_item_hour = form.recep_item_hour.data
        lostitem.recep_item_minute = form.recep_item_minute.data
        lostitem.recep_manager = form.recep_manager.data
        lostitem.lost_person = form.lost_person.data
        lostitem.lost_class = form.lost_class.data
        lostitem.lost_affiliation = form.lost_affiliation.data
        lostitem.lost_tel1 = form.lost_tel1.data
        lostitem.lost_tel2 = form.lost_tel2.data
        lostitem.lost_post = form.lost_post.data
        lostitem.lost_address = form.lost_address.data
        lostitem.note_date = form.note_date.data
        lostitem.note_hour = form.note_hour.data
        lostitem.note_minute = form.note_minute.data
        lostitem.note_process = form.note_process.data
        lostitem.note_manager = form.note_manager.data
        lostitem.response_date = form.response_date.data
        lostitem.response_hour = form.response_hour.data
        lostitem.response_minute = form.response_minute.data
        lostitem.response_expect = form.response_expect.data
        lostitem.response_content = form.response_content.data
        lostitem.response_remarks = form.response_remarks.data
        db.session.add(lostitem)
        db.session.commit()
        return redirect(url_for('return_item.item', item_id=lostitem.id))
    return render_template("return_item/note.html", lostitem=lostitem, form=form)


# 返還処理
@return_item.route("/item/<item_id>/return_item", methods=["POST", "GET"])
def item_return(item_id):
    lostitem = LostItem.query.filter_by(id=item_id).first()
    form = ReturnItemForm()

    if form.submit.data:
        lostitem.item_situation = "返還済み"
        lostitem.return_date = form.return_date.data
        lostitem.return_check = form.return_check.data
        lostitem.return_person = form.return_person.data
        lostitem.return_address = form.return_address.data
        lostitem.return_tel = form.return_tel.data
        lostitem.return_manager = form.return_manager.data
        db.session.add(lostitem)
        db.session.commit()
        return redirect(url_for('return_item.item', item_id=lostitem.id))
    return render_template("return_item/return_item.html", lostitem=lostitem, form=form)
