"""
通知API模块
Notification API endpoints for alert notifications and student feedback
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import logging
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.notification_service import get_notification_service

logger = logging.getLogger(__name__)
notification_bp = Blueprint('notification', __name__)


def check_teacher_or_admin():
    """检查是否为老师或管理员"""
    claims = get_jwt()
    role = claims.get('role', '')
    return role in ['teacher', 'admin']


def check_student():
    """检查是否为学生"""
    claims = get_jwt()
    role = claims.get('role', '')
    return role == 'student'


# ==================== 通知发送接口（老师/管理员） ====================

@notification_bp.route('/send', methods=['POST'])
@jwt_required()
def send_notification():
    """
    发送通知给学生
    
    Request Body:
        {
            "receiver_id": 123,
            "title": "课堂行为提醒",
            "content": "同学你好，系统检测到...",
            "alert_id": 456,  // 可选，关联的预警ID
            "notification_type": "warning",  // warning/reminder/suggestion/praise
            "priority": "normal",  // low/normal/high/urgent
            "requires_feedback": true,
            "feedback_days": 3
        }
    """
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '只有老师和管理员可以发送通知'
        }), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('receiver_id') or not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: receiver_id, title, content'
            }), 400
        
        claims = get_jwt()
        sender_id = claims.get('user_id')
        
        service = get_notification_service()
        notification_id = service.send_notification(
            sender_id=sender_id,
            receiver_id=data['receiver_id'],
            title=data['title'],
            content=data['content'],
            alert_id=data.get('alert_id'),
            notification_type=data.get('notification_type', 'warning'),
            priority=data.get('priority', 'normal'),
            requires_feedback=data.get('requires_feedback', True),
            feedback_days=data.get('feedback_days', 3)
        )
        
        return jsonify({
            'success': True,
            'message': '通知发送成功',
            'data': {'notification_id': notification_id}
        }), 201
        
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        return jsonify({
            'success': False,
            'message': f'发送通知失败: {str(e)}'
        }), 500


@notification_bp.route('/send-batch', methods=['POST'])
@jwt_required()
def send_batch_notifications():
    """
    批量发送通知
    
    Request Body:
        {
            "receiver_ids": [123, 456, 789],
            "title": "课堂行为提醒",
            "content": "同学们好...",
            "notification_type": "reminder",
            "requires_feedback": false
        }
    """
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '只有老师和管理员可以发送通知'
        }), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('receiver_ids') or not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        claims = get_jwt()
        sender_id = claims.get('user_id')
        
        service = get_notification_service()
        notification_ids = service.send_batch_notifications(
            sender_id=sender_id,
            receiver_ids=data['receiver_ids'],
            title=data['title'],
            content=data['content'],
            notification_type=data.get('notification_type', 'warning'),
            priority=data.get('priority', 'normal'),
            requires_feedback=data.get('requires_feedback', True)
        )
        
        return jsonify({
            'success': True,
            'message': f'成功发送 {len(notification_ids)} 条通知',
            'data': {'notification_ids': notification_ids}
        }), 201
        
    except Exception as e:
        logger.error(f"Send batch notifications error: {e}")
        return jsonify({
            'success': False,
            'message': f'批量发送失败: {str(e)}'
        }), 500


@notification_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent_notifications():
    """获取已发送的通知列表（老师/管理员）"""
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '无权访问'
        }), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        claims = get_jwt()
        sender_id = claims.get('user_id')
        
        service = get_notification_service()
        notifications = service.get_sent_notifications(sender_id, page, page_size)
        
        return jsonify({
            'success': True,
            'data': {
                'items': notifications,
                'page': page,
                'page_size': page_size
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get sent notifications error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取发送记录失败: {str(e)}'
        }), 500


# ==================== 通知接收接口（学生） ====================

@notification_bp.route('/received', methods=['GET'])
@jwt_required()
def get_received_notifications():
    """获取收到的通知列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        is_read = request.args.get('is_read')
        
        if is_read is not None:
            is_read = is_read.lower() == 'true'
        
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        service = get_notification_service()
        notifications, total = service.get_user_notifications(
            user_id=user_id,
            is_read=is_read,
            page=page,
            page_size=page_size
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': notifications,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get received notifications error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取通知失败: {str(e)}'
        }), 500


