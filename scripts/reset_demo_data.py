"""彻底重置数据库，为每个班级生成独立的检测数据"""
import sys
import os
import random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mysql.connector

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

STUDENT_NAMES = [
    '张伟', '王芳', '李娜', '刘洋', '陈明', '杨静', '赵强', '黄丽', '周杰', '吴敏',
    '徐涛', '孙燕', '马超', '朱婷', '胡军', '郭芳', '林峰', '何雪', '高明', '罗琳',
    '梁宇', '宋雨', '唐磊', '许晴', '韩冰', '冯娟', '董鹏', '萧红', '程亮', '曹雪',
]

CLASS_CONFIG = [
    {'name': '计算机2401班', 'grade': '2024级', 'department': '计算机学院', 'student_count': 30},
    {'name': '计算机2402班', 'grade': '2024级', 'department': '计算机学院', 'student_count': 30},
    {'name': '软件工程2401班', 'grade': '2024级', 'department': '软件学院', 'student_count': 30},
    {'name': '软件工程2402班', 'grade': '2024级', 'department': '软件学院', 'student_count': 30},
]

CLASS_PERIODS = [
    {'name': '第1-2节', 'start_hour': 8, 'start_minute': 0, 'duration_minutes': 90},
    {'name': '第3-4节', 'start_hour': 10, 'start_minute': 10, 'duration_minutes': 90},
    {'name': '第5-6节', 'start_hour': 14, 'start_minute': 0, 'duration_minutes': 90},
    {'name': '第7-8节', 'start_hour': 15, 'start_minute': 50, 'duration_minutes': 90},
]

COURSE_NAMES = ['高等数学', '数据结构', '操作系统', '计算机网络', '数据库原理', 'Python程序设计']

conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='123456', database='classroom_behavior_db')
cursor = conn.cursor()

print("=" * 50)
print("彻底重置数据库...")
print("=" * 50)

# 1. 检查并添加class_id字段到detection_sessions表
print("\n[0/5] 检查数据库结构...")
cursor.execute("SHOW COLUMNS FROM detection_sessions LIKE 'class_id'")
if not cursor.fetchone():
    print("  添加 class_id 字段到 detection_sessions 表...")
    cursor.execute("ALTER TABLE detection_sessions ADD COLUMN class_id INT NULL AFTER schedule_id")
    cursor.execute("ALTER TABLE detection_sessions ADD INDEX idx_class_id (class_id)")
    conn.commit()
    print("  字段已添加")
else:
    print("  class_id 字段已存在")

# 2. 清空所有数据
print("\n[1/5] 清空所有数据...")
cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
cursor.execute('TRUNCATE TABLE behavior_entries')
cursor.execute('TRUNCATE TABLE detection_records')
cursor.execute('TRUNCATE TABLE detection_sessions')
cursor.execute('TRUNCATE TABLE students')
cursor.execute('TRUNCATE TABLE classes')
cursor.execute('DELETE FROM users WHERE role = "student"')
cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
conn.commit()
print("  数据已清空")

# 3. 创建4个班级
print("\n[2/5] 创建班级...")
class_ids = []
for cfg in CLASS_CONFIG:
    cursor.execute(
        'INSERT INTO classes (class_name, grade, department, student_count) VALUES (%s, %s, %s, %s)',
        (cfg['name'], cfg['grade'], cfg['department'], cfg['student_count'])
    )
    class_ids.append(cursor.lastrowid)
    print(f"  创建班级: {cfg['name']} (ID: {cursor.lastrowid})")
conn.commit()

# 4. 创建学生
print("\n[3/5] 创建学生...")
for idx, (class_id, cfg) in enumerate(zip(class_ids, CLASS_CONFIG)):
    for i in range(cfg['student_count']):
        name = STUDENT_NAMES[i % len(STUDENT_NAMES)]
        student_number = f'2024{idx+1:02d}{i+1:03d}'
        cursor.execute(
            'INSERT INTO students (student_number, name, class_id, gender, enrollment_year) VALUES (%s, %s, %s, %s, %s)',
            (student_number, name, class_id, random.choice(['male', 'female']), 2024)
        )
    print(f"  {cfg['name']}: {cfg['student_count']}名学生")
