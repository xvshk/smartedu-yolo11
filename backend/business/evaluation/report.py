"""
报告生成模块
Report generation model for model evaluation.
"""
from typing import List, Dict, Optional
from pathlib import Path
import json
import numpy as np

from .models import EvaluationResult, ClassMetrics


class ReportGenerator:
    """
    评估报告生成器
    Generator for evaluation reports and visualizations.
    """
    
    def __init__(self, output_dir: str, dpi: int = 150):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
            dpi: 图像 DPI
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
    
    def generate_json_report(
        self,
        result: EvaluationResult,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成 JSON 格式报告
        
        Args:
            result: 评估结果
            output_path: 输出路径，默认为 output_dir/evaluation_report.json
            
        Returns:
            生成的报告文件路径
        """
        if output_path is None:
            output_path = self.output_dir / 'evaluation_report.json'
        else:
            output_path = Path(output_path)
        
        report_data = result.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def generate_markdown_report(
        self,
        result: EvaluationResult,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成 Markdown 格式报告
        
        Args:
            result: 评估结果
            output_path: 输出路径，默认为 output_dir/evaluation_report.md
            
        Returns:
            生成的报告文件路径
        """
        if output_path is None:
            output_path = self.output_dir / 'evaluation_report.md'
        else:
            output_path = Path(output_path)
        
        lines = []
        
        # 标题
        lines.append("# 模型评估报告")
        lines.append("")
        
        # 元数据
        lines.append("## 评估信息")
        lines.append("")
        lines.append(f"- **模型权重**: {result.weights_path}")
        lines.append(f"- **数据集配置**: {result.data_yaml}")
        lines.append(f"- **评估分割**: {result.split}")
        lines.append(f"- **评估时间**: {result.evaluation_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **置信度阈值**: {result.conf_threshold}")
        lines.append(f"- **IoU 阈值**: {result.iou_threshold}")
        lines.append("")
        
        # 整体指标
        lines.append("## 整体指标")
        lines.append("")
        om = result.overall_metrics
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| mAP@50 | {om.mAP50:.4f} |")
        lines.append(f"| mAP@50-95 | {om.mAP50_95:.4f} |")
        lines.append(f"| Precision | {om.precision:.4f} |")
        lines.append(f"| Recall | {om.recall:.4f} |")
        lines.append(f"| F1 Score | {om.f1_score:.4f} |")
        lines.append(f"| 图像数量 | {om.total_images} |")
        lines.append(f"| 预测数量 | {om.total_predictions} |")
        lines.append(f"| 真实标签数量 | {om.total_ground_truths} |")
        lines.append("")
        
        # 行为组指标
        lines.append("## 行为组指标")
        lines.append("")
        gm = result.group_metrics
        
        lines.append("### 正常行为 (举手、阅读、书写)")
        lines.append("")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| Precision | {gm.normal_precision:.4f} |")
        lines.append(f"| Recall | {gm.normal_recall:.4f} |")
        lines.append(f"| F1 Score | {gm.normal_f1:.4f} |")
        lines.append(f"| mAP@50 | {gm.normal_mAP50:.4f} |")
        lines.append("")
        
        lines.append("### 预警行为 (睡觉、站立、使用电子设备、交谈)")
        lines.append("")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| Precision | {gm.warning_precision:.4f} |")
        lines.append(f"| Recall | {gm.warning_recall:.4f} |")
        lines.append(f"| F1 Score | {gm.warning_f1:.4f} |")
        lines.append(f"| mAP@50 | {gm.warning_mAP50:.4f} |")
        lines.append("")
        
        if gm.warning_recall_critical:
            lines.append("> ⚠️ **警告**: 预警行为召回率低于 0.5，模型可能无法有效检测预警行为！")
            lines.append("")
        
        # 每类别指标
        lines.append("## 每类别指标")
        lines.append("")
        lines.append("| 类别 | Precision | Recall | F1 | AP@50 | AP@50-95 | 样本数 |")
        lines.append("|------|-----------|--------|-----|-------|----------|--------|")
        
        for class_id in sorted(result.per_class_metrics.keys()):
            cm = result.per_class_metrics[class_id]
            cn_name = result.class_names_cn[class_id] if class_id < len(result.class_names_cn) else cm.class_name
            lines.append(
                f"| {cn_name} | {cm.precision:.4f} | {cm.recall:.4f} | "
                f"{cm.f1_score:.4f} | {cm.ap50:.4f} | {cm.ap50_95:.4f} | {cm.support} |"
            )
        lines.append("")
        
        # 混淆分析
        lines.append("## 混淆分析")
        lines.append("")
        lines.append("### 最容易混淆的类别对")
        lines.append("")
        
        if result.confused_pairs:
            for i, pair in enumerate(result.confused_pairs, 1):
                lines.append(f"**{i}. {pair.class_a_name} → {pair.class_b_name}**")
                lines.append(f"- 混淆率: {pair.confusion_rate:.2%}")
                lines.append(f"- 建议: {pair.recommendation}")
                lines.append("")
        else:
            lines.append("没有发现明显的类别混淆。")
            lines.append("")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return str(output_path)
    
    def generate_confusion_heatmap(
        self,
        confusion_matrix,
        class_names: List[str],
        output_path: Optional[str] = None
    ) -> str:
        """
        生成混淆矩阵热力图
        
        Args:
            confusion_matrix: 混淆矩阵
            class_names: 类别名称列表
            output_path: 输出路径
            
        Returns:
            生成的图像文件路径
        """
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        
        if output_path is None:
            output_path = self.output_dir / 'confusion_matrix.png'
        else:
            output_path = Path(output_path)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 绘制热力图
        im = ax.imshow(confusion_matrix, cmap='Blues')
        
        # 添加颜色条
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('比例', rotation=-90, va="bottom")
        
        # 设置刻度
        ax.set_xticks(np.arange(len(class_names)))
        ax.set_yticks(np.arange(len(class_names)))
        ax.set_xticklabels(class_names)
        ax.set_yticklabels(class_names)
        
        # 旋转 x 轴标签
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # 添加数值标注
        for i in range(len(class_names)):
            for j in range(len(class_names)):
                value = confusion_matrix[i, j]
                text_color = "white" if value > 0.5 else "black"
                ax.text(j, i, f'{value:.2f}', ha="center", va="center", color=text_color)
        
        ax.set_xlabel('预测类别')
        ax.set_ylabel('真实类别')
        ax.set_title('混淆矩阵 (归一化)')
        
        fig.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def generate_pr_curves(
        self,
        per_class_metrics: Dict[int, ClassMetrics],
        class_names: List[str],
        output_path: Optional[str] = None
    ) -> str:
        """
        生成 PR 曲线图（基于 AP 值的简化版本）
        
        Args:
            per_class_metrics: 每类别指标
            class_names: 类别名称列表
            output_path: 输出路径
            
        Returns:
            生成的图像文件路径
        """
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        
        if output_path is None:
            output_path = self.output_dir / 'pr_curves.png'
        else:
            output_path = Path(output_path)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(class_names)))
        
        for class_id, metrics in per_class_metrics.items():
            if class_id < len(class_names):
                name = class_names[class_id]
                # 简化的 PR 曲线：使用单点表示
                ax.scatter(
                    metrics.recall, metrics.precision,
                    color=colors[class_id], s=100, marker='o',
                    label=f'{name} (AP={metrics.ap50:.2f})'
                )
        
        ax.set_xlim([0, 1.05])
        ax.set_ylim([0, 1.05])
        ax.set_xlabel('Recall (召回率)')
        ax.set_ylabel('Precision (精确率)')
        ax.set_title('各类别 Precision-Recall')
        ax.legend(loc='lower left')
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def generate_metrics_bar_chart(
        self,
        per_class_metrics: Dict[int, ClassMetrics],
        class_names: List[str],
        output_path: Optional[str] = None
    ) -> str:
        """
        生成指标对比柱状图
        
        Args:
            per_class_metrics: 每类别指标
            class_names: 类别名称列表
            output_path: 输出路径
            
        Returns:
            生成的图像文件路径
        """
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        
        if output_path is None:
            output_path = self.output_dir / 'metrics_comparison.png'
        else:
            output_path = Path(output_path)
        
        # 准备数据
        classes = []
        precisions = []
        recalls = []
        f1_scores = []
        
        for class_id in sorted(per_class_metrics.keys()):
            metrics = per_class_metrics[class_id]
            if class_id < len(class_names):
                classes.append(class_names[class_id])
            else:
                classes.append(metrics.class_name)
            precisions.append(metrics.precision)
            recalls.append(metrics.recall)
            f1_scores.append(metrics.f1_score)
        
        x = np.arange(len(classes))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars1 = ax.bar(x - width, precisions, width, label='Precision', color='#2196F3')
        bars2 = ax.bar(x, recalls, width, label='Recall', color='#4CAF50')
        bars3 = ax.bar(x + width, f1_scores, width, label='F1 Score', color='#FF9800')
        
        ax.set_xlabel('行为类别')
        ax.set_ylabel('指标值')
        ax.set_title('各类别指标对比')
        ax.set_xticks(x)
        ax.set_xticklabels(classes, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim([0, 1.1])
        ax.grid(True, axis='y', alpha=0.3)
        
        # 添加数值标注
        def add_labels(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)
        
        add_labels(bars1)
        add_labels(bars2)
        add_labels(bars3)
        
        fig.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
