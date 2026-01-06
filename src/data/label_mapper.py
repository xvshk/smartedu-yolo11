"""
标签映射模块
Label mapping module for unifying labels across different datasets.
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
import yaml

from src.config.behavior_config import BehaviorConfig


logger = logging.getLogger(__name__)


class LabelMapper:
    """
    标签映射器
    Maps labels from different datasets to unified class IDs.
    """
    
    # Teacher behavior class names to filter out
    TEACHER_BEHAVIORS: List[str] = [
        'teacher', 'guide', 'answer', 'On-stage interaction', 
        'blackboard-writing', 'pointing', 'walking', 'explaining'
    ]
    
    def __init__(self, config: Optional[BehaviorConfig] = None):
        """
        初始化标签映射器
        
        Args:
            config: BehaviorConfig instance, creates new one if None
        """
        self.config = config or BehaviorConfig()
        
    def remap_label(
        self, 
        original_class_id: int, 
        dataset_name: str,
        dataset_classes: Optional[List[str]] = None
    ) -> Optional[int]:
        """
        将原始标签映射到统一类别ID
        Remap original class ID to unified class ID.
        
        Args:
            original_class_id: Original class ID from the source dataset
            dataset_name: Name of the source dataset
            dataset_classes: List of class names in the source dataset (optional)
            
        Returns:
            Unified class ID (0-6), or None if mapping not found or should be filtered
        """
        # Get mapping for this dataset
        mapping = self.config.get_mapping_for_dataset(dataset_name)
        
        if mapping is None:
            logger.warning(f"No mapping found for dataset: {dataset_name}")
            return None
            
        # If dataset_classes provided, use it to get the class name
        if dataset_classes is not None:
            if original_class_id < 0 or original_class_id >= len(dataset_classes):
                logger.warning(
                    f"Invalid class ID {original_class_id} for dataset {dataset_name} "
                    f"with {len(dataset_classes)} classes"
                )
                return None
            class_name = dataset_classes[original_class_id]
        else:
            # Try to find class name by reverse lookup in mapping
            class_name = None
            for name, mapped_id in mapping.items():
                # This is a fallback - not ideal but handles simple cases
                if mapped_id == original_class_id:
                    class_name = name
                    break
            if class_name is None:
                logger.warning(
                    f"Cannot determine class name for ID {original_class_id} "
                    f"in dataset {dataset_name}"
                )
                return None
        
        # Check if this is a teacher behavior
        if self._is_teacher_behavior(class_name):
            logger.debug(f"Filtering teacher behavior: {class_name}")
            return None
            
        # Get unified class ID from mapping
        unified_id = mapping.get(class_name)
        if unified_id is None:
            # Try case-insensitive match
            for mapped_name, mapped_id in mapping.items():
                if mapped_name.lower() == class_name.lower():
                    unified_id = mapped_id
                    break
                    
        if unified_id is None:
            logger.warning(
                f"No mapping for class '{class_name}' in dataset {dataset_name}"
            )
            
        return unified_id
    
    def remap_label_line(
        self,
        label_line: str,
        dataset_name: str,
        dataset_classes: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        重映射单行YOLO格式标签
        Remap a single YOLO format label line.
        
        Args:
            label_line: YOLO format label line (class_id x y w h)
            dataset_name: Name of the source dataset
            dataset_classes: List of class names in the source dataset
            
        Returns:
            Remapped label line, or None if should be filtered
        """
        parts = label_line.strip().split()
        if len(parts) < 5:
            logger.warning(f"Invalid label line format: {label_line}")
            return None
            
        try:
            original_class_id = int(parts[0])
        except ValueError:
            logger.warning(f"Invalid class ID in label line: {label_line}")
            return None
            
        unified_id = self.remap_label(original_class_id, dataset_name, dataset_classes)
        if unified_id is None:
            return None
            
        # Reconstruct the label line with unified class ID
        return f"{unified_id} {' '.join(parts[1:])}"
    
    def remap_label_file(
        self,
        input_path: str,
        output_path: str,
        dataset_name: str,
        dataset_classes: Optional[List[str]] = None
    ) -> Tuple[int, int]:
        """
        重映射整个标签文件
        Remap an entire label file.
        
        Args:
            input_path: Path to input label file
            output_path: Path to output label file
            dataset_name: Name of the source dataset
            dataset_classes: List of class names in the source dataset
            
        Returns:
            Tuple of (total_lines, remapped_lines)
        """
        total_lines = 0
        remapped_lines = 0
        output_lines = []
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    total_lines += 1
                    
                    remapped = self.remap_label_line(
                        line, dataset_name, dataset_classes
                    )
                    if remapped is not None:
                        output_lines.append(remapped)
                        remapped_lines += 1
                        
        except Exception as e:
            logger.error(f"Error reading label file {input_path}: {e}")
            return 0, 0
            
        # Write output file
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
                if output_lines:
                    f.write('\n')
        except Exception as e:
            logger.error(f"Error writing label file {output_path}: {e}")
            return total_lines, 0
            
        return total_lines, remapped_lines
    
    def filter_teacher_labels(
        self,
        label_lines: List[str],
        dataset_classes: List[str]
    ) -> List[str]:
        """
        过滤教师行为标注
        Filter out teacher behavior annotations.
        
        Args:
            label_lines: List of YOLO format label lines
            dataset_classes: List of class names in the dataset
            
        Returns:
            Filtered list of label lines (only student behaviors)
        """
        filtered = []
        for line in label_lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
                
            try:
                class_id = int(parts[0])
            except ValueError:
                continue
                
            if class_id < 0 or class_id >= len(dataset_classes):
                continue
                
            class_name = dataset_classes[class_id]
            if not self._is_teacher_behavior(class_name):
                filtered.append(line)
                
        return filtered
    
    def _is_teacher_behavior(self, class_name: str) -> bool:
        """
        判断是否为教师行为
        Check if a class name represents teacher behavior.
        
        Args:
            class_name: The class name to check
            
        Returns:
            True if it's a teacher behavior, False otherwise
        """
        class_name_lower = class_name.lower()
        for teacher_behavior in self.TEACHER_BEHAVIORS:
            if teacher_behavior.lower() in class_name_lower:
                return True
        return False
    
    def generate_mapping_config(self, output_path: Optional[str] = None) -> Dict:
        """
        生成映射配置文件
        Generate mapping configuration file.
        
        Args:
            output_path: Optional path to save the config file (YAML format)
            
        Returns:
            Dictionary containing the mapping configuration
        """
        config_dict = {
            'unified_classes': {
                class_id: {
                    'name': info['name'],
                    'cn_name': info['cn_name'],
                    'type': info['type'],
                    'alert_level': info['alert_level']
                }
                for class_id, info in self.config.CLASSES.items()
            },
            'class_names': self.config.get_class_names(),
            'num_classes': self.config.get_num_classes(),
            'normal_classes': self.config.NORMAL_CLASSES,
            'warning_classes': self.config.WARNING_CLASSES,
            'alert_levels': {
                level: {
                    'name': info['name'],
                    'cn_name': info['cn_name'],
                    'classes': info['classes']
                }
                for level, info in self.config.ALERT_LEVELS.items()
            },
            'dataset_mappings': self.config.LABEL_MAPPING,
            'teacher_behaviors_filtered': self.TEACHER_BEHAVIORS
        }
        
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
                logger.info(f"Mapping config saved to {output_path}")
            except Exception as e:
                logger.error(f"Error saving mapping config: {e}")
                
        return config_dict
    
    def get_dataset_class_mapping(
        self, 
        dataset_name: str,
        dataset_classes: List[str]
    ) -> Dict[int, Optional[int]]:
        """
        获取数据集的完整类别映射表
        Get complete class mapping table for a dataset.
        
        Args:
            dataset_name: Name of the dataset
            dataset_classes: List of class names in the dataset
            
        Returns:
            Dictionary mapping original class IDs to unified class IDs
        """
        mapping_table = {}
        for orig_id, class_name in enumerate(dataset_classes):
            unified_id = self.remap_label(orig_id, dataset_name, dataset_classes)
            mapping_table[orig_id] = unified_id
        return mapping_table
