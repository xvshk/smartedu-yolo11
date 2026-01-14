"""
预警规则数据仓库模块
Alert rule data repository
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.model.ManagerModel import DatabaseManager

logger = logging.getLogger(__name__)


class RuleRepository:
    """预警规则数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        """
        初始化规则数据仓库
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
    
    # ==================== Rule CRUD 操作 ====================
    
    def create_rule(
        self,
        rule_name: str,
        rule_type: str,
        conditions: Dict[str, Any],
        alert_level: int = 1,
        description: str = None,
        behavior_type: str = None,
        class_id: int = None,
        threshold_count: int = 1,
        time_window_seconds: int = 60,
        created_by: int = None,
        is_active: bool = True
    ) -> int:
        """
        创建预警规则
        
        Args:
            rule_name: 规则名称
            rule_type: 规则类型 (frequency/duration/combination/threshold)
            conditions: 规则条件配置
            alert_level: 预警级别
            description: 规则描述
            behavior_type: 行为类型
            class_id: 行为类别ID
            threshold_count: 触发阈值
            time_window_seconds: 时间窗口（秒）
            created_by: 创建者用户ID
            is_active: 是否激活
            
        Returns:
            新创建的rule_id
        """
        sql = """
            INSERT INTO alert_rules 
            (rule_name, rule_type, description, conditions, alert_level, 
             behavior_type, class_id, threshold_count, time_window_seconds,
             created_by, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (
            rule_name,
            rule_type,
            description,
            json.dumps(conditions) if isinstance(conditions, dict) else conditions,
            alert_level,
            behavior_type,
            class_id,
            threshold_count,
            time_window_seconds,
            created_by,
            is_active
        ))
    
    def update_rule(
        self,
        rule_id: int,
        rule_name: str = None,
        rule_type: str = None,
        conditions: Dict[str, Any] = None,
        alert_level: int = None,
        description: str = None,
        behavior_type: str = None,
        class_id: int = None,
        threshold_count: int = None,
        time_window_seconds: int = None,
        is_active: bool = None
    ) -> None:
        """
        更新预警规则
        
        Args:
            rule_id: 规则ID
            其他参数: 要更新的字段
        """
        updates = []
        params = []
        
        if rule_name is not None:
            updates.append("rule_name = %s")
            params.append(rule_name)
        if rule_type is not None:
            updates.append("rule_type = %s")
            params.append(rule_type)
        if conditions is not None:
            updates.append("conditions = %s")
            params.append(json.dumps(conditions) if isinstance(conditions, dict) else conditions)
        if alert_level is not None:
            updates.append("alert_level = %s")
            params.append(alert_level)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if behavior_type is not None:
            updates.append("behavior_type = %s")
            params.append(behavior_type)
        if class_id is not None:
            updates.append("class_id = %s")
            params.append(class_id)
        if threshold_count is not None:
            updates.append("threshold_count = %s")
            params.append(threshold_count)
        if time_window_seconds is not None:
            updates.append("time_window_seconds = %s")
            params.append(time_window_seconds)
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)
        
        if not updates:
            return
        
        params.append(rule_id)
        sql = f"UPDATE alert_rules SET {', '.join(updates)} WHERE rule_id = %s"
        self.db.execute(sql, tuple(params))
    
    def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个规则详情
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则信息字典或None
        """
        sql = "SELECT * FROM alert_rules WHERE rule_id = %s"
        result = self.db.query_one(sql, (rule_id,))
        if result:
            result = self._parse_rule_json_fields(result)
        return result
    
    def get_rule_by_name(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """
        按名称获取规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            规则信息字典或None
        """
        sql = "SELECT * FROM alert_rules WHERE rule_name = %s"
        result = self.db.query_one(sql, (rule_name,))
        if result:
            result = self._parse_rule_json_fields(result)
        return result
    
    def list_rules(
        self,
        is_active: bool = None,
        rule_type: str = None,
        behavior_type: str = None,
        alert_level: int = None,
        created_by: int = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询规则列表
        
        Args:
            is_active: 是否激活筛选
            rule_type: 规则类型筛选
            behavior_type: 行为类型筛选
            alert_level: 预警级别筛选
            created_by: 创建者筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            规则列表
        """
        conditions = []
        params = []
        
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        if rule_type:
            conditions.append("rule_type = %s")
            params.append(rule_type)
        if behavior_type:
            conditions.append("behavior_type = %s")
            params.append(behavior_type)
        if alert_level is not None:
            conditions.append("alert_level = %s")
            params.append(alert_level)
        if created_by is not None:
            conditions.append("created_by = %s")
            params.append(created_by)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM alert_rules 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        results = self.db.query(sql, tuple(params))
        return [self._parse_rule_json_fields(r) for r in results]
    
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """
        获取所有激活的规则
        
        Returns:
            激活的规则列表
        """
        return self.list_rules(is_active=True, limit=1000)
    
    def count_rules(
        self,
        is_active: bool = None,
        rule_type: str = None
    ) -> int:
        """
        统计规则数量
        
        Returns:
            规则数量
        """
        conditions = []
        params = []
        
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        if rule_type:
            conditions.append("rule_type = %s")
            params.append(rule_type)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT COUNT(*) as count FROM alert_rules {where_clause}"
        result = self.db.query_one(sql, tuple(params))
        return result['count'] if result else 0
    
    def delete_rule(self, rule_id: int) -> None:
        """
        删除规则
        
        Args:
            rule_id: 规则ID
        """
        sql = "DELETE FROM alert_rules WHERE rule_id = %s"
        self.db.execute(sql, (rule_id,))
    
    def activate_rule(self, rule_id: int) -> None:
        """激活规则"""
        sql = "UPDATE alert_rules SET is_active = TRUE WHERE rule_id = %s"
        self.db.execute(sql, (rule_id,))
    
    def deactivate_rule(self, rule_id: int) -> None:
        """停用规则"""
        sql = "UPDATE alert_rules SET is_active = FALSE WHERE rule_id = %s"
        self.db.execute(sql, (rule_id,))
    
    def _parse_rule_json_fields(self, rule: Dict) -> Dict:
        """解析规则中的JSON字段"""
        if rule.get('conditions') and isinstance(rule['conditions'], str):
            try:
                rule['conditions'] = json.loads(rule['conditions'])
            except json.JSONDecodeError:
                pass
        return rule
    
    # ==================== Intervention 操作 ====================
    
    def create_intervention(
        self,
        alert_id: int,
        action_taken: str,
        outcome: str = None,
        effectiveness_rating: int = None,
        recorded_by: int = None
    ) -> int:
        """
        创建干预记录
        
        Args:
            alert_id: 预警ID
            action_taken: 采取的干预措施
            outcome: 干预结果
            effectiveness_rating: 有效性评分 (1-5)
            recorded_by: 记录者用户ID
            
        Returns:
            新创建的intervention_id
        """
        sql = """
            INSERT INTO interventions 
            (alert_id, action_taken, outcome, effectiveness_rating, recorded_by)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (
            alert_id,
            action_taken,
            outcome,
            effectiveness_rating,
            recorded_by
        ))
    
    def update_intervention(
        self,
        intervention_id: int,
        outcome: str = None,
        effectiveness_rating: int = None
    ) -> None:
        """
        更新干预记录
        
        Args:
            intervention_id: 干预记录ID
            outcome: 干预结果
            effectiveness_rating: 有效性评分
        """
        updates = []
        params = []
        
        if outcome is not None:
            updates.append("outcome = %s")
            params.append(outcome)
        if effectiveness_rating is not None:
            updates.append("effectiveness_rating = %s")
            params.append(effectiveness_rating)
        
        if not updates:
            return
        
        params.append(intervention_id)
        sql = f"UPDATE interventions SET {', '.join(updates)} WHERE intervention_id = %s"
        self.db.execute(sql, tuple(params))
    
    def get_intervention(self, intervention_id: int) -> Optional[Dict[str, Any]]:
        """获取干预记录"""
        sql = "SELECT * FROM interventions WHERE intervention_id = %s"
        return self.db.query_one(sql, (intervention_id,))
    
    def get_interventions_by_alert(self, alert_id: int) -> List[Dict[str, Any]]:
        """获取预警的所有干预记录"""
        sql = "SELECT * FROM interventions WHERE alert_id = %s ORDER BY created_at"
        return self.db.query(sql, (alert_id,))
    
    def get_intervention_effectiveness(self, behavior_type: str = None) -> List[Dict[str, Any]]:
        """
        获取干预有效性统计
        
        Args:
            behavior_type: 可选的行为类型筛选
            
        Returns:
            干预有效性统计列表
        """
        if behavior_type:
            sql = """
                SELECT i.action_taken, 
                       COUNT(*) as count,
                       AVG(i.effectiveness_rating) as avg_effectiveness
                FROM interventions i
                JOIN alerts a ON i.alert_id = a.alert_id
                WHERE a.behavior_type = %s AND i.effectiveness_rating IS NOT NULL
                GROUP BY i.action_taken
                ORDER BY avg_effectiveness DESC
            """
            return self.db.query(sql, (behavior_type,))
        else:
            sql = """
                SELECT action_taken, 
                       COUNT(*) as count,
                       AVG(effectiveness_rating) as avg_effectiveness
                FROM interventions
                WHERE effectiveness_rating IS NOT NULL
                GROUP BY action_taken
                ORDER BY avg_effectiveness DESC
            """
            return self.db.query(sql)
    
    # ==================== Notification Preferences 操作 ====================
    
    def get_notification_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户通知偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            通知偏好字典或None
        """
        sql = "SELECT * FROM notification_preferences WHERE user_id = %s"
        return self.db.query_one(sql, (user_id,))
    
    def create_or_update_notification_preferences(
        self,
        user_id: int,
        alert_level_0: bool = False,
        alert_level_1: bool = True,
        alert_level_2: bool = True,
        alert_level_3: bool = True,
        sound_enabled: bool = True
    ) -> int:
        """
        创建或更新用户通知偏好
        
        Args:
            user_id: 用户ID
            alert_level_0: 正常级别通知
            alert_level_1: 轻度预警通知
            alert_level_2: 中度预警通知
            alert_level_3: 严重预警通知
            sound_enabled: 声音提醒
            
        Returns:
            preference_id
        """
        # 检查是否已存在
        existing = self.get_notification_preferences(user_id)
        
        if existing:
            sql = """
                UPDATE notification_preferences 
                SET alert_level_0 = %s, alert_level_1 = %s, alert_level_2 = %s,
                    alert_level_3 = %s, sound_enabled = %s
                WHERE user_id = %s
            """
            self.db.execute(sql, (
                alert_level_0, alert_level_1, alert_level_2,
                alert_level_3, sound_enabled, user_id
            ))
            return existing['preference_id']
        else:
            sql = """
                INSERT INTO notification_preferences 
                (user_id, alert_level_0, alert_level_1, alert_level_2, alert_level_3, sound_enabled)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            return self.db.insert_and_get_id(sql, (
                user_id, alert_level_0, alert_level_1, alert_level_2,
                alert_level_3, sound_enabled
            ))
    
    def should_notify(self, user_id: int, alert_level: int) -> bool:
        """
        检查是否应该通知用户
        
        Args:
            user_id: 用户ID
            alert_level: 预警级别
            
        Returns:
            是否应该通知
        """
        prefs = self.get_notification_preferences(user_id)
        if not prefs:
            # 默认：级别1及以上通知
            return alert_level >= 1
        
        level_key = f'alert_level_{alert_level}'
        return prefs.get(level_key, alert_level >= 1)
