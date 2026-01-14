"""
架构分析工具包
基础层 - 提供架构合规性检查和依赖分析功能
"""

from .architecture_analyzer import (
    ArchitectureAnalyzer,
    ArchitectureViolation,
    ViolationType,
    LayerType,
    LayerDependencyRules
)

from .dependency_analyzer import (
    DependencyAnalyzer,
    DependencyInfo
)

from .layer_dependency_checker import (
    LayerDependencyChecker,
    LayerDependencyViolation
)

from .compliance_checker import (
    ComplianceChecker,
    ComplianceReport,
    ComplianceMetrics,
    ComplianceLevel
)

__all__ = [
    'ArchitectureAnalyzer',
    'ArchitectureViolation', 
    'ViolationType',
    'LayerType',
    'LayerDependencyRules',
    'DependencyAnalyzer',
    'DependencyInfo',
    'LayerDependencyChecker',
    'LayerDependencyViolation',
    'ComplianceChecker',
    'ComplianceReport',
    'ComplianceMetrics',
    'ComplianceLevel'
]