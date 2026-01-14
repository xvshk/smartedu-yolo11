"""
用户仓库模块
User repository for user management and authentication
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import bcrypt
from backend.model.ManagerModel import DatabaseManager
from backend.model.InterfaceModel import IUserRepository

logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    """用户数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        """
        初始化用户仓库
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
    
    # ==================== 基础CRUD操作 ====================
    
    def create(self, data: Dict[str, Any]) -> int:
        """创建用户记录"""
        return self.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'student'),
            full_name=data.get('full_name')
        )
    
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        return self.get_user_by_id(id)
    
    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """更新用户记录"""
        return self.update_user(id, data)
    
    def delete(self, id: int) -> bool:
        """删除用户记录"""
        return self.delete_user(id)
    
    def get_all(self, limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """获取所有用户（分页）"""
        return self.get_all_users(limit=limit, offset=offset)
    
    # ==================== 用户 CRUD ====================
    
    def create_user(
        self,
        username: str,
        password: str,
        email: str = None,
        role: str = 'viewer'
    ) -> int:
        """
        创建用户
        
        Args:
            username: 用户名
            password: 明文密码（将被加密存储）
            email: 邮箱
            role: 角色 (admin/teacher/student/viewer)
            
        Returns:
            新创建的user_id
        """
        # 加密密码
        password_hash = self._hash_password(password)
        
        sql = """
            INSERT INTO users (username, password_hash, email, role)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (username, password_hash, email, role))
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典或None
        """
        sql = "SELECT * FROM users WHERE user_id = %s"
        return self.db.query_one(sql, (user_id,))
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        return self.get_user_by_username(username)
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            用户信息字典或None
        """
        sql = "SELECT * FROM users WHERE email = %s"
        return self.db.query_one(sql, (email,))
    
    def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索用户
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            用户列表
        """
        sql = """
            SELECT user_id, username, email, role, created_at, last_login, is_active 
            FROM users 
            WHERE username LIKE %s OR email LIKE %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        search_pattern = f"%{query}%"
        return self.db.query(sql, (search_pattern, search_pattern, limit))
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        按用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典或None
        """
        sql = "SELECT * FROM users WHERE username = %s"
        return self.db.query_one(sql, (username,))
    
    def update_user(self, user_id: int, **kwargs) -> None:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段 (email, role, is_active)
        """
        allowed_fields = {'email', 'role', 'is_active'}
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)
        
        if not updates:
            return
        
        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
        self.db.execute(sql, tuple(params))
    
    def update_password(self, user_id: int, password_hash: str) -> bool:
        """
        更新用户密码
        
        Args:
            user_id: 用户ID
            password_hash: 密码哈希（如果是明文密码，会自动加密）
            
        Returns:
            是否更新成功
        """
        try:
            # 如果传入的不是哈希值，则进行加密
            if not password_hash.startswith('$2b$'):
                password_hash = self._hash_password(password_hash)
            
            sql = "UPDATE users SET password_hash = %s WHERE user_id = %s"
            self.db.execute(sql, (password_hash, user_id))
            return True
        except Exception as e:
            logger.error(f"Update password failed: {e}")
            return False
    
    def update_last_login(self, user_id: int, login_time: datetime = None) -> bool:
        """
        更新最后登录时间
        
        Args:
            user_id: 用户ID
            login_time: 登录时间，默认为当前时间
            
        Returns:
            是否更新成功
        """
        try:
            if login_time:
                sql = "UPDATE users SET last_login = %s WHERE user_id = %s"
                self.db.execute(sql, (login_time, user_id))
            else:
                sql = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s"
                self.db.execute(sql, (user_id,))
            return True
        except Exception as e:
            logger.error(f"Update last login failed: {e}")
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
            sql = "DELETE FROM users WHERE user_id = %s"
            self.db.execute(sql, (user_id,))
            return True
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            return False
    
    def list_users(
        self,
        role: str = None,
        is_active: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询用户列表
        
        Args:
            role: 角色筛选
            is_active: 是否激活筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            用户列表
        """
        conditions = []
        params = []
        
        if role:
            conditions.append("role = %s")
            params.append(role)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT user_id, username, email, role, created_at, last_login, is_active 
            FROM users 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    # ==================== 密码验证 ====================
    
    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证用户密码
        
        Args:
            username: 用户名
            password: 明文密码
            
        Returns:
            验证成功返回用户信息，失败返回None
        """
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not user.get('is_active', True):
            logger.warning(f"User {username} is not active")
            return None
        
        if self._check_password(password, user['password_hash']):
            # 更新最后登录时间
            self.update_last_login(user['user_id'])
            return user
        
        return None
    
    def _hash_password(self, password: str) -> str:
        """
        加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码哈希
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _check_password(self, password: str, password_hash: str) -> bool:
        """
        检查密码是否匹配
        
        Args:
            password: 明文密码
            password_hash: 存储的密码哈希
            
        Returns:
            是否匹配
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password check failed: {e}")
            return False
    
    # ==================== 权限管理 ====================
    
    def get_permissions(self, role: str) -> List[str]:
        """
        获取角色的所有权限
        
        Args:
            role: 角色名称
            
        Returns:
            权限名称列表
        """
        sql = """
            SELECT permission_name FROM role_permissions 
            WHERE role = %s AND is_allowed = TRUE
        """
        results = self.db.query(sql, (role,))
        return [r['permission_name'] for r in results]
    
    def set_permission(self, role: str, permission: str, is_allowed: bool) -> None:
        """
        设置角色权限
        
        Args:
            role: 角色名称
            permission: 权限名称
            is_allowed: 是否允许
        """
        sql = """
            INSERT INTO role_permissions (role, permission_name, is_allowed)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE is_allowed = VALUES(is_allowed)
        """
        self.db.execute(sql, (role, permission, is_allowed))
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """
        检查用户是否有指定权限
        
        Args:
            user_id: 用户ID
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        sql = """
            SELECT rp.is_allowed FROM role_permissions rp
            JOIN users u ON u.role = rp.role
            WHERE u.user_id = %s AND rp.permission_name = %s
        """
        result = self.db.query_one(sql, (user_id, permission))
        return result['is_allowed'] if result else False
    
    def get_all_permissions_for_user(self, user_id: int) -> List[str]:
        """
        获取用户的所有权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限名称列表
        """
        sql = """
            SELECT rp.permission_name FROM role_permissions rp
            JOIN users u ON u.role = rp.role
            WHERE u.user_id = %s AND rp.is_allowed = TRUE
        """
        results = self.db.query(sql, (user_id,))
        return [r['permission_name'] for r in results]
