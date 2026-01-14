"""
认证API模块
Authentication API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt
)
import logging

from backend.service.AuthService import get_auth_service

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


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
        
        # 调用认证服务
        auth_service = get_auth_service()
        user = auth_service.authenticate_user(username, password)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
        
        # 生成JWT令牌
        access_token, refresh_token = auth_service.generate_tokens(user)
        
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
                    'student_id': user.get('student_id')
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
        
        auth_service = get_auth_service()
        access_token = auth_service.refresh_access_token(identity, claims)
        
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
        
        auth_service = get_auth_service()
        success, user_info, error_msg = auth_service.get_user_info(user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 404 if "不存在" in error_msg else 500
        
        return jsonify({
            'success': True,
            'data': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500
