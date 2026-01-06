# Requirements Document

## Introduction

本功能旨在为课堂行为检测系统添加数据持久化能力，通过MySQL数据库存储每次检测的结果数据，包括学生行为记录、检测会话信息和预警统计。该数据库将支持历史数据查询、行为趋势分析和预警报告生成。

## Glossary

- **Detection_Database**: 检测数据库模块，负责与MySQL数据库的连接和操作
- **Detection_Session**: 检测会话，代表一次完整的检测过程（如一节课的检测）
- **Detection_Record**: 检测记录，单次检测帧中的所有行为检测结果
- **Behavior_Entry**: 行为条目，单个学生行为的检测数据
- **Alert_Statistics**: 预警统计，按会话或时间段聚合的预警数据
- **MySQL_Connector**: MySQL数据库连接器

## Database Configuration

- **Host**: localhost
- **Port**: 3306
- **User**: root
- **Password**: 123456
- **Database**: classroom_behavior_db

## Requirements

### Requirement 1: 数据库连接管理

**User Story:** 作为开发者，我希望系统能够安全可靠地连接MySQL数据库，以便存储和查询检测数据。

#### Acceptance Criteria

1. THE Detection_Database SHALL 使用配置参数（host、port、user、password、database）建立MySQL连接
2. WHEN 数据库连接失败 THEN THE Detection_Database SHALL 记录错误并抛出明确的异常信息
3. THE Detection_Database SHALL 支持连接池管理，避免频繁创建和销毁连接
4. WHEN 应用程序关闭 THEN THE Detection_Database SHALL 正确关闭所有数据库连接
5. THE Detection_Database SHALL 在首次连接时自动创建所需的数据库和表结构

### Requirement 2: 检测会话管理

**User Story:** 作为用户，我希望每次检测过程能够作为一个会话被记录，便于后续查询和分析。

#### Acceptance Criteria

1. WHEN 开始新的检测 THEN THE Detection_Database SHALL 创建新的Detection_Session记录，包含session_id、start_time、source_type（image/video/stream）、source_path
2. WHEN 检测结束 THEN THE Detection_Database SHALL 更新Detection_Session的end_time和total_frames字段
3. THE Detection_Database SHALL 支持按时间范围查询Detection_Session列表
4. THE Detection_Database SHALL 支持按session_id查询单个会话的详细信息
5. WHEN 删除Detection_Session THEN THE Detection_Database SHALL 级联删除关联的所有Detection_Record和Behavior_Entry

### Requirement 3: 检测记录存储

**User Story:** 作为用户，我希望每一帧的检测结果都能被保存，以便进行详细的行为分析。

#### Acceptance Criteria

1. WHEN 完成一帧检测 THEN THE Detection_Database SHALL 保存Detection_Record，包含record_id、session_id、frame_id、timestamp、alert_triggered、detection_count
2. THE Detection_Database SHALL 支持批量插入Detection_Record以提高性能
3. THE Detection_Database SHALL 支持按session_id查询所有Detection_Record
4. THE Detection_Database SHALL 支持按时间范围查询Detection_Record
5. WHEN 查询Detection_Record THEN THE Detection_Database SHALL 支持分页返回结果

### Requirement 4: 行为条目存储

**User Story:** 作为用户，我希望每个检测到的学生行为都能被详细记录，包括位置、类别和置信度。

#### Acceptance Criteria

1. WHEN 检测到学生行为 THEN THE Detection_Database SHALL 保存Behavior_Entry，包含entry_id、record_id、bbox_x1、bbox_y1、bbox_x2、bbox_y2、class_id、class_name、confidence、behavior_type、alert_level
2. THE Detection_Database SHALL 支持批量插入Behavior_Entry以提高性能
3. THE Detection_Database SHALL 支持按record_id查询所有Behavior_Entry
4. THE Detection_Database SHALL 支持按class_id或behavior_type筛选Behavior_Entry
5. THE Detection_Database SHALL 支持按alert_level筛选预警行为

### Requirement 5: 预警统计查询

**User Story:** 作为用户，我希望能够查询预警统计数据，了解课堂行为的整体情况。

#### Acceptance Criteria

1. THE Detection_Database SHALL 支持按session_id统计各类行为的出现次数
2. THE Detection_Database SHALL 支持按时间范围统计各预警级别的分布
3. THE Detection_Database SHALL 支持查询指定时间段内预警最频繁的行为类型
4. THE Detection_Database SHALL 支持生成会话级别的预警摘要报告
5. THE Detection_Database SHALL 支持导出统计数据为JSON格式

### Requirement 6: 用户角色管理

**User Story:** 作为系统管理员，我希望能够管理不同角色的用户，以便后期实现登录和权限控制功能。

#### Acceptance Criteria

1. THE Detection_Database SHALL 支持存储用户信息，包含user_id、username、password_hash、email、role、created_at、last_login
2. THE Detection_Database SHALL 支持以下用户角色：admin（管理员）、teacher（教师）、student（学生）、viewer（观察者）
3. WHEN 创建新用户 THEN THE Detection_Database SHALL 对密码进行加密存储（使用bcrypt或类似算法）
4. THE Detection_Database SHALL 支持按角色查询用户列表
5. THE Detection_Database SHALL 支持用户信息的增删改查操作
6. WHEN 用户登录成功 THEN THE Detection_Database SHALL 更新last_login时间戳
7. THE Detection_Database SHALL 支持用户与检测会话的关联，记录是哪个用户创建的检测会话

