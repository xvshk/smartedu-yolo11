"""
Dashboard API模块
Dashboard API endpoints for real-time statistics
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import logging
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.manager import DatabaseManager

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)


def get_db():
    return DatabaseManager()


@dashboard_bp.route('/teacher/stats', methods=['GET'])
@jwt_required()
def get_teacher_stats():
    """获取老师的统计数据"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        role = claims.get('role', '')
        
        if role not in ['teacher', 'admin']:
            return jsonify({
                'success': False,
                'message': '无权访问'
            }), 403
        
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取老师管理的班级数
        if role == 'admin':
            cursor.execute("SELECT COUNT(*) as count FROM classes")
        else:
            cursor.execute("""
                SELECT COUNT(*) as count FROM teacher_classes WHERE teacher_id = %s
            """, (user_id,))
        class_count = cursor.fetchone()['count']
        
        # 获取学生总数
        if role == 'admin':
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
        else:
            cursor.execute("""
                SELECT COUNT(DISTINCT u.user_id) as count 
                FROM users u
                JOIN students s ON u.username = s.student_number
                JOIN teacher_classes tc ON s.class_id = tc.class_id
                WHERE tc.teacher_id = %s AND u.role = 'student'
            """, (user_id,))
        student_count = cursor.fetchone()['count']
        
        # 获取活跃预警数
        today = datetime.now().date()
        if role == 'admin':
            cursor.execute("""
                SELECT COUNT(*) as count FROM alerts 
                WHERE DATE(created_at) = %s AND is_read = FALSE
            """, (today,))
        else:
            cursor.execute("""
                SELECT COUNT(*) as count FROM alerts a
                JOIN detection_sessions ds ON a.session_id = ds.session_id
                JOIN teacher_classes tc ON ds.class_id = tc.class_id
                WHERE tc.teacher_id = %s AND DATE(a.created_at) = %s AND a.is_read = FALSE
            """, (user_id, today))
        alert_count = cursor.fetchone()['count']
        
        # 获取今日检测次数
        if role == 'admin':
            cursor.execute("""
                SELECT COUNT(*) as count FROM detection_sessions 
                WHERE DATE(start_time) = %s
            """, (today,))
        else:
            cursor.execute("""
                SELECT COUNT(*) as count FROM detection_sessions ds
                JOIN teacher_classes tc ON ds.class_id = tc.class_id
                WHERE tc.teacher_id = %s AND DATE(ds.start_time) = %s
            """, (user_id, today))
        detection_count = cursor.fetchone()['count']
        
        cursor.close()
        db.release_connection(conn)
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'totalClasses': class_count,
                'totalStudents': student_count,
                'activeAlerts': alert_count,
                'detectionCount': detection_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get teacher stats error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500


