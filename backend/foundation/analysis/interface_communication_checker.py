"""
接口层间通信验证器
基础层 - 验证层间调用是否通过接口进行
"""
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass

from .architecture_analyzer import LayerType, ArchitectureViolation, ViolationType


@dataclass
class InterfaceViolation:
    """接口通信违规"""
    source_file: str
    target_class: str
    line_number: int
    violation_type: str  # "direct_implementation", "missing_interface"
    description: str
    severity: str = "warning"


class InterfaceCommunicationChecker:
    """接口层间通信检查器"""
    
    # 定义接口模式
    INTERFACE_PATTERNS = {
        'service_interfaces': r'I[A-Z]\w*Service',  # IDetectionService, IAuthService
        'repository_interfaces': r'I[A-Z]\w*Repository',  # IDetectionRepository
        'general_interfaces': r'I[A-Z]\w*'  # 通用接口模式
    }
    
    # 实现类模式
    IMPLEMENTATION_PATTERNS = {
        'service_implementations': r'[A-Z]\w*Service',  # DetectionService
        'repository_implementations': r'[A-Z]\w*Repository'  # DetectionRepository
    }
    
    def __init__(self, project_root: str = "backend"):
        self.project_root = Path(project_root)
        self.violations: List[InterfaceViolation] = []
        self.interfaces: Dict[str, Set[str]] = {}  # 层 -> 接口集合
        self.implementations: Dict[str, Set[str]] = {}  # 层 -> 实现类集合
        
    def _get_layer_from_path(self, file_path: Path) -> Optional[str]:
        """从文件路径确定所属层"""
        relative_path = file_path.relative_to(self.project_root)
        parts = relative_path.parts
        
        if len(parts) == 0:
            return None
            
        return parts[0]  # 返回第一级目录名
    
    def _extract_class_definitions(self, file_path: Path) -> List[Tuple[str, int]]:
        """提取文件中的类定义"""
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append((node.name, node.lineno))
                    
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            
        return classes
    
    def _extract_imports_and_usage(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """提取导入和类使用情况"""
        usage = []  # (imported_name, used_class, line_number)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 收集导入的类名
            imported_classes = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_classes.add(alias.name.split('.')[-1])
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imported_classes.add(alias.name)
            
            # 查找类的实例化和调用
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        class_name = node.func.id
                        if class_name in imported_classes:
                            usage.append(("direct", class_name, node.lineno))
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            class_name = node.func.value.id
                            if class_name in imported_classes:
                                usage.append(("method", class_name, node.lineno))
                                
        except Exception as e:
            print(f"Warning: Failed to analyze usage in {file_path}: {e}")
            
        return usage
    
    def _is_interface(self, class_name: str) -> bool:
        """判断是否为接口"""
        for pattern in self.INTERFACE_PATTERNS.values():
            if re.match(pattern, class_name):
                return True
        return False
    
    def _is_implementation(self, class_name: str) -> bool:
        """判断是否为实现类"""
        for pattern in self.IMPLEMENTATION_PATTERNS.values():
            if re.match(pattern, class_name):
                return True
        return False
    
    def _find_corresponding_interface(self, implementation_name: str) -> Optional[str]:
        """查找实现类对应的接口"""
        # 简单的命名约定：DetectionService -> IDetectionService
        if implementation_name.endswith('Service'):
            return f"I{implementation_name}"
        elif implementation_name.endswith('Repository'):
            return f"I{implementation_name}"
        return None
    
    def scan_interfaces_and_implementations(self):
        """扫描所有接口和实现类"""
        self.interfaces = {}
        self.implementations = {}
        
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            layer = self._get_layer_from_path(py_file)
            if layer is None:
                continue
                
            if layer not in self.interfaces:
                self.interfaces[layer] = set()
            if layer not in self.implementations:
                self.implementations[layer] = set()
                
            classes = self._extract_class_definitions(py_file)
            
            for class_name, _ in classes:
                if self._is_interface(class_name):
                    self.interfaces[layer].add(class_name)
                elif self._is_implementation(class_name):
                    self.implementations[layer].add(class_name)
    
    def check_interface_usage(self) -> List[InterfaceViolation]:
        """检查接口使用情况"""
        self.violations = []
        self.scan_interfaces_and_implementations()
        
        # 检查每个文件的类使用情况
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            source_layer = self._get_layer_from_path(py_file)
            if source_layer is None:
                continue
                
            usage = self._extract_imports_and_usage(py_file)
            
            for usage_type, class_name, line_no in usage:
                # 检查是否直接使用了实现类而不是接口
                if self._is_implementation(class_name):
                    # 查找对应的接口
                    interface_name = self._find_corresponding_interface(class_name)
                    
                    if interface_name:
                        # 检查是否有对应的接口定义
                        interface_exists = any(
                            interface_name in interfaces 
                            for interfaces in self.interfaces.values()
                        )
                        
                        if interface_exists:
                            violation = InterfaceViolation(
                                source_file=str(py_file),
                                target_class=class_name,
                                line_number=line_no,
                                violation_type="direct_implementation",
                                description=f"Direct use of implementation {class_name} instead of interface {interface_name}",
                                severity="warning"
                            )
                            self.violations.append(violation)
                        else:
                            violation = InterfaceViolation(
                                source_file=str(py_file),
                                target_class=class_name,
                                line_number=line_no,
                                violation_type="missing_interface",
                                description=f"Implementation {class_name} used without corresponding interface {interface_name}",
                                severity="error"
                            )
                            self.violations.append(violation)
        
        return self.violations
    
    def get_interface_coverage_report(self) -> Dict[str, Any]:
        """获取接口覆盖率报告"""
        report = {
            'by_layer': {},
            'summary': {
                'total_interfaces': 0,
                'total_implementations': 0,
                'coverage_ratio': 0.0
            }
        }
        
        total_interfaces = 0
        total_implementations = 0
        
        for layer in set(list(self.interfaces.keys()) + list(self.implementations.keys())):
            interfaces = self.interfaces.get(layer, set())
            implementations = self.implementations.get(layer, set())
            
            # 计算覆盖率
            covered_implementations = 0
            for impl in implementations:
                interface_name = self._find_corresponding_interface(impl)
                if interface_name and interface_name in interfaces:
                    covered_implementations += 1
            
            coverage = (covered_implementations / len(implementations) * 100) if implementations else 100
            
            report['by_layer'][layer] = {
                'interfaces': list(interfaces),
                'implementations': list(implementations),
                'interface_count': len(interfaces),
                'implementation_count': len(implementations),
                'covered_implementations': covered_implementations,
                'coverage_percentage': coverage
            }
            
            total_interfaces += len(interfaces)
            total_implementations += len(implementations)
        
        report['summary']['total_interfaces'] = total_interfaces
        report['summary']['total_implementations'] = total_implementations
        report['summary']['coverage_ratio'] = (
            total_interfaces / total_implementations * 100 
            if total_implementations > 0 else 100
        )
        
        return report
    
    def generate_interface_report(self) -> str:
        """生成接口通信报告"""
        report = ["🔌 Interface Communication Analysis Report", "=" * 50, ""]
        
        # 违规统计
        violation_types = {}
        for violation in self.violations:
            vtype = violation.violation_type
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        report.append("📊 Interface Violation Summary:")
        if violation_types:
            for vtype, count in violation_types.items():
                report.append(f"  {vtype}: {count}")
        else:
            report.append("  ✅ No interface communication violations found!")
        report.append("")
        
        # 接口覆盖率
        coverage_report = self.get_interface_coverage_report()
        report.append("📈 Interface Coverage by Layer:")
        
        for layer, info in coverage_report['by_layer'].items():
            report.append(f"  {layer}:")
            report.append(f"    Interfaces: {info['interface_count']}")
            report.append(f"    Implementations: {info['implementation_count']}")
            report.append(f"    Coverage: {info['coverage_percentage']:.1f}%")
            
            if info['interfaces']:
                report.append(f"    Interface List: {', '.join(info['interfaces'])}")
            if info['implementations']:
                report.append(f"    Implementation List: {', '.join(info['implementations'])}")
            report.append("")
        
        overall_coverage = coverage_report['summary']['coverage_ratio']
        report.append(f"Overall Interface Coverage: {overall_coverage:.1f}%")
        report.append("")
        
        # 详细违规列表
        if self.violations:
            report.append("🚨 Interface Communication Violations:")
            for i, violation in enumerate(self.violations[:10], 1):  # 只显示前10个
                report.append(f"  {i}. {violation.description}")
                report.append(f"     File: {violation.source_file}:{violation.line_number}")
                report.append(f"     Severity: {violation.severity}")
                report.append("")
            
            if len(self.violations) > 10:
                report.append(f"  ... and {len(self.violations) - 10} more violations")
                report.append("")
        
        # 建议
        report.append("💡 Recommendations:")
        if violation_types.get("direct_implementation", 0) > 0:
            report.append("  - Replace direct implementation usage with interface dependencies")
        if violation_types.get("missing_interface", 0) > 0:
            report.append("  - Create missing interfaces for implementation classes")
        if overall_coverage < 80:
            report.append("  - Improve interface coverage to at least 80%")
        if not violation_types:
            report.append("  - Interface communication patterns are well-implemented!")
        
        return "\n".join(report)
    
    def convert_to_architecture_violations(self) -> List[ArchitectureViolation]:
        """转换为架构违规格式"""
        arch_violations = []
        
        for violation in self.violations:
            severity = "error" if violation.violation_type == "missing_interface" else "warning"
            
            arch_violation = ArchitectureViolation(
                violation_type=ViolationType.CROSS_LAYER_CALL,  # 使用现有类型
                source_file=violation.source_file,
                target_file=violation.target_class,
                line_number=violation.line_number,
                description=f"Interface violation: {violation.description}",
                severity=severity
            )
            arch_violations.append(arch_violation)
        
        return arch_violations


def main():
    """主函数"""
    checker = InterfaceCommunicationChecker()
    
    print("Checking interface communication patterns...")
    violations = checker.check_interface_usage()
    
    print(checker.generate_interface_report())
    
    return len([v for v in violations if v.severity == "error"])


if __name__ == "__main__":
    import sys
    sys.exit(main())