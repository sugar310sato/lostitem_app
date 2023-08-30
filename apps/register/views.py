import base64
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, current_app, redirect, render_template, request,
                   send_from_directory, session, url_for)
from sqlalchemy import func

from apps.app import db
from apps.config import ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S
from apps.crud.models import User
from apps.register.forms import (ChoicesFinderForm, OwnerLostItemForm,
                                 ThirdPartyLostItemForm)
from apps.register.models import LostItem

basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "images"))

register = Blueprint(
    "register",
    __name__,
    template_folder="templates",
)


# 画像の保存処理
def save_image():
    source_folder = Path(current_app.root_path, "images")
    destination_folder = Path(current_app.root_path, "renamed_images")

    original_filename = "captured_image.jpg"
    new_filename = str(uuid.uuid4())
    _, file_extension = os.path.splitext(original_filename)
    new_filename = new_filename + file_extension

    original_filepath = os.path.join(source_folder, original_filename)
    new_filepath = os.path.join(source_folder, new_filename)

    # ファイルの名前を変更
    os.rename(original_filepath, new_filepath)

    # ファイルが存在する場合、移動
    destination_filepath = os.path.join(destination_folder, new_filename)
    if os.path.exists(destination_filepath):
        os.remove(destination_filepath)

    # 移動
    shutil.move(new_filepath, destination_folder)

    # .gitkeepファイル以外を削除
    for filename in os.listdir(source_folder):
        if filename == ".gitkeep":
            continue  # Skip .gitkeep file
        file_path = os.path.join(source_folder, filename)
        os.unlink(file_path)

    return new_filename


# ホーム画面
@register.route("/")
def index():
    session.pop('search_dislist', None)
    session.pop('search_item', None)
    session.pop('not_found_search', None)
    session.pop('search_polices', None)
    session.pop('item_ids', None)
    session.pop('search_register_num', None)
    session.pop('search_refund_item', None)
    session.pop('police_item_ids', None)
    session.pop('search_refunded', None)
    session.pop('search_refund_list', None)
    return render_template("register/index.html")


# 写真登録画面
@register.route("/photo")
def photo():
    return render_template("register/photo.html")


# 画像の保存
@register.route("/upload", methods=["POST"])
def upload():
    image_data = request.json['image']
    image_data = image_data.replace("data:image/jpeg;base64,", "")

    # 画像の保存処理
    filename = 'captured_image.jpg'  # 保存するファイル名を指定してください
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(save_path, 'wb') as f:
        f.write(base64.b64decode(image_data))

    return redirect(url_for("register.choices_finder"))


# 占有者拾得か第三者拾得か
@register.route("/choices_finder", methods=["POST", "GET"])
def choices_finder():
    form = ChoicesFinderForm()

    if form.validate_on_submit():
        choice_finder = form.choice_finder.data
        return redirect(url_for("register.register_item", choice_finder=choice_finder))
    return render_template("register/choices_finder.html", form=form)


# 拾得物の情報登録
@register.route("/register_item/<choice_finder>", methods=["POST", "GET"])
def register_item(choice_finder):
    current_year = datetime.now().year % 100
    main_id = generate_main_id(choice_finder, current_year)
    # Userの一覧取得
    users = User.query.all()
    user_choice = [(str(user.id), user.username) for user in users]

    if choice_finder == "占有者拾得":
        form = OwnerLostItemForm()
        form.recep_manager.choices = user_choice
        if form.submit.data:
            moved_path = save_image()
            ownerlostitem = LostItem(
                main_id=main_id,
                current_year=current_year,
                choice_finder=choice_finder,
                track_num=form.track_num.data,
                notify=form.notify.data,
                get_item=form.get_item.data,
                get_item_hour=form.get_item_hour.data,
                get_item_minute=form.get_item_minute.data,
                recep_item=form.recep_item.data,
                recep_item_hour=form.recep_item_hour.data,
                recep_item_minute=form.recep_item_minute.data,
                recep_manager=form.recep_manager.data,
                find_area=form.find_area.data,
                find_area_police=form.find_area_police.data,
                own_waiver=form.own_waiver.data,
                finder_name=form.finder_name.data,
                own_name_note=form.own_name_note.data,
                finder_age=form.finder_age.data,
                finder_sex=form.finder_sex.data,
                finder_post=form.finder_post.data,
                finder_address=form.finder_address.data,
                finder_tel1=form.finder_tel1.data,
                finder_tel2=form.finder_tel2.data,

                # 大中小項目の実装
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
                item_image=moved_path,
                finder_class=form.finder_class.data,
                finder_affiliation=form.finder_affiliation.data,
                item_situation="保管中",
                refund_situation="未",

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
            db.session.add(ownerlostitem)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=ownerlostitem.id))
    elif choice_finder == "第三者拾得":
        form = ThirdPartyLostItemForm()
        form.recep_manager.choices = user_choice
        if form.submit.data:
            moved_path = save_image()
            thirdpartylostitem = LostItem(
                main_id=main_id,
                current_year=current_year,
                choice_finder=choice_finder,
                track_num=form.track_num.data,
                notify=form.notify.data,
                get_item=form.get_item.data,
                get_item_hour=form.get_item_hour.data,
                get_item_minute=form.get_item_minute.data,
                recep_item=form.recep_item.data,
                recep_item_hour=form.recep_item_hour.data,
                recep_item_minute=form.recep_item_minute.data,
                recep_manager=form.recep_manager.data,
                find_area=form.find_area.data,
                find_area_police=form.find_area_police.data,
                own_waiver=form.own_waiver.data,
                finder_name=form.finder_name.data,
                own_name_note=form.own_name_note.data,
                finder_age=form.finder_age.data,
                finder_sex=form.finder_sex.data,
                finder_post=form.finder_post.data,
                finder_address=form.finder_address.data,
                finder_tel1=form.finder_tel1.data,
                finder_tel2=form.finder_tel2.data,

                # 大中小項目の実装
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
                item_image=moved_path,
                thirdparty_waiver=form.thirdparty_waiver.data,
                thirdparty_name_note=form.thirdparty_name_note.data,
                item_situation="保管中",
                refund_situation="未",

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
            db.session.add(thirdpartylostitem)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=thirdpartylostitem.id))
    return render_template("register/register_item.html", choice_finder=choice_finder,
                           form=form, ITEM_CLASS_L=ITEM_CLASS_L,
                           ITEM_CLASS_M=ITEM_CLASS_M, ITEM_CLASS_S=ITEM_CLASS_S)


# 識別番号の生成関数
def generate_main_id(choice_finder, current_year):
    # choice_finderとcurrent_yearが一致するレコードの数をカウント
    count = db.session.query(func.count(LostItem.id)
                             ).filter(LostItem.choice_finder == choice_finder,
                                      LostItem.current_year == current_year).scalar()
    if choice_finder == "占有者拾得":
        identifier = f"1{current_year:02}{count+1:05}"
    else:
        identifier = f"2{current_year:02}{count+1:05}"
    return identifier


# 画像の表示
@register.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(current_app.config["CARD_IMAGE_FOLDER"], filename)
