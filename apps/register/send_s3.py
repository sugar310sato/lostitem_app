import base64

import requests

# S3のフォルダ名との連携
S3_FOLDER = {
    "現金": "cash",
    "かばん類": "Bags",
    "袋・封筒類": "Bags_envelopes",
    "財布類": "Wallets",
    "カードケース類": "card_ cases",
    "カメラ類": "Cameras",
    "時計類": "watches",
    "めがね類": "Glasses",
    "電気製品類": "Electrical_products",
    "携帯電話類": "Mobile_phones",
    "貴金属類": "precious_metals",
    "趣味娯楽用品類": "Hobbies_and_entertainment_supplies",
    "証明書類・カード類": "Certification_documents_cards",
    "有価証券類": "Securities",
    "著作品類": "Works",
    "手帳文具類": "Notebook_stationery",
    "書類・紙類": "Documents_papers",
    "小包・箱類": "Parcels_Boxes",
    "衣類・履物類": "Clothing_footwear",
    "かさ類": "Umbrellas",
    "鍵類": "keys",
    "生活用品類": "Daily_necessities",
    "医療・化粧品類": "Medical_Cosmetics",
    "食料品類": "Food_items",
    "動植物類": "flora_and_fauna",
    "その他": "others",
}


def send_image_S3(image_path, folder):
    # 日本語のフォルダ名をS3のフォルダ名に変換
    print("-----------start------------------------------------")
    s3_folder = S3_FOLDER.get(folder, "others")

    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    # Lambdaに送信
    url = "https://t5l9d8ykje.execute-api.ap-northeast-1.amazonaws.com/default/save_image_to_S3"
    print("---------------------------end----------------------")
    try:
        response = requests.post(url, json={"image": image_base64, "folder": s3_folder})
        print(response)
        if response.status_code == 200:
            return response.json()
        else:
            return "Error: " + response.text
    except requests.exceptions.Timeout:
        return "Error: Timeout"
    except requests.exceptions.RequestException as e:
        return "Error: " + str(e)
