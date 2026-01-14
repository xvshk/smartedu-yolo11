# 架构违规防范指南

## 概述

本指南帮助开发者识别、避免和修复常见的架构违规问题，确保代码符合分层架构规范。

## 常见违规类型和解决方案

### 1. 跨层调用违规 (Cross-Layer Call Violations)

#### 问题描述
上层模块直接调用非相邻的下层模块，跳过了中间层。

#### 常见场景
```python
# ❌ 违规：Presentation层直接调用Business层
# backend/presentation/cli/detection_cli.py
from backend.business.detection_pipeline import DetectionPipeline  # 违规！

class DetectionCLI:
    def run_detection(self):
        pipeline = DetectionPipeline()  # 跳过了Service层
        result = pipeline.process_video("video.mp4")
```

#### 解决方案
通过中间层（Service层）进行调用：

```python
# ✅ 正确：通过Service层调用
# backend/presentation/cli/detection_cli.py
from backend.service.InterfaceService import IDetectionService


class DetectionCLI:
    def __init__(self, detection_service: IDetectionService):
        self.detection_service = detection_service

    def run_detection(self):
        result = self.detection_service.detect_behaviors("video.mp4")
```

#### 重构步骤
1. 识别跨层调用的代码
2. 在Service层创建相应的业务方法
3. 更新上层代码使用Service接口
4. 移除直接的跨层导入

### 2. 直接数据库访问违规 (Direct Database Access)

#### 问题描述
Controller层直接访问数据库，绕过了Repository模式。

#### 常见场景
```python
# ❌ 违规：Controller直接访问数据库
# backend/controller/DashboardController.py
import sqlite3

class DashboardController:
    def get_statistics(self):
        conn = sqlite3.connect('database.db')  # 违规！
        cursor = conn.execute("SELECT * FROM detections")  # 违规！
        results = cursor.fetchall()
        return jsonify(results)
```

#### 解决方案
使用Repository模式和Service层：

```python
# ✅ 正确：通过Service和Repository访问数据
# backend/controller/DashboardController.py
from backend.service.InterfaceService import IDashboardService


class DashboardController:
    def __init__(self, dashboard_service: IDashboardService):
        self.dashboard_service = dashboard_service

    def get_statistics(self):
        stats = self.dashboard_service.get_dashboard_statistics()
        return jsonify(stats)


# backend/service/dashboard_service.py
class DashboardService(IDashboardService):
    def __init__(self, detection_repository: IDetectionRepository):
        self.detection_repository = detection_repository

    def get_dashboard_statistics(self):
        return self.detection_repository.get_statistics()


# backend/model/repositories/Detection_repositoryModel.py
class DetectionRepository(IDetectionRepository):
    def get_statistics(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.execute("SELECT * FROM detections")
        return cursor.fetchall()
```

#### 重构步骤
1. 在Module层创建Repository接口和实现
2. 在Service层创建业务方法
3. 更新Controller使用Service接口
4. 移除Controller中的数据库访问代码

### 3. 业务逻辑在Controller中 (Business Logic in Controller)

#### 问题描述
Controller包含业务逻辑，违反了单一职责原则。

#### 常见场景
```python
# ❌ 违规：Controller包含业务逻辑
# backend/controller/DetectionController.py
class DetectionController:
    def detect_behaviors(self):
        video_path = request.json['video_path']
        
        # 这些都是业务逻辑，不应该在Controller中！
        model = YOLO('yolo11s.pt')  # 违规！
        results = model.predict(video_path)  # 违规！
        
        # 复杂的数据处理逻辑
        behaviors = []
        for result in results:
            if result.conf > 0.5:  # 违规！
                behavior = {
                    'class': result.cls,
                    'confidence': result.conf,
                    'bbox': result.bbox
                }
                behaviors.append(behavior)
        
        return jsonify({'behaviors': behaviors})
```

#### 解决方案
将业务逻辑移到Service和Business层：

```python
# ✅ 正确：Controller只处理HTTP逻辑
# backend/controller/DetectionController.py
class DetectionController:
    def __init__(self, detection_service: IDetectionService):
        self.detection_service = detection_service
    
    def detect_behaviors(self):
        video_path = request.json.get('video_path')
        if not video_path:
            return jsonify({'error': 'Missing video_path'}), 400
        
        try:
            result = self.detection_service.detect_behaviors(video_path)
            return jsonify(result), 200
        except ServiceError as e:
            return jsonify({'error': str(e)}), 500

# ✅ 业务逻辑在Service层
# backend/service/DetectionService.py
class DetectionService(IDetectionService):
    def __init__(self, detection_pipeline: IDetectionPipeline):
        self.detection_pipeline = detection_pipeline
    
    def detect_behaviors(self, video_path: str) -> Dict:
        return self.detection_pipeline.process_video(video_path)

# ✅ 算法实现在Business层
# backend/business/detection_pipeline.py
class YOLODetectionPipeline(IDetectionPipeline):
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
    
    def process_video(self, video_path: str) -> Dict:
        results = self.model.predict(video_path)
        behaviors = self._extract_behaviors(results)
        return {'behaviors': behaviors}
    
    def _extract_behaviors(self, results):
        behaviors = []
        for result in results:
            if result.conf > self.confidence_threshold:
                behavior = {
                    'class': result.cls,
                    'confidence': result.conf,
                    'bbox': result.bbox
                }
                behaviors.append(behavior)
        return behaviors
```

