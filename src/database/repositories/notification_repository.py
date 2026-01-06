"""
通知和反馈数据仓库模块
Notification and feedback data repository
"""
import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class NotificationRepository:
    """通知和反馈数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    # ==================== 通知操作 ====================
    
    def create_notification(
        self,
        sender_id: int,
        receiver_id: int,
        title: str,
        content: str,
        alert_id: int = None,
        notification_type: str = 'warning',
        priority: str = 'normal',
        requires_feedback: bool = True,
        feedback_deadline: datetime = None
    ) -> int:
        """创建通知"""
        sql = """
            INSERT INTO alert_notifications 
            (alert_id, sender_id, receiver_id, title, content, notification_type, 
             priority, requires_feedback, feedback_deadline)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (
            alert_id, sender_id, receiver_id, title, content,
            notification_type, priority, requires_feedback, feedback_deadline
        ))
    
    def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """获取单个通知详情"""
        sql = """
            SELECT n.*, 
                   s.username as sender_name, s.role as sender_role,
                   r.username as receiver_name
            FROM alert_notifications n
            LEFT JOIN users s ON n.sender_id = s.user_id
            LEFT JOIN users r ON n.receiver_id = r.user_id
            WHERE n.notification_id = %s
        """
        return self.db.query_one(sql, (notification_id,))
    
    def list_notifications_for_user(
        self,
        user_id: int,
        is_read: bool = None,
        notification_type: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户的通知列表"""
        conditions = ["receiver_id = %s"]
        params = [user_id]
        
        if is_read is not None:
            conditions.append("is_read = %s")
            params.append(is_read)
        if notification_type:
            conditions.append("notification_type = %s")
            params.append(notification_type)
        
        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT n.*, 
                   s.username as sender_name, s.role as sender_role,
                   (SELECT COUNT(*) FROM student_feedbacks f WHERE f.notification_id = n.notification_id) as feedback_count
            FROM alert_notifications n
            LEFT JOIN users s ON n.sender_id = s.user_id
            WHERE {where_clause}
            ORDER BY n.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    def list_sent_notifications(
        self,
        sender_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取发送的通知列表"""
        sql = """
            SELECT n.*, 
                   r.username as receiver_name,
                   (SELECT COUNT(*) FROM student_feedbacks f WHERE f.notification_id = n.notification_id) as feedback_count,
                   (SELECT COUNT(*) FROM student_feedbacks f WHERE f.notification_id = n.notification_id AND f.status = 'pending') as pending_feedback_count,
                   (SELECT f.status FROM student_feedbacks f WHERE f.notification_id = n.notification_id ORDER BY f.created_at DESC LIMIT 1) as latest_feedback_status
            FROM alert_notifications n
            LEFT JOIN users r ON n.receiver_id = r.user_id
            WHERE n.sender_id = %s
            ORDER BY n.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.db.query(sql, (sender_id, limit, offset))
    
    def count_notifications_for_user(self, user_id: int, is_read: bool = None) -> int:
        """统计用户通知数量"""
        conditions = ["receiver_id = %s"]
        params = [user_id]
        
        if is_read is not None:
            conditions.append("is_read = %s")
            params.append(is_read)
        
        where_clause = " AND ".join(conditions)
        sql = f"SELECT COUNT(*) as count FROM alert_notifications WHERE {where_clause}"
        result = self.db.query_one(sql, tuple(params))
        return result['count'] if result else 0
    
    def mark_as_read(self, notification_id: int) -> None:
        """标记通知为已读"""
        sql = "UPDATE alert_notifications SET is_read = TRUE, read_at = NOW() WHERE notification_id = %s"
        self.db.execute(sql, (notification_id,))
    
    def mark_all_as_read(self, user_id: int) -> int:
        """标记用户所有通知为已读"""
        sql = "UPDATE alert_notifications SET is_read = TRUE, read_at = NOW() WHERE receiver_id = %s AND is_read = FALSE"
        return self.db.execute(sql, (user_id,))
    
    def delete_notification(self, notification_id: int) -> None:
        """删除通知"""
        sql = "DELETE FROM alert_notifications WHERE notification_id = %s"
        self.db.execute(sql, (notification_id,))
    
    # ==================== 反馈操作 ====================
    
    def create_feedback(
        self,
        notification_id: int,
        student_id: int,
        feedback_type: str,
        content: str,
        attachment_url: str = None
    ) -> int:
        """创建学生反馈"""
        sql = """
            INSERT INTO student_feedbacks 
            (notification_id, student_id, feedback_type, content, attachment_url)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (
            notification_id, student_id, feedback_type, content, attachment_url
        ))
    
    def get_feedback(self, feedback_id: int) -> Optional[Dict[str, Any]]:
        """获取单个反馈详情"""
        sql = """
            SELECT f.*, 
                   s.username as student_name,
                   r.username as reviewer_name,
                   n.title as notification_title
            FROM student_feedbacks f
            LEFT JOIN users s ON f.student_id = s.user_id
            LEFT JOIN users r ON f.reviewer_id = r.user_id
            LEFT JOIN alert_notifications n ON f.notification_id = n.notification_id
            WHERE f.feedback_id = %s
        """
        return self.db.query_one(sql, (feedback_id,))
    
    def list_feedbacks_for_notification(self, notification_id: int) -> List[Dict[str, Any]]:
        """获取通知的所有反馈"""
        sql = """
            SELECT f.*, 
                   s.username as student_name,
                   r.username as reviewer_name
            FROM student_feedbacks f
            LEFT JOIN users s ON f.student_id = s.user_id
            LEFT JOIN users r ON f.reviewer_id = r.user_id
            WHERE f.notification_id = %s
            ORDER BY f.created_at DESC
        """
        return self.db.query(sql, (notification_id,))
    
    def list_feedbacks_for_review(
        self,
        status: str = 'pending',
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取待审核的反馈列表"""
        sql = """
            SELECT f.*, 
                   s.username as student_name,
                   n.title as notification_title,
                   n.sender_id,
                   sender.username as sender_name
            FROM student_feedbacks f
            LEFT JOIN users s ON f.student_id = s.user_id
            LEFT JOIN alert_notifications n ON f.notification_id = n.notification_id
            LEFT JOIN users sender ON n.sender_id = sender.user_id
            WHERE f.status = %s
            ORDER BY f.created_at ASC
            LIMIT %s OFFSET %s
        """
        return self.db.query(sql, (status, limit, offset))
    
    def list_student_feedbacks(
        self,
        student_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取学生的反馈历史"""
        sql = """
            SELECT f.*, 
                   n.title as notification_title,
                   r.username as reviewer_name
            FROM student_feedbacks f
            LEFT JOIN alert_notifications n ON f.notification_id = n.notification_id
            LEFT JOIN users r ON f.reviewer_id = r.user_id
            WHERE f.student_id = %s
            ORDER BY f.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.db.query(sql, (student_id, limit, offset))
    
    def review_feedback(
        self,
        feedback_id: int,
        reviewer_id: int,
        status: str,
        comment: str = None
    ) -> None:
        """审核反馈"""
        sql = """
            UPDATE student_feedbacks 
            SET status = %s, reviewer_id = %s, reviewer_comment = %s, reviewed_at = NOW()
            WHERE feedback_id = %s
        """
        self.db.execute(sql, (status, reviewer_id, comment, feedback_id))
    
    def count_pending_feedbacks(self, sender_id: int = None) -> int:
        """统计待审核反馈数量"""
        if sender_id:
            sql = """
                SELECT COUNT(*) as count 
                FROM student_feedbacks f
                JOIN alert_notifications n ON f.notification_id = n.notification_id
                WHERE f.status = 'pending' AND n.sender_id = %s
            """
            result = self.db.query_one(sql, (sender_id,))
        else:
            sql = "SELECT COUNT(*) as count FROM student_feedbacks WHERE status = 'pending'"
            result = self.db.query_one(sql)
        return result['count'] if result else 0
    
    # ==================== 模板操作 ====================
    
    def list_templates(self, behavior_type: str = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """获取通知模板列表"""
        conditions = []
        params = []
        
        if behavior_type:
            conditions.append("behavior_type = %s")
            params.append(behavior_type)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM notification_templates {where_clause} ORDER BY template_name"
        return self.db.query(sql, tuple(params))
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """获取单个模板"""
        sql = "SELECT * FROM notification_templates WHERE template_id = %s"
        return self.db.query_one(sql, (template_id,))
    
    def create_template(
        self,
        template_name: str,
        title_template: str,
        content_template: str,
        behavior_type: str = None,
        notification_type: str = 'warning',
        created_by: int = None
    ) -> int:
        """创建通知模板"""
        sql = """
            INSERT INTO notification_templates 
            (template_name, behavior_type, title_template, content_template, notification_type, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (
            template_name, behavior_type, title_template, content_template, notification_type, created_by
        ))
    
    # ==================== 统计功能 ====================
    
    def get_notification_statistics(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """获取通知统计"""
        start_date = datetime.now() - timedelta(days=days)
        
        # 基础条件
        sender_condition = "AND sender_id = %s" if user_id else ""
        params = [start_date]
        if user_id:
            params.append(user_id)
        
        # 发送统计
        sql = f"""
            SELECT 
                COUNT(*) as total_sent,
                SUM(CASE WHEN is_read = TRUE THEN 1 ELSE 0 END) as total_read,
                SUM(CASE WHEN notification_type = 'warning' THEN 1 ELSE 0 END) as warning_count,
                SUM(CASE WHEN notification_type = 'reminder' THEN 1 ELSE 0 END) as reminder_count,
                SUM(CASE WHEN notification_type = 'suggestion' THEN 1 ELSE 0 END) as suggestion_count,
                SUM(CASE WHEN notification_type = 'praise' THEN 1 ELSE 0 END) as praise_count
            FROM alert_notifications
            WHERE created_at >= %s {sender_condition}
        """
        sent_stats = self.db.query_one(sql, tuple(params))
        
        # 反馈统计
        sql = f"""
            SELECT 
                COUNT(*) as total_feedbacks,
                SUM(CASE WHEN f.status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN f.status = 'reviewed' THEN 1 ELSE 0 END) as reviewed_count,
                SUM(CASE WHEN f.status = 'accepted' THEN 1 ELSE 0 END) as accepted_count,
                SUM(CASE WHEN f.status = 'rejected' THEN 1 ELSE 0 END) as rejected_count
            FROM student_feedbacks f
            JOIN alert_notifications n ON f.notification_id = n.notification_id
            WHERE f.created_at >= %s {sender_condition.replace('sender_id', 'n.sender_id')}
        """
        feedback_stats = self.db.query_one(sql, tuple(params))
        
        return {
            'sent': sent_stats or {},
            'feedbacks': feedback_stats or {},
            'period_days': days
        }
