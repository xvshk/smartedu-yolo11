#!/usr/bin/env python
"""
生成预警测试数据脚本
Generate test alert data for the intelligent alert system
"""
import logging
import sys
import os
import random
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.manager import DatabaseManager
from src.database.repositories.alert_repository import AlertRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 行为类型配置
BEHAVIOR_TYPES = [
    {'type': '睡觉', 'level': 3, 'suggestions': ['轻声提醒学生', '课后单独谈话', '关注学生作息']},
    {'type': '使用电子设备', 'level': 3, 'suggestions': ['提醒学生收起设备', '课后没收设备', '通知家长']},
    {'type': '交谈', 'level': 2, 'suggestions': ['眼神提醒', '点名提问', '调整座位']},
    {'type': '低头', 'level': 1, 'suggestions': ['提问互动', '走近观察', '课堂活动调动']},
    {'type': '站立', 'level': 1, 'suggestions': ['询问原因', '允许短暂活动', '关注学生状态']},
]


def get_or_create_session(db: DatabaseManager) -> int:
    """获取或创建一个检测会话"""
    # 先查找现有会话
    sql = "SELECT session_id FROM detection_sessions ORDER BY session_id DESC LIMIT 1"
    result = db.query_one(sql)
    
    if result:
        return result['session_id']
    
    # 创建新会话
    sql = """
        INSERT INTO detection_sessions (user_id, source_type, status, total_frames, processed_frames)
        VALUES (1, 'image', 'completed', 100, 100)
    """
    return db.insert_and_get_id(sql)


def generate_alerts(db: DatabaseManager, count: int = 50) -> int:
    """生成测试预警数据"""
    repo = AlertRepository(db)
    session_id = get_or_create_session(db)
    
    alerts = []
    now = datetime.now()
    
    for i in range(count):
        # 随机选择行为类型
        behavior = random.choice(BEHAVIOR_TYPES)
        
        # 随机生成时间（过去7天内）
        random_hours = random.randint(0, 168)  # 7天 = 168小时
        created_at = now - timedelta(hours=random_hours)
        
        # 随机生成置信度
        confidence = random.uniform(0.5, 0.98)
        
        # 随机决定是否已读
        is_read = random.random() < 0.3  # 30%已读
        
        alert = {
            'session_id': session_id,
            'alert_level': behavior['level'],
            'alert_type': random.choice(['rule_based', 'ml_predicted', 'anomaly_detected']),
            'behavior_type': behavior['type'],
            'behavior_count': random.randint(1, 5),
            'confidence': confidence,
            'location_info': {
                'x': random.randint(100, 800),
                'y': random.randint(100, 600),
                'width': random.randint(50, 150),
                'height': random.randint(50, 150)
            },
            'triggered_rules': [random.randint(1, 5)],
            'risk_score': random.uniform(0.3, 0.9),
            'anomaly_score': random.uniform(0.1, 0.8),
            'suggestions': behavior['suggestions']
        }
        alerts.append(alert)
    
    # 批量插入
    inserted = repo.create_alerts_batch(alerts)
    
    # 更新部分为已读
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        # 随机标记30%为已读
        cursor.execute("""
            UPDATE alerts 
            SET is_read = TRUE 
            WHERE alert_id IN (
                SELECT alert_id FROM (
                    SELECT alert_id FROM alerts ORDER BY RAND() LIMIT %s
                ) AS tmp
            )
        """, (int(count * 0.3),))
        conn.commit()
        cursor.close()
    finally:
        db.release_connection(conn)
    
    return inserted


def main():
    """主函数"""
    logger.info("Starting alert data generation...")
    
    try:
        db = DatabaseManager()
        
        # 先运行迁移确保表存在
        logger.info("Ensuring alert tables exist...")
        from scripts.migrate_alert_tables import create_alert_tables, insert_default_rules
        create_alert_tables(db)
        insert_default_rules(db)
        
        # 生成预警数据
        count = 50
        logger.info(f"Generating {count} test alerts...")
        inserted = generate_alerts(db, count)
        
        db.close()
        
        print("\n" + "=" * 50)
        print("Alert data generation completed!")
        print("=" * 50)
        print(f"\nGenerated {inserted} test alerts")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
