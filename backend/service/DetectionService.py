"""
实时检测服务模块
Real-time detection service using YOLOv11 for classroom behavior detection.
支持多线程处理以提高帧率
整合了数据存储功能，符合Service层职责
"""
import logging
import base64
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# 导入数据访问层组件
from ..model.ManagerModel import DatabaseManager
from ..model.ConfigModel import DatabaseConfig
from backend.model.Detection_accessModel import DetectionDataAccess

# 导入服务接口
from .InterfaceService import IDetectionService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

# 行为类别配置 - 与训练模型一致
BEHAVIOR_CLASSES = {
    0: {'name': 'handrise', 'cn_name': '举手', 'type': 'normal', 'color': (0, 255, 0)},
    # 1: {'name': 'read', 'cn_name': '阅读', 'type': 'normal', 'color': (0, 200, 0)},  # 已禁用
    2: {'name': 'write', 'cn_name': '书写', 'type': 'normal', 'color': (0, 180, 0)},
    3: {'name': 'sleep', 'cn_name': '睡觉', 'type': 'warning', 'color': (255, 0, 0)},
    4: {'name': 'stand', 'cn_name': '站立', 'type': 'warning', 'color': (128, 128, 128)},
    5: {'name': 'using_electronic_devices', 'cn_name': '使用电子设备', 'type': 'warning', 'color': (255, 0, 255)},
    6: {'name': 'talk', 'cn_name': '交谈', 'type': 'warning', 'color': (255, 165, 0)},
    7: {'name': 'head_down', 'cn_name': '低头', 'type': 'warning', 'color': (255, 128, 0)},  # 新增低头行为
}

# 预警级别
ALERT_LEVELS = {
    0: {'name': 'normal', 'cn_name': '正常', 'classes': [0, 2]},  # 移除阅读(1)
    1: {'name': 'mild', 'cn_name': '轻度预警', 'classes': [4, 7]},
    2: {'name': 'moderate', 'cn_name': '中度预警', 'classes': [6]},
    3: {'name': 'severe', 'cn_name': '严重预警', 'classes': [3, 5]},
}


@dataclass
class Detection:
    """检测结果"""
    class_id: int
    class_name: str
    class_name_cn: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    behavior_type: str
    alert_level: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DetectionResult:
    """检测结果汇总"""
    detections: List[Detection]
    total_count: int
    warning_count: int
    normal_count: int
    behavior_summary: Dict[str, int]
    alert_summary: Dict[str, int]
    timestamp: str
    behavior_duration: Dict[str, float] = None  # 各行为累计时间（秒）
    
    def to_dict(self) -> Dict:
        result = {
            'detections': [d.to_dict() for d in self.detections],
            'total_count': self.total_count,
            'warning_count': self.warning_count,
            'normal_count': self.normal_count,
            'behavior_summary': self.behavior_summary,
            'alert_summary': self.alert_summary,
            'timestamp': self.timestamp
        }
        if self.behavior_duration:
            result['behavior_duration'] = self.behavior_duration
        return result


class FPSCounter:
    """FPS计数器"""
    def __init__(self, avg_frames: int = 30):
        self.avg_frames = avg_frames
        self.timestamps = []
        self._lock = threading.Lock()
    
    def tick(self):
        """记录一帧"""
        with self._lock:
            now = time.time()
            self.timestamps.append(now)
            # 只保留最近的帧
            if len(self.timestamps) > self.avg_frames:
                self.timestamps = self.timestamps[-self.avg_frames:]
    
    def get_fps(self) -> float:
        """获取当前FPS"""
        with self._lock:
            if len(self.timestamps) < 2:
                return 0.0
            duration = self.timestamps[-1] - self.timestamps[0]
            if duration <= 0:
                return 0.0
            return (len(self.timestamps) - 1) / duration


class BehaviorTimeTracker:
    """
    行为时间跟踪器
    用于统计各种行为的累计持续时间
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.behavior_duration = {info['cn_name']: 0.0 for info in BEHAVIOR_CLASSES.values()}
        self.frame_count = 0
        self.detection_interval = 0.5  # 默认检测间隔（秒）
    
    def reset(self):
        """重置统计"""
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.behavior_duration = {info['cn_name']: 0.0 for info in BEHAVIOR_CLASSES.values()}
        self.frame_count = 0
    
    def update(self, detections: List[Detection], interval_seconds: float = None):
        """
        更新行为时间统计
        
        Args:
            detections: 当前帧检测到的行为列表
            interval_seconds: 检测间隔（秒），如果不提供则使用默认值
        """
        current_time = datetime.now()
        
        # 计算时间间隔
        if interval_seconds is not None:
            delta = interval_seconds
        else:
            delta = (current_time - self.last_update_time).total_seconds()
            # 限制最大间隔为2秒，避免异常值
            delta = min(delta, 2.0)
        
        self.last_update_time = current_time
        self.frame_count += 1
        
        # 统计当前帧检测到的行为
        current_behaviors = set()
        for det in detections:
            current_behaviors.add(det.class_name_cn)
        
        # 为检测到的行为累加时间
        for behavior_name in current_behaviors:
            if behavior_name in self.behavior_duration:
                self.behavior_duration[behavior_name] += delta
    
    def get_duration(self) -> Dict[str, float]:
        """获取各行为累计时间（秒）"""
        return {k: round(v, 1) for k, v in self.behavior_duration.items()}
    
    def get_duration_formatted(self) -> Dict[str, str]:
        """获取格式化的时间字符串（分:秒）"""
        result = {}
        for name, seconds in self.behavior_duration.items():
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            result[name] = f"{minutes}:{secs:02d}"
        return result
    
    def get_total_time(self) -> float:
        """获取总检测时间（秒）"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取完整统计信息"""
        total_time = self.get_total_time()
        return {
            'total_time': round(total_time, 1),
            'total_time_formatted': f"{int(total_time // 60)}:{int(total_time % 60):02d}",
            'frame_count': self.frame_count,
            'behavior_duration': self.get_duration(),
            'behavior_duration_formatted': self.get_duration_formatted()
        }


