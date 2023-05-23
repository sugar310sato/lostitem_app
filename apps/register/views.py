import base64
import os
from pathlib import Path

from flask import (Blueprint, current_app, render_template, request,
                   send_from_directory)

basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "images"))

register = Blueprint(
    "register",
    __name__,
    template_folder="templates",
)


# ホーム画面
@register.route("/")
def index():
    return render_template("register/index.html")


# 写真登録画面
@register.route("/photo")
def photo():
    return render_template("register/photo.html")


# 実際の保存処理
@register.route("/upload", methods=['POST'])
def upload():
    image_data = request.json['image']
    image_data = image_data.replace("data:image/jpeg;base64,", "")

    # 画像の保存処理
    filename = 'captured_image.jpg'  # 保存するファイル名を指定してください
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(save_path, 'wb') as f:
        f.write(base64.b64decode(image_data))

    return {'message': '画像を保存しました'}


# 拾得物の情報登録
@register.route("/register_item", methods=["POST", "GET"])
def register_item():
    return render_template("register/register_item.html")


# 画像の表示
@register.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(current_app.config["CARD_IMAGE_FOLDER"], filename)
