# 机器学习模块删除设计文档

## 概述

本文档详细设计了删除系统中前后端机器学习功能以及相关数据库组件的实施方案，但保留MLflow追踪功能。删除操作将分阶段进行，确保系统稳定性和数据安全。

## 架构

### 当前ML组件架构

```
系统架构 (删除前)
├── 前端
│   ├── MLDashboard.vue (删除)
│   ├── api/index.js (清理ML部分)
│   └── 路由配置 (移除ML路由)
├── 后端API
│   ├── ml.py (完全删除)
│   └── __init__.py (移除ML蓝图)
├── 服务层
│   ├── ml_engine.py (删除)
│   ├── backend/ml/risk_predictor.py (删除)
│   ├── backend/ml/anomaly_detector.py (删除)
│   └── backend/ml/mlflow_tracker.py (保留)
├── 数据库
│   ├── ml_models 表 (删除)
│   ├── ml_experiments 表 (删除)
│   └── ml_runs 表 (删除)
└── 文件系统
    └── runs/mlflow/ (保留)
```

### 删除后架构

```
系统架构 (删除后)
├── 前端
│   ├── Detection.vue (保留)
│   ├── Alert.vue (保留)
│   ├── Portrait.vue (保留)
│   └── api/index.js (仅保留核心API)
├── 后端API
│   ├── detection.py (保留)
│   ├── alert.py (保留)
│   └── portrait.py (保留)
├── 服务层
│   ├── detection_service.py (保留)
│   ├── alert_service.py (保留)
│   ├── portrait_service.py (保留)
│   └── backend/ml/mlflow_tracker.py (保留)
├── 数据库
│   ├── detection_sessions (保留)
│   ├── detection_entries (保留)
│   ├── alerts (保留)
│   └── users (保留)
└── 文件系统
    └── runs/mlflow/ (保留)
```

## 组件和接口

### 删除的文件和目录

#### 后端文件
- `backend/api/ml.py` - ML API接口
- `backend/services/ml_engine.py` - ML引擎服务
- `backend/ml/risk_predictor.py` - 风险预测器
- `backend/ml/anomaly_detector.py` - 异常检测器

#### 保留的文件
- `backend/ml/mlflow_tracker.py` - MLflow追踪器（保留）
- `backend/ml/__init__.py` - 模块初始化文件（保留）

#### 前端文件
- `frontend/src/views/MLDashboard.vue` - ML仪表板界面

#### 数据和配置文件
- ML相关的训练依赖包（scikit-learn等）

#### 保留的文件和配置
- `runs/mlflow/` - MLflow实验数据目录（保留）
- MLflow相关的环境变量配置（保留）
- mlflow依赖包（保留）

### 修改的文件

#### 后端修改
- `backend/api/__init__.py` - 移除ML蓝图注册
- `backend/app.py` - 移除ML相关初始化
- `requirements.txt` - 移除ML依赖包

#### 前端修改
- `frontend/src/api/index.js` - 移除ML API方法
- `frontend/src/router/index.js` - 移除ML路由
- `frontend/src/views/Dashboard.vue` - 移除ML相关链接

#### 数据库修改
- 删除ML相关数据表
- 更新数据库迁移脚本

## 数据模型

### 需要删除的数据表

```sql
-- 机器学习模型表
DROP TABLE IF EXISTS ml_models;

-- 机器学习实验表  
DROP TABLE IF EXISTS ml_experiments;

-- 机器学习运行记录表
DROP TABLE IF EXISTS ml_runs;

-- 模型预测结果表
DROP TABLE IF EXISTS model_predictions;

-- MLflow相关表（如果存在）
DROP TABLE IF EXISTS mlflow_experiments;
DROP TABLE IF EXISTS mlflow_runs;
DROP TABLE IF EXISTS mlflow_metrics;
DROP TABLE IF EXISTS mlflow_params;
```

### 保留的核心数据表

