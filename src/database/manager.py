"""
数据库管理器模块
Database manager module with connection pooling and transaction support
"""
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Generator
import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from .config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, config: DatabaseConfig = None):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置，如果为None则使用默认配置
        """
        self.config = config or DatabaseConfig()
        self._pool: Optional[pooling.MySQLConnectionPool] = None
        self._initialized = False
    
    def _create_pool(self) -> None:
        """创建连接池"""
        if self._pool is not None:
            return
        
        try:
            # 首先尝试不指定数据库连接，用于创建数据库
            pool_config = self.config.to_pool_config()
            pool_config.pop('database', None)
            
            temp_pool = pooling.MySQLConnectionPool(**pool_config)
            conn = temp_pool.get_connection()
            cursor = conn.cursor()
            
            # 创建数据库（如果不存在）
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self.config.database}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.close()
            conn.close()
            
            # 创建带数据库的连接池
            self._pool = pooling.MySQLConnectionPool(
                **self.config.to_pool_config()
            )
            logger.info(f"Database connection pool created: {self.config.database}")
            
        except MySQLError as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    
    def get_connection(self) -> mysql.connector.MySQLConnection:
        """
        从连接池获取连接
        
        Returns:
            MySQL连接对象
        """
        if self._pool is None:
            self._create_pool()
        
        try:
            conn = self._pool.get_connection()
            return conn
        except MySQLError as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise
    
    def release_connection(self, conn: mysql.connector.MySQLConnection) -> None:
        """
        释放连接回连接池
        
        Args:
            conn: 要释放的连接
        """
        if conn and conn.is_connected():
            try:
                conn.close()
            except MySQLError as e:
                logger.warning(f"Error releasing connection: {e}")
    
    def execute(self, sql: str, params: Tuple = None) -> int:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            影响的行数
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        except MySQLError as e:
            conn.rollback()
            logger.error(f"Execute failed: {e}, SQL: {sql}")
            raise
        finally:
            self.release_connection(conn)
    
    def query(self, sql: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询
        
        Args:
            sql: SQL查询语句
            params: 参数元组
            
        Returns:
            查询结果列表，每行为字典
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except MySQLError as e:
            logger.error(f"Query failed: {e}, SQL: {sql}")
            raise
        finally:
            self.release_connection(conn)
    
    def query_one(self, sql: str, params: Tuple = None) -> Optional[Dict[str, Any]]:
        """
        执行查询并返回单条结果
        
        Args:
            sql: SQL查询语句
            params: 参数元组
            
        Returns:
            单条查询结果或None
        """
        results = self.query(sql, params)
        return results[0] if results else None
    
    def execute_many(self, sql: str, params_list: List[Tuple]) -> int:
        """
        批量执行SQL语句
        
        Args:
            sql: SQL语句
            params_list: 参数列表
            
        Returns:
            影响的总行数
        """
        if not params_list:
            return 0
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        except MySQLError as e:
            conn.rollback()
            logger.error(f"Execute many failed: {e}, SQL: {sql}")
            raise
        finally:
            self.release_connection(conn)
    
    def insert_and_get_id(self, sql: str, params: Tuple = None) -> int:
        """
        执行插入并返回自增ID
        
        Args:
            sql: INSERT语句
            params: 参数元组
            
        Returns:
            插入记录的自增ID
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        except MySQLError as e:
            conn.rollback()
            logger.error(f"Insert failed: {e}, SQL: {sql}")
            raise
        finally:
            self.release_connection(conn)
    
    @contextmanager
    def transaction(self) -> Generator[mysql.connector.MySQLConnection, None, None]:
        """
        事务上下文管理器
        
        Usage:
            with db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
                cursor.execute(...)
            # 自动提交或回滚
        """
        conn = self.get_connection()
        try:
            conn.start_transaction()
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            self.release_connection(conn)

    
    def init_database(self) -> None:
        """初始化数据库表结构"""
        if self._initialized:
            return
        
        if self._pool is None:
            self._create_pool()
        
        # 创建所有表
        self._create_tables()
        # 插入默认权限配置
        self._init_default_permissions()
        
        self._initialized = True
        logger.info("Database initialized successfully")
    
    def _create_tables(self) -> None:
        """创建所有数据库表"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    role ENUM('admin', 'teacher', 'student', 'viewer') DEFAULT 'viewer',
                    settings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_role (role),
                    INDEX idx_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 角色权限表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    role ENUM('admin', 'teacher', 'student', 'viewer') NOT NULL,
                    permission_name VARCHAR(50) NOT NULL,
                    is_allowed BOOLEAN DEFAULT TRUE,
                    UNIQUE KEY uk_role_permission (role, permission_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 班级表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    class_id INT PRIMARY KEY AUTO_INCREMENT,
                    class_name VARCHAR(100) NOT NULL,
                    grade VARCHAR(20),
                    department VARCHAR(100),
                    student_count INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_department (department)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 学生表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INT PRIMARY KEY AUTO_INCREMENT,
                    student_number VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    class_id INT,
                    gender ENUM('male', 'female', 'other'),
                    enrollment_year INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE SET NULL,
                    INDEX idx_class (class_id),
                    INDEX idx_student_number (student_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 课程表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    course_id INT PRIMARY KEY AUTO_INCREMENT,
                    course_name VARCHAR(200) NOT NULL,
                    course_code VARCHAR(50),
                    teacher_id INT,
                    semester VARCHAR(20),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE SET NULL,
                    INDEX idx_teacher (teacher_id),
                    INDEX idx_semester (semester)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 课堂安排表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    schedule_id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT NOT NULL,
                    class_id INT NOT NULL,
                    classroom VARCHAR(100),
                    weekday TINYINT,
                    start_time TIME,
                    end_time TIME,
                    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
                    INDEX idx_course (course_id),
                    INDEX idx_class (class_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 检测会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_sessions (
                    session_id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT,
                    schedule_id INT,
                    source_type ENUM('image', 'video', 'stream') NOT NULL,
                    source_path VARCHAR(500),
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP NULL,
                    total_frames INT DEFAULT 0,
                    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                    FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id) ON DELETE SET NULL,
                    INDEX idx_user (user_id),
                    INDEX idx_schedule (schedule_id),
                    INDEX idx_start_time (start_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 检测记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_records (
                    record_id INT PRIMARY KEY AUTO_INCREMENT,
                    session_id INT NOT NULL,
                    frame_id INT NOT NULL,
                    timestamp DOUBLE NOT NULL,
                    alert_triggered BOOLEAN DEFAULT FALSE,
                    detection_count INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES detection_sessions(session_id) ON DELETE CASCADE,
                    INDEX idx_session (session_id),
                    INDEX idx_frame (session_id, frame_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 行为条目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS behavior_entries (
                    entry_id INT PRIMARY KEY AUTO_INCREMENT,
                    record_id INT NOT NULL,
                    bbox_x1 FLOAT NOT NULL,
                    bbox_y1 FLOAT NOT NULL,
                    bbox_x2 FLOAT NOT NULL,
                    bbox_y2 FLOAT NOT NULL,
                    class_id TINYINT NOT NULL,
                    class_name VARCHAR(50) NOT NULL,
                    confidence FLOAT NOT NULL,
                    behavior_type ENUM('normal', 'warning') NOT NULL,
                    alert_level TINYINT DEFAULT 0,
                    FOREIGN KEY (record_id) REFERENCES detection_records(record_id) ON DELETE CASCADE,
                    INDEX idx_record (record_id),
                    INDEX idx_behavior (behavior_type, alert_level),
                    INDEX idx_class (class_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 预警规则表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id INT PRIMARY KEY AUTO_INCREMENT,
                    rule_name VARCHAR(100) NOT NULL,
                    behavior_type VARCHAR(50),
                    class_id TINYINT,
                    threshold_count INT NOT NULL,
                    time_window_seconds INT NOT NULL,
                    alert_level TINYINT DEFAULT 1,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 预警事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_events (
                    event_id INT PRIMARY KEY AUTO_INCREMENT,
                    rule_id INT NOT NULL,
                    session_id INT NOT NULL,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    behavior_count INT NOT NULL,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP NULL,
                    FOREIGN KEY (rule_id) REFERENCES alert_rules(rule_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES detection_sessions(session_id) ON DELETE CASCADE,
                    INDEX idx_session (session_id),
                    INDEX idx_triggered (triggered_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 每日汇总表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    summary_date DATE UNIQUE NOT NULL,
                    total_sessions INT DEFAULT 0,
                    total_detections INT DEFAULT 0,
                    behavior_distribution JSON,
                    alert_distribution JSON,
                    avg_attention_rate FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_date (summary_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 课程汇总表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS course_summaries (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT NOT NULL,
                    period VARCHAR(20) NOT NULL,
                    period_start DATE,
                    period_end DATE,
                    total_sessions INT DEFAULT 0,
                    avg_attention_rate FLOAT,
                    behavior_trends JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
                    UNIQUE KEY uk_course_period (course_id, period, period_start),
                    INDEX idx_course (course_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 班级汇总表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS class_summaries (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    class_id INT NOT NULL,
                    period VARCHAR(20) NOT NULL,
                    period_start DATE,
                    period_end DATE,
                    total_sessions INT DEFAULT 0,
                    avg_attention_rate FLOAT,
                    top_warning_behaviors JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
                    UNIQUE KEY uk_class_period (class_id, period, period_start),
                    INDEX idx_class (class_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            conn.commit()
            cursor.close()
            logger.info("All tables created successfully")
            
        except MySQLError as e:
            conn.rollback()
            logger.error(f"Failed to create tables: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def _init_default_permissions(self) -> None:
        """初始化默认权限配置"""
        permissions = [
            # Admin权限
            ('admin', 'view_sessions', True),
            ('admin', 'create_session', True),
            ('admin', 'delete_session', True),
            ('admin', 'view_statistics', True),
            ('admin', 'manage_users', True),
            ('admin', 'export_data', True),
            # Teacher权限
            ('teacher', 'view_sessions', True),
            ('teacher', 'create_session', True),
            ('teacher', 'delete_session', False),
            ('teacher', 'view_statistics', True),
            ('teacher', 'manage_users', False),
            ('teacher', 'export_data', True),
            # Student权限
            ('student', 'view_sessions', True),
            ('student', 'create_session', False),
            ('student', 'delete_session', False),
            ('student', 'view_statistics', True),
            ('student', 'manage_users', False),
            ('student', 'export_data', False),
            # Viewer权限
            ('viewer', 'view_sessions', True),
            ('viewer', 'create_session', False),
            ('viewer', 'delete_session', False),
            ('viewer', 'view_statistics', False),
            ('viewer', 'manage_users', False),
            ('viewer', 'export_data', False),
        ]
        
        sql = """
            INSERT IGNORE INTO role_permissions (role, permission_name, is_allowed)
            VALUES (%s, %s, %s)
        """
        self.execute_many(sql, permissions)
        logger.info("Default permissions initialized")
    
    def close(self) -> None:
        """关闭所有连接"""
        if self._pool:
            # MySQL Connector的连接池没有显式的close方法
            # 连接会在垃圾回收时自动关闭
            self._pool = None
            self._initialized = False
            logger.info("Database connection pool closed")
    
    def __enter__(self) -> 'DatabaseManager':
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()
