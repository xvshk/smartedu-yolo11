# Requirements Document

## Introduction

本文档定义了课堂行为检测模型评估功能的需求。该功能用于全面评估 YOLOv11 模型在课堂行为检测任务上的性能，包括整体指标、各类别指标、混淆矩阵分析以及可视化输出。

## Glossary

- **Model_Evaluator**: 模型评估器，负责加载模型并执行评估流程
- **Behavior_Detector**: 行为检测器，使用训练好的模型对图像进行推理
- **Metrics_Calculator**: 指标计算器，计算各种评估指标
- **Report_Generator**: 报告生成器，生成评估报告和可视化结果
- **mAP50**: Mean Average Precision at IoU threshold 0.5
- **mAP50-95**: Mean Average Precision averaged over IoU thresholds from 0.5 to 0.95
- **Precision**: 精确率，正确预测的正样本占所有预测为正的比例
- **Recall**: 召回率，正确预测的正样本占所有实际正样本的比例
- **F1_Score**: F1分数，精确率和召回率的调和平均值
- **Confusion_Matrix**: 混淆矩阵，展示各类别预测与实际标签的对应关系

## Requirements

### Requirement 1: 模型加载与验证

**User Story:** As a developer, I want to load a trained model and validate it, so that I can ensure the model is ready for evaluation.

#### Acceptance Criteria

1. WHEN a model weights path is provided, THE Model_Evaluator SHALL load the model from the specified path
2. WHEN the model weights file does not exist, THE Model_Evaluator SHALL return a descriptive error message
3. WHEN the model is loaded successfully, THE Model_Evaluator SHALL validate that the model has 7 behavior classes
4. IF the model class count does not match expected classes, THEN THE Model_Evaluator SHALL log a warning and continue

### Requirement 2: 数据集评估

**User Story:** As a developer, I want to evaluate the model on validation and test datasets, so that I can understand the model's performance on different data splits.

#### Acceptance Criteria

1. WHEN a data.yaml configuration is provided, THE Model_Evaluator SHALL parse the dataset paths correctly
2. WHEN evaluating on a dataset split, THE Model_Evaluator SHALL process all images in that split
3. WHEN evaluation completes, THE Metrics_Calculator SHALL compute mAP50, mAP50-95, precision, recall, and F1 score
4. WHEN per-class metrics are requested, THE Metrics_Calculator SHALL compute metrics for each of the 7 behavior classes
5. IF an image cannot be processed, THEN THE Model_Evaluator SHALL log the error and continue with remaining images

### Requirement 3: 混淆矩阵分析

**User Story:** As a developer, I want to generate and analyze confusion matrices, so that I can understand which behaviors are being confused with each other.

#### Acceptance Criteria

1. WHEN evaluation completes, THE Metrics_Calculator SHALL generate a confusion matrix for all predictions
2. WHEN generating the confusion matrix, THE Metrics_Calculator SHALL normalize values by row (actual class)
3. WHEN confusion matrix is generated, THE Report_Generator SHALL identify the top 3 most confused class pairs
4. WHEN confusion analysis is complete, THE Report_Generator SHALL provide recommendations for improving confused classes

### Requirement 4: 可视化输出

**User Story:** As a developer, I want to generate visual reports of evaluation results, so that I can easily understand and share the model's performance.

#### Acceptance Criteria

1. WHEN evaluation completes, THE Report_Generator SHALL generate a confusion matrix heatmap image
2. WHEN evaluation completes, THE Report_Generator SHALL generate precision-recall curves for each class
3. WHEN evaluation completes, THE Report_Generator SHALL generate a bar chart comparing per-class metrics
4. WHEN generating visualizations, THE Report_Generator SHALL save images in PNG format with configurable DPI
5. WHEN generating visualizations, THE Report_Generator SHALL use Chinese labels for behavior class names

### Requirement 5: 评估报告生成

**User Story:** As a developer, I want to generate comprehensive evaluation reports, so that I can document and track model performance over time.

#### Acceptance Criteria

1. WHEN evaluation completes, THE Report_Generator SHALL generate a JSON report with all metrics
2. WHEN evaluation completes, THE Report_Generator SHALL generate a human-readable Markdown report
3. WHEN generating reports, THE Report_Generator SHALL include model metadata (weights path, evaluation date, dataset info)
4. WHEN generating reports, THE Report_Generator SHALL include overall metrics and per-class metrics
5. WHEN generating reports, THE Report_Generator SHALL include confusion analysis and recommendations

### Requirement 6: 命令行接口

**User Story:** As a developer, I want to run model evaluation from the command line, so that I can easily integrate evaluation into my workflow.

#### Acceptance Criteria

1. WHEN the script is executed with --weights and --data arguments, THE Model_Evaluator SHALL run evaluation
2. WHEN --split argument is provided, THE Model_Evaluator SHALL evaluate on the specified split (val or test)
3. WHEN --output argument is provided, THE Report_Generator SHALL save results to the specified directory
4. WHEN --conf argument is provided, THE Behavior_Detector SHALL use the specified confidence threshold
5. WHEN --iou argument is provided, THE Behavior_Detector SHALL use the specified IoU threshold for NMS
6. WHEN --verbose flag is set, THE Model_Evaluator SHALL output detailed progress information
7. IF required arguments are missing, THEN THE script SHALL display usage help and exit with error code

### Requirement 7: 预警行为分析

**User Story:** As a developer, I want to analyze model performance on warning behaviors specifically, so that I can ensure the model effectively detects problematic behaviors.

#### Acceptance Criteria

1. WHEN evaluation completes, THE Metrics_Calculator SHALL compute separate metrics for normal behaviors (handrise, read, write)
2. WHEN evaluation completes, THE Metrics_Calculator SHALL compute separate metrics for warning behaviors (sleep, stand, using_electronic_devices, talk)
3. WHEN generating reports, THE Report_Generator SHALL highlight warning behavior detection rates
4. WHEN warning behavior recall is below 0.5, THE Report_Generator SHALL flag this as a critical issue
