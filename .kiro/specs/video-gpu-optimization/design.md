# 视频处理GPU优化设计文档

## 设计概述

本文档详细描述了视频处理GPU优化功能的技术设计，包括系统架构、核心算法、API设计和用户界面设计。该设计旨在最大化GPU利用率，显著提升视频处理性能。

## 系统架构

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   后端API       │    │   检测服务      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │GPU状态卡片  │ │◄──►│ │GPU信息接口  │ │◄──►│ │GPU监控模块  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │模式选择对话框│ │◄──►│ │优化检测接口  │ │◄──►│ │批处理引擎   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │设置对话框   │ │◄──►│ │设置管理接口  │ │◄──►│ │配置管理器   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   YOLO模型      │
                                               │                 │
                                               │ ┌─────────────┐ │
                                               │ │行为检测模型 │ │
                                               │ └─────────────┘ │
                                               │ ┌─────────────┐ │
                                               │ │设备检测模型 │ │
                                               │ └─────────────┘ │
                                               └─────────────────┘
```

### 核心组件设计

#### 1. GPU监控模块 (GPUMonitor)

**职责**: 监控GPU状态，提供实时的硬件信息

```python
class GPUMonitor:
    def get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU基本信息"""
        
    def get_memory_usage(self) -> Dict[str, float]:
        """获取显存使用情况"""
        
    def is_gpu_available(self) -> bool:
        """检查GPU是否可用"""
        
    def get_optimal_batch_size(self, image_size: int) -> int:
        """根据显存计算最优批大小"""
```

#### 2. 批处理引擎 (BatchProcessor)

**职责**: 实现高效的GPU批处理算法

```python
class BatchProcessor:
    def __init__(self, model, batch_size: int = 8):
        self.model = model
        self.batch_size = batch_size
        self.frame_buffer = []
        
    def add_frame(self, frame: np.ndarray) -> Optional[List[DetectionResult]]:
        """添加帧到批处理缓冲区"""
        
    def process_batch(self, frames: List[np.ndarray]) -> List[DetectionResult]:
        """批量处理帧"""
        
    def flush(self) -> List[DetectionResult]:
        """处理剩余帧"""
```

#### 3. 优化策略管理器 (OptimizationManager)

**职责**: 管理各种优化策略的启用和配置

```python
class OptimizationManager:
    def __init__(self):
        self.strategies = {
            'fp16': FP16Strategy(),
            'batch_processing': BatchProcessingStrategy(),
            'dynamic_sizing': DynamicSizingStrategy(),
            'smart_frame_skip': SmartFrameSkipStrategy()
        }
        
    def apply_optimizations(self, config: Dict) -> None:
        """应用优化策略"""
        
    def get_optimization_report(self) -> Dict:
        """生成优化报告"""
```

## 核心算法设计

### 1. 自适应批处理算法

```python
def adaptive_batch_processing(frames: List[np.ndarray], 
                            gpu_memory: float,
                            target_batch_size: int) -> List[DetectionResult]:
    """
    自适应批处理算法
    
    Args:
        frames: 待处理的帧列表
        gpu_memory: 可用GPU内存
        target_batch_size: 目标批大小
        
    Returns:
        检测结果列表
    """
    
    # 1. 计算最优批大小
    optimal_batch_size = calculate_optimal_batch_size(
        image_size=frames[0].shape,
        available_memory=gpu_memory,
        target_size=target_batch_size
    )
    
    # 2. 分批处理
    results = []
    for i in range(0, len(frames), optimal_batch_size):
        batch = frames[i:i + optimal_batch_size]
        
        try:
            # 尝试批处理
            batch_results = process_batch_gpu(batch)
            results.extend(batch_results)
            
        except torch.cuda.OutOfMemoryError:
            # 显存不足，减小批大小重试
            smaller_batch_size = optimal_batch_size // 2
            if smaller_batch_size > 0:
                # 递归处理更小的批次
                sub_results = adaptive_batch_processing(
                    batch, gpu_memory * 0.8, smaller_batch_size
                )
                results.extend(sub_results)
            else:
                # 降级到单张处理
                for frame in batch:
                    result = process_single_frame(frame)
                    results.append(result)
    
    return results
```

### 2. 智能跳帧策略

```python
def smart_frame_skip_strategy(video_path: str, 
                            target_fps: float = 5.0,
                            quality_threshold: float = 0.8) -> int:
    """
    智能跳帧策略
    
    Args:
        video_path: 视频路径
        target_fps: 目标处理帧率
        quality_threshold: 质量阈值
        
    Returns:
        最优跳帧数
    """
    
    # 1. 分析视频特征
    video_info = analyze_video_characteristics(video_path)
    original_fps = video_info['fps']
    motion_intensity = video_info['motion_intensity']
    scene_complexity = video_info['scene_complexity']
    
    # 2. 计算基础跳帧数
    base_skip = max(1, int(original_fps / target_fps))
    
    # 3. 根据内容特征调整
    if motion_intensity > 0.7:  # 高运动强度
        skip_frames = max(1, base_skip - 1)
    elif motion_intensity < 0.3:  # 低运动强度
        skip_frames = base_skip + 1
    else:
        skip_frames = base_skip
    
    # 4. 根据场景复杂度调整
    if scene_complexity > 0.8:  # 复杂场景
        skip_frames = max(1, skip_frames - 1)
    
    return min(skip_frames, 10)  # 最大跳帧限制
```

### 3. 动态内存管理

```python
class DynamicMemoryManager:
    def __init__(self, gpu_device: str):
        self.device = gpu_device
        self.memory_threshold = 0.85  # 85%内存使用阈值
        
    def check_memory_usage(self) -> float:
        """检查当前内存使用率"""
        allocated = torch.cuda.memory_allocated(self.device)
        total = torch.cuda.get_device_properties(self.device).total_memory
        return allocated / total
        
    def optimize_batch_size(self, current_batch_size: int) -> int:
        """根据内存使用情况优化批大小"""
        memory_usage = self.check_memory_usage()
        
        if memory_usage > self.memory_threshold:
            # 内存使用过高，减小批大小
            new_batch_size = max(1, current_batch_size // 2)
            logger.warning(f"Memory usage high ({memory_usage:.1%}), "
                         f"reducing batch size to {new_batch_size}")
            return new_batch_size
            
        elif memory_usage < 0.5 and current_batch_size < 16:
            # 内存使用较低，可以增大批大小
            new_batch_size = min(16, current_batch_size * 2)
            logger.info(f"Memory usage low ({memory_usage:.1%}), "
                       f"increasing batch size to {new_batch_size}")
            return new_batch_size
            
        return current_batch_size
        
    def clear_cache_if_needed(self) -> None:
        """必要时清理GPU缓存"""
        if self.check_memory_usage() > 0.9:
            torch.cuda.empty_cache()
            logger.info("GPU cache cleared due to high memory usage")
```

## API设计

### 1. GPU信息接口

```python
@detection_bp.route('/gpu-info', methods=['GET'])
@jwt_required()
def get_gpu_info():
    """
    获取GPU信息和使用情况
    
    Response:
    {
        "success": true,
        "data": {
            "using_gpu": true,
            "gpu_name": "NVIDIA GeForce RTX 4050 Laptop GPU",
            "gpu_memory_total": "6.0GB",
            "gpu_memory_allocated": "0.08GB",
            "gpu_memory_cached": "0.17GB",
            "device": "cuda:0",
            "imgsz": 1280,
            "use_half": true,
            "model_loaded": true,
            "optimization_available": true
        }
    }
    """
```

### 2. 优化视频检测接口

```python
@detection_bp.route('/detect-video-optimized', methods=['POST'])
@jwt_required()
def detect_video_optimized():
    """
    GPU优化视频检测
    
    Request:
        multipart/form-data:
        - video: 视频文件
        - confidence: float (default 0.45)
        - frame_skip: int (default 3)
        - batch_size: int (default 8)
        - use_fp16: bool (default true)
        - image_size: int (default 1280)
    
    Response:
    {
        "success": true,
        "data": {
            "session_id": 123,
            "total_frames": 1500,
            "processed_frames": 500,
            "processing_time": 25.6,
            "avg_fps": 19.5,
            "optimization": {
                "gpu_accelerated": true,
                "batch_processing": true,
                "half_precision": true,
                "image_size": 1280,
                "batch_size": 8,
                "frame_skip": 3
            },
            "performance_gain": {
                "speed_improvement": "1.92x",
                "efficiency_improvement": "2.91x"
            },
            "behavior_summary": {...}
        }
    }
    """
```

### 3. 优化设置接口

```python
@detection_bp.route('/optimization-settings', methods=['GET', 'POST'])
@jwt_required()
def optimization_settings():
    """
    获取/更新优化设置
    
    GET Response:
    {
        "success": true,
        "data": {
            "batch_size": 8,
            "frame_skip": 3,
            "use_fp16": true,
            "image_size": 1280,
            "auto_optimize": true,
            "memory_threshold": 0.85
        }
    }
    
    POST Request:
    {
        "batch_size": 8,
        "frame_skip": 3,
        "use_fp16": true,
        "image_size": 1280,
        "auto_optimize": true
    }
    """
```

## 用户界面设计

### 1. GPU状态卡片

```vue
<template>
  <el-card class="gpu-status-card">
    <template #header>
      <div class="card-header">
        <span>GPU 状态</span>
        <el-tag :type="gpuStatus.type" size="small">
          {{ gpuStatus.text }}
        </el-tag>
      </div>
    </template>
    
    <div class="gpu-info">
      <!-- GPU基本信息 -->
      <div class="info-item">
        <span class="label">GPU:</span>
        <span class="value">{{ gpuInfo.name }}</span>
      </div>
      
      <!-- 显存使用情况 -->
      <div class="info-item">
        <span class="label">显存:</span>
        <div class="memory-usage">
          <el-progress 
            :percentage="memoryUsagePercent" 
            :stroke-width="8"
            :show-text="false"
          />
          <span class="memory-text">
            {{ gpuInfo.memory_allocated }} / {{ gpuInfo.memory_total }}
          </span>
        </div>
      </div>
      
      <!-- 当前配置 -->
      <div class="config-grid">
        <div class="config-item">
          <span class="config-label">图像尺寸</span>
          <span class="config-value">{{ gpuInfo.imgsz }}px</span>
        </div>
        <div class="config-item">
          <span class="config-label">半精度</span>
          <el-tag :type="gpuInfo.use_half ? 'success' : 'info'" size="small">
            {{ gpuInfo.use_half ? '启用' : '禁用' }}
          </el-tag>
        </div>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="gpu-actions">
      <el-button size="small" @click="refreshGpuInfo" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button size="small" type="primary" @click="showSettings = true">
        <el-icon><Setting /></el-icon>
        优化设置
      </el-button>
    </div>
  </el-card>
</template>
```

### 2. 处理模式选择对话框

```vue
<template>
  <el-dialog 
    v-model="showModeDialog" 
    title="选择视频处理模式" 
    width="600px"
    :close-on-click-modal="false"
  >
    <div class="mode-selection">
      <div class="mode-options">
        <!-- GPU优化模式 -->
        <div 
          class="mode-option" 
          :class="{ active: selectedMode === 'optimized' }"
          @click="selectedMode = 'optimized'"
        >
          <div class="mode-header">
            <el-icon class="mode-icon"><Lightning /></el-icon>
            <h3>GPU 优化处理</h3>
            <el-tag type="success" size="small">推荐</el-tag>
          </div>
          <div class="mode-description">
            <p>利用GPU加速，显著提升处理速度</p>
            <ul class="feature-list">
              <li>✓ 批处理优化 (8张/批)</li>
              <li>✓ FP16半精度加速</li>
              <li>✓ 智能跳帧 (每3帧)</li>
              <li>✓ 处理速度提升 ~2倍</li>
            </ul>
          </div>
          <div class="mode-requirements">
            <span class="requirement-label">要求:</span>
            <span>NVIDIA GPU, 4GB+ 显存</span>
          </div>
        </div>
        
        <!-- 标准模式 -->
        <div 
          class="mode-option" 
          :class="{ active: selectedMode === 'standard' }"
          @click="selectedMode = 'standard'"
        >
          <div class="mode-header">
            <el-icon class="mode-icon"><Monitor /></el-icon>
            <h3>标准处理</h3>
          </div>
          <div class="mode-description">
            <p>稳定可靠的CPU处理模式</p>
            <ul class="feature-list">
              <li>✓ 兼容性好</li>
              <li>✓ 资源占用低</li>
              <li>✓ 适合小文件</li>
              <li>✓ 无硬件要求</li>
            </ul>
          </div>
          <div class="mode-requirements">
            <span class="requirement-label">适用:</span>
            <span>所有设备，小于100MB视频</span>
          </div>
        </div>
      </div>
      
      <!-- 智能推荐 -->
      <div class="smart-recommendation" v-if="recommendation">
        <el-alert 
          :title="recommendation.title"
          :description="recommendation.description"
          :type="recommendation.type"
          show-icon
          :closable="false"
        />
      </div>
    </div>
    
    <template #footer>
      <el-button @click="showModeDialog = false">取消</el-button>
      <el-button 
        type="primary" 
        @click="confirmMode"
        :disabled="!selectedMode"
      >
        开始处理
      </el-button>
    </template>
  </el-dialog>
</template>
```

### 3. GPU优化设置对话框

```vue
<template>
  <el-dialog v-model="showOptimizationSettings" title="GPU 优化设置" width="500px">
    <el-form :model="optimizationForm" label-position="top">
      <!-- 批处理设置 -->
      <el-form-item label="批处理大小">
        <el-slider 
          v-model="optimizationForm.batch_size" 
          :min="1" 
          :max="16" 
          :step="1" 
          show-input
          :format-tooltip="formatBatchSizeTooltip"
        />
        <div class="setting-hint">
          更大的批大小可以提高GPU利用率，但需要更多显存
        </div>
      </el-form-item>
      
      <!-- 跳帧设置 -->
      <el-form-item label="跳帧策略">
        <el-slider 
          v-model="optimizationForm.frame_skip" 
          :min="1" 
          :max="10" 
          :step="1" 
          show-input
          :format-tooltip="formatFrameSkipTooltip"
        />
        <div class="setting-hint">
          跳帧数越大处理越快，但可能遗漏短暂行为
        </div>
      </el-form-item>
      
      <!-- 图像尺寸设置 -->
      <el-form-item label="推理图像尺寸">
        <el-slider 
          v-model="optimizationForm.image_size" 
          :min="320" 
          :max="1920" 
          :step="160" 
          show-input
          :format-tooltip="formatImageSizeTooltip"
        />
        <div class="setting-hint">
          更大的尺寸提高检测精度和GPU利用率，但降低速度
        </div>
      </el-form-item>
      
      <!-- FP16设置 -->
      <el-form-item label="半精度计算 (FP16)">
        <el-switch 
          v-model="optimizationForm.use_fp16"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="setting-hint">
          启用FP16可以减少显存使用并提高速度，但可能略微降低精度
        </div>
      </el-form-item>
      
      <!-- 自动优化 -->
      <el-form-item label="自动优化">
        <el-switch 
          v-model="optimizationForm.auto_optimize"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="setting-hint">
          根据GPU性能和视频特征自动调整优化参数
        </div>
      </el-form-item>
    </el-form>
    
    <!-- 预估性能 -->
    <div class="performance-estimate" v-if="performanceEstimate">
      <h4>预估性能</h4>
      <div class="estimate-grid">
        <div class="estimate-item">
          <span class="estimate-label">处理速度:</span>
          <span class="estimate-value">{{ performanceEstimate.speed }}</span>
        </div>
        <div class="estimate-item">
          <span class="estimate-label">显存使用:</span>
          <span class="estimate-value">{{ performanceEstimate.memory }}</span>
        </div>
        <div class="estimate-item">
          <span class="estimate-label">预计提升:</span>
          <span class="estimate-value">{{ performanceEstimate.improvement }}</span>
        </div>
      </div>
    </div>
    
    <template #footer>
      <el-button @click="resetToDefaults">恢复默认</el-button>
      <el-button @click="showOptimizationSettings = false">取消</el-button>
      <el-button type="primary" @click="applyOptimizationSettings" :loading="applying">
        应用设置
      </el-button>
    </template>
  </el-dialog>
</template>
```

## 性能优化策略

### 1. 内存优化
- **显存预分配**: 启动时预分配固定显存，避免动态分配开销
- **内存池管理**: 实现GPU内存池，重用已分配的内存块
- **梯度清理**: 及时清理不需要的梯度信息
- **缓存管理**: 智能管理PyTorch缓存，避免内存碎片

### 2. 计算优化
- **模型量化**: 支持INT8量化进一步提升性能
- **算子融合**: 利用TensorRT等工具进行算子融合优化
- **异步执行**: 实现CPU-GPU异步执行，隐藏数据传输延迟
- **多流并行**: 使用CUDA多流实现并行计算

### 3. I/O优化
- **数据预处理**: GPU端数据预处理，减少CPU-GPU数据传输
- **批量数据库操作**: 批量写入检测结果，减少数据库I/O
- **异步文件读取**: 异步读取视频帧，与GPU计算并行
- **结果缓存**: 缓存中间结果，避免重复计算

## 错误处理和降级策略

### 1. GPU错误处理

```python
class GPUErrorHandler:
    def __init__(self):
        self.fallback_strategies = [
            self.reduce_batch_size,
            self.disable_fp16,
            self.reduce_image_size,
            self.fallback_to_cpu
        ]
    
    def handle_gpu_error(self, error: Exception, context: Dict) -> bool:
        """处理GPU错误，返回是否成功恢复"""
        
        if isinstance(error, torch.cuda.OutOfMemoryError):
            return self.handle_memory_error(context)
        elif isinstance(error, torch.cuda.CudaError):
            return self.handle_cuda_error(context)
        else:
            return self.fallback_to_cpu(context)
    
    def handle_memory_error(self, context: Dict) -> bool:
        """处理显存不足错误"""
        for strategy in self.fallback_strategies:
            try:
                if strategy(context):
                    logger.info(f"Successfully recovered using {strategy.__name__}")
                    return True
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue
        return False
```

### 2. 自动降级机制

```python
def auto_fallback_processing(video_path: str, config: Dict) -> Dict:
    """自动降级处理机制"""
    
    processing_strategies = [
        ('gpu_optimized', process_with_gpu_optimization),
        ('gpu_standard', process_with_gpu_standard),
        ('cpu_optimized', process_with_cpu_optimization),
        ('cpu_basic', process_with_cpu_basic)
    ]
    
    for strategy_name, strategy_func in processing_strategies:
        try:
            logger.info(f"Attempting {strategy_name} processing")
            result = strategy_func(video_path, config)
            result['processing_strategy'] = strategy_name
            return result
            
        except Exception as e:
            logger.warning(f"{strategy_name} processing failed: {e}")
            if strategy_name == 'cpu_basic':
                # 最后的降级策略也失败了
                raise RuntimeError("All processing strategies failed")
            continue
    
    raise RuntimeError("No processing strategy succeeded")
```

## 监控和日志

### 1. 性能监控

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'processing_time': [],
            'gpu_utilization': [],
            'memory_usage': [],
            'batch_sizes': [],
            'frame_rates': []
        }
    
    def record_processing_session(self, session_data: Dict):
        """记录处理会话数据"""
        
    def generate_performance_report(self) -> Dict:
        """生成性能报告"""
        
    def get_optimization_recommendations(self) -> List[str]:
        """基于历史数据生成优化建议"""
```

### 2. 详细日志记录

```python
# 配置详细的日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gpu_optimization.log'),
        logging.StreamHandler()
    ]
)

# 关键操作日志
logger.info(f"GPU optimization started: batch_size={batch_size}, "
           f"fp16={use_fp16}, image_size={image_size}")
logger.info(f"Processing completed: {processing_time:.2f}s, "
           f"avg_fps={avg_fps:.1f}, improvement={improvement:.1f}x")
```

## 测试策略

### 1. 单元测试
- GPU监控模块测试
- 批处理引擎测试
- 优化策略测试
- 错误处理测试

### 2. 集成测试
- 端到端视频处理测试
- API接口测试
- 用户界面测试
- 性能基准测试

### 3. 压力测试
- 大文件处理测试
- 并发用户测试
- 长时间运行测试
- 内存泄漏测试

## 部署考虑

### 1. 环境要求
- NVIDIA GPU驱动 (≥470.x)
- CUDA Toolkit (≥11.0)
- PyTorch GPU版本
- 足够的显存 (≥4GB)

### 2. 配置管理
- GPU优化参数配置文件
- 用户偏好设置持久化
- 环境检测和自动配置
- 性能基准数据库

### 3. 监控和维护
- GPU健康状态监控
- 性能指标收集
- 错误日志分析
- 自动优化建议

这个设计文档提供了视频处理GPU优化功能的完整技术方案，涵盖了从系统架构到具体实现的各个方面，为后续的开发和优化工作提供了详细的指导。