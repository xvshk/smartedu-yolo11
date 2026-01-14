#!/usr/bin/env python
"""
训练脚本
Command-line training script for YOLOv11 classroom behavior detection model.
符合Presentation层职责：仅处理用户交互，通过Service层访问业务逻辑

Usage:
    python backend/presentation/cli/train_cli.py --data data.yaml --model yolo11m --epochs 100
    python backend/presentation/cli/train_cli.py --data data.yaml --model yolo11s --epochs 50 --batch-size 32
    python backend/presentation/cli/train_cli.py --resume --weights runs/detect/train/weights/last.pt
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 通过service层访问业务逻辑（待实现训练服务）
# from backend.service import get_training_service


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
        description='Train YOLOv11 classroom behavior detection model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model arguments
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='yolo11m',
        choices=['yolo11n', 'yolo11s', 'yolo11m', 'yolo11l', 'yolo11x'],
        help='Model size variant'
    )
    parser.add_argument(
        '--weights', '-w',
        type=str,
        default=None,
        help='Path to pretrained weights file (overrides --model)'
    )
    parser.add_argument(
        '--pretrained',
        action='store_true',
        default=True,
        help='Use pretrained weights'
    )
    parser.add_argument(
        '--no-pretrained',
        action='store_true',
        help='Do not use pretrained weights'
    )
    
    # Data arguments
    parser.add_argument(
        '--data', '-d',
        type=str,
        required=True,
        help='Path to data.yaml configuration file'
    )
    
    # Training arguments
    parser.add_argument(
        '--epochs', '-e',
        type=int,
        default=100,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=16,
        help='Batch size for training'
    )
    parser.add_argument(
        '--img-size', '-i',
        type=int,
        default=640,
        help='Input image size'
    )
    parser.add_argument(
        '--lr0',
        type=float,
        default=0.01,
        help='Initial learning rate'
    )
    parser.add_argument(
        '--patience',
        type=int,
        default=50,
        help='Early stopping patience (epochs without improvement)'
    )

    # Resume training
    parser.add_argument(
        '--resume', '-r',
        action='store_true',
        help='Resume training from last checkpoint'
    )
    parser.add_argument(
        '--resume-weights',
        type=str,
        default=None,
        help='Path to weights file for resuming training'
    )
    
    # Output arguments
    parser.add_argument(
        '--project',
        type=str,
        default='runs/detect',
        help='Project directory for saving results'
    )
    parser.add_argument(
        '--name',
        type=str,
        default='train',
        help='Experiment name'
    )
    parser.add_argument(
        '--exist-ok',
        action='store_true',
        help='Allow overwriting existing experiment'
    )
    
    # Device arguments
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device to use (e.g., "0", "0,1", "cpu")'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=8,
        help='Number of data loading workers'
    )
    
    # Data augmentation arguments
    parser.add_argument(
        '--mosaic',
        type=float,
        default=1.0,
        help='Mosaic augmentation probability (0.0-1.0)'
    )
    parser.add_argument(
        '--mixup',
        type=float,
        default=0.0,
        help='MixUp augmentation probability (0.0-1.0)'
    )
    parser.add_argument(
        '--hsv-h',
        type=float,
        default=0.015,
        help='HSV-Hue augmentation (fraction)'
    )
    parser.add_argument(
        '--hsv-s',
        type=float,
        default=0.7,
        help='HSV-Saturation augmentation (fraction)'
    )
    parser.add_argument(
        '--hsv-v',
        type=float,
        default=0.4,
        help='HSV-Value augmentation (fraction)'
    )
    parser.add_argument(
        '--degrees',
        type=float,
        default=0.0,
        help='Image rotation (+/- deg)'
    )
    parser.add_argument(
        '--translate',
        type=float,
        default=0.1,
        help='Image translation (+/- fraction)'
    )
    parser.add_argument(
        '--scale',
        type=float,
        default=0.5,
        help='Image scale (+/- gain)'
    )
    parser.add_argument(
        '--fliplr',
        type=float,
        default=0.5,
        help='Image flip left-right probability'
    )
    parser.add_argument(
        '--flipud',
        type=float,
        default=0.0,
        help='Image flip up-down probability'
    )
    
    # Validation arguments
    parser.add_argument(
        '--val',
        action='store_true',
        help='Run validation after training'
    )
    parser.add_argument(
        '--val-split',
        type=str,
        default='val',
        choices=['val', 'test'],
        help='Dataset split for validation'
    )
    
    # Export arguments
    parser.add_argument(
        '--export',
        type=str,
        default=None,
        choices=['onnx', 'torchscript', 'tensorrt', 'openvino', 'tflite'],
        help='Export model to specified format after training'
    )
    parser.add_argument(
        '--export-half',
        action='store_true',
        help='Use FP16 half-precision for export'
    )
    
    # Misc arguments
    parser.add_argument(
        '--seed',
        type=int,
        default=0,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='Verbose output'
    )
    parser.add_argument(
        '--cache',
        action='store_true',
        help='Cache images for faster training'
    )
    parser.add_argument(
        '--amp',
        action='store_true',
        default=True,
        help='Use automatic mixed precision training'
    )
    parser.add_argument(
        '--no-amp',
        action='store_true',
        help='Disable automatic mixed precision training'
    )
    
    return parser.parse_args()


def main():
    """Main training function."""
    args = parse_args()
    
    # Validate data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"Data configuration file not found: {args.data}")
        sys.exit(1)
    
    # Determine pretrained setting
    pretrained = args.pretrained and not args.no_pretrained
    
    # Initialize training pipeline
    logger.info("=" * 60)
    logger.info("Classroom Behavior Detection - Training Script")
    logger.info("=" * 60)
    
    try:
        # Create pipeline
        if args.weights:
            logger.info(f"Loading model from weights: {args.weights}")
            pipeline = TrainingPipeline(
                model_size=args.model,
                pretrained=False,
                weights=args.weights
            )
        else:
            logger.info(f"Initializing model: {args.model} (pretrained={pretrained})")
            pipeline = TrainingPipeline(
                model_size=args.model,
                pretrained=pretrained
            )
        
        # Configure training parameters
        logger.info("Configuring training parameters...")
        pipeline.configure(
            epochs=args.epochs,
            batch_size=args.batch_size,
            img_size=args.img_size,
            lr0=args.lr0,
            patience=args.patience,
            project=args.project,
            name=args.name,
            exist_ok=args.exist_ok,
            device=args.device,
            workers=args.workers,
            seed=args.seed,
            verbose=args.verbose,
            cache=args.cache,
            amp=args.amp and not args.no_amp,
        )
        
        # Configure data augmentation
        logger.info("Configuring data augmentation...")
        pipeline.configure_augmentation(
            mosaic=args.mosaic,
            mixup=args.mixup,
            hsv_h=args.hsv_h,
            hsv_s=args.hsv_s,
            hsv_v=args.hsv_v,
            degrees=args.degrees,
            translate=args.translate,
            scale=args.scale,
            fliplr=args.fliplr,
            flipud=args.flipud,
        )
        
        # Print configuration summary
        logger.info("-" * 60)
        logger.info("Training Configuration:")
        logger.info(f"  Model: {args.model}")
        logger.info(f"  Data: {args.data}")
        logger.info(f"  Epochs: {args.epochs}")
        logger.info(f"  Batch size: {args.batch_size}")
        logger.info(f"  Image size: {args.img_size}")
        logger.info(f"  Learning rate: {args.lr0}")
        logger.info(f"  Resume: {args.resume}")
        logger.info(f"  Project: {args.project}/{args.name}")
        logger.info("-" * 60)
        
        # Execute training
        logger.info("Starting training...")
        results = pipeline.train(
            data_yaml=args.data,
            resume=args.resume,
            resume_weights=args.resume_weights
        )
        
        # Print training results
        logger.info("=" * 60)
        logger.info("Training Results:")
        logger.info(f"  Save directory: {results.get('save_dir', 'N/A')}")
        logger.info(f"  Best weights: {results.get('best_weights', 'N/A')}")
        logger.info(f"  Last weights: {results.get('last_weights', 'N/A')}")
        
        if results.get('metrics'):
            logger.info("  Metrics:")
            for key, value in results['metrics'].items():
                if isinstance(value, float):
                    logger.info(f"    {key}: {value:.4f}")
        logger.info("=" * 60)
        
        # Run validation if requested
        if args.val:
            logger.info("Running validation...")
            val_results = pipeline.validate(
                weights=results.get('best_weights'),
                data_yaml=args.data,
                split=args.val_split
            )
            
            logger.info("Validation Results:")
            logger.info(f"  mAP50: {val_results.get('mAP50', 'N/A')}")
            logger.info(f"  mAP50-95: {val_results.get('mAP50-95', 'N/A')}")
            logger.info(f"  Precision: {val_results.get('precision', 'N/A')}")
            logger.info(f"  Recall: {val_results.get('recall', 'N/A')}")
        
        # Export model if requested
        if args.export:
            logger.info(f"Exporting model to {args.export} format...")
            export_path = pipeline.export(
                weights=results.get('best_weights'),
                format=args.export,
                imgsz=args.img_size,
                half=args.export_half
            )
            logger.info(f"Model exported to: {export_path}")
        
        logger.info("Training script completed successfully!")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        return 1
    except RuntimeError as e:
        logger.error(f"Training error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())