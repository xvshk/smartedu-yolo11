# Implementation Plan: 学生检测数据库

## Overview

本实现计划将设计文档转化为可执行的编码任务，采用增量开发方式，从数据库连接层开始，逐步构建数据访问层和业务逻辑层。使用Python语言，基于mysql-connector-python和SQLAlchemy实现。

## Tasks

- [x] 1. 项目依赖与数据库配置
  - [x] 1.1 更新项目依赖
    - 在 `requirements.txt` 中添加 mysql-connector-python, sqlalchemy, bcrypt
    - _Requirements: 1.1_

  - [x] 1.2 创建数据库配置模块
    - 创建 `src/database/config.py`
    - 实现 DatabaseConfig 数据类，包含 host, port, user, password, database, pool_size 等配置
    - 默认配置：localhost:3306, root/123456, classroom_behavior_db
    - _Requirements: 1.1_

- [x] 2. 数据库连接层实现
  - [x] 2.1 实现DatabaseManager连接管理器
    - 创建 `src/database/manager.py`
    - 实现连接池管理（使用mysql.connector.pooling）
    - 实现 get_connection(), release_connection() 方法
    - 实现 execute(), query(), execute_many() 方法
    - 实现 transaction() 上下文管理器
    - _Requirements: 1.1, 1.3, 1.4, 12.1_

  - [x] 2.2 实现数据库初始化
    - 在 DatabaseManager 中实现 init_database() 方法
    - 自动创建数据库（如不存在）
    - 执行所有建表SQL语句
    - 插入默认权限配置
    - _Requirements: 1.5, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 2.3 编写DatabaseManager属性测试
    - **Property 9: 事务原子性**
    - **Property 10: SQL注入防护**
    - **Validates: Requirements 12.1, 12.2, 12.3**

- [x] 3. Checkpoint - 确保数据库连接层测试通过
  - 运行测试确保DatabaseManager模块正确
  - 如有问题请询问用户

- [x] 4. 检测数据仓库实现
  - [x] 4.1 实现DetectionRepository
    - 创建 `src/database/repositories/detection_repository.py`
    - 实现 Session CRUD: create_session(), update_session(), get_session(), list_sessions(), delete_session()
    - 实现 Record CRUD: create_record(), create_records_batch(), get_records_by_session()
    - 实现 Entry CRUD: create_entry(), create_entries_batch(), get_entries_by_record(), get_entries_by_behavior()
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 4.2 编写DetectionRepository属性测试
    - **Property 1: 数据CRUD往返一致性**
    - **Property 2: 级联删除完整性**
    - **Property 3: 批量插入数据完整性**
    - **Property 4: 时间范围查询正确性**
    - **Property 5: 分页查询完整性**
    - **Validates: Requirements 2.1-2.5, 3.1-3.5, 4.1-4.5**

- [x] 5. Checkpoint - 确保检测数据仓库测试通过
  - 运行测试确保DetectionRepository模块正确
  - 如有问题请询问用户

- [-] 6. 用户仓库实现
  - [x] 6.1 实现UserRepository
    - 创建 `src/database/repositories/user_repository.py`
    - 实现用户 CRUD: create_user(), get_user(), get_user_by_username(), update_user(), delete_user(), list_users()
    - 实现密码加密: 使用bcrypt进行密码哈希
    - 实现 verify_password() 密码验证
    - 实现 update_last_login() 更新登录时间
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 6.2 实现权限管理
    - 在 UserRepository 中实现 get_permissions(), set_permission(), has_permission()
    - _Requirements: 7.1, 7.2, 7.7_

  - [ ]* 6.3 编写UserRepository属性测试
    - **Property 6: 用户密码加密存储**
    - **Property 7: 用户角色权限一致性**
    - **Validates: Requirements 6.3, 7.1-7.7**

- [x] 7. Checkpoint - 确保用户仓库测试通过
  - 运行测试确保UserRepository模块正确
  - 如有问题请询问用户

