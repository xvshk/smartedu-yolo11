"""
用户管理API模块
User management API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.model.ConfigModel import DatabaseConfig
from backend.model.ManagerModel import DatabaseManager
from backend.model.UserModel import UserRepository
from backend.config import Config

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)


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


def check_permission(user_id: int, permission: str) -> bool:
    """检查用户权限"""
    db = get_db()
    user_repo = UserRepository(db)
    has_perm = user_repo.has_permission(user_id, permission)
    db.close()
    return has_perm


@user_bp.route('/list', methods=['GET'])
@jwt_required()
def list_users():
    """获取用户列表"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        # 检查权限
        if not check_permission(user_id, 'manage_users'):
            return jsonify({
                'success': False,
                'message': '没有权限访问'
            }), 403
        
        # 获取查询参数
        role = request.args.get('role')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        
        db = get_db()
        user_repo = UserRepository(db)
        
        users = user_repo.list_users(
            role=role,
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        # 获取总数
        total_users = user_repo.list_users(role=role, limit=10000)
        total = len(total_users)
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'users': users,
                'page': page,
                'page_size': page_size,
                'total': total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@user_bp.route('/create', methods=['POST'])
@jwt_required()
def create_user():
    """创建用户"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        username = claims.get('username')
        
        # 检查权限
        if not check_permission(user_id, 'manage_users'):
            return jsonify({
                'success': False,
                'message': '没有权限创建用户'
            }), 403
        
        data = request.get_json()
        
        new_username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'viewer')
        
        if not new_username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        db = get_db()
        user_repo = UserRepository(db)
        
        # 检查用户名是否已存在
        existing = user_repo.get_user_by_username(new_username)
        if existing:
            db.close()
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 400
        
        new_user_id = user_repo.create_user(
            username=new_username,
            password=password,
            email=email,
            role=role
        )
        
        db.close()
        
        logger.info(f"User {new_username} created by {username}")
        
        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'data': {
                'user_id': new_user_id
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({
            'success': False,
            'message': f'创建用户失败: {str(e)}'
        }), 500


@user_bp.route('/update/<int:target_user_id>', methods=['PUT'])
@jwt_required()
def update_user(target_user_id):
    """更新用户信息"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        # 只能修改自己或有管理权限
        if user_id != target_user_id:
            if not check_permission(user_id, 'manage_users'):
                return jsonify({
                    'success': False,
                    'message': '没有权限修改此用户'
                }), 403
        
        data = request.get_json()
        
        db = get_db()
        user_repo = UserRepository(db)
        
        # 更新允许的字段
        update_fields = {}
        if 'email' in data:
            update_fields['email'] = data['email']
        if 'role' in data and check_permission(user_id, 'manage_users'):
            update_fields['role'] = data['role']
        if 'is_active' in data and check_permission(user_id, 'manage_users'):
            update_fields['is_active'] = data['is_active']
        
        if update_fields:
            user_repo.update_user(target_user_id, **update_fields)
        
        # 更新密码
        if 'password' in data and data['password']:
            user_repo.update_password(target_user_id, data['password'])
        
        db.close()
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Update user error: {e}")
        return jsonify({
            'success': False,
            'message': f'更新用户失败: {str(e)}'
        }), 500


@user_bp.route('/delete/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(target_user_id):
    """删除用户"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        username = claims.get('username')
        
        # 检查权限
        if not check_permission(user_id, 'manage_users'):
            return jsonify({
                'success': False,
                'message': '没有权限删除用户'
            }), 403
        
        # 不能删除自己
        if user_id == target_user_id:
            return jsonify({
                'success': False,
                'message': '不能删除自己的账户'
            }), 400
        
        db = get_db()
        user_repo = UserRepository(db)
        user_repo.delete_user(target_user_id)
        db.close()
        
        logger.info(f"User {target_user_id} deleted by {username}")
        
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        }), 500


@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改当前用户密码"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        
        data = request.get_json()
        old_password = data.get('old_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'message': '请输入当前密码和新密码'
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': '新密码长度不能少于6位'
            }), 400
        
        db = get_db()
        user_repo = UserRepository(db)
        
        # 获取用户信息
        user = user_repo.get_user(user_id)
        if not user:
            db.close()
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 验证旧密码
        if not user_repo._check_password(old_password, user['password_hash']):
            db.close()
            return jsonify({
                'success': False,
                'message': '当前密码错误'
            }), 400
        
        # 更新密码
        user_repo.update_password(user_id, new_password)
        db.close()
        
        logger.info(f"User {user_id} changed password")
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({
            'success': False,
            'message': f'密码修改失败: {str(e)}'
        }), 500
