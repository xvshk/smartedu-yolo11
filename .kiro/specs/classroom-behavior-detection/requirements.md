# Requirements Document

## Introduction

本项目旨在开发一个基于YOLOv11的大学生课堂行为预警模型，通过整合多个数据集，实现对课堂中学生不良行为的实时检测与预警。该模型专注于学生行为识别，支持将行为分类为正常行为和需要预警的异常行为，为后期预警系统提供可靠的检测基础。

## Glossary

- **YOLOv11**: Ultralytics最新的目标检测模型，具有更高的精度和速度
- **Behavior_Detector**: 课堂行为检测系统的核心模块
- **Data_Merger**: 数据集合并与预处理模块
- **Label_Mapper**: 标签映射模块，用于统一不同数据集的类别标签
- **Training_Pipeline**: 模型训练流水线
- **Inference_Engine**: 推理引擎，用于实时行为检测
- **Alert_Interface**: 预警接口，提供行为检测结果供预警系统调用
- **Normal_Behavior**: 正常行为，如举手、阅读、书写
- **Warning_Behavior**: 预警行为，如睡觉、使用电子设备、交谈、站立（非正常情况）
- **YOLO_Format**: YOLO标注格式，每行包含 class_id x_center y_center width height

## Requirements

### Requirement 1: 学生行为类别定义

**User Story:** 作为开发者，我希望定义清晰的学生行为类别体系，区分正常行为和预警行为，便于后期预警功能实现。

#### Acceptance Criteria

1. THE Label_Mapper SHALL 支持以下学生行为类别：handrise(举手)、read(阅读)、write(书写)、sleep(睡觉)、stand(站立)、using_electronic_devices(使用电子设备)、talk(交谈)
2. THE Label_Mapper SHALL 将行为分为两类：正常行为(handrise、read、write)和预警行为(sleep、using_electronic_devices、talk、stand)
3. THE Behavior_Detector SHALL 为每个检测结果提供behavior_type字段，标识该行为属于normal还是warning类型
4. WHEN 不同数据集使用不同名称表示相同行为 THEN THE Label_Mapper SHALL 正确映射（如hand-raising → handrise）
5. THE Label_Mapper SHALL 生成类别映射配置文件，包含类别ID、名称和预警级别

### Requirement 2: 数据集整合与预处理

**User Story:** 作为开发者，我希望能够将多个不同来源的数据集整合为统一格式，以便进行模型训练。

#### Acceptance Criteria

1. WHEN 执行数据合并脚本 THEN THE Data_Merger SHALL 扫描所有数据集目录并识别图像和标签文件
2. WHEN 发现不同数据集使用不同类别ID THEN THE Label_Mapper SHALL 将所有标签映射到统一的类别体系
3. WHEN 合并完成 THEN THE Data_Merger SHALL 生成新的data.yaml配置文件，包含正确的路径和类别信息
4. WHEN 图像格式不一致（png/jpg）THEN THE Data_Merger SHALL 统一处理所有支持的图像格式
5. IF 标签文件缺失或损坏 THEN THE Data_Merger SHALL 记录错误并跳过该样本
6. THE Data_Merger SHALL 只保留学生行为相关的标注，过滤掉教师行为标注

### Requirement 3: 数据集划分与验证

**User Story:** 作为开发者，我希望合并后的数据集能够正确划分为训练集、验证集和测试集。

#### Acceptance Criteria

1. WHEN 数据集已有train/val/test划分 THEN THE Data_Merger SHALL 保持原有划分
2. WHEN 数据集没有划分 THEN THE Data_Merger SHALL 按照8:1:1的比例进行划分
3. WHEN 划分完成 THEN THE Data_Merger SHALL 确保每个类别在各划分中都有足够的样本
4. THE Data_Merger SHALL 生成数据集统计报告，包含各类别的样本数量分布

### Requirement 4: YOLOv11模型配置

**User Story:** 作为开发者，我希望能够配置YOLOv11模型进行课堂行为检测训练。

#### Acceptance Criteria

1. THE Training_Pipeline SHALL 支持选择不同规模的YOLOv11模型（yolo11n、yolo11s、yolo11m、yolo11l、yolo11x）
2. WHEN 开始训练 THEN THE Training_Pipeline SHALL 加载预训练权重进行迁移学习
3. THE Training_Pipeline SHALL 支持配置训练超参数（epochs、batch_size、learning_rate、image_size等）
4. WHEN 训练过程中 THEN THE Training_Pipeline SHALL 保存最佳模型权重和最后一轮权重
5. THE Training_Pipeline SHALL 支持断点续训功能

