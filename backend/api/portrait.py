"""
学业全景画像API模块
Student Portrait API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime, date
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager
from backend.services.portrait_service import PortraitService
from backend.config import Config

logger = logging.getLogger(__name__)
portrait_bp = Blueprint('portrait', __name__)


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


def parse_date(date_str: str) -> date:
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


@portrait_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """获取班级概览数据"""
    try:
        class_id = request.args.get('class_id', type=int)
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        
        db = get_db()
        service = PortraitService(db)
        data = service.get_class_overview(class_id, start_date, end_date)
        db.close()
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Get overview error: {e}")
        return jsonify({'success': False, 'message': f'获取概览失败: {str(e)}'}), 500


@portrait_bp.route('/behavior-distribution', methods=['GET'])
@jwt_required()
def get_behavior_distribution():
    """获取行为分布统计"""
    try:
        class_id = request.args.get('class_id', type=int)
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        
        db = get_db()
        service = PortraitService(db)
        data = service.get_behavior_distribution(class_id, start_date, end_date)
        db.close()
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Get behavior distribution error: {e}")
        return jsonify({'success': False, 'message': f'获取行为分布失败: {str(e)}'}), 500


@portrait_bp.route('/attention-trend', methods=['GET'])
@jwt_required()
def get_attention_trend():
    """获取注意力趋势数据"""
    try:
        class_id = request.args.get('class_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        db = get_db()
        service = PortraitService(db)
        data = service.get_attention_trend(class_id=class_id, days=days)
        db.close()
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Get attention trend error: {e}")
        return jsonify({'success': False, 'message': f'获取注意力趋势失败: {str(e)}'}), 500


@portrait_bp.route('/warning-ranking', methods=['GET'])
@jwt_required()
def get_warning_ranking():
    """获取预警行为排名"""
    try:
        class_id = request.args.get('class_id', type=int)
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        limit = request.args.get('limit', 5, type=int)
        
        db = get_db()
        service = PortraitService(db)
        data = service.get_warning_ranking(class_id, start_date, end_date, limit)
        db.close()
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Get warning ranking error: {e}")
        return jsonify({'success': False, 'message': f'获取预警排名失败: {str(e)}'}), 500


@portrait_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_portrait(student_id):
    """获取学生个人画像"""
    try:
        claims = get_jwt()
        user_role = claims.get('role', '')
        user_student_id = claims.get('student_id')
        
        # 学生只能查看自己的画像
        if user_role == 'student' and user_student_id != student_id:
            return jsonify({'success': False, 'message': '只能查看自己的画像'}), 403
        
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        
        db = get_db()
        service = PortraitService(db)
        data = service.get_student_portrait(student_id, start_date, end_date)
        db.close()
        
        if not data:
            return jsonify({'success': False, 'message': '学生不存在'}), 404
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Get student portrait error: {e}")
        return jsonify({'success': False, 'message': f'获取学生画像失败: {str(e)}'}), 500


@portrait_bp.route('/student/<int:student_id>/suggestions', methods=['GET'])
@jwt_required()
def get_student_suggestions(student_id):
    """获取学生改进建议"""
    try:
        claims = get_jwt()
        user_role = claims.get('role', '')
        user_student_id = claims.get('student_id')
        
        # 学生只能查看自己的建议
        if user_role == 'student' and user_student_id != student_id:
            return jsonify({'success': False, 'message': '只能查看自己的建议'}), 403
        
        db = get_db()
        service = PortraitService(db)
        data = service.get_improvement_suggestions(student_id)
        db.close()
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Get student suggestions error: {e}")
        return jsonify({'success': False, 'message': f'获取改进建议失败: {str(e)}'}), 500


@portrait_bp.route('/export', methods=['GET'])
@jwt_required()
def export_data():
    """导出画像数据"""
    try:
        class_id = request.args.get('class_id', type=int)
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        
        db = get_db()
        service = PortraitService(db)
        data = service.export_portrait_data(class_id, start_date, end_date)
        db.close()
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Export portrait data error: {e}")
        return jsonify({'success': False, 'message': f'导出数据失败: {str(e)}'}), 500


@portrait_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    """获取学生列表"""
    try:
        class_id = request.args.get('class_id', type=int)
        
        db = get_db()
        from src.database.repositories.student_repository import StudentRepository
        student_repo = StudentRepository(db)
        students = student_repo.list_students(class_id=class_id, limit=200)
        db.close()
        
        return jsonify({
            'success': True, 
            'data': [{'student_id': s['student_id'], 'name': s['name'], 'student_number': s['student_number'], 'class_id': s.get('class_id')} for s in students]
        }), 200
    except Exception as e:
        logger.error(f"Get students error: {e}")
        return jsonify({'success': False, 'message': f'获取学生列表失败: {str(e)}'}), 500


@portrait_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_classes():
    """获取班级列表"""
    try:
        db = get_db()
        from src.database.repositories.student_repository import StudentRepository
        student_repo = StudentRepository(db)
        classes = student_repo.list_classes(limit=100)
        db.close()
        
        return jsonify({
            'success': True, 
            'data': [{'class_id': c['class_id'], 'class_name': c['class_name'], 'grade': c.get('grade', ''), 'department': c.get('department', '')} for c in classes]
        }), 200
    except Exception as e:
        logger.error(f"Get classes error: {e}")
        return jsonify({'success': False, 'message': f'获取班级列表失败: {str(e)}'}), 500