### 4. 反向依赖违规 (Reverse Dependency)

#### 问题描述
下层模块依赖上层模块，违反了依赖方向原则。

#### 常见场景

```python
# ❌ 违规：Foundation层依赖Service层
# backend/foundation/utils/logger.py
from backend.service.NotificationService import NotificationService  # 违规！


class Logger:
    def __init__(self):
        self.notification_service = NotificationService()  # 违规！

    def log_error(self, message):
        print(f"ERROR: {message}")
        # 错误：Foundation层不应该调用Service层
        self.notification_service.send_alert(message)  # 违规！
```

#### 解决方案
使用依赖注入和接口抽象：

```python
# ✅ 正确：使用接口和依赖注入
# backend/foundation/interfaces/logger.py
from abc import ABC, abstractmethod

class IAlertHandler(ABC):
    @abstractmethod
    def handle_alert(self, message: str): pass

# backend/foundation/utils/logger.py
class Logger:
    def __init__(self, alert_handler: Optional[IAlertHandler] = None):
        self.alert_handler = alert_handler
    
    def log_error(self, message):
        print(f"ERROR: {message}")
        if self.alert_handler:
            self.alert_handler.handle_alert(message)

# ✅ Service层实现接口
# backend/service/alert_handler.py
class ServiceAlertHandler(IAlertHandler):
    def __init__(self, notification_service: INotificationService):
        self.notification_service = notification_service
    
    def handle_alert(self, message: str):
        self.notification_service.send_alert(message)
```

### 5. 循环依赖违规 (Circular Dependencies)

#### 问题描述
两个或多个模块相互依赖，形成循环。

#### 常见场景

```python
# ❌ 违规：循环依赖
# backend/service/DetectionService.py
from backend.service.AlertService import AlertService  # A依赖B


class DetectionService:
    def __init__(self):
        self.alert_service = AlertService()


# backend/service/AlertService.py
from backend.service.DetectionService import DetectionService  # B依赖A


class AlertService:
    def __init__(self):
        self.detection_service = DetectionService()  # 循环！
```

#### 解决方案
使用接口抽象和依赖注入：

```python
# ✅ 正确：通过接口打破循环依赖
# backend/service/InterfaceService.py
class IDetectionService(ABC):
    @abstractmethod
    def get_latest_detection(self) -> Dict: pass

class IAlertService(ABC):
    @abstractmethod
    def send_alert(self, message: str): pass

# backend/service/DetectionService.py
class DetectionService(IDetectionService):
    def __init__(self, alert_service: IAlertService):  # 依赖接口
        self.alert_service = alert_service

# backend/service/AlertService.py
class AlertService(IAlertService):
    def __init__(self, detection_service: IDetectionService):  # 依赖接口
        self.detection_service = detection_service

# backend/service/ContainerService.py - 依赖注入容器解决循环
class ServiceContainer:
    def __init__(self):
        self._detection_service = None
        self._alert_service = None
    
    def get_detection_service(self) -> IDetectionService:
        if not self._detection_service:
            self._detection_service = DetectionService(self.get_alert_service())
        return self._detection_service
    
    def get_alert_service(self) -> IAlertService:
        if not self._alert_service:
            self._alert_service = AlertService(self.get_detection_service())
        return self._alert_service
```

## 违规检测和修复工具

### 1. 自动化检测
使用架构分析工具定期检查：

```bash
# 运行完整合规性检查
python -m backend.foundation.analysis.compliance_checker

# 检查特定违规类型
python -m backend.foundation.analysis.layer_dependency_checker
python -m backend.foundation.analysis.interface_communication_checker
```

### 2. IDE集成
配置IDE警告规则：

```python
# .pylintrc 配置示例
[MESSAGES CONTROL]
disable=
    import-error,
    
# 自定义规则检查跨层导入
[CUSTOM-RULES]
forbidden-imports=
    backend.presentation.*:backend.business.*,
    backend.presentation.*:backend.module.*,
    backend.controller.*:backend.business.*,
    backend.controller.*:backend.module.*
```

### 3. Git Hook集成
在提交前自动检查：

```bash
#!/bin/sh
# .git/hooks/pre-commit
echo "Running architecture compliance check..."
python -m backend.foundation.analysis.compliance_checker
if [ $? -ne 0 ]; then
    echo "Architecture violations detected. Please fix before committing."
    exit 1
fi
```

## 重构最佳实践

### 1. 渐进式重构
不要一次性重构整个系统，采用渐进式方法：