@notification_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取未读通知数量"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        service = get_notification_service()
        count = service.get_unread_count(user_id)
        
        return jsonify({
            'success': True,
            'data': {'count': count}
        }), 200
        
    except Exception as e:
        logger.error(f"Get unread count error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取未读数量失败: {str(e)}'
        }), 500


@notification_bp.route('/<int:notification_id>', methods=['GET'])
@jwt_required()
def get_notification_detail(notification_id):
    """获取通知详情"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        role = claims.get('role', '')
        
        service = get_notification_service()
        notification = service.get_notification(notification_id)
        
        if not notification:
            return jsonify({
                'success': False,
                'message': '通知不存在'
            }), 404
        
        # 检查权限：只有发送者、接收者或管理员可以查看
        if notification['receiver_id'] != user_id and notification['sender_id'] != user_id and role != 'admin':
            return jsonify({
                'success': False,
                'message': '无权查看此通知'
            }), 403
        
        return jsonify({
            'success': True,
            'data': notification
        }), 200
        
    except Exception as e:
        logger.error(f"Get notification detail error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取通知详情失败: {str(e)}'
        }), 500


@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """标记通知为已读"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        service = get_notification_service()
        notification = service.get_notification(notification_id)
        
        if not notification or notification['receiver_id'] != user_id:
            return jsonify({
                'success': False,
                'message': '通知不存在或无权操作'
            }), 404
        
        service.mark_as_read(notification_id)
        
        return jsonify({
            'success': True,
            'message': '已标记为已读'
        }), 200
        
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        return jsonify({
            'success': False,
            'message': f'标记失败: {str(e)}'
        }), 500


