import base64
import os
import shutil
import uuid
import json
from datetime import datetime
from pathlib import Path

import requests
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
    flash,
)
from PIL import Image
from sqlalchemy import func

from apps.app import db
from apps.config import ITEM_CLASS_L, ITEM_CLASS_M, ITEM_CLASS_S, LAMBDA_ENDPOINT
from apps.crud.models import User
from apps.register.forms import (
    ChoicesFinderForm,
    OwnerLostItemForm,
    ThirdPartyLostItemForm,
    FreeFlowLostItemForm,
)
from apps.register.model_folder.predict import img2text
from apps.register.model_folder.yolo_predict import YOLOPredictor
from apps.register.models import LostItem

from . import send_s3

basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "images"))

register = Blueprint(
    "register",
    __name__,
    template_folder="templates",
)

# テンプレート保存用のディレクトリ
def get_template_dir():
    if current_app:
        return Path(current_app.root_path).parent / "templates"
    else:
        return Path(__file__).parent.parent.parent / "templates"


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


# AWS lambdaで画像認識する関数
def send_image_AWS(image_path):
    # 画像ファイルを開き、Base64にエンコード
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    # Lambda関数のエンドポイントURL
    try:
        # Lambda関数に送信
        response = requests.post(LAMBDA_ENDPOINT, json={"image": image_base64})
        if response.status_code == 200:
            return response.json()
        else:
            return "Error"
    except requests.exceptions.Timeout:
        print("timeout!")
        return "Error"
    except requests.exceptions.RequestException:
        print("Error!")
        return "Error"


# YOLOローカル推論で画像認識する関数
def predict_with_yolo(image_path, confidence_threshold=0.5):
    """
    YOLOを使用したローカル画像認識
    Args:
        image_path: 画像ファイルのパス
        confidence_threshold: 信頼度の閾値
    Returns:
        str: 予測されたカテゴリ名
    """
    try:
        # YOLOモデルの初期化（初回のみ）
        if not hasattr(predict_with_yolo, 'predictor'):
            model_path = Path(current_app.root_path, "register", "model_folder", "yolo_model.pt")
            predict_with_yolo.predictor = YOLOPredictor(model_path if model_path.exists() else None)
        
        # 推論実行
        result = predict_with_yolo.predictor.predict_item_category(image_path, confidence_threshold)
        
        if "error" in result:
            print(f"YOLO推論エラー: {result['error']}")
            return "その他"
        
        print(f"YOLO推論結果: {result['category']} (信頼度: {result['confidence']:.3f})")
        return result['category']
        
    except Exception as e:
        print(f"YOLO推論中にエラーが発生しました: {str(e)}")
        return "その他"


# ホーム画面
@register.route("/")
def index():
    session.pop("search_dislist", None)
    session.pop("search_item", None)
    session.pop("not_found_search", None)
    session.pop("search_polices", None)
    session.pop("item_ids", None)
    session.pop("search_register_num", None)
    session.pop("search_refund_item", None)
    session.pop("police_item_ids", None)
    session.pop("search_refunded", None)
    session.pop("search_refund_list", None)
    return render_template("register/index.html")


# 写真登録画面
@register.route("/photo")
def photo():
    return render_template("register/photo.html")


# 画像の保存
@register.route("/upload", methods=["POST"])
def upload():
    image_data = request.json["image"]
    if (
        request.json["inferenceResult"] != "None"
        and request.json["photoDiscription"] != "None"
    ):
        session["inferenceResult"] = request.json["inferenceResult"]
        session["photoDiscription"] = request.json["photoDiscription"]
    else:
        session["inferenceResult"] = "None"
        session["photoDiscription"] = "None"
    image_data = image_data.replace("data:image/jpeg;base64,", "")

    # 画像の保存処理
    filename = "captured_image.jpg"  # 保存するファイル名を指定してください
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(save_path, "wb") as f:
        f.write(base64.b64decode(image_data))

    return redirect(url_for("register.choices_finder"))


# 占有者拾得か第三者拾得か
@register.route("/choices_finder", methods=["POST", "GET"])
def choices_finder():
    form = ChoicesFinderForm()

    if form.validate_on_submit():
        choice_finder = form.choice_finder.data
        if form.use_AI.data:
            use_AI = "usenoAI"
        else:
            use_AI = "useAI"
        return redirect(
            url_for(
                "register.register_item", choice_finder=choice_finder, use_AI=use_AI
            )
        )
    return render_template("register/choices_finder.html", form=form)


