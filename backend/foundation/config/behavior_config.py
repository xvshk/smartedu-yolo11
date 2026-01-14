"""
行为类别配置模块
Behavior category configuration model for classroom behavior detection.
"""
from typing import Dict, List, Optional


class BehaviorConfig:
    """
    行为类别配置类
    Manages behavior class definitions, label mappings, and alert levels.
    """
    
    # 统一类别定义 - Unified class definitions
    # 7 student behavior classes: 3 normal + 4 warning
    CLASSES: Dict[int, Dict] = {
        0: {'name': 'handrise', 'cn_name': '举手', 'type': 'normal', 'alert_level': 0},
        1: {'name': 'read', 'cn_name': '阅读', 'type': 'normal', 'alert_level': 0},
        2: {'name': 'write', 'cn_name': '书写', 'type': 'normal', 'alert_level': 0},
        3: {'name': 'sleep', 'cn_name': '睡觉', 'type': 'warning', 'alert_level': 3},
        4: {'name': 'stand', 'cn_name': '站立', 'type': 'warning', 'alert_level': 1},
        5: {'name': 'using_electronic_devices', 'cn_name': '使用电子设备', 'type': 'warning', 'alert_level': 3},
        6: {'name': 'talk', 'cn_name': '交谈', 'type': 'warning', 'alert_level': 2},
    }
    
    # 数据集标签映射 - Dataset label mappings
    # Maps original dataset labels to unified class IDs
    LABEL_MAPPING: Dict[str, Dict[str, int]] = {
        # student dataset mapping
        'student': {
            'handrise': 0,
            'read': 1,
            'write': 2,
            'sleep': 3,
            'stand': 4,
            'using_electronic_devices': 5,
        },
        # SCB5 datasets mappings
        'SCB5-Handrise-Read-write': {
            'hand-raising': 0,
            'handrise': 0,
            'read': 1,
            'write': 2,
        },
        'SCB5-Stand': {
            'stand': 4,
        },
        'SCB5-Talk': {
            'talk': 6,
        },
        'SCB5-Discuss': {
            'talk': 6,
            'discuss': 6,
        },
        # University YOLO dataset mapping
        'university_yolo': {
            'handrise': 0,
            'read': 1,
            'write': 2,
            'sleep': 3,
            'stand': 4,
            'using_electronic_devices': 5,
            'talk': 6,
        },
        # HRW dataset mapping (Handrise-Read-Write)
        'HRW': {
            'hand-raising': 0,
            'handrise': 0,
            'read': 1,
            'write': 2,
        },
    }
    
    # Normal behavior class IDs
    NORMAL_CLASSES: List[int] = [0, 1, 2]
    
    # Warning behavior class IDs
    WARNING_CLASSES: List[int] = [3, 4, 5, 6]
    
    # Alert level definitions
    ALERT_LEVELS: Dict[int, Dict] = {
        0: {'name': 'normal', 'cn_name': '正常', 'classes': [0, 1, 2]},
        1: {'name': 'mild', 'cn_name': '轻度预警', 'classes': [4]},  # stand
        2: {'name': 'moderate', 'cn_name': '中度预警', 'classes': [6]},  # talk
        3: {'name': 'severe', 'cn_name': '严重预警', 'classes': [3, 5]},  # sleep, using_electronic_devices
    }
    
    def get_class_info(self, class_id: int) -> Optional[Dict]:
        """
        获取指定类别ID的完整信息
        Get complete information for a given class ID.
        
        Args:
            class_id: The class ID (0-6)
            
        Returns:
            Dictionary containing name, cn_name, type, and alert_level,
            or None if class_id is invalid.
        """
        return self.CLASSES.get(class_id)
    
    def get_alert_level(self, class_id: int) -> int:
        """
        获取指定类别的预警级别
        Get the alert level for a given class ID.
        
        Args:
            class_id: The class ID (0-6)
            
        Returns:
            Alert level (0-3), or -1 if class_id is invalid.
        """
        class_info = self.CLASSES.get(class_id)
        if class_info is None:
            return -1
        return class_info['alert_level']
    
    def is_warning_behavior(self, class_id: int) -> bool:
        """
        判断指定类别是否为预警行为
        Check if a class ID represents a warning behavior.
        
        Args:
            class_id: The class ID (0-6)
            
        Returns:
            True if the behavior is a warning type, False otherwise.
        """
        class_info = self.CLASSES.get(class_id)
        if class_info is None:
            return False
        return class_info['type'] == 'warning'
    
    def get_class_names(self) -> List[str]:
        """
        获取所有类别名称列表（按ID顺序）
        Get list of all class names in order of class ID.
        
        Returns:
            List of class names: ['handrise', 'read', 'write', 'sleep', 
                                  'stand', 'using_electronic_devices', 'talk']
        """
        return [self.CLASSES[i]['name'] for i in range(len(self.CLASSES))]
    
    def get_class_id_by_name(self, name: str) -> int:
        """
        根据类别名称获取类别ID
        Get class ID by class name.
        
        Args:
            name: The class name (e.g., 'handrise', 'sleep')
            
        Returns:
            Class ID (0-6), or -1 if name is not found.
        """
        for class_id, info in self.CLASSES.items():
            if info['name'] == name:
                return class_id
        return -1
    
    def get_behavior_type(self, class_id: int) -> Optional[str]:
        """
        获取指定类别的行为类型
        Get the behavior type for a given class ID.
        
        Args:
            class_id: The class ID (0-6)
            
        Returns:
            'normal' or 'warning', or None if class_id is invalid.
        """
        class_info = self.CLASSES.get(class_id)
        if class_info is None:
            return None
        return class_info['type']
    
    def get_mapping_for_dataset(self, dataset_name: str) -> Optional[Dict[str, int]]:
        """
        获取指定数据集的标签映射
        Get label mapping for a specific dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary mapping label names to class IDs, or None if not found.
        """
        return self.LABEL_MAPPING.get(dataset_name)
    
    def get_num_classes(self) -> int:
        """
        获取类别总数
        Get total number of classes.
        
        Returns:
            Number of classes (7)
        """
        return len(self.CLASSES)
    
    def generate_mapping_config(self) -> Dict:
        """
        生成类别映射配置文件内容
        Generate mapping configuration for export.
        
        Returns:
            Dictionary containing complete class and mapping configuration.
        """
        return {
            'classes': {
                class_id: {
                    'name': info['name'],
                    'cn_name': info['cn_name'],
                    'type': info['type'],
                    'alert_level': info['alert_level']
                }
                for class_id, info in self.CLASSES.items()
            },
            'normal_classes': self.NORMAL_CLASSES,
            'warning_classes': self.WARNING_CLASSES,
            'alert_levels': self.ALERT_LEVELS,
            'dataset_mappings': self.LABEL_MAPPING
        }
