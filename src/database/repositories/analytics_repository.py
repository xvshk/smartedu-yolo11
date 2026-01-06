"""
分析仓库模块
Analytics repository for statistics, summaries, and alert rules
"""
import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """分析数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        """
        初始化分析仓库
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
    
    # ==================== 统计查询 ====================
    
    def get_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """
        获取会话统计信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            统计信息字典
        """
        # 基本信息
        session_sql = "SELECT * FROM detection_sessions WHERE session_id = %s"
        session = self.db.query_one(session_sql, (session_id,))
        
        if not session:
            return {}
        
        # 记录统计
        record_sql = """
            SELECT 
                COUNT(*) as total_records,
                SUM(detection_count) as total_detections,
                SUM(CASE WHEN alert_triggered THEN 1 ELSE 0 END) as alert_frames
            FROM detection_records 
            WHERE session_id = %s
        """
        record_stats = self.db.query_one(record_sql, (session_id,))
        
        # 行为分布
        behavior_sql = """
            SELECT 
                be.class_name,
                be.behavior_type,
                be.alert_level,
                COUNT(*) as count
            FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            WHERE dr.session_id = %s
            GROUP BY be.class_name, be.behavior_type, be.alert_level
        """
        behavior_dist = self.db.query(behavior_sql, (session_id,))
        
        # 构建结果
        behavior_distribution = {}
        alert_distribution = {0: 0, 1: 0, 2: 0, 3: 0}
        normal_count = 0
        warning_count = 0
        
        for row in behavior_dist:
            behavior_distribution[row['class_name']] = row['count']
            alert_distribution[row['alert_level']] = \
                alert_distribution.get(row['alert_level'], 0) + row['count']
            if row['behavior_type'] == 'normal':
                normal_count += row['count']
            else:
                warning_count += row['count']
        
        total_behaviors = normal_count + warning_count
        attention_rate = normal_count / total_behaviors if total_behaviors > 0 else 1.0
        
        return {
            'session_id': session_id,
            'source_type': session['source_type'],
            'start_time': session['start_time'],
            'end_time': session['end_time'],
            'total_frames': session['total_frames'],
            'total_records': record_stats['total_records'] or 0,
            'total_detections': record_stats['total_detections'] or 0,
            'alert_frames': record_stats['alert_frames'] or 0,
            'normal_count': normal_count,
            'warning_count': warning_count,
            'attention_rate': attention_rate,
            'behavior_distribution': behavior_distribution,
            'alert_distribution': alert_distribution
        }
    
    def get_behavior_distribution(
        self,
        start_date: date,
        end_date: date,
        course_id: int = None,
        class_id: int = None
    ) -> Dict[str, int]:
        """
        获取行为分布统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            course_id: 课程ID筛选
            class_id: 班级ID筛选
            
        Returns:
            行为分布字典 {class_name: count}
        """
        conditions = ["ds.start_time >= %s", "ds.start_time < DATE_ADD(%s, INTERVAL 1 DAY)"]
        params = [start_date, end_date]
        
        # 按班级筛选
        if class_id:
            conditions.append("ds.class_id = %s")
            params.append(class_id)
        
        sql = f"""
            SELECT be.class_name, COUNT(*) as count
            FROM behavior_entries be
            INNER JOIN detection_records dr ON be.record_id = dr.record_id
            INNER JOIN detection_sessions ds ON dr.session_id = ds.session_id
            WHERE {' AND '.join(conditions)}
            GROUP BY be.class_name
        """
        results = self.db.query(sql, tuple(params))
        return {r['class_name']: r['count'] for r in results}
    
    def get_alert_distribution(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[int, int]:
        """
        获取预警级别分布统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            预警分布字典 {alert_level: count}
        """
        sql = """
            SELECT be.alert_level, COUNT(*) as count
            FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            JOIN detection_sessions ds ON dr.session_id = ds.session_id
            WHERE DATE(ds.start_time) >= %s AND DATE(ds.start_time) <= %s
            GROUP BY be.alert_level
        """
        results = self.db.query(sql, (start_date, end_date))
        distribution = {0: 0, 1: 0, 2: 0, 3: 0}
        for r in results:
            distribution[r['alert_level']] = r['count']
        return distribution
    
    def get_top_warning_behaviors(
        self,
        start_date: date,
        end_date: date,
        class_id: int = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取预警行为排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            class_id: 班级ID筛选
            limit: 返回数量
            
        Returns:
            预警行为列表
        """
        conditions = [
            "ds.start_time >= %s",
            "ds.start_time < DATE_ADD(%s, INTERVAL 1 DAY)",
            "be.behavior_type = 'warning'"
        ]
        params = [start_date, end_date]
        
        if class_id:
            conditions.append("ds.class_id = %s")
            params.append(class_id)
        
        params.append(limit)
        
        sql = f"""
            SELECT be.class_name, be.alert_level, COUNT(*) as count
            FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            JOIN detection_sessions ds ON dr.session_id = ds.session_id
            WHERE {' AND '.join(conditions)}
            GROUP BY be.class_name, be.alert_level
            ORDER BY count DESC
            LIMIT %s
        """
        return self.db.query(sql, tuple(params))

    
    # ==================== 汇总数据管理 ====================
    
    def save_daily_summary(self, summary_date: date, summary: Dict[str, Any]) -> None:
        """
        保存每日汇总
        
        Args:
            summary_date: 日期
            summary: 汇总数据
        """
        sql = """
            INSERT INTO daily_summaries 
            (summary_date, total_sessions, total_detections, behavior_distribution, 
             alert_distribution, avg_attention_rate)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                total_sessions = VALUES(total_sessions),
                total_detections = VALUES(total_detections),
                behavior_distribution = VALUES(behavior_distribution),
                alert_distribution = VALUES(alert_distribution),
                avg_attention_rate = VALUES(avg_attention_rate)
        """
        self.db.execute(sql, (
            summary_date,
            summary.get('total_sessions', 0),
            summary.get('total_detections', 0),
            json.dumps(summary.get('behavior_distribution', {})),
            json.dumps(summary.get('alert_distribution', {})),
            summary.get('avg_attention_rate')
        ))
    
    def get_daily_summary(self, summary_date: date) -> Optional[Dict[str, Any]]:
        """
        获取每日汇总
        
        Args:
            summary_date: 日期
            
        Returns:
            汇总数据或None
        """
        sql = "SELECT * FROM daily_summaries WHERE summary_date = %s"
        result = self.db.query_one(sql, (summary_date,))
        if result:
            result['behavior_distribution'] = json.loads(result['behavior_distribution'] or '{}')
            result['alert_distribution'] = json.loads(result['alert_distribution'] or '{}')
        return result
    
    def get_daily_summaries(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取日期范围内的每日汇总
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            汇总列表
        """
        sql = """
            SELECT * FROM daily_summaries 
            WHERE summary_date >= %s AND summary_date <= %s
            ORDER BY summary_date
        """
        results = self.db.query(sql, (start_date, end_date))
        for r in results:
            r['behavior_distribution'] = json.loads(r['behavior_distribution'] or '{}')
            r['alert_distribution'] = json.loads(r['alert_distribution'] or '{}')
        return results
    
    def save_course_summary(
        self,
        course_id: int,
        period: str,
        period_start: date,
        period_end: date,
        summary: Dict[str, Any]
    ) -> None:
        """
        保存课程汇总
        
        Args:
            course_id: 课程ID
            period: 周期类型 (week/month/semester)
            period_start: 周期开始日期
            period_end: 周期结束日期
            summary: 汇总数据
        """
        sql = """
            INSERT INTO course_summaries 
            (course_id, period, period_start, period_end, total_sessions, 
             avg_attention_rate, behavior_trends)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                period_end = VALUES(period_end),
                total_sessions = VALUES(total_sessions),
                avg_attention_rate = VALUES(avg_attention_rate),
                behavior_trends = VALUES(behavior_trends)
        """
        self.db.execute(sql, (
            course_id,
            period,
            period_start,
            period_end,
            summary.get('total_sessions', 0),
            summary.get('avg_attention_rate'),
            json.dumps(summary.get('behavior_trends', {}))
        ))
    
    def get_course_summary(
        self,
        course_id: int,
        period: str,
        period_start: date = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取课程汇总
        
        Args:
            course_id: 课程ID
            period: 周期类型
            period_start: 周期开始日期
            
        Returns:
            汇总数据或None
        """
        if period_start:
            sql = """
                SELECT * FROM course_summaries 
                WHERE course_id = %s AND period = %s AND period_start = %s
            """
            result = self.db.query_one(sql, (course_id, period, period_start))
        else:
            sql = """
                SELECT * FROM course_summaries 
                WHERE course_id = %s AND period = %s
                ORDER BY period_start DESC LIMIT 1
            """
            result = self.db.query_one(sql, (course_id, period))
        
        if result:
            result['behavior_trends'] = json.loads(result['behavior_trends'] or '{}')
        return result
    
    def save_class_summary(
        self,
        class_id: int,
        period: str,
        period_start: date,
        period_end: date,
        summary: Dict[str, Any]
    ) -> None:
        """
        保存班级汇总
        
        Args:
            class_id: 班级ID
            period: 周期类型
            period_start: 周期开始日期
            period_end: 周期结束日期
            summary: 汇总数据
        """
        sql = """
            INSERT INTO class_summaries 
            (class_id, period, period_start, period_end, total_sessions, 
             avg_attention_rate, top_warning_behaviors)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                period_end = VALUES(period_end),
                total_sessions = VALUES(total_sessions),
                avg_attention_rate = VALUES(avg_attention_rate),
                top_warning_behaviors = VALUES(top_warning_behaviors)
        """
        self.db.execute(sql, (
            class_id,
            period,
            period_start,
            period_end,
            summary.get('total_sessions', 0),
            summary.get('avg_attention_rate'),
            json.dumps(summary.get('top_warning_behaviors', []))
        ))
    
    def get_class_summary(
        self,
        class_id: int,
        period: str,
        period_start: date = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取班级汇总
        
        Args:
            class_id: 班级ID
            period: 周期类型
            period_start: 周期开始日期
            
        Returns:
            汇总数据或None
        """
        if period_start:
            sql = """
                SELECT * FROM class_summaries 
                WHERE class_id = %s AND period = %s AND period_start = %s
            """
            result = self.db.query_one(sql, (class_id, period, period_start))
        else:
            sql = """
                SELECT * FROM class_summaries 
                WHERE class_id = %s AND period = %s
                ORDER BY period_start DESC LIMIT 1
            """
            result = self.db.query_one(sql, (class_id, period))
        
        if result:
            result['top_warning_behaviors'] = json.loads(result['top_warning_behaviors'] or '[]')
        return result
    
    # ==================== 注意力指数 ====================
    
    def calculate_attention_rate(self, session_id: int) -> float:
        """
        计算会话的注意力指数
        
        Args:
            session_id: 会话ID
            
        Returns:
            注意力指数 (0.0-1.0)
        """
        sql = """
            SELECT 
                SUM(CASE WHEN be.behavior_type = 'normal' THEN 1 ELSE 0 END) as normal_count,
                COUNT(*) as total_count
            FROM behavior_entries be
            JOIN detection_records dr ON be.record_id = dr.record_id
            WHERE dr.session_id = %s
        """
        result = self.db.query_one(sql, (session_id,))
        
        if not result or result['total_count'] == 0:
            return 1.0
        
        return result['normal_count'] / result['total_count']
    
    def get_attention_trend(
        self,
        course_id: int = None,
        class_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> List[Dict[str, Any]]:
        """
        获取注意力趋势
        
        Args:
            course_id: 课程ID筛选
            class_id: 班级ID筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            趋势数据列表
        """
        conditions = []
        params = []
        
        if start_date:
            conditions.append("ds.start_time >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("ds.start_time < DATE_ADD(%s, INTERVAL 1 DAY)")
            params.append(end_date)
        if class_id:
            conditions.append("ds.class_id = %s")
            params.append(class_id)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        sql = f"""
            SELECT 
                DATE(ds.start_time) as date,
                COUNT(DISTINCT ds.session_id) as session_count,
                SUM(CASE WHEN be.behavior_type = 'normal' THEN 1 ELSE 0 END) as normal_count,
                COUNT(be.entry_id) as total_count
            FROM detection_sessions ds
            LEFT JOIN detection_records dr ON ds.session_id = dr.session_id
            LEFT JOIN behavior_entries be ON dr.record_id = be.record_id
            {where_clause}
            GROUP BY DATE(ds.start_time)
            ORDER BY date
        """
        results = self.db.query(sql, tuple(params))
        
        # 计算每日注意力指数
        for r in results:
            if r['total_count'] and r['total_count'] > 0:
                r['attention_rate'] = r['normal_count'] / r['total_count']
            else:
                r['attention_rate'] = 1.0
        
        return results

    
    # ==================== 预警规则管理 ====================
    
    def create_alert_rule(
        self,
        rule_name: str,
        behavior_type: str = None,
        class_id: int = None,
        threshold_count: int = 1,
        time_window_seconds: int = 60,
        alert_level: int = 1
    ) -> int:
        """
        创建预警规则
        
        Args:
            rule_name: 规则名称
            behavior_type: 行为类型
            class_id: 类别ID
            threshold_count: 阈值数量
            time_window_seconds: 时间窗口（秒）
            alert_level: 预警级别
            
        Returns:
            新创建的rule_id
        """
        sql = """
            INSERT INTO alert_rules 
            (rule_name, behavior_type, class_id, threshold_count, time_window_seconds, alert_level)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(
            sql, (rule_name, behavior_type, class_id, threshold_count, time_window_seconds, alert_level)
        )
    
    def get_alert_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """
        获取预警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则信息或None
        """
        sql = "SELECT * FROM alert_rules WHERE rule_id = %s"
        return self.db.query_one(sql, (rule_id,))
    
    def get_alert_rules(self, is_active: bool = None) -> List[Dict[str, Any]]:
        """
        获取预警规则列表
        
        Args:
            is_active: 是否激活筛选
            
        Returns:
            规则列表
        """
        if is_active is not None:
            sql = "SELECT * FROM alert_rules WHERE is_active = %s ORDER BY created_at"
            return self.db.query(sql, (is_active,))
        else:
            sql = "SELECT * FROM alert_rules ORDER BY created_at"
            return self.db.query(sql)
    
    def update_alert_rule(self, rule_id: int, **kwargs) -> None:
        """
        更新预警规则
        
        Args:
            rule_id: 规则ID
            **kwargs: 要更新的字段
        """
        allowed_fields = {
            'rule_name', 'behavior_type', 'class_id', 
            'threshold_count', 'time_window_seconds', 'alert_level', 'is_active'
        }
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)
        
        if not updates:
            return
        
        params.append(rule_id)
        sql = f"UPDATE alert_rules SET {', '.join(updates)} WHERE rule_id = %s"
        self.db.execute(sql, tuple(params))
    
    def delete_alert_rule(self, rule_id: int) -> None:
        """
        删除预警规则
        
        Args:
            rule_id: 规则ID
        """
        sql = "DELETE FROM alert_rules WHERE rule_id = %s"
        self.db.execute(sql, (rule_id,))
    
    # ==================== 预警事件管理 ====================
    
    def create_alert_event(
        self,
        rule_id: int,
        session_id: int,
        behavior_count: int
    ) -> int:
        """
        创建预警事件
        
        Args:
            rule_id: 规则ID
            session_id: 会话ID
            behavior_count: 行为数量
            
        Returns:
            新创建的event_id
        """
        sql = """
            INSERT INTO alert_events (rule_id, session_id, behavior_count)
            VALUES (%s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (rule_id, session_id, behavior_count))
    
    def get_alert_events(
        self,
        session_id: int = None,
        rule_id: int = None,
        is_resolved: bool = None,
        start_date: date = None,
        end_date: date = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取预警事件列表
        
        Args:
            session_id: 会话ID筛选
            rule_id: 规则ID筛选
            is_resolved: 是否已解决筛选
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            事件列表
        """
        conditions = []
        params = []
        
        if session_id:
            conditions.append("session_id = %s")
            params.append(session_id)
        if rule_id:
            conditions.append("rule_id = %s")
            params.append(rule_id)
        if is_resolved is not None:
            conditions.append("is_resolved = %s")
            params.append(is_resolved)
        if start_date:
            conditions.append("DATE(triggered_at) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(triggered_at) <= %s")
            params.append(end_date)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT ae.*, ar.rule_name, ar.behavior_type, ar.alert_level
            FROM alert_events ae
            JOIN alert_rules ar ON ae.rule_id = ar.rule_id
            {where_clause}
            ORDER BY triggered_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    def resolve_alert_event(self, event_id: int) -> None:
        """
        解决预警事件
        
        Args:
            event_id: 事件ID
        """
        sql = """
            UPDATE alert_events 
            SET is_resolved = TRUE, resolved_at = CURRENT_TIMESTAMP
            WHERE event_id = %s
        """
        self.db.execute(sql, (event_id,))
    
    # ==================== 数据导出 ====================
    
    def export_session_to_json(self, session_id: int) -> str:
        """
        导出会话数据为JSON
        
        Args:
            session_id: 会话ID
            
        Returns:
            JSON字符串
        """
        stats = self.get_session_statistics(session_id)
        return json.dumps(stats, default=str, ensure_ascii=False, indent=2)
    
    def export_statistics_to_json(
        self,
        start_date: date,
        end_date: date
    ) -> str:
        """
        导出统计数据为JSON
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            JSON字符串
        """
        data = {
            'period': {
                'start_date': str(start_date),
                'end_date': str(end_date)
            },
            'behavior_distribution': self.get_behavior_distribution(start_date, end_date),
            'alert_distribution': self.get_alert_distribution(start_date, end_date),
            'top_warning_behaviors': self.get_top_warning_behaviors(start_date, end_date),
            'daily_summaries': self.get_daily_summaries(start_date, end_date)
        }
        return json.dumps(data, default=str, ensure_ascii=False, indent=2)
