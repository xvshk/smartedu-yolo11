"""
系统设置API模块
System settings API endpoints
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt
import logging
import sys
import os
import json
from datetime import datetime, timedelta
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager
from src.database.repositories.detection_repository import DetectionRepository
from src.database.repositories.user_repository import UserRepository
from backend.config import Config

logger = logging.getLogger(__name__)
settings_bp = Blueprint('settings', __name__)


def get_db():
    """获取数据库连接"""
    config = DatabaseConfig(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    return DatabaseManager(config)


@settings_bp.route('/export/<data_type>', methods=['GET'])
@jwt_required()
def export_data(data_type):
    """导出数据为CSV格式"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        db = get_db()
        
        if data_type == 'detection':
            # 导出检测记录
            detection_repo = DetectionRepository(db)
            records = detection_repo.get_all_sessions(limit=10000)
            
            # 生成CSV
            csv_content = "会话ID,课程ID,开始时间,结束时间,状态,总帧数,检测帧数\n"
            for record in records:
                csv_content += f"{record.get('session_id', '')},{record.get('course_id', '')},"
                csv_content += f"{record.get('start_time', '')},{record.get('end_time', '')},"
                csv_content += f"{record.get('status', '')},{record.get('total_frames', 0)},"
                csv_content += f"{record.get('detected_frames', 0)}\n"
            
            db.close()
            
            # 返回文件
            output = io.BytesIO()
            output.write(csv_content.encode('utf-8-sig'))
            output.seek(0)
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'detection_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
        elif data_type == 'alert':
            # 导出预警记录
            detection_repo = DetectionRepository(db)
            alerts = detection_repo.get_alerts(limit=10000)
            
            csv_content = "预警ID,学生ID,会话ID,预警类型,预警级别,预警消息,创建时间,是否已读\n"
            for alert in alerts:
                csv_content += f"{alert.get('alert_id', '')},{alert.get('student_id', '')},"
                csv_content += f"{alert.get('session_id', '')},{alert.get('alert_type', '')},"
                csv_content += f"{alert.get('alert_level', '')},{alert.get('alert_message', '')},"
                csv_content += f"{alert.get('created_at', '')},{alert.get('is_read', 0)}\n"
            
            db.close()
            
            output = io.BytesIO()
            output.write(csv_content.encode('utf-8-sig'))
            output.seek(0)
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'alert_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
        elif data_type == 'statistics':
            # 导出统计报表
            detection_repo = DetectionRepository(db)
            stats = detection_repo.get_behavior_statistics()
            
            csv_content = "行为类型,总次数,平均置信度\n"
            for stat in stats:
                csv_content += f"{stat.get('behavior_type', '')},{stat.get('count', 0)},"
                csv_content += f"{stat.get('avg_confidence', 0):.2f}\n"
            
            db.close()
            
            output = io.BytesIO()
            output.write(csv_content.encode('utf-8-sig'))
            output.seek(0)
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'statistics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        else:
            db.close()
            return jsonify({
                'success': False,
                'message': '不支持的导出类型'
            }), 400
            
    except Exception as e:
        logger.error(f"Export data error: {e}")
        return jsonify({
            'success': False,
            'message': f'导出数据失败: {str(e)}'
        }), 500


@settings_bp.route('/cleanup', methods=['POST'])
@jwt_required()
def cleanup_data():
    """清理历史数据"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        # 检查管理员权限
        db = get_db()
        user_repo = UserRepository(db)
        if not user_repo.has_permission(user_id, 'manage_users'):
            db.close()
            return jsonify({
                'success': False,
                'message': '没有权限执行此操作'
            }), 403
        
        data = request.get_json()
        days = data.get('days', 30)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 清理检测记录
        detection_repo = DetectionRepository(db)
        deleted_count = detection_repo.cleanup_old_records(cutoff_date)
        
        db.close()
        
        logger.info(f"User {user_id} cleaned up {deleted_count} records older than {days} days")
        
        return jsonify({
            'success': True,
            'message': f'成功清理 {deleted_count} 条历史记录',
            'data': {
                'deleted_count': deleted_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Cleanup data error: {e}")
        return jsonify({
            'success': False,
            'message': f'清理数据失败: {str(e)}'
        }), 500


@settings_bp.route('/system-info', methods=['GET'])
@jwt_required()
def get_system_info():
    """获取系统信息"""
    try:
        db = get_db()
        
        # 获取数据库统计
        detection_repo = DetectionRepository(db)
        user_repo = UserRepository(db)
        
        # 统计数据
        total_sessions = len(detection_repo.get_all_sessions(limit=100000))
        total_users = len(user_repo.list_users(limit=100000))
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'version': '1.0.0',
                'build_time': '2024-01-04',
                'total_sessions': total_sessions,
                'total_users': total_users,
                'database': 'MySQL',
                'ai_engine': 'YOLOv11'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get system info error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取系统信息失败: {str(e)}'
        }), 500


@settings_bp.route('/user-settings', methods=['GET'])
@jwt_required()
def get_user_settings():
    """获取用户设置"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        db = get_db()
        
        # 从数据库获取用户设置（如果有的话）
        result = db.query_one(
            "SELECT settings FROM users WHERE user_id = %s",
            (user_id,)
        )
        
        db.close()
        
        settings = {}
        if result and result.get('settings'):
            try:
                settings = json.loads(result['settings'])
            except:
                settings = {}
        
        return jsonify({
            'success': True,
            'data': settings
        }), 200
        
    except Exception as e:
        logger.error(f"Get user settings error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取设置失败: {str(e)}'
        }), 500


@settings_bp.route('/user-settings', methods=['POST'])
@jwt_required()
def save_user_settings():
    """保存用户设置"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        data = request.get_json()
        settings_json = json.dumps(data)
        
        db = get_db()
        
        # 检查是否有settings列，如果没有则添加
        try:
            db.execute(
                "UPDATE users SET settings = %s WHERE user_id = %s",
                (settings_json, user_id)
            )
        except Exception as e:
            # 如果列不存在，先添加列
            logger.warning(f"Settings column may not exist, adding it: {e}")
            db.execute("ALTER TABLE users ADD COLUMN settings TEXT")
            db.execute(
                "UPDATE users SET settings = %s WHERE user_id = %s",
                (settings_json, user_id)
            )
        
        db.close()
        
        return jsonify({
            'success': True,
            'message': '设置保存成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Save user settings error: {e}")
        return jsonify({
            'success': False,
            'message': f'保存设置失败: {str(e)}'
        }), 500