# 拾得物の情報登録
@register.route("/register_item/<choice_finder>/<use_AI>", methods=["POST", "GET"])
def register_item(choice_finder, use_AI):
    current_year = datetime.now().year % 100
    main_id = generate_main_id(choice_finder, current_year)
    inferenceResult = session["inferenceResult"]
    photoDiscription = session["photoDiscription"]
    # Userの一覧取得
    users = User.query.all()
    user_choice = [(user.username) for user in users]
    print(use_AI)
    # AI推論による分類
    if use_AI == "usenoAI":
        text = ""
        result = "現金"
    else:
        root_path = Path(current_app.root_path, "images/captured_image.jpg")
        
        # CoCaによるキャプション生成（オプション）
        # model_path = Path(
        #     current_app.root_path, "register", "model_folder", "model.pth"
        # )
        # if model_path.exists():
        #     # img2text関数を実行してテキストを取得
        #     text = img2text(model_path, root_path)
        # else:
        #     text = ""
        text = ""
        
        # YOLOローカル推論（AWS Lambdaの代わり）
        result = predict_with_yolo(str(root_path))
        print(f"YOLO推論結果: {result}")
        # ラズパイでの推論
        # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # vgg_model_path = Path(
        #     current_app.root_path, "register", "model_folder", "vgg_model.pth"
        # )
        # model = models.vgg16(weights=False)
        # model.classifier[6] = nn.Linear(in_features=4096, out_features=26)
        # model.load_state_dict(torch.load(vgg_model_path))
        # model.to(device).eval()
        # idx_to_class = {
        #     0: "かばん類",
        #     1: "袋・封筒類",
        #     2: "カメラ類",
        #     3: "証明書類・カード類",
        #     4: "衣類・履物類",
        #     5: "生活用品類",
        #     6: "書類・紙類",
        #     7: "電気製品類",
        #     8: "食料品類",
        #     9: "めがね類",
        #     10: "趣味娯楽用品類",
        #     11: "医療・化粧品類",
        #     12: "携帯電話類",
        #     13: "手帳文具類",
        #     14: "小包・箱類",
        #     15: "有価証券類",
        #     16: "かさ類",
        #     17: "財布類",
        #     18: "著作品類",
        #     19: "カードケース類",
        #     20: "現金",
        #     21: "動植物類",
        #     22: "鍵類",
        #     23: "その他",
        #     24: "貴金属類",
        #     25: "時計類",
        # }
        # input_data = Image.open(root_path)
        # resize = 224
        # mean = (0.485, 0.456, 0.406)
        # std = (0.229, 0.224, 0.225)

        # transform = transforms.Compose(
        #     [
        #         transforms.Resize(resize),
        #         transforms.CenterCrop(resize),
        #         transforms.ToTensor(),
        #         transforms.Normalize(mean, std),
        #     ]
        # )

        # # 画像に変換と前処理を適用
        # input_data = transform(input_data).unsqueeze(0)
        # input_data = input_data.to(device)
        # with torch.no_grad():
        #     output = model(input_data)
        #     _, preds = torch.max(output, 1)
        # pred_class_name = idx_to_class[preds.item()]
        # result = pred_class_name

    if choice_finder == "占有者拾得":
        form = OwnerLostItemForm()
        form.recep_manager.choices = user_choice
        if text != "":
            form.item_feature.data = text
        if form.submit.data:
            moved_path = save_image()
            s3_image_path = os.path.join(basedir, "renamed_images", moved_path)
            send_s3.send_image_S3(s3_image_path, request.form.get("item_class_L"))
            ownerlostitem = LostItem(
                main_id=main_id,
                current_year=current_year,
                choice_finder=choice_finder,
                # track_num=form.track_num.data,
                notify=form.notify.data,
                get_item=form.get_item.data,
                get_item_hour=request.form.get("get_item_hours"),
                get_item_minute=request.form.get("get_item_minutes"),
                recep_item=form.recep_item.data,
                recep_item_hour=request.form.get("recep_item_hours"),
                recep_item_minute=request.form.get("recep_item_minutes"),
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
                item_class_L=request.form.get("item_class_L"),
                item_class_M=request.form.get("item_class_M"),
                item_class_S=request.form.get("item_class_S"),
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
                # finder_class=form.finder_class.data,
                finder_affiliation=form.finder_affiliation.data,
                item_situation="保管中",
                refund_situation="未",
                # カードの場合は、カード情報の登録
                card_campany=form.card_campany.data,
                card_tel=form.card_tel.data,
                card_name=form.card_name.data,
                card_person=form.card_person.data,
            )
            db.session.add(ownerlostitem)
            db.session.commit()
            return redirect(url_for("items.detail", item_id=ownerlostitem.id))
    elif choice_finder == "第三者拾得":
        form = ThirdPartyLostItemForm()
        form.recep_manager.choices = user_choice
        if text != "":
            form.item_feature.data = text
        if form.submit.data:
            moved_path = save_image()
            s3_image_path = os.path.join(basedir, "renamed_images", moved_path)
            send_s3.send_image_S3(s3_image_path, request.form.get("item_class_L"))
            thirdpartylostitem = LostItem(
                main_id=main_id,
                current_year=current_year,
                choice_finder=choice_finder,
                # track_num=form.track_num.data,
                notify=form.notify.data,
                get_item=form.get_item.data,
                get_item_hour=request.form.get("get_item_hours"),
                get_item_minute=request.form.get("get_item_minutes"),
                recep_item=form.recep_item.data,
                recep_item_hour=request.form.get("recep_item_hours"),
                recep_item_minute=request.form.get("recep_item_minutes"),
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
                item_class_L=request.form.get("item_class_L"),
                item_class_M=request.form.get("item_class_M"),
                item_class_S=request.form.get("item_class_S"),
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
            )
            db.session.add(thirdpartylostitem)
            db.session.commit()
            return redirect(
                url_for(
                    "items.detail",
                    item_id=thirdpartylostitem.id,
                )
            )
    return render_template(
        "register/register_item.html",
        choice_finder=choice_finder,
        use_AI=use_AI,
        form=form,
        ITEM_CLASS_L=ITEM_CLASS_L,
        ITEM_CLASS_M=ITEM_CLASS_M,
        ITEM_CLASS_S=ITEM_CLASS_S,
        inferenceResult=inferenceResult,
        photoDiscription=photoDiscription,
        main_id=main_id,
        result=result,
    )