```sql
-- 检测会话表 (保留)
detection_sessions
├── session_id (主键)
├── start_time
├── end_time
├── source_type
└── metadata

-- 检测条目表 (保留)
detection_entries
├── entry_id (主键)
├── session_id (外键)
├── class_name
├── confidence
├── behavior_type
└── timestamp

-- 预警表 (保留)
alerts
├── alert_id (主键)
├── session_id (外键)
├── alert_type
├── severity
└── created_at

-- 用户表 (保留)
users
├── user_id (主键)
├── username
├── email
└── role
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式声明。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: ML功能完全移除
*对于任何* ML相关的API请求，系统应该返回404错误，表明这些功能已被完全移除
**验证: 需求 1.1, 1.2**

### 属性 2: 核心功能保持完整
*对于任何* 核心检测功能的请求，系统应该继续正常工作，不受ML模块删除的影响
**验证: 需求 8.1, 8.2, 8.3**

### 属性 3: 数据库一致性
*对于任何* 数据库查询，系统不应尝试访问已删除的ML相关表
**验证: 需求 4.1, 4.2, 4.3, 4.4**

### 属性 4: 系统启动稳定性
*对于任何* 系统启动过程，不应出现ML相关的错误或警告
**验证: 需求 2.3, 10.2**

### 属性 5: 前端界面一致性
*对于任何* 前端页面访问，用户不应看到任何ML功能的入口或残留界面
**验证: 需求 5.2, 5.3, 5.4**

## 错误处理

### ML API访问错误处理
- 返回404状态码和清晰的错误消息
- 记录访问尝试日志用于监控
- 提供替代功能建议（如果适用）

### 数据库访问错误处理
- 捕获并处理ML表不存在的错误
- 提供优雅的降级处理
- 记录错误日志但不影响核心功能

### 前端路由错误处理
- ML相关路由重定向到主页面
- 显示友好的"功能已移除"消息
- 更新导航菜单移除ML选项

## 测试策略

### 删除验证测试
- **单元测试**: 验证ML相关代码已完全移除
- **集成测试**: 验证系统在没有ML组件的情况下正常工作
- **API测试**: 确认ML API返回404错误
- **数据库测试**: 验证ML表已删除且不影响其他功能

### 核心功能回归测试
- **检测功能测试**: 图片和视频检测正常工作
- **预警功能测试**: 预警规则和通知正常工作
- **用户界面测试**: 所有保留的界面功能正常
- **性能测试**: 系统性能保持或改善

### 数据完整性测试
- **备份验证**: 确认ML数据已正确备份
- **迁移测试**: 验证数据库迁移脚本正确执行
- **回滚测试**: 验证回滚方案可行（如果需要）

## 实施阶段

### 阶段 1: 准备和备份
1. 创建ML相关数据的完整备份
2. 记录当前ML功能的使用情况
3. 通知用户即将进行的更改

### 阶段 2: 前端清理
1. 删除MLDashboard.vue文件
2. 更新路由配置移除ML路由
3. 清理API调用和导航菜单
4. 测试前端功能完整性

### 阶段 3: 后端API清理
1. 删除ml.py API文件
2. 更新蓝图注册
3. 清理相关服务依赖
4. 测试API功能

### 阶段 4: 服务层清理
1. 删除ml_engine.py和backend/ml/目录
2. 更新其他服务的ML依赖
3. 清理配置文件
4. 测试服务层功能

### 阶段 5: 数据库清理
1. 执行数据库备份
2. 删除ML相关表
3. 更新数据库迁移脚本
4. 验证数据库完整性

### 阶段 6: 依赖和配置清理
1. 更新requirements.txt
2. 清理环境变量配置
3. 删除MLflow相关文件
4. 更新文档

### 阶段 7: 测试和验证
1. 执行完整的回归测试
2. 验证系统性能
3. 确认所有ML功能已移除
4. 用户验收测试

## 回滚计划

### 数据恢复
- 从备份恢复ML相关数据表
- 恢复MLflow实验数据
- 恢复配置文件

### 代码恢复
- 从Git历史恢复删除的文件
- 重新注册ML蓝图和路由
- 恢复前端ML界面

### 依赖恢复
- 重新安装ML相关Python包
- 恢复环境变量配置
- 重启相关服务

## 监控和维护

### 删除后监控
- 监控404错误日志中的ML API访问尝试
- 监控系统性能改善情况
- 监控用户反馈和问题报告

### 长期维护
- 定期清理残留的ML相关日志
- 更新系统文档保持同步
- 考虑是否需要添加替代功能