# 课堂行为检测系统架构指导原则

## 概述

本文档定义了课堂行为检测系统的分层架构规范，确保代码的可维护性、可扩展性和团队协作效率。

## 分层架构概览

系统采用六层架构模式，每层都有明确的职责和依赖关系：

```
┌─────────────────┐
│  Presentation   │ ← 用户交互层（CLI/GUI/程序入口）
├─────────────────┤
│   Controller    │ ← HTTP路由和响应格式化
├─────────────────┤
│    Service      │ ← 业务流程编排和服务协调
├─────────────────┤
│    Business     │ ← 算法实现和ML流水线
├─────────────────┤
│     Module      │ ← 数据访问和存储抽象
├─────────────────┤
│   Foundation    │ ← 基础工具和通用功能
└─────────────────┘
```

## 层级职责定义

### 1. Presentation Layer (表现层)
**目录**: `backend/presentation/`

**职责**:
- CLI命令行界面实现
- GUI图形界面实现  
- 程序入口点和启动逻辑
- 用户输入验证和输出格式化

**允许依赖**: Service Layer, Foundation Layer

**禁止行为**:
- ❌ 直接调用Business Layer或Module Layer
- ❌ 包含业务逻辑
- ❌ 直接访问数据库

**示例代码**:

```python
# ✅ 正确：通过Service层访问业务功能
from backend.service.InterfaceService import IDetectionService


class DetectionCLI:
    def __init__(self, detection_service: IDetectionService):
        self.detection_service = detection_service

    def run_detection(self, video_path: str):
        result = self.detection_service.detect_behaviors(video_path)
        self.display_results(result)


# ❌ 错误：直接调用Business层
from backend.business.detection_pipeline import DetectionPipeline  # 违规！
```

### 2. Controller Layer (控制层)
**目录**: `backend/controller/`

**职责**:
- HTTP请求路由处理
- 请求参数验证和解析
- 响应格式化和状态码设置
- 异常处理和错误响应

**允许依赖**: Service Layer, Foundation Layer

**禁止行为**:
- ❌ 直接调用Business Layer或Module Layer
- ❌ 包含业务逻辑
- ❌ 直接访问数据库

**示例代码**:

```python
# ✅ 正确：Controller只处理HTTP相关逻辑
from flask import request, jsonify
from backend.service.InterfaceService import IDetectionService


class DetectionController:
    def __init__(self, detection_service: IDetectionService):
        self.detection_service = detection_service

    def detect_endpoint(self):
        video_path = request.json.get('video_path')
        if not video_path:
            return jsonify({'error': 'Missing video_path'}), 400

        result = self.detection_service.detect_behaviors(video_path)
        return jsonify(result), 200


# ❌ 错误：Controller包含业务逻辑
def detect_endpoint(self):
    # 这些业务逻辑应该在Service层！
    model = load_model('yolo11s.pt')  # 违规！
    predictions = model.predict(video_path)  # 违规！
```

### 3. Service Layer (服务层)
**目录**: `backend/service/`

**职责**:
- 业务流程编排和协调
- 跨模块业务逻辑整合
- 事务管理和一致性保证
- 外部服务集成

**允许依赖**: Business Layer, Module Layer, Foundation Layer

**核心文件**:
- `interfaces.py` - 服务接口定义
- `container.py` - 依赖注入容器
- `*_service.py` - 具体服务实现

**示例代码**:

```python
# ✅ 正确：Service层编排业务流程
from backend.service.InterfaceService import IDetectionService
from backend.business.interfaces import IDetectionPipeline
from backend.model.InterfaceModel import IDetectionRepository


class DetectionService(IDetectionService):
    def __init__(self,
                 pipeline: IDetectionPipeline,
                 repository: IDetectionRepository):
        self.pipeline = pipeline
        self.repository = repository

    def detect_behaviors(self, video_path: str) -> Dict:
        # 1. 业务流程编排
        results = self.pipeline.process_video(video_path)

        # 2. 数据持久化
        detection_id = self.repository.save_detection(results)

        # 3. 返回整合结果
        return {
            'detection_id': detection_id,
            'behaviors': results['behaviors'],
            'statistics': results['statistics']
        }
```

### 4. Business Layer (业务层)
**目录**: `backend/business/`

**职责**:
- 核心算法实现
- 机器学习模型训练和推理
- 业务规则和计算逻辑
- 领域特定的数据处理

**允许依赖**: Module Layer, Foundation Layer

**示例代码**:
```python
# ✅ 正确：Business层专注算法实现
from backend.business.interfaces import IDetectionPipeline
from backend.foundation.utils import Logger

class YOLODetectionPipeline(IDetectionPipeline):
    def __init__(self, model_path: str):
        self.model = self.load_model(model_path)
        self.logger = Logger()
    
    def process_video(self, video_path: str) -> Dict:
        # 纯算法逻辑
        frames = self.extract_frames(video_path)
        predictions = self.model.predict(frames)
        behaviors = self.post_process(predictions)
        
        return {
            'behaviors': behaviors,
            'confidence_scores': predictions.conf,
            'processing_time': self.get_processing_time()
        }
```

