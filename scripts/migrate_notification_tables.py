#!/usr/bin/env python
"""
预警通知和学生反馈数据库迁移脚本
Database migration script for alert notifications and student feedback
"""
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_notification_tables(db: DatabaseManager) -> None:
    """创建通知和反馈相关数据表"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. 预警通知表 (alert_notifications) - 老师/管理员发送给学生的通知
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_notifications (
                notification_id INT PRIMARY KEY AUTO_INCREMENT,
                alert_id INT COMMENT '关联的预警ID，可为空表示一般通知',
                sender_id INT NOT NULL COMMENT '发送者ID（老师/管理员）',
                receiver_id INT NOT NULL COMMENT '接收者ID（学生）',
                title VARCHAR(200) NOT NULL COMMENT '通知标题',
                content TEXT NOT NULL COMMENT '通知内容',
                notification_type ENUM('warning', 'reminder', 'suggestion', 'praise') 
                    DEFAULT 'warning' COMMENT '通知类型',
                priority ENUM('low', 'normal', 'high', 'urgent') 
                    DEFAULT 'normal' COMMENT '优先级',
                is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
                read_at TIMESTAMP NULL COMMENT '阅读时间',
                requires_feedback BOOLEAN DEFAULT TRUE COMMENT '是否需要反馈',
                feedback_deadline TIMESTAMP NULL COMMENT '反馈截止时间',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts(alert_id) ON DELETE SET NULL,
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_receiver (receiver_id),
                INDEX idx_sender (sender_id),
                INDEX idx_alert (alert_id),
                INDEX idx_unread (receiver_id, is_read),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='预警通知表'
        """)
        logger.info("Created table: alert_notifications")
        
        # 2. 学生反馈表 (student_feedbacks) - 学生对通知的反馈
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_feedbacks (
                feedback_id INT PRIMARY KEY AUTO_INCREMENT,
                notification_id INT NOT NULL COMMENT '关联的通知ID',
                student_id INT NOT NULL COMMENT '学生ID',
                feedback_type ENUM('acknowledge', 'explain', 'appeal', 'commit') 
                    NOT NULL COMMENT '反馈类型：确认/解释/申诉/承诺改进',
                content TEXT NOT NULL COMMENT '反馈内容',
                attachment_url VARCHAR(500) COMMENT '附件URL（如证明材料）',
                status ENUM('pending', 'reviewed', 'accepted', 'rejected') 
                    DEFAULT 'pending' COMMENT '反馈状态',
                reviewer_id INT COMMENT '审核人ID',
                reviewer_comment TEXT COMMENT '审核意见',
                reviewed_at TIMESTAMP NULL COMMENT '审核时间',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (notification_id) REFERENCES alert_notifications(notification_id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (reviewer_id) REFERENCES users(user_id) ON DELETE SET NULL,
                INDEX idx_notification (notification_id),
                INDEX idx_student (student_id),
                INDEX idx_status (status),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='学生反馈表'
        """)
        logger.info("Created table: student_feedbacks")
        
        # 3. 通知模板表 (notification_templates) - 预设的通知模板
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_templates (
                template_id INT PRIMARY KEY AUTO_INCREMENT,
                template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
                behavior_type VARCHAR(50) COMMENT '关联的行为类型',
                title_template VARCHAR(200) NOT NULL COMMENT '标题模板',
                content_template TEXT NOT NULL COMMENT '内容模板',
                notification_type ENUM('warning', 'reminder', 'suggestion', 'praise') 
                    DEFAULT 'warning',
                is_active BOOLEAN DEFAULT TRUE,
                created_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
                INDEX idx_behavior (behavior_type),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='通知模板表'
        """)
        logger.info("Created table: notification_templates")
        
        conn.commit()
        cursor.close()
        logger.info("All notification tables created successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create notification tables: {e}")
        raise
    finally:
        db.release_connection(conn)


def insert_default_templates(db: DatabaseManager) -> None:
    """插入默认通知模板"""
    default_templates = [
        {
            'template_name': '睡觉行为提醒',
            'behavior_type': '睡觉',
            'title_template': '课堂行为提醒 - 睡觉',
            'content_template': '同学你好，系统检测到你在课堂上有睡觉行为。请注意保持良好的学习状态，如有特殊情况请及时反馈说明。',
            'notification_type': 'warning'
        },
        {
            'template_name': '使用电子设备提醒',
            'behavior_type': '使用电子设备',
            'title_template': '课堂行为提醒 - 使用电子设备',
            'content_template': '同学你好，系统检测到你在课堂上使用电子设备。请遵守课堂纪律，如有学习需要请提前告知老师。',
            'notification_type': 'warning'
        },
        {
            'template_name': '交谈行为提醒',
            'behavior_type': '交谈',
            'title_template': '课堂行为提醒 - 交谈',
            'content_template': '同学你好，系统检测到你在课堂上有频繁交谈行为。请保持课堂安静，有问题可以举手提问。',
            'notification_type': 'reminder'
        },
        {
            'template_name': '低头行为提醒',
            'behavior_type': '低头',
            'title_template': '课堂行为提醒 - 注意力',
            'content_template': '同学你好，系统检测到你在课堂上长时间低头。请注意听讲，保持良好的学习姿态。',
            'notification_type': 'reminder'
        },
        {
            'template_name': '积极表现表扬',
            'behavior_type': '举手',
            'title_template': '课堂表现表扬',
            'content_template': '同学你好，老师注意到你在课堂上积极举手发言，表现非常好！请继续保持这种学习态度。',
            'notification_type': 'praise'
        },
        {
            'template_name': '学习建议',
            'behavior_type': None,
            'title_template': '学习建议',
            'content_template': '同学你好，根据你近期的课堂表现，老师有一些学习建议想和你分享。希望能帮助你更好地学习。',
            'notification_type': 'suggestion'
        },
    ]
    
    sql = """
        INSERT IGNORE INTO notification_templates 
        (template_name, behavior_type, title_template, content_template, notification_type, is_active)
        VALUES (%s, %s, %s, %s, %s, TRUE)
    """
    
    for template in default_templates:
        try:
            db.execute(sql, (
                template['template_name'],
                template['behavior_type'],
                template['title_template'],
                template['content_template'],
                template['notification_type']
            ))
        except Exception as e:
            logger.warning(f"Failed to insert template '{template['template_name']}': {e}")
    
    logger.info(f"Inserted {len(default_templates)} default notification templates")


def main():
    """主函数"""
    logger.info("Starting notification system database migration...")
    
    try:
        # 使用默认配置连接数据库
        db = DatabaseManager()
        
        # 确保基础表已创建
        db.init_database()
        
        # 创建通知相关表
        logger.info("Creating notification tables...")
        create_notification_tables(db)
        
        # 插入默认模板
        logger.info("Inserting default notification templates...")
        insert_default_templates(db)
        
        db.close()
        
        print("\n" + "=" * 50)
        print("Notification system database migration completed!")
        print("=" * 50)
        print("\nNew tables created:")
        print("  - alert_notifications (预警通知表)")
        print("  - student_feedbacks (学生反馈表)")
        print("  - notification_templates (通知模板表)")
        print("\nDefault notification templates inserted.")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
