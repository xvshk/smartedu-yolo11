"""
预警API模块
Alert API endpoints for alert management, rules, and notifications
"""
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt
import logging
from datetime import datetime, date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.alert_service import get_alert_service, AlertService
from backend.services.rule_engine import get_rule_engine, RuleEngine
from backend.services.intervention_service import get_intervention_service, InterventionService
from src.database.manager import DatabaseManager
from src.database.repositories.rule_repository import RuleRepository

logger = logging.getLogger(__name__)
alert_bp = Blueprint('alert', __name__)


# ==================== 预警查询接口 ====================

@alert_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """
    获取预警列表
    
    Query Parameters:
        page: 页码 (default: 1)
        page_size: 每页数量 (default: 20)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        alert_level: 预警级别 (0-3)
        behavior_type: 行为类型
        is_read: 是否已读 (true/false)
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        alert_level = request.args.get('alert_level', type=int)
        behavior_type = request.args.get('behavior_type')
        
        # 解析日期
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None
        
        service = get_alert_service()
        alerts, total = service.get_alert_history(
            start_date=start_date,
            end_date=end_date,
            alert_level=alert_level,
            behavior_type=behavior_type,
            page=page,
            page_size=page_size
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': alerts,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取预警列表失败: {str(e)}'
        }), 500


@alert_bp.route('/alerts/<int:alert_id>', methods=['GET'])
@jwt_required()
def get_alert_detail(alert_id):
    """获取预警详情"""
    try:
        service = get_alert_service()
        alert = service.get_alert(alert_id)
        
        if not alert:
            return jsonify({
                'success': False,
                'message': '预警不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': alert
        }), 200
        
    except Exception as e:
        logger.error(f"Get alert detail error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取预警详情失败: {str(e)}'
        }), 500


@alert_bp.route('/alerts/unread', methods=['GET'])
@jwt_required()
def get_unread_alerts():
    """获取未读预警"""
    try:
        limit = request.args.get('limit', 50, type=int)
        service = get_alert_service()
        alerts = service.get_unread_alerts(limit)
        
        return jsonify({
            'success': True,
            'data': {
                'items': alerts,
                'count': len(alerts)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get unread alerts error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取未读预警失败: {str(e)}'
        }), 500


@alert_bp.route('/alerts/<int:alert_id>/read', methods=['POST'])
@jwt_required()
def mark_alert_read(alert_id):
    """标记预警为已读"""
    try:
        service = get_alert_service()
        service.mark_alert_read(alert_id)
        
        return jsonify({
            'success': True,
            'message': '已标记为已读'
        }), 200
        
    except Exception as e:
        logger.error(f"Mark alert read error: {e}")
        return jsonify({
            'success': False,
            'message': f'标记失败: {str(e)}'
        }), 500


@alert_bp.route('/alerts/read-all', methods=['POST'])
@jwt_required()
def mark_all_alerts_read():
    """批量标记预警为已读"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        service = get_alert_service()
        count = service.mark_all_read(session_id)
        
        return jsonify({
            'success': True,
            'message': f'已标记{count}条预警为已读'
        }), 200
        
    except Exception as e:
        logger.error(f"Mark all alerts read error: {e}")
        return jsonify({
            'success': False,
            'message': f'批量标记失败: {str(e)}'
        }), 500


@alert_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_alert(alert_id):
    """删除预警"""
    try:
        service = get_alert_service()
        service.delete_alert(alert_id)
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete alert error: {e}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ==================== 统计接口 ====================

