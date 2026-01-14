"""
检测数据仓库模块
Detection data repository for sessions, records, and behavior entries
"""
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from backend.model.ManagerModel import DatabaseManager
from backend.model.InterfaceModel import IDetectionRepository

logger = logging.getLogger(__name__)


class DetectionRepository(IDetectionRepository):
    """检测数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        """
        初始化检测数据仓库
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
    
    # ==================== 基础CRUD操作 ====================
    
    def create(self, data: Dict[str, Any]) -> int:
        """创建记录（通用方法）"""
        # 这是一个通用接口，具体实现由专门的方法处理
        raise NotImplementedError("Use specific create methods like create_session, create_record")
    
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记录（通用方法）"""
        # 这是一个通用接口，具体实现由专门的方法处理
        raise NotImplementedError("Use specific get methods like get_session, get_record")
    
    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """更新记录（通用方法）"""
        # 这是一个通用接口，具体实现由专门的方法处理
        raise NotImplementedError("Use specific update methods like update_session")
    
    def delete(self, id: int) -> bool:
        """删除记录（通用方法）"""
        # 这是一个通用接口，具体实现由专门的方法处理
        raise NotImplementedError("Use specific delete methods")
    
    def get_all(self, limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """获取所有记录（通用方法）"""
        return self.get_all_sessions(limit or 1000)
    
    # ==================== Session 操作 ====================
    
    def create_session(
        self,
        source_type: str,
        source_path: str = None,
        user_id: int = None,
        schedule_id: int = None
    ) -> int:
        """
        创建检测会话
        
        Args:
            source_type: 输入源类型 (image/video/stream)
            source_path: 输入源路径
            user_id: 创建用户ID
            schedule_id: 关联的课堂安排ID
            
        Returns:
            新创建的session_id
        """
        sql = """
            INSERT INTO detection_sessions 
            (source_type, source_path, user_id, schedule_id, status)
            VALUES (%s, %s, %s, %s, 'running')
        """
        return self.db.insert_and_get_id(sql, (source_type, source_path, user_id, schedule_id))
    
    def update_session(
        self,
        session_id: int,
        end_time: datetime = None,
        total_frames: int = None,
        status: str = None
    ) -> None:
        """
        更新检测会话
        
        Args:
            session_id: 会话ID
            end_time: 结束时间
            total_frames: 总帧数
            status: 状态
        """
        updates = []
        params = []
        
        if end_time is not None:
            updates.append("end_time = %s")
            params.append(end_time)
        if total_frames is not None:
            updates.append("total_frames = %s")
            params.append(total_frames)
        if status is not None:
            updates.append("status = %s")
            params.append(status)
        
        if not updates:
            return
        
        params.append(session_id)
        sql = f"UPDATE detection_sessions SET {', '.join(updates)} WHERE session_id = %s"
        self.db.execute(sql, tuple(params))
    
    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个会话详情
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息字典或None
        """
        sql = "SELECT * FROM detection_sessions WHERE session_id = %s"
        return self.db.query_one(sql, (session_id,))
    
    def list_sessions(
        self,
        start_date: date = None,
        end_date: date = None,
        user_id: int = None,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询会话列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID筛选
            status: 状态筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            会话列表
        """
        conditions = []
        params = []
        
        if start_date:
            conditions.append("DATE(start_time) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(start_time) <= %s")
            params.append(end_date)
        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM detection_sessions 
            {where_clause}
            ORDER BY start_time DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    def delete_session(self, session_id: int) -> None:
        """
        删除会话（级联删除关联的records和entries）
        
        Args:
            session_id: 会话ID
        """
        sql = "DELETE FROM detection_sessions WHERE session_id = %s"
        self.db.execute(sql, (session_id,))
    
    def count_sessions(
        self,
        start_date: date = None,
        end_date: date = None,
        user_id: int = None,
        class_id: int = None
    ) -> int:
        """
        统计会话数量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID筛选
            class_id: 班级ID筛选
            
        Returns:
            会话数量
        """
        conditions = []
        params = []
        
        if start_date:
            conditions.append("DATE(start_time) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(start_time) <= %s")
            params.append(end_date)
        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)
        if class_id:
            conditions.append("class_id = %s")
            params.append(class_id)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT COUNT(*) as count FROM detection_sessions {where_clause}"
        result = self.db.query_one(sql, tuple(params))
        return result['count'] if result else 0

    
    # ==================== Record 操作 ====================
    
    def create_record(
        self,
        session_id: int,
        frame_id: int,
        timestamp: float,
        alert_triggered: bool = False,
        detection_count: int = 0
    ) -> int:
        """
        创建检测记录
        
        Args:
            session_id: 会话ID
            frame_id: 帧ID
            timestamp: 时间戳
            alert_triggered: 是否触发预警
            detection_count: 检测数量
            
        Returns:
            新创建的record_id
        """
        sql = """
            INSERT INTO detection_records 
            (session_id, frame_id, timestamp, alert_triggered, detection_count)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(
            sql, (session_id, frame_id, timestamp, alert_triggered, detection_count)
        )
    
    def create_records_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        批量创建检测记录
        
        Args:
            records: 记录列表，每个记录包含 session_id, frame_id, timestamp, 
                     alert_triggered, detection_count
            
        Returns:
            插入的记录数
        """
        if not records:
            return 0
        
        sql = """
            INSERT INTO detection_records 
            (session_id, frame_id, timestamp, alert_triggered, detection_count)
            VALUES (%s, %s, %s, %s, %s)
        """
        params_list = [
            (
                r['session_id'],
                r['frame_id'],
                r['timestamp'],
                r.get('alert_triggered', False),
                r.get('detection_count', 0)
            )
            for r in records
        ]
        return self.db.execute_many(sql, params_list)
    
    def get_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个检测记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录信息字典或None
        """
        sql = "SELECT * FROM detection_records WHERE record_id = %s"
        return self.db.query_one(sql, (record_id,))
    
    def get_records_by_session(
        self,
        session_id: int,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        按会话ID查询检测记录
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            记录列表
        """
        sql = """
            SELECT * FROM detection_records 
            WHERE session_id = %s
            ORDER BY frame_id
            LIMIT %s OFFSET %s
        """
        return self.db.query(sql, (session_id, limit, offset))
    
    def get_records_by_time_range(
        self,
        start_time: float,
        end_time: float,
        session_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        按时间范围查询检测记录
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            session_id: 可选的会话ID筛选
            
        Returns:
            记录列表
        """
        conditions = ["timestamp >= %s", "timestamp <= %s"]
        params = [start_time, end_time]
        
        if session_id:
            conditions.append("session_id = %s")
            params.append(session_id)
        
        sql = f"""
            SELECT * FROM detection_records 
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp
        """
        return self.db.query(sql, tuple(params))
    
    def count_records_by_session(self, session_id: int) -> int:
        """
        统计会话的记录数量
        
        Args:
            session_id: 会话ID
            
        Returns:
            记录数量
        """
        sql = "SELECT COUNT(*) as count FROM detection_records WHERE session_id = %s"
        result = self.db.query_one(sql, (session_id,))
        return result['count'] if result else 0
    
    # ==================== Entry 操作 ====================
    
    def create_entry(
        self,
        record_id: int,
        bbox: Tuple[float, float, float, float],
        class_id: int,
        class_name: str,
        confidence: float,
        behavior_type: str,
        alert_level: int = 0
    ) -> int:
        """
        创建行为条目
        
        Args:
            record_id: 记录ID
            bbox: 边界框 (x1, y1, x2, y2)
            class_id: 类别ID
            class_name: 类别名称
            confidence: 置信度
            behavior_type: 行为类型 (normal/warning)
            alert_level: 预警级别 (0-3)
            
        Returns:
            新创建的entry_id
        """
        sql = """
            INSERT INTO behavior_entries 
            (record_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, 
             class_id, class_name, confidence, behavior_type, alert_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(
            sql, (record_id, bbox[0], bbox[1], bbox[2], bbox[3],
                  class_id, class_name, confidence, behavior_type, alert_level)
        )
    
    def create_entries_batch(self, entries: List[Dict[str, Any]]) -> int:
        """
        批量创建行为条目
        
        Args:
            entries: 条目列表，每个条目包含 record_id, bbox, class_id, 
                     class_name, confidence, behavior_type, alert_level
            
        Returns:
            插入的条目数
        """
        if not entries:
            return 0
        
        sql = """
            INSERT INTO behavior_entries 
            (record_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, 
             class_id, class_name, confidence, behavior_type, alert_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params_list = []
        for e in entries:
            bbox = e['bbox']
            params_list.append((
                e['record_id'],
                bbox[0], bbox[1], bbox[2], bbox[3],
                e['class_id'],
                e['class_name'],
                e['confidence'],
                e['behavior_type'],
                e.get('alert_level', 0)
            ))
        return self.db.execute_many(sql, params_list)
    
    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个行为条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            条目信息字典或None
        """
        sql = "SELECT * FROM behavior_entries WHERE entry_id = %s"
        return self.db.query_one(sql, (entry_id,))
    
    def get_entries_by_record(self, record_id: int) -> List[Dict[str, Any]]:
        """
        按记录ID查询行为条目
        
        Args:
            record_id: 记录ID
            
        Returns:
            条目列表
        """
        sql = "SELECT * FROM behavior_entries WHERE record_id = %s"
        return self.db.query(sql, (record_id,))
    
    def get_entries_by_session(self, session_id: int) -> List[Dict[str, Any]]:
        """
        按会话ID查询所有行为条目
        
        Args:
            session_id: 会话ID
            
        Returns:
            条目列表
        """
        sql = """
            SELECT be.* FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            WHERE dr.session_id = %s
        """
        return self.db.query(sql, (session_id,))
    
    def get_entries_by_behavior(
        self,
        session_id: int,
        behavior_type: str = None,
        alert_level: int = None,
        class_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        按行为类型筛选条目
        
        Args:
            session_id: 会话ID
            behavior_type: 行为类型筛选 (normal/warning)
            alert_level: 预警级别筛选
            class_id: 类别ID筛选
            
        Returns:
            条目列表
        """
        conditions = ["dr.session_id = %s"]
        params = [session_id]
        
        if behavior_type:
            conditions.append("be.behavior_type = %s")
            params.append(behavior_type)
        if alert_level is not None:
            conditions.append("be.alert_level = %s")
            params.append(alert_level)
        if class_id is not None:
            conditions.append("be.class_id = %s")
            params.append(class_id)
        
        sql = f"""
            SELECT be.* FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            WHERE {' AND '.join(conditions)}
        """
        return self.db.query(sql, tuple(params))
    
    def count_entries_by_session(self, session_id: int) -> int:
        """
        统计会话的行为条目数量
        
        Args:
            session_id: 会话ID
            
        Returns:
            条目数量
        """
        sql = """
            SELECT COUNT(*) as count FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            WHERE dr.session_id = %s
        """
        result = self.db.query_one(sql, (session_id,))
        return result['count'] if result else 0
    
    # ==================== 导出和清理操作 ====================
    
    def get_all_sessions(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        获取所有会话（用于导出）
        
        Args:
            limit: 返回数量限制
            
        Returns:
            会话列表
        """
        sql = """
            SELECT session_id, schedule_id as course_id, start_time, end_time, 
                   status, total_frames,
                   (SELECT COUNT(*) FROM detection_records WHERE session_id = ds.session_id) as detected_frames
            FROM detection_sessions ds
            ORDER BY start_time DESC
            LIMIT %s
        """
        return self.db.query(sql, (limit,))
    
    def get_alerts(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        获取预警记录（用于导出）
        
        Args:
            limit: 返回数量限制
            
        Returns:
            预警列表
        """
        sql = """
            SELECT be.entry_id as alert_id, be.class_name as student_id,
                   dr.session_id, be.behavior_type as alert_type,
                   be.alert_level, be.class_name as alert_message,
                   dr.created_at, 0 as is_read
            FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            WHERE be.alert_level > 0
            ORDER BY dr.created_at DESC
            LIMIT %s
        """
        return self.db.query(sql, (limit,))
    
    def get_behavior_statistics(self) -> List[Dict[str, Any]]:
        """
        获取行为统计（用于导出）
        
        Returns:
            行为统计列表
        """
        sql = """
            SELECT class_name as behavior_type, 
                   COUNT(*) as count,
                   AVG(confidence) as avg_confidence
            FROM behavior_entries
            GROUP BY class_name
            ORDER BY count DESC
        """
        return self.db.query(sql)
    
    def cleanup_old_records(self, cutoff_date: datetime) -> int:
        """
        清理指定日期之前的历史数据
        
        Args:
            cutoff_date: 截止日期
            
        Returns:
            删除的记录数
        """
        # 先统计要删除的数量
        count_sql = """
            SELECT COUNT(*) as count FROM detection_sessions 
            WHERE start_time < %s
        """
        result = self.db.query_one(count_sql, (cutoff_date,))
        count = result['count'] if result else 0
        
        # 删除旧会话（级联删除关联的records和entries）
        delete_sql = "DELETE FROM detection_sessions WHERE start_time < %s"
        self.db.execute(delete_sql, (cutoff_date,))
        
        return count
