# Requirements Document

## Introduction

本文档定义了预警模块页面和首页图表优化的需求规格。主要目标是修复图表显示问题、新增数据可视化图表并美化页面样式，提升用户体验和视觉效果。

## Glossary

- **Alert_Page**: 预警管理页面，展示预警列表、统计图表和规则配置
- **Dashboard_Page**: 首页/系统概览页面，展示系统整体数据和趋势
- **Level_Chart**: 预警级别分布饼图，展示各级别预警的占比
- **Behavior_Chart**: 行为类型分布柱状图/饼图，展示各类行为的分布
- **Trend_Chart**: 趋势折线图，展示数据随时间的变化
- **Heatmap_Chart**: 热力图，展示时间段内的行为分布密度
- **Time_Distribution_Chart**: 时间分布图，展示预警在各时段的分布
- **Relation_Graph**: 关系图，展示数据实体之间的关联关系
- **Funnel_Chart**: 漏斗图，展示预警处理流程的转化情况
- **Stat_Card**: 统计卡片，展示关键指标数据
- **Filter_Bar**: 筛选条件栏，用于筛选预警列表

## Requirements

### Requirement 1: 预警页面图表显示修复

**User Story:** As a teacher, I want to see alert distribution charts correctly, so that I can understand the overall alert situation at a glance.

#### Acceptance Criteria

1. WHEN the Alert_Page loads, THE Level_Chart SHALL display alert level distribution data correctly
2. WHEN the Alert_Page loads, THE Behavior_Chart SHALL display behavior type distribution data correctly
3. WHEN statistics data is empty, THE charts SHALL display a placeholder message indicating no data
4. WHEN statistics data is loaded, THE charts SHALL update automatically without page refresh
5. WHEN the window is resized, THE charts SHALL resize responsively to fit the container

### Requirement 2: 首页图表显示修复

**User Story:** As a user, I want to see dashboard charts correctly, so that I can understand the system overview at a glance.

#### Acceptance Criteria

1. WHEN the Dashboard_Page loads, THE Trend_Chart SHALL display attention rate trend data correctly
2. WHEN the Dashboard_Page loads, THE Behavior_Chart SHALL display behavior distribution data correctly
3. WHEN chart data is empty, THE Dashboard_Page SHALL display meaningful empty state messages
4. WHEN chart period is changed, THE Trend_Chart SHALL reload data and update display
5. THE charts SHALL handle loading and error states gracefully with visual feedback

### Requirement 3: 新增首页图表

**User Story:** As a user, I want to see more comprehensive data visualizations on the dashboard, so that I can better understand system performance and student behavior patterns.

#### Acceptance Criteria

1. THE Dashboard_Page SHALL include a weekly alert trend line chart showing alert counts over time
2. THE Dashboard_Page SHALL include a behavior heatmap showing behavior distribution by time of day
3. THE Dashboard_Page SHALL include a class comparison bar chart showing performance across different classes
4. THE Dashboard_Page SHALL include a real-time activity indicator showing current detection status
5. THE Dashboard_Page SHALL include a Relation_Graph showing relationships between students, behaviors, and alerts
6. THE Relation_Graph SHALL display nodes for different entity types (students, behaviors, sessions) with connecting edges
7. WHEN new charts are added, THE Dashboard_Page SHALL maintain responsive layout on all screen sizes

### Requirement 4: 新增预警页面图表

**User Story:** As a teacher, I want to see more detailed alert analytics, so that I can identify patterns and take proactive measures.

#### Acceptance Criteria

1. THE Alert_Page SHALL include an alert trend line chart showing alert frequency over time
2. THE Alert_Page SHALL include a time distribution chart showing peak alert hours
3. THE Alert_Page SHALL include a severity comparison chart showing alert levels by behavior type
4. THE Alert_Page SHALL include a Funnel_Chart showing alert processing workflow (generated → viewed → handled → resolved)
5. THE Funnel_Chart SHALL display conversion rates between each stage
6. WHEN hovering over chart elements, THE charts SHALL display detailed tooltips with context information

### Requirement 5: 图表样式美化

**User Story:** As a user, I want the charts to look visually appealing, so that the data is easier to understand.

#### Acceptance Criteria

1. THE Level_Chart SHALL use distinct colors for each alert level (green for normal, gray for mild, orange for moderate, red for severe)
2. THE Behavior_Chart SHALL use gradient colors for visual appeal
3. THE charts SHALL display tooltips with detailed information on hover
4. THE charts SHALL include legends for data identification
5. THE charts SHALL have smooth animations when data changes
6. THE Trend_Chart SHALL use area fill with gradient for better visual effect

### Requirement 6: 页面布局优化

**User Story:** As a user, I want a well-organized page layout, so that I can navigate and find information easily.

#### Acceptance Criteria

1. THE Alert_Page SHALL maintain consistent spacing between components
2. THE Dashboard_Page SHALL organize charts in a logical grid layout
3. THE filter bar SHALL be visually distinct and easy to use
4. THE alert list items SHALL have clear visual hierarchy with level indicators
5. THE pages SHALL be responsive and work well on different screen sizes
6. THE card headers SHALL have consistent styling across the page

### Requirement 7: 预警列表样式美化

**User Story:** As a teacher, I want the alert list to be visually clear, so that I can quickly identify important alerts.

#### Acceptance Criteria

1. THE alert items SHALL have distinct background colors based on alert level
2. THE unread alerts SHALL be visually distinguished from read alerts
3. THE alert level indicators SHALL use consistent color coding
4. THE alert item hover effects SHALL provide visual feedback
5. THE alert timestamps SHALL be formatted in a readable manner

### Requirement 8: 统计卡片优化

**User Story:** As a user, I want the statistics cards to display data clearly, so that I can quickly understand key metrics.

#### Acceptance Criteria

1. THE Stat_Cards SHALL display icons that match their content
2. THE trend indicators SHALL show direction (up/down) with appropriate colors
3. THE Stat_Cards SHALL have hover effects for interactivity
4. WHEN a Stat_Card is clicked, THE page SHALL filter or navigate accordingly
5. THE Stat_Cards SHALL handle loading and error states gracefully

### Requirement 9: 空状态处理

**User Story:** As a user, I want to see meaningful feedback when there is no data, so that I understand the system state.

#### Acceptance Criteria

1. WHEN the alert list is empty, THE Alert_Page SHALL display an empty state illustration
2. WHEN chart data is empty, THE charts SHALL display "暂无数据" message with appropriate styling
3. WHEN data is loading, THE components SHALL display loading indicators
4. WHEN an error occurs, THE pages SHALL display an error message with retry option