class DetectionService(IDetectionService):
    """
    实时检测服务
    Provides real-time behavior detection using YOLO models.
    支持双模型检测：行为模型 + 物体检测模型（检测电子设备）
    支持人脸检测判断低头行为
    支持多线程处理以提高帧率
    """
    
    # COCO数据集中的电子设备类别（仅检测非学习用途的设备）
    # 对于计算机专业学生，电脑和笔记本是正常学习工具，不作为预警
    ELECTRONIC_DEVICE_CLASSES = {
        67: 'cell phone',      # 手机 - 需要检测
        # 63: 'laptop',        # 笔记本电脑 - 计算机专业正常使用，已禁用
        # 62: 'tv',            # 电视/显示器 - 计算机专业正常使用，已禁用
        # 66: 'keyboard',      # 键盘 - 计算机专业正常使用，已禁用
        # 64: 'mouse',         # 鼠标 - 计算机专业正常使用，已禁用
        # 74: 'remote',        # 遥控器 - 已禁用
    }
    
    # COCO数据集中的人类别
    PERSON_CLASS_ID = 0
    
    def __init__(self, model_path: str = None, db: DatabaseManager = None, config: DatabaseConfig = None):
        """
        初始化检测服务
        
        Args:
            model_path: YOLO模型路径，默认使用项目中训练好的模型
            db: 数据库管理器实例，如果为None则创建新实例
            config: 数据库配置
        """
        # YOLO检测相关初始化
        self.model = None
        self.device_model = None  # 电子设备检测模型
        self.face_cascade = None  # 人脸检测器
        self.model_path = model_path
        self.confidence_threshold = 0.45  # 提高默认置信度阈值以减少误检测
        self.iou_threshold = 0.5  # 提高IOU阈值以减少重叠框
        self.model_loaded = False
        self.device_model_loaded = False
        self.device = self._get_device()  # 检测设备（GPU/CPU）
        self.time_tracker = BehaviorTimeTracker()  # 行为时间跟踪器
        
        # 数据存储相关初始化
        if db is None:
            self.data_access = DetectionDataAccess(config=config)
        else:
            self.data_access = DetectionDataAccess(db=db)
        
        # 当前会话状态
        self._current_session_id: Optional[int] = None
        self._frame_count: int = 0
        self._record_buffer: List[Dict] = []
        self._entry_buffer: List[Dict] = []
        self._buffer_size: int = 100  # 批量插入阈值
        
        # GPU 优化参数
        self.use_half = self.device != 'cpu'  # GPU 时使用 FP16 半精度
        self.imgsz = 1280  # 推理图像尺寸（增大以提高 GPU 利用率）
        
        # 多线程相关
        self._executor = ThreadPoolExecutor(max_workers=3)  # 线程池
        self._detection_lock = threading.Lock()  # 检测锁
        self._last_result = None  # 缓存最后一次检测结果
        self._last_annotated_image = None  # 缓存最后一次标注图像
        self._frame_skip = 2  # 跳帧数（每N帧检测一次）
        self._frame_count_detection = 0  # 检测帧计数器（区别于数据库帧计数）
        self._fps_counter = FPSCounter()  # FPS计数器
        
        self._load_model()
        self._load_device_model()
        self._load_face_detector()
    
    def _get_device(self) -> str:
        """获取最佳计算设备（优先使用GPU）"""
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"Using GPU: {device_name} ({gpu_memory:.1f}GB)")
                return 'cuda:0'  # 使用第一个GPU
            else:
                logger.info("CUDA not available, using CPU")
                return 'cpu'
        except Exception as e:
            logger.warning(f"Failed to detect GPU: {e}, using CPU")
            return 'cpu'
    
    def _load_model(self):
        """加载YOLO模型"""
        try:
            from ultralytics import YOLO
            
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 优先使用指定的模型路径
            if self.model_path and os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                self.model.to(self.device)  # 移动到GPU
                if self.use_half and self.device != 'cpu':
                    self.model.model.half()  # 启用 FP16 半精度
                    logger.info("Model using FP16 half precision")
                logger.info(f"Loaded model from {self.model_path} on device {self.device}")
                self.model_loaded = True
                return
            
            # 尝试加载训练好的模型
            trained_model_path = os.path.join(project_root, 'runs/detect/classroom_behavior_4050/weights/best.pt')
            if os.path.exists(trained_model_path):
                self.model = YOLO(trained_model_path)
                self.model.to(self.device)  # 移动到GPU
                if self.use_half and self.device != 'cpu':
                    self.model.model.half()  # 启用 FP16 半精度
                    logger.info("Model using FP16 half precision")
                logger.info(f"Loaded trained model from {trained_model_path} on device {self.device}")
                self.model_loaded = True
                return
            
            # 尝试加载预训练模型
            pretrained_paths = [
                os.path.join(project_root, 'yolo11n.pt'),
                os.path.join(project_root, 'yolo11s.pt'),
                os.path.join(project_root, 'yolo11m.pt'),
            ]
            for path in pretrained_paths:
                if os.path.exists(path):
                    self.model = YOLO(path)
                    self.model.to(self.device)  # 移动到GPU
                    if self.use_half and self.device != 'cpu':
                        self.model.model.half()  # 启用 FP16 半精度
                        logger.info("Model using FP16 half precision")
                    logger.info(f"Loaded pretrained model from {path} on device {self.device}")
                    self.model_loaded = True
                    return
            
            logger.warning("No YOLO model found, using demo mode")
            self.model_loaded = False
                
        except ImportError:
            logger.error("ultralytics not installed, using demo mode")
            self.model_loaded = False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model_loaded = False
    
    def _load_device_model(self):
        """加载电子设备检测模型（使用预训练的COCO模型）"""
        try:
            from ultralytics import YOLO
            
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 使用预训练的YOLOv11模型检测电子设备
            pretrained_paths = [
                os.path.join(project_root, 'yolo11n.pt'),
                os.path.join(project_root, 'yolo11s.pt'),
                os.path.join(project_root, 'yolo11m.pt'),
            ]
            
            for path in pretrained_paths:
                if os.path.exists(path):
                    self.device_model = YOLO(path)
                    self.device_model.to(self.device)  # 移动到GPU
                    if self.use_half and self.device != 'cpu':
                        self.device_model.model.half()  # 启用 FP16 半精度
                    logger.info(f"Loaded device detection model from {path} on device {self.device}")
                    self.device_model_loaded = True
                    return
            
            logger.warning("No pretrained model found for device detection")
            self.device_model_loaded = False
            
        except Exception as e:
            logger.error(f"Failed to load device model: {e}")
            self.device_model_loaded = False
    
    def _load_face_detector(self):
        """加载人脸检测器（用于低头检测）"""
        try:
            # 使用OpenCV的Haar级联分类器检测人脸
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            # 也加载侧脸检测器
            profile_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
            self.profile_cascade = cv2.CascadeClassifier(profile_path)
            
            logger.info("Face detector loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load face detector: {e}")
            self.face_cascade = None
            self.profile_cascade = None
    
    def _detect_head_down(self, image: np.ndarray, person_boxes: List[List[float]], existing_detections: List = None) -> List[Dict]:
        """
        改进的低头检测算法
        
        核心逻辑：
        1. 只检测近距离的大目标（避免远处小目标误检）
        2. 检测整个人体上半部分区域的人脸
        3. 如果在整个区域都检测不到人脸，才判定为低头
        4. 增加更多过滤条件减少误检
        
        Args:
            image: 图像
            person_boxes: 人体边界框列表 [[x1,y1,x2,y2], ...]
            existing_detections: 已有的检测结果，用于避免与其他行为冲突
            
        Returns:
            低头检测结果列表
        """
        head_down_detections = []
        
        if self.face_cascade is None:
            return head_down_detections
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = image.shape[:2]
        
        # 获取已检测到的行为区域
        existing_boxes = []
        if existing_detections:
            for det in existing_detections:
                if det.class_id in [0, 2, 3, 4, 5, 6]:
                    existing_boxes.append(det.bbox)
        
        for person_box in person_boxes:
            x1, y1, x2, y2 = [int(v) for v in person_box]
            
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            if x2 <= x1 or y2 <= y1:
                continue
            
            person_height = y2 - y1
            person_width = x2 - x1
            
            # 严格过滤：只检测占图像30%以上的大目标
            if person_height < h * 0.3:
                continue
            
            if person_height < 200 or person_width < 100:
                continue
            
            aspect_ratio = person_width / person_height
            if aspect_ratio > 1.2 or aspect_ratio < 0.25:
                continue
            
            # 检查与已检测行为的重叠
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
            
            # 检测人体上半部分的人脸
            head_y2 = y1 + int(person_height * 0.5)
            person_region = gray[y1:head_y2, x1:x2]
            
            if person_region.size == 0:
                continue
            
            # 宽松参数检测人脸
            faces = self.face_cascade.detectMultiScale(
                person_region,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(20, 20),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(faces) > 0:
                continue
            
            # 检测侧脸
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
            
            # 判定为低头
            confidence = 0.6 + (person_height / h) * 0.2
            confidence = min(0.85, confidence)
            
            head_down_detections.append({
                'bbox': [x1, y1, x2, y1 + int(person_height * 0.45)],
                'confidence': confidence,
                'reason': 'no_face_detected'
            })
        
        return head_down_detections
    
    def detect_image(self, image: np.ndarray) -> Tuple[np.ndarray, DetectionResult]:
        """
        检测单张图片
        
        Args:
            image: OpenCV格式的图片 (BGR)
            
        Returns:
            (标注后的图片, 检测结果)
        """
        detections = []
        device_detections = []  # 电子设备检测结果
        person_boxes = []  # 人体边界框（用于低头检测）
        behavior_summary = {info['cn_name']: 0 for info in BEHAVIOR_CLASSES.values()}
        alert_summary = {level['cn_name']: 0 for level in ALERT_LEVELS.values()}
        
        # 1. 先检测电子设备和人体
        if self.device_model is not None and self.device_model_loaded:
            try:
                device_results = self.device_model(
                    image, 
                    conf=0.3, 
                    iou=self.iou_threshold, 
                    imgsz=self.imgsz,
                    half=self.use_half,
                    verbose=False
                )
                for result in device_results:
                    boxes = result.boxes
                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            # 检测电子设备
                            if cls_id in self.ELECTRONIC_DEVICE_CLASSES:
                                device_name = self.ELECTRONIC_DEVICE_CLASSES[cls_id]
                                device_detections.append({
                                    'class_id': cls_id,
                                    'name': device_name,
                                    'confidence': conf,
                                    'bbox': xyxy
                                })
                            
                            # 检测人体（用于低头检测）
                            if cls_id == self.PERSON_CLASS_ID and conf > 0.4:
                                person_boxes.append(xyxy)
                                
            except Exception as e:
                logger.error(f"Device detection error: {e}")
        
        # 2. 行为检测
        if self.model is not None and self.model_loaded:
            try:
                # 运行YOLO检测（使用优化参数）
                results = self.model(
                    image, 
                    conf=self.confidence_threshold, 
                    iou=self.iou_threshold, 
                    imgsz=self.imgsz,
                    half=self.use_half,
                    verbose=False
                )
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            # 获取类别信息
                            if cls_id in BEHAVIOR_CLASSES:
                                class_info = BEHAVIOR_CLASSES[cls_id]
                            else:
                                logger.warning(f"Unknown class_id: {cls_id}")
                                continue  # 跳过未知类别
                            
                            # 获取预警级别
                            alert_level = 0
                            for level, level_info in ALERT_LEVELS.items():
                                if cls_id in level_info['classes']:
                                    alert_level = level
                                    break
                            
                            detection = Detection(
                                class_id=cls_id,
                                class_name=class_info['name'],
                                class_name_cn=class_info['cn_name'],
                                confidence=round(conf, 3),
                                bbox=[round(v, 1) for v in xyxy],
                                behavior_type=class_info['type'],
                                alert_level=alert_level
                            )
                            detections.append(detection)
                            behavior_summary[class_info['cn_name']] += 1
                            alert_summary[ALERT_LEVELS[alert_level]['cn_name']] += 1
                            
            except Exception as e:
                logger.error(f"Detection error: {e}", exc_info=True)
                detections, behavior_summary, alert_summary = self._generate_demo_detections(image)
        else:
            # 模拟检测结果
            detections, behavior_summary, alert_summary = self._generate_demo_detections(image)
        
        # 3. 如果检测到电子设备但没有检测到"使用电子设备"行为，添加该行为
        if device_detections and not any(d.class_id == 5 for d in detections):
            for device in device_detections:
                # 为每个检测到的电子设备创建一个"使用电子设备"的检测结果
                device_class_info = BEHAVIOR_CLASSES[5]  # using_electronic_devices
                detection = Detection(
                    class_id=5,
                    class_name=device_class_info['name'],
                    class_name_cn=f"{device_class_info['cn_name']}({device['name']})",
                    confidence=round(device['confidence'], 3),
                    bbox=[round(v, 1) for v in device['bbox']],
                    behavior_type=device_class_info['type'],
                    alert_level=3  # 严重预警
                )
                detections.append(detection)
                behavior_summary[device_class_info['cn_name']] += 1
                alert_summary[ALERT_LEVELS[3]['cn_name']] += 1
        
        # 4. 低头检测（传入已有检测结果以避免与书写行为冲突）
        if person_boxes:
            head_down_results = self._detect_head_down(image, person_boxes, detections)
            for hd in head_down_results:
                head_down_class_info = BEHAVIOR_CLASSES[7]  # head_down
                detection = Detection(
                    class_id=7,
                    class_name=head_down_class_info['name'],
                    class_name_cn=head_down_class_info['cn_name'],
                    confidence=round(hd['confidence'], 3),
                    bbox=[round(v, 1) for v in hd['bbox']],
                    behavior_type=head_down_class_info['type'],
                    alert_level=1  # 轻度预警
                )
                detections.append(detection)
                behavior_summary[head_down_class_info['cn_name']] += 1
                alert_summary[ALERT_LEVELS[1]['cn_name']] += 1
        
        # 绘制检测框
        annotated_image = self._draw_detections(image.copy(), detections, device_detections)
        
        # 统计结果
        warning_count = sum(1 for d in detections if d.behavior_type == 'warning')
        normal_count = sum(1 for d in detections if d.behavior_type == 'normal')
        
        # 更新行为时间统计
        self.time_tracker.update(detections)
        
        result = DetectionResult(
            detections=detections,
            total_count=len(detections),
            warning_count=warning_count,
            normal_count=normal_count,
            behavior_summary=behavior_summary,
            alert_summary=alert_summary,
            timestamp=datetime.now().isoformat(),
            behavior_duration=self.time_tracker.get_duration()
        )
        
        return annotated_image, result
    
    def _generate_demo_detections(self, image: np.ndarray) -> Tuple[List[Detection], Dict[str, int], Dict[str, int]]:
        """生成模拟检测结果用于演示"""
        import random
        
        h, w = image.shape[:2]
        detections = []
        behavior_summary = {info['cn_name']: 0 for info in BEHAVIOR_CLASSES.values()}
        alert_summary = {level['cn_name']: 0 for level in ALERT_LEVELS.values()}
        
        # 生成3-8个随机检测框
        num_detections = random.randint(3, 8)
        
        for i in range(num_detections):
            # 随机选择行为类别
            class_id = random.choice(list(BEHAVIOR_CLASSES.keys()))
            class_info = BEHAVIOR_CLASSES[class_id]
            
            # 生成随机边界框
            box_w = random.randint(80, 150)
            box_h = random.randint(100, 200)
            x1 = random.randint(50, max(51, w - box_w - 50))
            y1 = random.randint(50, max(51, h - box_h - 50))
            x2 = x1 + box_w
            y2 = y1 + box_h
            
            # 获取预警级别
            alert_level = 0
            for level, level_info in ALERT_LEVELS.items():
                if class_id in level_info['classes']:
                    alert_level = level
                    break
            
            detection = Detection(
                class_id=class_id,
                class_name=class_info['name'],
                class_name_cn=class_info['cn_name'],
                confidence=round(random.uniform(0.6, 0.95), 3),
                bbox=[x1, y1, x2, y2],
                behavior_type=class_info['type'],
                alert_level=alert_level
            )
            detections.append(detection)
            behavior_summary[class_info['cn_name']] += 1
            alert_summary[ALERT_LEVELS[alert_level]['cn_name']] += 1
        
        return detections, behavior_summary, alert_summary
    
    def _draw_detections(self, image: np.ndarray, detections: List[Detection], device_detections: List[Dict] = None) -> np.ndarray:
        """在图片上绘制检测框（支持中文标签）"""
        # 转换为PIL图像以支持中文
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_image)
        
        # 尝试加载中文字体
        font = None
        font_size = 20
        try:
            # Windows 系统字体路径
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
                "/System/Library/Fonts/PingFang.ttc",  # macOS
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            if font is None:
                font = ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Failed to load font: {e}")
            font = ImageFont.load_default()
        
        # 绘制电子设备检测框（蓝色）
        if device_detections:
            for device in device_detections:
                x1, y1, x2, y2 = [int(v) for v in device['bbox']]
                device_color = (0, 100, 255)  # 蓝色
                draw.rectangle([x1, y1, x2, y2], outline=device_color, width=2)
                
                # 绘制设备标签
                device_label = f"📱{device['name']} {device['confidence']:.2f}"
                try:
                    bbox = draw.textbbox((0, 0), device_label, font=font)
                    label_w = bbox[2] - bbox[0]
                    label_h = bbox[3] - bbox[1]
                except:
                    label_w, label_h = len(device_label) * 10, 20
                
                label_y = max(0, y1 - label_h - 6)
                draw.rectangle([x1, label_y, x1 + label_w + 10, y1], fill=device_color)
                draw.text((x1 + 5, label_y + 2), device_label, fill=(255, 255, 255), font=font)
        
        # 绘制行为检测框
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det.bbox]
            
            # 获取颜色 (RGB)
            color_rgb = BEHAVIOR_CLASSES.get(det.class_id, {}).get('color', (0, 255, 0))
            
            # 根据预警级别调整边框粗细
            thickness = 2 if det.alert_level == 0 else 3
            
            # 绘制边界框
            draw.rectangle([x1, y1, x2, y2], outline=color_rgb, width=thickness)
            
            # 绘制标签
            label = f"{det.class_name_cn} {det.confidence:.2f}"
            
            # 获取文字大小
            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                label_w = bbox[2] - bbox[0]
                label_h = bbox[3] - bbox[1]
            except:
                label_w, label_h = len(label) * 10, 20
            
            # 标签背景
            label_y = max(0, y1 - label_h - 6)
            draw.rectangle([x1, label_y, x1 + label_w + 10, y1], fill=color_rgb)
            
            # 绘制标签文字（白色）
            draw.text((x1 + 5, label_y + 2), label, fill=(255, 255, 255), font=font)
            
            # 如果是预警行为，添加警告标记
            if det.behavior_type == 'warning':
                # 绘制警告圆点
                warn_x, warn_y = x2 - 15, y1 + 15
                draw.ellipse([warn_x - 10, warn_y - 10, warn_x + 10, warn_y + 10], fill=(255, 0, 0))
                draw.text((warn_x - 5, warn_y - 8), "!", fill=(255, 255, 255), font=font)
        
        # 添加统计信息
        warning_count = sum(1 for d in detections if d.behavior_type == 'warning')
        device_count = len(device_detections) if device_detections else 0
        stats_text = f"检测: {len(detections)} | 预警: {warning_count} | 电子设备: {device_count}"
        draw.text((10, 10), stats_text, fill=(0, 255, 0), font=font)
        
        # 转换回OpenCV格式
        result_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return result_image
    
    def detect_base64(self, base64_image: str) -> Tuple[str, DetectionResult]:
        """
        检测Base64编码的图片
        
        Args:
            base64_image: Base64编码的图片字符串
            
        Returns:
            (Base64编码的标注图片, 检测结果)
        """
        # 解码Base64图片
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        image_data = base64.b64decode(base64_image)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Invalid image data")
        
        # 检测
        annotated_image, result = self.detect_image(image)
        
        # 编码为Base64
        _, buffer = cv2.imencode('.jpg', annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{annotated_base64}", result
    
    def detect_base64_fast(self, base64_image: str, skip_detection: bool = False) -> Tuple[str, DetectionResult]:
        """
        快速检测Base64编码的图片（支持跳帧）
        
        Args:
            base64_image: Base64编码的图片字符串
            skip_detection: 是否跳过检测（使用缓存结果）
            
        Returns:
            (Base64编码的标注图片, 检测结果)
        """
        # 更新FPS计数
        self._fps_counter.tick()
        
        # 解码Base64图片
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        image_data = base64.b64decode(base64_image)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Invalid image data")
        
        # 帧计数
        self._frame_count_detection += 1
        
        # 判断是否需要执行检测
        should_detect = (self._frame_count_detection % (self._frame_skip + 1) == 0) or self._last_result is None
        
        if should_detect and not skip_detection:
            # 执行快速检测（禁用低头检测以提高性能）
            with self._detection_lock:
                annotated_image, result = self.detect_image_fast(image)
                self._last_result = result
                self._last_annotated_image = annotated_image
        else:
            # 使用缓存的检测结果，但在当前帧上绘制
            if self._last_result is not None:
                annotated_image = self._draw_detections_simple(image.copy(), self._last_result.detections)
                result = self._last_result
            else:
                annotated_image = image
                result = DetectionResult(
                    detections=[],
                    total_count=0,
                    warning_count=0,
                    normal_count=0,
                    behavior_summary={info['cn_name']: 0 for info in BEHAVIOR_CLASSES.values()},
                    alert_summary={level['cn_name']: 0 for level in ALERT_LEVELS.values()},
                    timestamp=datetime.now().isoformat()
                )
        
        # 在图像上添加FPS信息（使用OpenCV，更快）
        fps = self._fps_counter.get_fps()
        cv2.putText(annotated_image, f"FPS: {fps:.1f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # 编码为Base64（降低质量以提高速度）
        _, buffer = cv2.imencode('.jpg', annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 70])
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{annotated_base64}", result
    
    def detect_image_fast(self, image: np.ndarray) -> Tuple[np.ndarray, DetectionResult]:
        """
        快速检测单张图片（包含低头检测和设备检测）
        
        Args:
            image: OpenCV格式的图片 (BGR)
            
        Returns:
            (标注后的图片, 检测结果)
        """
        detections = []
        device_detections = []
        person_boxes = []
        behavior_summary = {info['cn_name']: 0 for info in BEHAVIOR_CLASSES.values()}
        alert_summary = {level['cn_name']: 0 for level in ALERT_LEVELS.values()}
        
        # 1. 电子设备和人体检测
        if self.device_model is not None and self.device_model_loaded:
            try:
                device_results = self.device_model(
                    image, 
                    conf=0.3, 
                    iou=self.iou_threshold, 
                    imgsz=self.imgsz,
                    half=self.use_half,
                    verbose=False
                )
                for result in device_results:
                    boxes = result.boxes
                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            # 检测电子设备
                            if cls_id in self.ELECTRONIC_DEVICE_CLASSES:
                                device_name = self.ELECTRONIC_DEVICE_CLASSES[cls_id]
                                device_detections.append({
                                    'class_id': cls_id,
                                    'name': device_name,
                                    'confidence': conf,
                                    'bbox': xyxy
                                })
                            
                            # 检测人体（用于低头检测）
                            if cls_id == self.PERSON_CLASS_ID and conf > 0.4:
                                person_boxes.append(xyxy)
            except Exception as e:
                logger.error(f"Device detection error: {e}")
        
        # 2. 行为检测
        if self.model is not None and self.model_loaded:
            try:
                results = self.model(
                    image, 
                    conf=self.confidence_threshold, 
                    iou=self.iou_threshold, 
                    imgsz=self.imgsz,
                    half=self.use_half,
                    verbose=False
                )
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            xyxy = box.xyxy[0].tolist()
                            
                            # 获取类别信息
                            if cls_id in BEHAVIOR_CLASSES:
                                class_info = BEHAVIOR_CLASSES[cls_id]
                            else:
                                continue
                            
                            # 获取预警级别
                            alert_level = 0
                            for level, level_info in ALERT_LEVELS.items():
                                if cls_id in level_info['classes']:
                                    alert_level = level
                                    break
                            
                            detection = Detection(
                                class_id=cls_id,
                                class_name=class_info['name'],
                                class_name_cn=class_info['cn_name'],
                                confidence=round(conf, 3),
                                bbox=[round(v, 1) for v in xyxy],
                                behavior_type=class_info['type'],
                                alert_level=alert_level
                            )
                            detections.append(detection)
                            behavior_summary[class_info['cn_name']] += 1
                            alert_summary[ALERT_LEVELS[alert_level]['cn_name']] += 1
                            
            except Exception as e:
                logger.error(f"Fast detection error: {e}")
        
        # 3. 添加电子设备检测结果
        if device_detections and not any(d.class_id == 5 for d in detections):
            for device in device_detections:
                device_class_info = BEHAVIOR_CLASSES[5]
                detection = Detection(
                    class_id=5,
                    class_name=device_class_info['name'],
                    class_name_cn=f"{device_class_info['cn_name']}({device['name']})",
                    confidence=round(device['confidence'], 3),
                    bbox=[round(v, 1) for v in device['bbox']],
                    behavior_type=device_class_info['type'],
                    alert_level=3
                )
                detections.append(detection)
                behavior_summary[device_class_info['cn_name']] += 1
                alert_summary[ALERT_LEVELS[3]['cn_name']] += 1
        
        # 4. 低头检测
        if person_boxes:
            head_down_results = self._detect_head_down(image, person_boxes, detections)
            for hd in head_down_results:
                head_down_class_info = BEHAVIOR_CLASSES[7]
                detection = Detection(
                    class_id=7,
                    class_name=head_down_class_info['name'],
                    class_name_cn=head_down_class_info['cn_name'],
                    confidence=round(hd['confidence'], 3),
                    bbox=[round(v, 1) for v in hd['bbox']],
                    behavior_type=head_down_class_info['type'],
                    alert_level=1
                )
                detections.append(detection)
                behavior_summary[head_down_class_info['cn_name']] += 1
                alert_summary[ALERT_LEVELS[1]['cn_name']] += 1
        
        # 使用简化的绘制方法
        annotated_image = self._draw_detections_simple(image.copy(), detections, device_detections)
        
        # 统计结果
        warning_count = sum(1 for d in detections if d.behavior_type == 'warning')
        normal_count = sum(1 for d in detections if d.behavior_type == 'normal')
        
        # 更新行为时间统计
        self.time_tracker.update(detections)
        
        result = DetectionResult(
            detections=detections,
            total_count=len(detections),
            warning_count=warning_count,
            normal_count=normal_count,
            behavior_summary=behavior_summary,
            alert_summary=alert_summary,
            timestamp=datetime.now().isoformat(),
            behavior_duration=self.time_tracker.get_duration()
        )
        
        return annotated_image, result
    
    def _draw_detections_simple(self, image: np.ndarray, detections: List[Detection], device_detections: List[Dict] = None) -> np.ndarray:
        """简化的检测框绘制（使用OpenCV，更快）"""
        # 绘制电子设备检测框（蓝色）
        if device_detections:
            for device in device_detections:
                x1, y1, x2, y2 = [int(v) for v in device['bbox']]
                cv2.rectangle(image, (x1, y1), (x2, y2), (255, 100, 0), 2)
                label = f"phone {device['confidence']:.2f}"
                cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 2)
        
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det.bbox]
            
            # 获取颜色 (BGR for OpenCV)
            color_rgb = BEHAVIOR_CLASSES.get(det.class_id, {}).get('color', (0, 255, 0))
            color_bgr = (color_rgb[2], color_rgb[1], color_rgb[0])
            
            # 绘制边界框
            thickness = 3 if det.behavior_type == 'warning' else 2
            cv2.rectangle(image, (x1, y1), (x2, y2), color_bgr, thickness)
            
            # 绘制标签（英文，避免中文字体加载）
            label = f"{det.class_name} {det.confidence:.2f}"
            font_scale = 0.6
            font_thickness = 2
            (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)
            
            # 标签背景
            label_y = max(label_h + 10, y1)
            cv2.rectangle(image, (x1, label_y - label_h - 10), (x1 + label_w + 10, label_y), color_bgr, -1)
            
            # 标签文字
            cv2.putText(image, label, (x1 + 5, label_y - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), font_thickness)
            
            # 预警标记
            if det.behavior_type == 'warning':
                cv2.circle(image, (x2 - 15, y1 + 15), 10, (0, 0, 255), -1)
                cv2.putText(image, "!", (x2 - 20, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 统计信息
        warning_count = sum(1 for d in detections if d.behavior_type == 'warning')
        cv2.rectangle(image, (5, 5), (220, 35), (0, 0, 0), -1)
        cv2.putText(image, f"Detect: {len(detections)} | Warn: {warning_count}", (10, 28), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return image
    
    def set_frame_skip(self, skip: int):
        """设置跳帧数（0表示不跳帧）"""
        self._frame_skip = max(0, min(10, skip))
    
    def get_fps(self) -> float:
        """获取当前FPS"""
        return self._fps_counter.get_fps()
    
    def set_confidence_threshold(self, threshold: float):
        """设置置信度阈值"""
        self.confidence_threshold = max(0.1, min(0.9, threshold))
    
    def set_iou_threshold(self, threshold: float):
        """设置IOU阈值"""
        self.iou_threshold = max(0.1, min(0.9, threshold))
    
    def detect_batch(self, images: List[np.ndarray], batch_size: int = 4) -> List[DetectionResult]:
        """
        批量检测多张图片（GPU 优化）
        
        Args:
            images: 图片列表
            batch_size: 批处理大小，根据 GPU 内存调整
            
        Returns:
            检测结果列表
        """
        if not images:
            return []
        
        results = []
        
        # 分批处理
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            batch_results = self._process_batch(batch_images)
            results.extend(batch_results)
        
        return results
    
    def _process_batch(self, batch_images: List[np.ndarray]) -> List[DetectionResult]:
        """
        处理一个批次的图片
        
        Args:
            batch_images: 批次图片列表
            
        Returns:
            批次检测结果列表
        """
        batch_results = []
        
        if self.model is not None and self.model_loaded:
            try:
                # 对于 YOLO，我们仍然需要逐张处理，但可以优化其他部分
                for image in batch_images:
                    # 使用快速检测方法
                    _, result = self.detect_image_fast(image)
                    batch_results.append(result)
                    
            except Exception as e:
                logger.error(f"Batch detection error: {e}")
                # 降级到单张处理
                for image in batch_images:
                    try:
                        _, result = self.detect_image(image)
                        batch_results.append(result)
                    except Exception as e2:
                        logger.error(f"Single image detection error: {e2}")
                        # 创建空结果
                        empty_result = DetectionResult(
                            detections=[],
                            total_count=0,
                            warning_count=0,
                            normal_count=0,
                            behavior_summary={info['cn_name']: 0 for info in BEHAVIOR_CLASSES.values()},
                            alert_summary={level['cn_name']: 0 for level in ALERT_LEVELS.values()},
                            timestamp=datetime.now().isoformat()
                        )
                        batch_results.append(empty_result)
        else:
            # 模拟检测结果
            for image in batch_images:
                detections, behavior_summary, alert_summary = self._generate_demo_detections(image)
                result = DetectionResult(
                    detections=detections,
                    total_count=len(detections),
                    warning_count=sum(1 for d in detections if d.behavior_type == 'warning'),
                    normal_count=sum(1 for d in detections if d.behavior_type == 'normal'),
                    behavior_summary=behavior_summary,
                    alert_summary=alert_summary,
                    timestamp=datetime.now().isoformat()
                )
                batch_results.append(result)
        
        return batch_results
    
    def detect_video_optimized(self, video_path: str, frame_skip: int = 5, batch_size: int = 4, 
                              progress_callback=None) -> Dict[str, Any]:
        """
        优化的视频检测方法（GPU 加速）
        
        Args:
            video_path: 视频文件路径
            frame_skip: 跳帧数
            batch_size: 批处理大小
            progress_callback: 进度回调函数
            
        Returns:
            检测结果统计
        """
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"开始处理视频: {total_frames} 帧, FPS: {fps}")
        
        # 收集需要处理的帧
        frames_to_process = []
        frame_indices = []
        frame_count = 0
        processed_count = 0
        
        # 第一阶段：收集帧数据
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 跳帧处理
            if frame_count % (frame_skip + 1) != 0:
                continue
            
            frames_to_process.append(frame.copy())
            frame_indices.append(frame_count)
            processed_count += 1
            
            # 当收集到足够的帧或到达视频末尾时，进行批处理
            if len(frames_to_process) >= batch_size:
                # 处理当前批次
                batch_results = self.detect_batch(frames_to_process, batch_size)
                
                # 清空缓存
                frames_to_process = []
                frame_indices = []
                
                # 更新进度
                if progress_callback:
                    progress = processed_count / (total_frames // (frame_skip + 1))
                    progress_callback(progress, processed_count)
        
        # 处理剩余的帧
        if frames_to_process:
            batch_results = self.detect_batch(frames_to_process, len(frames_to_process))
        
        cap.release()
        
        # 统计结果
        total_detections = 0
        warning_count = 0
        behavior_totals = {}
        
        logger.info(f"视频处理完成: 处理了 {processed_count} 帧")
        
        return {
            'total_frames': total_frames,
            'processed_frames': processed_count,
            'video_fps': fps,
            'total_detections': total_detections,
            'warning_count': warning_count,
            'behavior_summary': behavior_totals,
            'processing_time': 0  # 可以添加计时
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        gpu_info = {}
        if self.device != 'cpu':
            try:
                import torch
                gpu_info = {
                    'gpu_name': torch.cuda.get_device_name(0),
                    'gpu_memory_total': f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB",
                    'gpu_memory_allocated': f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}GB",
                    'gpu_memory_cached': f"{torch.cuda.memory_reserved(0) / 1024**3:.2f}GB",
                }
            except:
                pass
        
        return {
            'model_loaded': self.model_loaded,
            'device': self.device,
            'using_gpu': self.device != 'cpu',
            'use_half': self.use_half,
            'imgsz': self.imgsz,
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold,
            'num_classes': len(BEHAVIOR_CLASSES),
            'classes': [{'id': k, **v} for k, v in BEHAVIOR_CLASSES.items()],
            **gpu_info
        }
    
    def set_imgsz(self, imgsz: int):
        """设置推理图像尺寸（影响 GPU 利用率）"""
        self.imgsz = max(320, min(1920, imgsz))
        logger.info(f"Image size set to {self.imgsz}")
    
    def set_half_precision(self, use_half: bool):
        """设置是否使用 FP16 半精度"""
        if self.device == 'cpu':
            logger.warning("FP16 not supported on CPU")
            return
        self.use_half = use_half
        logger.info(f"Half precision set to {self.use_half}")
    
    def get_time_statistics(self) -> Dict[str, Any]:
        """获取行为时间统计"""
        return self.time_tracker.get_statistics()
    
    def reset_time_tracker(self):
        """重置时间统计"""
        self.time_tracker.reset()
    
    # ==================== 数据存储功能 ====================
    # 整合自 model/services/DetectionService.py
    
    def start_session(
        self,
        source_type: str,
        source_path: str = None,
        user_id: int = None,
        schedule_id: int = None
    ) -> int:
        """
        开始新的检测会话
        
        Args:
            source_type: 输入源类型 (image/video/stream)
            source_path: 输入源路径
            user_id: 用户ID
            schedule_id: 课堂安排ID
            
        Returns:
            会话ID
        """
        self._current_session_id = self.data_access.create_session(
            source_type=source_type,
            source_path=source_path,
            user_id=user_id,
            schedule_id=schedule_id
        )
        self._frame_count = 0
        self._record_buffer = []
        self._entry_buffer = []
        
        logger.info(f"Started detection session: {self._current_session_id}")
        return self._current_session_id
    
    def end_session(self, status: str = 'completed') -> Dict[str, Any]:
        """
        结束当前检测会话
        
        Args:
            status: 会话状态 (completed/failed)
            
        Returns:
            会话统计信息
        """
        if self._current_session_id is None:
            logger.warning("No active session to end")
            return {}
        
        # 刷新缓冲区
        self._flush_buffers()
        
        # 更新会话
        self.data_access.update_session(
            session_id=self._current_session_id,
            end_time=datetime.now(),
            total_frames=self._frame_count,
            status=status
        )
        
        # 获取统计信息
        stats = self.data_access.get_session_statistics(self._current_session_id)
        
        logger.info(f"Ended detection session: {self._current_session_id}, frames: {self._frame_count}")
        
        session_id = self._current_session_id
        self._current_session_id = None
        self._frame_count = 0
        
        return stats
    
    @property
    def current_session_id(self) -> Optional[int]:
        """获取当前会话ID"""
        return self._current_session_id
    
    def save_detection_result(
        self,
        frame_id: int,
        timestamp: float,
        detections: List[Dict[str, Any]],
        alert_triggered: bool = False
    ) -> int:
        """
        保存单帧检测结果
        
        Args:
            frame_id: 帧ID
            timestamp: 时间戳
            detections: 检测结果列表，每个检测包含:
                - bbox: (x1, y1, x2, y2)
                - class_id: 类别ID
                - class_name: 类别名称
                - confidence: 置信度
                - behavior_type: 行为类型 (normal/warning)
                - alert_level: 预警级别 (0-3)
            alert_triggered: 是否触发预警
            
        Returns:
            记录ID
        """
        if self._current_session_id is None:
            raise RuntimeError("No active session. Call start_session() first.")
        
        self._frame_count += 1
        
        # 添加到缓冲区
        record = {
            'session_id': self._current_session_id,
            'frame_id': frame_id,
            'timestamp': timestamp,
            'alert_triggered': alert_triggered,
            'detection_count': len(detections)
        }
        self._record_buffer.append(record)
        
        # 暂存检测条目（需要record_id，稍后处理）
        for det in detections:
            entry = {
                'frame_id': frame_id,  # 临时标记
                'bbox': det['bbox'],
                'class_id': det['class_id'],
                'class_name': det['class_name'],
                'confidence': det['confidence'],
                'behavior_type': det['behavior_type'],
                'alert_level': det.get('alert_level', 0)
            }
            self._entry_buffer.append(entry)
        
        # 检查是否需要刷新缓冲区
        if len(self._record_buffer) >= self._buffer_size:
            self._flush_buffers()
        
        return frame_id
    
    def save_detection_batch(
        self,
        results: List[Dict[str, Any]]
    ) -> int:
        """
        批量保存检测结果
        
        Args:
            results: 检测结果列表，每个结果包含:
                - frame_id: 帧ID
                - timestamp: 时间戳
                - detections: 检测列表
                - alert_triggered: 是否触发预警
                
        Returns:
            保存的记录数
        """
        for result in results:
            self.save_detection_result(
                frame_id=result['frame_id'],
                timestamp=result['timestamp'],
                detections=result.get('detections', []),
                alert_triggered=result.get('alert_triggered', False)
            )
        
        return len(results)
    
    def _flush_buffers(self) -> None:
        """刷新缓冲区到数据库"""
        if not self._record_buffer:
            return
        
        # 使用repository模式，而不是直接数据库操作
        try:
            # 批量保存记录
            record_ids = []
            for record in self._record_buffer:
                record_id = self.data_access.detection_repo.create_record(
                    session_id=record['session_id'],
                    frame_id=record['frame_id'],
                    timestamp=record['timestamp'],
                    alert_triggered=record['alert_triggered'],
                    detection_count=record['detection_count']
                )
                record_ids.append(record_id)
            
            # 批量保存条目
            if self._entry_buffer and record_ids:
                # 构建frame_id到record_id的映射
                frame_to_record = {}
                for i, record in enumerate(self._record_buffer):
                    if i < len(record_ids):
                        frame_to_record[record['frame_id']] = record_ids[i]
                
                # 保存条目
                for entry in self._entry_buffer:
                    record_id = frame_to_record.get(entry['frame_id'])
                    if record_id:
                        self.data_access.detection_repo.create_entry(
                            record_id=record_id,
                            bbox=entry['bbox'],
                            class_id=entry['class_id'],
                            class_name=entry['class_name'],
                            confidence=entry['confidence'],
                            behavior_type=entry['behavior_type'],
                            alert_level=entry['alert_level']
                        )
        
        except Exception as e:
            logger.error(f"Failed to flush buffers: {e}")
            raise
        finally:
            # 清空缓冲区
            self._record_buffer = []
            self._entry_buffer = []
    
    def save_alert_result(self, alert_result: Any, frame_id: int = None) -> int:
        """
        保存AlertResult对象
        
        Args:
            alert_result: AlertResult对象（来自alert模块）
            frame_id: 帧ID（如果AlertResult中没有）
            
        Returns:
            记录ID
        """
        # 从AlertResult提取数据
        detections = []
        for det in alert_result.detections:
            detections.append({
                'bbox': det.bbox,
                'class_id': det.class_id,
                'class_name': det.class_name,
                'confidence': det.confidence,
                'behavior_type': det.behavior_type,
                'alert_level': det.alert_level
            })
        
        return self.save_detection_result(
            frame_id=frame_id or alert_result.frame_id,
            timestamp=alert_result.timestamp,
            detections=detections,
            alert_triggered=alert_result.alert_triggered
        )
    
    def get_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """获取会话统计"""
        return self.data_access.get_session_statistics(session_id)
    
    def get_session_detections(
        self,
        session_id: int,
        behavior_type: str = None,
        alert_level: int = None
    ) -> List[Dict[str, Any]]:
        """获取会话的检测结果"""
        return self.data_access.get_behavior_entries(
            session_id=session_id,
            behavior_type=behavior_type,
            alert_level=alert_level
        )
    
    def export_session_json(self, session_id: int) -> str:
        """导出会话数据为JSON"""
        return self.data_access.export_session_to_json(session_id)
    
    def close(self) -> None:
        """关闭服务"""
        if self._current_session_id:
            self.end_session(status='failed')
        self.data_access.close()
    
    def __enter__(self) -> 'DetectionService':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# 全局检测服务实例
_detection_service: Optional[DetectionService] = None

def get_detection_service() -> DetectionService:
    """获取检测服务单例"""
    global _detection_service
    if _detection_service is None:
        _detection_service = DetectionService()
    return _detection_service
