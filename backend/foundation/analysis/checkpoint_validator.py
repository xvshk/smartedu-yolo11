"""
架构检查点验证器
基础层 - 验证架构重构进度和层间约束
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

from .compliance_checker import ComplianceChecker, ComplianceLevel


@dataclass
class CheckpointResult:
    """检查点结果"""
    checkpoint_name: str
    passed: bool
    score: float
    violations: int
    critical_issues: List[str]
    recommendations: List[str]
    details: Dict[str, Any]


class CheckpointValidator:
    """架构检查点验证器"""
    
    def __init__(self, project_root: str = "backend"):
        self.project_root = project_root
        self.compliance_checker = ComplianceChecker(project_root)
        
    def validate_layer_constraints(self) -> CheckpointResult:
        """验证所有层间约束"""
        print("🔍 Validating layer constraints...")
        
        # 运行完整合规性分析
        report = self.compliance_checker.run_full_analysis()
        
        # 分析违规类型
        violation_analysis = self._analyze_violations(report.violations)
        
        # 确定是否通过检查点
        passed = (
            report.metrics.compliance_score >= 60.0 and  # 至少达到POOR级别
            violation_analysis['cross_layer_calls'] <= 10 and  # 跨层调用违规不超过10个
            violation_analysis['direct_db_access'] <= 20  # 直接数据库访问不超过20个
        )
        
        # 识别关键问题
        critical_issues = []
        if report.metrics.compliance_level == ComplianceLevel.CRITICAL:
            critical_issues.append("Overall compliance is CRITICAL - requires immediate attention")
        
        if violation_analysis['cross_layer_calls'] > 15:
            critical_issues.append(f"Too many cross-layer violations ({violation_analysis['cross_layer_calls']})")
        
        if violation_analysis['direct_db_access'] > 30:
            critical_issues.append(f"Too many direct database access violations ({violation_analysis['direct_db_access']})")
        
        # 生成建议
        recommendations = report.recommendations.copy()
        if not passed:
            recommendations.insert(0, "Focus on fixing cross-layer dependency violations first")
            recommendations.insert(1, "Implement service layer interfaces to reduce coupling")
        
        return CheckpointResult(
            checkpoint_name="Layer Constraints Validation",
            passed=passed,
            score=report.metrics.compliance_score,
            violations=report.metrics.total_violations,
            critical_issues=critical_issues,
            recommendations=recommendations,
            details={
                'compliance_level': report.metrics.compliance_level.value,
                'violation_breakdown': violation_analysis,
                'files_analyzed': report.metrics.analyzed_files,
                'timestamp': report.timestamp
            }
        )
    
    def validate_presentation_business_separation(self) -> CheckpointResult:
        """验证表现层和业务层分离"""
        print("🔍 Validating presentation-business layer separation...")
        
        # 运行合规性分析
        report = self.compliance_checker.run_full_analysis()
        
        # 检查presentation层是否直接调用business层
        presentation_business_violations = []
        for violation in report.violations:
            if (violation.source_file.startswith("backend\\presentation") and 
                "backend.business" in str(violation.target_file)):
                presentation_business_violations.append(violation)
        
        # 检查presentation层是否直接调用module层
        presentation_module_violations = []
        for violation in report.violations:
            if (violation.source_file.startswith("backend\\presentation") and 
                "backend.model" in str(violation.target_file)):
                presentation_module_violations.append(violation)
        
        total_separation_violations = len(presentation_business_violations) + len(presentation_module_violations)
        
        # 通过条件：presentation层不直接调用business或module层
        passed = total_separation_violations == 0
        
        critical_issues = []
        if presentation_business_violations:
            critical_issues.append(f"Presentation layer directly calls business layer ({len(presentation_business_violations)} violations)")
        if presentation_module_violations:
            critical_issues.append(f"Presentation layer directly calls model layer ({len(presentation_module_violations)} violations)")
        
        recommendations = []
        if not passed:
            recommendations.append("Route presentation layer calls through service layer")
            recommendations.append("Remove direct business logic imports from presentation files")
        else:
            recommendations.append("Presentation-business separation is maintained!")
        
        return CheckpointResult(
            checkpoint_name="Presentation-Business Separation",
            passed=passed,
            score=100.0 if passed else max(0, 100 - total_separation_violations * 10),
            violations=total_separation_violations,
            critical_issues=critical_issues,
            recommendations=recommendations,
            details={
                'presentation_business_violations': len(presentation_business_violations),
                'presentation_module_violations': len(presentation_module_violations),
                'total_violations': total_separation_violations
            }
        )
    
    def validate_service_layer_completeness(self) -> CheckpointResult:
        """验证服务层完整性"""
        print("🔍 Validating service layer completeness...")
        
        service_files = list(Path(self.project_root).glob("service/*.py"))
        service_files = [f for f in service_files if f.name != "__init__.py"]
        
        # 检查关键服务是否存在
        expected_services = [
            "DetectionService.py",
            "AuthService.py",
            "AlertService.py"
        ]
        
        missing_services = []
        for service in expected_services:
            service_path = Path(self.project_root) / "service" / service
            if not service_path.exists():
                missing_services.append(service)
        
        # 检查服务接口是否存在
        interfaces_file = Path(self.project_root) / "service" / "InterfaceService.py"
        has_interfaces = interfaces_file.exists()
        
        # 检查依赖注入容器是否存在
        container_file = Path(self.project_root) / "service" / "ContainerService.py"
        has_container = container_file.exists()
        
        passed = (
            len(missing_services) == 0 and
            has_interfaces and
            has_container and
            len(service_files) >= 3
        )
        
        critical_issues = []
        if missing_services:
            critical_issues.append(f"Missing critical services: {', '.join(missing_services)}")
        if not has_interfaces:
            critical_issues.append("Service interfaces not implemented")
        if not has_container:
            critical_issues.append("Dependency injection container not implemented")
        
        recommendations = []
        if missing_services:
            recommendations.append(f"Implement missing services: {', '.join(missing_services)}")
        if not has_interfaces:
            recommendations.append("Create service interfaces for better abstraction")
        if not has_container:
            recommendations.append("Implement dependency injection container")
        if passed:
            recommendations.append("Service layer structure is complete!")
        
        return CheckpointResult(
            checkpoint_name="Service Layer Completeness",
            passed=passed,
            score=100.0 if passed else max(0, 100 - len(missing_services) * 20 - (0 if has_interfaces else 20) - (0 if has_container else 20)),
            violations=len(missing_services) + (0 if has_interfaces else 1) + (0 if has_container else 1),
            critical_issues=critical_issues,
            recommendations=recommendations,
            details={
                'service_files_count': len(service_files),
                'missing_services': missing_services,
                'has_interfaces': has_interfaces,
                'has_container': has_container,
                'expected_services': expected_services
            }
        )
    
    def run_checkpoint_10(self) -> Dict[str, CheckpointResult]:
        """运行检查点10：验证所有层间约束"""
        print("\n" + "="*60)
        print("🏗️  CHECKPOINT 10: LAYER CONSTRAINTS VALIDATION")
        print("="*60)
        
        results = {}
        
        # 验证层间约束
        results['layer_constraints'] = self.validate_layer_constraints()
        
        # 验证表现层和业务层分离
        results['presentation_business_separation'] = self.validate_presentation_business_separation()
        
        # 验证服务层完整性
        results['service_layer_completeness'] = self.validate_service_layer_completeness()
        
        # 总体评估
        all_passed = all(result.passed for result in results.values())
        overall_score = sum(result.score for result in results.values()) / len(results)
        
        print(f"\n📊 CHECKPOINT 10 SUMMARY:")
        print(f"Overall Status: {'✅ PASSED' if all_passed else '❌ FAILED'}")
        print(f"Overall Score: {overall_score:.1f}%")
        print(f"Tests Passed: {sum(1 for r in results.values() if r.passed)}/{len(results)}")
        
        for name, result in results.items():
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {name}: {status} ({result.score:.1f}%)")
        
        if not all_passed:
            print(f"\n🚨 CRITICAL ISSUES:")
            for result in results.values():
                for issue in result.critical_issues:
                    print(f"  - {issue}")
        
        print(f"\n💡 NEXT STEPS:")
        if all_passed:
            print("  - Proceed to task 11: Interface layer communication verification")
            print("  - Continue with architecture documentation")
        else:
            print("  - Address critical issues before proceeding")
            print("  - Focus on highest impact violations first")
            for result in results.values():
                if not result.passed and result.recommendations:
                    print(f"  - {result.recommendations[0]}")
        
        return results
    
    def _analyze_violations(self, violations: List) -> Dict[str, int]:
        """分析违规类型统计"""
        analysis = {
            'cross_layer_calls': 0,
            'direct_db_access': 0,
            'business_logic_in_controller': 0,
            'circular_dependencies': 0,
            'other': 0
        }
        
        for violation in violations:
            vtype = str(violation.violation_type)
            if 'CROSS_LAYER_CALL' in vtype:
                analysis['cross_layer_calls'] += 1
            elif 'DIRECT_DATABASE_ACCESS' in vtype:
                analysis['direct_db_access'] += 1
            elif 'BUSINESS_LOGIC_IN_CONTROLLER' in vtype:
                analysis['business_logic_in_controller'] += 1
            elif 'CIRCULAR_DEPENDENCY' in vtype:
                analysis['circular_dependencies'] += 1
            else:
                analysis['other'] += 1
        
        return analysis
    
    def save_checkpoint_report(self, results: Dict[str, CheckpointResult], 
                              output_file: str = "checkpoint_10_report.json"):
        """保存检查点报告"""
        report_data = {
            'checkpoint': 'Checkpoint 10 - Layer Constraints Validation',
            'timestamp': self.compliance_checker.run_full_analysis().timestamp,
            'overall_passed': all(result.passed for result in results.values()),
            'overall_score': sum(result.score for result in results.values()) / len(results),
            'results': {
                name: {
                    'checkpoint_name': result.checkpoint_name,
                    'passed': result.passed,
                    'score': result.score,
                    'violations': result.violations,
                    'critical_issues': result.critical_issues,
                    'recommendations': result.recommendations,
                    'details': result.details
                }
                for name, result in results.items()
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Checkpoint report saved to: {output_file}")
        return output_file


def main():
    """主函数"""
    validator = CheckpointValidator()
    results = validator.run_checkpoint_10()
    validator.save_checkpoint_report(results)
    
    # 返回错误码
    all_passed = all(result.passed for result in results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())