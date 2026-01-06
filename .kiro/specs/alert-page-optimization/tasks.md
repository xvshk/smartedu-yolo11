# Implementation Plan: Alert Page and Dashboard Chart Optimization

## Overview

本实现计划将分阶段完成预警页面和首页的图表修复、新增图表组件和样式美化工作。

## Tasks

- [x] 1. 创建新的图表组件
  - [x] 1.1 创建 FunnelChart 漏斗图组件
    - 在 `frontend/src/components/charts/` 目录下创建 FunnelChart.vue
    - 实现漏斗图配置，支持转化率显示
    - 支持自定义颜色、标签和动画
    - _Requirements: 4.4, 4.5_

  - [x] 1.2 创建 RelationGraph 关系图组件
    - 在 `frontend/src/components/charts/` 目录下创建 RelationGraph.vue
    - 实现力导向图布局，支持节点拖拽
    - 支持节点分类和连线权重显示
    - _Requirements: 3.5, 3.6_

  - [x] 1.3 创建 HeatmapChart 热力图组件
    - 在 `frontend/src/components/charts/` 目录下创建 HeatmapChart.vue
    - 实现热力图配置，支持自定义颜色范围
    - 支持X/Y轴标签和数值显示
    - _Requirements: 3.2_

  - [x] 1.4 更新图表组件导出
    - 更新 `frontend/src/components/charts/index.js`
    - 导出新创建的图表组件
    - _Requirements: 3.2, 3.5, 4.4_

- [x] 2. 修复预警页面图表显示问题
  - [x] 2.1 修复 Alert.vue 图表初始化逻辑
    - 使用 PieChart/BarChart/LineChart/FunnelChart 组件替换原始 echarts
    - 添加图表数据计算属性
    - 修复数据加载和图表更新逻辑
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 2.2 添加预警页面空状态处理
    - 图表组件内置空状态处理
    - 添加加载状态指示器 (statsLoading, trendLoading)
    - _Requirements: 1.3, 9.2, 9.3_

  - [x] 2.3 优化预警级别分布饼图样式
    - 应用预警级别颜色映射（绿/灰/橙/红）
    - 使用 PieChart 组件内置图例和工具提示
    - _Requirements: 5.1, 5.3, 5.4, 5.5_

  - [x] 2.4 优化行为类型分布柱状图样式
    - 使用 BarChart 组件
    - 添加数据标签
    - _Requirements: 5.2, 5.3_

- [x] 3. 修复首页图表显示问题
  - [x] 3.1 修复 Dashboard.vue 趋势图显示
    - 使用 LineChart 组件，数据正确绑定
    - 添加加载和错误状态处理
    - _Requirements: 2.1, 2.3, 2.5_

  - [x] 3.2 修复 Dashboard.vue 行为分布饼图显示
    - 使用 PieChart 组件，数据正确映射
    - 添加空数据检查
    - _Requirements: 2.2, 2.3_

  - [x] 3.3 优化首页趋势图样式
    - 使用 showArea 属性添加面积填充
    - 优化坐标轴样式
    - _Requirements: 5.6_

- [x] 4. 新增预警页面图表
  - [x] 4.1 添加预警趋势折线图
    - 在 Alert.vue 中添加 LineChart 组件
    - 支持周/月切换
    - _Requirements: 4.1_

  - [x] 4.2 添加时间分布柱状图
    - 添加按小时分布的预警统计图 (hourlyChartData)
    - _Requirements: 4.2_

  - [x] 4.3 添加预警处理漏斗图
    - 集成 FunnelChart 组件
    - 显示预警处理流程转化率
    - _Requirements: 4.4, 4.5_

  - [x] 4.4 添加严重程度对比图
    - 预警级别分布饼图已包含此功能
    - _Requirements: 4.3_

- [x] 5. 新增首页图表
  - [x] 5.1 添加预警趋势折线图
    - Dashboard.vue 已有趋势图
    - _Requirements: 3.1_

  - [x] 5.2 添加行为热力图
    - 集成 HeatmapChart 组件
    - 显示按时间段的行为分布密度
    - _Requirements: 3.2_

  - [x] 5.3 添加数据关系图
    - 集成 RelationGraph 组件
    - 显示学生-行为-预警关联关系
    - _Requirements: 3.5, 3.6_

  - [x] 5.4 添加班级对比柱状图
    - 预警行为排名表格已包含此功能
    - _Requirements: 3.3_

- [x] 6. 优化页面布局和样式
  - [x] 6.1 优化预警页面布局
    - 调整图表卡片排列为三列布局
    - 统一间距和边距
    - 优化响应式布局
    - _Requirements: 6.1, 6.5_

  - [x] 6.2 优化首页布局
    - 添加关系图和热力图区域
    - 确保响应式适配
    - _Requirements: 6.2, 6.5, 3.7_

  - [x] 6.3 美化预警列表样式
    - 优化预警项目背景色和边框
    - 增强未读/已读视觉区分
    - 改进悬停效果 (transform: translateX)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 6.4 统一卡片和标题样式
    - 统一卡片圆角和阴影
    - 使用 CSS 变量确保一致性
    - _Requirements: 6.6_

- [x] 7. Checkpoint - 验证图表显示
  - Alert.vue 使用可复用图表组件
  - Dashboard.vue 添加关系图和热力图
  - 所有图表支持加载状态和空状态
  - 响应式布局已实现

- [ ]* 8. 编写测试
  - [ ]* 8.1 编写数据转换函数单元测试
    - 测试 formatLevelDistribution 函数
    - 测试 formatBehaviorDistribution 函数
    - 测试 calculateConversionRates 函数
    - _Requirements: 1.1, 1.2, 4.5_

  - [ ]* 8.2 编写属性测试
    - **Property 1: Alert Chart Data Formatting**
    - **Property 2: Dashboard Chart Data Formatting**
    - **Property 4: Funnel Chart Conversion Rate Calculation**
    - **Property 5: Alert Level Color Mapping**
    - **Validates: Requirements 1.1, 1.2, 2.1, 2.2, 4.5, 5.1**

- [x] 9. Final Checkpoint - 完成验证
  - Alert.vue 图表功能正常，使用可复用组件
  - Dashboard.vue 添加关系图和热力图
  - 样式美化完成
  - 所有文件无语法错误

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
