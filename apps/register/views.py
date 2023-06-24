import base64
import os
import shutil
import uuid
from pathlib import Path

from flask import (Blueprint, current_app, redirect, render_template, request,
                   send_from_directory, url_for)

from apps.app import db
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


def save_image():
    # 画像の保存処理
    # 画像取得元
    source_folder = Path(current_app.root_path, "images")
    # 画像移動先フォルダ
    destination_folder = Path(current_app.root_path, "renamed_images")

    # ファイル名と拡張子を取得、ファイル名をuuidに
    originnl_filename = "captured_image.jpg"
    new_filename = str(uuid.uuid4())
    _, file_extention = os.path.splitext(originnl_filename)
    new_filename = new_filename + file_extention
    send_file = new_filename
    originnl_filename = os.path.join(source_folder, originnl_filename)
    new_filename = os.path.join(source_folder, new_filename)
    os.rename(originnl_filename, new_filename)

    # 画像の移動
    for file in os.listdir(source_folder):
        file_path = os.path.join(source_folder, new_filename)
        moved_path = shutil.move(file_path, destination_folder)

    # imagesに登録されている写真の削除
    sourcefoder = Path(current_app.root_path, "images")
    for filename in os.listdir(sourcefoder):
        file_path = os.path.join(sourcefoder, filename)
        os.unlink(file_path)

    return send_file


# ホーム画面
@register.route("/")
def index():
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
    if choice_finder == "占有者拾得":
        form = OwnerLostItemForm()
        # form.validate_on_submit()だとNULLをうまく受け付けてくれない
        # submit.dataとすることで、入力がない場合にも対応できる
        if form.submit.data:
            moved_path = save_image()
            ownerlostitem = LostItem(
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
                finder_tel1=form.finder_tel1.data,
                finder_tel2=form.finder_tel2.data,

                # 大中小項目の実装

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
                item_situation=form.item_situation.data,
                item_image=moved_path,
                finder_class=form.finder_class.data,
                finder_affiliation=form.finder_affiliation.data,
            )
            db.session.add(ownerlostitem)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=ownerlostitem.id))
    elif choice_finder == "第三者拾得":
        form = ThirdPartyLostItemForm()
        if form.submit.data:
            moved_path = save_image()
            thirdpartylostitem = LostItem(
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
                    finder_tel1=form.finder_tel1.data,
                    finder_tel2=form.finder_tel2.data,

                    # 大中小項目の実装

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
                    item_situation=form.item_situation.data,
                    item_image=moved_path,
                    thirdparty_waiver=form.thirdparty_waiver.data,
                    thirdparty_name_note=form.thirdparty_name_note.data,
            )
            db.session.add(thirdpartylostitem)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=thirdpartylostitem.id))
    return render_template("register/register_item.html", choice_finder=choice_finder,
                           form=form)


# 画像の表示
@register.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(current_app.config["CARD_IMAGE_FOLDER"], filename)
