# Database module for classroom behavior detection system
from .config import DatabaseConfig
from .manager import DatabaseManager
from .repositories import (
    DetectionRepository,
    UserRepository,
    CourseRepository,
    StudentRepository,
    AnalyticsRepository
)
from .services import DetectionService

__all__ = [
    'DatabaseConfig',
    'DatabaseManager',
    'DetectionRepository',
    'UserRepository',
    'CourseRepository',
    'StudentRepository',
    'AnalyticsRepository',
    'DetectionService'
]
