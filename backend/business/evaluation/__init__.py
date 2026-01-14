"""
模型评估模块
Model evaluation model for classroom behavior detection.
"""
from .models import (
    Detection,
    ClassMetrics,
    OverallMetrics,
    GroupMetrics,
    ConfusedPair,
    EvaluationResult,
)
from .metrics import MetricsCalculator
from .report import ReportGenerator
from .evaluator import ModelEvaluator

__all__ = [
    'Detection',
    'ClassMetrics',
    'OverallMetrics',
    'GroupMetrics',
    'ConfusedPair',
    'EvaluationResult',
    'MetricsCalculator',
    'ReportGenerator',
    'ModelEvaluator',
]
