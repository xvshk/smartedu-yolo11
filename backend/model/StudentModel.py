"""
学生仓库模块
Student repository for student profile management
"""
import logging
from typing import Any, Dict, List, Optional
from backend.model.ManagerModel import DatabaseManager

logger = logging.getLogger(__name__)


class StudentRepository:
    """学生数据访问层"""
    
    def __init__(self, db: DatabaseManager):
        """
        初始化学生仓库
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db
    
    # ==================== 学生 CRUD ====================
    
    def create_student(
        self,
        student_number: str,
        name: str,
        class_id: int = None,
        gender: str = None,
        enrollment_year: int = None
    ) -> int:
        """
        创建学生
        
        Args:
            student_number: 学号
            name: 姓名
            class_id: 班级ID
            gender: 性别 (male/female/other)
            enrollment_year: 入学年份
            
        Returns:
            新创建的student_id
        """
        sql = """
            INSERT INTO students (student_number, name, class_id, gender, enrollment_year)
            VALUES (%s, %s, %s, %s, %s)
        """
        student_id = self.db.insert_and_get_id(
            sql, (student_number, name, class_id, gender, enrollment_year)
        )
        
        # 更新班级学生人数
        if class_id:
            self._update_class_student_count(class_id)
        
        return student_id
    
    def get_student(self, student_id: int) -> Optional[Dict[str, Any]]:
        """
        获取学生信息
        
        Args:
            student_id: 学生ID
            
        Returns:
            学生信息字典或None
        """
        sql = "SELECT * FROM students WHERE student_id = %s"
        return self.db.query_one(sql, (student_id,))
    
    def get_student_by_number(self, student_number: str) -> Optional[Dict[str, Any]]:
        """
        按学号获取学生信息
        
        Args:
            student_number: 学号
            
        Returns:
            学生信息字典或None
        """
        sql = "SELECT * FROM students WHERE student_number = %s"
        return self.db.query_one(sql, (student_number,))
    
    def list_students(
        self,
        class_id: int = None,
        gender: str = None,
        enrollment_year: int = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询学生列表
        
        Args:
            class_id: 班级ID筛选
            gender: 性别筛选
            enrollment_year: 入学年份筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            学生列表
        """
        conditions = []
        params = []
        
        if class_id:
            conditions.append("class_id = %s")
            params.append(class_id)
        if gender:
            conditions.append("gender = %s")
            params.append(gender)
        if enrollment_year:
            conditions.append("enrollment_year = %s")
            params.append(enrollment_year)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM students 
            {where_clause}
            ORDER BY student_number
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        return self.db.query(sql, tuple(params))
    
    def update_student(self, student_id: int, **kwargs) -> None:
        """
        更新学生信息
        
        Args:
            student_id: 学生ID
            **kwargs: 要更新的字段
        """
        # 获取原班级ID
        old_student = self.get_student(student_id)
        old_class_id = old_student['class_id'] if old_student else None
        
        allowed_fields = {'name', 'class_id', 'gender', 'enrollment_year'}
        updates = []
        params = []
        new_class_id = None
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)
                if key == 'class_id':
                    new_class_id = value
        
        if not updates:
            return
        
        params.append(student_id)
        sql = f"UPDATE students SET {', '.join(updates)} WHERE student_id = %s"
        self.db.execute(sql, tuple(params))
        
        # 更新班级学生人数
        if new_class_id is not None and new_class_id != old_class_id:
            if old_class_id:
                self._update_class_student_count(old_class_id)
            if new_class_id:
                self._update_class_student_count(new_class_id)
    
    def delete_student(self, student_id: int) -> None:
        """
        删除学生
        
        Args:
            student_id: 学生ID
        """
        # 获取班级ID
        student = self.get_student(student_id)
        class_id = student['class_id'] if student else None
        
        sql = "DELETE FROM students WHERE student_id = %s"
        self.db.execute(sql, (student_id,))
        
        # 更新班级学生人数
        if class_id:
            self._update_class_student_count(class_id)
    
    def import_students_batch(self, students: List[Dict[str, Any]]) -> int:
        """
        批量导入学生
        
        Args:
            students: 学生列表，每个学生包含 student_number, name, class_id, gender, enrollment_year
            
        Returns:
            导入的学生数
        """
        if not students:
            return 0
        
        sql = """
            INSERT INTO students (student_number, name, class_id, gender, enrollment_year)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name),
                class_id = VALUES(class_id),
                gender = VALUES(gender),
                enrollment_year = VALUES(enrollment_year)
        """
        params_list = [
            (
                s['student_number'],
                s['name'],
                s.get('class_id'),
                s.get('gender'),
                s.get('enrollment_year')
            )
            for s in students
        ]
        count = self.db.execute_many(sql, params_list)
        
        # 更新所有涉及班级的学生人数
        class_ids = set(s.get('class_id') for s in students if s.get('class_id'))
        for class_id in class_ids:
            self._update_class_student_count(class_id)
        
        return count
    
    def count_students(self, class_id: int = None) -> int:
        """
        统计学生数量
        
        Args:
            class_id: 班级ID筛选
            
        Returns:
            学生数量
        """
        if class_id:
            sql = "SELECT COUNT(*) as count FROM students WHERE class_id = %s"
            result = self.db.query_one(sql, (class_id,))
        else:
            sql = "SELECT COUNT(*) as count FROM students"
            result = self.db.query_one(sql)
        
        return result['count'] if result else 0
    
    def get_student_with_class(self, student_id: int) -> Optional[Dict[str, Any]]:
        """
        获取学生信息（包含班级信息）
        
        Args:
            student_id: 学生ID
            
        Returns:
            详细信息字典或None
        """
        sql = """
            SELECT s.*, c.class_name, c.grade, c.department
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            WHERE s.student_id = %s
        """
        return self.db.query_one(sql, (student_id,))
    
    def _update_class_student_count(self, class_id: int) -> None:
        """
        更新班级学生人数
        
        Args:
            class_id: 班级ID
        """
        sql = """
            UPDATE classes 
            SET student_count = (
                SELECT COUNT(*) FROM students WHERE class_id = %s
            )
            WHERE class_id = %s
        """
        self.db.execute(sql, (class_id, class_id))
    
    def list_classes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取班级列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            班级列表
        """
        sql = """
            SELECT class_id, class_name, grade, department, student_count
            FROM classes
            ORDER BY grade DESC, class_name
            LIMIT %s
        """
        return self.db.query(sql, (limit,))
