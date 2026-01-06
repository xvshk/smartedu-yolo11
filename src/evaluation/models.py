"""
数据模型定义
Data model definitions for model evaluation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np


@dataclass
class Detection:
    """
    检测结果
    Single detection result from model inference.
    """
    class_id: int
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    image_id: str = ""
    
    def __post_init__(self):
        if len(self.bbox) != 4:
            raise ValueError("bbox must have exactly 4 values [x1, y1, x2, y2]")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class ClassMetrics:
    """
    单个类别的评估指标
    Evaluation metrics for a single class.
    """
    class_id: int
    class_name: str
    precision: float
    recall: float
    f1_score: float
    ap50: float
    ap50_95: float
    support: int  # 该类别的样本数
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'ap50': self.ap50,
            'ap50_95': self.ap50_95,
            'support': self.support,
        }


@dataclass
class OverallMetrics:
    """
    整体评估指标
    Overall evaluation metrics.
    """
    mAP50: float
    mAP50_95: float
    precision: float
    recall: float
    f1_score: float
    total_images: int
    total_predictions: int
    total_ground_truths: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'mAP50': self.mAP50,
            'mAP50_95': self.mAP50_95,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'total_images': self.total_images,
            'total_predictions': self.total_predictions,
            'total_ground_truths': self.total_ground_truths,
        }


@dataclass
class GroupMetrics:
    """
    行为组指标
    Metrics grouped by behavior type (normal vs warning).
    """
    # 正常行为指标 (handrise, read, write)
    normal_precision: float
    normal_recall: float
    normal_f1: float
    normal_mAP50: float
    
    # 预警行为指标 (sleep, stand, using_electronic_devices, talk)
    warning_precision: float
    warning_recall: float
    warning_f1: float
    warning_mAP50: float
    
    # 预警行为召回率是否低于0.5（关键问题标记）
    warning_recall_critical: bool = False
    
    def __post_init__(self):
        self.warning_recall_critical = self.warning_recall < 0.5
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'normal': {
                'precision': self.normal_precision,
                'recall': self.normal_recall,
                'f1_score': self.normal_f1,
                'mAP50': self.normal_mAP50,
            },
            'warning': {
                'precision': self.warning_precision,
                'recall': self.warning_recall,
                'f1_score': self.warning_f1,
                'mAP50': self.warning_mAP50,
                'recall_critical': self.warning_recall_critical,
            },
        }


@dataclass
class ConfusedPair:
    """
    混淆类别对
    A pair of classes that are frequently confused.
    """
    class_a: int
    class_a_name: str
    class_b: int
    class_b_name: str
    confusion_rate: float  # 混淆率
    recommendation: str  # 改进建议
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'class_a': self.class_a,
            'class_a_name': self.class_a_name,
            'class_b': self.class_b,
            'class_b_name': self.class_b_name,
            'confusion_rate': self.confusion_rate,
            'recommendation': self.recommendation,
        }


@dataclass
class EvaluationResult:
    """
    完整评估结果
    Complete evaluation result containing all metrics and analysis.
    """
    # 元数据
    weights_path: str
    data_yaml: str
    split: str
    evaluation_date: datetime
    conf_threshold: float
    iou_threshold: float
    
    # 指标
    overall_metrics: OverallMetrics
    per_class_metrics: Dict[int, ClassMetrics]
    group_metrics: GroupMetrics
    
    # 混淆分析
    confusion_matrix: np.ndarray
    confused_pairs: List[ConfusedPair]
    
    # 类别名称映射
    class_names: List[str] = field(default_factory=list)
    class_names_cn: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'metadata': {
                'weights_path': self.weights_path,
                'data_yaml': self.data_yaml,
                'split': self.split,
                'evaluation_date': self.evaluation_date.isoformat(),
                'conf_threshold': self.conf_threshold,
                'iou_threshold': self.iou_threshold,
                'class_names': self.class_names,
                'class_names_cn': self.class_names_cn,
            },
            'overall_metrics': self.overall_metrics.to_dict(),
            'per_class_metrics': {
                str(k): v.to_dict() for k, v in self.per_class_metrics.items()
            },
            'group_metrics': self.group_metrics.to_dict(),
            'confusion_matrix': self.confusion_matrix.tolist(),
            'confused_pairs': [p.to_dict() for p in self.confused_pairs],
        }
