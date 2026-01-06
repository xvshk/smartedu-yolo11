"""
生成演示数据脚本
Generate demo data for student portrait feature demonstration
"""
import random
import sys
import os
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import DatabaseConfig
from src.database.manager import DatabaseManager
from src.database.repositories.student_repository import StudentRepository
from src.database.repositories.detection_repository import DetectionRepository

# 数据库配置
DB_CONFIG = DatabaseConfig(
    host='localhost',
    port=3306,
    user='root',
    password='123456',
    database='classroom_behavior_db'
)

# 行为配置
BEHAVIORS = [
    {'class_id': 0, 'name': 'handrise', 'type': 'normal', 'alert_level': 0},
    {'class_id': 1, 'name': 'read', 'type': 'normal', 'alert_level': 0},
    {'class_id': 2, 'name': 'write', 'type': 'normal', 'alert_level': 0},
    {'class_id': 3, 'name': 'sleep', 'type': 'warning', 'alert_level': 3},
    {'class_id': 4, 'name': 'stand', 'type': 'warning', 'alert_level': 1},
    {'class_id': 5, 'name': 'using_electronic_devices', 'type': 'warning', 'alert_level': 3},
    {'class_id': 6, 'name': 'talk', 'type': 'warning', 'alert_level': 2},
]

# 学生姓名列表
STUDENT_NAMES = [
    '张伟', '王芳', '李娜', '刘洋', '陈明', '杨静', '赵强', '黄丽', '周杰', '吴敏',
    '徐涛', '孙燕', '马超', '朱婷', '胡军', '郭芳', '林峰', '何雪', '高明', '罗琳',
    '梁宇', '宋雨', '唐磊', '许晴', '韩冰', '冯娟', '董鹏', '萧红', '程亮', '曹雪',
    '袁浩', '邓丽', '彭飞', '曾静', '蒋涛', '蔡明', '贾玲', '魏强', '薛冰', '叶青',
    '田华', '石磊', '崔婷', '潘伟', '杜鹃', '钟灵', '姜波', '范明', '方圆', '任静'
]

# 班级配置 - 只保留4个班级
CLASS_CONFIG = [
    {'name': '计算机2401班', 'grade': '2024级', 'department': '计算机学院', 'student_count': 30},
    {'name': '计算机2402班', 'grade': '2024级', 'department': '计算机学院', 'student_count': 30},
    {'name': '软件工程2401班', 'grade': '2024级', 'department': '软件学院', 'student_count': 30},
    {'name': '软件工程2402班', 'grade': '2024级', 'department': '软件学院', 'student_count': 30},
]

# 课程时间段配置
CLASS_PERIODS = [
    {'name': '第1-2节', 'start_hour': 8, 'start_minute': 0, 'duration_minutes': 90},
    {'name': '第3-4节', 'start_hour': 10, 'start_minute': 10, 'duration_minutes': 90},
    {'name': '第5-6节', 'start_hour': 14, 'start_minute': 0, 'duration_minutes': 90},
    {'name': '第7-8节', 'start_hour': 15, 'start_minute': 50, 'duration_minutes': 90},
    {'name': '第9-10节', 'start_hour': 19, 'start_minute': 0, 'duration_minutes': 90},
]

# 课程名称
COURSE_NAMES = [
    '高等数学', '线性代数', '概率论', '数据结构', '算法设计',
    '操作系统', '计算机网络', '数据库原理', '软件工程', '编译原理',
    '机器学习', '深度学习', 'Python程序设计', 'Java程序设计', 'C++程序设计',
    '计算机组成原理', '离散数学', '人工智能导论', '大数据技术', '云计算'
]


def create_class(db: DatabaseManager, class_name: str, grade: str, department: str = '计算机学院') -> int:
    """创建班级"""
    sql = """
        INSERT INTO classes (class_name, grade, department, student_count)
        VALUES (%s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE class_id=LAST_INSERT_ID(class_id)
    """
    return db.insert_and_get_id(sql, (class_name, grade, department))


