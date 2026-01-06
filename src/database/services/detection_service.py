"""
检测服务模块
Detection service for integrating detection results with database storage
"""
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from ..manager import DatabaseManager
from ..config import DatabaseConfig
from ..repositories.detection_repository import DetectionRepository
from ..repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class DetectionService:
    """检测数据服务层"""
    
    def __init__(self, db: DatabaseManager = None, config: DatabaseConfig = None):
        """
        初始化检测服务
        
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
        
        # 当前会话状态
        self._current_session_id: Optional[int] = None
        self._frame_count: int = 0
        self._record_buffer: List[Dict] = []
        self._entry_buffer: List[Dict] = []
        self._buffer_size: int = 100  # 批量插入阈值
    
    # ==================== 会话管理 ====================
    
    def start_session(
        self,
        source_type: str,
        source_path: str = None,
        user_id: int = None,
        schedule_id: int = None
    ) -> int:
        """
        开始新的检测会话
        
        Args:
            source_type: 输入源类型 (image/video/stream)
            source_path: 输入源路径
            user_id: 用户ID
            schedule_id: 课堂安排ID
            
        Returns:
            会话ID
        """
        self._current_session_id = self.detection_repo.create_session(
            source_type=source_type,
            source_path=source_path,
            user_id=user_id,
            schedule_id=schedule_id
        )
        self._frame_count = 0
        self._record_buffer = []
        self._entry_buffer = []
        
        logger.info(f"Started detection session: {self._current_session_id}")
        return self._current_session_id
    
    def end_session(self, status: str = 'completed') -> Dict[str, Any]:
        """
        结束当前检测会话
        
        Args:
            status: 会话状态 (completed/failed)
            
        Returns:
            会话统计信息
        """
        if self._current_session_id is None:
            logger.warning("No active session to end")
            return {}
        
        # 刷新缓冲区
        self._flush_buffers()
        
        # 更新会话
        self.detection_repo.update_session(
            session_id=self._current_session_id,
            end_time=datetime.now(),
            total_frames=self._frame_count,
            status=status
        )
        
        # 获取统计信息
        stats = self.analytics_repo.get_session_statistics(self._current_session_id)
        
        logger.info(f"Ended detection session: {self._current_session_id}, frames: {self._frame_count}")
        
        session_id = self._current_session_id
        self._current_session_id = None
        self._frame_count = 0
        
        return stats
    
    @property
    def current_session_id(self) -> Optional[int]:
        """获取当前会话ID"""
        return self._current_session_id
    
    # ==================== 检测结果保存 ====================
    
    def save_detection_result(
        self,
        frame_id: int,
        timestamp: float,
        detections: List[Dict[str, Any]],
        alert_triggered: bool = False
    ) -> int:
        """
        保存单帧检测结果
        
        Args:
            frame_id: 帧ID
            timestamp: 时间戳
            detections: 检测结果列表，每个检测包含:
                - bbox: (x1, y1, x2, y2)
                - class_id: 类别ID
                - class_name: 类别名称
                - confidence: 置信度
                - behavior_type: 行为类型 (normal/warning)
                - alert_level: 预警级别 (0-3)
            alert_triggered: 是否触发预警
            
        Returns:
            记录ID
        """
        if self._current_session_id is None:
            raise RuntimeError("No active session. Call start_session() first.")
        
        self._frame_count += 1
        
        # 添加到缓冲区
        record = {
            'session_id': self._current_session_id,
            'frame_id': frame_id,
            'timestamp': timestamp,
            'alert_triggered': alert_triggered,
            'detection_count': len(detections)
        }
        self._record_buffer.append(record)
        
        # 暂存检测条目（需要record_id，稍后处理）
        for det in detections:
            entry = {
                'frame_id': frame_id,  # 临时标记
                'bbox': det['bbox'],
                'class_id': det['class_id'],
                'class_name': det['class_name'],
                'confidence': det['confidence'],
                'behavior_type': det['behavior_type'],
                'alert_level': det.get('alert_level', 0)
            }
            self._entry_buffer.append(entry)
        
        # 检查是否需要刷新缓冲区
        if len(self._record_buffer) >= self._buffer_size:
            self._flush_buffers()
        
        return frame_id
    
    def save_detection_batch(
        self,
        results: List[Dict[str, Any]]
    ) -> int:
        """
        批量保存检测结果
        
        Args:
            results: 检测结果列表，每个结果包含:
                - frame_id: 帧ID
                - timestamp: 时间戳
                - detections: 检测列表
                - alert_triggered: 是否触发预警
                
        Returns:
            保存的记录数
        """
        for result in results:
            self.save_detection_result(
                frame_id=result['frame_id'],
                timestamp=result['timestamp'],
                detections=result.get('detections', []),
                alert_triggered=result.get('alert_triggered', False)
            )
        
        return len(results)
    
    def _flush_buffers(self) -> None:
        """刷新缓冲区到数据库"""
        if not self._record_buffer:
            return
        
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            
            # 批量插入记录
            record_sql = """
                INSERT INTO detection_records 
                (session_id, frame_id, timestamp, alert_triggered, detection_count)
                VALUES (%s, %s, %s, %s, %s)
            """
            record_params = [
                (r['session_id'], r['frame_id'], r['timestamp'], 
                 r['alert_triggered'], r['detection_count'])
                for r in self._record_buffer
            ]
            cursor.executemany(record_sql, record_params)
            
            # 获取插入的record_id范围
            first_record_id = cursor.lastrowid - len(self._record_buffer) + 1
            
            # 构建frame_id到record_id的映射
            frame_to_record = {}
            for i, record in enumerate(self._record_buffer):
                frame_to_record[record['frame_id']] = first_record_id + i
            
            # 批量插入条目
            if self._entry_buffer:
                entry_sql = """
                    INSERT INTO behavior_entries 
                    (record_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, 
                     class_id, class_name, confidence, behavior_type, alert_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                entry_params = []
                for e in self._entry_buffer:
                    record_id = frame_to_record.get(e['frame_id'])
                    if record_id:
                        bbox = e['bbox']
                        entry_params.append((
                            record_id,
                            bbox[0], bbox[1], bbox[2], bbox[3],
                            e['class_id'], e['class_name'], e['confidence'],
                            e['behavior_type'], e['alert_level']
                        ))
                
                if entry_params:
                    cursor.executemany(entry_sql, entry_params)
            
            cursor.close()
        
        # 清空缓冲区
        self._record_buffer = []
        self._entry_buffer = []
    
    # ==================== 与AlertInterface集成 ====================
    
    def save_alert_result(self, alert_result: Any, frame_id: int = None) -> int:
        """
        保存AlertResult对象
        
        Args:
            alert_result: AlertResult对象（来自alert模块）
            frame_id: 帧ID（如果AlertResult中没有）
            
        Returns:
            记录ID
        """
        # 从AlertResult提取数据
        detections = []
        for det in alert_result.detections:
            detections.append({
                'bbox': det.bbox,
                'class_id': det.class_id,
                'class_name': det.class_name,
                'confidence': det.confidence,
                'behavior_type': det.behavior_type,
                'alert_level': det.alert_level
            })
        
        return self.save_detection_result(
            frame_id=frame_id or alert_result.frame_id,
            timestamp=alert_result.timestamp,
            detections=detections,
            alert_triggered=alert_result.alert_triggered
        )
    
    # ==================== 查询接口 ====================
    
    def get_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """获取会话统计"""
        return self.analytics_repo.get_session_statistics(session_id)
    
    def get_session_detections(
        self,
        session_id: int,
        behavior_type: str = None,
        alert_level: int = None
    ) -> List[Dict[str, Any]]:
        """获取会话的检测结果"""
        return self.detection_repo.get_entries_by_behavior(
            session_id=session_id,
            behavior_type=behavior_type,
            alert_level=alert_level
        )
    
    def export_session_json(self, session_id: int) -> str:
        """导出会话数据为JSON"""
        return self.analytics_repo.export_session_to_json(session_id)
    
    # ==================== 资源管理 ====================
    
    def close(self) -> None:
        """关闭服务"""
        if self._current_session_id:
            self.end_session(status='failed')
        self.db.close()
    
    def __enter__(self) -> 'DetectionService':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