@alert_bp.route('/alerts/statistics', methods=['GET'])
@jwt_required()
def get_alert_statistics():
    """
    获取预警统计
    
    Query Parameters:
        period: 统计周期 (daily/weekly/monthly)
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        period = request.args.get('period', 'daily')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None
        
        service = get_alert_service()
        stats = service.get_statistics(period, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': stats.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        }), 500


@alert_bp.route('/alerts/export', methods=['GET'])
@jwt_required()
def export_alerts():
    """
    导出预警数据
    
    Query Parameters:
        format: 导出格式 (csv/json)
        start_date: 开始日期
        end_date: 结束日期
        alert_level: 预警级别
    """
    try:
        export_format = request.args.get('format', 'csv')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        alert_level = request.args.get('alert_level', type=int)
        
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None
        
        service = get_alert_service()
        data = service.export_alerts(start_date, end_date, alert_level, export_format)
        
        if export_format == 'json':
            return Response(
                data,
                mimetype='application/json',
                headers={'Content-Disposition': 'attachment;filename=alerts.json'}
            )
        else:
            return Response(
                data,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=alerts.csv'}
            )
        
    except Exception as e:
        logger.error(f"Export alerts error: {e}")
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}'
        }), 500


# ==================== 规则管理接口 ====================

@alert_bp.route('/rules', methods=['GET'])
@jwt_required()
def get_rules():
    """获取规则列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        is_active = request.args.get('is_active')
        rule_type = request.args.get('rule_type')
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
        
        engine = get_rule_engine()
        rules, total = engine.list_rules(
            is_active=is_active,
            rule_type=rule_type,
            page=page,
            page_size=page_size
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': rules,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get rules error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取规则列表失败: {str(e)}'
        }), 500


@alert_bp.route('/rules/<int:rule_id>', methods=['GET'])
@jwt_required()
def get_rule_detail(rule_id):
    """获取规则详情"""
    try:
        engine = get_rule_engine()
        rule = engine.get_rule(rule_id)
        
        if not rule:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': rule
        }), 200
        
    except Exception as e:
        logger.error(f"Get rule detail error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取规则详情失败: {str(e)}'
        }), 500


