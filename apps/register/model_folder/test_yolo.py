#!/usr/bin/env python3
"""
YOLOモデルのテストスクリプト
使用方法: python test_yolo.py [画像パス]
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.register.model_folder.yolo_predict import YOLOPredictor

def test_yolo_prediction(image_path):
    """
    YOLOモデルで画像をテスト
    Args:
        image_path: テストする画像のパス
    """
    print(f"テスト画像: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"エラー: 画像ファイルが見つかりません: {image_path}")
        return
    
    try:
        # YOLOモデルの初期化
        print("YOLOモデルを初期化中...")
        predictor = YOLOPredictor()
        
        # モデル情報の表示
        model_info = predictor.get_model_info()
        print(f"モデル情報: {model_info}")
        
        # 推論実行
        print("推論実行中...")
        result = predictor.predict_item_category(image_path, confidence_threshold=0.3)
        
        if "error" in result:
            print(f"推論エラー: {result['error']}")
            return
        
        # 結果の表示
        print("\n=== 推論結果 ===")
        print(f"予測カテゴリ: {result['category']}")
        print(f"信頼度: {result['confidence']:.3f}")
        
        if result['detected_objects']:
            print("\n検出された物体:")
            for i, obj in enumerate(result['detected_objects'][:5]):  # 上位5件のみ表示
                print(f"  {i+1}. {obj['category']} (信頼度: {obj['confidence']:.3f})")
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python test_yolo.py [画像パス]")
        print("例: python test_yolo.py test_image.jpg")
        return
    
    image_path = sys.argv[1]
    test_yolo_prediction(image_path)

if __name__ == "__main__":
    main() 