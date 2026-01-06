#!/usr/bin/env python
"""
创建测试用户脚本
Create test users for different roles
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager
from src.database.repositories.user_repository import UserRepository

# 测试用户列表
TEST_USERS = [
    {'username': 'teacher001', 'password': '123456', 'email': 'teacher001@example.com', 'role': 'teacher'},
    {'username': 'teacher002', 'password': '123456', 'email': 'teacher002@example.com', 'role': 'teacher'},
    {'username': 'student001', 'password': '123456', 'email': 'student001@example.com', 'role': 'student'},
    {'username': 'student002', 'password': '123456', 'email': 'student002@example.com', 'role': 'student'},
    {'username': 'viewer001', 'password': '123456', 'email': 'viewer001@example.com', 'role': 'viewer'},
]

def main():
    config = DatabaseConfig(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='classroom_behavior_db'
    )
    
    db = DatabaseManager(config)
    user_repo = UserRepository(db)
    
    print("\n" + "=" * 60)
    print("创建测试用户")
    print("=" * 60)
    
    for user_data in TEST_USERS:
        existing = user_repo.get_user_by_username(user_data['username'])
        if existing:
            print(f"[跳过] {user_data['username']} 已存在")
        else:
            user_id = user_repo.create_user(**user_data)
            print(f"[创建] {user_data['username']} (ID: {user_id}, 角色: {user_data['role']})")
    
    print("\n" + "=" * 60)
    print("测试账号列表")
    print("=" * 60)
    print(f"{'用户名':<15} {'密码':<10} {'角色':<10}")
    print("-" * 40)
    print(f"{'admin':<15} {'admin123':<10} {'admin':<10}")
    for user in TEST_USERS:
        print(f"{user['username']:<15} {user['password']:<10} {user['role']:<10}")
    print("=" * 60 + "\n")
    
    db.close()

if __name__ == '__main__':
    main()
