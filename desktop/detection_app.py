"""
PySide6 实时课堂行为检测应用
支持摄像头和视频文件检测，使用 YOLO 模型进行行为识别
检测结果自动保存到数据库
"""
import sys
import os
import cv2
import json
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import requests

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider, QGroupBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QFrame,
    QProgressBar, QMessageBox, QSpinBox, QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPalette

# 行为类别配置
BEHAVIOR_CLASSES = {
    0: {'name': 'handrise', 'cn_name': '举手', 'type': 'normal', 'color': (0, 255, 0)},
    2: {'name': 'write', 'cn_name': '书写', 'type': 'normal', 'color': (0, 180, 0)},
    3: {'name': 'sleep', 'cn_name': '睡觉', 'type': 'warning', 'color': (255, 0, 0)},
    4: {'name': 'stand', 'cn_name': '站立', 'type': 'warning', 'color': (128, 128, 128)},
    5: {'name': 'using_electronic_devices', 'cn_name': '使用电子设备', 'type': 'warning', 'color': (255, 0, 255)},
    6: {'name': 'talk', 'cn_name': '交谈', 'type': 'warning', 'color': (255, 165, 0)},
    7: {'name': 'head_down', 'cn_name': '低头', 'type': 'warning', 'color': (255, 128, 0)},
}

# 电子设备类别（COCO）
ELECTRONIC_DEVICE_CLASSES = {
    67: 'cell phone',
    63: 'laptop',
}

# 后端 API 地址
API_BASE_URL = "http://127.0.0.1:5000/api"


