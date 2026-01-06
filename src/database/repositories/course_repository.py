"""
课程仓库模块
Course repository for courses, classes, and schedules management
"""
import logging
from datetime import time
from typing import Any, Dict, List, Optional
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class CourseRepository:
    """课程数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        """
        初始化课程仓库
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
    
    # ==================== 课程 CRUD ====================
    
    def create_course(
        self,
        course_name: str,
        course_code: str = None,
        teacher_id: int = None,
        semester: str = None,
        description: str = None
    ) -> int:
        """
        创建课程
        
        Args:
            course_name: 课程名称
            course_code: 课程代码
            teacher_id: 教师ID
            semester: 学期
            description: 描述
            
        Returns:
            新创建的course_id
        """
        sql = """
            INSERT INTO courses (course_name, course_code, teacher_id, semester, description)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(
            sql, (course_name, course_code, teacher_id, semester, description)
        )
    
    def get_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        获取课程信息
        
        Args:
            course_id: 课程ID
            
        Returns:
            课程信息字典或None
        """
        sql = "SELECT * FROM courses WHERE course_id = %s"
        return self.db.query_one(sql, (course_id,))
    
    def list_courses(
        self,
        teacher_id: int = None,
        semester: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询课程列表
        
        Args:
            teacher_id: 教师ID筛选
            semester: 学期筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            课程列表
        """
        conditions = []
        params = []
        
        if teacher_id:
            conditions.append("teacher_id = %s")
            params.append(teacher_id)
        if semester:
            conditions.append("semester = %s")
            params.append(semester)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM courses 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    def update_course(self, course_id: int, **kwargs) -> None:
        """
        更新课程信息
        
        Args:
            course_id: 课程ID
            **kwargs: 要更新的字段
        """
        allowed_fields = {'course_name', 'course_code', 'teacher_id', 'semester', 'description'}
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)
        
        if not updates:
            return
        
        params.append(course_id)
        sql = f"UPDATE courses SET {', '.join(updates)} WHERE course_id = %s"
        self.db.execute(sql, tuple(params))
    
    def delete_course(self, course_id: int) -> None:
        """
        删除课程
        
        Args:
            course_id: 课程ID
        """
        sql = "DELETE FROM courses WHERE course_id = %s"
        self.db.execute(sql, (course_id,))
    
    # ==================== 班级 CRUD ====================
    
    def create_class(
        self,
        class_name: str,
        grade: str = None,
        department: str = None,
        student_count: int = 0
    ) -> int:
        """
        创建班级
        
        Args:
            class_name: 班级名称
            grade: 年级
            department: 院系
            student_count: 学生人数
            
        Returns:
            新创建的class_id
        """
        sql = """
            INSERT INTO classes (class_name, grade, department, student_count)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(sql, (class_name, grade, department, student_count))
    
    def get_class(self, class_id: int) -> Optional[Dict[str, Any]]:
        """
        获取班级信息
        
        Args:
            class_id: 班级ID
            
        Returns:
            班级信息字典或None
        """
        sql = "SELECT * FROM classes WHERE class_id = %s"
        return self.db.query_one(sql, (class_id,))
    
    def list_classes(
        self,
        department: str = None,
        grade: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询班级列表
        
        Args:
            department: 院系筛选
            grade: 年级筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            班级列表
        """
        conditions = []
        params = []
        
        if department:
            conditions.append("department = %s")
            params.append(department)
        if grade:
            conditions.append("grade = %s")
            params.append(grade)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM classes 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    def update_class(self, class_id: int, **kwargs) -> None:
        """
        更新班级信息
        
        Args:
            class_id: 班级ID
            **kwargs: 要更新的字段
        """
        allowed_fields = {'class_name', 'grade', 'department', 'student_count'}
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)
        
        if not updates:
            return
        
        params.append(class_id)
        sql = f"UPDATE classes SET {', '.join(updates)} WHERE class_id = %s"
        self.db.execute(sql, tuple(params))
    
    def delete_class(self, class_id: int) -> None:
        """
        删除班级
        
        Args:
            class_id: 班级ID
        """
        sql = "DELETE FROM classes WHERE class_id = %s"
        self.db.execute(sql, (class_id,))
    
    # ==================== 课堂安排 CRUD ====================
    
    def create_schedule(
        self,
        course_id: int,
        class_id: int,
        classroom: str = None,
        weekday: int = None,
        start_time: time = None,
        end_time: time = None
    ) -> int:
        """
        创建课堂安排
        
        Args:
            course_id: 课程ID
            class_id: 班级ID
            classroom: 教室
            weekday: 星期几 (1-7)
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            新创建的schedule_id
        """
        sql = """
            INSERT INTO schedules (course_id, class_id, classroom, weekday, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.db.insert_and_get_id(
            sql, (course_id, class_id, classroom, weekday, start_time, end_time)
        )
    
    def get_schedule(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """
        获取课堂安排信息
        
        Args:
            schedule_id: 安排ID
            
        Returns:
            安排信息字典或None
        """
        sql = "SELECT * FROM schedules WHERE schedule_id = %s"
        return self.db.query_one(sql, (schedule_id,))
    
    def list_schedules(
        self,
        course_id: int = None,
        class_id: int = None,
        weekday: int = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询课堂安排列表
        
        Args:
            course_id: 课程ID筛选
            class_id: 班级ID筛选
            weekday: 星期几筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            安排列表
        """
        conditions = []
        params = []
        
        if course_id:
            conditions.append("course_id = %s")
            params.append(course_id)
        if class_id:
            conditions.append("class_id = %s")
            params.append(class_id)
        if weekday:
            conditions.append("weekday = %s")
            params.append(weekday)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM schedules 
            {where_clause}
            ORDER BY weekday, start_time
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    def update_schedule(self, schedule_id: int, **kwargs) -> None:
        """
        更新课堂安排
        
        Args:
            schedule_id: 安排ID
            **kwargs: 要更新的字段
        """
        allowed_fields = {'classroom', 'weekday', 'start_time', 'end_time'}
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)
        
        if not updates:
            return
        
        params.append(schedule_id)
        sql = f"UPDATE schedules SET {', '.join(updates)} WHERE schedule_id = %s"
        self.db.execute(sql, tuple(params))
    
    def delete_schedule(self, schedule_id: int) -> None:
        """
        删除课堂安排
        
        Args:
            schedule_id: 安排ID
        """
        sql = "DELETE FROM schedules WHERE schedule_id = %s"
        self.db.execute(sql, (schedule_id,))
    
    def get_schedule_with_details(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """
        获取课堂安排详情（包含课程和班级信息）
        
        Args:
            schedule_id: 安排ID
            
        Returns:
            详细信息字典或None
        """
        sql = """
            SELECT s.*, c.course_name, c.course_code, cl.class_name, cl.grade
            FROM schedules s
            JOIN courses c ON s.course_id = c.course_id
            JOIN classes cl ON s.class_id = cl.class_id
            WHERE s.schedule_id = %s
        """
        return self.db.query_one(sql, (schedule_id,))
