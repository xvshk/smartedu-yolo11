"""
为学生创建系统用户账户
Create system user accounts for students
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.student_repository import StudentRepository

# 数据库配置
DB_CONFIG = DatabaseConfig(
    host='localhost',
    port=3306,
    user='root',
    password='123456',
    database='classroom_behavior_db'
)


def main():
    """为学生创建用户账户"""
    print("=" * 50)
    print("为学生创建系统用户账户...")
    print("=" * 50)
    
    db = DatabaseManager(DB_CONFIG)
    
    try:
        student_repo = StudentRepository(db)
        user_repo = UserRepository(db)
        
        # 获取所有学生
        students = student_repo.list_students(limit=500)
        print(f"\n找到 {len(students)} 名学生")
        
        created = 0
        skipped = 0
        
        for student in students:
            student_number = student['student_number']
            name = student['name']
            student_id = student['student_id']
            
            # 检查用户是否已存在
            existing = user_repo.get_user_by_username(student_number)
            if existing:
                skipped += 1
                continue
            
            # 创建用户账户
            # 用户名: 学号, 密码: 123456, 角色: student
            user_id = user_repo.create_user(
                username=student_number,
                password='123456',
                email=f'{student_number}@example.com',
                role='student'
            )
            
            # 更新用户表，关联学生ID（如果有这个字段的话）
            # 这里简化处理，在JWT中可以通过用户名查找学生
            
            created += 1
            print(f"  创建用户: {student_number} ({name})")
        
        print(f"\n创建了 {created} 个用户账户")
        print(f"跳过了 {skipped} 个已存在的用户")
        print("\n学生登录信息:")
        print("  用户名: 学号 (如 202401001)")
        print("  密码: 123456")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