@dataclass
class Detection:
    """检测结果"""
    class_id: int
    class_name: str
    class_name_cn: str
    confidence: float
    bbox: List[float]
    behavior_type: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DetectionThread(QThread):
    """检测线程"""
    frame_ready = Signal(np.ndarray, list)
    fps_updated = Signal(float)
    error_occurred = Signal(str)
    session_created = Signal(int)  # 会话ID
    
    # COCO 人体类别ID
    PERSON_CLASS_ID = 0
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.cap = None
        self.model = None
        self.device_model = None
        self.face_cascade = None  # 人脸检测器
        self.profile_cascade = None  # 侧脸检测器
        self.confidence_threshold = 0.35
        self.source = 0
        self.device = 'cpu'
        self.session_id = None
        self.save_to_db = True
        self.save_interval = 30  # 每30帧保存一次
        self.frame_count = 0
        
        # 低头检测相关参数
        self.head_down_history = {}  # 记录每个人的低头历史 {person_id: [is_head_down, ...]}
        self.head_down_confirm_frames = 3  # 连续N帧确认才判定为低头
        self.head_down_min_confidence = 0.55  # 低头检测最低置信度
        
        self._load_models()
        self._load_face_detector()
    
    def _load_models(self):
        """加载 YOLO 模型"""
        try:
            from ultralytics import YOLO
            import torch
            
            if torch.cuda.is_available():
                self.device = 'cuda:0'
                print(f"使用 GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.device = 'cpu'
                print("使用 CPU")
            
            model_path = os.path.join(project_root, 'runs/detect/classroom_behavior_4050/weights/best.pt')
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
                self.model.to(self.device)
                print(f"已加载行为检测模型: {model_path}")
            
            device_model_paths = [
                os.path.join(project_root, 'yolo11n.pt'),
                os.path.join(project_root, 'yolo11s.pt'),
            ]
            for path in device_model_paths:
                if os.path.exists(path):
                    self.device_model = YOLO(path)
                    self.device_model.to(self.device)
                    print(f"已加载电子设备检测模型: {path}")
                    break
                    
        except Exception as e:
            print(f"加载模型失败: {e}")
            self.error_occurred.emit(f"加载模型失败: {e}")
    
    def _load_face_detector(self):
        """加载人脸检测器（用于低头检测）"""
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            profile_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
            self.profile_cascade = cv2.CascadeClassifier(profile_path)
            
            print("人脸检测器加载成功")
        except Exception as e:
            print(f"加载人脸检测器失败: {e}")
            self.face_cascade = None
            self.profile_cascade = None
    
    def set_source(self, source):
        self.source = source
    
    def set_confidence(self, conf: float):
        self.confidence_threshold = conf
    
    def set_save_to_db(self, save: bool):
        self.save_to_db = save
    
    def create_session(self, class_id: int = None) -> Optional[int]:
        """创建检测会话"""
        try:
            response = requests.post(f"{API_BASE_URL}/detection/session/start", json={
                "class_id": class_id,
                "source_type": "pyside6_realtime"
            }, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.session_id = data['data']['session_id']
                    print(f"创建检测会话: {self.session_id}")
                    return self.session_id
        except Exception as e:
            print(f"创建会话失败: {e}")
        return None
    
    def end_session(self):
        """结束检测会话"""
        if self.session_id:
            try:
                requests.post(f"{API_BASE_URL}/detection/session/end", json={
                    "session_id": self.session_id
                }, timeout=5)
                print(f"结束检测会话: {self.session_id}")
            except Exception as e:
                print(f"结束会话失败: {e}")
            self.session_id = None
    
    def save_detection_result(self, detections: List[Detection]):
        """保存检测结果到数据库"""
        if not self.save_to_db or not self.session_id:
            return
        
        try:
            detection_data = {
                "session_id": self.session_id,
                "detections": [d.to_dict() for d in detections],
                "total_count": len(detections),
                "warning_count": sum(1 for d in detections if d.behavior_type == 'warning'),
                "normal_count": sum(1 for d in detections if d.behavior_type == 'normal'),
                "behavior_summary": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # 统计行为
            for d in detections:
                name = d.class_name_cn
                if '使用电子设备' in name:
                    name = '使用电子设备'
                detection_data["behavior_summary"][name] = detection_data["behavior_summary"].get(name, 0) + 1
            
            requests.post(f"{API_BASE_URL}/detection/save", json=detection_data, timeout=3)
        except Exception as e:
            print(f"保存检测结果失败: {e}")
    
    def run(self):
        self.running = True
        self.frame_count = 0
        
        # 创建会话
        if self.save_to_db:
            session_id = self.create_session()
            if session_id:
                self.session_created.emit(session_id)
        
        # 打开视频源
        if isinstance(self.source, str) and os.path.exists(self.source):
            self.cap = cv2.VideoCapture(self.source)
        else:
            self.cap = cv2.VideoCapture(int(self.source) if str(self.source).isdigit() else 0)
        
        if not self.cap.isOpened():
            self.error_occurred.emit("无法打开视频源")
            return
        
        frame_count = 0
        start_time = datetime.now()
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                if isinstance(self.source, str):
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            
            detections = self._detect(frame)
            annotated_frame = self._draw_detections(frame, detections)
            self.frame_ready.emit(annotated_frame, detections)
            
            # 定期保存到数据库
            self.frame_count += 1
            if self.save_to_db and self.frame_count % self.save_interval == 0:
                self.save_detection_result(detections)
            
            frame_count += 1
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                self.fps_updated.emit(fps)
                frame_count = 0
                start_time = datetime.now()
        
        # 结束会话
        if self.save_to_db:
            self.end_session()
        
        if self.cap:
            self.cap.release()
    
    def _detect(self, frame: np.ndarray) -> List[Detection]:
        detections = []
        person_boxes = []  # 人体边界框（用于低头检测）
        
        if self.model is not None:
            try:
                results = self.model(frame, conf=self.confidence_threshold, iou=0.5, verbose=False)
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            if cls_id in BEHAVIOR_CLASSES:
                                class_info = BEHAVIOR_CLASSES[cls_id]
                                detections.append(Detection(
                                    class_id=cls_id,
                                    class_name=class_info['name'],
                                    class_name_cn=class_info['cn_name'],
                                    confidence=conf,
                                    bbox=xyxy,
                                    behavior_type=class_info['type']
                                ))
            except Exception as e:
                print(f"行为检测错误: {e}")
        
        if self.device_model is not None:
            try:
                results = self.device_model(frame, conf=0.3, iou=0.5, verbose=False)
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            # 检测电子设备 - 检查是否与已有检测框重叠
                            if cls_id in ELECTRONIC_DEVICE_CLASSES:
                                # 检查是否与已有行为检测框重叠
                                if not self._is_overlapping(xyxy, detections, threshold=0.3):
                                    device_name = ELECTRONIC_DEVICE_CLASSES[cls_id]
                                    detections.append(Detection(
                                        class_id=5,
                                        class_name='using_electronic_devices',
                                        class_name_cn=f'使用电子设备({device_name})',
                                        confidence=conf,
                                        bbox=xyxy,
                                        behavior_type='warning'
                                    ))
                            
                            # 检测人体（用于低头检测）
                            if cls_id == self.PERSON_CLASS_ID and conf > 0.4:
                                person_boxes.append(xyxy)
            except Exception as e:
                print(f"电子设备检测错误: {e}")
        
        # 低头检测
        if person_boxes and self.face_cascade is not None:
            head_down_results = self._detect_head_down(frame, person_boxes, detections)
            for hd in head_down_results:
                # 检查是否与已有检测框重叠
                if not self._is_overlapping(hd['bbox'], detections, threshold=0.3):
                    head_down_class_info = BEHAVIOR_CLASSES[7]  # head_down
                    detections.append(Detection(
                        class_id=7,
                        class_name=head_down_class_info['name'],
                        class_name_cn=head_down_class_info['cn_name'],
                        confidence=hd['confidence'],
                        bbox=hd['bbox'],
                        behavior_type=head_down_class_info['type']
                    ))
        
        # 最终去重：移除重叠的检测框，保留置信度最高的
        detections = self._remove_duplicate_detections(detections)
        
        return detections
    
    def _is_overlapping(self, bbox: List[float], detections: List[Detection], threshold: float = 0.3) -> bool:
        """检查边界框是否与已有检测框重叠"""
        x1, y1, x2, y2 = bbox
        box_area = (x2 - x1) * (y2 - y1)
        
        for det in detections:
            dx1, dy1, dx2, dy2 = det.bbox
            
            # 计算交集
            inter_x1 = max(x1, dx1)
            inter_y1 = max(y1, dy1)
            inter_x2 = min(x2, dx2)
            inter_y2 = min(y2, dy2)
            
            if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                det_area = (dx2 - dx1) * (dy2 - dy1)
                
                # 计算IoU
                union_area = box_area + det_area - inter_area
                iou = inter_area / union_area if union_area > 0 else 0
                
                if iou > threshold:
                    return True
        
        return False
    
    def _remove_duplicate_detections(self, detections: List[Detection]) -> List[Detection]:
        """移除重叠的检测框，保留置信度最高的"""
        if len(detections) <= 1:
            return detections
        
        # 按置信度降序排序
        sorted_dets = sorted(detections, key=lambda x: x.confidence, reverse=True)
        keep = []
        
        for det in sorted_dets:
            # 检查是否与已保留的检测框重叠
            is_duplicate = False
            for kept in keep:
                x1, y1, x2, y2 = det.bbox
                kx1, ky1, kx2, ky2 = kept.bbox
                
                # 计算交集
                inter_x1 = max(x1, kx1)
                inter_y1 = max(y1, ky1)
                inter_x2 = min(x2, kx2)
                inter_y2 = min(y2, ky2)
                
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    det_area = (x2 - x1) * (y2 - y1)
                    kept_area = (kx2 - kx1) * (ky2 - ky1)
                    
                    # 计算IoU
                    union_area = det_area + kept_area - inter_area
                    iou = inter_area / union_area if union_area > 0 else 0
                    
                    # 如果IoU > 0.4，认为是同一个人的重复检测
                    if iou > 0.4:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                keep.append(det)
        
        return keep
    
    def _detect_head_down(self, image: np.ndarray, person_boxes: List[List[float]], 
                          existing_detections: List[Detection]) -> List[Dict]:
        """
        改进的低头检测算法
        
        核心逻辑：
        1. 只检测近距离的大目标（避免远处小目标误检）
        2. 检测整个人体区域的人脸，而不仅仅是头部区域
        3. 如果在整个人体区域都检测不到人脸，才判定为低头
        4. 增加更多过滤条件减少误检
        
        Args:
            image: 图像
            person_boxes: 人体边界框列表
            existing_detections: 已有的检测结果
            
        Returns:
            低头检测结果列表
        """
        head_down_detections = []
        
        if self.face_cascade is None:
            return head_down_detections
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = image.shape[:2]
        
        # 获取已检测到的行为区域（排除低头）
        existing_boxes = []
        if existing_detections:
            for det in existing_detections:
                # 排除已检测到的行为
                if det.class_id in [0, 2, 3, 4, 5, 6]:
                    existing_boxes.append(det.bbox)
        
        for person_box in person_boxes:
            x1, y1, x2, y2 = [int(v) for v in person_box]
            
            # 确保坐标在图像范围内
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            if x2 <= x1 or y2 <= y1:
                continue
            
            person_height = y2 - y1
            person_width = x2 - x1
            
            # 严格过滤条件1：只检测足够大的目标（近距离）
            # 人体框必须占图像高度的30%以上
            if person_height < h * 0.3:
                continue
            
            # 严格过滤条件2：人体框必须足够大（绝对尺寸）
            if person_height < 200 or person_width < 100:
                continue
            
            # 严格过滤条件3：宽高比检查
            aspect_ratio = person_width / person_height
            if aspect_ratio > 1.2 or aspect_ratio < 0.25:
                continue
            
            # 严格过滤条件4：检查是否与已检测行为区域重叠
            skip_person = False
            for eb in existing_boxes:
                ex1, ey1, ex2, ey2 = [int(v) for v in eb]
                inter_x1 = max(x1, ex1)
                inter_y1 = max(y1, ey1)
                inter_x2 = min(x2, ex2)
                inter_y2 = min(y2, ey2)
                
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    person_area = (x2 - x1) * (y2 - y1)
                    if inter_area / person_area > 0.15:
                        skip_person = True
                        break
            
            if skip_person:
                continue
            
            # 在整个人体上半部分区域检测人脸（扩大检测范围到50%）
            head_y2 = y1 + int(person_height * 0.5)
            person_region = gray[y1:head_y2, x1:x2]
            
            if person_region.size == 0:
                continue
            
            # 使用更宽松的参数检测人脸（减少漏检）
            faces = self.face_cascade.detectMultiScale(
                person_region,
                scaleFactor=1.1,
                minNeighbors=3,  # 降低以提高检测率
                minSize=(20, 20),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # 如果检测到人脸，说明不是低头
            if len(faces) > 0:
                continue
            
            # 尝试检测侧脸
            if self.profile_cascade is not None:
                profiles = self.profile_cascade.detectMultiScale(
                    person_region,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(20, 20),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(profiles) > 0:
                    continue
                
                # 翻转检测另一侧
                flipped = cv2.flip(person_region, 1)
                profiles_flip = self.profile_cascade.detectMultiScale(
                    flipped,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(20, 20),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(profiles_flip) > 0:
                    continue
            
            # 所有人脸检测都失败，判定为低头
            # 置信度基于人体框大小
            confidence = 0.6 + (person_height / h) * 0.2
            confidence = min(0.85, confidence)
            
            head_down_detections.append({
                'bbox': [x1, y1, x2, y1 + int(person_height * 0.45)],
                'confidence': round(confidence, 3),
                'reason': 'no_face_detected'
            })
        
        return head_down_detections
    
    def _draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det.bbox]
            
            if det.class_id in BEHAVIOR_CLASSES:
                color = BEHAVIOR_CLASSES[det.class_id]['color']
            else:
                color = (255, 0, 255)
            
            color_bgr = (color[2], color[1], color[0])
            thickness = 3 if det.behavior_type == 'warning' else 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, thickness)
            
            label = f"{det.class_name_cn} {det.confidence:.2f}"
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - label_h - 10), (x1 + label_w + 10, y1), color_bgr, -1)
            
            try:
                from PIL import Image, ImageDraw, ImageFont
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_img)
                
                font = None
                font_paths = [
                    "C:/Windows/Fonts/msyh.ttc",
                    "C:/Windows/Fonts/simhei.ttf",
                    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                ]
                for fp in font_paths:
                    if os.path.exists(fp):
                        font = ImageFont.truetype(fp, 16)
                        break
                
                if font:
                    draw.text((x1 + 5, y1 - label_h - 8), label, fill=(255, 255, 255), font=font)
                    frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                else:
                    cv2.putText(frame, label, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            except:
                cv2.putText(frame, label, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def stop(self):
        self.running = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("课堂行为智能检测系统 - PySide6")
        self.setMinimumSize(1200, 800)
        
        self.detection_thread = DetectionThread()
        self.detection_thread.frame_ready.connect(self.update_frame)
        self.detection_thread.fps_updated.connect(self.update_fps)
        self.detection_thread.error_occurred.connect(self.show_error)
        self.detection_thread.session_created.connect(self.on_session_created)
        
        self.behavior_stats = {info['cn_name']: 0 for info in BEHAVIOR_CLASSES.values()}
        self.current_session_id = None
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧：视频显示区域
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                border: 2px solid #667eea;
                border-radius: 10px;
            }
        """)
        self.video_label.setText("点击「开始检测」启动摄像头\n或选择视频文件")
        left_layout.addWidget(self.video_label)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ 开始检测")
        self.start_btn.clicked.connect(self.start_detection)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ 停止检测")
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.file_btn = QPushButton("🎬 选择视频")
        self.file_btn.clicked.connect(self.select_video)
        control_layout.addWidget(self.file_btn)
        
        self.image_btn = QPushButton("🖼️ 检测图片")
        self.image_btn.clicked.connect(self.detect_image)
        control_layout.addWidget(self.image_btn)
        
        self.screenshot_btn = QPushButton("📷 截图")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        control_layout.addWidget(self.screenshot_btn)
        
        left_layout.addLayout(control_layout)
        
        # 状态栏
        status_layout = QHBoxLayout()
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("color: #67C23A; font-weight: bold;")
        status_layout.addWidget(self.fps_label)
        
        self.status_label = QLabel("状态: 就绪")
        status_layout.addWidget(self.status_label)
        
        self.session_label = QLabel("会话: 未创建")
        self.session_label.setStyleSheet("color: #909399;")
        status_layout.addWidget(self.session_label)
        
        status_layout.addStretch()
        left_layout.addLayout(status_layout)
        
        main_layout.addWidget(left_panel, stretch=3)
        
        # 右侧：控制面板和统计
        right_panel = QWidget()
        right_panel.setMaximumWidth(350)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        
        # 设置组
        settings_group = QGroupBox("检测设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 摄像头选择
        cam_layout = QHBoxLayout()
        cam_layout.addWidget(QLabel("摄像头:"))
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["摄像头 0", "摄像头 1", "摄像头 2"])
        cam_layout.addWidget(self.camera_combo)
        settings_layout.addLayout(cam_layout)
        
        # 置信度阈值
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("置信度:"))
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(10, 90)
        self.conf_slider.setValue(35)
        self.conf_slider.valueChanged.connect(self.update_confidence)
        conf_layout.addWidget(self.conf_slider)
        self.conf_label = QLabel("0.35")
        conf_layout.addWidget(self.conf_label)
        settings_layout.addLayout(conf_layout)
        
        # 保存到数据库选项
        self.save_db_checkbox = QCheckBox("保存检测结果到数据库")
        self.save_db_checkbox.setChecked(True)
        settings_layout.addWidget(self.save_db_checkbox)
        
        right_layout.addWidget(settings_group)
        
        # 实时统计组
        stats_group = QGroupBox("实时统计")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["行为类型", "检测次数"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setRowCount(len(BEHAVIOR_CLASSES))
        
        for i, (cls_id, info) in enumerate(BEHAVIOR_CLASSES.items()):
            self.stats_table.setItem(i, 0, QTableWidgetItem(info['cn_name']))
            self.stats_table.setItem(i, 1, QTableWidgetItem("0"))
        
        stats_layout.addWidget(self.stats_table)
        
        self.reset_stats_btn = QPushButton("重置统计")
        self.reset_stats_btn.clicked.connect(self.reset_stats)
        stats_layout.addWidget(self.reset_stats_btn)
        
        right_layout.addWidget(stats_group)
        
        # 当前检测结果
        current_group = QGroupBox("当前帧检测")
        current_layout = QVBoxLayout(current_group)
        
        self.current_table = QTableWidget()
        self.current_table.setColumnCount(3)
        self.current_table.setHorizontalHeaderLabels(["行为", "置信度", "类型"])
        self.current_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        current_layout.addWidget(self.current_table)
        
        right_layout.addWidget(current_group)
        right_layout.addStretch()
        
        main_layout.addWidget(right_panel, stretch=1)
    
    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fa; }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #667eea;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #667eea;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:disabled { background: #cccccc; }
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #667eea;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #667eea;
                border-radius: 4px;
            }
        """)
    
    @Slot(np.ndarray, list)
    def update_frame(self, frame: np.ndarray, detections: List[Detection]):
        # 转换BGR到RGB并确保内存连续
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame)
        
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # 使用RGB格式创建QImage
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # 复制图像数据避免内存问题
        pixmap = QPixmap.fromImage(qt_image.copy())
        
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
        
        for det in detections:
            if det.class_name_cn in self.behavior_stats:
                self.behavior_stats[det.class_name_cn] += 1
            elif '使用电子设备' in det.class_name_cn:
                self.behavior_stats['使用电子设备'] += 1
        
        for i, (cls_id, info) in enumerate(BEHAVIOR_CLASSES.items()):
            count = self.behavior_stats.get(info['cn_name'], 0)
            self.stats_table.setItem(i, 1, QTableWidgetItem(str(count)))
        
        self.current_table.setRowCount(len(detections))
        for i, det in enumerate(detections):
            self.current_table.setItem(i, 0, QTableWidgetItem(det.class_name_cn))
            self.current_table.setItem(i, 1, QTableWidgetItem(f"{det.confidence:.2f}"))
            
            type_item = QTableWidgetItem("⚠️ 预警" if det.behavior_type == 'warning' else "✅ 正常")
            if det.behavior_type == 'warning':
                type_item.setForeground(QColor("#F56C6C"))
            else:
                type_item.setForeground(QColor("#67C23A"))
            self.current_table.setItem(i, 2, type_item)
    
    @Slot(float)
    def update_fps(self, fps: float):
        self.fps_label.setText(f"FPS: {fps:.1f}")
    
    @Slot(str)
    def show_error(self, error: str):
        QMessageBox.critical(self, "错误", error)
    
    @Slot(int)
    def on_session_created(self, session_id: int):
        self.current_session_id = session_id
        self.session_label.setText(f"会话: #{session_id}")
        self.session_label.setStyleSheet("color: #67C23A; font-weight: bold;")
    
    def update_confidence(self, value: int):
        conf = value / 100.0
        self.conf_label.setText(f"{conf:.2f}")
        self.detection_thread.set_confidence(conf)
    
    def start_detection(self):
        source = self.camera_combo.currentIndex()
        self.detection_thread.set_source(source)
        self.detection_thread.set_save_to_db(self.save_db_checkbox.isChecked())
        self.detection_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("状态: 检测中...")
    
    def stop_detection(self):
        self.detection_thread.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("状态: 已停止")
        self.session_label.setText("会话: 已结束")
        self.session_label.setStyleSheet("color: #909399;")
    
    def select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov);;所有文件 (*.*)"
        )
        if file_path:
            self.detection_thread.set_source(file_path)
            self.status_label.setText(f"已选择: {os.path.basename(file_path)}")
    
    def detect_image(self):
        """检测单张图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.webp);;所有文件 (*.*)"
        )
        if not file_path:
            return
        
        # 停止视频检测（如果正在运行）
        if self.detection_thread.running:
            self.stop_detection()
        
        self.status_label.setText(f"正在检测: {os.path.basename(file_path)}")
        
        try:
            # 读取图片
            image = cv2.imread(file_path)
            if image is None:
                QMessageBox.warning(self, "错误", "无法读取图片文件")
                return
            
            # 使用检测线程的方法进行检测
            detections = self._detect_single_image(image)
            
            # 绘制检测结果
            annotated_image = self.detection_thread._draw_detections(image.copy(), detections)
            
            # 转换为RGB格式并创建QImage
            # 使用 .copy() 确保数据连续，避免内存问题
            rgb_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
            rgb_image = np.ascontiguousarray(rgb_image)
            
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # 创建QImage时使用RGB格式
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # 立即转换为QPixmap（这会复制数据，避免内存问题）
            pixmap = QPixmap.fromImage(qt_image.copy())
            
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
            
            # 更新统计
            for det in detections:
                if det.class_name_cn in self.behavior_stats:
                    self.behavior_stats[det.class_name_cn] += 1
                elif '使用电子设备' in det.class_name_cn:
                    self.behavior_stats['使用电子设备'] += 1
            
            for i, (cls_id, info) in enumerate(BEHAVIOR_CLASSES.items()):
                count = self.behavior_stats.get(info['cn_name'], 0)
                self.stats_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
            # 更新当前检测表
            self.current_table.setRowCount(len(detections))
            for i, det in enumerate(detections):
                self.current_table.setItem(i, 0, QTableWidgetItem(det.class_name_cn))
                self.current_table.setItem(i, 1, QTableWidgetItem(f"{det.confidence:.2f}"))
                
                type_item = QTableWidgetItem("⚠️ 预警" if det.behavior_type == 'warning' else "✅ 正常")
                if det.behavior_type == 'warning':
                    type_item.setForeground(QColor("#F56C6C"))
                else:
                    type_item.setForeground(QColor("#67C23A"))
                self.current_table.setItem(i, 2, type_item)
            
            self.status_label.setText(f"检测完成: 发现 {len(detections)} 个行为")
            self.fps_label.setText("FPS: -")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "检测错误", f"检测图片时出错: {str(e)}")
            self.status_label.setText("状态: 检测失败")
    
    def _detect_single_image(self, frame: np.ndarray) -> List[Detection]:
        """检测单张图片（复用检测线程的逻辑）"""
        detections = []
        person_boxes = []
        
        # 行为检测
        if self.detection_thread.model is not None:
            try:
                results = self.detection_thread.model(
                    frame, 
                    conf=self.detection_thread.confidence_threshold, 
                    iou=0.5, 
                    verbose=False
                )
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            if cls_id in BEHAVIOR_CLASSES:
                                class_info = BEHAVIOR_CLASSES[cls_id]
                                detections.append(Detection(
                                    class_id=cls_id,
                                    class_name=class_info['name'],
                                    class_name_cn=class_info['cn_name'],
                                    confidence=conf,
                                    bbox=xyxy,
                                    behavior_type=class_info['type']
                                ))
            except Exception as e:
                print(f"行为检测错误: {e}")
        
        # 电子设备检测
        if self.detection_thread.device_model is not None:
            try:
                results = self.detection_thread.device_model(frame, conf=0.3, iou=0.5, verbose=False)
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            if cls_id in ELECTRONIC_DEVICE_CLASSES:
                                if not self.detection_thread._is_overlapping(xyxy, detections, threshold=0.3):
                                    device_name = ELECTRONIC_DEVICE_CLASSES[cls_id]
                                    detections.append(Detection(
                                        class_id=5,
                                        class_name='using_electronic_devices',
                                        class_name_cn=f'使用电子设备({device_name})',
                                        confidence=conf,
                                        bbox=xyxy,
                                        behavior_type='warning'
                                    ))
                            
                            if cls_id == self.detection_thread.PERSON_CLASS_ID and conf > 0.4:
                                person_boxes.append(xyxy)
            except Exception as e:
                print(f"电子设备检测错误: {e}")
        
        # 低头检测
        if person_boxes and self.detection_thread.face_cascade is not None:
            head_down_results = self.detection_thread._detect_head_down(frame, person_boxes, detections)
            for hd in head_down_results:
                if not self.detection_thread._is_overlapping(hd['bbox'], detections, threshold=0.3):
                    head_down_class_info = BEHAVIOR_CLASSES[7]
                    detections.append(Detection(
                        class_id=7,
                        class_name=head_down_class_info['name'],
                        class_name_cn=head_down_class_info['cn_name'],
                        confidence=hd['confidence'],
                        bbox=hd['bbox'],
                        behavior_type=head_down_class_info['type']
                    ))
        
        # 去重
        detections = self.detection_thread._remove_duplicate_detections(detections)
        
        return detections
    
    def take_screenshot(self):
        pixmap = self.video_label.pixmap()
        if pixmap:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            pixmap.save(filename)
            QMessageBox.information(self, "截图成功", f"已保存: {filename}")
    
    def reset_stats(self):
        self.behavior_stats = {info['cn_name']: 0 for info in BEHAVIOR_CLASSES.values()}
        for i in range(self.stats_table.rowCount()):
            self.stats_table.setItem(i, 1, QTableWidgetItem("0"))
    
    def closeEvent(self, event):
        self.detection_thread.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
