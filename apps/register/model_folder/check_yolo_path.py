#!/usr/bin/env python3
"""
YOLOモデルの保存場所を確認するスクリプト
"""

import os
from pathlib import Path
from ultralytics import YOLO
import torch

def check_yolo_paths():
    """YOLOモデルの保存場所を確認"""
    print("=== YOLOモデル保存場所の確認 ===\n")
    
    # 1. ultralyticsの設定ディレクトリ
    try:
        from ultralytics.utils.settings import Settings
        settings = Settings()
        print(f"Ultralytics設定ディレクトリ: {settings.root}")
    except Exception as e:
        print(f"設定ディレクトリの取得に失敗: {e}")
    
    # 2. 一般的な保存場所
    common_paths = [
        # Windows
        Path.home() / "AppData" / "Roaming" / "Ultralytics",
        Path.home() / "AppData" / "Local" / "Ultralytics",
        # macOS/Linux
        Path.home() / ".config" / "Ultralytics",
        Path.home() / ".cache" / "ultralytics",
    ]
    
    print("\n一般的な保存場所:")
    for path in common_paths:
        if path.exists():
            print(f"✓ {path}")
            # サブディレクトリも確認
            for subdir in path.rglob("*"):
                if subdir.is_dir():
                    print(f"  └─ {subdir}")
        else:
            print(f"✗ {path} (存在しません)")
    
    # 3. モデルファイルの確認
    print("\n=== モデルファイルの確認 ===")
    
    # YOLOモデルを初期化して実際のパスを確認
    try:
        print("YOLO v8nモデルを初期化中...")
        model = YOLO('yolov8n.pt')
        
        # モデルのパスを確認
        if hasattr(model, 'ckpt_path'):
            print(f"モデルファイルパス: {model.ckpt_path}")
        
        # モデル情報
        print(f"モデルタイプ: {type(model).__name__}")
        print(f"デバイス: {model.device}")
        
        # モデルサイズ
        if hasattr(model, 'model'):
            total_params = sum(p.numel() for p in model.model.parameters())
            print(f"パラメータ数: {total_params:,}")
        
    except Exception as e:
        print(f"モデル初期化エラー: {e}")
    
    # 4. torch hubのキャッシュディレクトリ
    print("\n=== PyTorch Hub キャッシュ ===")
    torch_hub_dir = torch.hub.get_dir()
    print(f"PyTorch Hub ディレクトリ: {torch_hub_dir}")
    
    if Path(torch_hub_dir).exists():
        print("PyTorch Hub キャッシュ内容:")
        for item in Path(torch_hub_dir).iterdir():
            if item.is_dir():
                print(f"  📁 {item.name}")
            else:
                print(f"  📄 {item.name}")

if __name__ == "__main__":
    check_yolo_paths() 