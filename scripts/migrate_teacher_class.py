#!/usr/bin/env python
"""
老师-班级关联数据库迁移脚本
Database migration script for teacher-class relationship
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_teacher_class_table(db: DatabaseManager) -> None:
    """创建老师-班级关联表"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # 老师-班级关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_classes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                teacher_id INT NOT NULL COMMENT '老师用户ID',
                class_id INT NOT NULL COMMENT '班级ID',
                is_head_teacher BOOLEAN DEFAULT FALSE COMMENT '是否班主任',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
                UNIQUE KEY uk_teacher_class (teacher_id, class_id),
                INDEX idx_teacher (teacher_id),
                INDEX idx_class (class_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='老师-班级关联表'
        """)
        logger.info("Created table: teacher_classes")
        
        conn.commit()
        cursor.close()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create teacher_classes table: {e}")
        raise
    finally:
        db.release_connection(conn)


def insert_demo_classes(db: DatabaseManager) -> None:
    """插入演示班级数据"""
    classes = [
        ('计算机2301班', '2023', '计算机学院'),
        ('计算机2302班', '2023', '计算机学院'),
        ('软件2301班', '2023', '软件学院'),
        ('软件2302班', '2023', '软件学院'),
    ]
    
    sql = """
        INSERT IGNORE INTO classes (class_name, grade, department, student_count)
        VALUES (%s, %s, %s, 30)
    """
    
    for cls in classes:
        try:
            db.execute(sql, cls)
        except Exception as e:
            logger.warning(f"Failed to insert class '{cls[0]}': {e}")
    
    logger.info(f"Inserted {len(classes)} demo classes")


def insert_teacher_class_relations(db: DatabaseManager) -> None:
    """插入老师-班级关联数据"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取老师用户
        cursor.execute("SELECT user_id, username FROM users WHERE role = 'teacher'")
        teachers = cursor.fetchall()
        
        # 获取班级
        cursor.execute("SELECT class_id, class_name, department FROM classes")
        classes = cursor.fetchall()
        
        if not teachers or not classes:
            logger.warning("No teachers or classes found")
            return
        
        # 分配班级给老师
        # teacher001 -> 计算机学院的班级
        # teacher002 -> 软件学院的班级
        for teacher in teachers:
            username = teacher['username']
            teacher_id = teacher['user_id']
            
            if username == 'teacher001':
                # 计算机学院
                target_classes = [c for c in classes if '计算机' in c['class_name']]
            elif username == 'teacher002':
                # 软件学院
                target_classes = [c for c in classes if '软件' in c['class_name']]
            else:
                continue
            
            for cls in target_classes:
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO teacher_classes (teacher_id, class_id, is_head_teacher)
                        VALUES (%s, %s, TRUE)
                    """, (teacher_id, cls['class_id']))
                    logger.info(f"Assigned {username} to {cls['class_name']}")
                except Exception as e:
                    logger.warning(f"Failed to assign teacher to class: {e}")
        
        conn.commit()
        cursor.close()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to insert teacher-class relations: {e}")
        raise
    finally:
        db.release_connection(conn)


def main():
    """主函数"""
    logger.info("Starting teacher-class migration...")
    
    try:
        db = DatabaseManager()
        db.init_database()
        
        # 创建关联表
        logger.info("Creating teacher_classes table...")
        create_teacher_class_table(db)
        
        # 插入演示班级
        logger.info("Inserting demo classes...")
        insert_demo_classes(db)
        
        # 插入老师-班级关联
        logger.info("Inserting teacher-class relations...")
        insert_teacher_class_relations(db)
        
        db.close()
        
        print("\n" + "=" * 50)
        print("Teacher-class migration completed!")
        print("=" * 50)
        print("\nTeacher assignments:")
        print("  - teacher001 -> 计算机2301班, 计算机2302班")
        print("  - teacher002 -> 软件2301班, 软件2302班")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
