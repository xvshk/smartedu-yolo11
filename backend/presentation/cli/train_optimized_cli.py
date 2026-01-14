#!/usr/bin/env python
"""
针对RTX 4050 (6GB显存) 优化的训练脚本
Optimized training script for RTX 4050 with 6GB VRAM.

显存优化策略:
1. 使用yolo11n或yolo11s模型（更小的模型占用更少显存）
2. 减小batch_size到4-8
3. 减小图像尺寸到480或512
4. 启用AMP混合精度训练
5. 减少workers数量
6. 使用梯度累积模拟更大batch

Usage:
    python backend/presentation/cli/train_optimized_cli.py --data merged_dataset_v2/data.yaml
    python backend/presentation/cli/train_optimized_cli.py --data merged_dataset_v2/data.yaml --model yolo11s
    python backend/presentation/cli/train_optimized_cli.py --data merged_dataset_v2/data.yaml --aggressive  # 更激进的显存优化
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# RTX 4050 6GB 优化配置预设
PRESETS = {
    # 标准配置 - yolo11n, 适合大多数情况
    'standard': {
        'model': 'yolo11n',
        'batch_size': 8,
        'img_size': 512,
        'workers': 4,
        'cache': False,
        'description': '标准配置 - 平衡性能和显存使用'
    },
    # 性能配置 - yolo11s, 更好的精度
    'performance': {
        'model': 'yolo11s',
        'batch_size': 4,
        'img_size': 512,
        'workers': 4,
        'cache': False,
        'description': '性能配置 - 更高精度，较慢训练'
    },
    # 激进配置 - 最小显存占用
    'aggressive': {
        'model': 'yolo11n',
        'batch_size': 4,
        'img_size': 480,
        'workers': 2,
        'cache': False,
        'description': '激进配置 - 最小显存占用'
    },
    # 快速测试配置
    'quick_test': {
        'model': 'yolo11n',
        'batch_size': 8,
        'img_size': 416,
        'workers': 4,
        'cache': False,
        'description': '快速测试配置 - 用于验证流程'
    }
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='RTX 4050 (6GB) 优化训练脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
配置预设说明:
  standard    - yolo11n, batch=8, img=512  (推荐首选)
  performance - yolo11s, batch=4, img=512  (更高精度)
  aggressive  - yolo11n, batch=4, img=480  (显存不足时使用)
  quick_test  - yolo11n, batch=8, img=416  (快速验证)

示例:
  python backend/presentation/cli/train_optimized_cli.py --data merged_dataset_v2/data.yaml
  python backend/presentation/cli/train_optimized_cli.py --data merged_dataset_v2/data.yaml --preset performance
  python backend/presentation/cli/train_optimized_cli.py --data merged_dataset_v2/data.yaml --epochs 150 --patience 30
        """
    )
    
    # 数据配置
    parser.add_argument('--data', '-d', type=str, required=True,
                        help='数据集配置文件路径 (data.yaml)')
    
    # 预设配置
    parser.add_argument('--preset', '-p', type=str, default='standard',
                        choices=list(PRESETS.keys()),
                        help='配置预设 (default: standard)')
    
    # 可覆盖的参数
    parser.add_argument('--model', '-m', type=str, default=None,
                        choices=['yolo11n', 'yolo11s', 'yolo11m'],
                        help='模型大小 (覆盖预设)')
    parser.add_argument('--batch-size', '-b', type=int, default=None,
                        help='批次大小 (覆盖预设)')
    parser.add_argument('--img-size', '-i', type=int, default=None,
                        help='图像尺寸 (覆盖预设)')
    parser.add_argument('--epochs', '-e', type=int, default=100,
                        help='训练轮数 (default: 100)')
    parser.add_argument('--patience', type=int, default=30,
                        help='早停耐心值 (default: 30)')
    
    # 学习率配置
    parser.add_argument('--lr0', type=float, default=0.01,
                        help='初始学习率 (default: 0.01)')
    parser.add_argument('--lrf', type=float, default=0.01,
                        help='最终学习率因子 (default: 0.01)')
    
    # 输出配置
    parser.add_argument('--project', type=str, default='runs/detect',
                        help='项目目录')
    parser.add_argument('--name', type=str, default='train_4050',
                        help='实验名称')
    parser.add_argument('--exist-ok', action='store_true',
                        help='允许覆盖已有实验')
    
    # 恢复训练
    parser.add_argument('--resume', '-r', action='store_true',
                        help='从上次中断处恢复训练')
    parser.add_argument('--weights', '-w', type=str, default=None,
                        help='预训练权重路径')
    
    # 数据增强
    parser.add_argument('--mosaic', type=float, default=1.0,
                        help='Mosaic增强概率 (default: 1.0)')
    parser.add_argument('--mixup', type=float, default=0.1,
                        help='MixUp增强概率 (default: 0.1)')
    parser.add_argument('--close-mosaic', type=int, default=15,
                        help='最后N轮关闭Mosaic (default: 15)')
    
    # 高级选项
    parser.add_argument('--cache', action='store_true',
                        help='缓存图像到内存 (需要足够RAM)')
    parser.add_argument('--workers', type=int, default=None,
                        help='数据加载线程数 (覆盖预设)')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子 (default: 42)')
    
    # 验证和导出
    parser.add_argument('--val', action='store_true', default=True,
                        help='训练后运行验证')
    parser.add_argument('--export', type=str, default=None,
                        choices=['onnx', 'torchscript', 'tensorrt'],
                        help='训练后导出模型格式')
    
    # 调试选项
    parser.add_argument('--verbose', action='store_true', default=True,
                        help='详细输出')
    parser.add_argument('--dry-run', action='store_true',
                        help='只显示配置，不实际训练')
    
    return parser.parse_args()


