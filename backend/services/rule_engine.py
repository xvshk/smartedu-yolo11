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

from src.database.manager import DatabaseManager
from src.database.repositories.rule_repository import RuleRepository

logger = logging.getLogger(__name__)


@dataclass
class RuleMatch:
    """规则匹配结果"""
    rule_id: int
    rule_name: str
    rule_type: str
    alert_level: int
    behavior_type: str
    matched_count: int
    threshold: int
    confidence: float
    message: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EvaluationContext:
    """规则评估上下文"""
    session_id: int
    current_time: datetime
    time_window_seconds: int = 60
    historical_detections: List[Dict] = None
    behavior_counts: Dict[str, int] = None
    
    def __post_init__(self):
        if self.historical_detections is None:
            self.historical_detections = []
        if self.behavior_counts is None:
            self.behavior_counts = {}


class RuleEngine:
    """
    规则引擎 - 管理和评估预警规则
    
    支持的规则类型:
    - frequency: 频率规则，在时间窗口内行为出现次数超过阈值
    - duration: 持续时间规则，行为持续时间超过阈值
    - combination: 组合规则，多种行为同时出现
    - threshold: 阈值规则，单次检测中行为数量超过阈值
    """
    
    def __init__(self, db: DatabaseManager = None):
        """
        初始化规则引擎
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db or DatabaseManager()
        self.rule_repo = RuleRepository(self.db)
        self._rules_cache = None
        self._cache_time = None
        self._cache_ttl = 60  # 缓存60秒
    
    def create_rule(
        self,
        rule_name: str,
        rule_type: str,
        conditions: Dict[str, Any],
        alert_level: int = 1,
        description: str = None,
        behavior_type: str = None,
        threshold_count: int = 1,
        time_window_seconds: int = 60,
        created_by: int = None
    ) -> Dict[str, Any]:
        """
        创建预警规则
        
        Args:
            rule_name: 规则名称
            rule_type: 规则类型 (frequency/duration/combination/threshold)
            conditions: 规则条件配置
            alert_level: 预警级别 (0-3)
            description: 规则描述
            behavior_type: 行为类型
            threshold_count: 触发阈值
            time_window_seconds: 时间窗口（秒）
            created_by: 创建者用户ID
            
        Returns:
            创建的规则信息
        """
        # 验证规则类型
        valid_types = ['frequency', 'duration', 'combination', 'threshold']
        if rule_type not in valid_types:
            raise ValueError(f"Invalid rule_type: {rule_type}. Must be one of {valid_types}")
        
        # 验证预警级别
        if alert_level not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid alert_level: {alert_level}. Must be 0, 1, 2, or 3")
        
        # 创建规则
        rule_id = self.rule_repo.create_rule(
            rule_name=rule_name,
            rule_type=rule_type,
            conditions=conditions,
            alert_level=alert_level,
            description=description,
            behavior_type=behavior_type,
            threshold_count=threshold_count,
            time_window_seconds=time_window_seconds,
            created_by=created_by
        )
        
        # 清除缓存
        self._invalidate_cache()
        
        return self.rule_repo.get_rule(rule_id)
    
    def update_rule(
        self,
        rule_id: int,
        rule_name: str = None,
        rule_type: str = None,
        conditions: Dict[str, Any] = None,
        alert_level: int = None,
        description: str = None,
        behavior_type: str = None,
        threshold_count: int = None,
        time_window_seconds: int = None,
        is_active: bool = None
    ) -> Dict[str, Any]:
        """
        更新预警规则
        
        Returns:
            更新后的规则信息
        """
        # 验证规则存在
        existing = self.rule_repo.get_rule(rule_id)
        if not existing:
            raise ValueError(f"Rule not found: {rule_id}")
        
        # 验证规则类型
        if rule_type is not None:
            valid_types = ['frequency', 'duration', 'combination', 'threshold']
            if rule_type not in valid_types:
                raise ValueError(f"Invalid rule_type: {rule_type}")
        
        # 验证预警级别
        if alert_level is not None and alert_level not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid alert_level: {alert_level}")
        
        self.rule_repo.update_rule(
            rule_id=rule_id,
            rule_name=rule_name,
            rule_type=rule_type,
            conditions=conditions,
            alert_level=alert_level,
            description=description,
            behavior_type=behavior_type,
            threshold_count=threshold_count,
            time_window_seconds=time_window_seconds,
            is_active=is_active
        )
        
        # 清除缓存
        self._invalidate_cache()
        
        return self.rule_repo.get_rule(rule_id)
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        删除预警规则
        
        Returns:
            是否删除成功
        """
        existing = self.rule_repo.get_rule(rule_id)
        if not existing:
            return False
        
        self.rule_repo.delete_rule(rule_id)
        self._invalidate_cache()
        return True
    
    def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """获取单个规则"""
        return self.rule_repo.get_rule(rule_id)
    
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """
        获取所有活跃规则（带缓存）
        
        Returns:
            活跃的规则列表
        """
        now = datetime.now()
        if (self._rules_cache is not None and 
            self._cache_time is not None and
            (now - self._cache_time).total_seconds() < self._cache_ttl):
            return self._rules_cache
        
        self._rules_cache = self.rule_repo.get_active_rules()
        self._cache_time = now
        return self._rules_cache
    
    def list_rules(
        self,
        is_active: bool = None,
        rule_type: str = None,
        behavior_type: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        分页查询规则列表
        
        Returns:
            (规则列表, 总数)
        """
        offset = (page - 1) * page_size
        rules = self.rule_repo.list_rules(
            is_active=is_active,
            rule_type=rule_type,
            behavior_type=behavior_type,
            limit=page_size,
            offset=offset
        )
        total = self.rule_repo.count_rules(is_active=is_active, rule_type=rule_type)
        return rules, total
    
    def evaluate(
        self,
        detections: List[Dict],
        context: EvaluationContext
    ) -> List[RuleMatch]:
        """
        评估检测结果是否触发规则
        
        Args:
            detections: 当前检测到的行为列表
            context: 评估上下文（包含历史数据）
            
        Returns:
            触发的规则匹配列表
        """
        matches = []
        rules = self.get_active_rules()
        
        for rule in rules:
            match = self._evaluate_rule(rule, detections, context)
            if match:
                matches.append(match)
        
        return matches
    
    def _evaluate_rule(
        self,
        rule: Dict,
        detections: List[Dict],
        context: EvaluationContext
    ) -> Optional[RuleMatch]:
        """
        评估单个规则
        
        Args:
            rule: 规则配置
            detections: 当前检测结果
            context: 评估上下文
            
        Returns:
            匹配结果或None
        """
        rule_type = rule['rule_type']
        
        if rule_type == 'frequency':
            return self._evaluate_frequency_rule(rule, detections, context)
        elif rule_type == 'threshold':
            return self._evaluate_threshold_rule(rule, detections, context)
        elif rule_type == 'combination':
            return self._evaluate_combination_rule(rule, detections, context)
        elif rule_type == 'duration':
            return self._evaluate_duration_rule(rule, detections, context)
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return None
    
    def _evaluate_frequency_rule(
        self,
        rule: Dict,
        detections: List[Dict],
        context: EvaluationContext
    ) -> Optional[RuleMatch]:
        """
        评估频率规则
        在时间窗口内，特定行为出现次数超过阈值时触发
        """
        behavior_type = rule.get('behavior_type')
        threshold = rule.get('threshold_count', 3)
        time_window = rule.get('time_window_seconds', 60)
        conditions = rule.get('conditions', {})
        min_confidence = conditions.get('min_confidence', 0.5)
        
        # 统计当前检测中的行为数量
        current_count = 0
        total_confidence = 0.0
        
        for det in detections:
            det_behavior = det.get('class_name') or det.get('behavior_type')
            det_confidence = det.get('confidence', 0)
            
            if behavior_type and det_behavior != behavior_type:
                continue
            if det_confidence < min_confidence:
                continue
            
            current_count += 1
            total_confidence += det_confidence
        
        # 加上历史数据中的计数
        historical_count = context.behavior_counts.get(behavior_type, 0) if behavior_type else 0
        total_count = current_count + historical_count
        
        if total_count >= threshold:
            avg_confidence = total_confidence / current_count if current_count > 0 else 0.5
            return RuleMatch(
                rule_id=rule['rule_id'],
                rule_name=rule['rule_name'],
                rule_type='frequency',
                alert_level=rule['alert_level'],
                behavior_type=behavior_type or 'multiple',
                matched_count=total_count,
                threshold=threshold,
                confidence=round(avg_confidence, 3),
                message=f"行为'{behavior_type}'在{time_window}秒内出现{total_count}次，超过阈值{threshold}"
            )
        
        return None
    
    def _evaluate_threshold_rule(
        self,
        rule: Dict,
        detections: List[Dict],
        context: EvaluationContext
    ) -> Optional[RuleMatch]:
        """
        评估阈值规则
        单次检测中特定行为数量超过阈值时触发
        """
        behavior_type = rule.get('behavior_type')
        threshold = rule.get('threshold_count', 1)
        conditions = rule.get('conditions', {})
        min_confidence = conditions.get('min_confidence', 0.5)
        
        # 统计当前检测中的行为数量
        count = 0
        total_confidence = 0.0
        
        for det in detections:
            det_behavior = det.get('class_name') or det.get('behavior_type')
            det_confidence = det.get('confidence', 0)
            
            if behavior_type and det_behavior != behavior_type:
                continue
            if det_confidence < min_confidence:
                continue
            
            count += 1
            total_confidence += det_confidence
        
        if count >= threshold:
            avg_confidence = total_confidence / count if count > 0 else 0.5
            return RuleMatch(
                rule_id=rule['rule_id'],
                rule_name=rule['rule_name'],
                rule_type='threshold',
                alert_level=rule['alert_level'],
                behavior_type=behavior_type or 'multiple',
                matched_count=count,
                threshold=threshold,
                confidence=round(avg_confidence, 3),
                message=f"检测到{count}个'{behavior_type}'行为，超过阈值{threshold}"
            )
        
        return None
    
    def _evaluate_combination_rule(
        self,
        rule: Dict,
        detections: List[Dict],
        context: EvaluationContext
    ) -> Optional[RuleMatch]:
        """
        评估组合规则
        多种指定行为同时出现时触发
        """
        conditions = rule.get('conditions', {})
        required_behaviors = conditions.get('behaviors', [])
        min_confidence = conditions.get('min_confidence', 0.5)
        
        if not required_behaviors:
            return None
        
        # 统计当前检测中出现的行为类型
        detected_behaviors = set()
        total_confidence = 0.0
        count = 0
        
        for det in detections:
            det_behavior = det.get('class_name') or det.get('behavior_type')
            det_confidence = det.get('confidence', 0)
            
            if det_confidence >= min_confidence:
                detected_behaviors.add(det_behavior)
                total_confidence += det_confidence
                count += 1
        
        # 检查是否所有必需行为都出现
        required_set = set(required_behaviors)
        if required_set.issubset(detected_behaviors):
            avg_confidence = total_confidence / count if count > 0 else 0.5
            return RuleMatch(
                rule_id=rule['rule_id'],
                rule_name=rule['rule_name'],
                rule_type='combination',
                alert_level=rule['alert_level'],
                behavior_type=','.join(required_behaviors),
                matched_count=len(required_behaviors),
                threshold=len(required_behaviors),
                confidence=round(avg_confidence, 3),
                message=f"同时检测到多种行为: {', '.join(required_behaviors)}"
            )
        
        return None
    
    def _evaluate_duration_rule(
        self,
        rule: Dict,
        detections: List[Dict],
        context: EvaluationContext
    ) -> Optional[RuleMatch]:
        """
        评估持续时间规则
        行为持续时间超过阈值时触发
        
        注意：此规则需要历史数据支持，通过context中的behavior_duration判断
        """
        behavior_type = rule.get('behavior_type')
        conditions = rule.get('conditions', {})
        duration_threshold = conditions.get('duration_seconds', 30)
        min_confidence = conditions.get('min_confidence', 0.5)
        
        # 检查当前是否检测到该行为
        current_detected = False
        confidence = 0.5
        
        for det in detections:
            det_behavior = det.get('class_name') or det.get('behavior_type')
            det_confidence = det.get('confidence', 0)
            
            if det_behavior == behavior_type and det_confidence >= min_confidence:
                current_detected = True
                confidence = det_confidence
                break
        
        if not current_detected:
            return None
        
        # 从上下文获取行为持续时间
        behavior_duration = getattr(context, 'behavior_duration', {})
        duration = behavior_duration.get(behavior_type, 0)
        
        if duration >= duration_threshold:
            return RuleMatch(
                rule_id=rule['rule_id'],
                rule_name=rule['rule_name'],
                rule_type='duration',
                alert_level=rule['alert_level'],
                behavior_type=behavior_type,
                matched_count=int(duration),
                threshold=duration_threshold,
                confidence=round(confidence, 3),
                message=f"行为'{behavior_type}'持续{int(duration)}秒，超过阈值{duration_threshold}秒"
            )
        
        return None
    
    def _invalidate_cache(self):
        """清除规则缓存"""
        self._rules_cache = None
        self._cache_time = None


# 单例模式
_rule_engine_instance = None


def get_rule_engine() -> RuleEngine:
    """获取规则引擎单例"""
    global _rule_engine_instance
    if _rule_engine_instance is None:
        _rule_engine_instance = RuleEngine()
    return _rule_engine_instance
