"""
认证服务模块
Authentication service for handling user authentication and authorization
"""
import logging
from typing import Dict, Optional, Tuple, Any
from flask_jwt_extended import create_access_token, create_refresh_token

from backend.model.ConfigModel import DatabaseConfig
from backend.model.ManagerModel import DatabaseManager
from backend.model.UserModel import UserRepository
from backend.model.StudentModel import StudentRepository
from backend.config import Config
from .InterfaceService import IAuthService

logger = logging.getLogger(__name__)


class AuthService(IAuthService):
    """
    认证服务 - 处理用户认证和授权业务逻辑
    
    职责:
    - 用户登录验证
    - JWT令牌生成和刷新
    - 用户信息获取
    - 权限验证
    """
    
    def __init__(self, db: DatabaseManager = None):
        """
        初始化认证服务
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db or self._create_db_connection()
        self.user_repo = UserRepository(self.db)
        self.student_repo = StudentRepository(self.db)
    
    def _create_db_connection(self) -> DatabaseManager:
        """创建数据库连接"""
        config = DatabaseConfig(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return DatabaseManager(config)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户信息字典，认证失败返回None
        """
        try:
            # 参数验证
            if not username or not password:
                return None
            
            username = username.strip()
            password = password.strip()
            
            # 验证用户
            user = self.user_repo.verify_password(username, password)
            
            if not user:
                return None
            
            # 如果是学生角色，查找对应的学生ID
            student_id = None
            if user['role'] == 'student':
                student = self.student_repo.get_student_by_number(username)
                if student:
                    student_id = student['student_id']
                    logger.info(f"Found student_id {student_id} for username {username}")
            
            # 添加学生ID到用户信息
            user_info = dict(user)
            user_info['student_id'] = student_id
            
            logger.info(f"User {username} authenticated successfully")
            return user_info
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """
        创建用户
        
        Args:
            user_data: 用户数据
            
        Returns:
            新用户的ID
        """
        try:
            return self.user_repo.create_user(user_data)
        except Exception as e:
            logger.error(f"Create user error: {e}")
            raise
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 更新的用户数据
            
        Returns:
            是否更新成功
        """
        try:
            return self.user_repo.update_user(user_id, user_data)
        except Exception as e:
            logger.error(f"Update user error: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            return self.user_repo.delete_user(user_id)
        except Exception as e:
            logger.error(f"Delete user error: {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息，不存在返回None
        """
        try:
            return self.user_repo.get_user(user_id)
        except Exception as e:
            logger.error(f"Get user by id error: {e}")
            return None
    
    def generate_tokens(self, user: Dict) -> Tuple[str, str]:
        """
        生成JWT令牌
        
        Args:
            user: 用户信息
            
        Returns:
            (access_token, refresh_token)
        """
        user_identity = str(user['user_id'])
        
        additional_claims = {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'student_id': user.get('student_id')
        }
        
        access_token = create_access_token(
            identity=user_identity,
            additional_claims=additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=user_identity,
            additional_claims=additional_claims
        )
        
        return access_token, refresh_token
    
    def refresh_access_token(self, identity: str, claims: Dict) -> str:
        """
        刷新访问令牌
        
        Args:
            identity: 用户身份标识
            claims: JWT声明
            
        Returns:
            新的访问令牌
        """
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                'user_id': claims.get('user_id'),
                'username': claims.get('username'),
                'role': claims.get('role'),
                'student_id': claims.get('student_id')
            }
        )
        
        return access_token
    
    def get_user_info(self, user_id: int) -> Tuple[bool, Optional[Dict], str]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            (是否成功, 用户信息, 错误消息)
        """
        try:
            user = self.user_repo.get_user(user_id)
            
            if not user:
                return False, None, "用户不存在"
            
            # 获取用户权限
            permissions = self.user_repo.get_all_permissions_for_user(user['user_id'])
            
            user_info = {
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'email': user.get('email'),
                'permissions': permissions,
                'created_at': str(user.get('created_at')),
                'last_login': str(user.get('last_login')) if user.get('last_login') else None
            }
            
            return True, user_info, ""
            
        except Exception as e:
            logger.error(f"Get user info error: {e}")
            return False, None, f"获取用户信息失败: {str(e)}"
    
    def validate_user_permissions(self, user_id: int, required_permission: str) -> bool:
        """
        验证用户权限
        
        Args:
            user_id: 用户ID
            required_permission: 需要的权限
            
        Returns:
            是否有权限
        """
        try:
            permissions = self.user_repo.get_all_permissions_for_user(user_id)
            return required_permission in permissions
        except Exception as e:
            logger.error(f"Permission validation error: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()


# 单例模式
_auth_service_instance = None


def get_auth_service() -> AuthService:
    """获取认证服务单例"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance