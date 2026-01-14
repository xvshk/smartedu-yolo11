"""
预警服务模块
Alert service for generating, managing, and analyzing alerts
"""
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.model.ManagerModel import DatabaseManager
from backend.model.AlertModel import AlertRepository
from backend.model.RuleModel import RuleRepository
from backend.service.Rule_engineService import get_rule_engine

logger = logging.getLogger(__name__)


class RuleMatch:
    """规则匹配结果"""
    def __init__(self, rule_id: int, rule_name: str, rule_type: str, alert_level: int, 
                 behavior_type: str, matched_count: int, threshold: int, confidence: float, message: str):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.alert_level = alert_level
        self.behavior_type = behavior_type
        self.matched_count = matched_count
        self.threshold = threshold
        self.confidence = confidence
        self.message = message


class EvaluationContext:
    """规则评估上下文"""
    def __init__(self, session_id: int, current_time: datetime, time_window_seconds: int = 60,
                 historical_detections: List[Dict] = None, behavior_counts: Dict[str, int] = None):
        self.session_id = session_id
        self.current_time = current_time
        self.time_window_seconds = time_window_seconds
        self.historical_detections = historical_detections or []
        self.behavior_counts = behavior_counts or {}


@dataclass
class Alert:
    """预警数据模型"""
    alert_id: int
    session_id: int
    alert_level: int  # 0-3: 正常、轻度、中度、严重
    alert_type: str  # rule_based, ml_predicted, anomaly_detected
    behavior_type: str
    behavior_count: int
    confidence: float
    location_info: Dict[str, Any]
    triggered_rules: List[int]
    risk_score: Optional[float]
    anomaly_score: Optional[float]
    suggestions: List[str]
    created_at: datetime
    is_read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if isinstance(result['created_at'], datetime):
            result['created_at'] = result['created_at'].isoformat()
        return result


@dataclass
class AlertStatistics:
    """预警统计数据"""
    total: int
    level_distribution: Dict[int, int]
    behavior_distribution: Dict[str, int]
    time_series: List[Dict]
    peak_hour: Optional[int]
    top_behaviors: List[Dict]
    trend: Dict[str, Any]
    period: str
    start_date: str
    end_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# 预警级别名称映射
ALERT_LEVEL_NAMES = {
    0: '正常',
    1: '轻度预警',
    2: '中度预警',
    3: '严重预警'
}

# 干预建议模板
INTERVENTION_SUGGESTIONS = {
    '睡觉': ['轻声提醒学生', '走近学生位置', '课间单独沟通'],
    '交谈': ['眼神示意', '点名提问', '调整座位'],
    '使用电子设备': ['提醒收起设备', '暂时收管设备'],
    '低头': ['提问互动', '调整教学节奏'],
    '站立': ['询问是否需要帮助', '提醒注意课堂纪律'],
}


