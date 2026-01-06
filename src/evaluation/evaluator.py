"""
模型评估器模块
Model evaluator module for classroom behavior detection.
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging
import yaml
import numpy as np

from .models import Detection, EvaluationResult
from .metrics import MetricsCalculator
from .report import ReportGenerator


logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    模型评估器主类
    Main evaluator class for YOLOv11 classroom behavior detection model.
    """
    
    NUM_CLASSES = 7
    CLASS_NAMES = [
        'handrise', 'read', 'write', 'sleep',
        'stand', 'using_electronic_devices', 'talk'
    ]
    CLASS_NAMES_CN = [
        '举手', '阅读', '书写', '睡觉',
        '站立', '使用电子设备', '交谈'
    ]
    
    def __init__(self, weights_path: str, device: str = 'auto'):
        """
        初始化评估器
        
        Args:
            weights_path: 模型权重文件路径
            device: 运行设备 ('auto', 'cpu', '0', '0,1' 等)
        """
        self.weights_path = weights_path
        self.device = device
        self.model = None
        self.metrics_calculator = MetricsCalculator(num_classes=self.NUM_CLASSES)
    
    def load_model(self) -> bool:
        """
        加载并验证模型
        
        Returns:
            True 如果加载成功
            
        Raises:
            FileNotFoundError: 如果权重文件不存在
            ValueError: 如果模型格式无效
        """
        weights_path = Path(self.weights_path)
        
        if not weights_path.exists():
            raise FileNotFoundError(f"模型权重文件不存在: {self.weights_path}")
        
        try:
            from ultralytics import YOLO
            
            logger.info(f"正在加载模型: {self.weights_path}")
            self.model = YOLO(str(weights_path))
            
            # 验证模型类别数
            if hasattr(self.model, 'names'):
                num_classes = len(self.model.names)
                if num_classes != self.NUM_CLASSES:
                    logger.warning(
                        f"模型类别数 ({num_classes}) 与预期 ({self.NUM_CLASSES}) 不匹配，继续执行"
                    )
            
            logger.info("模型加载成功")
            return True
            
        except ImportError:
            raise ImportError("请安装 ultralytics 库: pip install ultralytics")
        except Exception as e:
            raise ValueError(f"模型加载失败: {e}")
    
    def _parse_data_yaml(self, data_yaml: str) -> Dict:
        """
        解析数据集配置文件
        
        Args:
            data_yaml: data.yaml 文件路径
            
        Returns:
            解析后的配置字典
            
        Raises:
            FileNotFoundError: 如果配置文件不存在
            ValueError: 如果配置文件格式无效
        """
        data_path = Path(data_yaml).resolve()
        
        if not data_path.exists():
            raise FileNotFoundError(f"数据集配置文件不存在: {data_yaml}")
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 验证必需字段
            required_fields = ['path', 'train', 'val', 'names', 'nc']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"配置文件缺少必需字段: {field}")
            
            # 解析路径 - 优先使用配置中的路径，如果不存在则使用相对于 data.yaml 的路径
            base_path = Path(config['path'])
            
            # 如果配置的路径不存在，尝试使用 data.yaml 所在目录
            if not base_path.exists():
                base_path = data_path.parent
                logger.info(f"配置路径不存在，使用 data.yaml 所在目录: {base_path}")
            
            config['train_path'] = base_path / config['train']
            config['val_path'] = base_path / config['val']
            
            if 'test' in config:
                config['test_path'] = base_path / config['test']
            
            logger.info(f"数据集配置解析成功: {data_yaml}")
            logger.info(f"  训练集: {config['train_path']}")
            logger.info(f"  验证集: {config['val_path']}")
            
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析错误: {e}")
    
    def _load_ground_truths(self, images_dir: Path, labels_dir: Path) -> Tuple[List[str], List[Detection]]:
        """
        加载真实标签
        
        Args:
            images_dir: 图像目录
            labels_dir: 标签目录
            
        Returns:
            (image_paths, ground_truths) 图像路径列表和真实标签列表
        """
        image_paths = []
        ground_truths = []
        
        # 支持的图像格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        
        for img_path in images_dir.iterdir():
            if img_path.suffix.lower() not in image_extensions:
                continue
            
            image_paths.append(str(img_path))
            image_id = img_path.stem
            
            # 查找对应的标签文件
            label_path = labels_dir / f"{image_id}.txt"
            
            if label_path.exists():
                try:
                    with open(label_path, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                class_id = int(parts[0])
                                # YOLO 格式: class x_center y_center width height
                                x_center, y_center, w, h = map(float, parts[1:5])
                                # 转换为 [x1, y1, x2, y2] 格式（归一化坐标）
                                x1 = x_center - w / 2
                                y1 = y_center - h / 2
                                x2 = x_center + w / 2
                                y2 = y_center + h / 2
                                
                                ground_truths.append(Detection(
                                    class_id=class_id,
                                    confidence=1.0,
                                    bbox=[x1, y1, x2, y2],
                                    image_id=image_id,
                                ))
                except Exception as e:
                    logger.warning(f"读取标签文件失败 {label_path}: {e}")
        
        return image_paths, ground_truths
    
    def evaluate(
        self,
        data_yaml: str,
        split: str = 'val',
        conf: float = 0.25,
        iou: float = 0.45,
        verbose: bool = False,
        output_dir: Optional[str] = None
    ) -> EvaluationResult:
        """
        执行模型评估
        
        Args:
            data_yaml: 数据集配置文件路径
            split: 数据集分割 ('val' 或 'test')
            conf: 置信度阈值
            iou: NMS IoU 阈值
            verbose: 是否输出详细信息
            output_dir: 输出目录，用于保存报告和可视化
            
        Returns:
            EvaluationResult 包含所有评估结果
        """
        # 加载模型
        if self.model is None:
            self.load_model()
        
        # 解析数据集配置
        config = self._parse_data_yaml(data_yaml)
        
        # 获取数据集路径
        if split == 'val':
            images_dir = config['val_path']
        elif split == 'test':
            if 'test_path' not in config:
                raise ValueError("数据集配置中没有 test 分割")
            images_dir = config['test_path']
        else:
            raise ValueError(f"无效的分割: {split}，必须是 'val' 或 'test'")
        
        # 标签目录
        labels_dir = images_dir.parent.parent / 'labels' / split
        
        logger.info(f"开始评估 {split} 数据集...")
        logger.info(f"  图像目录: {images_dir}")
        logger.info(f"  标签目录: {labels_dir}")
        
        # 加载真实标签
        image_paths, ground_truths = self._load_ground_truths(images_dir, labels_dir)
        logger.info(f"  图像数量: {len(image_paths)}")
        logger.info(f"  真实标签数量: {len(ground_truths)}")
        
        # 执行推理
        predictions = []
        processed = 0
        
        for img_path in image_paths:
            try:
                results = self.model.predict(
                    img_path,
                    conf=conf,
                    iou=iou,
                    device=self.device if self.device != 'auto' else None,
                    verbose=False,
                )
                
                image_id = Path(img_path).stem
                
                for result in results:
                    if result.boxes is not None:
                        boxes = result.boxes
                        for i in range(len(boxes)):
                            # 获取归一化坐标
                            xyxyn = boxes.xyxyn[i].cpu().numpy()
                            cls = int(boxes.cls[i].cpu().numpy())
                            conf_score = float(boxes.conf[i].cpu().numpy())
                            
                            predictions.append(Detection(
                                class_id=cls,
                                confidence=conf_score,
                                bbox=xyxyn.tolist(),
                                image_id=image_id,
                            ))
                
                processed += 1
                if verbose and processed % 100 == 0:
                    logger.info(f"  已处理 {processed}/{len(image_paths)} 张图像")
                    
            except Exception as e:
                logger.warning(f"处理图像失败 {img_path}: {e}")
                continue
        
        logger.info(f"  预测数量: {len(predictions)}")
        
        # 计算指标
        logger.info("计算评估指标...")
        overall_metrics = self.metrics_calculator.compute_overall_metrics(
            predictions, ground_truths
        )
        per_class_metrics = self.metrics_calculator.compute_per_class_metrics(
            predictions, ground_truths
        )
        group_metrics = self.metrics_calculator.compute_group_metrics(per_class_metrics)
        
        # 生成混淆矩阵
        confusion_matrix = self.metrics_calculator.generate_confusion_matrix(
            predictions, ground_truths, normalize=True
        )
        confused_pairs = self.metrics_calculator.analyze_confusion(confusion_matrix)
        
        # 创建评估结果
        result = EvaluationResult(
            weights_path=self.weights_path,
            data_yaml=data_yaml,
            split=split,
            evaluation_date=datetime.now(),
            conf_threshold=conf,
            iou_threshold=iou,
            overall_metrics=overall_metrics,
            per_class_metrics=per_class_metrics,
            group_metrics=group_metrics,
            confusion_matrix=confusion_matrix,
            confused_pairs=confused_pairs,
            class_names=self.CLASS_NAMES,
            class_names_cn=self.CLASS_NAMES_CN,
        )
        
        # 生成报告
        if output_dir:
            logger.info(f"生成评估报告到: {output_dir}")
            report_generator = ReportGenerator(output_dir)
            report_generator.generate_json_report(result)
            report_generator.generate_markdown_report(result)
            report_generator.generate_confusion_heatmap(
                confusion_matrix, self.CLASS_NAMES_CN
            )
            report_generator.generate_metrics_bar_chart(
                per_class_metrics, self.CLASS_NAMES_CN
            )
        
        logger.info("评估完成!")
        return result