@notification_bp.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    """标记所有通知为已读"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        service = get_notification_service()
        count = service.mark_all_as_read(user_id)
        
        return jsonify({
            'success': True,
            'message': f'已标记 {count} 条通知为已读'
        }), 200
        
    except Exception as e:
        logger.error(f"Mark all notifications read error: {e}")
        return jsonify({
            'success': False,
            'message': f'批量标记失败: {str(e)}'
        }), 500


# ==================== 学生反馈接口 ====================

@notification_bp.route('/<int:notification_id>/feedback', methods=['POST'])
@jwt_required()
def submit_feedback(notification_id):
    """
    学生提交反馈
    
    Request Body:
        {
            "feedback_type": "explain",  // acknowledge/explain/appeal/commit
            "content": "老师好，当时是因为...",
            "attachment_url": "http://..."  // 可选
        }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('feedback_type') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: feedback_type, content'
            }), 400
        
        valid_types = ['acknowledge', 'explain', 'appeal', 'commit']
        if data['feedback_type'] not in valid_types:
            return jsonify({
                'success': False,
                'message': f'无效的反馈类型，可选: {", ".join(valid_types)}'
            }), 400
        
        claims = get_jwt()
        student_id = claims.get('user_id')
        
        service = get_notification_service()
        feedback_id = service.submit_feedback(
            notification_id=notification_id,
            student_id=student_id,
            feedback_type=data['feedback_type'],
            content=data['content'],
            attachment_url=data.get('attachment_url')
        )
        
        return jsonify({
            'success': True,
            'message': '反馈提交成功',
            'data': {'feedback_id': feedback_id}
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Submit feedback error: {e}")
        return jsonify({
            'success': False,
            'message': f'提交反馈失败: {str(e)}'
        }), 500


@notification_bp.route('/my-feedbacks', methods=['GET'])
@jwt_required()
def get_my_feedbacks():
    """获取我的反馈历史（学生）"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        claims = get_jwt()
        student_id = claims.get('user_id')
        
        service = get_notification_service()
        feedbacks = service.get_student_feedbacks(student_id, page, page_size)
        
        return jsonify({
            'success': True,
            'data': {
                'items': feedbacks,
                'page': page,
                'page_size': page_size
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get my feedbacks error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取反馈历史失败: {str(e)}'
        }), 500


# ==================== 反馈审核接口（老师/管理员） ====================

@notification_bp.route('/feedbacks/pending', methods=['GET'])
@jwt_required()
def get_pending_feedbacks():
    """获取待审核的反馈列表"""
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '无权访问'
        }), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        claims = get_jwt()
        sender_id = claims.get('user_id')
        role = claims.get('role', '')
        
        # 管理员可以看所有，老师只能看自己发送的通知的反馈
        if role == 'admin':
            sender_id = None
        
        service = get_notification_service()
        feedbacks, total = service.get_pending_feedbacks(sender_id, page, page_size)
        
        return jsonify({
            'success': True,
            'data': {
                'items': feedbacks,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get pending feedbacks error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取待审核反馈失败: {str(e)}'
        }), 500


@notification_bp.route('/feedbacks/<int:feedback_id>', methods=['GET'])
@jwt_required()
def get_feedback_detail(feedback_id):
    """获取反馈详情"""
    try:
        service = get_notification_service()
        feedback = service.get_feedback(feedback_id)
        
        if not feedback:
            return jsonify({
                'success': False,
                'message': '反馈不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': feedback
        }), 200
        
    except Exception as e:
        logger.error(f"Get feedback detail error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取反馈详情失败: {str(e)}'
        }), 500


@notification_bp.route('/feedbacks/<int:feedback_id>/review', methods=['POST'])
@jwt_required()
def review_feedback(feedback_id):
    """
    审核反馈
    
    Request Body:
        {
            "status": "accepted",  // reviewed/accepted/rejected
            "comment": "已了解情况，感谢反馈"
        }
    """
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '只有老师和管理员可以审核反馈'
        }), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('status'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: status'
            }), 400
        
        claims = get_jwt()
        reviewer_id = claims.get('user_id')
        
        service = get_notification_service()
        service.review_feedback(
            feedback_id=feedback_id,
            reviewer_id=reviewer_id,
            status=data['status'],
            comment=data.get('comment')
        )
        
        return jsonify({
            'success': True,
            'message': '审核完成'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Review feedback error: {e}")
        return jsonify({
            'success': False,
            'message': f'审核失败: {str(e)}'
        }), 500


# ==================== 模板接口 ====================

@notification_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """获取通知模板列表"""
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '无权访问'
        }), 403
    
    try:
        behavior_type = request.args.get('behavior_type')
        
        service = get_notification_service()
        templates = service.get_templates(behavior_type)
        
        return jsonify({
            'success': True,
            'data': templates
        }), 200
        
    except Exception as e:
        logger.error(f"Get templates error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取模板失败: {str(e)}'
        }), 500


@notification_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_template():
    """创建通知模板"""
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '无权操作'
        }), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('template_name') or not data.get('title_template') or not data.get('content_template'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        service = get_notification_service()
        template_id = service.create_template(
            template_name=data['template_name'],
            title_template=data['title_template'],
            content_template=data['content_template'],
            behavior_type=data.get('behavior_type'),
            notification_type=data.get('notification_type', 'warning'),
            created_by=user_id
        )
        
        return jsonify({
            'success': True,
            'message': '模板创建成功',
            'data': {'template_id': template_id}
        }), 201
        
    except Exception as e:
        logger.error(f"Create template error: {e}")
        return jsonify({
            'success': False,
            'message': f'创建模板失败: {str(e)}'
        }), 500


# ==================== 统计接口 ====================

@notification_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_notification_statistics():
    """获取通知统计"""
    if not check_teacher_or_admin():
        return jsonify({
            'success': False,
            'message': '无权访问'
        }), 403
    
    try:
        days = request.args.get('days', 30, type=int)
        
        claims = get_jwt()
        user_id = claims.get('user_id')
        role = claims.get('role', '')
        
        # 管理员看全局统计，老师看自己的统计
        if role == 'admin':
            user_id = None
        
        service = get_notification_service()
        stats = service.get_statistics(user_id, days)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Get notification statistics error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        }), 500
