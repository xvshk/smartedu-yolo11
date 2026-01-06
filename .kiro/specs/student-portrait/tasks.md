# Implementation Plan: Student Portrait (学业全景画像)

## Overview

本实现计划将学业全景画像功能分解为可执行的编码任务。后端使用 Python Flask，前端使用 Vue 3 + Element Plus。

## Tasks

- [x] 1. 创建后端服务基础结构
  - 创建 `backend/services/` 目录
  - 创建 `portrait_service.py` 服务文件
  - 定义数据类和基础方法
  - _Requirements: 1.1, 7.1_

- [x] 2. 实现班级概览功能
  - [x] 2.1 实现 get_class_overview 方法
    - 统计检测会话数、学生数、检测总数
    - 计算平均注意力指数
    - 获取行为分布数据
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [ ]* 2.2 编写概览数据完整性测试
    - **Property 1: Overview Data Completeness**
    - **Validates: Requirements 1.2, 1.3, 1.4**

- [x] 3. 实现行为分布分析
  - [x] 3.1 实现 get_behavior_distribution 方法
    - 统计 7 种行为类型的数量
    - 分类为正常行为和预警行为
    - 支持日期范围过滤
    - _Requirements: 2.1, 2.2, 2.4_
  
  - [ ]* 3.2 编写行为分布完整性测试
    - **Property 2: Behavior Distribution Completeness**
    - **Validates: Requirements 2.1, 2.2**

- [x] 4. 实现注意力趋势分析
  - [x] 4.1 实现 get_attention_trend 方法
    - 计算每日注意力指数
    - 使用公式: normal_behaviors / total_behaviors
    - 支持不同时间范围 (7天, 30天, 自定义)
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  
  - [ ]* 4.2 编写注意力计算属性测试
    - **Property 4: Attention Rate Calculation**
    - **Validates: Requirements 3.2**

- [x] 5. 实现预警行为排名
  - [x] 5.1 实现 get_warning_ranking 方法
    - 统计预警行为数量
    - 按数量降序排序
    - 返回 Top N (默认5)
    - _Requirements: 4.1, 4.2_
  
  - [ ]* 5.2 编写排名排序属性测试
    - **Property 6: Warning Ranking Order**
    - **Validates: Requirements 4.1, 4.2**

- [x] 6. Checkpoint - 确保班级画像功能测试通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 7. 实现学生个人画像
  - [x] 7.1 实现 get_student_portrait 方法
    - 获取学生个人行为分布
    - 计算学生注意力指数
    - 获取班级平均值进行对比
    - 计算同伴对比数据
    - _Requirements: 7.2, 7.3, 7.4, 7.6_
  
  - [ ]* 7.2 编写学生画像完整性测试
    - **Property 7: Student Portrait Completeness**
    - **Validates: Requirements 7.2, 7.3, 7.4, 7.5, 7.6**

- [x] 8. 实现改进建议功能
  - [x] 8.1 实现 get_improvement_suggestions 方法
    - 分析学生最频繁的预警行为
    - 根据行为类型生成个性化建议
    - 设置建议优先级
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 8.2 编写建议生成属性测试
    - **Property 8: Suggestion Generation**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [x] 9. 实现数据导出功能
  - [x] 9.1 实现 export_portrait_data 方法
    - 生成包含所有画像数据的 JSON
    - 包含元数据、行为分布、趋势、排名
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 10. 创建 API Blueprint
  - [x] 10.1 创建 portrait.py API 文件
    - 实现 /overview 端点
    - 实现 /behavior-distribution 端点
    - 实现 /attention-trend 端点
    - 实现 /warning-ranking 端点
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 10.2 实现学生画像 API 端点
    - 实现 /student/{student_id} 端点
    - 实现 /student/{student_id}/suggestions 端点
    - 实现权限控制
    - _Requirements: 9.5, 9.6, 9.8, 9.9_
  
  - [x] 10.3 实现导出 API 端点
    - 实现 /export 端点
    - _Requirements: 9.7_

- [x] 11. 注册 API Blueprint
  - 在 app.py 中注册 portrait_bp
  - 添加路由前缀 /api/portrait
  - _Requirements: 9.1_

- [x] 12. Checkpoint - 确保后端 API 测试通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 13. 更新前端 API 模块
  - 在 frontend/src/api/index.js 中添加 portrait API
  - 添加所有画像相关的 API 调用方法
  - _Requirements: 9.1-9.7_

- [x] 14. 实现前端班级画像页面
  - [x] 14.1 实现班级概览卡片
    - 显示总会话数、学生数、平均注意力
    - 显示预警数量
    - _Requirements: 1.2_
  
  - [x] 14.2 实现行为分布图表
    - 使用 ECharts 饼图展示行为分布
    - 区分正常行为和预警行为颜色
    - _Requirements: 1.3, 2.3_
  
  - [x] 14.3 实现注意力趋势图表
    - 使用 ECharts 折线图展示趋势
    - 支持日期范围选择
    - _Requirements: 1.4, 3.1, 3.4_
  
  - [x] 14.4 实现预警排名列表
    - 显示 Top 5 预警行为
    - 使用颜色区分预警级别
    - _Requirements: 4.1, 4.3_

- [x] 15. 实现前端学生画像页面
  - [x] 15.1 实现学生画像视图
    - 显示个人注意力指数
    - 显示与班级平均对比
    - 显示同伴排名
    - _Requirements: 7.2, 7.6_
  
  - [x] 15.2 实现改进建议展示
    - 显示个性化改进建议
    - 按优先级排序
    - _Requirements: 8.1_

- [x] 16. 实现数据导出功能
  - 添加导出按钮
  - 触发 JSON 文件下载
  - _Requirements: 6.4_

- [x] 17. Final Checkpoint - 确保所有功能测试通过
  - 确保所有测试通过，如有问题请询问用户

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
