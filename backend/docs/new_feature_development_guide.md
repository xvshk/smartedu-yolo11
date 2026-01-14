# 新功能开发指导

## 概述

本指导文档帮助开发者在分层架构框架下正确开发新功能，确保代码符合架构规范并保持系统的可维护性。

## 开发流程

### 1. 需求分析和架构设计

在开始编码前，先分析功能需求并设计架构：

#### 1.1 功能分解
将功能按层级职责分解：

```
新功能：学生行为分析报告
├── Presentation Layer: 报告展示界面
├── Controller Layer: 报告API端点
├── Service Layer: 报告生成业务逻辑
├── Business Layer: 数据分析算法
├── Module Layer: 数据查询和存储
└── Foundation Layer: 报告格式化工具
```

#### 1.2 接口设计
先设计接口，再实现功能：

```python
# 1. 定义Service接口
class IReportService(ABC):
    @abstractmethod
    def generate_behavior_report(self, student_id: str, 
                               date_range: DateRange) -> ReportDTO:
        pass

# 2. 定义Repository接口
class IReportRepository(ABC):
    @abstractmethod
    def get_student_behaviors(self, student_id: str, 
                            date_range: DateRange) -> List[BehaviorRecord]:
        pass

# 3. 定义Business接口
class IBehaviorAnalyzer(ABC):
    @abstractmethod
    def analyze_behavior_patterns(self, 
                                behaviors: List[BehaviorRecord]) -> AnalysisResult:
        pass
```

### 2. 自下而上实现

按照依赖方向，从Foundation层开始实现：

#### 2.1 Foundation Layer - 基础工具
```python
# backend/foundation/utils/report_formatter.py
class ReportFormatter:
    """报告格式化工具"""
    
    @staticmethod
    def format_percentage(value: float) -> str:
        return f"{value:.1f}%"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

# backend/foundation/models/report_dto.py
@dataclass
class ReportDTO:
    student_id: str
    date_range: DateRange
    behavior_summary: Dict[str, int]
    analysis_result: AnalysisResult
    generated_at: datetime
```

#### 2.2 Module Layer - 数据访问
```python
# backend/module/repositories/report_repository.py
class ReportRepository(IReportRepository):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_student_behaviors(self, student_id: str, 
                            date_range: DateRange) -> List[BehaviorRecord]:
        query = """
        SELECT behavior_type, timestamp, confidence
        FROM detections 
        WHERE student_id = ? AND timestamp BETWEEN ? AND ?
        """
        cursor = self.db.execute(query, (
            student_id, 
            date_range.start, 
            date_range.end
        ))
        return [BehaviorRecord.from_row(row) for row in cursor.fetchall()]
    
    def save_report(self, report: ReportDTO) -> str:
        # 保存报告到数据库
        pass
```

#### 2.3 Business Layer - 算法实现
```python
# backend/business/behavior_analyzer.py
class BehaviorAnalyzer(IBehaviorAnalyzer):
    def __init__(self, config: BehaviorConfig):
        self.config = config
    
    def analyze_behavior_patterns(self, 
                                behaviors: List[BehaviorRecord]) -> AnalysisResult:
        # 行为模式分析算法
        attention_score = self._calculate_attention_score(behaviors)
        participation_score = self._calculate_participation_score(behaviors)
        warning_behaviors = self._identify_warning_behaviors(behaviors)
        
        return AnalysisResult(
            attention_score=attention_score,
            participation_score=participation_score,
            warning_behaviors=warning_behaviors,
            recommendations=self._generate_recommendations(behaviors)
        )
    
    def _calculate_attention_score(self, behaviors: List[BehaviorRecord]) -> float:
        # 专注度计算算法
        total_tim