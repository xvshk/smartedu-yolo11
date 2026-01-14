"""
层间依赖检查工具
基础层 - 验证层间依赖是否符合单向原则
"""
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .architecture_analyzer import LayerType, ArchitectureViolation, ViolationType


@dataclass
class LayerDependencyViolation:
    """层间依赖违规"""
    source_file: str
    target_module: str
    source_layer: LayerType
    target_layer: LayerType
    line_number: int
    violation_type: str  # "invalid_direction", "skip_layer", "circular"
    description: str


class LayerDependencyChecker:
    """层间依赖检查器"""
    
    # 定义允许的层间依赖方向
    ALLOWED_DEPENDENCIES = {
        LayerType.PRESENTATION: [LayerType.SERVICE, LayerType.FOUNDATION],
        LayerType.CONTROLLER: [LayerType.SERVICE, LayerType.FOUNDATION],
        LayerType.SERVICE: [LayerType.MODULE, LayerType.BUSINESS, LayerType.FOUNDATION],
        LayerType.BUSINESS: [LayerType.MODULE, LayerType.FOUNDATION],
        LayerType.MODULE: [LayerType.FOUNDATION],
        LayerType.FOUNDATION: []  # 基础层不依赖其他层
    }
    
    # 禁止的跨层调用（跳过中间层）
    FORBIDDEN_SKIP_LAYER = {
        LayerType.PRESENTATION: [LayerType.MODULE, LayerType.BUSINESS],
        LayerType.CONTROLLER: [LayerType.MODULE, LayerType.BUSINESS],
    }
    
    def __init__(self, project_root: str = "backend"):
        self.project_root = Path(project_root)
        self.violations: List[LayerDependencyViolation] = []
        
    def _get_layer_from_path(self, file_path: Path) -> Optional[LayerType]:
        """从文件路径确定所属层"""
        relative_path = file_path.relative_to(self.project_root)
        parts = relative_path.parts
        
        if len(parts) == 0:
            return None
            
        layer_name = parts[0]
        layer_mapping = {
            'presentation': LayerType.PRESENTATION,
            'controller': LayerType.CONTROLLER,
            'service': LayerType.SERVICE,
            'business': LayerType.BUSINESS,
            'model': LayerType.MODULE,
            'foundation': LayerType.FOUNDATION
        }
        
        return layer_mapping.get(layer_name)
    
    def _get_layer_from_module(self, module_name: str) -> Optional[LayerType]:
        """从模块名确定所属层"""
        if not module_name.startswith('backend.'):
            return None
            
        parts = module_name.split('.')
        if len(parts) < 2:
            return None
            
        layer_name = parts[1]
        layer_mapping = {
            'presentation': LayerType.PRESENTATION,
            'controller': LayerType.CONTROLLER,
            'service': LayerType.SERVICE,
            'business': LayerType.BUSINESS,
            'model': LayerType.MODULE,
            'foundation': LayerType.FOUNDATION
        }
        
        return layer_mapping.get(layer_name)
    
    def _extract_imports(self, file_path: Path) -> List[Tuple[str, int]]:
        """提取文件中的导入语句"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, node.lineno))
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append((node.module, node.lineno))
                        
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            
        return imports
    
    def _is_dependency_allowed(self, source_layer: LayerType, target_layer: LayerType) -> bool:
        """检查层间依赖是否被允许"""
        allowed_targets = self.ALLOWED_DEPENDENCIES.get(source_layer, [])
        return target_layer in allowed_targets
    
    def _is_skip_layer_violation(self, source_layer: LayerType, target_layer: LayerType) -> bool:
        """检查是否为跨层调用违规"""
        forbidden_targets = self.FORBIDDEN_SKIP_LAYER.get(source_layer, [])
        return target_layer in forbidden_targets
    
    def check_layer_dependencies(self) -> List[LayerDependencyViolation]:
        """检查所有层间依赖"""
        self.violations = []
        
        # 遍历所有Python文件
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            source_layer = self._get_layer_from_path(py_file)
            if source_layer is None:
                continue
                
            imports = self._extract_imports(py_file)
            
            for imported_module, line_no in imports:
                # 只检查项目内部依赖
                if not imported_module.startswith('backend.'):
                    continue
                    
                target_layer = self._get_layer_from_module(imported_module)
                if target_layer is None:
                    continue
                    
                # 跳过同层依赖
                if source_layer == target_layer:
                    continue
                
                # 检查依赖方向是否允许
                if not self._is_dependency_allowed(source_layer, target_layer):
                    violation = LayerDependencyViolation(
                        source_file=str(py_file),
                        target_module=imported_module,
                        source_layer=source_layer,
                        target_layer=target_layer,
                        line_number=line_no,
                        violation_type="invalid_direction",
                        description=f"Invalid dependency direction: {source_layer.value} -> {target_layer.value}"
                    )
                    self.violations.append(violation)
                
                # 检查跨层调用
                elif self._is_skip_layer_violation(source_layer, target_layer):
                    violation = LayerDependencyViolation(
                        source_file=str(py_file),
                        target_module=imported_module,
                        source_layer=source_layer,
                        target_layer=target_layer,
                        line_number=line_no,
                        violation_type="skip_layer",
                        description=f"Skip layer violation: {source_layer.value} should not directly call {target_layer.value}"
                    )
                    self.violations.append(violation)
        
        return self.violations
    
    def get_layer_dependency_matrix(self) -> Dict[str, Dict[str, int]]:
        """获取层间依赖矩阵"""
        matrix = {}
        
        # 初始化矩阵
        for source_layer in LayerType:
            matrix[source_layer.value] = {}
            for target_layer in LayerType:
                matrix[source_layer.value][target_layer.value] = 0
        
        # 统计依赖关系
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            source_layer = self._get_layer_from_path(py_file)
            if source_layer is None:
                continue
                
            imports = self._extract_imports(py_file)
            
            for imported_module, _ in imports:
                if not imported_module.startswith('backend.'):
                    continue
                    
                target_layer = self._get_layer_from_module(imported_module)
                if target_layer is None:
                    continue
                    
                matrix[source_layer.value][target_layer.value] += 1
        
        return matrix
    
    def generate_dependency_report(self) -> str:
        """生成层间依赖报告"""
        report = ["🏗️ Layer Dependency Analysis Report", "=" * 50, ""]
        
        # 违规统计
        violation_types = {}
        for violation in self.violations:
            vtype = violation.violation_type
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        report.append("📊 Violation Summary:")
        if violation_types:
            for vtype, count in violation_types.items():
                report.append(f"  {vtype}: {count}")
        else:
            report.append("  ✅ No layer dependency violations found!")
        report.append("")
        
        # 详细违规列表
        if self.violations:
            report.append("🚨 Layer Dependency Violations:")
            for i, violation in enumerate(self.violations[:10], 1):  # 只显示前10个
                report.append(f"  {i}. {violation.description}")
                report.append(f"     File: {violation.source_file}:{violation.line_number}")
                report.append(f"     Target: {violation.target_module}")
                report.append("")
            
            if len(self.violations) > 10:
                report.append(f"  ... and {len(self.violations) - 10} more violations")
                report.append("")
        
        # 层间依赖矩阵
        matrix = self.get_layer_dependency_matrix()
        report.append("📈 Layer Dependency Matrix:")
        report.append("     " + "".join(f"{layer[:4]:>8}" for layer in matrix.keys()))
        
        for source_layer, targets in matrix.items():
            row = f"{source_layer[:4]:>4} "
            for target_layer, count in targets.items():
                if count > 0:
                    row += f"{count:>8}"
                else:
                    row += f"{'':>8}"
            report.append(row)
        report.append("")
        
        # 建议
        report.append("💡 Recommendations:")
        if violation_types.get("invalid_direction", 0) > 0:
            report.append("  - Fix invalid dependency directions by introducing proper interfaces")
        if violation_types.get("skip_layer", 0) > 0:
            report.append("  - Eliminate skip-layer calls by routing through intermediate layers")
        if not violation_types:
            report.append("  - Layer dependencies are well-structured!")
        
        return "\n".join(report)
    
    def convert_to_architecture_violations(self) -> List[ArchitectureViolation]:
        """转换为架构违规格式"""
        arch_violations = []
        
        for violation in self.violations:
            if violation.violation_type == "invalid_direction":
                vtype = ViolationType.CROSS_LAYER_CALL
            elif violation.violation_type == "skip_layer":
                vtype = ViolationType.CROSS_LAYER_CALL
            else:
                vtype = ViolationType.CROSS_LAYER_CALL
            
            arch_violation = ArchitectureViolation(
                violation_type=vtype,
                source_file=violation.source_file,
                target_file=violation.target_module,
                line_number=violation.line_number,
                description=violation.description,
                severity="error"
            )
            arch_violations.append(arch_violation)
        
        return arch_violations


def main():
    """主函数"""
    checker = LayerDependencyChecker()
    
    print("Checking layer dependencies...")
    violations = checker.check_layer_dependencies()
    
    print(checker.generate_dependency_report())
    
    return len(violations)


if __name__ == "__main__":
    import sys
    sys.exit(main())