def get_optimized_config(args):
    """获取针对4050优化的训练配置"""
    # 从预设开始
    preset = PRESETS[args.preset]
    
    config = {
        # 模型配置
        'model': args.model or preset['model'],
        
        # 训练配置 - 针对6GB显存优化
        'epochs': args.epochs,
        'batch': args.batch_size or preset['batch_size'],
        'imgsz': args.img_size or preset['img_size'],
        'patience': args.patience,
        
        # 学习率配置
        'lr0': args.lr0,
        'lrf': args.lrf,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3.0,
        'warmup_momentum': 0.8,
        
        # 显存优化配置
        'amp': True,  # 混合精度训练 - 关键优化
        'cache': args.cache or preset['cache'],
        'workers': args.workers or preset['workers'],
        'device': 0,  # 使用GPU 0
        
        # 数据增强 - 适度增强
        'mosaic': args.mosaic,
        'mixup': args.mixup,
        'close_mosaic': args.close_mosaic,
        'hsv_h': 0.015,
        'hsv_s': 0.7,
        'hsv_v': 0.4,
        'degrees': 10.0,  # 轻微旋转
        'translate': 0.1,
        'scale': 0.5,
        'shear': 2.0,
        'flipud': 0.0,
        'fliplr': 0.5,
        'erasing': 0.3,
        
        # 输出配置
        'project': args.project,
        'name': args.name,
        'exist_ok': args.exist_ok,
        'save': True,
        'save_period': 10,  # 每10轮保存一次
        
        # 其他配置
        'seed': args.seed,
        'deterministic': True,
        'verbose': args.verbose,
        'plots': True,
        
        # 损失函数权重
        'box': 7.5,
        'cls': 0.5,
        'dfl': 1.5,
    }
    
    return config, preset['description']


def print_config_summary(config, preset_desc, data_path):
    """打印配置摘要"""
    logger.info("=" * 70)
    logger.info("RTX 4050 (6GB) 优化训练配置")
    logger.info("=" * 70)
    logger.info(f"预设: {preset_desc}")
    logger.info("-" * 70)
    logger.info("核心配置:")
    logger.info(f"  模型: {config['model']}")
    logger.info(f"  数据集: {data_path}")
    logger.info(f"  训练轮数: {config['epochs']}")
    logger.info(f"  批次大小: {config['batch']}")
    logger.info(f"  图像尺寸: {config['imgsz']}")
    logger.info(f"  初始学习率: {config['lr0']}")
    logger.info(f"  早停耐心值: {config['patience']}")
    logger.info("-" * 70)
    logger.info("显存优化:")
    logger.info(f"  混合精度(AMP): {config['amp']}")
    logger.info(f"  数据加载线程: {config['workers']}")
    logger.info(f"  图像缓存: {config['cache']}")
    logger.info("-" * 70)
    logger.info("数据增强:")
    logger.info(f"  Mosaic: {config['mosaic']}")
    logger.info(f"  MixUp: {config['mixup']}")
    logger.info(f"  关闭Mosaic轮数: {config['close_mosaic']}")
    logger.info("-" * 70)
    logger.info("输出:")
    logger.info(f"  保存目录: {config['project']}/{config['name']}")
    logger.info("=" * 70)


