"""
检测数据访问组合器
Detection data access aggregator for complex data operations
符合Model层职责：仅处理数据访问，不包含业务逻辑
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.model.ManagerModel import DatabaseManager
from backend.model.ConfigModel import DatabaseConfig
from backend.model.Detection_repositoryModel import DetectionRepository
from backend.model.AnalyticsModel import AnalyticsRepository

logger = logging.getLogger(__name__)


class DetectionDataAccess:
    """检测数据访问组合器 - 组合多个repository提供复合数据操作"""
    
    def __init__(self, db: DatabaseManager = None, config: DatabaseConfig = None):
        """
        初始化检测数据访问组合器
        
        Args:
            db: 数据库管理器实例，如果为None则创建新实例
            config: 数据库配置
        """
        if db is None:
            self.db = DatabaseManager(config or DatabaseConfig())
            self.db.init_database()
        else:
            self.db = db
        
        self.detection_repo = DetectionRepository(self.db)
        self.analytics_repo = AnalyticsRepository(self.db)
    
    # ==================== 会话数据访问 ====================
    
    def create_session(
        self,
        source_type: str,
        source_path: str = None,
        user_id: int = None,
        schedule_id: int = None
    ) -> int:
        """创建检测会话记录"""
        return self.detection_repo.create_session(
            source_type=source_type,
            source_path=source_path,
            user_id=user_id,
            schedule_id=schedule_id
        )
    
    def update_session(
        self,
        session_id: int,
        end_time: datetime = None,
        total_frames: int = None,
        status: str = None
    ) -> None:
        """更新会话记录"""
        self.detection_repo.update_session(
            session_id=session_id,
            end_time=end_time,
            total_frames=total_frames,
            status=status
        )
    
    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.detection_repo.get_session(session_id)
    
    # ==================== 检测记录数据访问 ====================
    
    def save_detection_records(self, records: List[Dict[str, Any]]) -> List[int]:
        """批量保存检测记录"""
        record_ids = []
        for record in records:
            record_id = self.detection_repo.create_record(
                session_id=record['session_id'],
                frame_id=record['frame_id'],
                timestamp=record['timestamp'],
                alert_triggered=record.get('alert_triggered', False),
                detection_count=record.get('detection_count', 0)
            )
            record_ids.append(record_id)
        return record_ids
    
    def save_behavior_entries(self, entries: List[Dict[str, Any]]) -> List[int]:
        """批量保存行为条目"""
        entry_ids = []
        for entry in entries:
            entry_id = self.detection_repo.create_entry(
                record_id=entry['record_id'],
                bbox=entry['bbox'],
                class_id=entry['class_id'],
                class_name=entry['class_name'],
                confidence=entry['confidence'],
                behavior_type=entry['behavior_type'],
                alert_level=entry.get('alert_level', 0)
            )
            entry_ids.append(entry_id)
        return entry_ids
    
    def get_detection_records(
        self,
        session_id: int,
        limit: int = None,
        offset: int = None
    ) -> List[Dict[str, Any]]:
        """获取检测记录"""
        return self.detection_repo.get_records_by_session(
            session_id=session_id,
            limit=limit,
            offset=offset
        )
    
    def get_behavior_entries(
        self,
        session_id: int = None,
        record_id: int = None,
        behavior_type: str = None,
        alert_level: int = None
    ) -> List[Dict[str, Any]]:
        """获取行为条目"""
        if record_id:
            return self.detection_repo.get_entries_by_record(record_id)
        elif session_id:
            return self.detection_repo.get_entries_by_behavior(
                session_id=session_id,
                behavior_type=behavior_type,
                alert_level=alert_level
            )
        else:
            raise ValueError("Must provide either session_id or record_id")
    
    # ==================== 统计数据访问 ====================
    
    def get_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """获取会话统计数据"""
        return self.analytics_repo.get_session_statistics(session_id)
    
    def get_behavior_statistics(
        self,
        session_id: int = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> Dict[str, Any]:
        """获取行为统计数据"""
        return self.analytics_repo.get_behavior_statistics(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time
        )
    
    def export_session_to_json(self, session_id: int) -> str:
        """导出会话数据为JSON"""
        return self.analytics_repo.export_session_to_json(session_id)
    
    # ==================== 资源管理 ====================
    
    def close(self) -> None:
        """关闭数据访问服务"""
        self.db.close()
    
    def __enter__(self) -> 'DetectionDataAccess':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()