### Requirement 5: 数据增强策略

**User Story:** 作为开发者，我希望应用适当的数据增强策略来提高模型的泛化能力。

#### Acceptance Criteria

1. THE Training_Pipeline SHALL 支持基础数据增强（翻转、旋转、缩放）
2. THE Training_Pipeline SHALL 支持颜色空间增强（HSV调整、亮度对比度变化）
3. THE Training_Pipeline SHALL 支持Mosaic和MixUp增强
4. WHEN 配置增强参数 THEN THE Training_Pipeline SHALL 允许用户自定义增强强度
5. IF 增强导致标注框超出图像边界 THEN THE Training_Pipeline SHALL 自动裁剪或丢弃该标注

### Requirement 6: 模型训练与监控

**User Story:** 作为开发者，我希望能够监控训练过程并评估模型性能。

#### Acceptance Criteria

1. WHEN 训练进行中 THEN THE Training_Pipeline SHALL 实时显示损失值和评估指标
2. THE Training_Pipeline SHALL 在每个epoch结束后在验证集上评估模型
3. THE Training_Pipeline SHALL 记录并可视化训练曲线（loss、mAP、precision、recall）
4. WHEN 训练完成 THEN THE Training_Pipeline SHALL 生成详细的评估报告
5. THE Training_Pipeline SHALL 支持TensorBoard或WandB进行训练可视化

### Requirement 7: 预警接口设计

**User Story:** 作为开发者，我希望模型提供标准化的预警接口，便于后期预警系统集成。

#### Acceptance Criteria

1. THE Alert_Interface SHALL 为每个检测结果返回结构化数据：bbox(边界框)、class_id(类别ID)、class_name(类别名称)、confidence(置信度)、behavior_type(normal/warning)、alert_level(预警级别0-3)
2. THE Alert_Interface SHALL 定义预警级别：0-正常、1-轻度预警(stand)、2-中度预警(talk)、3-严重预警(sleep、using_electronic_devices)
3. WHEN 检测到预警行为 THEN THE Alert_Interface SHALL 返回alert_triggered=true标志
4. THE Alert_Interface SHALL 支持批量检测结果的聚合统计，返回各类预警行为的数量
5. THE Alert_Interface SHALL 提供时间戳字段，便于预警系统进行时序分析

### Requirement 8: 模型推理与实时检测

**User Story:** 作为用户，我希望能够使用训练好的模型进行实时课堂行为检测。

#### Acceptance Criteria

1. THE Inference_Engine SHALL 支持图像、视频和摄像头实时输入
2. WHEN 检测到行为 THEN THE Inference_Engine SHALL 通过Alert_Interface返回标准化结果
3. THE Inference_Engine SHALL 支持设置置信度阈值和NMS阈值
4. THE Inference_Engine SHALL 支持导出为ONNX、TensorRT等格式以优化推理速度
5. WHEN 处理视频流 THEN THE Inference_Engine SHALL 达到至少15FPS的推理速度

### Requirement 9: 结果可视化与统计

**User Story:** 作为用户，我希望能够直观地查看检测结果和预警统计。

#### Acceptance Criteria

1. THE Inference_Engine SHALL 在图像/视频上绘制检测框，正常行为使用绿色，预警行为使用红色/橙色
2. THE Inference_Engine SHALL 在检测框旁显示类别名称、置信度和预警级别
3. WHEN 处理视频 THEN THE Inference_Engine SHALL 统计各类预警行为的出现频率和持续时长
4. THE Inference_Engine SHALL 支持导出检测结果为JSON格式，包含完整的预警信息
5. THE Inference_Engine SHALL 生成课堂行为预警分析报告

### Requirement 10: 错误处理与日志

**User Story:** 作为开发者，我希望系统能够妥善处理错误并记录详细日志。

#### Acceptance Criteria

1. IF 数据文件损坏或格式错误 THEN THE Behavior_Detector SHALL 记录错误并继续处理其他文件
2. IF GPU内存不足 THEN THE Training_Pipeline SHALL 自动减小batch_size并重试
3. THE Behavior_Detector SHALL 记录所有操作的详细日志，包含时间戳和操作结果
4. IF 模型加载失败 THEN THE Inference_Engine SHALL 提供明确的错误信息和解决建议
5. THE Behavior_Detector SHALL 支持配置日志级别（DEBUG、INFO、WARNING、ERROR）