### 5. Module Layer (模块层)
**目录**: `backend/module/`

**职责**:
- 数据访问抽象（Repository模式）
- 数据模型定义
- 数据库操作封装
- 外部数据源集成

**允许依赖**: Foundation Layer

**核心文件**:
- `interfaces.py` - Repository接口定义
- `repositories/` - 具体Repository实现
- `models/` - 数据模型定义

**示例代码**:

```python
# ✅ 正确：Module层专注数据访问
from backend.model.InterfaceModel import IDetectionRepository
from backend.foundation.utils import get_database_connection


class DetectionRepository(IDetectionRepository):
    def __init__(self):
        self.db = get_database_connection()

    def save_detection(self, detection_data: Dict) -> str:
        # 纯数据访问逻辑
        query = """
        INSERT INTO detections (video_path, results, created_at)
        VALUES (?, ?, ?)
        """
        cursor = self.db.execute(query, (
            detection_data['video_path'],
            json.dumps(detection_data['results']),
            datetime.now()
        ))
        return cursor.lastrowid
```

### 6. Foundation Layer (基础层)
**目录**: `backend/foundation/`

**职责**:
- 通用工具函数
- 配置管理
- 日志记录
- 数据预处理工具
- 架构分析工具

**允许依赖**: 无（不依赖其他层）

**子模块**:
- `utils/` - 通用工具
- `config/` - 配置管理
- `data/` - 数据处理工具
- `analysis/` - 架构分析工具

## 依赖关系规则

### 允许的依赖方向
```
Presentation → Service → Business → Module → Foundation
     ↓           ↓         ↓         ↓
Foundation  Foundation Foundation Foundation
```

### 禁止的依赖模式

1. **反向依赖** - 下层不能依赖上层
   ```python
   # ❌ 错误：Foundation层依赖Service层
   from backend.service.DetectionService import DetectionService  # 违规！
   ```

2. **跨层调用** - 不能跳过中间层
   ```python
   # ❌ 错误：Presentation直接调用Business
   from backend.business.detection_pipeline import DetectionPipeline  # 违规！
   
   # ✅ 正确：通过Service层调用
   from backend.service.InterfaceService import IDetectionService
   ```

3. **循环依赖** - 任何层级都不能形成循环
   ```python
   # ❌ 错误：A依赖B，B又依赖A
   # service/a.py
   from backend.service.b import ServiceB  # 违规！
   
   # service/b.py  
   from backend.service.a import ServiceA  # 违规！
   ```

## 接口设计原则

### 1. 依赖倒置原则
高层模块不应该依赖低层模块，两者都应该依赖抽象。

```python
# ✅ 正确：依赖接口而不是具体实现
from backend.service.InterfaceService import IDetectionService


class DetectionController:
    def __init__(self, detection_service: IDetectionService):  # 依赖接口
        self.detection_service = detection_service


# ❌ 错误：依赖具体实现
from backend.service.DetectionService import DetectionService


class DetectionController:
    def __init__(self, detection_service: DetectionService):  # 依赖实现
        self.detection_service = detection_service
```

### 2. 接口命名约定
- 接口以 `I` 开头：`IDetectionService`, `IUserRepository`
- 实现类去掉 `I` 前缀：`DetectionService`, `UserRepository`

### 3. 接口定义示例
```python
# service/InterfaceService.py
from abc import ABC, abstractmethod
from typing import Dict, List

class IDetectionService(ABC):
    @abstractmethod
    def detect_behaviors(self, video_path: str) -> Dict:
        """检测视频中的行为"""
        pass
    
    @abstractmethod
    def get_detection_history(self, user_id: str) -> List[Dict]:
        """获取检测历史"""
        pass
```

## 错误处理模式

### 1. 分层错误处理
每层都应该处理自己职责范围内的错误：

```python
# Controller层：处理HTTP相关错误
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({'error': str(e)}), 400

# Service层：处理业务逻辑错误
class DetectionService:
    def detect_behaviors(self, video_path: str):
        try:
            return self.pipeline.process_video(video_path)
        except ModelLoadError as e:
            raise ServiceError(f"Detection failed: {e}")

# Module层：处理数据访问错误
class DetectionRepository:
    def save_detection(self, data):
        try:
            return self.db.insert(data)
        except DatabaseError as e:
            raise RepositoryError(f"Save failed: {e}")
```

## 测试策略

### 1. 单元测试
每层都应该有独立的单元测试：

```python
# 测试Service层（使用Mock）
def test_detection_service():
    # Arrange
    mock_pipeline = Mock(spec=IDetectionPipeline)
    mock_repository = Mock(spec=IDetectionRepository)
    service = DetectionService(mock_pipeline, mock_repository)
    
    # Act
    result = service.detect_behaviors("test.mp4")
    
    # Assert
    mock_pipeline.process_video.assert_called_once_with("test.mp4")
    mock_repository.save_detection.assert_called_once()
```