# 識別番号の生成関数
def generate_main_id(choice_finder, current_year):
    # choice_finderとcurrent_yearが一致するレコードの数をカウント
    count = (
        db.session.query(func.count(LostItem.id))
        .filter(
            LostItem.choice_finder == choice_finder,
            LostItem.current_year == current_year,
        )
        .scalar()
    )
    if choice_finder == "占有者拾得":
        identifier = f"1{current_year:02}{count+1:05}"
    else:
        identifier = f"2{current_year:02}{count+1:05}"
    return identifier


# 画像の表示
@register.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(current_app.config["CARD_IMAGE_FOLDER"], filename)


# フリーフロー拾得物登録
@register.route("/freeflow_register_item/<choice_finder>/<use_AI>", methods=["POST", "GET"])
def freeflow_register_item(choice_finder, use_AI):
    current_year = datetime.now().year % 100
    main_id = generate_main_id(choice_finder, current_year)
    
    # AI認識結果の取得
    inferenceResult = session.get("inferenceResult", "")
    photoDiscription = session.get("photoDiscription", "")
    
    # YOLO推論による分類（AI使用時）
    if use_AI != "usenoAI":
        root_path = Path(current_app.root_path, "images/captured_image.jpg")
        if root_path.exists():
            inferenceResult = predict_with_yolo(str(root_path))
            print(f"フリーフローYOLO推論結果: {inferenceResult}")
    
    # Userの一覧取得
    users = User.query.all()
    user_choice = [(user.username) for user in users]
    
    form = FreeFlowLostItemForm()
    form.recep_manager.choices = user_choice
    
    if request.method == "POST":
        if form.add_field.data:
            # 項目を追加
            form.dynamic_fields.append_entry()
            return render_template(
                "register/freeflow_register.html",
                choice_finder=choice_finder,
                use_AI=use_AI,
                form=form,
                main_id=main_id,
                inferenceResult=inferenceResult,
                photoDiscription=photoDiscription,
                ITEM_CLASS_L=ITEM_CLASS_L,
                ITEM_CLASS_M=ITEM_CLASS_M,
                ITEM_CLASS_S=ITEM_CLASS_S,
                result=inferenceResult,
            )
        
        elif form.remove_field.data:
            # 項目を削除
            if len(form.dynamic_fields.data) > 1:
                form.dynamic_fields.pop_entry()
            return render_template(
                "register/freeflow_register.html",
                choice_finder=choice_finder,
                use_AI=use_AI,
                form=form,
                main_id=main_id,
                inferenceResult=inferenceResult,
                photoDiscription=photoDiscription,
                ITEM_CLASS_L=ITEM_CLASS_L,
                ITEM_CLASS_M=ITEM_CLASS_M,
                ITEM_CLASS_S=ITEM_CLASS_S,
                result=inferenceResult,
            )
        
        elif form.save_template.data:
            # テンプレートを保存
            template_data = {
                "fields": []
            }
            for field in form.dynamic_fields.data:
                template_data["fields"].append({
                    "name": field.get("field_name", ""),
                    "type": field.get("field_type", ""),
                    "value": field.get("field_value", ""),
                    "required": field.get("required", False)
                })
            
            template_file = get_template_dir() / f"freeflow_template_{choice_finder}.json"
            with open(template_file, "w", encoding="utf-8") as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            flash("テンプレートを保存しました", "success")
            return render_template(
                "register/freeflow_register.html",
                choice_finder=choice_finder,
                use_AI=use_AI,
                form=form,
                main_id=main_id,
                inferenceResult=inferenceResult,
                photoDiscription=photoDiscription,
                ITEM_CLASS_L=ITEM_CLASS_L,
                ITEM_CLASS_M=ITEM_CLASS_M,
                ITEM_CLASS_S=ITEM_CLASS_S,
                result=inferenceResult,
            )
        
        elif form.load_template.data:
            # テンプレートを読み込み
            template_file = get_template_dir() / f"freeflow_template_{choice_finder}.json"
            if template_file.exists():
                with open(template_file, "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                
                # 既存のフィールドをクリア
                while len(form.dynamic_fields.data) > 0:
                    form.dynamic_fields.pop_entry()
                
                # テンプレートからフィールドを復元
                for field_data in template_data.get("fields", []):
                    field_entry = {
                        "field_name": field_data.get("name", ""),
                        "field_type": field_data.get("type", ""),
                        "field_value": field_data.get("value", ""),
                        "required": field_data.get("required", False)
                    }
                    form.dynamic_fields.append_entry(field_entry)
                
                flash("テンプレートを読み込みました", "success")
            else:
                flash("テンプレートが見つかりません", "error")
            
            return render_template(
                "register/freeflow_register.html",
                choice_finder=choice_finder,
                use_AI=use_AI,
                form=form,
                main_id=main_id,
                inferenceResult=inferenceResult,
                photoDiscription=photoDiscription,
                ITEM_CLASS_L=ITEM_CLASS_L,
                ITEM_CLASS_M=ITEM_CLASS_M,
                ITEM_CLASS_S=ITEM_CLASS_S,
                result=inferenceResult,
            )
        
        elif form.submit.data and form.validate():
            # 拾得物を登録
            moved_path = save_image()
            s3_image_path = os.path.join(basedir, "renamed_images", moved_path)
            send_s3.send_image_S3(s3_image_path, "フリーフロー登録")
            
            # 動的フィールドのデータをJSONとして保存
            dynamic_data = {}
            for field in form.dynamic_fields.data:
                field_name = field.get("field_name", "")
                if field_name:
                    dynamic_data[field_name] = {
                        "type": field.get("field_type", ""),
                        "value": field.get("field_value", ""),
                        "required": field.get("required", False)
                    }
            
            # 拾得物オブジェクトを作成
            lostitem = LostItem(
                main_id=main_id,
                current_year=current_year,
                choice_finder=choice_finder,
                notify=form.notify.data,
                get_item=form.get_item.data,
                get_item_hour=request.form.get("get_item_hour"),
                get_item_minute=request.form.get("get_item_minute"),
                recep_item=form.recep_item.data,
                recep_item_hour=request.form.get("recep_item_hour"),
                recep_item_minute=request.form.get("recep_item_minute"),
                recep_manager=form.recep_manager.data,
                find_area=form.find_area.data,
                finder_name=form.finder_name.data,
                finder_post=form.finder_post.data,
                finder_address=form.finder_address.data,
                finder_tel1=form.finder_tel1.data,
                finder_tel2=form.finder_tel2.data,
                item_feature=form.item_feature.data,
                item_value=form.item_value.data,
                item_image=moved_path,
                item_situation="保管中",
                refund_situation="未",
                # 動的フィールドのデータを備考欄に追加
                item_remarks=form.item_remarks.data + "\n\n--- カスタム項目 ---\n" + json.dumps(dynamic_data, ensure_ascii=False, indent=2) if form.item_remarks.data else "--- カスタム項目 ---\n" + json.dumps(dynamic_data, ensure_ascii=False, indent=2),
            )
            
            db.session.add(lostitem)
            db.session.commit()
            
            flash("拾得物を登録しました", "success")
            return redirect(url_for("items.detail", item_id=lostitem.id))
    
    return render_template(
        "register/freeflow_register.html",
        choice_finder=choice_finder,
        use_AI=use_AI,
        form=form,
        main_id=main_id,
        inferenceResult=inferenceResult,
        photoDiscription=photoDiscription,
        ITEM_CLASS_L=ITEM_CLASS_L,
        ITEM_CLASS_M=ITEM_CLASS_M,
        ITEM_CLASS_S=ITEM_CLASS_S,
        result=inferenceResult,
    )
