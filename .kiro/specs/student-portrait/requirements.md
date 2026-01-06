# Requirements Document

## Introduction

本文档定义了学业全景画像功能的需求。该功能用于分析和展示学生在课堂中的行为表现，提供多维度的数据可视化和趋势分析，帮助教师了解学生的学习状态和课堂参与度。

## Glossary

- **Portrait_Service**: 画像服务，负责生成和管理学生画像数据
- **Student_Portrait**: 学生画像，包含单个学生的行为分析数据
- **Class_Portrait**: 班级画像，包含班级整体的行为分析数据
- **Attention_Rate**: 注意力指数，正常行为占总行为的比例
- **Behavior_Trend**: 行为趋势，一段时间内行为变化的统计
- **Warning_Behavior**: 预警行为，包括睡觉、站立、使用电子设备、交谈

## Requirements

### Requirement 1: 班级整体画像

**User Story:** As a teacher, I want to view the overall portrait of a class, so that I can understand the class's learning status and behavior patterns.

#### Acceptance Criteria

1. WHEN a user visits the portrait page, THE Portrait_Service SHALL display the class overview dashboard
2. WHEN displaying class overview, THE Portrait_Service SHALL show total detection sessions, total students, and average attention rate
3. WHEN displaying class overview, THE Portrait_Service SHALL show behavior distribution pie chart for all 7 behavior types
4. WHEN displaying class overview, THE Portrait_Service SHALL show attention rate trend over the past 7 days
5. WHEN displaying class overview, THE Portrait_Service SHALL highlight warning behaviors with alert indicators

### Requirement 2: 行为分布分析

**User Story:** As a teacher, I want to analyze behavior distribution, so that I can identify common behavior patterns in the classroom.

#### Acceptance Criteria

1. WHEN analyzing behavior distribution, THE Portrait_Service SHALL compute counts for each of the 7 behavior types
2. WHEN displaying behavior distribution, THE Portrait_Service SHALL show both normal behaviors (handrise, read, write) and warning behaviors (sleep, stand, using_electronic_devices, talk)
3. WHEN displaying behavior distribution, THE Portrait_Service SHALL use color coding to distinguish normal (green) and warning (red/orange) behaviors
4. WHEN a date range is selected, THE Portrait_Service SHALL filter behavior data within that range
5. WHEN behavior data is empty, THE Portrait_Service SHALL display a friendly empty state message

### Requirement 3: 注意力趋势分析

**User Story:** As a teacher, I want to track attention trends over time, so that I can monitor class engagement and identify patterns.

#### Acceptance Criteria

1. WHEN displaying attention trend, THE Portrait_Service SHALL show a line chart of daily attention rates
2. WHEN calculating attention rate, THE Portrait_Service SHALL use the formula: normal_behaviors / total_behaviors
3. WHEN attention rate falls below 0.5, THE Portrait_Service SHALL highlight this as a critical issue
4. WHEN displaying trend, THE Portrait_Service SHALL support date range selection (7 days, 30 days, custom)
5. WHEN no data exists for a date, THE Portrait_Service SHALL skip that date in the trend chart

### Requirement 4: 预警行为排名

**User Story:** As a teacher, I want to see top warning behaviors, so that I can focus on the most common issues.

#### Acceptance Criteria

1. WHEN displaying warning ranking, THE Portrait_Service SHALL show top 5 warning behaviors by count
2. WHEN displaying warning ranking, THE Portrait_Service SHALL include behavior name, count, and percentage
3. WHEN displaying warning ranking, THE Portrait_Service SHALL use alert level colors (mild=yellow, moderate=orange, severe=red)
4. WHEN a warning behavior is clicked, THE Portrait_Service SHALL show detailed breakdown by time period

### Requirement 5: 课程效果对比

**User Story:** As a teacher, I want to compare behavior patterns across different courses, so that I can evaluate teaching effectiveness.

#### Acceptance Criteria

1. WHEN comparing courses, THE Portrait_Service SHALL show attention rates for each course
2. WHEN comparing courses, THE Portrait_Service SHALL display a bar chart comparing course metrics
3. WHEN comparing courses, THE Portrait_Service SHALL rank courses by attention rate
4. IF no course data exists, THEN THE Portrait_Service SHALL display a message indicating no data available

### Requirement 6: 数据导出

**User Story:** As a teacher, I want to export portrait data, so that I can use it for reports and further analysis.

#### Acceptance Criteria

1. WHEN export is requested, THE Portrait_Service SHALL generate a JSON file with all portrait data
2. WHEN export is requested, THE Portrait_Service SHALL include metadata (date range, class info, generation time)
3. WHEN export is requested, THE Portrait_Service SHALL include behavior distribution, attention trends, and warning rankings
4. WHEN export completes, THE Portrait_Service SHALL trigger a file download

### Requirement 7: 学生个人画像

**User Story:** As a student, I want to view my personal learning portrait, so that I can understand my own classroom behavior and improve my learning habits.

#### Acceptance Criteria

1. WHEN a student visits their portrait page, THE Portrait_Service SHALL display their personal behavior summary
2. WHEN displaying personal portrait, THE Portrait_Service SHALL show the student's attention rate compared to class average
3. WHEN displaying personal portrait, THE Portrait_Service SHALL show the student's behavior distribution pie chart
4. WHEN displaying personal portrait, THE Portrait_Service SHALL show the student's attention trend over time
5. WHEN displaying personal portrait, THE Portrait_Service SHALL highlight areas for improvement based on warning behaviors
6. WHEN displaying personal portrait, THE Portrait_Service SHALL show behavior comparison with class peers (anonymized)
7. WHEN a student has no detection data, THE Portrait_Service SHALL display a friendly message indicating no data available

### Requirement 8: 学生行为改进建议

**User Story:** As a student, I want to receive personalized improvement suggestions, so that I can improve my classroom engagement.

#### Acceptance Criteria

1. WHEN displaying improvement suggestions, THE Portrait_Service SHALL analyze the student's most frequent warning behaviors
2. WHEN a student has high frequency of sleep behavior, THE Portrait_Service SHALL suggest rest and schedule adjustments
3. WHEN a student has high frequency of device usage, THE Portrait_Service SHALL suggest focus techniques
4. WHEN a student has high frequency of talking, THE Portrait_Service SHALL suggest appropriate discussion times
5. WHEN a student's attention rate improves, THE Portrait_Service SHALL display positive encouragement messages

### Requirement 9: API 接口

**User Story:** As a developer, I want portrait data accessible via API, so that the frontend can display the data.

#### Acceptance Criteria

1. WHEN GET /api/portrait/overview is called, THE Portrait_Service SHALL return class overview data
2. WHEN GET /api/portrait/behavior-distribution is called with date range, THE Portrait_Service SHALL return behavior counts
3. WHEN GET /api/portrait/attention-trend is called with date range, THE Portrait_Service SHALL return daily attention rates
4. WHEN GET /api/portrait/warning-ranking is called, THE Portrait_Service SHALL return top warning behaviors
5. WHEN GET /api/portrait/student/{student_id} is called, THE Portrait_Service SHALL return student personal portrait data
6. WHEN GET /api/portrait/student/{student_id}/suggestions is called, THE Portrait_Service SHALL return improvement suggestions
7. WHEN GET /api/portrait/export is called, THE Portrait_Service SHALL return downloadable JSON data
8. IF authentication fails, THEN THE Portrait_Service SHALL return 401 status code
9. IF a student accesses another student's data, THEN THE Portrait_Service SHALL return 403 status code
