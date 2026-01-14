"""
数据库配置模块
Database configuration model for classroom behavior detection system
"""
from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class DatabaseConfig:
    """数据库配置类"""
    
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = "123456"
    database: str = "classroom_behavior_db"
    pool_size: int = 5
    pool_recycle: int = 3600
    charset: str = "utf8mb4"
    autocommit: bool = False
    
    # 连接超时设置
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """从环境变量创建配置"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '123456'),
            database=os.getenv('DB_NAME', 'classroom_behavior_db'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '5')),
        )
    
    @property
    def connection_string(self) -> str:
        """获取连接字符串"""
        return f"mysql+mysqlconnector://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
    
    def to_dict(self) -> dict:
        """转换为字典格式（用于mysql.connector）"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'autocommit': self.autocommit,
            'connect_timeout': self.connect_timeout,
        }
    
    def to_pool_config(self) -> dict:
        """转换为连接池配置"""
        return {
            'pool_name': 'classroom_behavior_pool',
            'pool_size': self.pool_size,
            'pool_reset_session': True,
            **self.to_dict()
        }
