# Implementation Plan: 大学生课堂行为预警模型

## Overview

本实现计划将设计文档转化为可执行的编码任务，采用增量开发方式，从核心配置模块开始，逐步构建数据处理、训练流水线、推理引擎和预警接口。使用Python语言，基于Ultralytics YOLOv11框架实现。

## Tasks

- [x] 1. 项目初始化与核心配置
  - [x] 1.1 创建项目目录结构和依赖配置
    - 创建 `src/` 目录结构
    - 创建 `requirements.txt` 包含 ultralytics, opencv-python, numpy, pyyaml, hypothesis
    - 创建 `pyproject.toml` 配置pytest
    - _Requirements: 10.5_

  - [x] 1.2 实现BehaviorConfig类别配置模块
    - 创建 `src/config/behavior_config.py`
    - 实现CLASSES字典定义7个学生行为类别
    - 实现LABEL_MAPPING定义各数据集的标签映射
    - 实现 `get_class_info()`, `get_alert_level()`, `is_warning_behavior()`, `get_class_names()` 方法
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 1.3 编写BehaviorConfig属性测试
    - **Property 1: 类别配置完整性**
    - **Validates: Requirements 1.1, 1.2**

- [ ] 2. Checkpoint - 确保配置模块测试通过
  - 运行测试确保BehaviorConfig模块正确
  - 如有问题请询问用户

- [x] 3. 数据处理模块实现
  - [x] 3.1 实现Label_Mapper标签映射模块
    - 创建 `src/data/label_mapper.py`
    - 实现 `remap_label()` 方法将原始标签映射到统一类别
    - 实现 `filter_teacher_labels()` 过滤教师行为标注
    - 实现 `generate_mapping_config()` 生成映射配置文件
    - _Requirements: 1.4, 2.2, 2.6_

  - [ ]* 3.2 编写Label_Mapper属性测试
    - **Property 3: 标签映射一致性**
    - **Property 6: 教师行为过滤**
    - **Validates: Requirements 1.4, 2.2, 2.6**

  - [x] 3.3 实现DataMerger数据合并模块
    - 创建 `src/data/data_merger.py`
    - 实现 `scan_datasets()` 扫描数据集目录
    - 实现 `merge_datasets()` 合并多个数据集
    - 实现 `split_dataset()` 按8:1:1比例划分数据集
    - 实现 `generate_data_yaml()` 生成YOLO配置文件
    - 实现 `generate_statistics()` 生成统计报告
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 3.4 编写DataMerger属性测试
    - **Property 5: 数据集划分比例**
    - **Validates: Requirements 3.2, 3.3**

- [x] 4. Checkpoint - 确保数据处理模块测试通过
  - 运行测试确保Label_Mapper和DataMerger模块正确
  - 如有问题请询问用户

- [x] 5. 预警接口模块实现
  - [x] 5.1 实现Detection和AlertResult数据类
    - 创建 `src/alert/models.py`
    - 实现 `Detection` dataclass 包含bbox, class_id, class_name, confidence, behavior_type, alert_level, timestamp
    - 实现 `AlertResult` dataclass 包含detections, alert_triggered, alert_summary, frame_id, timestamp
    - _Requirements: 7.1, 7.2, 7.5_

  - [ ]* 5.2 编写数据模型属性测试
    - **Property 2: 检测结果数据结构完整性**
    - **Validates: Requirements 1.3, 7.1, 7.2, 7.5**

  - [x] 5.3 实现AlertInterface预警接口
    - 创建 `src/alert/alert_interface.py`
    - 实现 `process_detections()` 处理原始检测结果
    - 实现 `aggregate_alerts()` 聚合时间窗口内的预警
    - 实现 `to_json()` 序列化为JSON
    - 实现 `get_alert_summary()` 获取预警摘要
    - _Requirements: 7.3, 7.4_

  - [ ]* 5.4 编写AlertInterface属性测试
    - **Property 4: 预警触发逻辑正确性**
    - **Property 8: JSON序列化往返一致性**
    - **Property 9: 视频统计聚合正确性**
    - **Validates: Requirements 7.3, 7.4, 9.3, 9.4**

- [ ] 6. Checkpoint - 确保预警接口模块测试通过
  - 运行测试确保Detection、AlertResult和AlertInterface模块正确
  - 如有问题请询问用户

- [x] 7. 训练流水线实现
  - [x] 7.1 实现TrainingPipeline训练模块
    - 创建 `src/training/training_pipeline.py`
    - 实现 `__init__()` 支持选择yolo11n/s/m/l/x模型
    - 实现 `configure()` 配置训练超参数
    - 实现 `train()` 执行训练，支持断点续训
    - 实现 `validate()` 在验证集上评估
    - 实现 `export()` 导出ONNX/TensorRT格式
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 7.2 创建训练脚本
    - 创建 `scripts/train.py` 命令行训练脚本
    - 支持参数：--model, --data, --epochs, --batch-size, --img-size, --resume
    - _Requirements: 4.1, 4.3, 4.5, 6.1, 6.2, 6.3, 6.4_

- [x] 8. 推理引擎实现
  - [x] 8.1 实现InferenceEngine推理模块
    - 创建 `src/inference/inference_engine.py`
    - 实现 `__init__()` 加载模型权重
    - 实现 `detect()` 单图像检测
    - 实现 `detect_video()` 视频检测
    - 实现 `detect_stream()` 实时视频流检测
    - 集成AlertInterface返回标准化预警结果
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 8.2 实现Visualizer可视化模块
    - 创建 `src/visualization/visualizer.py`
    - 实现颜色映射：正常行为绿色，预警行为按级别橙色/红色
    - 实现 `draw_detections()` 绘制检测框和标签
    - 实现 `draw_alert_panel()` 绘制预警统计面板
    - 实现 `generate_report()` 生成预警分析报告
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

  - [ ]* 8.3 编写Visualizer属性测试
    - **Property 7: 可视化颜色映射**
    - **Validates: Requirements 9.1**

- [ ] 9. Checkpoint - 确保推理模块测试通过
  - 运行测试确保InferenceEngine和Visualizer模块正确
  - 如有问题请询问用户

- [x] 10. 集成与脚本
  - [x] 10.1 创建数据合并脚本
    - 创建 `scripts/merge_datasets.py`
    - 支持参数：--datasets, --output, --split-ratio
    - 输出统一格式的数据集和data.yaml
    - _Requirements: 2.1, 2.3, 3.1, 3.2, 3.4_

  - [x] 10.2 创建推理脚本
    - 创建 `scripts/detect.py`
    - 支持参数：--weights, --source, --conf, --iou, --output
    - 支持图像、视频、摄像头输入
    - 输出可视化结果和JSON预警数据
    - _Requirements: 8.1, 8.3, 9.1, 9.4_

  - [x] 10.3 创建预警演示脚本
    - 创建 `scripts/demo_alert.py`
    - 实时显示检测结果和预警统计
    - 支持预警阈值配置
    - _Requirements: 7.3, 9.1, 9.2, 9.3_


- [x] 11. Final Checkpoint - 确保所有测试通过
  - 运行完整测试套件
  - 验证端到端流程
  - 如有问题请询问用户

## Notes

- 任务标记 `*` 为可选的属性测试任务，可跳过以加快MVP开发
- 每个任务引用具体的需求条款以确保可追溯性
- Checkpoint任务用于增量验证，确保每个模块正确后再继续
- 属性测试使用hypothesis库，每个测试运行至少100次迭代
- 单元测试和属性测试互补，共同确保代码正确性
