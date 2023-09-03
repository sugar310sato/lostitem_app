import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from apps.register.models import Denomination

basedir = Path(__file__).parent.parent
# 各種還付後処理保存先
UPLOAD_FOLDER_REFUNDED = str(Path(basedir, "PDFfile", "refund_list_file", "refunded"))
UPLOAD_FOLDER_REFUNDED_MANAGER = str(Path(UPLOAD_FOLDER_REFUNDED, "店長渡し一覧表"))
UPLOAD_FOLDER_REFUNDED_DISPOSAL = str(Path(UPLOAD_FOLDER_REFUNDED, "廃棄物品一覧表"))
UPLOAD_FOLDER_REFUNDED_MONEY = str(Path(UPLOAD_FOLDER_REFUNDED, "入金物品一覧表"))
UPLOAD_FOLDER_REFUNDED_HQ = str(Path(UPLOAD_FOLDER_REFUNDED, "本部預物件一覧表"))
UPLOAD_FOLDER_REFUNDED_HOLD = str(Path(UPLOAD_FOLDER_REFUNDED, "保留物品一覧表"))
UPLOAD_FOLDER_REFUNDED_POLICE = str(Path(UPLOAD_FOLDER_REFUNDED, "警察処分物品一覧表"))
# 還付請求一覧
UPLOAD_FOLDER_REFUND_ITEM = str(Path(basedir, "PDFfile", "refund_list_file",
                                     "refund_item"))


def draw_table(p, start_num, items):
    items_per_page = 20
    item_count = 0

    for item in items:
        p.rect(20, start_num, 70, 30), p.rect(90, start_num, 80, 30)
        p.rect(170, start_num, 80, 30), p.rect(250, start_num, 70, 30)
        p.rect(320, start_num, 260, 30)

        if item.refunded_date:
            p.drawCentredString(55, start_num+10,
                                item.refunded_date.strftime('%Y/%m/%d'))
        else:
            p.drawCentredString(55, start_num+10, "")
        p.drawCentredString(130, start_num+10, str(item.main_id))
        p.drawCentredString(205, start_num+17, item.refunded_process_manager)
        p.drawCentredString(205, start_num+5, item.refunded_process_sub_manager)
        if item.get_item:
            p.drawCentredString(285, start_num+10, item.get_item.strftime('%Y/%m/%d'))
        else:
            p.drawCentredString(285, start_num+10, "")
        p.drawCentredString(450, start_num+17, item.item_class_S)
        p.drawCentredString(450, start_num+5, item.item_feature)
        item_count += 1
        start_num -= 30

        # 1ページに追加する項目数が上限に達した場合、新しいページを作成
        if item_count >= items_per_page:
            p.showPage()  # 新しいページを作成
            p.setFont('HeiseiMin-W3', 10)
            start_num = 680  # Y座標をリセット
            item_count = 0  # 項目数をリセット
            p.rect(20, 710, 70, 30), p.rect(90, 710, 80, 30), p.rect(170, 710, 80, 30)
            p.rect(250, 710, 70, 30), p.rect(320, 710, 260, 30)
            p.drawCentredString(55, 720, "処理日"), p.drawCentredString(130, 720, "管理番号")
            p.drawCentredString(205, 727, "処理担当者1"), p.drawCentredString(205, 715,
                                                                         "処理担当者2")
            p.drawCentredString(285, 720, "拾得日時"), p.drawCentredString(450, 720,
                                                                       "物件の種類及び特徴")


def make_pdf(file_path, header_title, items):
    p = canvas.Canvas(file_path, pagesize=A4)
    p.setFont('HeiseiMin-W3', 20)
    p.drawCentredString(300, 780, header_title)
    p.setFont('HeiseiMin-W3', 10)
    p.drawString(500, 760, datetime.now().strftime("%Y年%m月%d日"))

    # 表の部分の描画
    p.rect(20, 710, 70, 30), p.rect(90, 710, 80, 30), p.rect(170, 710, 80, 30)
    p.rect(250, 710, 70, 30), p.rect(320, 710, 260, 30)
    p.drawCentredString(55, 720, "処理日"), p.drawCentredString(130, 720, "管理番号")
    p.drawCentredString(205, 727, "処理担当者1"), p.drawCentredString(205, 715, "処理担当者2")
    p.drawCentredString(285, 720, "拾得日時"), p.drawCentredString(450, 720, "物件の種類及び特徴")

    # 表の作成
    draw_table(p, 680, items)

    p.showPage()
    p.save()