```python
# 步骤1：保持原有代码，添加新的Service层
class DetectionController:
    def __init__(self):
        # 保持原有实现
        self.old_implementation = True
        # 添加新的Service依赖
        self.detection_service = None
    
    def detect_behaviors(self):
        if self.detection_service:
            # 使用新的Service层
            return self.detection_service.detect_behaviors()
        else:
            # 保持原有逻辑（标记为待重构）
            # TODO: 重构为使用Service层
            return self._old_detect_behaviors()

# 步骤2：逐步迁移到新实现
# 步骤3：移除旧代码
```

### 2. 接口优先设计
在重构时，先定义接口：

```python
# 1. 先定义接口
class IDetectionService(ABC):
    @abstractmethod
    def detect_behaviors(self, video_path: str) -> Dict: pass

# 2. 创建实现
class DetectionService(IDetectionService):
    def detect_behaviors(self, video_path: str) -> Dict:
        # 实现逻辑
        pass

# 3. 更新调用方使用接口
class DetectionController:
    def __init__(self, detection_service: IDetectionService):  # 使用接口
        self.detection_service = detection_service
```

### 3. 测试驱动重构
在重构过程中保持测试覆盖：

```python
# 重构前：为现有代码编写测试
def test_detection_controller_original():
    controller = DetectionController()
    result = controller.detect_behaviors()
    assert result is not None

# 重构中：为新接口编写测试
def test_detection_service_interface():
    mock_service = Mock(spec=IDetectionService)
    controller = DetectionController(mock_service)
    controller.detect_behaviors()
    mock_service.detect_behaviors.assert_called_once()

# 重构后：验证行为一致性
def test_refactored_behavior_consistency():
    # 确保重构后的行为与原来一致
    pass
```

## 代码审查检查清单

### 🔍 导入语句检查
- [ ] 没有跨层导入（如Presentation直接导入Business）
- [ ] 没有反向导入（如Foundation导入Service）
- [ ] 使用接口而不是具体实现类
- [ ] 导入路径符合层级结构

### 🔍 类职责检查
- [ ] Controller只包含HTTP处理逻辑
- [ ] Service包含业务流程编排
- [ ] Business专注算法和计算逻辑
- [ ] Repository只处理数据访问
- [ ] Foundation只包含通用工具

### 🔍 依赖注入检查
- [ ] 构造函数接收接口参数
- [ ] 没有在类内部直接实例化依赖
- [ ] 使用依赖注入容器管理对象生命周期

### 🔍 错误处理检查
- [ ] 每层都有适当的异常处理
- [ ] 异常类型符合层级职责
- [ ] 不会泄露下层实现细节

## 常见问题解答

### Q: 如何处理需要跨多层的数据传递？
**A**: 使用数据传输对象（DTO）：

```python
# 定义DTO在Foundation层
@dataclass
class DetectionResultDTO:
    behaviors: List[BehaviorDTO]
    statistics: StatisticsDTO
    metadata: MetadataDTO

# 各层使用相同的DTO
class DetectionService:
    def detect_behaviors(self) -> DetectionResultDTO:
        # Service层处理
        return DetectionResultDTO(...)

class DetectionController:
    def detect_endpoint(self):
        result = self.detection_service.detect_behaviors()
        return jsonify(asdict(result))  # DTO转JSON
```

### Q: Foundation层可以定义业务相关的工具吗？
**A**: 可以，但必须是通用的、无业务逻辑的工具：

```python
# ✅ 正确：通用的行为配置工具
# backend/foundation/config/behavior_config.py
class BehaviorConfig:
    CLASSES = {0: 'handrise', 1: 'read', 2: 'write'}  # 配置数据，无逻辑

# ❌ 错误：包含业务逻辑的工具
# backend/foundation/utils/behavior_analyzer.py
def analyze_behavior_patterns(detections):
    # 这是业务逻辑，应该在Business层！
    if len(detections) > 10:
        return "high_activity"
```

### Q: 如何在不违反架构的情况下共享代码？
**A**: 将共享代码放在Foundation层，或使用接口抽象：

```python
# ✅ 方案1：共享工具放在Foundation层
# backend/foundation/utils/video_processor.py
class VideoProcessor:
    @staticmethod
    def extract_frames(video_path: str) -> List[np.ndarray]:
        # 通用视频处理工具
        pass

# ✅ 方案2：使用接口抽象共享行为
# backend/foundation/interfaces/processor.py
class IVideoProcessor(ABC):
    @abstractmethod
    def extract_frames(self, video_path: str) -> List[np.ndarray]: pass

# 各层实现自己的处理器
class BusinessVideoProcessor(IVideoProcessor):
    def extract_frames(self, video_path: str) -> List[np.ndarray]:
        # Business层的实现
        pass
```

## 总结

遵循这些违规防范指南将帮助你：

1. **避免常见架构问题** - 提前识别和预防违规模式
2. **提高代码质量** - 保持清晰的职责分离
3. **简化维护工作** - 减少因架构混乱导致的bug
4. **促进团队协作** - 统一的架构规范提高开发效率

记住：**好的架构不是一蹴而就的，需要持续的关注和改进**。定期运行架构检查工具，及时发现和修复违规问题。