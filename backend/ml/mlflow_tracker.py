"""
MLflow追踪器模块
MLflow tracker for experiment tracking and model management
"""
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

# 尝试导入MLflow
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not installed. ML tracking will be disabled.")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class MLflowTracker:
    """
    MLflow追踪器 - 监控机器学习实验和模型
    
    功能:
    - 实验和运行管理
    - 参数、指标、产物记录
    - 模型注册和加载
    - 实验比较和最佳模型选择
    """
    
    def __init__(
        self,
        tracking_uri: str = None,
        experiment_name: str = "alert_ml"
    ):
        """
        初始化MLflow追踪器
        
        Args:
            tracking_uri: MLflow服务器地址，默认使用本地
            experiment_name: 实验名称
        """
        self.tracking_uri = tracking_uri or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "runs/mlflow"
        )
        self.experiment_name = experiment_name
        self.current_run_id = None
        self._client = None
        self._experiment_id = None
        
        if MLFLOW_AVAILABLE:
            self._setup_mlflow()
    
    def _setup_mlflow(self):
        """设置MLflow"""
        try:
            # 确保目录存在
            os.makedirs(self.tracking_uri, exist_ok=True)
            
            # 设置tracking URI
            mlflow.set_tracking_uri(f"file://{self.tracking_uri}")
            
            # 创建或获取实验
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                self._experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    artifact_location=os.path.join(self.tracking_uri, "artifacts")
                )
            else:
                self._experiment_id = experiment.experiment_id
            
            mlflow.set_experiment(self.experiment_name)
            self._client = MlflowClient()
            
            logger.info(f"MLflow initialized: tracking_uri={self.tracking_uri}, experiment={self.experiment_name}")
        except Exception as e:
            logger.error(f"Failed to setup MLflow: {e}")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """检查MLflow是否可用"""
        return MLFLOW_AVAILABLE and self._client is not None
    
    def start_run(
        self,
        run_name: str,
        tags: Dict[str, str] = None
    ) -> Optional[str]:
        """
        开始一个新的MLflow运行
        
        Args:
            run_name: 运行名称
            tags: 运行标签
            
        Returns:
            run_id 或 None
        """
        if not self.is_available:
            logger.warning("MLflow not available, skipping run start")
            return None
        
        try:
            run = mlflow.start_run(run_name=run_name, tags=tags)
            self.current_run_id = run.info.run_id
            logger.info(f"Started MLflow run: {run_name} (id={self.current_run_id})")
            return self.current_run_id
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            return None
    
    def log_params(self, params: Dict[str, Any]) -> None:
        """
        记录模型参数
        
        Args:
            params: 参数字典
        """
        if not self.is_available:
            return
        
        try:
            # MLflow参数值必须是字符串
            str_params = {k: str(v) for k, v in params.items()}
            mlflow.log_params(str_params)
            logger.debug(f"Logged params: {list(params.keys())}")
        except Exception as e:
            logger.error(f"Failed to log params: {e}")
    
    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: int = None
    ) -> None:
        """
        记录性能指标
        
        Args:
            metrics: 指标字典
            step: 步骤编号
        """
        if not self.is_available:
            return
        
        try:
            for key, value in metrics.items():
                mlflow.log_metric(key, value, step=step)
            logger.debug(f"Logged metrics: {list(metrics.keys())}")
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")
    
    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: str = None
    ) -> Optional[str]:
        """
        记录并注册模型
        
        Args:
            model: 训练好的模型
            artifact_path: 模型存储路径
            registered_model_name: 注册的模型名称
            
        Returns:
            模型URI 或 None
        """
        if not self.is_available:
            return None
        
        try:
            # 根据模型类型选择合适的日志方法
            model_info = None
            
            # 尝试sklearn
            try:
                import sklearn
                if hasattr(model, 'fit') and hasattr(model, 'predict'):
                    model_info = mlflow.sklearn.log_model(
                        model,
                        artifact_path,
                        registered_model_name=registered_model_name
                    )
            except ImportError:
                pass
            
            if model_info is None:
                # 使用通用方法
                import pickle
                import tempfile
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
                    pickle.dump(model, f)
                    temp_path = f.name
                
                mlflow.log_artifact(temp_path, artifact_path)
                os.unlink(temp_path)
                
                model_uri = f"runs:/{self.current_run_id}/{artifact_path}"
                logger.info(f"Logged model to {model_uri}")
                return model_uri
            
            model_uri = model_info.model_uri
            logger.info(f"Logged model to {model_uri}")
            return model_uri
            
        except Exception as e:
            logger.error(f"Failed to log model: {e}")
            return None
    
    def log_artifacts(
        self,
        local_dir: str,
        artifact_path: str = None
    ) -> None:
        """
        记录训练产物
        
        Args:
            local_dir: 本地目录
            artifact_path: 存储路径
        """
        if not self.is_available:
            return
        
        try:
            mlflow.log_artifacts(local_dir, artifact_path)
            logger.debug(f"Logged artifacts from {local_dir}")
        except Exception as e:
            logger.error(f"Failed to log artifacts: {e}")
    
    def log_artifact(self, local_path: str, artifact_path: str = None) -> None:
        """记录单个产物文件"""
        if not self.is_available:
            return
        
        try:
            mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            logger.error(f"Failed to log artifact: {e}")
    
    def log_dataset(
        self,
        dataset,
        name: str,
        context: str = "training"
    ) -> None:
        """
        记录数据集信息
        
        Args:
            dataset: 数据集 (DataFrame或dict)
            name: 数据集名称
            context: 上下文 (training/validation/test)
        """
        if not self.is_available:
            return
        
        try:
            # 记录数据集统计信息
            if PANDAS_AVAILABLE and hasattr(dataset, 'shape'):
                stats = {
                    f"{name}_rows": dataset.shape[0],
                    f"{name}_cols": dataset.shape[1] if len(dataset.shape) > 1 else 1,
                    f"{name}_context": context
                }
                self.log_params(stats)
            elif isinstance(dataset, dict):
                self.log_params({f"{name}_keys": str(list(dataset.keys()))})
        except Exception as e:
            logger.error(f"Failed to log dataset: {e}")
    
    def end_run(self, status: str = "FINISHED") -> None:
        """
        结束当前运行
        
        Args:
            status: 运行状态 (FINISHED/FAILED/KILLED)
        """
        if not self.is_available:
            return
        
        try:
            mlflow.end_run(status=status)
            logger.info(f"Ended MLflow run with status: {status}")
            self.current_run_id = None
        except Exception as e:
            logger.error(f"Failed to end run: {e}")
    
    def get_best_model(
        self,
        metric: str = "f1_score",
        ascending: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        获取最佳模型
        
        Args:
            metric: 评估指标
            ascending: 是否升序排列
            
        Returns:
            最佳模型信息
        """
        if not self.is_available:
            return None
        
        try:
            runs = self._client.search_runs(
                experiment_ids=[self._experiment_id],
                filter_string="",
                order_by=[f"metrics.{metric} {'ASC' if ascending else 'DESC'}"],
                max_results=1
            )
            
            if not runs:
                return None
            
            best_run = runs[0]
            return {
                'run_id': best_run.info.run_id,
                'run_name': best_run.info.run_name,
                'metrics': best_run.data.metrics,
                'params': best_run.data.params,
                'artifact_uri': best_run.info.artifact_uri
            }
        except Exception as e:
            logger.error(f"Failed to get best model: {e}")
            return None
    
    def compare_runs(
        self,
        run_ids: List[str],
        metrics: List[str]
    ) -> Optional[Dict]:
        """
        比较多个运行的性能
        
        Args:
            run_ids: 运行ID列表
            metrics: 要比较的指标列表
            
        Returns:
            比较结果
        """
        if not self.is_available:
            return None
        
        try:
            results = []
            for run_id in run_ids:
                run = self._client.get_run(run_id)
                row = {'run_id': run_id, 'run_name': run.info.run_name}
                for metric in metrics:
                    row[metric] = run.data.metrics.get(metric)
                results.append(row)
            
            return {'runs': results, 'metrics': metrics}
        except Exception as e:
            logger.error(f"Failed to compare runs: {e}")
            return None
    
    def load_model(self, model_uri: str) -> Optional[Any]:
        """
        加载已注册的模型
        
        Args:
            model_uri: 模型URI
            
        Returns:
            加载的模型
        """
        if not self.is_available:
            return None
        
        try:
            # 尝试sklearn加载
            try:
                return mlflow.sklearn.load_model(model_uri)
            except:
                pass
            
            # 尝试pyfunc加载
            return mlflow.pyfunc.load_model(model_uri)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def list_experiments(self) -> List[Dict]:
        """列出所有实验"""
        if not self.is_available:
            return []
        
        try:
            experiments = self._client.search_experiments()
            return [
                {
                    'experiment_id': exp.experiment_id,
                    'name': exp.name,
                    'artifact_location': exp.artifact_location,
                    'lifecycle_stage': exp.lifecycle_stage
                }
                for exp in experiments
            ]
        except Exception as e:
            logger.error(f"Failed to list experiments: {e}")
            return []
    
    def list_runs(
        self,
        experiment_id: str = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        列出实验的运行记录
        
        Args:
            experiment_id: 实验ID，默认使用当前实验
            max_results: 最大返回数量
            
        Returns:
            运行记录列表
        """
        if not self.is_available:
            return []
        
        try:
            exp_id = experiment_id or self._experiment_id
            runs = self._client.search_runs(
                experiment_ids=[exp_id],
                max_results=max_results,
                order_by=["start_time DESC"]
            )
            
            return [
                {
                    'run_id': run.info.run_id,
                    'run_name': run.info.run_name,
                    'status': run.info.status,
                    'start_time': datetime.fromtimestamp(run.info.start_time / 1000).isoformat() if run.info.start_time else None,
                    'end_time': datetime.fromtimestamp(run.info.end_time / 1000).isoformat() if run.info.end_time else None,
                    'metrics': run.data.metrics,
                    'params': run.data.params
                }
                for run in runs
            ]
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []
    
    def get_run(self, run_id: str) -> Optional[Dict]:
        """获取运行详情"""
        if not self.is_available:
            return None
        
        try:
            run = self._client.get_run(run_id)
            return {
                'run_id': run.info.run_id,
                'run_name': run.info.run_name,
                'experiment_id': run.info.experiment_id,
                'status': run.info.status,
                'start_time': datetime.fromtimestamp(run.info.start_time / 1000).isoformat() if run.info.start_time else None,
                'end_time': datetime.fromtimestamp(run.info.end_time / 1000).isoformat() if run.info.end_time else None,
                'metrics': run.data.metrics,
                'params': run.data.params,
                'tags': run.data.tags,
                'artifact_uri': run.info.artifact_uri
            }
        except Exception as e:
            logger.error(f"Failed to get run: {e}")
            return None


# 单例模式
_tracker_instance = None


def get_mlflow_tracker(experiment_name: str = "alert_ml") -> MLflowTracker:
    """获取MLflow追踪器单例"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = MLflowTracker(experiment_name=experiment_name)
    return _tracker_instance
