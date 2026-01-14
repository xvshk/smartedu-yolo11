"""
架构合规性检查框架
基础层 - 统一的架构规则检查和报告系统
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .architecture_analyzer import ArchitectureAnalyzer, ArchitectureViolation, ViolationType
from .dependency_analyzer import DependencyAnalyzer
from .layer_dependency_checker import LayerDependencyChecker


class ComplianceLevel(Enum):
    """合规级别"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 80-89%
    FAIR = "fair"           # 70-79%
    POOR = "poor"           # 60-69%
    CRITICAL = "critical"   # <60%


@dataclass
class ComplianceMetrics:
    """合规性指标"""
    total_files: int
    analyzed_files: int
    total_violations: int
    error_count: int
    warning_count: int
    compliance_score: float
    compliance_level: ComplianceLevel
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceReport:
    """合规性报告"""
    timestamp: str
    project_root: str
    metrics: ComplianceMetrics
    violations: List[ArchitectureViolation]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'project_root': self.project_root,
            'metrics': self.metrics.to_dict(),
            'violations': [asdict(v) for v in self.violations],
            'recommendations': self.recommendations
        }


class ComplianceChecker:
    """架构合规性检查器"""
    
    def __init__(self, project_root: str = "backend"):
        self.project_root = Path(project_root)
        self.architecture_analyzer = ArchitectureAnalyzer(project_root)
        self.dependency_analyzer = DependencyAnalyzer(project_root)
        self.layer_dependency_checker = LayerDependencyChecker(project_root)
        
    def run_full_analysis(self) -> ComplianceReport:
        """运行完整的合规性分析"""
        print("🔍 Starting architecture compliance analysis...")
        
        # 架构分析
        print("  Analyzing architecture violations...")
        arch_violations = self.architecture_analyzer.analyze_project()
        
        # 依赖分析
        print("  Analyzing dependencies...")
        self.dependency_analyzer.analyze_dependencies()
        
        # 层间依赖检查
        print("  Checking layer dependencies...")
        layer_violations = self.layer_dependency_checker.check_layer_dependencies()
        layer_arch_violations = self.layer_dependency_checker.convert_to_architecture_violations()
        
        # 合并所有违规
        all_violations = arch_violations + layer_arch_violations
        
        # 计算指标
        metrics = self._calculate_metrics(all_violations)
        
        # 生成建议
        recommendations = self._generate_recommendations(all_violations, metrics)
        
        # 创建报告
        report = ComplianceReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            metrics=metrics,
            violations=all_violations,
            recommendations=recommendations
        )
        
        print(f"✅ Analysis complete. Compliance score: {metrics.compliance_score:.1f}%")
        return report
    
    def _calculate_metrics(self, violations: List[ArchitectureViolation]) -> ComplianceMetrics:
        """计算合规性指标"""
        # 统计文件数量
        total_files = len(list(self.project_root.rglob("*.py")))
        analyzed_files = len([f for f in self.project_root.rglob("*.py") 
                            if "__pycache__" not in str(f)])
        
        # 统计违规
        error_count = len([v for v in violations if v.severity == "error"])
        warning_count = len([v for v in violations if v.severity == "warning"])
        total_violations = len(violations)
        
        # 计算合规分数
        # 基础分数100，每个错误扣10分，每个警告扣2分
        base_score = 100.0
        penalty = (error_count * 10) + (warning_count * 2)
        compliance_score = max(0.0, base_score - penalty)
        
        # 确定合规级别
        if compliance_score >= 90:
            level = ComplianceLevel.EXCELLENT
        elif compliance_score >= 80:
            level = ComplianceLevel.GOOD
        elif compliance_score >= 70:
            level = ComplianceLevel.FAIR
        elif compliance_score >= 60:
            level = ComplianceLevel.POOR
        else:
            level = ComplianceLevel.CRITICAL
        
        return ComplianceMetrics(
            total_files=total_files,
            analyzed_files=analyzed_files,
            total_violations=total_violations,
            error_count=error_count,
            warning_count=warning_count,
            compliance_score=compliance_score,
            compliance_level=level
        )
    
    def _generate_recommendations(self, violations: List[ArchitectureViolation], 
                                metrics: ComplianceMetrics) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于违规类型的建议
        violation_types = {}
        for violation in violations:
            vtype = violation.violation_type
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        if ViolationType.CROSS_LAYER_CALL in violation_types:
            count = violation_types[ViolationType.CROSS_LAYER_CALL]
            recommendations.append(
                f"Fix {count} cross-layer dependency violations by introducing proper service interfaces"
            )
        
        if ViolationType.BUSINESS_LOGIC_IN_CONTROLLER in violation_types:
            count = violation_types[ViolationType.BUSINESS_LOGIC_IN_CONTROLLER]
            recommendations.append(
                f"Move business logic from {count} controller functions to service layer"
            )
        
        if ViolationType.DIRECT_DATABASE_ACCESS in violation_types:
            count = violation_types[ViolationType.DIRECT_DATABASE_ACCESS]
            recommendations.append(
                f"Implement repository pattern for {count} direct database access violations"
            )
        
        if ViolationType.CIRCULAR_DEPENDENCY in violation_types:
            count = violation_types[ViolationType.CIRCULAR_DEPENDENCY]
            recommendations.append(
                f"Break {count} circular dependencies by introducing interfaces or reorganizing modules"
            )
        
        # 基于合规级别的建议
        if metrics.compliance_level == ComplianceLevel.CRITICAL:
            recommendations.append("URGENT: Architecture requires immediate refactoring")
            recommendations.append("Consider creating a detailed refactoring plan")
        elif metrics.compliance_level == ComplianceLevel.POOR:
            recommendations.append("Schedule architecture refactoring in next sprint")
        elif metrics.compliance_level == ComplianceLevel.FAIR:
            recommendations.append("Gradually improve architecture during feature development")
        
        # 通用建议
        if metrics.error_count > 0:
            recommendations.append("Prioritize fixing error-level violations first")
        
        if not recommendations:
            recommendations.append("Architecture is in good shape! Consider adding more detailed checks")
        
        return recommendations
    
    def generate_html_report(self, report: ComplianceReport, 
                           output_file: str = "compliance_report.html") -> str:
        """生成HTML格式的报告"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Architecture Compliance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }}
        .excellent {{ color: #28a745; }}
        .good {{ color: #17a2b8; }}
        .fair {{ color: #ffc107; }}
        .poor {{ color: #fd7e14; }}
        .critical {{ color: #dc3545; }}
        .violation {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }}
        .error {{ border-left-color: #dc3545; background: #f8d7da; }}
        .warning {{ border-left-color: #ffc107; background: #fff3cd; }}
        .recommendations {{ background: #d1ecf1; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏗️ Architecture Compliance Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Project:</strong> {project_root}</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <h3>📊 Overall Score</h3>
            <h2 class="{level_class}">{score:.1f}%</h2>
            <p>Level: <span class="{level_class}">{level}</span></p>
        </div>
        <div class="metric-card">
            <h3>📁 Files</h3>
            <p>Total: {total_files}</p>
            <p>Analyzed: {analyzed_files}</p>
        </div>
        <div class="metric-card">
            <h3>⚠️ Violations</h3>
            <p>Errors: <span class="critical">{errors}</span></p>
            <p>Warnings: <span class="poor">{warnings}</span></p>
        </div>
    </div>
    
    <h2>🔍 Violations</h2>
    <div class="violations">
        {violations_html}
    </div>
    
    <h2>💡 Recommendations</h2>
    <div class="recommendations">
        <ul>
            {recommendations_html}
        </ul>
    </div>
</body>
</html>"""
        
        # 生成违规HTML
        violations_html = ""
        for violation in report.violations:
            css_class = violation.severity
            violations_html += f"""
            <div class="violation {css_class}">
                <strong>{violation.violation_type.value}</strong><br>
                {violation.description}<br>
                <small>{violation.source_file}:{violation.line_number}</small>
            </div>
            """
        
        # 生成建议HTML
        recommendations_html = ""
        for rec in report.recommendations:
            recommendations_html += f"<li>{rec}</li>"
        
        # 填充模板
        html_content = html_template.format(
            timestamp=report.timestamp,
            project_root=report.project_root,
            score=report.metrics.compliance_score,
            level=report.metrics.compliance_level.value.title(),
            level_class=report.metrics.compliance_level.value,
            total_files=report.metrics.total_files,
            analyzed_files=report.metrics.analyzed_files,
            errors=report.metrics.error_count,
            warnings=report.metrics.warning_count,
            violations_html=violations_html,
            recommendations_html=recommendations_html
        )
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
    
    def save_report_json(self, report: ComplianceReport, 
                        output_file: str = "compliance_report.json") -> str:
        """保存JSON格式的报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        return output_file
    
    def print_summary(self, report: ComplianceReport):
        """打印报告摘要"""
        metrics = report.metrics
        
        print("\n" + "="*50)
        print("🏗️  ARCHITECTURE COMPLIANCE SUMMARY")
        print("="*50)
        
        # 合规分数
        level_emoji = {
            ComplianceLevel.EXCELLENT: "🟢",
            ComplianceLevel.GOOD: "🔵", 
            ComplianceLevel.FAIR: "🟡",
            ComplianceLevel.POOR: "🟠",
            ComplianceLevel.CRITICAL: "🔴"
        }
        
        emoji = level_emoji.get(metrics.compliance_level, "⚪")
        print(f"{emoji} Compliance Score: {metrics.compliance_score:.1f}% ({metrics.compliance_level.value.title()})")
        print(f"📁 Files Analyzed: {metrics.analyzed_files}/{metrics.total_files}")
        print(f"⚠️  Total Violations: {metrics.total_violations} ({metrics.error_count} errors, {metrics.warning_count} warnings)")
        
        if report.recommendations:
            print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(report.recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        print("="*50)


def main():
    """主函数 - 命令行工具"""
    checker = ComplianceChecker()
    
    # 运行分析
    report = checker.run_full_analysis()
    
    # 打印摘要
    checker.print_summary(report)
    
    # 保存报告
    json_file = checker.save_report_json(report)
    html_file = checker.generate_html_report(report)
    
    print(f"\n📄 Reports saved:")
    print(f"  JSON: {json_file}")
    print(f"  HTML: {html_file}")
    
    # 返回错误码
    return 1 if report.metrics.error_count > 0 else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())