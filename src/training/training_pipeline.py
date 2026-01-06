"""
训练流水线模块
Training pipeline module for YOLOv11 classroom behavior detection model.
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Union

from ultralytics import YOLO

from src.config.behavior_config import BehaviorConfig


# Configure logging
logger = logging.getLogger(__name__)


class TrainingPipeline:
    """
    YOLOv11训练流水线
    Training pipeline for YOLOv11 model with support for different model sizes,
    hyperparameter configuration, training, validation, and model export.
    """
    
    # Supported model sizes
    SUPPORTED_MODELS = ['yolo11n', 'yolo11s', 'yolo11m', 'yolo11l', 'yolo11x']
    
    # Default training hyperparameters
    DEFAULT_CONFIG = {
        'epochs': 100,
        'batch': 16,
        'imgsz': 640,
        'lr0': 0.01,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3.0,
        'warmup_momentum': 0.8,
        'warmup_bias_lr': 0.1,
        'box': 7.5,
        'cls': 0.5,
        'dfl': 1.5,
        'patience': 50,
        'save': True,
        'save_period': -1,
        'cache': False,
        'device': None,  # Auto-select GPU/CPU
        'workers': 8,
        'project': 'runs/detect',
        'name': 'train',
        'exist_ok': False,
        'pretrained': True,
        'optimizer': 'auto',
        'verbose': True,
        'seed': 0,
        'deterministic': True,
        'single_cls': False,
        'rect': False,
        'cos_lr': False,
        'close_mosaic': 10,
        'amp': True,
        'fraction': 1.0,
        'profile': False,
        'freeze': None,
        # Data augmentation parameters
        'hsv_h': 0.015,
        'hsv_s': 0.7,
        'hsv_v': 0.4,
        'degrees': 0.0,
        'translate': 0.1,
        'scale': 0.5,
        'shear': 0.0,
        'perspective': 0.0,
        'flipud': 0.0,
        'fliplr': 0.5,
        'bgr': 0.0,
        'mosaic': 1.0,
        'mixup': 0.0,
        'copy_paste': 0.0,
        'copy_paste_mode': 'flip',
        'auto_augment': 'randaugment',
        'erasing': 0.4,
        'crop_fraction': 1.0,
    }
    
    # Export format mappings
    EXPORT_FORMATS = {
        'onnx': 'onnx',
        'torchscript': 'torchscript',
        'tensorrt': 'engine',
        'openvino': 'openvino',
        'coreml': 'coreml',
        'tflite': 'tflite',
        'pb': 'pb',
        'paddle': 'paddle',
        'ncnn': 'ncnn',
    }
    
    def __init__(
        self,
        model_size: str = 'yolo11m',
        pretrained: bool = True,
        weights: Optional[str] = None
    ):
        """
        初始化训练流水线
        Initialize the training pipeline.
        
        Args:
            model_size: Model size variant ('yolo11n', 'yolo11s', 'yolo11m', 
                       'yolo11l', 'yolo11x'). Default is 'yolo11m'.
            pretrained: Whether to use pretrained weights. Default is True.
            weights: Path to custom weights file. If provided, overrides 
                    model_size and pretrained settings.
        
        Raises:
            ValueError: If model_size is not supported.
        """
        self.config = BehaviorConfig()
        self.training_config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self.model: Optional[YOLO] = None
        self.model_size = model_size
        self.pretrained = pretrained
        self.weights = weights
        self.training_results: Optional[Any] = None
        
        # Validate model size
        if model_size not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model size: {model_size}. "
                f"Supported models: {self.SUPPORTED_MODELS}"
            )
        
        # Initialize model
        self._init_model()
        
        logger.info(f"TrainingPipeline initialized with model: {model_size}")

    def _init_model(self) -> None:
        """
        初始化YOLO模型
        Initialize the YOLO model based on configuration.
        """
        if self.weights:
            # Load from custom weights
            logger.info(f"Loading model from weights: {self.weights}")
            self.model = YOLO(self.weights)
        elif self.pretrained:
            # Load pretrained model
            model_name = f"{self.model_size}.pt"
            logger.info(f"Loading pretrained model: {model_name}")
            self.model = YOLO(model_name)
        else:
            # Load model architecture only (no pretrained weights)
            model_name = f"{self.model_size}.yaml"
            logger.info(f"Loading model architecture: {model_name}")
            self.model = YOLO(model_name)
    
    def configure(
        self,
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        img_size: Optional[int] = None,
        lr0: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        配置训练超参数
        Configure training hyperparameters.
        
        Args:
            epochs: Number of training epochs.
            batch_size: Batch size for training.
            img_size: Input image size.
            lr0: Initial learning rate.
            **kwargs: Additional hyperparameters to override defaults.
        
        Returns:
            Dictionary of current training configuration.
        """
        # Update specific parameters if provided
        if epochs is not None:
            self.training_config['epochs'] = epochs
        if batch_size is not None:
            self.training_config['batch'] = batch_size
        if img_size is not None:
            self.training_config['imgsz'] = img_size
        if lr0 is not None:
            self.training_config['lr0'] = lr0
        
        # Update any additional parameters
        for key, value in kwargs.items():
            if key in self.training_config:
                self.training_config[key] = value
            else:
                logger.warning(f"Unknown parameter: {key}. Adding to config anyway.")
                self.training_config[key] = value
        
        logger.info(f"Training configuration updated: epochs={self.training_config['epochs']}, "
                   f"batch={self.training_config['batch']}, imgsz={self.training_config['imgsz']}")
        
        return self.training_config.copy()
    
    def configure_augmentation(
        self,
        hsv_h: Optional[float] = None,
        hsv_s: Optional[float] = None,
        hsv_v: Optional[float] = None,
        degrees: Optional[float] = None,
        translate: Optional[float] = None,
        scale: Optional[float] = None,
        shear: Optional[float] = None,
        flipud: Optional[float] = None,
        fliplr: Optional[float] = None,
        mosaic: Optional[float] = None,
        mixup: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        配置数据增强参数
        Configure data augmentation parameters.
        
        Args:
            hsv_h: HSV-Hue augmentation (fraction).
            hsv_s: HSV-Saturation augmentation (fraction).
            hsv_v: HSV-Value augmentation (fraction).
            degrees: Image rotation (+/- deg).
            translate: Image translation (+/- fraction).
            scale: Image scale (+/- gain).
            shear: Image shear (+/- deg).
            flipud: Image flip up-down (probability).
            fliplr: Image flip left-right (probability).
            mosaic: Mosaic augmentation (probability).
            mixup: MixUp augmentation (probability).
            **kwargs: Additional augmentation parameters.
        
        Returns:
            Dictionary of current augmentation configuration.
        """
        aug_params = {
            'hsv_h': hsv_h,
            'hsv_s': hsv_s,
            'hsv_v': hsv_v,
            'degrees': degrees,
            'translate': translate,
            'scale': scale,
            'shear': shear,
            'flipud': flipud,
            'fliplr': fliplr,
            'mosaic': mosaic,
            'mixup': mixup,
        }
        
        # Update only non-None values
        for key, value in aug_params.items():
            if value is not None:
                self.training_config[key] = value
        
        # Update any additional parameters
        for key, value in kwargs.items():
            self.training_config[key] = value
        
        logger.info("Data augmentation configuration updated")
        
        # Return augmentation-related config
        aug_keys = ['hsv_h', 'hsv_s', 'hsv_v', 'degrees', 'translate', 'scale',
                   'shear', 'flipud', 'fliplr', 'mosaic', 'mixup', 'copy_paste',
                   'auto_augment', 'erasing']
        return {k: self.training_config[k] for k in aug_keys if k in self.training_config}

    def train(
        self,
        data_yaml: str,
        resume: bool = False,
        resume_weights: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行训练
        Execute model training.
        
        Args:
            data_yaml: Path to data.yaml configuration file.
            resume: Whether to resume training from last checkpoint.
            resume_weights: Path to weights file for resuming training.
                          If resume=True and this is None, uses last.pt.
        
        Returns:
            Dictionary containing training results and metrics.
        
        Raises:
            FileNotFoundError: If data_yaml file does not exist.
            RuntimeError: If training fails.
        """
        # Validate data.yaml exists
        data_path = Path(data_yaml)
        if not data_path.exists():
            raise FileNotFoundError(f"Data configuration file not found: {data_yaml}")
        
        logger.info(f"Starting training with data: {data_yaml}")
        logger.info(f"Training config: epochs={self.training_config['epochs']}, "
                   f"batch={self.training_config['batch']}, imgsz={self.training_config['imgsz']}")
        
        # Handle resume training
        if resume:
            if resume_weights:
                logger.info(f"Resuming training from: {resume_weights}")
                self.model = YOLO(resume_weights)
            else:
                # Try to find last.pt in the project directory
                logger.info("Resuming training from last checkpoint")
        
        try:
            # Prepare training arguments
            train_args = self.training_config.copy()
            train_args['data'] = str(data_yaml)
            train_args['resume'] = resume
            
            # Execute training
            self.training_results = self.model.train(**train_args)
            
            # Extract and return results
            results = self._extract_training_results()
            logger.info("Training completed successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise RuntimeError(f"Training failed: {str(e)}") from e
    
    def _extract_training_results(self) -> Dict[str, Any]:
        """
        提取训练结果
        Extract training results and metrics.
        
        Returns:
            Dictionary containing training metrics and paths.
        """
        if self.training_results is None:
            return {}
        
        results = {
            'save_dir': str(self.training_results.save_dir) if hasattr(self.training_results, 'save_dir') else None,
            'best_weights': None,
            'last_weights': None,
            'metrics': {},
        }
        
        # Get weights paths
        if hasattr(self.training_results, 'save_dir'):
            save_dir = Path(self.training_results.save_dir)
            weights_dir = save_dir / 'weights'
            if weights_dir.exists():
                best_path = weights_dir / 'best.pt'
                last_path = weights_dir / 'last.pt'
                if best_path.exists():
                    results['best_weights'] = str(best_path)
                if last_path.exists():
                    results['last_weights'] = str(last_path)
        
        # Extract metrics if available
        if hasattr(self.training_results, 'results_dict'):
            results['metrics'] = self.training_results.results_dict
        
        return results
    
    def validate(
        self,
        weights: Optional[str] = None,
        data_yaml: Optional[str] = None,
        split: str = 'val',
        conf: float = 0.001,
        iou: float = 0.6,
        **kwargs
    ) -> Dict[str, Any]:
        """
        在验证集上评估模型
        Validate model on validation/test set.
        
        Args:
            weights: Path to model weights. If None, uses current model.
            data_yaml: Path to data.yaml. If None, uses training data.
            split: Dataset split to validate on ('val' or 'test').
            conf: Confidence threshold for validation.
            iou: IoU threshold for NMS.
            **kwargs: Additional validation parameters.
        
        Returns:
            Dictionary containing validation metrics.
        """
        # Load weights if provided
        if weights:
            logger.info(f"Loading weights for validation: {weights}")
            model = YOLO(weights)
        else:
            model = self.model
        
        logger.info(f"Running validation on {split} split")
        
        try:
            # Prepare validation arguments
            val_args = {
                'split': split,
                'conf': conf,
                'iou': iou,
                'verbose': True,
            }
            
            if data_yaml:
                val_args['data'] = data_yaml
            
            val_args.update(kwargs)
            
            # Execute validation
            results = model.val(**val_args)
            
            # Extract metrics
            metrics = self._extract_validation_metrics(results)
            logger.info(f"Validation completed. mAP50: {metrics.get('mAP50', 'N/A')}, "
                       f"mAP50-95: {metrics.get('mAP50-95', 'N/A')}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            raise RuntimeError(f"Validation failed: {str(e)}") from e

    def _extract_validation_metrics(self, results: Any) -> Dict[str, Any]:
        """
        提取验证指标
        Extract validation metrics from results.
        
        Args:
            results: Validation results object from YOLO.
        
        Returns:
            Dictionary containing validation metrics.
        """
        metrics = {}
        
        if hasattr(results, 'box'):
            box = results.box
            metrics['mAP50'] = float(box.map50) if hasattr(box, 'map50') else None
            metrics['mAP50-95'] = float(box.map) if hasattr(box, 'map') else None
            metrics['precision'] = float(box.mp) if hasattr(box, 'mp') else None
            metrics['recall'] = float(box.mr) if hasattr(box, 'mr') else None
            
            # Per-class metrics
            if hasattr(box, 'ap50'):
                metrics['ap50_per_class'] = box.ap50.tolist() if hasattr(box.ap50, 'tolist') else list(box.ap50)
            if hasattr(box, 'ap'):
                metrics['ap_per_class'] = box.ap.tolist() if hasattr(box.ap, 'tolist') else list(box.ap)
        
        # Add class names
        metrics['class_names'] = self.config.get_class_names()
        
        return metrics
    
    def export(
        self,
        weights: Optional[str] = None,
        format: str = 'onnx',
        imgsz: Optional[int] = None,
        half: bool = False,
        dynamic: bool = False,
        simplify: bool = True,
        opset: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        导出模型为指定格式
        Export model to specified format.
        
        Args:
            weights: Path to model weights. If None, uses current model.
            format: Export format ('onnx', 'torchscript', 'tensorrt', 
                   'openvino', 'coreml', 'tflite', 'pb', 'paddle', 'ncnn').
            imgsz: Image size for export. If None, uses training config.
            half: Use FP16 half-precision.
            dynamic: Enable dynamic input shapes (ONNX only).
            simplify: Simplify ONNX model.
            opset: ONNX opset version.
            **kwargs: Additional export parameters.
        
        Returns:
            Path to exported model file.
        
        Raises:
            ValueError: If format is not supported.
            RuntimeError: If export fails.
        """
        # Validate format
        format_lower = format.lower()
        if format_lower not in self.EXPORT_FORMATS:
            raise ValueError(
                f"Unsupported export format: {format}. "
                f"Supported formats: {list(self.EXPORT_FORMATS.keys())}"
            )
        
        # Load weights if provided
        if weights:
            logger.info(f"Loading weights for export: {weights}")
            model = YOLO(weights)
        else:
            model = self.model
        
        # Determine image size
        if imgsz is None:
            imgsz = self.training_config.get('imgsz', 640)
        
        logger.info(f"Exporting model to {format} format, imgsz={imgsz}")
        
        try:
            # Prepare export arguments
            export_args = {
                'format': format_lower,
                'imgsz': imgsz,
                'half': half,
                'dynamic': dynamic,
                'simplify': simplify,
            }
            
            if opset is not None:
                export_args['opset'] = opset
            
            export_args.update(kwargs)
            
            # Execute export
            export_path = model.export(**export_args)
            
            logger.info(f"Model exported successfully to: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise RuntimeError(f"Export failed: {str(e)}") from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        Get model information.
        
        Returns:
            Dictionary containing model information.
        """
        info = {
            'model_size': self.model_size,
            'pretrained': self.pretrained,
            'weights': self.weights,
            'num_classes': self.config.get_num_classes(),
            'class_names': self.config.get_class_names(),
        }
        
        if self.model is not None:
            info['model_type'] = type(self.model).__name__
            if hasattr(self.model, 'names'):
                info['model_classes'] = self.model.names
        
        return info
    
    def get_training_config(self) -> Dict[str, Any]:
        """
        获取当前训练配置
        Get current training configuration.
        
        Returns:
            Dictionary of current training configuration.
        """
        return self.training_config.copy()
    
    def reset_config(self) -> None:
        """
        重置训练配置为默认值
        Reset training configuration to defaults.
        """
        self.training_config = self.DEFAULT_CONFIG.copy()
        logger.info("Training configuration reset to defaults")
