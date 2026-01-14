"""
预警数据仓库模块
Alert data repository for alerts, rules, interventions, and notification preferences
"""
import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from backend.model.ManagerModel import DatabaseManager

logger = logging.getLogger(__name__)


class AlertRepository:
    """预警数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        """
        初始化预警数据仓库
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
    
    # ==================== Alert 操作 ====================
    
    def create_alert(
        self,
        session_id: int,
        alert_level: int,
        alert_type: str,
        behavior_type: str,
        behavior_count: int = 1,
        confidence: float = None,
        location_info: Dict = None,
        triggered_rules: List[int] = None,
        risk_score: float = None,
        anomaly_score: float = None,
        suggestions: List[str] = None
    ) -> int:
        """
        创建预警记录
        
        Args:
            session_id: 会话ID
            alert_level: 预警级别 (0-3)
            alert_type: 预警类型 (rule_based/ml_predicted/anomaly_detected)
            behavior_type: 行为类型
            behavior_count: 行为数量
            confidence: 置信度
            location_info: 位置信息 (bbox)
            triggered_rules: 触发的规则ID列表
            risk_score: 风险分数
            anomaly_score: 异常分数
            suggestions: 干预建议列表
            
        Returns:
            新创建的alert_id
        """
        sql = """
            INSERT INTO alerts 
            (session_id, alert_level, alert_type, behavior_type, behavior_count,
             confidence, location_info, triggered_rules, risk_score, anomaly_score, suggestions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (
            session_id,
            alert_level,
            alert_type,
            behavior_type,
            behavior_count,
            confidence,
            json.dumps(location_info) if location_info else None,
            json.dumps(triggered_rules) if triggered_rules else None,
            risk_score,
            anomaly_score,
            json.dumps(suggestions) if suggestions else None
        ))
    
    def create_alerts_batch(self, alerts: List[Dict[str, Any]]) -> int:
        """
        批量创建预警记录
        
        Args:
            alerts: 预警列表
            
        Returns:
            插入的记录数
        """
        if not alerts:
            return 0
        
        sql = """
            INSERT INTO alerts 
            (session_id, alert_level, alert_type, behavior_type, behavior_count,
             confidence, location_info, triggered_rules, risk_score, anomaly_score, suggestions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params_list = [
            (
                a['session_id'],
                a['alert_level'],
                a['alert_type'],
                a['behavior_type'],
                a.get('behavior_count', 1),
                a.get('confidence'),
                json.dumps(a.get('location_info')) if a.get('location_info') else None,
                json.dumps(a.get('triggered_rules')) if a.get('triggered_rules') else None,
                a.get('risk_score'),
                a.get('anomaly_score'),
                json.dumps(a.get('suggestions')) if a.get('suggestions') else None
            )
            for a in alerts
        ]
        return self.db.execute_many(sql, params_list)
    
    def get_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个预警详情
        
        Args:
            alert_id: 预警ID
            
        Returns:
            预警信息字典或None
        """
        sql = "SELECT * FROM alerts WHERE alert_id = %s"
        result = self.db.query_one(sql, (alert_id,))
        if result:
            result = self._parse_alert_json_fields(result)
        return result
    
    def list_alerts(
        self,
        session_id: int = None,
        start_date: date = None,
        end_date: date = None,
        alert_level: int = None,
        alert_type: str = None,
        behavior_type: str = None,
        is_read: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询预警列表
        
        Args:
            session_id: 会话ID筛选
            start_date: 开始日期
            end_date: 结束日期
            alert_level: 预警级别筛选
            alert_type: 预警类型筛选
            behavior_type: 行为类型筛选
            is_read: 是否已读筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            预警列表
        """
        conditions = []
        params = []
        
        if session_id is not None:
            conditions.append("session_id = %s")
            params.append(session_id)
        if start_date:
            conditions.append("DATE(created_at) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= %s")
            params.append(end_date)
        if alert_level is not None:
            conditions.append("alert_level = %s")
            params.append(alert_level)
        if alert_type:
            conditions.append("alert_type = %s")
            params.append(alert_type)
        if behavior_type:
            conditions.append("behavior_type = %s")
            params.append(behavior_type)
        if is_read is not None:
            conditions.append("is_read = %s")
            params.append(is_read)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM alerts 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        results = self.db.query(sql, tuple(params))
        return [self._parse_alert_json_fields(r) for r in results]
    
    def count_alerts(
        self,
        session_id: int = None,
        start_date: date = None,
        end_date: date = None,
        alert_level: int = None,
        alert_type: str = None,
        behavior_type: str = None,
        is_read: bool = None
    ) -> int:
        """
        统计预警数量
        
        Returns:
            预警数量
        """
        conditions = []
        params = []
        
        if session_id is not None:
            conditions.append("session_id = %s")
            params.append(session_id)
        if start_date:
            conditions.append("DATE(created_at) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= %s")
            params.append(end_date)
        if alert_level is not None:
            conditions.append("alert_level = %s")
            params.append(alert_level)
        if alert_type:
            conditions.append("alert_type = %s")
            params.append(alert_type)
        if behavior_type:
            conditions.append("behavior_type = %s")
            params.append(behavior_type)
        if is_read is not None:
            conditions.append("is_read = %s")
            params.append(is_read)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT COUNT(*) as count FROM alerts {where_clause}"
        result = self.db.query_one(sql, tuple(params))
        return result['count'] if result else 0
    
    def mark_as_read(self, alert_id: int) -> None:
        """标记预警为已读"""
        sql = "UPDATE alerts SET is_read = TRUE WHERE alert_id = %s"
        self.db.execute(sql, (alert_id,))
    
    def mark_all_as_read(self, session_id: int = None) -> int:
        """
        批量标记预警为已读
        
        Args:
            session_id: 可选的会话ID筛选
            
        Returns:
            更新的记录数
        """
        if session_id:
            sql = "UPDATE alerts SET is_read = TRUE WHERE session_id = %s AND is_read = FALSE"
            return self.db.execute(sql, (session_id,))
        else:
            sql = "UPDATE alerts SET is_read = TRUE WHERE is_read = FALSE"
            return self.db.execute(sql)
    
    def delete_alert(self, alert_id: int) -> None:
        """删除预警"""
        sql = "DELETE FROM alerts WHERE alert_id = %s"
        self.db.execute(sql, (alert_id,))
    
    def delete_alerts_by_session(self, session_id: int) -> int:
        """删除会话的所有预警"""
        sql = "DELETE FROM alerts WHERE session_id = %s"
        return self.db.execute(sql, (session_id,))
    
    def _parse_alert_json_fields(self, alert: Dict) -> Dict:
        """解析预警中的JSON字段"""
        if alert.get('location_info') and isinstance(alert['location_info'], str):
            alert['location_info'] = json.loads(alert['location_info'])
        if alert.get('triggered_rules') and isinstance(alert['triggered_rules'], str):
            alert['triggered_rules'] = json.loads(alert['triggered_rules'])
        if alert.get('suggestions') and isinstance(alert['suggestions'], str):
            alert['suggestions'] = json.loads(alert['suggestions'])
        return alert
    
    # ==================== 统计功能 ====================
    
    def get_statistics(
        self,
        start_date: date = None,
        end_date: date = None,
        period: str = 'daily'
    ) -> Dict[str, Any]:
        """
        获取预警统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            period: 统计周期 (daily/weekly/monthly)
            
        Returns:
            统计数据
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # 总数统计
        total = self.count_alerts(start_date=start_date, end_date=end_date)
        
        # 按级别统计
        level_stats = self._get_level_distribution(start_date, end_date)
        
        # 按行为类型统计
        behavior_stats = self._get_behavior_distribution(start_date, end_date)
        
        # 按时间段统计
        time_series = self._get_time_series(start_date, end_date, period)
        
        # 峰值时间
        peak_hour = self._get_peak_hour(start_date, end_date)
        
        # 最频繁行为
        top_behaviors = self._get_top_behaviors(start_date, end_date, limit=5)
        
        return {
            'total': total,
            'level_distribution': level_stats,
            'behavior_distribution': behavior_stats,
            'time_series': time_series,
            'peak_hour': peak_hour,
            'top_behaviors': top_behaviors,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    def _get_level_distribution(self, start_date: date, end_date: date) -> Dict[int, int]:
        """获取预警级别分布"""
        sql = """
            SELECT alert_level, COUNT(*) as count
            FROM alerts
            WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s
            GROUP BY alert_level
        """
        results = self.db.query(sql, (start_date, end_date))
        return {r['alert_level']: r['count'] for r in results}
    
    def _get_behavior_distribution(self, start_date: date, end_date: date) -> Dict[str, int]:
        """获取行为类型分布"""
        sql = """
            SELECT behavior_type, COUNT(*) as count
            FROM alerts
            WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s
            GROUP BY behavior_type
            ORDER BY count DESC
        """
        results = self.db.query(sql, (start_date, end_date))
        return {r['behavior_type']: r['count'] for r in results}
    
    def _get_time_series(self, start_date: date, end_date: date, period: str) -> List[Dict]:
        """获取时间序列数据"""
        if period == 'daily':
            date_format = '%Y-%m-%d'
            group_by = 'DATE(created_at)'
        elif period == 'weekly':
            date_format = '%Y-%u'
            group_by = 'YEARWEEK(created_at)'
        else:  # monthly
            date_format = '%Y-%m'
            group_by = "DATE_FORMAT(created_at, '%Y-%m')"
        
        sql = f"""
            SELECT {group_by} as period, COUNT(*) as count
            FROM alerts
            WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s
            GROUP BY {group_by}
            ORDER BY period
        """
        results = self.db.query(sql, (start_date, end_date))
        return [{'period': str(r['period']), 'count': r['count']} for r in results]
    
    def _get_peak_hour(self, start_date: date, end_date: date) -> Optional[int]:
        """获取预警峰值小时"""
        sql = """
            SELECT HOUR(created_at) as hour, COUNT(*) as count
            FROM alerts
            WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s
            GROUP BY HOUR(created_at)
            ORDER BY count DESC
            LIMIT 1
        """
        result = self.db.query_one(sql, (start_date, end_date))
        return result['hour'] if result else None
    
    def _get_top_behaviors(self, start_date: date, end_date: date, limit: int = 5) -> List[Dict]:
        """获取最频繁的行为类型"""
        sql = """
            SELECT behavior_type, COUNT(*) as count
            FROM alerts
            WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s
            GROUP BY behavior_type
            ORDER BY count DESC
            LIMIT %s
        """
        return self.db.query(sql, (start_date, end_date, limit))
    
    def get_trend(self, current_start: date, current_end: date) -> Dict[str, Any]:
        """
        计算趋势（与上一周期对比）
        
        Args:
            current_start: 当前周期开始日期
            current_end: 当前周期结束日期
            
        Returns:
            趋势数据
        """
        period_days = (current_end - current_start).days + 1
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=period_days - 1)
        
        current_count = self.count_alerts(start_date=current_start, end_date=current_end)
        previous_count = self.count_alerts(start_date=previous_start, end_date=previous_end)
        
        if previous_count > 0:
            change_percent = ((current_count - previous_count) / previous_count) * 100
        else:
            change_percent = 100.0 if current_count > 0 else 0.0
        
        return {
            'current_count': current_count,
            'previous_count': previous_count,
            'change_percent': round(change_percent, 2),
            'trend': 'up' if change_percent > 0 else ('down' if change_percent < 0 else 'stable')
        }
    
    # ==================== 数据清理 ====================
    
    def cleanup_old_alerts(self, retention_days: int) -> int:
        """
        清理旧预警数据
        
        Args:
            retention_days: 保留天数
            
        Returns:
            删除的记录数
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # 先统计要删除的数量
        count_sql = "SELECT COUNT(*) as count FROM alerts WHERE created_at < %s"
        result = self.db.query_one(count_sql, (cutoff_date,))
        count = result['count'] if result else 0
        
        # 删除旧记录
        delete_sql = "DELETE FROM alerts WHERE created_at < %s"
        self.db.execute(delete_sql, (cutoff_date,))
        
        return count