class AlertService:
    """
    预警服务 - 核心预警生成和管理
    
    功能:
    - 根据检测结果和规则生成预警
    - 预警聚合和去重
    - 预警历史查询和统计
    - 预警级别分类
    """
    
    def __init__(self, db: DatabaseManager = None):
        """
        初始化预警服务
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db or DatabaseManager()
        self.alert_repo = AlertRepository(self.db)
        self.rule_repo = RuleRepository(self.db)
        self.rule_engine = get_rule_engine()
    
    def generate_alerts(
        self,
        detections: List[Dict],
        session_id: int,
        context: EvaluationContext = None
    ) -> List[Alert]:
        """
        根据检测结果生成预警
        
        Args:
            detections: 检测结果列表
            session_id: 会话ID
            context: 评估上下文
            
        Returns:
            生成的预警列表
        """
        if not detections:
            return []
        
        # 创建评估上下文
        if context is None:
            context = EvaluationContext(
                session_id=session_id,
                current_time=datetime.now()
            )
        
        # 评估规则
        rule_matches = self.rule_engine.evaluate(detections, context)
        
        # 生成预警
        alerts = []
        for match in rule_matches:
            alert = self._create_alert_from_match(match, session_id, detections)
            if alert:
                alerts.append(alert)
        
        # 聚合相似预警
        aggregated_alerts = self.aggregate_alerts(alerts)
        
        # 持久化预警
        saved_alerts = []
        for alert in aggregated_alerts:
            alert_id = self._save_alert(alert)
            alert.alert_id = alert_id
            saved_alerts.append(alert)
        
        return saved_alerts
    
    def _create_alert_from_match(
        self,
        match: RuleMatch,
        session_id: int,
        detections: List[Dict]
    ) -> Optional[Alert]:
        """从规则匹配创建预警"""
        # 获取位置信息
        location_info = self._extract_location_info(detections, match.behavior_type)
        
        # 获取干预建议
        suggestions = self._get_suggestions(match.behavior_type, match.alert_level)
        
        return Alert(
            alert_id=0,  # 待保存后更新
            session_id=session_id,
            alert_level=match.alert_level,
            alert_type='rule_based',
            behavior_type=match.behavior_type,
            behavior_count=match.matched_count,
            confidence=match.confidence,
            location_info=location_info,
            triggered_rules=[match.rule_id],
            risk_score=None,
            anomaly_score=None,
            suggestions=suggestions,
            created_at=datetime.now(),
            is_read=False
        )
    
    def _extract_location_info(
        self,
        detections: List[Dict],
        behavior_type: str
    ) -> Dict[str, Any]:
        """提取行为位置信息"""
        bboxes = []
        for det in detections:
            det_behavior = det.get('class_name') or det.get('behavior_type')
            if det_behavior == behavior_type or not behavior_type:
                bbox = det.get('bbox')
                if bbox:
                    bboxes.append(bbox)
        
        if not bboxes:
            return {}
        
        return {
            'bboxes': bboxes,
            'count': len(bboxes)
        }
    
    def _get_suggestions(self, behavior_type: str, alert_level: int) -> List[str]:
        """获取干预建议"""
        suggestions = INTERVENTION_SUGGESTIONS.get(behavior_type, [])
        
        # 根据预警级别调整建议
        if alert_level >= 3 and suggestions:
            # 严重预警，返回所有建议
            return suggestions
        elif alert_level >= 2 and suggestions:
            # 中度预警，返回前两个建议
            return suggestions[:2]
        elif suggestions:
            # 轻度预警，返回第一个建议
            return suggestions[:1]
        
        return ['关注学生状态']
    
    def _save_alert(self, alert: Alert) -> int:
        """保存预警到数据库"""
        return self.alert_repo.create_alert(
            session_id=alert.session_id,
            alert_level=alert.alert_level,
            alert_type=alert.alert_type,
            behavior_type=alert.behavior_type,
            behavior_count=alert.behavior_count,
            confidence=alert.confidence,
            location_info=alert.location_info,
            triggered_rules=alert.triggered_rules,
            risk_score=alert.risk_score,
            anomaly_score=alert.anomaly_score,
            suggestions=alert.suggestions
        )
    
    def aggregate_alerts(
        self,
        alerts: List[Alert],
        time_window: int = 5
    ) -> List[Alert]:
        """
        聚合时间窗口内的相似预警
        
        Args:
            alerts: 原始预警列表
            time_window: 聚合时间窗口（秒）
            
        Returns:
            聚合后的预警列表
        """
        if not alerts:
            return []
        
        # 按行为类型分组
        groups: Dict[str, List[Alert]] = {}
        for alert in alerts:
            key = alert.behavior_type
            if key not in groups:
                groups[key] = []
            groups[key].append(alert)
        
        # 聚合每组预警
        aggregated = []
        for behavior_type, group in groups.items():
            if len(group) == 1:
                aggregated.append(group[0])
            else:
                # 合并同类预警
                merged = self._merge_alerts(group)
                aggregated.append(merged)
        
        return aggregated
    
    def _merge_alerts(self, alerts: List[Alert]) -> Alert:
        """合并多个预警"""
        if not alerts:
            raise ValueError("Cannot merge empty alert list")
        
        # 取最高预警级别
        max_level = max(a.alert_level for a in alerts)
        
        # 合并触发规则
        all_rules = set()
        for a in alerts:
            all_rules.update(a.triggered_rules)
        
        # 合并位置信息
        all_bboxes = []
        for a in alerts:
            bboxes = a.location_info.get('bboxes', [])
            all_bboxes.extend(bboxes)
        
        # 合并建议（去重）
        all_suggestions = []
        seen = set()
        for a in alerts:
            for s in a.suggestions:
                if s not in seen:
                    all_suggestions.append(s)
                    seen.add(s)
        
        # 计算平均置信度
        avg_confidence = sum(a.confidence for a in alerts) / len(alerts)
        
        # 总行为数
        total_count = sum(a.behavior_count for a in alerts)
        
        return Alert(
            alert_id=0,
            session_id=alerts[0].session_id,
            alert_level=max_level,
            alert_type=alerts[0].alert_type,
            behavior_type=alerts[0].behavior_type,
            behavior_count=total_count,
            confidence=round(avg_confidence, 3),
            location_info={'bboxes': all_bboxes, 'count': len(all_bboxes)},
            triggered_rules=list(all_rules),
            risk_score=max((a.risk_score for a in alerts if a.risk_score), default=None),
            anomaly_score=max((a.anomaly_score for a in alerts if a.anomaly_score), default=None),
            suggestions=all_suggestions[:5],  # 最多5条建议
            created_at=datetime.now(),
            is_read=False
        )
    
    def classify_alert_level(self, behavior_type: str, count: int, confidence: float) -> int:
        """
        根据行为类型、数量和置信度分类预警级别
        
        Args:
            behavior_type: 行为类型
            count: 行为数量
            confidence: 置信度
            
        Returns:
            预警级别 (0-3)
        """
        # 严重预警行为
        severe_behaviors = ['睡觉', '使用电子设备']
        # 中度预警行为
        moderate_behaviors = ['交谈']
        # 轻度预警行为
        mild_behaviors = ['低头', '站立']
        
        if behavior_type in severe_behaviors:
            if count >= 3 or confidence >= 0.9:
                return 3
            elif count >= 2 or confidence >= 0.7:
                return 2
            else:
                return 1
        elif behavior_type in moderate_behaviors:
            if count >= 5 or confidence >= 0.9:
                return 3
            elif count >= 3 or confidence >= 0.7:
                return 2
            else:
                return 1
        elif behavior_type in mild_behaviors:
            if count >= 5:
                return 2
            elif count >= 2:
                return 1
            else:
                return 0
        else:
            # 正常行为
            return 0
    
    def get_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """获取单个预警详情"""
        return self.alert_repo.get_alert(alert_id)
    
    def get_alert_history(
        self,
        start_date: date = None,
        end_date: date = None,
        alert_level: int = None,
        behavior_type: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        查询预警历史
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            alert_level: 预警级别筛选
            behavior_type: 行为类型筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            (预警列表, 总数)
        """
        offset = (page - 1) * page_size
        alerts = self.alert_repo.list_alerts(
            start_date=start_date,
            end_date=end_date,
            alert_level=alert_level,
            behavior_type=behavior_type,
            limit=page_size,
            offset=offset
        )
        total = self.alert_repo.count_alerts(
            start_date=start_date,
            end_date=end_date,
            alert_level=alert_level,
            behavior_type=behavior_type
        )
        return alerts, total

    
    def get_statistics(
        self,
        period: str = 'daily',
        start_date: date = None,
        end_date: date = None
    ) -> AlertStatistics:
        """
        获取预警统计
        
        Args:
            period: 统计周期 (daily/weekly/monthly)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            预警统计数据
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # 获取基础统计
        stats = self.alert_repo.get_statistics(
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        
        # 获取趋势
        trend = self.alert_repo.get_trend(start_date, end_date)
        
        return AlertStatistics(
            total=stats['total'],
            level_distribution=stats['level_distribution'],
            behavior_distribution=stats['behavior_distribution'],
            time_series=stats['time_series'],
            peak_hour=stats['peak_hour'],
            top_behaviors=stats['top_behaviors'],
            trend=trend,
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
    
    def get_session_alerts(self, session_id: int) -> List[Dict[str, Any]]:
        """获取会话的所有预警"""
        return self.alert_repo.list_alerts(session_id=session_id, limit=1000)
    
    def get_unread_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取未读预警"""
        return self.alert_repo.list_alerts(is_read=False, limit=limit)
    
    def mark_alert_read(self, alert_id: int) -> None:
        """标记预警为已读"""
        self.alert_repo.mark_as_read(alert_id)
    
    def mark_all_read(self, session_id: int = None) -> int:
        """批量标记预警为已读"""
        return self.alert_repo.mark_all_as_read(session_id)
    
    def delete_alert(self, alert_id: int) -> None:
        """删除预警"""
        self.alert_repo.delete_alert(alert_id)
    
    def export_alerts(
        self,
        start_date: date = None,
        end_date: date = None,
        alert_level: int = None,
        format: str = 'csv'
    ) -> str:
        """
        导出预警数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            alert_level: 预警级别筛选
            format: 导出格式 (csv/json)
            
        Returns:
            导出的数据字符串
        """
        alerts = self.alert_repo.list_alerts(
            start_date=start_date,
            end_date=end_date,
            alert_level=alert_level,
            limit=10000
        )
        
        if format == 'json':
            import json
            return json.dumps(alerts, ensure_ascii=False, default=str, indent=2)
        else:
            # CSV格式
            import csv
            import io
            
            output = io.StringIO()
            if alerts:
                fieldnames = ['alert_id', 'session_id', 'alert_level', 'alert_type',
                             'behavior_type', 'behavior_count', 'confidence',
                             'created_at', 'is_read']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for alert in alerts:
                    writer.writerow(alert)
            
            return output.getvalue()
    
    def cleanup_old_alerts(self, retention_days: int = 90) -> int:
        """
        清理旧预警数据
        
        Args:
            retention_days: 保留天数
            
        Returns:
            删除的记录数
        """
        return self.alert_repo.cleanup_old_alerts(retention_days)
    
    def create_ml_alert(
        self,
        session_id: int,
        alert_type: str,
        behavior_type: str,
        risk_score: float = None,
        anomaly_score: float = None,
        confidence: float = 0.5,
        suggestions: List[str] = None
    ) -> int:
        """
        创建机器学习预警
        
        Args:
            session_id: 会话ID
            alert_type: 预警类型 (ml_predicted/anomaly_detected)
            behavior_type: 行为类型
            risk_score: 风险分数
            anomaly_score: 异常分数
            confidence: 置信度
            suggestions: 干预建议
            
        Returns:
            预警ID
        """
        # 根据分数确定预警级别
        score = risk_score or anomaly_score or 0.5
        if score >= 0.8:
            alert_level = 3
        elif score >= 0.6:
            alert_level = 2
        elif score >= 0.4:
            alert_level = 1
        else:
            alert_level = 0
        
        if suggestions is None:
            suggestions = self._get_suggestions(behavior_type, alert_level)
        
        return self.alert_repo.create_alert(
            session_id=session_id,
            alert_level=alert_level,
            alert_type=alert_type,
            behavior_type=behavior_type,
            behavior_count=1,
            confidence=confidence,
            location_info={},
            triggered_rules=[],
            risk_score=risk_score,
            anomaly_score=anomaly_score,
            suggestions=suggestions
        )


# 单例模式
_alert_service_instance = None


def get_alert_service() -> AlertService:
    """获取预警服务单例"""
    global _alert_service_instance
    if _alert_service_instance is None:
        _alert_service_instance = AlertService()
    return _alert_service_instance
