# Implementation Plan: Model Evaluation

## Overview

本实现计划将模型评估功能分解为可执行的编码任务。实现将使用 Python，基于 Ultralytics YOLO 库进行模型推理，使用 matplotlib 和 seaborn 进行可视化。

## Tasks

- [x] 1. 创建评估模块基础结构
  - 创建 `src/evaluation/` 目录结构
  - 创建 `__init__.py` 和基础模块文件
  - 定义数据模型类 (Detection, ClassMetrics, OverallMetrics, GroupMetrics, EvaluationResult)
  - _Requirements: 2.3, 2.4, 7.1, 7.2_

- [x] 2. 实现 MetricsCalculator 核心功能
  - [x] 2.1 实现整体指标计算方法
    - 实现 `compute_overall_metrics()` 方法
    - 计算 mAP50, mAP50-95, precision, recall, F1 score
    - _Requirements: 2.3_
  
  - [ ]* 2.2 编写指标计算的属性测试
    - **Property 4: Metric Completeness**
    - **Validates: Requirements 2.3, 2.4**
  
  - [x] 2.3 实现每类别指标计算
    - 实现 `compute_per_class_metrics()` 方法
    - 为 7 个行为类别分别计算指标
    - _Requirements: 2.4_
  
  - [x] 2.4 实现行为组指标计算
    - 实现 `compute_group_metrics()` 方法
    - 分别计算正常行为和预警行为的指标
    - 实现预警行为召回率低于 0.5 的标记逻辑
    - _Requirements: 7.1, 7.2, 7.4_
  
  - [ ]* 2.5 编写行为组指标的属性测试
    - **Property 8: Behavior Group Metrics**
    - **Validates: Requirements 7.1, 7.2**

- [x] 3. 实现混淆矩阵功能
  - [x] 3.1 实现混淆矩阵生成
    - 实现 `generate_confusion_matrix()` 方法
    - 支持行归一化
    - _Requirements: 3.1, 3.2_
  
  - [ ]* 3.2 编写混淆矩阵的属性测试
    - **Property 5: Confusion Matrix Dimensions**
    - **Property 6: Confusion Matrix Normalization**
    - **Validates: Requirements 3.1, 3.2**
  
  - [x] 3.3 实现混淆分析
    - 实现 `analyze_confusion()` 方法
    - 识别 top 3 最容易混淆的类别对
    - 生成改进建议
    - _Requirements: 3.3, 3.4_

- [x] 4. 实现 ModelEvaluator 主类
  - [x] 4.1 实现模型加载功能
    - 实现 `load_model()` 方法
    - 验证模型类别数
    - 处理文件不存在错误
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x] 4.2 实现数据集解析
    - 解析 data.yaml 配置文件
    - 获取数据集路径和类别信息
    - _Requirements: 2.1_
  
  - [x] 4.3 实现评估主流程
    - 实现 `evaluate()` 方法
    - 遍历数据集图像进行推理
    - 收集预测结果和真实标签
    - 调用 MetricsCalculator 计算指标
    - _Requirements: 2.2, 2.5_

- [x] 5. Checkpoint - 确保核心功能测试通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 6. 实现 ReportGenerator 报告功能
  - [x] 6.1 实现 JSON 报告生成
    - 实现 `generate_json_report()` 方法
    - 包含所有元数据和指标
    - _Requirements: 5.1, 5.3, 5.4_
  
  - [ ]* 6.2 编写报告内容完整性的属性测试
    - **Property 7: Report Content Completeness**
    - **Validates: Requirements 5.1, 5.3, 5.4**
  
  - [x] 6.3 实现 Markdown 报告生成
    - 实现 `generate_markdown_report()` 方法
    - 包含整体指标、每类别指标、混淆分析
    - 高亮预警行为检测率
    - _Requirements: 5.2, 5.5, 7.3_

- [x] 7. 实现可视化功能
  - [x] 7.1 实现混淆矩阵热力图
    - 实现 `generate_confusion_heatmap()` 方法
    - 使用中文类别标签
    - 保存为 PNG 格式
    - _Requirements: 4.1, 4.4, 4.5_
  
  - [x] 7.2 实现 PR 曲线图
    - 实现 `generate_pr_curves()` 方法
    - 为每个类别生成 PR 曲线
    - _Requirements: 4.2_
  
  - [x] 7.3 实现指标对比柱状图
    - 实现 `generate_metrics_bar_chart()` 方法
    - 对比各类别的 precision, recall, F1
    - _Requirements: 4.3_

- [x] 8. 实现命令行接口
  - [x] 8.1 创建 CLI 脚本
    - 实现 `scripts/evaluate_model.py`
    - 支持 --weights, --data, --split, --output, --conf, --iou, --verbose 参数
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 8.2 实现参数验证和错误处理
    - 验证必需参数
    - 显示帮助信息
    - _Requirements: 6.7_

- [x] 9. Final Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
