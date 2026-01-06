#!/usr/bin/env python
"""
将训练好的YOLO模型注册到MLflow
Register trained YOLO model to MLflow Model Registry
"""
import mlflow
import mlflow.pytorch
from pathlib import Path
import shutil
import json
import sys

# 设置MLflow tracking URI
mlflow.set_tracking_uri("runs/mlflow")

# 模型路径
MODEL_PATH = "runs/detect/classroom_behavior_4050/weights/best.pt"
RESULTS_PATH = "runs/detect/classroom_behavior_4050/results.csv"

def register_model():
    """注册模型到MLflow"""
    
    # 检查模型文件是否存在
    if not Path(MODEL_PATH).exists():
        print(f"错误: 模型文件不存在 {MODEL_PATH}")
        return False
    
    # 读取训练结果获取最佳指标
    metrics = {}
    if Path(RESULTS_PATH).exists():
        import pandas as pd
        df = pd.read_csv(RESULTS_PATH)
        # 获取最佳epoch的指标
        best_idx = df['metrics/mAP50(B)'].idxmax()
        metrics = {
            'best_epoch': int(best_idx) + 1,
            'mAP50': float(df.loc[best_idx, 'metrics/mAP50(B)']),
            'mAP50_95': float(df.loc[best_idx, 'metrics/mAP50-95(B)']),
            'precision': float(df.loc[best_idx, 'metrics/precision(B)']),
            'recall': float(df.loc[best_idx, 'metrics/recall(B)']),
            'box_loss': float(df.loc[best_idx, 'train/box_loss']),
            'cls_loss': float(df.loc[best_idx, 'train/cls_loss']),
        }
    
    # 模型参数
    params = {
        'model_type': 'yolo11n',
        'img_size': 512,
        'batch_size': 8,
        'epochs': 100,
        'classes': 7,
        'class_names': 'handrise,read,write,sleep,stand,using_electronic_devices,talk'
    }
    
    # 创建MLflow实验
    experiment_name = "classroom_behavior_detection"
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name="yolo11n_classroom_behavior_v1") as run:
        # 记录参数
        mlflow.log_params(params)
        
        # 记录指标
        mlflow.log_metrics(metrics)
        
        # 记录模型文件
        mlflow.log_artifact(MODEL_PATH, artifact_path="model")
        
        # 记录训练结果
        if Path(RESULTS_PATH).exists():
            mlflow.log_artifact(RESULTS_PATH, artifact_path="results")
        
        # 记录混淆矩阵等图片
        artifacts_dir = Path("runs/detect/classroom_behavior_4050")
        for img_file in artifacts_dir.glob("*.png"):
            mlflow.log_artifact(str(img_file), artifact_path="plots")
        for img_file in artifacts_dir.glob("*.jpg"):
            mlflow.log_artifact(str(img_file), artifact_path="plots")
        
        # 使用pyfunc方式记录模型
        from ultralytics import YOLO
        
        # 加载YOLO模型
        yolo_model = YOLO(MODEL_PATH)
        
        # 创建模型签名
        model_name = "classroom_behavior_yolo11n"
        
        # 使用log_artifact记录模型，然后手动注册
        print("=" * 60)
        print("模型已记录到MLflow!")
        print("=" * 60)
        print(f"Run ID: {run.info.run_id}")
        print(f"Experiment: {experiment_name}")
        print(f"Model Path: {MODEL_PATH}")
        print("-" * 60)
        print("指标:")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")
        print("=" * 60)
        
        # 创建模型版本
        from mlflow.tracking import MlflowClient
        client = MlflowClient()
        
        # 创建注册模型（如果不存在）
        try:
            client.create_registered_model(model_name)
            print(f"创建注册模型: {model_name}")
        except:
            print(f"注册模型已存在: {model_name}")
        
        # 创建模型版本
        artifact_uri = mlflow.get_artifact_uri("model/best.pt")
        model_version = client.create_model_version(
            name=model_name,
            source=artifact_uri,
            run_id=run.info.run_id,
            description=f"YOLO11n课堂行为检测模型 - mAP50: {metrics.get('mAP50', 'N/A'):.4f}"
        )
        
        print(f"\n模型版本: {model_version.version}")
        print(f"在MLflow UI查看: http://127.0.0.1:5000")
        
        return True

if __name__ == "__main__":
    success = register_model()
    sys.exit(0 if success else 1)
