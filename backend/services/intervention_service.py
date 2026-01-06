"""
干预建议服务模块
Intervention service for generating and managing intervention suggestions
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.manager import DatabaseManager
from src.database.repositories.rule_repository import RuleRepository

logger = logging.getLogger(__name__)


@dataclass
class InterventionSuggestion:
    """干预建议"""
    action: str
    action_cn: str
    effectiveness: float
    priority: int
    behavior_type: str
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


# 干预建议模板
INTERVENTION_TEMPLATES = {
    '睡觉': [
        {'action': 'gentle_reminder', 'action_cn': '轻声提醒', 'effectiveness': 0.7, 'description': '轻声提醒学生注意听讲'},
        {'action': 'approach', 'action_cn': '走近学生位置', 'effectiveness': 0.8, 'description': '走到学生附近，引起注意'},
        {'action': 'private_talk', 'action_cn': '课间单独沟通', 'effectiveness': 0.9, 'description': '课后与学生单独交流，了解原因'},
    ],
    '交谈': [
        {'action': 'eye_contact', 'action_cn': '眼神示意', 'effectiveness': 0.6, 'description': '用眼神示意学生安静'},
        {'action': 'call_name', 'action_cn': '点名提问', 'effectiveness': 0.8, 'description': '点名让学生回答问题'},
        {'action': 'seat_adjustment', 'action_cn': '调整座位', 'effectiveness': 0.85, 'description': '调整学生座位，分开交谈的学生'},
    ],
    '使用电子设备': [
        {'action': 'remind_put_away', 'action_cn': '提醒收起设备', 'effectiveness': 0.75, 'description': '提醒学生收起电子设备'},
        {'action': 'confiscate_temp', 'action_cn': '暂时收管设备', 'effectiveness': 0.9, 'description': '暂时收管设备，课后归还'},
    ],
    '低头': [
        {'action': 'interactive_question', 'action_cn': '提问互动', 'effectiveness': 0.7, 'description': '通过提问让学生参与课堂'},
        {'action': 'adjust_pace', 'action_cn': '调整教学节奏', 'effectiveness': 0.65, 'description': '调整教学节奏，增加互动环节'},
        {'action': 'group_activity', 'action_cn': '小组活动', 'effectiveness': 0.75, 'description': '组织小组讨论或活动'},
    ],
    '站立': [
        {'action': 'ask_need', 'action_cn': '询问是否需要帮助', 'effectiveness': 0.6, 'description': '询问学生是否需要帮助'},
        {'action': 'remind_discipline', 'action_cn': '提醒注意课堂纪律', 'effectiveness': 0.7, 'description': '提醒学生注意课堂纪律'},
    ],
}

# 默认建议（当没有匹配的行为类型时）
DEFAULT_SUGGESTIONS = [
    {'action': 'observe', 'action_cn': '持续观察', 'effectiveness': 0.5, 'description': '继续观察学生状态'},
    {'action': 'general_reminder', 'action_cn': '一般性提醒', 'effectiveness': 0.6, 'description': '进行一般性的课堂提醒'},
]


class InterventionService:
    """
    干预建议服务 - 提供个性化干预建议
    
    功能:
    - 根据预警生成干预建议
    - 记录干预结果
    - 更新干预有效性
    - 基于历史数据优化建议排序
    """
    
    def __init__(self, db: DatabaseManager = None):
        """
        初始化干预建议服务
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db or DatabaseManager()
        self.rule_repo = RuleRepository(self.db)
        
        # 动态有效性调整（基于历史反馈）
        self._effectiveness_adjustments: Dict[str, Dict[str, float]] = {}
    
    def get_suggestions(
        self,
        alert: Dict[str, Any],
        history: List[Dict] = None,
        max_suggestions: int = 3
    ) -> List[InterventionSuggestion]:
        """
        获取干预建议
        
        Args:
            alert: 预警信息
            history: 历史干预记录
            max_suggestions: 最大建议数量
            
        Returns:
            排序后的干预建议列表
        """
        behavior_type = alert.get('behavior_type', '')
        alert_level = alert.get('alert_level', 1)
        
        # 获取模板建议
        templates = INTERVENTION_TEMPLATES.get(behavior_type, DEFAULT_SUGGESTIONS)
        
        suggestions = []
        for i, template in enumerate(templates):
            # 计算调整后的有效性
            base_effectiveness = template['effectiveness']
            adjusted_effectiveness = self._get_adjusted_effectiveness(
                behavior_type, template['action'], base_effectiveness
            )
            
            # 根据预警级别调整优先级
            priority = self._calculate_priority(i, alert_level, adjusted_effectiveness)
            
            suggestion = InterventionSuggestion(
                action=template['action'],
                action_cn=template['action_cn'],
                effectiveness=round(adjusted_effectiveness, 2),
                priority=priority,
                behavior_type=behavior_type,
                description=template.get('description', '')
            )
            suggestions.append(suggestion)
        
        # 按有效性降序排序
        suggestions.sort(key=lambda x: x.effectiveness, reverse=True)
        
        # 如果有历史记录，进一步优化排序
        if history:
            suggestions = self._optimize_with_history(suggestions, history)
        
        return suggestions[:max_suggestions]
    
    def _get_adjusted_effectiveness(
        self,
        behavior_type: str,
        action: str,
        base_effectiveness: float
    ) -> float:
        """获取调整后的有效性"""
        adjustments = self._effectiveness_adjustments.get(behavior_type, {})
        adjustment = adjustments.get(action, 0)
        
        # 应用调整，但保持在[0, 1]范围内
        adjusted = base_effectiveness + adjustment
        return max(0.0, min(1.0, adjusted))
    
    def _calculate_priority(
        self,
        index: int,
        alert_level: int,
        effectiveness: float
    ) -> int:
        """计算建议优先级"""
        # 基础优先级（越小越优先）
        base_priority = index + 1
        
        # 根据预警级别调整
        if alert_level >= 3:
            # 严重预警，优先推荐高效措施
            if effectiveness >= 0.8:
                return base_priority
            else:
                return base_priority + 2
        elif alert_level >= 2:
            # 中度预警
            return base_priority + 1
        else:
            # 轻度预警，优先推荐温和措施
            if effectiveness <= 0.7:
                return base_priority
            else:
                return base_priority + 1
    
    def _optimize_with_history(
        self,
        suggestions: List[InterventionSuggestion],
        history: List[Dict]
    ) -> List[InterventionSuggestion]:
        """基于历史记录优化建议排序"""
        # 统计历史干预的有效性
        action_stats: Dict[str, List[int]] = {}
        for record in history:
            action = record.get('action_taken')
            rating = record.get('effectiveness_rating')
            if action and rating:
                if action not in action_stats:
                    action_stats[action] = []
                action_stats[action].append(rating)
        
        # 计算平均评分
        action_avg: Dict[str, float] = {}
        for action, ratings in action_stats.items():
            action_avg[action] = sum(ratings) / len(ratings)
        
        # 根据历史评分调整排序
        def sort_key(s: InterventionSuggestion) -> float:
            historical_score = action_avg.get(s.action, 3.0)  # 默认3分
            return s.effectiveness * 0.7 + (historical_score / 5) * 0.3
        
        suggestions.sort(key=sort_key, reverse=True)
        return suggestions
    
    def record_intervention(
        self,
        alert_id: int,
        action_taken: str,
        outcome: str = None,
        effectiveness_rating: int = None,
        recorded_by: int = None
    ) -> int:
        """
        记录干预结果
        
        Args:
            alert_id: 预警ID
            action_taken: 采取的干预措施
            outcome: 干预结果描述
            effectiveness_rating: 有效性评分 (1-5)
            recorded_by: 记录者用户ID
            
        Returns:
            干预记录ID
        """
        # 验证评分范围
        if effectiveness_rating is not None:
            if effectiveness_rating < 1 or effectiveness_rating > 5:
                raise ValueError("effectiveness_rating must be between 1 and 5")
        
        intervention_id = self.rule_repo.create_intervention(
            alert_id=alert_id,
            action_taken=action_taken,
            outcome=outcome,
            effectiveness_rating=effectiveness_rating,
            recorded_by=recorded_by
        )
        
        # 如果有评分，更新有效性调整
        if effectiveness_rating is not None:
            self._update_effectiveness_from_rating(
                alert_id, action_taken, effectiveness_rating
            )
        
        return intervention_id
    
    def update_intervention_outcome(
        self,
        intervention_id: int,
        outcome: str,
        effectiveness_rating: int
    ) -> None:
        """
        更新干预结果
        
        Args:
            intervention_id: 干预记录ID
            outcome: 结果描述
            effectiveness_rating: 有效性评分 (1-5)
        """
        if effectiveness_rating < 1 or effectiveness_rating > 5:
            raise ValueError("effectiveness_rating must be between 1 and 5")
        
        self.rule_repo.update_intervention(
            intervention_id=intervention_id,
            outcome=outcome,
            effectiveness_rating=effectiveness_rating
        )
    
    def _update_effectiveness_from_rating(
        self,
        alert_id: int,
        action: str,
        rating: int
    ) -> None:
        """根据评分更新有效性调整"""
        # 获取预警的行为类型
        sql = "SELECT behavior_type FROM alerts WHERE alert_id = %s"
        result = self.db.query_one(sql, (alert_id,))
        
        if not result:
            return
        
        behavior_type = result['behavior_type']
        
        # 计算调整值（评分3为中性，1-2为负面，4-5为正面）
        adjustment = (rating - 3) * 0.02  # 每分调整2%
        
        # 更新调整值
        if behavior_type not in self._effectiveness_adjustments:
            self._effectiveness_adjustments[behavior_type] = {}
        
        current = self._effectiveness_adjustments[behavior_type].get(action, 0)
        # 使用指数移动平均
        self._effectiveness_adjustments[behavior_type][action] = current * 0.8 + adjustment * 0.2
    
    def get_intervention_history(
        self,
        alert_id: int = None,
        behavior_type: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取干预历史
        
        Args:
            alert_id: 预警ID筛选
            behavior_type: 行为类型筛选
            limit: 返回数量限制
            
        Returns:
            干预记录列表
        """
        if alert_id:
            return self.rule_repo.get_interventions_by_alert(alert_id)
        
        # 查询所有干预记录
        sql = """
            SELECT i.*, a.behavior_type, a.alert_level
            FROM interventions i
            JOIN alerts a ON i.alert_id = a.alert_id
        """
        params = []
        
        if behavior_type:
            sql += " WHERE a.behavior_type = %s"
            params.append(behavior_type)
        
        sql += " ORDER BY i.created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.db.query(sql, tuple(params))
    
    def get_effectiveness_statistics(
        self,
        behavior_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取干预有效性统计
        
        Args:
            behavior_type: 行为类型筛选
            
        Returns:
            有效性统计列表
        """
        return self.rule_repo.get_intervention_effectiveness(behavior_type)
    
    def get_recommended_action(
        self,
        behavior_type: str,
        alert_level: int
    ) -> Optional[InterventionSuggestion]:
        """
        获取推荐的干预措施
        
        Args:
            behavior_type: 行为类型
            alert_level: 预警级别
            
        Returns:
            最推荐的干预建议
        """
        alert = {'behavior_type': behavior_type, 'alert_level': alert_level}
        suggestions = self.get_suggestions(alert, max_suggestions=1)
        return suggestions[0] if suggestions else None


# 单例模式
_intervention_service_instance = None


def get_intervention_service() -> InterventionService:
    """获取干预建议服务单例"""
    global _intervention_service_instance
    if _intervention_service_instance is None:
        _intervention_service_instance = InterventionService()
    return _intervention_service_instance
