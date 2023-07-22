import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, redirect, render_template, url_for
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from apps.app import db
from apps.register.models import LostItem
from apps.return_item.forms import LostNote

basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "PDFfile"))

return_item = Blueprint(
    "return_item",
    __name__,
    template_folder="templates",
    static_folder="static",
)

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))


# PDFの作成
@return_item.route("/makepdf/<item_id>")
def make_pdf(item_id):
    item = LostItem.query.filter_by(id=item_id).first()

    file_name = datetime.now().strftime("%Y%m%d_%H%M%S") + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    p = canvas.Canvas(file_path, pagesize=letter)

    # ここからPDF
    textobject = p.beginText()
    textobject.setTextOrigin(50, 500)

    textobject.setFont('HeiseiMin-W3', 12)

    textobject.textLine("遺失物受領確認書")
    textobject.textLine("受領者: " + item.recep_manager)
    textobject.textLine("アイテム名: " + item.item_class_S)
    textobject.textLine("アイテムの詳細: " + item.item_feature)
    textobject.textLine("発見日: " + str(item.get_item))

    p.drawText(textobject)

    # Close the PDF object cleanly.
    p.showPage()
    p.save()

    return "PDF receipt saved as " + file_name


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
