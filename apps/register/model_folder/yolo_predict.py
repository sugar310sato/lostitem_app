import os
import torch
from ultralytics import YOLO
from PIL import Image
import numpy as np
from pathlib import Path

class YOLOPredictor:
    def __init__(self, model_path=None):
        """
        YOLOモデルの初期化
        Args:
            model_path: カスタムモデルのパス（Noneの場合は事前学習済みモデルを使用）
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        if model_path and os.path.exists(model_path):
            # カスタムモデルを使用
            self.model = YOLO(model_path)
        else:
            # 事前学習済みのYOLO v8nモデルを使用
            self.model = YOLO('yolov8n.pt')
        
        # 拾得物の分類カテゴリ
        self.item_categories = {
            0: "かばん類",
            1: "袋・封筒類", 
            2: "カメラ類",
            3: "証明書類・カード類",
            4: "衣類・履物類",
            5: "生活用品類",
            6: "書類・紙類",
            7: "電気製品類",
            8: "食料品類",
            9: "めがね類",
            10: "趣味娯楽用品類",
            11: "医療・化粧品類",
            12: "携帯電話類",
            13: "手帳文具類",
            14: "小包・箱類",
            15: "有価証券類",
            16: "かさ類",
            17: "財布類",
            18: "著作品類",
            19: "カードケース類",
            20: "現金",
            21: "動植物類",
            22: "鍵類",
            23: "その他",
            24: "貴金属類",
            25: "時計類"
        }
        
        # 一般的な物体検出カテゴリ（COCOデータセット）
        self.coco_categories = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus',
            6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant',
            11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat',
            16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant',
            21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella',
            26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis',
            31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove',
            36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle', 40: 'wine glass',
            41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl',
            46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli',
            51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut', 55: 'cake',
            56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table',
            61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote',
            66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster',
            71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase',
            76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'
        }

    def predict_item_category(self, image_path, confidence_threshold=0.5):
        """
        画像から拾得物のカテゴリを予測
        Args:
            image_path: 画像ファイルのパス
            confidence_threshold: 信頼度の閾値
        Returns:
            dict: 予測結果（カテゴリ名、信頼度、検出された物体のリスト）
        """
        try:
            # 画像の読み込み
            if not os.path.exists(image_path):
                return {"error": "画像ファイルが見つかりません"}
            
            # YOLOで推論実行
            results = self.model(image_path, conf=confidence_threshold)
            
            if not results or len(results) == 0:
                return {"category": "その他", "confidence": 0.0, "detected_objects": []}
            
            result = results[0]  # 最初の結果を取得
            
            # 検出された物体の情報を取得
            detected_objects = []
            if result.boxes is not None:
                for box in result.boxes:
                    if box.conf is not None and box.cls is not None:
                        for i in range(len(box.conf)):
                            class_id = int(box.cls[i].item())
                            confidence = float(box.conf[i].item())
                            
                            # カテゴリ名を取得
                            if class_id in self.coco_categories:
                                category_name = self.coco_categories[class_id]
                            else:
                                category_name = f"Unknown_{class_id}"
                            
                            detected_objects.append({
                                "category": category_name,
                                "confidence": confidence,
                                "class_id": class_id
                            })
            
            # 最も信頼度の高い物体を選択
            if detected_objects:
                best_detection = max(detected_objects, key=lambda x: x["confidence"])
                
                # 拾得物カテゴリへのマッピング
                mapped_category = self._map_to_item_category(best_detection["category"])
                
                return {
                    "category": mapped_category,
                    "confidence": best_detection["confidence"],
                    "detected_objects": detected_objects
                }
            else:
                return {"category": "その他", "confidence": 0.0, "detected_objects": []}
                
        except Exception as e:
            print(f"推論中にエラーが発生しました: {str(e)}")
            return {"error": f"推論エラー: {str(e)}"}

    def _map_to_item_category(self, detected_category):
        """
        検出されたカテゴリを拾得物カテゴリにマッピング
        Args:
            detected_category: 検出されたカテゴリ名
        Returns:
            str: 拾得物カテゴリ名
        """
        # カテゴリマッピング辞書
        category_mapping = {
            # かばん類
            "backpack": "かばん類",
            "handbag": "かばん類",
            "suitcase": "かばん類",
            
            # 袋・封筒類
            "plastic bag": "袋・封筒類",
            
            # カメラ類
            "camera": "カメラ類",
            
            # 証明書類・カード類
            "card": "証明書類・カード類",
            "id card": "証明書類・カード類",
            
            # 衣類・履物類
            "tie": "衣類・履物類",
            "shirt": "衣類・履物類",
            "pants": "衣類・履物類",
            "shoes": "衣類・履物類",
            
            # 生活用品類
            "bottle": "生活用品類",
            "cup": "生活用品類",
            "bowl": "生活用品類",
            "fork": "生活用品類",
            "knife": "生活用品類",
            "spoon": "生活用品類",
            
            # 書類・紙類
            "book": "書類・紙類",
            "newspaper": "書類・紙類",
            "magazine": "書類・紙類",
            
            # 電気製品類
            "tv": "電気製品類",
            "laptop": "電気製品類",
            "cell phone": "携帯電話類",
            "remote": "電気製品類",
            "keyboard": "電気製品類",
            "mouse": "電気製品類",
            "microwave": "電気製品類",
            "oven": "電気製品類",
            "refrigerator": "電気製品類",
            
            # 食料品類
            "banana": "食料品類",
            "apple": "食料品類",
            "orange": "食料品類",
            "sandwich": "食料品類",
            "hot dog": "食料品類",
            "pizza": "食料品類",
            "donut": "食料品類",
            "cake": "食料品類",
            
            # めがね類
            "glasses": "めがね類",
            
            # 趣味娯楽用品類
            "sports ball": "趣味娯楽用品類",
            "baseball bat": "趣味娯楽用品類",
            "tennis racket": "趣味娯楽用品類",
            "skateboard": "趣味娯楽用品類",
            "surfboard": "趣味娯楽用品類",
            
            # 医療・化粧品類
            "toothbrush": "医療・化粧品類",
            
            # 手帳文具類
            "pen": "手帳文具類",
            "pencil": "手帳文具類",
            
            # 小包・箱類
            "box": "小包・箱類",
            "package": "小包・箱類",
            
            # 有価証券類
            "money": "有価証券類",
            "coin": "有価証券類",
            
            # かさ類
            "umbrella": "かさ類",
            
            # 財布類
            "wallet": "財布類",
            
            # 時計類
            "clock": "時計類",
            "watch": "時計類",
            
            # 鍵類
            "key": "鍵類",
        }
        
        # マッピングを試行
        for key, value in category_mapping.items():
            if key.lower() in detected_category.lower():
                return value
        
        # デフォルトは「その他」
        return "その他"

    def get_model_info(self):
        """
        モデルの情報を取得
        Returns:
            dict: モデル情報
        """
        return {
            "model_type": "YOLO",
            "device": str(self.device),
            "available_categories": len(self.coco_categories),
            "item_categories": len(self.item_categories)
        } 