@dashboard_bp.route('/teacher/classes', methods=['GET'])
@jwt_required()
def get_teacher_classes():
    """获取老师管理的班级列表"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        role = claims.get('role', '')
        
        if role not in ['teacher', 'admin']:
            return jsonify({
                'success': False,
                'message': '无权访问'
            }), 403
        
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        if role == 'admin':
            cursor.execute("""
                SELECT c.class_id as id, c.class_name as name, c.department, c.student_count,
                       (SELECT COUNT(*) FROM students WHERE class_id = c.class_id) as actual_count
                FROM classes c
                ORDER BY c.class_name
            """)
        else:
            cursor.execute("""
                SELECT c.class_id as id, c.class_name as name, c.department, c.student_count,
                       tc.is_head_teacher,
                       (SELECT COUNT(*) FROM students WHERE class_id = c.class_id) as actual_count
                FROM classes c
                JOIN teacher_classes tc ON c.class_id = tc.class_id
                WHERE tc.teacher_id = %s
                ORDER BY c.class_name
            """, (user_id,))
        
        classes = cursor.fetchall()
        
        cursor.close()
        db.release_connection(conn)
        db.close()
        
        return jsonify({
            'success': True,
            'data': classes
        }), 200
        
    except Exception as e:
        logger.error(f"Get teacher classes error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取班级列表失败: {str(e)}'
        }), 500


@dashboard_bp.route('/teacher/class/<int:class_id>/students', methods=['GET'])
@jwt_required()
def get_class_students(class_id):
    """获取班级学生列表及状态"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        role = claims.get('role', '')
        
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 验证权限
        if role == 'teacher':
            cursor.execute("""
                SELECT 1 FROM teacher_classes WHERE teacher_id = %s AND class_id = %s
            """, (user_id, class_id))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': '无权访问此班级'
                }), 403
        
        # 获取班级信息
        cursor.execute("""
            SELECT class_id, class_name, department, student_count
            FROM classes WHERE class_id = %s
        """, (class_id,))
        class_info = cursor.fetchone()
        
        if not class_info:
            return jsonify({
                'success': False,
                'message': '班级不存在'
            }), 404
        
        # 获取学生列表
        cursor.execute("""
            SELECT s.student_id as id, s.name, s.student_number,
                   u.user_id
            FROM students s
            LEFT JOIN users u ON s.student_number = u.username
            WHERE s.class_id = %s
            ORDER BY s.student_number
        """, (class_id,))
        students = cursor.fetchall()
        
        # 获取今日预警统计 - alerts 通过 session_id 关联，不直接关联学生
        # 这里简化处理，给每个学生设置默认值
        today = datetime.now().date()
        for student in students:
            # 由于 alerts 表没有 student_id，暂时设置默认值
            student['alertLevel'] = 0
            student['attentionScore'] = 85  # 默认值，后续可从检测记录计算
        
        cursor.close()
        db.release_connection(conn)
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'classInfo': {
                    'id': class_info['class_id'],
                    'name': class_info['class_name'],
                    'department': class_info['department'],
                    'totalStudents': len(students),
                    'onlineStudents': len(students),
                    'averageAttention': 85
                },
                'students': students
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get class students error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取学生列表失败: {str(e)}'
        }), 500


@dashboard_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():
    """获取管理员统计数据"""
    try:
        claims = get_jwt()
        role = claims.get('role', '')
        
        if role != 'admin':
            return jsonify({
                'success': False,
                'message': '无权访问'
            }), 403
        
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 用户统计
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'teacher'")
        teacher_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()['count']
        
        # 班级统计
        cursor.execute("SELECT COUNT(*) as count FROM classes")
        class_count = cursor.fetchone()['count']
        
        # 今日检测统计
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*) as count FROM detection_sessions 
            WHERE DATE(start_time) = %s
        """, (today,))
        today_detections = cursor.fetchone()['count']
        
        # 今日预警统计
        cursor.execute("""
            SELECT COUNT(*) as count FROM alerts 
            WHERE DATE(created_at) = %s
        """, (today,))
        today_alerts = cursor.fetchone()['count']
        
        cursor.close()
        db.release_connection(conn)
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'totalUsers': total_users,
                'teacherCount': teacher_count,
                'studentCount': student_count,
                'classCount': class_count,
                'todayDetections': today_detections,
                'todayAlerts': today_alerts
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get admin stats error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500


@dashboard_bp.route('/student/stats', methods=['GET'])
@jwt_required()
def get_student_stats():
    """获取学生个人统计数据"""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id')
        username = claims.get('username', '')
        
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取学生信息
        cursor.execute("""
            SELECT s.student_id, s.name, s.class_id, c.class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            WHERE s.student_number = %s
        """, (username,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            db.release_connection(conn)
            db.close()
            return jsonify({
                'success': True,
                'data': {
                    'className': '未分配班级',
                    'todayAlerts': 0,
                    'unreadNotifications': 0,
                    'averageAttention': 0
                }
            }), 200
        
        # 今日预警数
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*) as count FROM alerts 
            WHERE student_id = %s AND DATE(created_at) = %s
        """, (student['student_id'], today))
        today_alerts = cursor.fetchone()['count']
        
        # 未读通知数
        cursor.execute("""
            SELECT COUNT(*) as count FROM alert_notifications 
            WHERE receiver_id = %s AND is_read = FALSE
        """, (user_id,))
        unread_notifications = cursor.fetchone()['count']
        
        cursor.close()
        db.release_connection(conn)
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'className': student['class_name'] or '未分配班级',
                'todayAlerts': today_alerts,
                'unreadNotifications': unread_notifications,
                'averageAttention': 85
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get student stats error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500
