"""
Service层接口定义
定义清晰的service接口，支持依赖注入和测试
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime


class IDetectionService(ABC):
    """检测服务接口"""
    
    @abstractmethod
    def detect_image(self, image: np.ndarray) -> Tuple[np.ndarray, Any]:
        """
        检测单张图片
        
        Args:
            image: OpenCV格式的图片 (BGR)
            
        Returns:
            (标注后的图片, 检测结果)
        """
        pass
    
    @abstractmethod
    def detect_base64(self, base64_image: str) -> Tuple[str, Any]:
        """
        检测Base64编码的图片
        
        Args:
            base64_image: Base64编码的图片字符串
            
        Returns:
            (Base64编码的标注图片, 检测结果)
        """
        pass
    
    @abstractmethod
    def start_session(
        self,
        source_type: str,
        source_path: str = None,
        user_id: int = None,
        schedule_id: int = None
    ) -> int:
        """开始新的检测会话"""
        pass
    
    @abstractmethod
    def end_session(self, status: str = 'completed') -> Dict[str, Any]:
        """结束当前检测会话"""
        pass
    
    @abstractmethod
    def save_detection_result(
        self,
        frame_id: int,
        timestamp: float,
        detections: List[Dict[str, Any]],
        alert_triggered: bool = False
    ) -> int:
        """保存检测结果"""
        pass
    
    @abstractmethod
    def get_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """获取会话统计"""
        pass


class IAuthService(ABC):
    """认证服务接口"""
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        pass
    
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """创建用户"""
        pass
    
    @abstractmethod
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """更新用户信息"""
        pass
    
    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        pass
    
    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        pass


class IRuleEngineService(ABC):
    """规则引擎服务接口"""
    
    @abstractmethod
    def evaluate_alert_rules(self, detection_result: Any) -> Dict[str, Any]:
        """评估预警规则"""
        pass
    
    @abstractmethod
    def create_rule(self, rule_data: Dict[str, Any]) -> int:
        """创建规则"""
        pass
    
    @abstractmethod
    def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """更新规则"""
        pass
    
    @abstractmethod
    def delete_rule(self, rule_id: int) -> bool:
        """删除规则"""
        pass
    
    @abstractmethod
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """获取活跃规则"""
        pass


class IDashboardService(ABC):
    """仪表板服务接口"""
    
    @abstractmethod
    def get_dashboard_data(self, user_id: int, date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """获取仪表板数据"""
        pass
    
    @abstractmethod
    def get_behavior_statistics(self, session_id: int = None, date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """获取行为统计"""
        pass
    
    @abstractmethod
    def get_alert_summary(self, date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """获取预警汇总"""
        pass
    
    @abstractmethod
    def export_report(self, report_type: str, params: Dict[str, Any]) -> str:
        """导出报告"""
        pass


class IUserManagementService(ABC):
    """用户管理服务接口"""
    
    @abstractmethod
    def get_all_users(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取所有用户（分页）"""
        pass
    
    @abstractmethod
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """搜索用户"""
        pass
    
    @abstractmethod
    def update_user_role(self, user_id: int, role: str) -> bool:
        """更新用户角色"""
        pass
    
    @abstractmethod
    def get_user_activity(self, user_id: int, date_range: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """获取用户活动记录"""
        pass


class IStudentPortraitService(ABC):
    """学生画像服务接口"""
    
    @abstractmethod
    def generate_student_portrait(self, student_id: int, date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """生成学生画像"""
        pass
    
    @abstractmethod
    def get_behavior_trends(self, student_id: int, behavior_type: str = None) -> Dict[str, Any]:
        """获取行为趋势"""
        pass
    
    @abstractmethod
    def compare_students(self, student_ids: List[int]) -> Dict[str, Any]:
        """学生对比分析"""
        pass
    
    @abstractmethod
    def get_class_overview(self, class_id: int, date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """获取班级概览"""
        pass