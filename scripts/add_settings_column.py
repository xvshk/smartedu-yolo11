#!/usr/bin/env python
"""
添加 settings 列到 users 表
Add settings column to users table
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager

def main():
    config = DatabaseConfig(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='classroom_behavior_db'
    )
    
    db = DatabaseManager(config)
    
    try:
        # 检查列是否存在
        result = db.query("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'classroom_behavior_db' 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'settings'
        """)
        
        if result:
            print("Settings column already exists")
        else:
            db.execute("ALTER TABLE users ADD COLUMN settings TEXT")
            print("Settings column added successfully")
            
        # 同时添加 created_at 列到 detection_records 如果不存在
        result2 = db.query("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'classroom_behavior_db' 
            AND TABLE_NAME = 'detection_records' 
            AND COLUMN_NAME = 'created_at'
        """)
        
        if not result2:
            db.execute("ALTER TABLE detection_records ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("created_at column added to detection_records")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    main()
