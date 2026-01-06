"""
认证API模块
Authentication API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager
from src.database.repositories.user_repository import UserRepository
from backend.config import Config

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


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


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    Request Body:
        {
            "username": "admin",
            "password": "admin123",
            "school": "东软智慧教育平台"  # 可选
        }
    
    Response:
        {
            "success": true,
            "message": "登录成功",
            "data": {
                "access_token": "...",
                "refresh_token": "...",
                "user": {
                    "user_id": 1,
                    "username": "admin",
                    "role": "admin",
                    "email": "admin@example.com"
                }
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 验证用户
        db = get_db()
        user_repo = UserRepository(db)
        user = user_repo.verify_password(username, password)
        
        if not user:
            db.close()
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
        
        # 如果是学生角色，查找对应的学生ID
        student_id = None
        if user['role'] == 'student':
            from src.database.repositories.student_repository import StudentRepository
            student_repo = StudentRepository(db)
            # 通过学号（用户名）查找学生
            student = student_repo.get_student_by_number(username)
            if student:
                student_id = student['student_id']
                logger.info(f"Found student_id {student_id} for username {username}")
        
        # 生成JWT令牌 - identity 使用 user_id 字符串
        user_identity = str(user['user_id'])
        access_token = create_access_token(
            identity=user_identity,
            additional_claims={
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'student_id': student_id
            }
        )
        refresh_token = create_refresh_token(
            identity=user_identity,
            additional_claims={
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'student_id': student_id
            }
        )
        
        db.close()
        
        logger.info(f"User {username} logged in successfully")
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'role': user['role'],
                    'email': user.get('email'),
                    'student_id': student_id
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                'user_id': claims.get('user_id'),
                'username': claims.get('username'),
                'role': claims.get('role')
            }
        )
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'message': f'刷新令牌失败: {str(e)}'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    # JWT是无状态的，客户端删除令牌即可
    return jsonify({
        'success': True,
        'message': '登出成功'
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        db = get_db()
        user_repo = UserRepository(db)
        user = user_repo.get_user(user_id)
        
        if not user:
            db.close()
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 获取用户权限
        permissions = user_repo.get_all_permissions_for_user(user['user_id'])
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'email': user.get('email'),
                'permissions': permissions,
                'created_at': str(user.get('created_at')),
                'last_login': str(user.get('last_login')) if user.get('last_login') else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500