# 店長渡し一覧表
# 横幅は20-580くらい
def make_refunded_list_manager(items):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "refunded" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER_REFUNDED_MANAGER, file_name)
    make_pdf(file_path, "店長渡し一覧", items)
    return "PDF receipt saved as " + file_name


# 廃棄物品一覧表
def make_refunded_list_disposal(items):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "refunded" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER_REFUNDED_DISPOSAL, file_name)
    make_pdf(file_path, "廃棄物品一覧", items)
    return "PDF receipt saved as " + file_name


# 入金物品一覧表
def make_refunded_list_money(items):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "refunded" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER_REFUNDED_MONEY, file_name)
    make_pdf(file_path, "入金物品一覧", items)
    return "PDF receipt saved as " + file_name


# 本部預物件一覧表
def make_refunded_list_HQ(items):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "refunded" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER_REFUNDED_HQ, file_name)
    make_pdf(file_path, "本部預物件一覧", items)
    return "PDF receipt saved as " + file_name


# 保留物品一覧表
def make_refunded_list_hold(items):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "refunded" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER_REFUNDED_HOLD, file_name)
    make_pdf(file_path, "保留物品一覧", items)
    return "PDF receipt saved as " + file_name


# 警察処分物品一覧表
def make_refunded_list_police(items):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "refunded" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER_REFUNDED_POLICE, file_name)
    make_pdf(file_path, "警察処分物品一覧", items)
    return "PDF receipt saved as " + file_name


# 還付請求一覧
def make_pdf_refund_items(items):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = "refund_item" + current_time + '.pdf'
    file_path = os.path.join(UPLOAD_FOLDER_REFUND_ITEM, file_name)
    p = canvas.Canvas(file_path, pagesize=landscape(A4))
    # ヘッダー部分(表までのテンプレ)
    p.setFont('HeiseiMin-W3', 20)
    p.drawString(350, 550, "還付請求一覧")
    p.setFont('HeiseiMin-W3', 10)
    p.drawString(750, 520, datetime.now().strftime("%Y年%m月%d日"))

    # 表の部分
    p.rect(20, 480, 80, 20), p.rect(100, 480, 80, 20), p.rect(180, 480, 80, 20)
    p.rect(260, 480, 80, 20), p.rect(340, 480, 80, 20), p.rect(420, 480, 320, 20)
    p.rect(740, 480, 80, 20)
    p.drawCentredString(60, 485, "還付予定日"), p.drawCentredString(140, 485, "受理番号")
    p.drawCentredString(220, 485, "警察届出日"), p.drawCentredString(300, 485, "拾得日時")
    p.drawCentredString(380, 485, "管理番号"), p.drawCentredString(580, 485, "物件の種類及び特徴")
    p.drawCentredString(780, 485, "金額")

    start_num = 450

    # 拾得物の内容記載
    for item in items:
        p.rect(20, start_num, 80, 30), p.rect(100, start_num, 80, 30)
        p.rect(180, start_num, 80, 30), p.rect(260, start_num, 80, 30)
        p.rect(340, start_num, 80, 30), p.rect(420, start_num, 320, 30)
        p.rect(740, start_num, 80, 30)

        denomination = Denomination.query.filter_by(lostitem_id=item.id).first()
        if item.refunded_date:
            p.drawCentredString(50, start_num+10,
                                item.refunded_date.strftime('%Y/%m/%d'))
        else:
            p.drawCentredString(50, start_num+10, "")
        p.drawCentredString(140, start_num+10, str(item.receiptnumber))
        if item.police_date:
            p.drawCentredString(220, start_num+10,
                                item.police_date.strftime('%Y/%m/%d'))
        else:
            p.drawCentredString(220, start_num+10, "")
        if item.get_item:
            p.drawCentredString(300, start_num+10, item.get_item.strftime('%Y/%m/%d'))
        else:
            p.drawCentredString(300, start_num+10, "")
        p.drawCentredString(380, start_num+10, str(item.main_id))
        p.drawCentredString(580, start_num+17, item.item_class_S)
        p.drawCentredString(580, start_num+5, item.item_feature)
        if denomination is not None:
            p.drawCentredString(780, start_num+10, str(denomination.total_yen))
        start_num -= 30

    # Close the PDF object cleanly.
    p.showPage()
    p.save()

    return "PDF receipt saved as " + file_name
