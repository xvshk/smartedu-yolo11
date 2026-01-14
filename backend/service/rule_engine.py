"""
预警规则引擎模块
Alert rule engine for evaluating and managing alert rules
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.module.manager import DatabaseManager
from .interfaces import IRuleEngineService

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
    
    def to_dict(self) -> Dict:
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'alert_level': self.alert_level,
            'behavior_type': self.behavior_type,
            'matched_count': self.matched_count,
            'threshold': self.threshold,
            'confidence': self.confidence,
            'message': self.message
        }


class EvaluationContext:
    """规则评估上下文"""
    def __init__(self, session_id: int, current_time: datetime, time_window_seconds: int = 60,
                 historical_detections: List[Dict] = None, behavior_counts: Dict[str, int] = None):
        self.session_id = session_id
        self.current_time = current_time
        self.time_window_seconds = time_window_seconds
        self.historical_detections = historical_detections or []
        self.behavior_counts = behavior_counts or {}


class RuleEngine(IRuleEngineService):
    """
    规则引擎 - 管理和评估预警规则
    """
    
    def __init__(self, db: DatabaseManager = None):
        """
        初始化规则引擎
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db or DatabaseManager()
        self._rules_cache = None
        self._cache_time = None
        self._cache_ttl = 60  # 缓存60秒
    
    def evaluate_alert_rules(self, detection_result: Any) -> Dict[str, Any]:
        """
        评估预警规则
        
        Args:
            detection_result: 检测结果
            
        Returns:
            评估结果字典
        """
        try:
            # 简化实现，返回默认结果
            return {
                'success': True,
                'matches': [],
                'total_matches': 0,
                'alert_triggered': False,
                'highest_alert_level': 0
            }
            
        except Exception as e:
            logger.error(f"Evaluate alert rules error: {e}")
            return {
                'success': False,
                'error': str(e),
                'matches': [],
                'total_matches': 0,
                'alert_triggered': False,
                'highest_alert_level': 0
            }
    
    def evaluate(self, detections: List[Dict], context: 'EvaluationContext') -> List['RuleMatch']:
        """
        评估检测结果并返回规则匹配
        
        Args:
            detections: 检测结果列表
            context: 评估上下文
            
        Returns:
            规则匹配列表
        """
        try:
            matches = []
            
            # 简化实现：基于检测结果生成基本预警
            behavior_counts = {}
            for detection in detections:
                behavior_type = detection.get('class_name') or detection.get('behavior_type', 'unknown')
                confidence = detection.get('confidence', 0.5)
                
                if behavior_type not in behavior_counts:
                    behavior_counts[behavior_type] = {'count': 0, 'max_confidence': 0}
                
                behavior_counts[behavior_type]['count'] += 1
                behavior_counts[behavior_type]['max_confidence'] = max(
                    behavior_counts[behavior_type]['max_confidence'], confidence
                )
            
            # 为每种行为类型生成规则匹配
            for behavior_type, stats in behavior_counts.items():
                if behavior_type in ['睡觉', '使用电子设备', '交谈', '低头', '站立']:
                    alert_level = self._classify_alert_level(behavior_type, stats['count'], stats['max_confidence'])
                    
                    if alert_level > 0:  # 只有非正常级别才生成匹配
                        match = RuleMatch(
                            rule_id=1,  # 默认规则ID
                            rule_name=f"{behavior_type}预警规则",
                            rule_type="frequency",
                            alert_level=alert_level,
                            behavior_type=behavior_type,
                            matched_count=stats['count'],
                            threshold=1,
                            confidence=stats['max_confidence'],
                            message=f"检测到{stats['count']}次{behavior_type}行为"
                        )
                        matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Evaluate rules error: {e}")
            return []
    
    def _classify_alert_level(self, behavior_type: str, count: int, confidence: float) -> int:
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
    
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """
        获取所有活跃规则
        
        Returns:
            活跃的规则列表
        """
        # 简化实现，返回一些默认规则
        return [
            {
                'rule_id': 1,
                'rule_name': '睡觉预警规则',
                'rule_type': 'frequency',
                'behavior_type': '睡觉',
                'alert_level': 2,
                'threshold_count': 1,
                'time_window_seconds': 60,
                'is_active': True,
                'description': '检测到睡觉行为时触发预警'
            },
            {
                'rule_id': 2,
                'rule_name': '使用电子设备预警',
                'rule_type': 'frequency',
                'behavior_type': '使用电子设备',
                'alert_level': 3,
                'threshold_count': 1,
                'time_window_seconds': 30,
                'is_active': True,
                'description': '检测到使用电子设备时触发严重预警'
            },
            {
                'rule_id': 3,
                'rule_name': '交谈预警规则',
                'rule_type': 'frequency',
                'behavior_type': '交谈',
                'alert_level': 1,
                'threshold_count': 3,
                'time_window_seconds': 120,
                'is_active': True,
                'description': '频繁交谈时触发预警'
            }
        ]
    
    def list_rules(self, is_active: bool = None, rule_type: str = None, 
                   page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """
        获取规则列表（分页）
        
        Args:
            is_active: 是否活跃筛选
            rule_type: 规则类型筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            (规则列表, 总数)
        """
        all_rules = self.get_active_rules()
        
        # 应用筛选
        filtered_rules = all_rules
        if is_active is not None:
            filtered_rules = [r for r in filtered_rules if r['is_active'] == is_active]
        if rule_type:
            filtered_rules = [r for r in filtered_rules if r['rule_type'] == rule_type]
        
        # 分页
        total = len(filtered_rules)
        start = (page - 1) * page_size
        end = start + page_size
        page_rules = filtered_rules[start:end]
        
        return page_rules, total
    
    def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个规则详情
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则详情或None
        """
        rules = self.get_active_rules()
        for rule in rules:
            if rule['rule_id'] == rule_id:
                return rule
        return None
    
    def create_rule(self, rule_data: Dict[str, Any]) -> int:
        """
        创建规则
        
        Args:
            rule_data: 规则数据字典
            
        Returns:
            新规则的ID
        """
        # 简化实现，返回新规则ID
        return 4
    
    def create_rule_detailed(self, rule_name: str, rule_type: str, conditions: Dict = None,
                    alert_level: int = 1, description: str = None, behavior_type: str = None,
                    threshold_count: int = 1, time_window_seconds: int = 60,
                    created_by: int = None) -> Dict[str, Any]:
        """
        创建新规则（详细版本，用于API调用）
        
        Args:
            rule_name: 规则名称
            rule_type: 规则类型
            conditions: 条件配置
            alert_level: 预警级别
            description: 描述
            behavior_type: 行为类型
            threshold_count: 阈值数量
            time_window_seconds: 时间窗口
            created_by: 创建者ID
            
        Returns:
            创建的规则
        """
        # 简化实现，返回新规则
        new_rule = {
            'rule_id': 4,  # 新规则ID
            'rule_name': rule_name,
            'rule_type': rule_type,
            'behavior_type': behavior_type,
            'alert_level': alert_level,
            'threshold_count': threshold_count,
            'time_window_seconds': time_window_seconds,
            'is_active': True,
            'description': description,
            'conditions': conditions or {},
            'created_by': created_by,
            'created_at': datetime.now().isoformat()
        }
        return new_rule
    
    def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """
        更新规则
        
        Args:
            rule_id: 规则ID
            rule_data: 更新的规则数据
            
        Returns:
            是否更新成功
        """
        # 简化实现
        return True
    
    def update_rule_detailed(self, rule_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """
        更新规则（详细版本，用于API调用）
        
        Args:
            rule_id: 规则ID
            **kwargs: 更新的字段
            
        Returns:
            更新后的规则或None
        """
        rule = self.get_rule(rule_id)
        if rule:
            # 更新字段
            for key, value in kwargs.items():
                if value is not None and key in rule:
                    rule[key] = value
            rule['updated_at'] = datetime.now().isoformat()
            return rule
        return None
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        删除预警规则
        
        Returns:
            是否删除成功
        """
        # 简化实现
        return True
    
    def get_user_notification_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户通知偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            通知偏好配置
        """
        # 简化实现，返回默认偏好
        return {
            'user_id': user_id,
            'alert_level_0': False,  # 正常级别不通知
            'alert_level_1': True,   # 轻度预警通知
            'alert_level_2': True,   # 中度预警通知
            'alert_level_3': True,   # 严重预警通知
            'sound_enabled': True,   # 声音提醒
            'email_enabled': False,  # 邮件通知
            'updated_at': datetime.now().isoformat()
        }
    
    def update_user_notification_preferences(self, user_id: int, preferences: Dict[str, Any]) -> None:
        """
        更新用户通知偏好
        
        Args:
            user_id: 用户ID
            preferences: 偏好配置
        """
        # 简化实现，记录日志
        logger.info(f"Updated notification preferences for user {user_id}: {preferences}")


# 单例模式
_rule_engine_instance = None


def get_rule_engine() -> RuleEngine:
    """获取规则引擎单例"""
    global _rule_engine_instance
    if _rule_engine_instance is None:
        _rule_engine_instance = RuleEngine()
    return _rule_engine_instance