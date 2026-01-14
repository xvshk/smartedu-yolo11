"""
通知服务模块
Notification service for alert notifications and student feedback
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.model.ManagerModel import DatabaseManager
from backend.model.NotificationModel import NotificationRepository

logger = logging.getLogger(__name__)


@dataclass
class NotificationData:
    """通知数据类"""
    notification_id: int
    alert_id: Optional[int]
    sender_id: int
    sender_name: str
    receiver_id: int
    receiver_name: str
    title: str
    content: str
    notification_type: str
    priority: str
    is_read: bool
    requires_feedback: bool
    feedback_count: int
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'notification_id': self.notification_id,
            'alert_id': self.alert_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver_name,
            'title': self.title,
            'content': self.content,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'is_read': self.is_read,
            'requires_feedback': self.requires_feedback,
            'feedback_count': self.feedback_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.repo = NotificationRepository(self.db)
    
    def send_notification(
        self,
        sender_id: int,
        receiver_id: int,
        title: str,
        content: str,
        alert_id: int = None,
        notification_type: str = 'warning',
        priority: str = 'normal',
        requires_feedback: bool = True,
        feedback_days: int = 3
    ) -> int:
        """
        发送通知给学生
        
        Args:
            sender_id: 发送者ID（老师/管理员）
            receiver_id: 接收者ID（学生）
            title: 通知标题
            content: 通知内容
            alert_id: 关联的预警ID
            notification_type: 通知类型
            priority: 优先级
            requires_feedback: 是否需要反馈
            feedback_days: 反馈截止天数
            
        Returns:
            通知ID
        """
        feedback_deadline = None
        if requires_feedback and feedback_days > 0:
            feedback_deadline = datetime.now() + timedelta(days=feedback_days)
        
        notification_id = self.repo.create_notification(
            sender_id=sender_id,
            receiver_id=receiver_id,
            title=title,
            content=content,
            alert_id=alert_id,
            notification_type=notification_type,
            priority=priority,
            requires_feedback=requires_feedback,
            feedback_deadline=feedback_deadline
        )
        
        logger.info(f"Notification sent: {notification_id} from {sender_id} to {receiver_id}")
        return notification_id
    
    def send_batch_notifications(
        self,
        sender_id: int,
        receiver_ids: List[int],
        title: str,
        content: str,
        notification_type: str = 'warning',
        priority: str = 'normal',
        requires_feedback: bool = True
    ) -> List[int]:
        """批量发送通知"""
        notification_ids = []
        for receiver_id in receiver_ids:
            try:
                nid = self.send_notification(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    title=title,
                    content=content,
                    notification_type=notification_type,
                    priority=priority,
                    requires_feedback=requires_feedback
                )
                notification_ids.append(nid)
            except Exception as e:
                logger.error(f"Failed to send notification to {receiver_id}: {e}")
        
        return notification_ids
    
    def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """获取通知详情"""
        notification = self.repo.get_notification(notification_id)
        if notification:
            # 获取反馈列表
            feedbacks = self.repo.list_feedbacks_for_notification(notification_id)
            notification['feedbacks'] = feedbacks
        return notification
    
    def get_user_notifications(
        self,
        user_id: int,
        is_read: bool = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户的通知列表"""
        offset = (page - 1) * page_size
        notifications = self.repo.list_notifications_for_user(
            user_id=user_id,
            is_read=is_read,
            limit=page_size,
            offset=offset
        )
        total = self.repo.count_notifications_for_user(user_id, is_read)
        return notifications, total
    
    def get_sent_notifications(
        self,
        sender_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """获取发送的通知列表"""
        offset = (page - 1) * page_size
        return self.repo.list_sent_notifications(sender_id, page_size, offset)
    
    def get_unread_count(self, user_id: int) -> int:
        """获取未读通知数量"""
        return self.repo.count_notifications_for_user(user_id, is_read=False)
    
    def mark_as_read(self, notification_id: int) -> None:
        """标记通知为已读"""
        self.repo.mark_as_read(notification_id)
    
    def mark_all_as_read(self, user_id: int) -> int:
        """标记所有通知为已读"""
        return self.repo.mark_all_as_read(user_id)
    
    def delete_notification(self, notification_id: int) -> None:
        """删除通知"""
        self.repo.delete_notification(notification_id)
    
    # ==================== 反馈功能 ====================
    
    def submit_feedback(
        self,
        notification_id: int,
        student_id: int,
        feedback_type: str,
        content: str,
        attachment_url: str = None
    ) -> int:
        """
        学生提交反馈
        
        Args:
            notification_id: 通知ID
            student_id: 学生ID
            feedback_type: 反馈类型 (acknowledge/explain/appeal/commit)
            content: 反馈内容
            attachment_url: 附件URL
            
        Returns:
            反馈ID
        """
        # 验证通知存在且属于该学生
        notification = self.repo.get_notification(notification_id)
        if not notification:
            raise ValueError("通知不存在")
        if notification['receiver_id'] != student_id:
            raise ValueError("无权对此通知进行反馈")
        
        feedback_id = self.repo.create_feedback(
            notification_id=notification_id,
            student_id=student_id,
            feedback_type=feedback_type,
            content=content,
            attachment_url=attachment_url
        )
        
        # 自动标记通知为已读
        self.repo.mark_as_read(notification_id)
        
        logger.info(f"Feedback submitted: {feedback_id} for notification {notification_id}")
        return feedback_id
    
    def get_feedback(self, feedback_id: int) -> Optional[Dict[str, Any]]:
        """获取反馈详情"""
        return self.repo.get_feedback(feedback_id)
    
    def get_feedbacks_for_notification(self, notification_id: int) -> List[Dict[str, Any]]:
        """获取通知的所有反馈"""
        return self.repo.list_feedbacks_for_notification(notification_id)
    
    def get_pending_feedbacks(
        self,
        sender_id: int = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取待审核的反馈"""
        offset = (page - 1) * page_size
        feedbacks = self.repo.list_feedbacks_for_review('pending', page_size, offset)
        
        # 如果指定了发送者，过滤只显示自己发送的通知的反馈
        if sender_id:
            feedbacks = [f for f in feedbacks if f.get('sender_id') == sender_id]
        
        total = self.repo.count_pending_feedbacks(sender_id)
        return feedbacks, total
    
    def get_student_feedbacks(
        self,
        student_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """获取学生的反馈历史"""
        offset = (page - 1) * page_size
        return self.repo.list_student_feedbacks(student_id, page_size, offset)
    
    def review_feedback(
        self,
        feedback_id: int,
        reviewer_id: int,
        status: str,
        comment: str = None
    ) -> None:
        """
        审核反馈
        
        Args:
            feedback_id: 反馈ID
            reviewer_id: 审核人ID
            status: 审核状态 (reviewed/accepted/rejected)
            comment: 审核意见
        """
        if status not in ['reviewed', 'accepted', 'rejected']:
            raise ValueError("无效的审核状态")
        
        self.repo.review_feedback(feedback_id, reviewer_id, status, comment)
        logger.info(f"Feedback {feedback_id} reviewed: {status}")
    
    # ==================== 模板功能 ====================
    
    def get_templates(self, behavior_type: str = None) -> List[Dict[str, Any]]:
        """获取通知模板列表"""
        return self.repo.list_templates(behavior_type)
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """获取单个模板"""
        return self.repo.get_template(template_id)
    
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
        return self.repo.create_template(
            template_name=template_name,
            title_template=title_template,
            content_template=content_template,
            behavior_type=behavior_type,
            notification_type=notification_type,
            created_by=created_by
        )
    
    # ==================== 统计功能 ====================
    
    def get_statistics(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """获取通知统计"""
        return self.repo.get_notification_statistics(user_id, days)
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()


# 单例模式
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """获取通知服务单例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
