"""
架构分析器 - 静态代码分析工具
基础层 - 纯工具，用于检测分层架构违规
"""
import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import networkx as nx


class LayerType(Enum):
    """层级类型枚举"""
    CONTROLLER = "controller"
    SERVICE = "service"
    MODULE = "model"
    PRESENTATION = "presentation"
    BUSINESS = "business"
    FOUNDATION = "foundation"
    ML = "ml"  # 横向支撑


class ViolationType(Enum):
    """违规类型枚举"""
    CROSS_LAYER_CALL = "cross_layer_call"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    WRONG_LAYER_CONTENT = "wrong_layer_content"
    DIRECT_DATABASE_ACCESS = "direct_database_access"
    BUSINESS_LOGIC_IN_CONTROLLER = "business_logic_in_controller"


@dataclass
class ArchitectureViolation:
    """架构违规数据模型"""
    violation_type: ViolationType
    source_file: str
    target_file: Optional[str]
    line_number: int
    description: str
    severity: str  # "error", "warning"
    
    def __str__(self) -> str:
        return f"{self.severity.upper()}: {self.description} at {self.source_file}:{self.line_number}"


class LayerDependencyRules:
    """分层依赖规则定义"""
    
    # 允许的依赖关系 (上层 -> 下层)
    ALLOWED_DEPENDENCIES = {
        LayerType.CONTROLLER: {LayerType.SERVICE, LayerType.FOUNDATION},
        LayerType.PRESENTATION: {LayerType.BUSINESS, LayerType.SERVICE, LayerType.FOUNDATION},
        LayerType.SERVICE: {LayerType.MODULE, LayerType.FOUNDATION},
        LayerType.BUSINESS: {LayerType.MODULE, LayerType.FOUNDATION},
        LayerType.MODULE: {LayerType.FOUNDATION},
        LayerType.FOUNDATION: set(),  # 基础层不依赖其他层
        LayerType.ML: {LayerType.FOUNDATION}  # MLOps可以使用基础设施
    }
    
    # 禁止的直接依赖 (跨层调用)
    FORBIDDEN_DEPENDENCIES = {
        LayerType.CONTROLLER: {LayerType.MODULE, LayerType.BUSINESS},
        LayerType.PRESENTATION: {LayerType.MODULE},
    }
    
    @classmethod
    def is_dependency_allowed(cls, from_layer: LayerType, to_layer: LayerType) -> bool:
        """检查依赖是否被允许"""
        if from_layer == to_layer:
            return True  # 同层调用允许
        
        # 检查是否在允许列表中
        allowed = cls.ALLOWED_DEPENDENCIES.get(from_layer, set())
        if to_layer in allowed:
            return True
            
        # 检查是否被明确禁止
        forbidden = cls.FORBIDDEN_DEPENDENCIES.get(from_layer, set())
        if to_layer in forbidden:
            return False
            
        return False


