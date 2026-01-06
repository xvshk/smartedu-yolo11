#!/usr/bin/env python
"""
预警系统数据库迁移脚本
Database migration script for intelligent alert system tables
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


def create_alert_tables(db: DatabaseManager) -> None:
    """创建预警相关数据表"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. 预警表 (alerts) - 存储所有生成的预警
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id INT PRIMARY KEY AUTO_INCREMENT,
                session_id INT NOT NULL,
                alert_level INT NOT NULL DEFAULT 0 COMMENT '0:正常 1:轻度 2:中度 3:严重',
                alert_type VARCHAR(50) NOT NULL COMMENT 'rule_based/ml_predicted/anomaly_detected',
                behavior_type VARCHAR(50) NOT NULL,
                behavior_count INT DEFAULT 1,
                confidence FLOAT,
                location_info JSON COMMENT 'bbox信息',
                triggered_rules JSON COMMENT '触发的规则ID列表',
                risk_score FLOAT COMMENT 'ML风险分数',
                anomaly_score FLOAT COMMENT '异常分数',
                suggestions JSON COMMENT '干预建议列表',
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES detection_sessions(session_id) ON DELETE CASCADE,
                INDEX idx_session (session_id),
                INDEX idx_level (alert_level),
                INDEX idx_type (alert_type),
                INDEX idx_behavior (behavior_type),
                INDEX idx_created (created_at),
                INDEX idx_unread (is_read, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='预警记录表'
        """)
        logger.info("Created table: alerts")
        
        # 2. 更新预警规则表 (alert_rules) - 扩展现有表
        # 先检查表是否存在，如果存在则添加新字段
        cursor.execute("SHOW TABLES LIKE 'alert_rules'")
        if cursor.fetchone():
            # 检查是否需要添加新字段
            cursor.execute("SHOW COLUMNS FROM alert_rules LIKE 'rule_type'")
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE alert_rules
                    ADD COLUMN rule_type VARCHAR(50) DEFAULT 'frequency' 
                        COMMENT 'frequency/duration/combination/threshold' AFTER rule_name,
                    ADD COLUMN description TEXT AFTER rule_type,
                    ADD COLUMN conditions JSON COMMENT '规则条件配置' AFTER description,
                    ADD COLUMN created_by INT AFTER is_active,
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                        ON UPDATE CURRENT_TIMESTAMP AFTER created_at,
                    ADD FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
                """)
                logger.info("Updated table: alert_rules with new columns")
        else:
            # 创建新的预警规则表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    rule_type VARCHAR(50) NOT NULL DEFAULT 'frequency' 
                        COMMENT 'frequency/duration/combination/threshold',
                    description TEXT,
                    conditions JSON NOT NULL COMMENT '规则条件配置',
                    alert_level INT NOT NULL DEFAULT 1,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
                    INDEX idx_active (is_active),
                    INDEX idx_type (rule_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='预警规则表'
            """)
            logger.info("Created table: alert_rules (new version)")
        
        # 3. 干预记录表 (interventions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interventions (
                intervention_id INT PRIMARY KEY AUTO_INCREMENT,
                alert_id INT NOT NULL,
                action_taken VARCHAR(255) NOT NULL COMMENT '采取的干预措施',
                outcome TEXT COMMENT '干预结果描述',
                effectiveness_rating INT COMMENT '有效性评分 1-5',
                recorded_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts(alert_id) ON DELETE CASCADE,
                FOREIGN KEY (recorded_by) REFERENCES users(user_id) ON DELETE SET NULL,
                INDEX idx_alert (alert_id),
                INDEX idx_effectiveness (effectiveness_rating)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='干预记录表'
        """)
        logger.info("Created table: interventions")
        
        # 4. 用户通知偏好表 (notification_preferences)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                preference_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL UNIQUE,
                alert_level_0 BOOLEAN DEFAULT FALSE COMMENT '正常级别通知',
                alert_level_1 BOOLEAN DEFAULT TRUE COMMENT '轻度预警通知',
                alert_level_2 BOOLEAN DEFAULT TRUE COMMENT '中度预警通知',
                alert_level_3 BOOLEAN DEFAULT TRUE COMMENT '严重预警通知',
                sound_enabled BOOLEAN DEFAULT TRUE COMMENT '声音提醒',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='用户通知偏好表'
        """)
        logger.info("Created table: notification_preferences")
        
        conn.commit()
        cursor.close()
        logger.info("All alert tables created successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create alert tables: {e}")
        raise
    finally:
        db.release_connection(conn)


def create_ml_tables(db: DatabaseManager) -> None:
    """创建机器学习相关数据表"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. 机器学习模型表 (ml_models)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_models (
                model_id INT PRIMARY KEY AUTO_INCREMENT,
                model_type VARCHAR(50) NOT NULL COMMENT 'risk_predictor/anomaly_detector',
                version VARCHAR(20) NOT NULL,
                training_date TIMESTAMP,
                training_samples INT COMMENT '训练样本数',
                metrics JSON COMMENT '性能指标 {accuracy, precision, recall, f1}',
                model_path VARCHAR(255) COMMENT '模型文件路径',
                mlflow_run_id VARCHAR(100) COMMENT 'MLflow运行ID',
                mlflow_model_uri VARCHAR(255) COMMENT 'MLflow模型URI',
                is_active BOOLEAN DEFAULT FALSE COMMENT '是否为当前活跃模型',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_type_active (model_type, is_active),
                INDEX idx_mlflow_run (mlflow_run_id),
                INDEX idx_version (model_type, version)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='机器学习模型表'
        """)
        logger.info("Created table: ml_models")
        
        # 2. MLflow实验记录表 (mlflow_experiments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mlflow_experiments (
                experiment_id VARCHAR(100) PRIMARY KEY,
                experiment_name VARCHAR(255) NOT NULL,
                artifact_location VARCHAR(500),
                lifecycle_stage VARCHAR(50) DEFAULT 'active',
                tags JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (experiment_name),
                INDEX idx_stage (lifecycle_stage)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='MLflow实验记录表'
        """)
        logger.info("Created table: mlflow_experiments")
        
        # 3. MLflow运行记录表 (mlflow_runs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mlflow_runs (
                run_id VARCHAR(100) PRIMARY KEY,
                run_name VARCHAR(255),
                experiment_id VARCHAR(100),
                status VARCHAR(50) DEFAULT 'RUNNING' COMMENT 'RUNNING/FINISHED/FAILED/KILLED',
                start_time TIMESTAMP,
                end_time TIMESTAMP NULL,
                params JSON COMMENT '模型参数',
                metrics JSON COMMENT '性能指标',
                tags JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES mlflow_experiments(experiment_id) ON DELETE CASCADE,
                INDEX idx_experiment (experiment_id),
                INDEX idx_status (status),
                INDEX idx_start_time (start_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='MLflow运行记录表'
        """)
        logger.info("Created table: mlflow_runs")
        
        conn.commit()
        cursor.close()
        logger.info("All ML tables created successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create ML tables: {e}")
        raise
    finally:
        db.release_connection(conn)


def insert_default_rules(db: DatabaseManager) -> None:
    """插入默认预警规则"""
    default_rules = [
        {
            'rule_name': '睡觉行为预警',
            'rule_type': 'frequency',
            'description': '检测到睡觉行为时触发预警',
            'behavior_type': 'sleep',
            'class_id': 3,
            'threshold_count': 1,
            'time_window_seconds': 60,
            'conditions': '{"behavior_type": "sleep", "threshold": 1, "time_window": 60, "min_confidence": 0.5}',
            'alert_level': 3
        },
        {
            'rule_name': '使用电子设备预警',
            'rule_type': 'frequency',
            'description': '检测到使用电子设备时触发预警',
            'behavior_type': 'using_electronic_devices',
            'class_id': 5,
            'threshold_count': 1,
            'time_window_seconds': 60,
            'conditions': '{"behavior_type": "using_electronic_devices", "threshold": 1, "time_window": 60, "min_confidence": 0.5}',
            'alert_level': 3
        },
        {
            'rule_name': '交谈行为预警',
            'rule_type': 'frequency',
            'description': '检测到多次交谈行为时触发预警',
            'behavior_type': 'talk',
            'class_id': 6,
            'threshold_count': 3,
            'time_window_seconds': 120,
            'conditions': '{"behavior_type": "talk", "threshold": 3, "time_window": 120, "min_confidence": 0.5}',
            'alert_level': 2
        },
        {
            'rule_name': '低头行为预警',
            'rule_type': 'duration',
            'description': '持续低头超过一定时间触发预警',
            'behavior_type': 'head_down',
            'class_id': 7,
            'threshold_count': 1,
            'time_window_seconds': 300,
            'conditions': '{"behavior_type": "head_down", "duration": 300, "min_confidence": 0.5}',
            'alert_level': 1
        },
        {
            'rule_name': '站立行为预警',
            'rule_type': 'frequency',
            'description': '检测到站立行为时触发轻度预警',
            'behavior_type': 'stand',
            'class_id': 4,
            'threshold_count': 1,
            'time_window_seconds': 60,
            'conditions': '{"behavior_type": "stand", "threshold": 1, "time_window": 60, "min_confidence": 0.5}',
            'alert_level': 1
        },
    ]
    
    sql = """
        INSERT IGNORE INTO alert_rules 
        (rule_name, rule_type, description, behavior_type, class_id, threshold_count, 
         time_window_seconds, conditions, alert_level, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
    """
    
    for rule in default_rules:
        try:
            db.execute(sql, (
                rule['rule_name'],
                rule['rule_type'],
                rule['description'],
                rule['behavior_type'],
                rule['class_id'],
                rule['threshold_count'],
                rule['time_window_seconds'],
                rule['conditions'],
                rule['alert_level']
            ))
        except Exception as e:
            logger.warning(f"Failed to insert rule '{rule['rule_name']}': {e}")
    
    logger.info(f"Inserted {len(default_rules)} default alert rules")


def main():
    """主函数"""
    logger.info("Starting alert system database migration...")
    
    try:
        # 使用默认配置连接数据库
        db = DatabaseManager()
        
        # 确保基础表已创建
        db.init_database()
        
        # 创建预警相关表
        logger.info("Creating alert tables...")
        create_alert_tables(db)
        
        # 创建机器学习相关表
        logger.info("Creating ML tables...")
        create_ml_tables(db)
        
        # 插入默认规则
        logger.info("Inserting default alert rules...")
        insert_default_rules(db)
        
        db.close()
        
        print("\n" + "=" * 50)
        print("Alert system database migration completed!")
        print("=" * 50)
        print("\nNew tables created:")
        print("  - alerts (预警记录表)")
        print("  - alert_rules (预警规则表 - 已更新)")
        print("  - interventions (干预记录表)")
        print("  - notification_preferences (通知偏好表)")
        print("  - ml_models (机器学习模型表)")
        print("  - mlflow_experiments (MLflow实验表)")
        print("  - mlflow_runs (MLflow运行表)")
        print("\nDefault alert rules inserted.")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
