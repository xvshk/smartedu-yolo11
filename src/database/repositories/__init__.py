# Database repositories
from .detection_repository import DetectionRepository
from .user_repository import UserRepository
from .course_repository import CourseRepository
from .student_repository import StudentRepository
from .analytics_repository import AnalyticsRepository

__all__ = [
    'DetectionRepository',
    'UserRepository', 
    'CourseRepository',
    'StudentRepository',
    'AnalyticsRepository'
]