def generate_students(db: DatabaseManager, class_id: int, class_index: int, count: int = 40):
    """生成学生数据"""
    student_repo = StudentRepository(db)
    students = []
    
    for i in range(count):
        name = STUDENT_NAMES[i % len(STUDENT_NAMES)]
        if i >= len(STUDENT_NAMES):
            name = name + str(i // len(STUDENT_NAMES))
        
        students.append({
            'student_number': f'2024{class_index:02d}{i+1:03d}',
            'name': name,
            'class_id': class_id,
            'gender': random.choice(['male', 'female']),
            'enrollment_year': 2024 if class_index < 7 else 2023
        })
    
    student_repo.import_students_batch(students)
    print(f"    创建了 {count} 名学生")
    return students


def generate_detection_sessions_for_class(db: DatabaseManager, class_id: int, class_name: str, days: int = 30):
    """为指定班级生成检测会话和行为数据"""
    detection_repo = DetectionRepository(db)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    total_sessions = 0
    total_records = 0
    total_entries = 0
    
    current_date = start_date
    while current_date <= end_date:
        # 跳过周末
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        
        # 每天随机选择 2-4 个课程时间段
        selected_periods = random.sample(CLASS_PERIODS, random.randint(2, 4))
        
        for period in selected_periods:
            # 创建会话
            start_time = datetime.combine(
                current_date, 
                datetime.min.time().replace(
                    hour=period['start_hour'], 
                    minute=period['start_minute']
                )
            )
            
            course_name = random.choice(COURSE_NAMES)
            
            session_id = detection_repo.create_session(
                source_type='video',
                source_path=f'/videos/{class_name}/{current_date.strftime("%Y%m%d")}_{period["name"]}_{course_name}.mp4',
                user_id=1
            )
            
            # 更新会话结束时间
            actual_duration = period['duration_minutes'] + random.randint(-10, 5)
            end_time = start_time + timedelta(minutes=actual_duration)
            total_frames = random.randint(2000, 5000)
            detection_repo.update_session(
                session_id=session_id,
                end_time=end_time,
                total_frames=total_frames,
                status='completed'
            )
            
            total_sessions += 1
            
            # 生成检测记录和行为条目
            num_records = random.randint(80, 200)
            records = []
            
            for frame_idx in range(num_records):
                timestamp = frame_idx * 0.5  # 每0.5秒一帧
                detection_count = random.randint(10, 45)  # 检测到的学生数量
                alert_triggered = random.random() < 0.12  # 12%概率触发预警
                
                records.append({
                    'session_id': session_id,
                    'frame_id': frame_idx,
                    'timestamp': timestamp,
                    'alert_triggered': alert_triggered,
                    'detection_count': detection_count
                })
            
            detection_repo.create_records_batch(records)
            total_records += len(records)
            
            # 获取刚创建的记录ID
            created_records = detection_repo.get_records_by_session(session_id)
            
            # 为每个记录生成行为条目
            entries = []
            for record in created_records:
                record_id = record['record_id']
                num_entries = random.randint(8, 25)  # 每帧检测到的行为数量
                
                for _ in range(num_entries):
                    # 正常行为概率更高 (75%)
                    if random.random() < 0.75:
                        behavior = random.choice([b for b in BEHAVIORS if b['type'] == 'normal'])
                    else:
                        behavior = random.choice([b for b in BEHAVIORS if b['type'] == 'warning'])
                    
                    entries.append({
                        'record_id': record_id,
                        'bbox': (
                            random.uniform(0, 0.8),
                            random.uniform(0, 0.8),
                            random.uniform(0.1, 0.3),
                            random.uniform(0.1, 0.4)
                        ),
                        'class_id': behavior['class_id'],
                        'class_name': behavior['name'],
                        'confidence': random.uniform(0.7, 0.99),
                        'behavior_type': behavior['type'],
                        'alert_level': behavior['alert_level']
                    })
            
            detection_repo.create_entries_batch(entries)
            total_entries += len(entries)
        
        current_date += timedelta(days=1)
    
    return total_sessions, total_records, total_entries


def generate_detection_sessions(db: DatabaseManager, days: int = 30):
    """生成检测会话和行为数据（兼容旧接口）"""
    return generate_detection_sessions_for_class(db, 1, '计算机2401班', days)


def main():
    """主函数"""
    print("=" * 60)
    print("开始生成演示数据...")
    print("=" * 60)
    
    db = DatabaseManager(DB_CONFIG)
    
    try:
        total_classes = 0
        total_students = 0
        total_sessions = 0
        total_records = 0
        total_entries = 0
        
        # 为每个班级生成数据
        for idx, class_config in enumerate(CLASS_CONFIG):
            print(f"\n[班级 {idx+1}/{len(CLASS_CONFIG)}] {class_config['name']}")
            print("-" * 40)
            
            # 1. 创建班级
            print(f"  创建班级...")
            class_id = create_class(
                db, 
                class_config['name'], 
                class_config['grade'],
                class_config['department']
            )
            print(f"    班级ID: {class_id}")
            total_classes += 1
            
            # 2. 生成学生
            print(f"  生成学生数据...")
            generate_students(db, class_id, idx + 1, count=class_config['student_count'])
            total_students += class_config['student_count']
            
            # 3. 生成检测数据 (最近15天，减少数据量)
            print(f"  生成检测会话和行为数据 (最近15天)...")
            sessions, records, entries = generate_detection_sessions_for_class(
                db, class_id, class_config['name'], days=15
            )
            total_sessions += sessions
            total_records += records
            total_entries += entries
            print(f"    会话: {sessions}, 记录: {records}, 行为条目: {entries}")
        
        print("\n" + "=" * 60)
        print("演示数据生成完成！")
        print("=" * 60)
        print(f"\n统计汇总:")
        print(f"  - 班级总数: {total_classes}")
        print(f"  - 学生总数: {total_students}")
        print(f"  - 检测会话总数: {total_sessions}")
        print(f"  - 检测记录总数: {total_records}")
        print(f"  - 行为条目总数: {total_entries}")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