class ImportAnalyzer(ast.NodeVisitor):
    """导入语句分析器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: List[Tuple[str, int]] = []  # (module_name, line_number)
        
    def visit_Import(self, node: ast.Import):
        """访问import语句"""
        for alias in node.names:
            self.imports.append((alias.name, node.lineno))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """访问from...import语句"""
        if node.module:
            self.imports.append((node.module, node.lineno))
        self.generic_visit(node)


class CodePatternAnalyzer(ast.NodeVisitor):
    """代码模式分析器 - 检测不符合分层的代码模式"""
    
    def __init__(self, file_path: str, layer_type: LayerType):
        self.file_path = file_path
        self.layer_type = layer_type
        self.violations: List[ArchitectureViolation] = []
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """分析函数定义"""
        if self.layer_type == LayerType.CONTROLLER:
            self._check_controller_function(node)
        elif self.layer_type == LayerType.SERVICE:
            self._check_service_function(node)
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """分析函数调用"""
        if self.layer_type == LayerType.CONTROLLER:
            self._check_controller_calls(node)
        elif self.layer_type in [LayerType.SERVICE, LayerType.BUSINESS]:
            self._check_database_calls(node)
            
        self.generic_visit(node)
    
    def _check_controller_function(self, node: ast.FunctionDef):
        """检查controller函数是否包含业务逻辑"""
        # 检查函数体长度 - controller函数应该简短
        if len(node.body) > 20:  # 超过20行可能包含业务逻辑
            self.violations.append(ArchitectureViolation(
                violation_type=ViolationType.BUSINESS_LOGIC_IN_CONTROLLER,
                source_file=self.file_path,
                target_file=None,
                line_number=node.lineno,
                description=f"Controller function '{node.name}' is too complex ({len(node.body)} lines), may contain business logic",
                severity="warning"
            ))
    
    def _check_controller_calls(self, node: ast.Call):
        """检查controller中的函数调用"""
        # 检查是否直接调用数据库操作
        if isinstance(node.func, ast.Attribute):
            if hasattr(node.func.value, 'id'):
                if 'cursor' in getattr(node.func.value, 'id', ''):
                    self.violations.append(ArchitectureViolation(
                        violation_type=ViolationType.DIRECT_DATABASE_ACCESS,
                        source_file=self.file_path,
                        target_file=None,
                        line_number=node.lineno,
                        description="Controller should not directly access database",
                        severity="error"
                    ))
    
    def _check_service_function(self, node: ast.FunctionDef):
        """检查service函数结构"""
        # Service函数应该有适当的复杂度
        pass
    
    def _check_database_calls(self, node: ast.Call):
        """检查数据库调用是否通过repository"""
        if isinstance(node.func, ast.Attribute):
            func_name = getattr(node.func, 'attr', '')
            if func_name in ['execute', 'executemany', 'fetchone', 'fetchall']:
                self.violations.append(ArchitectureViolation(
                    violation_type=ViolationType.DIRECT_DATABASE_ACCESS,
                    source_file=self.file_path,
                    target_file=None,
                    line_number=node.lineno,
                    description="Database operations should go through repository pattern",
                    severity="error"
                ))


class ArchitectureAnalyzer:
    """架构分析器主类"""
    
    def __init__(self, project_root: str = "backend"):
        self.project_root = Path(project_root)
        self.dependency_graph = nx.DiGraph()
        self.violations: List[ArchitectureViolation] = []
        
    def get_layer_type(self, file_path: Path) -> Optional[LayerType]:
        """根据文件路径确定层级类型"""
        relative_path = file_path.relative_to(self.project_root)
        parts = relative_path.parts
        
        if not parts:
            return None
            
        first_part = parts[0]
        
        # 映射文件夹到层级类型
        layer_mapping = {
            'controller': LayerType.CONTROLLER,
            'service': LayerType.SERVICE,
            'model': LayerType.MODULE,
            'presentation': LayerType.PRESENTATION,
            'business': LayerType.BUSINESS,
            'foundation': LayerType.FOUNDATION,
            'ml': LayerType.ML
        }
        
        return layer_mapping.get(first_part)
    
    def analyze_file(self, file_path: Path) -> List[ArchitectureViolation]:
        """分析单个文件"""
        if not file_path.suffix == '.py':
            return []
            
        violations = []
        layer_type = self.get_layer_type(file_path)
        
        if not layer_type:
            return violations
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            # 分析导入依赖
            import_analyzer = ImportAnalyzer(str(file_path))
            import_analyzer.visit(tree)
            
            # 检查依赖关系
            for import_module, line_no in import_analyzer.imports:
                target_layer = self._get_import_layer(import_module)
                if target_layer and not LayerDependencyRules.is_dependency_allowed(layer_type, target_layer):
                    violations.append(ArchitectureViolation(
                        violation_type=ViolationType.CROSS_LAYER_CALL,
                        source_file=str(file_path),
                        target_file=import_module,
                        line_number=line_no,
                        description=f"Invalid dependency: {layer_type.value} -> {target_layer.value}",
                        severity="error"
                    ))
            
            # 分析代码模式
            pattern_analyzer = CodePatternAnalyzer(str(file_path), layer_type)
            pattern_analyzer.visit(tree)
            violations.extend(pattern_analyzer.violations)
            
            # 添加到依赖图
            self._add_to_dependency_graph(file_path, import_analyzer.imports)
            
        except Exception as e:
            violations.append(ArchitectureViolation(
                violation_type=ViolationType.WRONG_LAYER_CONTENT,
                source_file=str(file_path),
                target_file=None,
                line_number=0,
                description=f"Failed to analyze file: {str(e)}",
                severity="warning"
            ))
        
        return violations
    
    def _get_import_layer(self, import_module: str) -> Optional[LayerType]:
        """根据导入模块名确定目标层级"""
        if import_module.startswith('backend.'):
            parts = import_module.split('.')
            if len(parts) >= 2:
                folder = parts[1]
                layer_mapping = {
                    'controller': LayerType.CONTROLLER,
                    'service': LayerType.SERVICE,
                    'model': LayerType.MODULE,
                    'presentation': LayerType.PRESENTATION,
                    'business': LayerType.BUSINESS,
                    'foundation': LayerType.FOUNDATION,
                    'ml': LayerType.ML
                }
                return layer_mapping.get(folder)
        return None
    
    def _add_to_dependency_graph(self, file_path: Path, imports: List[Tuple[str, int]]):
        """添加文件依赖到依赖图"""
        source_node = str(file_path)
        self.dependency_graph.add_node(source_node)
        
        for import_module, _ in imports:
            if import_module.startswith('backend.'):
                self.dependency_graph.add_edge(source_node, import_module)
    
    def check_circular_dependencies(self) -> List[ArchitectureViolation]:
        """检查循环依赖"""
        violations = []
        
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            for cycle in cycles:
                cycle_str = " -> ".join(cycle) + f" -> {cycle[0]}"
                violations.append(ArchitectureViolation(
                    violation_type=ViolationType.CIRCULAR_DEPENDENCY,
                    source_file=cycle[0],
                    target_file=cycle[-1],
                    line_number=0,
                    description=f"Circular dependency detected: {cycle_str}",
                    severity="error"
                ))
        except Exception as e:
            violations.append(ArchitectureViolation(
                violation_type=ViolationType.CIRCULAR_DEPENDENCY,
                source_file="unknown",
                target_file=None,
                line_number=0,
                description=f"Failed to check circular dependencies: {str(e)}",
                severity="warning"
            ))
        
        return violations
    
    def analyze_project(self) -> List[ArchitectureViolation]:
        """分析整个项目"""
        all_violations = []
        
        # 分析所有Python文件
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                violations = self.analyze_file(py_file)
                all_violations.extend(violations)
        
        # 检查循环依赖
        circular_violations = self.check_circular_dependencies()
        all_violations.extend(circular_violations)
        
        self.violations = all_violations
        return all_violations
    
    def generate_report(self) -> str:
        """生成分析报告"""
        if not self.violations:
            return "✅ No architecture violations found!"
        
        report = ["🔍 Architecture Analysis Report", "=" * 40, ""]
        
        # 按严重程度分组
        errors = [v for v in self.violations if v.severity == "error"]
        warnings = [v for v in self.violations if v.severity == "warning"]
        
        if errors:
            report.append(f"❌ ERRORS ({len(errors)}):")
            for error in errors:
                report.append(f"  {error}")
            report.append("")
        
        if warnings:
            report.append(f"⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                report.append(f"  {warning}")
            report.append("")
        
        # 统计信息
        violation_counts = {}
        for violation in self.violations:
            vtype = violation.violation_type.value
            violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
        
        report.append("📊 Violation Summary:")
        for vtype, count in violation_counts.items():
            report.append(f"  {vtype}: {count}")
        
        return "\n".join(report)


def main():
    """主函数 - 命令行工具"""
    analyzer = ArchitectureAnalyzer()
    violations = analyzer.analyze_project()
    
    print(analyzer.generate_report())
    
    # 返回错误码
    error_count = len([v for v in violations if v.severity == "error"])
    return min(error_count, 1)  # 0 = success, 1 = has errors


if __name__ == "__main__":
    sys.exit(main())