- [x] 8. 课程与学生仓库实现
  - [x] 8.1 实现CourseRepository
    - 创建 `src/database/repositories/course_repository.py`
    - 实现课程 CRUD: create_course(), get_course(), list_courses(), update_course(), delete_course()
    - 实现班级 CRUD: create_class(), get_class(), list_classes()
    - 实现课堂安排 CRUD: create_schedule(), get_schedule(), list_schedules()
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 8.2 实现StudentRepository
    - 创建 `src/database/repositories/student_repository.py`
    - 实现学生 CRUD: create_student(), get_student(), get_student_by_number(), list_students(), update_student(), delete_student()
    - 实现批量导入: import_students_batch()
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

  - [ ]* 8.3 编写CourseRepository和StudentRepository属性测试
    - **Property 11: 外键引用完整性**
    - **Validates: Requirements 8.1-8.5, 9.1-9.5, 12.6**

- [x] 9. Checkpoint - 确保课程与学生仓库测试通过
  - 运行测试确保CourseRepository和StudentRepository模块正确
  - 如有问题请询问用户

- [x] 10. 分析仓库实现
  - [x] 10.1 实现AnalyticsRepository统计查询
    - 创建 `src/database/repositories/analytics_repository.py`
    - 实现 get_session_statistics() 会话统计
    - 实现 get_behavior_distribution() 行为分布统计
    - 实现 get_alert_distribution() 预警分布统计
    - 实现 get_top_warning_behaviors() 预警行为排名
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 10.2 实现汇总数据管理
    - 实现 save_daily_summary(), get_daily_summary(), get_daily_summaries()
    - 实现 save_course_summary(), get_course_summary()
    - 实现 save_class_summary(), get_class_summary()
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 10.3 实现注意力指数计算
    - 实现 calculate_attention_rate() 计算注意力指数
    - 实现 get_attention_trend() 获取注意力趋势
    - _Requirements: 10.4, 10.5_

  - [x] 10.4 实现预警规则管理
    - 实现 create_alert_rule(), get_alert_rules(), update_alert_rule()
    - 实现 create_alert_event(), get_alert_events(), resolve_alert_event()
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 10.5 编写AnalyticsRepository属性测试
    - **Property 8: 统计聚合正确性**
    - **Property 12: 注意力指数计算正确性**
    - **Validates: Requirements 5.1-5.5, 10.4**

- [x] 11. Checkpoint - 确保分析仓库测试通过
  - 运行测试确保AnalyticsRepository模块正确
  - 如有问题请询问用户

- [x] 12. 数据导出与集成
  - [x] 12.1 实现JSON导出功能
    - 在 AnalyticsRepository 中实现 export_to_json() 方法
    - 支持导出会话统计、行为分布、预警数据
    - _Requirements: 5.5_

  - [x] 12.2 创建数据库服务层
    - 创建 `src/database/services/detection_service.py`
    - 封装检测数据的存储流程，集成 AlertInterface
    - 实现 save_detection_result() 保存单帧检测结果
    - 实现 save_detection_batch() 批量保存检测结果
    - _Requirements: 2.1, 3.1, 4.1, 6.7_

  - [x] 12.3 创建数据库初始化脚本
    - 创建 `scripts/init_database.py`
    - 支持命令行参数配置数据库连接
    - 自动创建数据库和表结构
    - 创建默认管理员用户
    - _Requirements: 1.5_

- [x] 13. Final Checkpoint - 确保所有测试通过
  - 运行完整测试套件
  - 验证端到端流程
  - 如有问题请询问用户

## Notes

- 任务标记 `*` 为可选的属性测试任务，可跳过以加快MVP开发
- 每个任务引用具体的需求条款以确保可追溯性
- Checkpoint任务用于增量验证，确保每个模块正确后再继续
- 属性测试使用hypothesis库，每个测试运行至少100次迭代
- 单元测试和属性测试互补，共同确保代码正确性
- 测试使用独立的测试数据库 classroom_behavior_test_db