### 2. 集成测试
测试层间交互：

```python
def test_detection_flow_integration():
    # 测试从Controller到Repository的完整流程
    container = ServiceContainer()
    controller = DetectionController(container.get_detection_service())
    
    with app.test_client() as client:
        response = client.post('/detect', json={'video_path': 'test.mp4'})
        assert response.status_code == 200
```

## 重构指导

### 1. 识别违规代码
使用架构分析工具识别违规：

```bash
python -m backend.foundation.analysis.compliance_checker
```

### 2. 重构步骤

**步骤1：提取业务逻辑**
```python
# 重构前：Controller包含业务逻辑
class DetectionController:
    def detect(self):
        model = load_model()  # 业务逻辑
        result = model.predict()  # 业务逻辑
        return jsonify(result)

# 重构后：业务逻辑移到Service层
class DetectionController:
    def detect(self):
        result = self.detection_service.detect_behaviors()
        return jsonify(result)
```

**步骤2：引入接口**

```python
# 重构前：直接依赖实现
from backend.service.DetectionService import DetectionService

# 重构后：依赖接口
from backend.service.InterfaceService import IDetectionService
```

**步骤3：使用依赖注入**
```python
# 重构前：硬编码依赖
class DetectionService:
    def __init__(self):
        self.repository = DetectionRepository()  # 硬编码

# 重构后：依赖注入
class DetectionService:
    def __init__(self, repository: IDetectionRepository):
        self.repository = repository  # 注入
```

## 代码审查检查清单

### ✅ 架构合规性检查
- [ ] 每个文件都在正确的层级目录中
- [ ] 导入语句符合依赖方向规则
- [ ] 没有跨层调用（跳过中间层）
- [ ] 没有反向依赖（下层依赖上层）
- [ ] 没有循环依赖

### ✅ 接口设计检查
- [ ] 层间调用使用接口而不是具体实现
- [ ] 接口命名符合约定（I前缀）
- [ ] 接口定义清晰，职责单一
- [ ] 实现类正确实现接口

### ✅ 职责分离检查
- [ ] Controller只处理HTTP相关逻辑
- [ ] Service层包含业务流程编排
- [ ] Business层专注算法实现
- [ ] Module层只处理数据访问
- [ ] Foundation层只包含通用工具

### ✅ 错误处理检查
- [ ] 每层都有适当的错误处理
- [ ] 异常类型符合层级职责
- [ ] 错误信息对上层有意义

## 常见问题和解决方案

### Q1: 如何处理跨多个Service的业务流程？
**A**: 创建协调Service或使用事件驱动模式：

```python
class WorkflowService:
    def __init__(self, detection_service: IDetectionService, 
                 alert_service: IAlertService):
        self.detection_service = detection_service
        self.alert_service = alert_service
    
    def process_video_with_alerts(self, video_path: str):
        # 协调多个服务
        detection_result = self.detection_service.detect_behaviors(video_path)
        if detection_result['has_warnings']:
            self.alert_service.send_alert(detection_result)
```

### Q2: Foundation层可以访问数据库吗？
**A**: 不可以。Foundation层应该只提供通用工具，数据库访问应该在Module层：

```python
# ❌ 错误：Foundation层直接访问数据库
# foundation/utils/db_helper.py
def save_log_to_db(message):
    db.execute("INSERT INTO logs ...")  # 违规！

# ✅ 正确：Foundation层提供抽象，Module层实现
# foundation/interfaces/logger.py
class ILogRepository(ABC):
    @abstractmethod
    def save_log(self, message: str): pass

# model/repositories/log_repository.py
class LogRepository(ILogRepository):
    def save_log(self, message: str):
        self.db.execute("INSERT INTO logs ...")
```

### Q3: 如何在不同层之间传递复杂数据？
**A**: 使用数据传输对象（DTO）和领域模型：

```python
# foundation/models/dto.py
@dataclass
class DetectionResultDTO:
    video_path: str
    behaviors: List[BehaviorDTO]
    statistics: StatisticsDTO

# service层使用DTO在层间传递数据
class DetectionService:
    def detect_behaviors(self, video_path: str) -> DetectionResultDTO:
        # 业务逻辑处理
        return DetectionResultDTO(...)
```

## 总结

遵循这些架构指导原则将帮助团队：

1. **提高代码质量** - 清晰的职责分离和依赖管理
2. **增强可维护性** - 模块化设计便于修改和扩展
3. **促进团队协作** - 统一的架构规范减少沟通成本
4. **简化测试** - 接口抽象使单元测试更容易
5. **支持持续重构** - 自动化工具帮助识别和修复违规

定期运行架构合规性检查，持续改进代码质量：

```bash
# 运行完整架构分析
python -m backend.foundation.analysis.compliance_checker

# 检查层间依赖
python -m backend.foundation.analysis.layer_dependency_checker

# 验证接口使用
python -m backend.foundation.analysis.interface_communication_checker
```