conn.commit()

# 5. 生成检测数据 (15天) - 每个班级独立的数据
print("\n[4/5] 生成检测数据 (15天)...")
end_date = date.today()
start_date = end_date - timedelta(days=15)

total_sessions = 0
total_records = 0
total_entries = 0

for class_id, cfg in zip(class_ids, CLASS_CONFIG):
    class_sessions = 0
    class_entries = 0
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() >= 5:  # 跳过周末
            current_date += timedelta(days=1)
            continue
        
        # 每天2-3节课
        selected_periods = random.sample(CLASS_PERIODS, random.randint(2, 3))
        
        for period in selected_periods:
            start_time = datetime.combine(current_date, datetime.min.time().replace(
                hour=period['start_hour'], minute=period['start_minute']
            ))
            course_name = random.choice(COURSE_NAMES)
            
            # 创建会话 - 关联班级ID
            cursor.execute(
                'INSERT INTO detection_sessions (source_type, source_path, user_id, class_id, status, start_time, end_time, total_frames) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                ('video', f'/videos/{cfg["name"]}/{current_date.strftime("%Y%m%d")}_{course_name}.mp4', 1, class_id, 'completed',
                 start_time, start_time + timedelta(minutes=period['duration_minutes']), random.randint(2000, 4000))
            )
            session_id = cursor.lastrowid
            total_sessions += 1
            class_sessions += 1
            
            # 生成检测记录 (每个会话50-100条记录)
            num_records = random.randint(50, 100)
            for frame_idx in range(num_records):
                cursor.execute(
                    'INSERT INTO detection_records (session_id, frame_id, timestamp, alert_triggered, detection_count) VALUES (%s, %s, %s, %s, %s)',
                    (session_id, frame_idx, frame_idx * 0.5, random.random() < 0.1, random.randint(5, 20))
                )
                record_id = cursor.lastrowid
                total_records += 1
                
                # 每条记录5-15个行为条目
                num_entries = random.randint(5, 15)
                for _ in range(num_entries):
                    behavior = random.choice(BEHAVIORS[:3]) if random.random() < 0.75 else random.choice(BEHAVIORS[3:])
                    cursor.execute(
                        'INSERT INTO behavior_entries (record_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, class_id, class_name, confidence, behavior_type, alert_level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (record_id, random.uniform(0, 0.8), random.uniform(0, 0.8), random.uniform(0.1, 0.3), random.uniform(0.1, 0.4),
                         behavior['class_id'], behavior['name'], random.uniform(0.7, 0.99), behavior['type'], behavior['alert_level'])
                    )
                    total_entries += 1
                    class_entries += 1
        
        current_date += timedelta(days=1)
    
    conn.commit()
    print(f"  {cfg['name']}: {class_sessions}个会话, {class_entries}条行为记录")

# 6. 创建学生用户
print("\n[5/5] 创建学生用户...")
cursor.execute('SELECT student_id, student_number, name FROM students')
students = cursor.fetchall()
for student_id, student_number, name in students:
    cursor.execute(
        'INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)',
        (student_number, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYn.Pw5e5Kje', f'{student_number}@example.com', 'student')
    )
conn.commit()
print(f"  创建了 {len(students)} 个学生用户")

print("\n" + "=" * 50)
print("数据重置完成!")
print("=" * 50)
print(f"\n统计:")
print(f"  - 班级: {len(class_ids)}")
print(f"  - 学生: {sum(c['student_count'] for c in CLASS_CONFIG)}")
print(f"  - 检测会话: {total_sessions}")
print(f"  - 检测记录: {total_records}")
print(f"  - 行为条目: {total_entries}")

cursor.close()
conn.close()
