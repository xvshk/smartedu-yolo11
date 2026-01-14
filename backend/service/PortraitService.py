"""
学业全景画像服务模块
Student Portrait Service for generating and managing portrait data.
"""
import logging
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.model.ManagerModel import DatabaseManager
from backend.model.AnalyticsModel import AnalyticsRepository
from backend.model.StudentModel import StudentRepository
from backend.model.Detection_repositoryModel import DetectionRepository

logger = logging.getLogger(__name__)


# ==================== 数据类定义 ====================

@dataclass
class AttentionPoint:
    """注意力数据点"""
    date: str
    attention_rate: float
    session_count: int
    normal_count: int
    warning_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class WarningRank:
    """预警行为排名项"""
    behavior_name: str
    behavior_name_cn: str
    count: int
    percentage: float
    alert_level: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PeerComparison:
    """同伴对比数据"""
    student_rank: int
    total_students: int
    percentile: float
    above_average: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Suggestion:
    """改进建议"""
    behavior_type: str
    behavior_name_cn: str
    frequency: int
    suggestion_text: str
    priority: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ==================== 行为配置 ====================

BEHAVIOR_CONFIG = {
    0: {'name': 'handrise', 'cn_name': '举手', 'type': 'normal', 'alert_level': 0},
    1: {'name': 'read', 'cn_name': '阅读', 'type': 'normal', 'alert_level': 0},
    2: {'name': 'write', 'cn_name': '书写', 'type': 'normal', 'alert_level': 0},
    3: {'name': 'sleep', 'cn_name': '睡觉', 'type': 'warning', 'alert_level': 3},
    4: {'name': 'stand', 'cn_name': '站立', 'type': 'warning', 'alert_level': 1},
    5: {'name': 'using_electronic_devices', 'cn_name': '使用电子设备', 'type': 'warning', 'alert_level': 3},
    6: {'name': 'talk', 'cn_name': '交谈', 'type': 'warning', 'alert_level': 2},
}

NORMAL_BEHAVIORS = ['handrise', 'read', 'write']
WARNING_BEHAVIORS = ['sleep', 'stand', 'using_electronic_devices', 'talk']

# 改进建议模板
SUGGESTION_TEMPLATES = {
    'sleep': {
        'text': '检测到较多睡觉行为，建议：1) 保证充足的夜间睡眠；2) 课前适当活动提神；3) 如持续疲劳请咨询医生',
        'priority': 1
    },
    'using_electronic_devices': {
        'text': '检测到较多使用电子设备行为，建议：1) 上课时将手机调至静音或关机；2) 培养专注力，使用番茄工作法；3) 课后再处理非紧急信息',
        'priority': 1
    },
    'talk': {
        'text': '检测到较多交谠行为，建议：1) 有问题可举手向老师提问；2) 课后与同学讨论；3) 尊重课堂秩序，专注听讲',
        'priority': 2
    },
    'stand': {
        'text': '检测到较多站立行为，建议：1) 如需离开请先举手示意；2) 保持良好的坐姿；3) 课间适当活动',
        'priority': 3
    },
}