@alert_bp.route('/rules', methods=['POST'])
@jwt_required()
def create_rule():
    """
    创建预警规则
    
    Request Body:
        {
            "rule_name": "睡觉预警",
            "rule_type": "frequency",
            "conditions": {"min_confidence": 0.5},
            "alert_level": 2,
            "description": "检测到睡觉行为时触发",
            "behavior_type": "睡觉",
            "threshold_count": 1,
            "time_window_seconds": 60
        }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('rule_name') or not data.get('rule_type'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: rule_name, rule_type'
            }), 400
        
        # 获取当前用户ID
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        engine = get_rule_engine()
        rule = engine.create_rule(
            rule_name=data['rule_name'],
            rule_type=data['rule_type'],
            conditions=data.get('conditions', {}),
            alert_level=data.get('alert_level', 1),
            description=data.get('description'),
            behavior_type=data.get('behavior_type'),
            threshold_count=data.get('threshold_count', 1),
            time_window_seconds=data.get('time_window_seconds', 60),
            created_by=user_id
        )
        
        return jsonify({
            'success': True,
            'message': '规则创建成功',
            'data': rule
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Create rule error: {e}")
        return jsonify({
            'success': False,
            'message': f'创建规则失败: {str(e)}'
        }), 500


@alert_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_rule(rule_id):
    """更新预警规则"""
    try:
        data = request.get_json()
        
        engine = get_rule_engine()
        rule = engine.update_rule(
            rule_id=rule_id,
            rule_name=data.get('rule_name'),
            rule_type=data.get('rule_type'),
            conditions=data.get('conditions'),
            alert_level=data.get('alert_level'),
            description=data.get('description'),
            behavior_type=data.get('behavior_type'),
            threshold_count=data.get('threshold_count'),
            time_window_seconds=data.get('time_window_seconds'),
            is_active=data.get('is_active')
        )
        
        return jsonify({
            'success': True,
            'message': '规则更新成功',
            'data': rule
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Update rule error: {e}")
        return jsonify({
            'success': False,
            'message': f'更新规则失败: {str(e)}'
        }), 500


@alert_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_rule(rule_id):
    """删除预警规则"""
    try:
        engine = get_rule_engine()
        success = engine.delete_rule(rule_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '规则删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete rule error: {e}")
        return jsonify({
            'success': False,
            'message': f'删除规则失败: {str(e)}'
        }), 500


# ==================== 干预建议接口 ====================

@alert_bp.route('/alerts/<int:alert_id>/suggestions', methods=['GET'])
@jwt_required()
def get_intervention_suggestions(alert_id):
    """获取干预建议"""
    try:
        service = get_alert_service()
        alert = service.get_alert(alert_id)
        
        if not alert:
            return jsonify({
                'success': False,
                'message': '预警不存在'
            }), 404
        
        intervention_service = get_intervention_service()
        suggestions = intervention_service.get_suggestions(alert)
        
        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in suggestions]
        }), 200
        
    except Exception as e:
        logger.error(f"Get suggestions error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取建议失败: {str(e)}'
        }), 500


@alert_bp.route('/alerts/<int:alert_id>/interventions', methods=['POST'])
@jwt_required()
def record_intervention(alert_id):
    """
    记录干预结果
    
    Request Body:
        {
            "action_taken": "轻声提醒",
            "outcome": "学生恢复听讲",
            "effectiveness_rating": 4
        }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('action_taken'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: action_taken'
            }), 400
        
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        intervention_service = get_intervention_service()
        intervention_id = intervention_service.record_intervention(
            alert_id=alert_id,
            action_taken=data['action_taken'],
            outcome=data.get('outcome'),
            effectiveness_rating=data.get('effectiveness_rating'),
            recorded_by=user_id
        )
        
        return jsonify({
            'success': True,
            'message': '干预记录已保存',
            'data': {'intervention_id': intervention_id}
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Record intervention error: {e}")
        return jsonify({
            'success': False,
            'message': f'记录干预失败: {str(e)}'
        }), 500


@alert_bp.route('/interventions/<int:intervention_id>', methods=['PUT'])
@jwt_required()
def update_intervention(intervention_id):
    """更新干预结果"""
    try:
        data = request.get_json()
        
        intervention_service = get_intervention_service()
        intervention_service.update_intervention_outcome(
            intervention_id=intervention_id,
            outcome=data.get('outcome', ''),
            effectiveness_rating=data.get('effectiveness_rating', 3)
        )
        
        return jsonify({
            'success': True,
            'message': '干预记录已更新'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Update intervention error: {e}")
        return jsonify({
            'success': False,
            'message': f'更新干预记录失败: {str(e)}'
        }), 500


@alert_bp.route('/interventions/statistics', methods=['GET'])
@jwt_required()
def get_intervention_statistics():
    """获取干预有效性统计"""
    try:
        behavior_type = request.args.get('behavior_type')
        
        intervention_service = get_intervention_service()
        stats = intervention_service.get_effectiveness_statistics(behavior_type)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Get intervention statistics error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        }), 500


# ==================== 通知偏好接口 ====================

@alert_bp.route('/notification-preferences', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    """获取当前用户的通知偏好"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '无法获取用户信息'
            }), 401
        
        db = DatabaseManager()
        repo = RuleRepository(db)
        prefs = repo.get_notification_preferences(user_id)
        
        if not prefs:
            # 返回默认偏好
            prefs = {
                'user_id': user_id,
                'alert_level_0': False,
                'alert_level_1': True,
                'alert_level_2': True,
                'alert_level_3': True,
                'sound_enabled': True
            }
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': prefs
        }), 200
        
    except Exception as e:
        logger.error(f"Get notification preferences error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取通知偏好失败: {str(e)}'
        }), 500


@alert_bp.route('/notification-preferences', methods=['POST'])
@jwt_required()
def update_notification_preferences():
    """
    更新通知偏好
    
    Request Body:
        {
            "alert_level_0": false,
            "alert_level_1": true,
            "alert_level_2": true,
            "alert_level_3": true,
            "sound_enabled": true
        }
    """
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '无法获取用户信息'
            }), 401
        
        data = request.get_json() or {}
        
        db = DatabaseManager()
        repo = RuleRepository(db)
        repo.create_or_update_notification_preferences(
            user_id=user_id,
            alert_level_0=data.get('alert_level_0', False),
            alert_level_1=data.get('alert_level_1', True),
            alert_level_2=data.get('alert_level_2', True),
            alert_level_3=data.get('alert_level_3', True),
            sound_enabled=data.get('sound_enabled', True)
        )
        
        db.close()
        
        return jsonify({
            'success': True,
            'message': '通知偏好已更新'
        }), 200
        
    except Exception as e:
        logger.error(f"Update notification preferences error: {e}")
        return jsonify({
            'success': False,
            'message': f'更新通知偏好失败: {str(e)}'
        }), 500