def estimate_vram_usage(config):
    """估算显存使用量"""
    model_vram = {
        'yolo11n': 1.5,  # GB
        'yolo11s': 2.5,
        'yolo11m': 4.0,
    }
    
    base_vram = model_vram.get(config['model'], 2.0)
    
    # 批次大小影响
    batch_factor = config['batch'] / 8
    
    # 图像尺寸影响 (相对于640)
    img_factor = (config['imgsz'] / 640) ** 2
    
    # AMP减少约30%显存
    amp_factor = 0.7 if config['amp'] else 1.0
    
    estimated = base_vram * batch_factor * img_factor * amp_factor
    
    return estimated


def main():
    """主函数"""
    args = parse_args()
    
    # 验证数据文件
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"数据配置文件不存在: {args.data}")
        sys.exit(1)
    
    # 获取优化配置
    config, preset_desc = get_optimized_config(args)
    
    # 打印配置摘要
    print_config_summary(config, preset_desc, args.data)
    
    # 估算显存使用
    estimated_vram = estimate_vram_usage(config)
    logger.info(f"预估显存使用: ~{estimated_vram:.1f} GB")
    if estimated_vram > 5.5:
        logger.warning("⚠️ 预估显存可能超出6GB限制，建议使用更激进的配置")
        logger.warning("   尝试: --preset aggressive 或减小 --batch-size")
    else:
        logger.info("✓ 显存使用在安全范围内")
    logger.info("=" * 70)
    
    # 干运行模式
    if args.dry_run:
        logger.info("干运行模式 - 不执行实际训练")
        return 0
    
    try:
        from ultralytics import YOLO
        
        # 加载模型
        if args.weights:
            logger.info(f"从权重加载模型: {args.weights}")
            model = YOLO(args.weights)
        else:
            model_file = f"{config['model']}.pt"
            logger.info(f"加载预训练模型: {model_file}")
            model = YOLO(model_file)
        
        # 准备训练参数
        train_args = {k: v for k, v in config.items() if k != 'model'}
        train_args['data'] = str(args.data)
        train_args['resume'] = args.resume
        
        # 开始训练
        logger.info("开始训练...")
        logger.info("提示: 如果出现CUDA内存不足错误，请尝试:")
        logger.info("  1. 减小 --batch-size (如 --batch-size 4)")
        logger.info("  2. 减小 --img-size (如 --img-size 480)")
        logger.info("  3. 使用 --preset aggressive")
        logger.info("-" * 70)
        
        results = model.train(**train_args)
        
        # 训练完成
        logger.info("=" * 70)
        logger.info("训练完成!")
        
        if hasattr(results, 'save_dir'):
            save_dir = Path(results.save_dir)
            logger.info(f"结果保存在: {save_dir}")
            
            best_weights = save_dir / 'weights' / 'best.pt'
            if best_weights.exists():
                logger.info(f"最佳权重: {best_weights}")
                
                # 验证
                if args.val:
                    logger.info("运行验证...")
                    val_model = YOLO(str(best_weights))
                    val_results = val_model.val(data=str(args.data))
                    
                    if hasattr(val_results, 'box'):
                        logger.info(f"验证结果:")
                        logger.info(f"  mAP50: {val_results.box.map50:.4f}")
                        logger.info(f"  mAP50-95: {val_results.box.map:.4f}")
                        logger.info(f"  Precision: {val_results.box.mp:.4f}")
                        logger.info(f"  Recall: {val_results.box.mr:.4f}")
                
                # 导出
                if args.export:
                    logger.info(f"导出模型为 {args.export} 格式...")
                    export_model = YOLO(str(best_weights))
                    export_path = export_model.export(
                        format=args.export,
                        imgsz=config['imgsz'],
                        half=True  # FP16导出
                    )
                    logger.info(f"模型已导出: {export_path}")
        
        logger.info("=" * 70)
        return 0
        
    except Exception as e:
        logger.error(f"训练失败: {e}")
        if "CUDA out of memory" in str(e) or "OutOfMemoryError" in str(e):
            logger.error("=" * 70)
            logger.error("显存不足! 请尝试以下解决方案:")
            logger.error("  1. python backend/presentation/cli/train_optimized_cli.py --data ... --preset aggressive")
            logger.error("  2. python backend/presentation/cli/train_optimized_cli.py --data ... --batch-size 2 --img-size 416")
            logger.error("  3. 关闭其他占用GPU的程序")
            logger.error("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())