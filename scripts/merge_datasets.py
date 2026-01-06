#!/usr/bin/env python
"""
数据合并脚本
Script for merging multiple datasets into unified YOLO format.

Usage:
    python scripts/merge_datasets.py --datasets path1 path2 --output merged_dataset
    python scripts/merge_datasets.py --datasets ./student ./SCB-Dataset --output ./merged --split-ratio 0.8 0.1 0.1
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.behavior_config import BehaviorConfig
from src.data.data_merger import DataMerger
from src.data.label_mapper import LabelMapper


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Merge multiple datasets into unified YOLO format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Merge two datasets with default 8:1:1 split
    python scripts/merge_datasets.py --datasets ./student ./SCB-Dataset --output ./merged_dataset

    # Merge with custom split ratio
    python scripts/merge_datasets.py --datasets ./data1 ./data2 --output ./merged --split-ratio 0.7 0.15 0.15

    # Preserve existing splits from source datasets
    python scripts/merge_datasets.py --datasets ./data1 --output ./merged --preserve-splits

    # Generate mapping config file
    python scripts/merge_datasets.py --datasets ./data1 --output ./merged --generate-mapping
        """
    )
    
    parser.add_argument(
        '--datasets', '-d',
        nargs='+',
        required=True,
        help='Paths to dataset directories to merge'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='merged_dataset',
        help='Output directory for merged dataset (default: merged_dataset)'
    )
    
    parser.add_argument(
        '--split-ratio', '-s',
        nargs=3,
        type=float,
        default=[0.8, 0.1, 0.1],
        metavar=('TRAIN', 'VAL', 'TEST'),
        help='Train/val/test split ratios (default: 0.8 0.1 0.1)'
    )
    
    parser.add_argument(
        '--preserve-splits', '-p',
        action='store_true',
        help='Preserve existing train/val/test splits from source datasets'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducible splits (default: 42)'
    )
    
    parser.add_argument(
        '--generate-mapping', '-m',
        action='store_true',
        help='Generate label mapping configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate split ratios
    train_ratio, val_ratio, test_ratio = args.split_ratio
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
        logger.error("Split ratios must sum to 1.0")
        return 1
    
    # Validate dataset paths
    dataset_paths = []
    for path in args.datasets:
        p = Path(path)
        if not p.exists():
            logger.error(f"Dataset path does not exist: {path}")
            return 1
        dataset_paths.append(str(p.resolve()))
    
    logger.info(f"Merging {len(dataset_paths)} datasets into {args.output}")
    logger.info(f"Split ratio: train={train_ratio}, val={val_ratio}, test={test_ratio}")
    
    try:
        # Initialize config and merger
        config = BehaviorConfig()
        merger = DataMerger(config=config, output_dir=args.output)
        
        # Generate mapping config if requested
        if args.generate_mapping:
            label_mapper = LabelMapper(config)
            mapping_path = Path(args.output) / 'label_mapping.yaml'
            label_mapper.generate_mapping_config(str(mapping_path))
            logger.info(f"Generated mapping config: {mapping_path}")
        
        # Scan datasets
        logger.info("Scanning datasets...")
        datasets = merger.scan_datasets(dataset_paths)
        
        if not datasets:
            logger.error("No valid datasets found")
            return 1
        
        logger.info(f"Found {len(datasets)} datasets:")
        for name, info in datasets.items():
            total_images = sum(len(imgs) for imgs in info['images'].values())
            logger.info(f"  - {name}: {total_images} images, has_split={info['has_split']}")
        
        # Merge datasets
        logger.info("Merging datasets...")
        merge_stats = merger.merge_datasets(datasets, preserve_splits=args.preserve_splits)
        
        logger.info(f"Merge complete:")
        logger.info(f"  - Total images: {merge_stats['total_images']}")
        logger.info(f"  - Total labels: {merge_stats['total_labels']}")
        logger.info(f"  - Remapped labels: {merge_stats['remapped_labels']}")
        logger.info(f"  - Filtered labels: {merge_stats['filtered_labels']}")
        
        # Split dataset if not preserving splits
        if not args.preserve_splits:
            logger.info("Splitting dataset...")
            split_stats = merger.split_dataset(
                train_ratio=train_ratio,
                val_ratio=val_ratio,
                test_ratio=test_ratio,
                seed=args.seed
            )
            logger.info(f"Split complete: train={split_stats['train']}, val={split_stats['val']}, test={split_stats['test']}")
        
        # Generate data.yaml
        logger.info("Generating data.yaml...")
        yaml_path = merger.generate_data_yaml()
        logger.info(f"Generated: {yaml_path}")
        
        # Generate statistics
        logger.info("Generating statistics...")
        stats_path = Path(args.output) / 'statistics.json'
        statistics = merger.generate_statistics(str(stats_path))
        
        # Print summary
        print("\n" + "="*60)
        print("MERGE SUMMARY")
        print("="*60)
        print(f"Output directory: {args.output}")
        print(f"Total images: {statistics['summary']['total_images']}")
        print(f"Total labels: {statistics['summary']['total_labels']}")
        print(f"Number of classes: {statistics['summary']['num_classes']}")
        print(f"Class names: {', '.join(statistics['summary']['class_names'])}")
        print("\nSplit distribution:")
        for split, info in statistics['splits'].items():
            print(f"  {split}: {info['images']} images, {info['labels']} labels")
        print("\nClass distribution:")
        for class_name, counts in statistics['class_distribution'].items():
            print(f"  {class_name}: {counts['total']} total")
        print("\nBehavior types:")
        print(f"  Normal behaviors: {statistics['behavior_types']['normal']['total_annotations']} annotations")
        print(f"  Warning behaviors: {statistics['behavior_types']['warning']['total_annotations']} annotations")
        print("="*60)
        
        logger.info("Dataset merge completed successfully!")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during merge: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
