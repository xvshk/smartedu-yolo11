#!/usr/bin/env python
"""
数据库初始化脚本
Database initialization script for classroom behavior detection system
"""
import argparse
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager
from src.database.repositories.user_repository import UserRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Initialize classroom behavior detection database'
    )
    parser.add_argument(
        '--host', type=str, default='localhost',
        help='Database host (default: localhost)'
    )
    parser.add_argument(
        '--port', type=int, default=3306,
        help='Database port (default: 3306)'
    )
    parser.add_argument(
        '--user', type=str, default='root',
        help='Database user (default: root)'
    )
    parser.add_argument(
        '--password', type=str, default='123456',
        help='Database password (default: 123456)'
    )
    parser.add_argument(
        '--database', type=str, default='classroom_behavior_db',
        help='Database name (default: classroom_behavior_db)'
    )
    parser.add_argument(
        '--admin-username', type=str, default='admin',
        help='Admin username (default: admin)'
    )
    parser.add_argument(
        '--admin-password', type=str, default='admin123',
        help='Admin password (default: admin123)'
    )
    parser.add_argument(
        '--admin-email', type=str, default='admin@example.com',
        help='Admin email (default: admin@example.com)'
    )
    parser.add_argument(
        '--skip-admin', action='store_true',
        help='Skip creating admin user'
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 创建数据库配置
    config = DatabaseConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    logger.info(f"Connecting to MySQL at {config.host}:{config.port}")
    logger.info(f"Database: {config.database}")
    
    try:
        # 初始化数据库
        db = DatabaseManager(config)
        db.init_database()
        logger.info("Database tables created successfully")
        
        # 创建管理员用户
        if not args.skip_admin:
            user_repo = UserRepository(db)
            
            # 检查管理员是否已存在
            existing_admin = user_repo.get_user_by_username(args.admin_username)
            if existing_admin:
                logger.info(f"Admin user '{args.admin_username}' already exists")
            else:
                user_id = user_repo.create_user(
                    username=args.admin_username,
                    password=args.admin_password,
                    email=args.admin_email,
                    role='admin'
                )
                logger.info(f"Created admin user '{args.admin_username}' with ID: {user_id}")
        
        # 显示数据库信息
        print("\n" + "=" * 50)
        print("Database initialization completed!")
        print("=" * 50)
        print(f"\nConnection Info:")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Database: {config.database}")
        print(f"  User: {config.user}")
        
        if not args.skip_admin:
            print(f"\nAdmin Account:")
            print(f"  Username: {args.admin_username}")
            print(f"  Password: {args.admin_password}")
            print(f"  Email: {args.admin_email}")
        
        print("\nTables created:")
        tables = [
            'users', 'role_permissions', 'classes', 'students',
            'courses', 'schedules', 'detection_sessions',
            'detection_records', 'behavior_entries', 'alert_rules',
            'alert_events', 'daily_summaries', 'course_summaries',
            'class_summaries'
        ]
        for table in tables:
            print(f"  - {table}")
        
        print("\n" + "=" * 50)
        
        db.close()
        return 0
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
