#!/usr/bin/env python
"""
模型评估脚本
Command-line evaluation script for YOLOv11 classroom behavior detection model.

Usage:
    python scripts/evaluate_model.py --weights runs/detect/train/weights/best.pt --data merged_dataset_v2/data.yaml
    python scripts/evaluate_model.py --weights best.pt --data data.yaml --split test --output results/
    python scripts/evaluate_model.py --weights best.pt --data data.yaml --conf 0.5 --iou 0.5 --verbose
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation import ModelEvaluator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Evaluate YOLOv11 classroom behavior detection model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        '--weights', '-w',
        type=str,
        required=True,
        help='Path to model weights file (.pt)'
    )
    parser.add_argument(
        '--data', '-d',
        type=str,
        required=True,
        help='Path to data.yaml configuration file'
    )
    
    # Optional arguments
    parser.add_argument(
        '--split', '-s',
        type=str,
        default='val',
        choices=['val', 'test'],
        help='Dataset split to evaluate on'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output directory for reports and visualizations'
    )
    parser.add_argument(
        '--conf',
        type=float,
        default=0.25,
        help='Confidence threshold for predictions'
    )
    parser.add_argument(
        '--iou',
        type=float,
        default=0.45,
        help='IoU threshold for NMS'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='auto',
        help='Device to use (auto, cpu, 0, 0,1, etc.)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def main():
    """Main evaluation function."""
    args = parse_args()
    
    # Validate weights file exists
    weights_path = Path(args.weights)
    if not weights_path.exists():
        logger.error(f"模型权重文件不存在: {args.weights}")
        sys.exit(1)
    
    # Validate data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"数据集配置文件不存在: {args.data}")
        sys.exit(1)
    
    # Set default output directory
    output_dir = args.output
    if output_dir is None:
        output_dir = f"runs/evaluate/{weights_path.stem}_{args.split}"
    
    # Print configuration
    logger.info("=" * 60)
    logger.info("课堂行为检测模型评估")
    logger.info("=" * 60)
    logger.info(f"模型权重: {args.weights}")
    logger.info(f"数据集配置: {args.data}")
    logger.info(f"评估分割: {args.split}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"置信度阈值: {args.conf}")
    logger.info(f"IoU 阈值: {args.iou}")
    logger.info(f"设备: {args.device}")
    logger.info("-" * 60)
    
    try:
        # Create evaluator
        evaluator = ModelEvaluator(
            weights_path=str(weights_path),
            device=args.device
        )
        
        # Run evaluation
        result = evaluator.evaluate(
            data_yaml=str(data_path),
            split=args.split,
            conf=args.conf,
            iou=args.iou,
            verbose=args.verbose,
            output_dir=output_dir
        )
        
        # Print results summary
        logger.info("=" * 60)
        logger.info("评估结果摘要")
        logger.info("=" * 60)
        
        om = result.overall_metrics
        logger.info(f"整体指标:")
        logger.info(f"  mAP@50:     {om.mAP50:.4f}")
        logger.info(f"  mAP@50-95:  {om.mAP50_95:.4f}")
        logger.info(f"  Precision:  {om.precision:.4f}")
        logger.info(f"  Recall:     {om.recall:.4f}")
        logger.info(f"  F1 Score:   {om.f1_score:.4f}")
        logger.info("")
        
        gm = result.group_metrics
        logger.info(f"行为组指标:")
        logger.info(f"  正常行为 - Precision: {gm.normal_precision:.4f}, Recall: {gm.normal_recall:.4f}, F1: {gm.normal_f1:.4f}")
        logger.info(f"  预警行为 - Precision: {gm.warning_precision:.4f}, Recall: {gm.warning_recall:.4f}, F1: {gm.warning_f1:.4f}")
        
        if gm.warning_recall_critical:
            logger.warning("⚠️ 预警行为召回率低于 0.5，模型可能无法有效检测预警行为！")
        
        logger.info("")
        logger.info(f"每类别指标:")
        for class_id in sorted(result.per_class_metrics.keys()):
            cm = result.per_class_metrics[class_id]
            cn_name = result.class_names_cn[class_id] if class_id < len(result.class_names_cn) else cm.class_name
            logger.info(f"  {cn_name}: P={cm.precision:.4f}, R={cm.recall:.4f}, F1={cm.f1_score:.4f}, AP50={cm.ap50:.4f}")
        
        logger.info("")
        logger.info(f"混淆分析 (Top 3):")
        for pair in result.confused_pairs[:3]:
            logger.info(f"  {pair.class_a_name} → {pair.class_b_name}: {pair.confusion_rate:.2%}")
        
        logger.info("")
        logger.info(f"报告已保存到: {output_dir}")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        return 1
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return 1
    except ImportError as e:
        logger.error(f"依赖缺失: {e}")
        return 1
    except Exception as e:
        logger.error(f"评估失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
