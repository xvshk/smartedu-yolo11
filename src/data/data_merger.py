"""
数据合并模块
Data merger module for combining multiple datasets into unified format.
"""
import os
import shutil
import random
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import yaml

from src.config.behavior_config import BehaviorConfig
from src.data.label_mapper import LabelMapper


logger = logging.getLogger(__name__)


class DataMerger:
    """
    数据集合并器
    Merges multiple datasets into a unified YOLO format dataset.
    """
    
    # Supported image extensions
    IMAGE_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    
    def __init__(
        self, 
        config: Optional[BehaviorConfig] = None,
        output_dir: str = 'merged_dataset'
    ):
        """
        初始化数据合并器
        
        Args:
            config: BehaviorConfig instance
            output_dir: Output directory for merged dataset
        """
        self.config = config or BehaviorConfig()
        self.label_mapper = LabelMapper(self.config)
        self.output_dir = output_dir
        self.statistics: Dict = {}
        
    def scan_datasets(self, dataset_paths: List[str]) -> Dict[str, Dict]:
        """
        扫描所有数据集目录并识别图像和标签文件
        Scan all dataset directories and identify image and label files.
        
        Args:
            dataset_paths: List of paths to dataset directories
            
        Returns:
            Dictionary with dataset info including images, labels, and classes
        """
        datasets = {}
        
        for dataset_path in dataset_paths:
            dataset_path = Path(dataset_path)
            if not dataset_path.exists():
                logger.warning(f"Dataset path does not exist: {dataset_path}")
                continue
                
            dataset_name = dataset_path.name
            logger.info(f"Scanning dataset: {dataset_name}")
            
            dataset_info = {
                'path': str(dataset_path),
                'name': dataset_name,
                'images': {'train': [], 'val': [], 'test': []},
                'labels': {'train': [], 'val': [], 'test': []},
                'classes': [],
                'has_split': False
            }
            
            # Try to find data.yaml or similar config
            yaml_files = list(dataset_path.glob('*.yaml')) + list(dataset_path.glob('*.yml'))
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        yaml_config = yaml.safe_load(f)
                    if 'names' in yaml_config:
                        dataset_info['classes'] = yaml_config['names']
                        logger.info(f"Found classes in {yaml_file}: {dataset_info['classes']}")
                        break
                except Exception as e:
                    logger.warning(f"Error reading {yaml_file}: {e}")
            
            # Scan for images and labels
            images_dir = dataset_path / 'images'
            labels_dir = dataset_path / 'labels'
            
            # Check for train/val/test splits - Structure 1: images/train, labels/train
            for split in ['train', 'val', 'valid', 'test']:
                split_key = 'val' if split == 'valid' else split
                
                # Check images
                img_split_dir = images_dir / split
                if img_split_dir.exists():
                    dataset_info['has_split'] = True
                    for img_file in img_split_dir.iterdir():
                        if img_file.suffix.lower() in self.IMAGE_EXTENSIONS:
                            dataset_info['images'][split_key].append(str(img_file))
                            
                # Check labels
                lbl_split_dir = labels_dir / split
                if lbl_split_dir.exists():
                    for lbl_file in lbl_split_dir.iterdir():
                        if lbl_file.suffix.lower() == '.txt':
                            dataset_info['labels'][split_key].append(str(lbl_file))
            
            # Check for train/val/test splits - Structure 2: train/images, train/labels (student dataset style)
            if not dataset_info['has_split']:
                for split in ['train', 'val', 'valid', 'test']:
                    split_key = 'val' if split == 'valid' else split
                    
                    # Check images in split/images
                    img_split_dir = dataset_path / split / 'images'
                    if img_split_dir.exists():
                        dataset_info['has_split'] = True
                        for img_file in img_split_dir.iterdir():
                            if img_file.suffix.lower() in self.IMAGE_EXTENSIONS:
                                dataset_info['images'][split_key].append(str(img_file))
                                
                    # Check labels in split/labels
                    lbl_split_dir = dataset_path / split / 'labels'
                    if lbl_split_dir.exists():
                        for lbl_file in lbl_split_dir.iterdir():
                            if lbl_file.suffix.lower() == '.txt':
                                dataset_info['labels'][split_key].append(str(lbl_file))
            
            # If no splits found, check root images/labels directories
            if not dataset_info['has_split']:
                if images_dir.exists():
                    for img_file in images_dir.iterdir():
                        if img_file.suffix.lower() in self.IMAGE_EXTENSIONS:
                            dataset_info['images']['train'].append(str(img_file))
                            
                if labels_dir.exists():
                    for lbl_file in labels_dir.iterdir():
                        if lbl_file.suffix.lower() == '.txt':
                            dataset_info['labels']['train'].append(str(lbl_file))
            
            # Count total samples
            total_images = sum(len(imgs) for imgs in dataset_info['images'].values())
            total_labels = sum(len(lbls) for lbls in dataset_info['labels'].values())
            
            logger.info(
                f"Dataset {dataset_name}: {total_images} images, "
                f"{total_labels} labels, {len(dataset_info['classes'])} classes"
            )
            
            if total_images > 0:
                datasets[dataset_name] = dataset_info
                
        return datasets
    
    def merge_datasets(
        self, 
        datasets: Dict[str, Dict],
        preserve_splits: bool = True
    ) -> Dict[str, int]:
        """
        合并多个数据集到统一目录
        Merge multiple datasets into unified directory.
        
        Args:
            datasets: Dictionary of dataset info from scan_datasets()
            preserve_splits: Whether to preserve existing train/val/test splits
            
        Returns:
            Dictionary with merge statistics
        """
        # Create output directories
        output_path = Path(self.output_dir)
        for split in ['train', 'val', 'test']:
            (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
            (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)
            
        stats = {
            'total_images': 0,
            'total_labels': 0,
            'remapped_labels': 0,
            'filtered_labels': 0,
            'errors': 0,
            'by_dataset': {},
            'by_split': {'train': 0, 'val': 0, 'test': 0}
        }
        
        for dataset_name, dataset_info in datasets.items():
            logger.info(f"Merging dataset: {dataset_name}")
            dataset_stats = {'images': 0, 'labels': 0, 'remapped': 0, 'filtered': 0}
            
            # Determine dataset mapping name
            mapping_name = self._get_mapping_name(dataset_name)
            dataset_classes = dataset_info.get('classes', [])
            
            for split in ['train', 'val', 'test']:
                images = dataset_info['images'].get(split, [])
                
                for img_path in images:
                    img_path = Path(img_path)
                    img_stem = img_path.stem
                    
                    # Find corresponding label file
                    label_path = self._find_label_file(img_path, dataset_info)
                    
                    # Generate unique filename
                    unique_name = f"{dataset_name}_{img_stem}"
                    
                    # Copy image
                    dst_img = output_path / 'images' / split / f"{unique_name}{img_path.suffix}"
                    try:
                        shutil.copy2(img_path, dst_img)
                        stats['total_images'] += 1
                        dataset_stats['images'] += 1
                        stats['by_split'][split] += 1
                    except Exception as e:
                        logger.error(f"Error copying image {img_path}: {e}")
                        stats['errors'] += 1
                        continue
                    
                    # Process and copy label
                    dst_label = output_path / 'labels' / split / f"{unique_name}.txt"
                    if label_path and label_path.exists():
                        total, remapped = self.label_mapper.remap_label_file(
                            str(label_path),
                            str(dst_label),
                            mapping_name,
                            dataset_classes if dataset_classes else None
                        )
                        stats['total_labels'] += total
                        stats['remapped_labels'] += remapped
                        stats['filtered_labels'] += (total - remapped)
                        dataset_stats['labels'] += total
                        dataset_stats['remapped'] += remapped
                        dataset_stats['filtered'] += (total - remapped)
                    else:
                        # Create empty label file if no labels
                        dst_label.touch()
                        
            stats['by_dataset'][dataset_name] = dataset_stats
            logger.info(
                f"Dataset {dataset_name}: {dataset_stats['images']} images, "
                f"{dataset_stats['remapped']}/{dataset_stats['labels']} labels remapped"
            )
            
        self.statistics = stats
        return stats
    
    def split_dataset(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: int = 42
    ) -> Dict[str, int]:
        """
        按比例划分数据集
        Split dataset by specified ratios.
        
        Args:
            train_ratio: Ratio for training set (default 0.8)
            val_ratio: Ratio for validation set (default 0.1)
            test_ratio: Ratio for test set (default 0.1)
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary with split statistics
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, \
            "Ratios must sum to 1.0"
            
        random.seed(seed)
        output_path = Path(self.output_dir)
        
        # Collect all images from train directory (unsplit data goes here first)
        train_images_dir = output_path / 'images' / 'train'
        all_images = list(train_images_dir.glob('*'))
        all_images = [f for f in all_images if f.suffix.lower() in self.IMAGE_EXTENSIONS]
        
        if not all_images:
            logger.warning("No images found to split")
            return {'train': 0, 'val': 0, 'test': 0}
            
        # Shuffle images
        random.shuffle(all_images)
        
        # Calculate split indices
        n_total = len(all_images)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        train_images = all_images[:n_train]
        val_images = all_images[n_train:n_train + n_val]
        test_images = all_images[n_train + n_val:]
        
        # Move files to appropriate splits
        stats = {'train': len(train_images), 'val': 0, 'test': 0}
        
        for img_path in val_images:
            self._move_sample(img_path, 'train', 'val')
            stats['val'] += 1
            
        for img_path in test_images:
            self._move_sample(img_path, 'train', 'test')
            stats['test'] += 1
            
        logger.info(
            f"Dataset split: train={stats['train']}, "
            f"val={stats['val']}, test={stats['test']}"
        )
        
        return stats
    
    def generate_data_yaml(self, output_path: Optional[str] = None) -> str:
        """
        生成YOLO格式的data.yaml配置文件
        Generate YOLO format data.yaml configuration file.
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Path to generated data.yaml file
        """
        if output_path is None:
            output_path = os.path.join(self.output_dir, 'data.yaml')
            
        # Get absolute paths
        base_path = Path(self.output_dir).resolve()
        
        config = {
            'path': str(base_path),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'nc': self.config.get_num_classes(),
            'names': self.config.get_class_names(),
            # Alert configuration for downstream use
            'alert_config': {
                'normal_classes': self.config.NORMAL_CLASSES,
                'warning_classes': self.config.WARNING_CLASSES,
                'alert_levels': {
                    level: info['classes'] 
                    for level, info in self.config.ALERT_LEVELS.items()
                }
            }
        }
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"Generated data.yaml at {output_path}")
        except Exception as e:
            logger.error(f"Error generating data.yaml: {e}")
            raise
            
        return output_path
    
    def generate_statistics(self, output_path: Optional[str] = None) -> Dict:
        """
        生成数据集统计报告
        Generate dataset statistics report.
        
        Args:
            output_path: Optional path to save statistics JSON
            
        Returns:
            Dictionary containing statistics
        """
        output_dir = Path(self.output_dir)
        
        # Count samples per split
        split_stats = {}
        for split in ['train', 'val', 'test']:
            images_dir = output_dir / 'images' / split
            labels_dir = output_dir / 'labels' / split
            
            n_images = len(list(images_dir.glob('*'))) if images_dir.exists() else 0
            n_labels = len(list(labels_dir.glob('*.txt'))) if labels_dir.exists() else 0
            
            split_stats[split] = {
                'images': n_images,
                'labels': n_labels
            }
            
        # Count class distribution
        class_counts = defaultdict(lambda: {'train': 0, 'val': 0, 'test': 0, 'total': 0})
        
        for split in ['train', 'val', 'test']:
            labels_dir = output_dir / 'labels' / split
            if not labels_dir.exists():
                continue
                
            for label_file in labels_dir.glob('*.txt'):
                try:
                    with open(label_file, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                class_id = int(parts[0])
                                class_name = self.config.get_class_names()[class_id] \
                                    if 0 <= class_id < self.config.get_num_classes() else f'unknown_{class_id}'
                                class_counts[class_name][split] += 1
                                class_counts[class_name]['total'] += 1
                except Exception as e:
                    logger.warning(f"Error reading label file {label_file}: {e}")
                    
        # Build statistics report
        statistics = {
            'summary': {
                'total_images': sum(s['images'] for s in split_stats.values()),
                'total_labels': sum(s['labels'] for s in split_stats.values()),
                'num_classes': self.config.get_num_classes(),
                'class_names': self.config.get_class_names()
            },
            'splits': split_stats,
            'class_distribution': dict(class_counts),
            'behavior_types': {
                'normal': {
                    'classes': [self.config.CLASSES[i]['name'] for i in self.config.NORMAL_CLASSES],
                    'total_annotations': sum(
                        class_counts[self.config.CLASSES[i]['name']]['total'] 
                        for i in self.config.NORMAL_CLASSES
                        if self.config.CLASSES[i]['name'] in class_counts
                    )
                },
                'warning': {
                    'classes': [self.config.CLASSES[i]['name'] for i in self.config.WARNING_CLASSES],
                    'total_annotations': sum(
                        class_counts[self.config.CLASSES[i]['name']]['total'] 
                        for i in self.config.WARNING_CLASSES
                        if self.config.CLASSES[i]['name'] in class_counts
                    )
                }
            },
            'merge_stats': self.statistics
        }
        
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(statistics, f, indent=2, ensure_ascii=False)
                logger.info(f"Statistics saved to {output_path}")
            except Exception as e:
                logger.error(f"Error saving statistics: {e}")
                
        return statistics
    
    def _get_mapping_name(self, dataset_name: str) -> str:
        """
        获取数据集对应的映射名称
        Get the mapping name for a dataset.
        """
        # Try exact match first
        if dataset_name in self.config.LABEL_MAPPING:
            return dataset_name
            
        # Try partial matches
        dataset_lower = dataset_name.lower()
        
        if 'university' in dataset_lower and 'yolo' in dataset_lower:
            return 'university_yolo'
        if 'hrw' in dataset_lower:
            return 'HRW'
        if 'student' in dataset_lower:
            return 'student'
        if 'scb5-handrise' in dataset_lower or 'handrise-read-write' in dataset_lower:
            return 'SCB5-Handrise-Read-write'
        if 'scb5-stand' in dataset_lower:
            return 'SCB5-Stand'
        if 'scb5-talk' in dataset_lower:
            return 'SCB5-Talk'
        if 'scb5-discuss' in dataset_lower:
            return 'SCB5-Discuss'
            
        # Default to university_yolo as it has the most complete mapping
        logger.warning(f"No specific mapping for {dataset_name}, using university_yolo")
        return 'university_yolo'
    
    def _find_label_file(self, img_path: Path, dataset_info: Dict) -> Optional[Path]:
        """
        查找图像对应的标签文件
        Find the label file corresponding to an image.
        """
        img_stem = img_path.stem
        dataset_path = Path(dataset_info['path'])
        
        # Structure 1: labels/split/filename.txt (SCB-Dataset style)
        for split in ['train', 'val', 'valid', 'test']:
            label_path = dataset_path / 'labels' / split / f"{img_stem}.txt"
            if label_path.exists():
                return label_path
        
        # Structure 2: split/labels/filename.txt (student dataset style)
        for split in ['train', 'val', 'valid', 'test']:
            label_path = dataset_path / split / 'labels' / f"{img_stem}.txt"
            if label_path.exists():
                return label_path
                
        # Check in root labels directory
        label_path = dataset_path / 'labels' / f"{img_stem}.txt"
        if label_path.exists():
            return label_path
            
        return None
    
    def _move_sample(self, img_path: Path, from_split: str, to_split: str) -> None:
        """
        移动样本到不同的划分
        Move a sample from one split to another.
        """
        output_path = Path(self.output_dir)
        img_name = img_path.name
        label_name = img_path.stem + '.txt'
        
        # Move image
        src_img = output_path / 'images' / from_split / img_name
        dst_img = output_path / 'images' / to_split / img_name
        if src_img.exists():
            shutil.move(str(src_img), str(dst_img))
            
        # Move label
        src_label = output_path / 'labels' / from_split / label_name
        dst_label = output_path / 'labels' / to_split / label_name
        if src_label.exists():
            shutil.move(str(src_label), str(dst_label))