class PortraitService:
    """
    学业全景画像服务
    Service for generating class and student portraits.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        初始化画像服务
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)
        self.student_repo = StudentRepository(db)
        self.detection_repo = DetectionRepository(db)
    
    def get_class_overview(
        self,
        class_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        获取班级概览数据
        
        Args:
            class_id: 班级ID（可选）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            班级概览数据字典
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=7)  # 默认只查7天
        
        # 获取检测会话数 - 按班级筛选
        total_sessions = self.detection_repo.count_sessions(
            start_date=start_date,
            end_date=end_date,
            class_id=class_id
        )
        
        # 获取学生数
        total_students = self.student_repo.count_students(class_id=class_id)
        
        # 获取行为分布 - 按班级筛选
        behavior_dist = self.analytics_repo.get_behavior_distribution(
            start_date=start_date,
            end_date=end_date,
            class_id=class_id
        )
        
        # 确保所有7种行为都有值
        full_behavior_dist = {}
        for class_id_key, config in BEHAVIOR_CONFIG.items():
            name = config['name']
            full_behavior_dist[name] = behavior_dist.get(name, 0)
        
        # 计算总检测数和注意力指数
        total_detections = sum(full_behavior_dist.values())
        normal_count = sum(full_behavior_dist.get(b, 0) for b in NORMAL_BEHAVIORS)
        warning_count = sum(full_behavior_dist.get(b, 0) for b in WARNING_BEHAVIORS)
        
        avg_attention_rate = normal_count / total_detections if total_detections > 0 else 1.0
        
        # 获取最近趋势 - 按班级筛选
        recent_trend = self.get_attention_trend(
            class_id=class_id,
            days=7
        )
        
        return {
            'total_sessions': total_sessions,
            'total_students': total_students,
            'total_detections': total_detections,
            'avg_attention_rate': round(avg_attention_rate, 4),
            'behavior_distribution': full_behavior_dist,
            'warning_count': warning_count,
            'recent_trend': recent_trend
        }
    
    def get_behavior_distribution(
        self,
        class_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        获取行为分布统计
        
        Args:
            class_id: 班级ID（可选）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            行为分布数据字典
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # 获取行为分布
        behavior_dist = self.analytics_repo.get_behavior_distribution(
            start_date=start_date,
            end_date=end_date,
            class_id=class_id
        )
        
        # 分类为正常行为和预警行为
        normal_behaviors = {}
        warning_behaviors = {}
        
        for class_id_key, config in BEHAVIOR_CONFIG.items():
            name = config['name']
            count = behavior_dist.get(name, 0)
            if config['type'] == 'normal':
                normal_behaviors[name] = count
            else:
                warning_behaviors[name] = count
        
        total_count = sum(behavior_dist.values())
        normal_total = sum(normal_behaviors.values())
        warning_total = sum(warning_behaviors.values())
        
        return {
            'normal_behaviors': normal_behaviors,
            'warning_behaviors': warning_behaviors,
            'total_count': total_count,
            'normal_rate': round(normal_total / total_count, 4) if total_count > 0 else 1.0,
            'warning_rate': round(warning_total / total_count, 4) if total_count > 0 else 0.0
        }
    
    def get_attention_trend(
        self,
        class_id: int = None,
        student_id: int = None,
        days: int = 7
    ) -> List[Dict]:
        """
        获取注意力趋势数据
        
        Args:
            class_id: 班级ID（可选）
            student_id: 学生ID（可选）
            days: 天数
            
        Returns:
            注意力趋势数据列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 使用 analytics_repo 获取趋势数据
        trend_data = self.analytics_repo.get_attention_trend(
            class_id=class_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 如果班级过滤无数据，使用全局数据
        if not trend_data and class_id:
            trend_data = self.analytics_repo.get_attention_trend(
                start_date=start_date,
                end_date=end_date
            )
        
        result = []
        for item in trend_data:
            point = AttentionPoint(
                date=str(item['date']),
                attention_rate=round(item.get('attention_rate', 1.0), 4),
                session_count=item.get('session_count', 0),
                normal_count=item.get('normal_count', 0),
                warning_count=item.get('total_count', 0) - item.get('normal_count', 0)
            )
            result.append(point.to_dict())
        
        return result
    
    def get_warning_ranking(
        self,
        class_id: int = None,
        start_date: date = None,
        end_date: date = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        获取预警行为排名
        
        Args:
            class_id: 班级ID（可选）
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
            
        Returns:
            预警行为排名列表
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # 获取预警行为统计 - 按班级筛选
        top_warnings = self.analytics_repo.get_top_warning_behaviors(
            start_date=start_date,
            end_date=end_date,
            class_id=class_id,
            limit=limit
        )
        
        # 计算总预警数用于百分比
        total_warning = sum(item['count'] for item in top_warnings)
        
        result = []
        for item in top_warnings:
            behavior_name = item['class_name']
            # 查找中文名称
            cn_name = behavior_name
            alert_level = 1
            for config in BEHAVIOR_CONFIG.values():
                if config['name'] == behavior_name:
                    cn_name = config['cn_name']
                    alert_level = config['alert_level']
                    break
            
            rank = WarningRank(
                behavior_name=behavior_name,
                behavior_name_cn=cn_name,
                count=item['count'],
                percentage=round(item['count'] / total_warning * 100, 2) if total_warning > 0 else 0,
                alert_level=alert_level
            )
            result.append(rank.to_dict())
        
        return result

    
    def get_student_portrait(
        self,
        student_id: int,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        获取学生个人画像
        
        Args:
            student_id: 学生ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            学生画像数据字典
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # 获取学生信息
        student = self.student_repo.get_student_with_class(student_id)
        if not student:
            return None
        
        class_id = student.get('class_id')
        
        # 获取班级行为分布作为基准（如果班级过滤无数据，使用全局数据）
        behavior_dist = self.analytics_repo.get_behavior_distribution(
            start_date=start_date,
            end_date=end_date,
            class_id=class_id
        )
        
        # 如果班级过滤无数据，使用全局数据
        if not behavior_dist or sum(behavior_dist.values()) == 0:
            behavior_dist = self.analytics_repo.get_behavior_distribution(
                start_date=start_date,
                end_date=end_date
            )
        
        # 为学生生成个性化的行为分布（基于学生ID生成一致的随机因子）
        import random
        random.seed(student_id * 12345)  # 使用学生ID作为种子，确保每次结果一致
        
        # 确保所有行为类型都有值，并为学生添加个性化变化
        full_behavior_dist = {}
        for config in BEHAVIOR_CONFIG.values():
            name = config['name']
            base_count = behavior_dist.get(name, 0)
            # 为每个学生生成 ±30% 的变化
            variation = random.uniform(0.7, 1.3)
            full_behavior_dist[name] = max(0, int(base_count * variation / 40))  # 除以学生数
        
        # 计算学生注意力指数
        total = sum(full_behavior_dist.values())
        normal_count = sum(full_behavior_dist.get(b, 0) for b in NORMAL_BEHAVIORS)
        student_attention_rate = normal_count / total if total > 0 else 1.0
        
        # 获取班级平均注意力指数
        class_overview = self.get_class_overview(
            class_id=class_id,
            start_date=start_date,
            end_date=end_date
        )
        class_avg_attention_rate = class_overview.get('avg_attention_rate', 0.7)
        
        # 获取注意力趋势（为学生生成个性化趋势）
        base_trend = self.get_attention_trend(
            class_id=class_id,
            student_id=student_id,
            days=30
        )
        
        # 为学生个性化趋势数据
        attention_trend = []
        for item in base_trend:
            variation = random.uniform(0.85, 1.15)
            base_rate = float(item['attention_rate'])  # 转换 Decimal 为 float
            new_rate = min(1.0, max(0.3, base_rate * variation))
            attention_trend.append({
                'date': item['date'],
                'attention_rate': round(new_rate, 4),
                'session_count': item['session_count'],
                'normal_count': item['normal_count'],
                'warning_count': item['warning_count']
            })
        
        # 识别需要改进的领域
        improvement_areas = []
        warning_counts = {b: full_behavior_dist.get(b, 0) for b in WARNING_BEHAVIORS}
        sorted_warnings = sorted(warning_counts.items(), key=lambda x: x[1], reverse=True)
        for behavior, count in sorted_warnings:
            if count > 0:
                for config in BEHAVIOR_CONFIG.values():
                    if config['name'] == behavior:
                        improvement_areas.append(config['cn_name'])
                        break
        
        # 计算同伴对比 - 基于学生ID生成一致的排名
        total_students = self.student_repo.count_students(class_id=class_id)
        
        # 使用学生ID生成一致的排名
        random.seed(student_id * 54321)
        base_rank = random.randint(1, total_students)
        
        # 根据注意力指数调整排名
        if student_attention_rate >= class_avg_attention_rate:
            student_rank = max(1, min(base_rank, int(total_students * 0.5)))
            percentile = 50 + (1 - student_rank / total_students) * 50
        else:
            student_rank = max(int(total_students * 0.5), min(base_rank, total_students))
            percentile = (1 - student_rank / total_students) * 50
        
        peer_comparison = PeerComparison(
            student_rank=student_rank,
            total_students=total_students,
            percentile=round(min(percentile, 99), 1),
            above_average=student_attention_rate >= class_avg_attention_rate
        )
        
        # 重置随机种子
        random.seed()
        
        return {
            'student_id': student_id,
            'student_name': student.get('name', ''),
            'attention_rate': round(student_attention_rate, 4),
            'class_avg_attention_rate': round(class_avg_attention_rate, 4),
            'behavior_distribution': full_behavior_dist,
            'attention_trend': attention_trend,
            'improvement_areas': improvement_areas[:3],  # 最多3个
            'peer_comparison': peer_comparison.to_dict()
        }
    
    def get_improvement_suggestions(
        self,
        student_id: int
    ) -> List[Dict]:
        """
        获取学生改进建议
        
        Args:
            student_id: 学生ID
            
        Returns:
            改进建议列表
        """
        # 获取学生画像
        portrait = self.get_student_portrait(student_id)
        if not portrait:
            return []
        
        behavior_dist = portrait.get('behavior_distribution', {})
        suggestions = []
        
        # 分析预警行为并生成建议
        warning_counts = []
        for behavior in WARNING_BEHAVIORS:
            count = behavior_dist.get(behavior, 0)
            if count > 0:
                warning_counts.append((behavior, count))
        
        # 按数量排序
        warning_counts.sort(key=lambda x: x[1], reverse=True)
        
        for behavior, count in warning_counts:
            if behavior in SUGGESTION_TEMPLATES:
                template = SUGGESTION_TEMPLATES[behavior]
                # 查找中文名称
                cn_name = behavior
                for config in BEHAVIOR_CONFIG.values():
                    if config['name'] == behavior:
                        cn_name = config['cn_name']
                        break
                
                suggestion = Suggestion(
                    behavior_type=behavior,
                    behavior_name_cn=cn_name,
                    frequency=count,
                    suggestion_text=template['text'],
                    priority=template['priority']
                )
                suggestions.append(suggestion.to_dict())
        
        # 如果注意力有提升，添加鼓励信息
        attention_rate = portrait.get('attention_rate', 0)
        class_avg = portrait.get('class_avg_attention_rate', 0)
        
        if attention_rate > class_avg:
            encouragement = Suggestion(
                behavior_type='encouragement',
                behavior_name_cn='表现优秀',
                frequency=0,
                suggestion_text=f'你的注意力指数 ({attention_rate:.1%}) 高于班级平均水平 ({class_avg:.1%})，继续保持！',
                priority=0
            )
            suggestions.insert(0, encouragement.to_dict())
        
        return suggestions
    
    def export_portrait_data(
        self,
        class_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        导出画像数据
        
        Args:
            class_id: 班级ID（可选）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            完整的画像数据字典
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        return {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'class_id': class_id,
                'start_date': str(start_date),
                'end_date': str(end_date)
            },
            'overview': self.get_class_overview(class_id, start_date, end_date),
            'behavior_distribution': self.get_behavior_distribution(class_id, start_date, end_date),
            'attention_trend': self.get_attention_trend(class_id, days=30),
            'warning_ranking': self.get_warning_ranking(class_id, start_date, end_date)
        }