### Requirement 7: 权限配置

**User Story:** 作为系统管理员，我希望能够为不同角色配置不同的权限，控制数据访问范围。

#### Acceptance Criteria

1. THE Detection_Database SHALL 存储角色权限配置，包含role、permission_name、is_allowed
2. THE Detection_Database SHALL 支持以下权限类型：view_sessions（查看会话）、create_session（创建会话）、delete_session（删除会话）、view_statistics（查看统计）、manage_users（管理用户）、export_data（导出数据）
3. THE Detection_Database SHALL 为admin角色默认分配所有权限
4. THE Detection_Database SHALL 为teacher角色默认分配view_sessions、create_session、view_statistics、export_data权限
5. THE Detection_Database SHALL 为student角色默认分配view_sessions、view_statistics权限
6. THE Detection_Database SHALL 为viewer角色默认分配view_sessions权限
7. THE Detection_Database SHALL 支持动态修改角色权限配置

### Requirement 8: 课堂信息管理

**User Story:** 作为教师，我希望能够管理课堂信息，将检测数据与具体的课程、班级关联起来。

#### Acceptance Criteria

1. THE Detection_Database SHALL 存储课程信息，包含course_id、course_name、course_code、teacher_id、semester、description
2. THE Detection_Database SHALL 存储班级信息，包含class_id、class_name、grade、department、student_count
3. THE Detection_Database SHALL 存储课堂安排信息，包含schedule_id、course_id、class_id、classroom、weekday、start_time、end_time
4. THE Detection_Database SHALL 支持将Detection_Session与课堂安排关联
5. THE Detection_Database SHALL 支持按课程或班级查询相关的检测会话

### Requirement 9: 学生档案管理

**User Story:** 作为教师，我希望能够管理学生档案，追踪每个学生的课堂行为表现。

#### Acceptance Criteria

1. THE Detection_Database SHALL 存储学生档案，包含student_id、student_number、name、class_id、gender、enrollment_year
2. THE Detection_Database SHALL 支持将检测到的行为与具体学生关联（可选，需要人脸识别支持）
3. THE Detection_Database SHALL 支持按学生查询其历史行为记录
4. THE Detection_Database SHALL 支持生成学生个人行为分析报告
5. THE Detection_Database SHALL 支持按班级批量导入学生信息

### Requirement 10: 全景分析数据

**User Story:** 作为管理员，我希望能够进行全景分析，了解整体课堂行为趋势和模式。

#### Acceptance Criteria

1. THE Detection_Database SHALL 存储每日行为汇总数据，包含date、total_sessions、total_detections、behavior_distribution（JSON）、alert_distribution（JSON）
2. THE Detection_Database SHALL 存储课程行为汇总数据，包含course_id、period（周/月/学期）、avg_attention_rate、behavior_trends（JSON）
3. THE Detection_Database SHALL 存储班级行为汇总数据，包含class_id、period、avg_attention_rate、top_warning_behaviors（JSON）
4. THE Detection_Database SHALL 支持计算注意力指数（正常行为占比）
5. THE Detection_Database SHALL 支持按时间维度（日/周/月/学期）聚合分析数据
6. THE Detection_Database SHALL 支持跨课程、跨班级的对比分析查询
7. THE Detection_Database SHALL 支持生成全景分析仪表板所需的数据接口

### Requirement 11: 预警规则配置

**User Story:** 作为管理员，我希望能够配置预警规则，自定义预警触发条件。

#### Acceptance Criteria

1. THE Detection_Database SHALL 存储预警规则配置，包含rule_id、rule_name、behavior_type、threshold_count、time_window_seconds、alert_level、is_active
2. THE Detection_Database SHALL 支持配置连续预警触发条件（如连续N帧检测到睡觉行为）
3. THE Detection_Database SHALL 支持配置累计预警触发条件（如5分钟内交谈行为超过10次）
4. THE Detection_Database SHALL 存储预警事件记录，包含event_id、rule_id、session_id、triggered_at、behavior_count、is_resolved
5. THE Detection_Database SHALL 支持预警规则的启用/禁用

### Requirement 12: 数据完整性与错误处理

**User Story:** 作为开发者，我希望数据库操作能够保证数据完整性并妥善处理错误。

#### Acceptance Criteria

1. THE Detection_Database SHALL 使用事务确保批量操作的原子性
2. IF 数据库操作失败 THEN THE Detection_Database SHALL 回滚事务并记录错误日志
3. THE Detection_Database SHALL 对所有输入参数进行验证，防止SQL注入
4. IF 插入重复数据 THEN THE Detection_Database SHALL 根据配置选择更新或忽略
5. THE Detection_Database SHALL 支持配置日志级别（DEBUG、INFO、WARNING、ERROR）
6. THE Detection_Database SHALL 使用外键约束确保数据引用完整性
7. THE Detection_Database SHALL 支持定期清理过期数据（可配置保留天数）