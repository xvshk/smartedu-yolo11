"""
Module层接口定义
Repository interfaces for standardized data access patterns
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class IRepository(ABC):
    """基础Repository接口"""
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        """创建记录"""
        pass
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记录"""
        pass
    
    @abstractmethod
    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """更新记录"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """删除记录"""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """获取所有记录（分页）"""
        pass


class IDetectionRepository(IRepository):
    """检测数据Repository接口"""
    
    @abstractmethod
    def create_session(
        self,
        source_type: str,
        source_path: str = None,
        user_id: int = None,
        schedule_id: int = None
    ) -> int:
        """创建检测会话"""
        pass
    
    @abstractmethod
    def update_session(
        self,
        session_id: int,
        end_time: datetime = None,
        total_frames: int = None,
        status: str = None
    ) -> bool:
        """更新会话"""
        pass
    
    @abstractmethod
    def create_record(
        self,
        session_id: int,
        frame_id: int,
        timestamp: float,
        alert_triggered: bool = False,
        detection_count: int = 0
    ) -> int:
        """创建检测记录"""
        pass
    
    @abstractmethod
    def create_entry(
        self,
        record_id: int,
        bbox: List[float],
        class_id: int,
        class_name: str,
        confidence: float,
        behavior_type: str,
        alert_level: int = 0
    ) -> int:
        """创建行为条目"""
        pass
    
    @abstractmethod
    def get_records_by_session(
        self,
        session_id: int,
        limit: int = None,
        offset: int = None
    ) -> List[Dict[str, Any]]:
        """获取会话的检测记录"""
        pass
    
    @abstractmethod
    def get_entries_by_behavior(
        self,
        session_id: int,
        behavior_type: str = None,
        alert_level: int = None
    ) -> List[Dict[str, Any]]:
        """根据行为类型获取条目"""
        pass


class IUserRepository(IRepository):
    """用户Repository接口"""
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        pass
    
    @abstractmethod
    def update_password(self, user_id: int, password_hash: str) -> bool:
        """更新密码"""
        pass
    
    @abstractmethod
    def update_last_login(self, user_id: int, login_time: datetime) -> bool:
        """更新最后登录时间"""
        pass
    
    @abstractmethod
    def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索用户"""
        pass


class IStudentRepository(IRepository):
    """学生Repository接口"""
    
    @abstractmethod
    def get_by_student_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """根据学号获取学生"""
        pass
    
    @abstractmethod
    def get_by_class(self, class_id: int) -> List[Dict[str, Any]]:
        """获取班级学生"""
        pass
    
    @abstractmethod
    def update_profile(self, student_id: int, profile_data: Dict[str, Any]) -> bool:
        """更新学生档案"""
        pass


class ICourseRepository(IRepository):
    """课程Repository接口"""
    
    @abstractmethod
    def get_by_teacher(self, teacher_id: int) -> List[Dict[str, Any]]:
        """获取教师的课程"""
        pass
    
    @abstractmethod
    def get_active_courses(self) -> List[Dict[str, Any]]:
        """获取活跃课程"""
        pass
    
    @abstractmethod
    def update_schedule(self, course_id: int, schedule_data: Dict[str, Any]) -> bool:
        """更新课程安排"""
        pass


class IAnalyticsRepository(ABC):
    """分析数据Repository接口"""
    
    @abstractmethod
    def get_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """获取会话统计"""
        pass
    
    @abstractmethod
    def get_behavior_statistics(
        self,
        session_id: int = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> Dict[str, Any]:
        """获取行为统计"""
        pass
    
    @abstractmethod
    def get_alert_statistics(
        self,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> Dict[str, Any]:
        """获取预警统计"""
        pass
    
    @abstractmethod
    def export_session_to_json(self, session_id: int) -> str:
        """导出会话数据为JSON"""
        pass


class IRuleRepository(IRepository):
    """规则Repository接口"""
    
    @abstractmethod
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """获取活跃规则"""
        pass
    
    @abstractmethod
    def get_by_type(self, rule_type: str) -> List[Dict[str, Any]]:
        """根据类型获取规则"""
        pass
    
    @abstractmethod
    def activate_rule(self, rule_id: int) -> bool:
        """激活规则"""
        pass
    
    @abstractmethod
    def deactivate_rule(self, rule_id: int) -> bool:
        """停用规则"""
        pass