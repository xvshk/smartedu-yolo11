<template>
  <div class="detection-page">
    <el-row :gutter="16">
      <!-- 左侧：视频区域 -->
      <el-col :span="16">
        <el-card class="detection-card">
          <template #header>
            <div class="card-header">
              <span>实时行为检测</span>
              <div class="header-right">
                <el-tag :type="modelLoaded ? 'success' : 'warning'" style="margin-right: 10px;">
                  {{ modelLoaded ? '模型已加载' : '演示模式' }}
                </el-tag>
                <el-tag v-if="isDetecting" type="danger">
                  检测中 ({{ fps }} FPS)
                </el-tag>
              </div>
            </div>
          </template>
          
          <!-- 检测区域 -->
          <div class="detection-area">
            <!-- 未开始状态 -->
            <div v-if="!cameraActive && !resultImage && !videoProcessing" class="start-area">
              <el-icon class="start-icon"><VideoCamera /></el-icon>
              <h3>实时课堂行为检测</h3>
              <p>启动桌面应用进行实时行为识别（检测结果自动保存）</p>
              <el-button type="primary" size="large" @click="launchDesktopApp" :loading="launchingApp">
                <el-icon><VideoCamera /></el-icon>
                启动桌面检测应用
              </el-button>
              
              <el-divider>或</el-divider>
              
              <div class="upload-buttons">
                <el-upload
                  class="upload-btn"
                  :auto-upload="false"
                  :show-file-list="false"
                  accept="image/*"
                  @change="handleFileChange"
                >
                  <el-button size="large">
                    <el-icon><UploadFilled /></el-icon>
                    上传图片检测
                  </el-button>
                </el-upload>
                
                <el-upload
                  class="upload-btn"
                  :auto-upload="false"
                  :show-file-list="false"
                  accept="video/*"
                  @change="handleVideoChange"
                >
                  <el-button size="large" type="success">
                    <el-icon><VideoPlay /></el-icon>
                    上传视频检测
                  </el-button>
                </el-upload>
              </div>
            </div>
            
            <!-- 视频处理中 -->
            <div v-if="videoProcessing" class="video-processing-area">
              <div class="video-preview-container">
                <video ref="videoPreviewRef" class="video-preview" muted></video>
                <canvas ref="videoCanvasRef" class="video-canvas"></canvas>
                <canvas ref="videoOutputRef" class="video-output"></canvas>
              </div>
              <div class="processing-info">
                <el-progress :percentage="videoProgress" :stroke-width="12" />
                <p class="progress-text">{{ videoProgressText }}</p>
                <div class="processing-stats">
                  <span>帧: {{ videoStats.currentFrame }} / {{ videoStats.totalFrames }}</span>
                  <span>学生: {{ videoStats.detections }}</span>
                  <span>预警行为: {{ videoStats.warnings }}</span>
                </div>
              </div>
              <el-button type="danger" @click="cancelVideoProcessing" style="margin-top: 16px;">
                停止检测
              </el-button>
            </div>
            
            <!-- 视频检测结果 -->
            <div v-if="videoResult && !videoProcessing" class="video-result-area">
              <el-result icon="success" title="视频检测完成">
                <template #sub-title>
                  <div class="video-stats">
                    <p>总帧数: {{ videoResult.total_frames }} | 处理帧数: {{ videoResult.processed_frames }}</p>
                    <p v-if="videoResult.optimization_used">
                      处理时间: {{ videoResult.processing_time }}s | 平均速度: {{ videoResult.avg_fps }} FPS
                      <el-tag type="success" size="small" style="margin-left: 8px;">GPU 优化</el-tag>
                    </p>
                    <p v-else>识别学生: {{ videoResult.total_students }} | 有预警行为: {{ videoResult.students_with_warning }}</p>
                    <p v-if="videoResult.optimization">
                      <el-tag :type="videoResult.optimization.gpu_accelerated ? 'success' : 'info'" size="small">
                        {{ videoResult.optimization.gpu_accelerated ? 'GPU 加速' : 'CPU 处理' }}
                      </el-tag>
                      <el-tag v-if="videoResult.optimization.batch_processing" type="primary" size="small" style="margin-left: 4px;">
                        批处理
                      </el-tag>
                      <el-tag v-if="videoResult.optimization.half_precision" type="warning" size="small" style="margin-left: 4px;">
                        FP16
                      </el-tag>
                      <span style="margin-left: 8px; font-size: 12px; color: #909399;">
                        图像尺寸: {{ videoResult.optimization.image_size }}px
                      </span>
                    </p>
                  </div>
                </template>
                <template #extra>
                  <el-button type="primary" @click="viewVideoDetail">查看详情</el-button>
                  <el-button @click="resetVideoResult">重新检测</el-button>
                </template>
              </el-result>
              
              <!-- 行为统计 -->
              <div class="video-behavior-summary">
                <h4>行为统计（按学生位置去重）</h4>
                <div v-for="(count, name) in videoResult.behavior_summary" :key="name" class="behavior-stat-item">
                  <span>{{ name }}</span>
                  <el-tag :type="getBehaviorTagType(name)" size="small">{{ count }} 人</el-tag>
                </div>
              </div>
            </div>
            
            <!-- 实时检测区域 -->
            <div v-if="cameraActive" class="realtime-area">
              <div class="video-container">
                <video ref="videoRef" autoplay playsinline muted class="camera-video"></video>
                <canvas ref="canvasRef" class="detection-canvas"></canvas>
                <canvas ref="outputCanvasRef" class="output-canvas"></canvas>
              </div>
              <div class="camera-controls">
                <el-button type="danger" @click="stopRealTimeDetection">
                  <el-icon><VideoPause /></el-icon>
                  停止检测
                </el-button>
                <el-button @click="captureSnapshot">
                  <el-icon><Camera /></el-icon>
                  截图保存
                </el-button>
              </div>
            </div>
            
            <!-- 图片检测结果 -->
            <div v-if="resultImage && !cameraActive" class="result-area">
              <img :src="resultImage" alt="检测结果" class="result-image" />
              <div class="result-controls">
                <el-button type="primary" @click="resetDetection">
                  <el-icon><RefreshRight /></el-icon>
                  重新检测
                </el-button>
                <el-button @click="downloadResult">
                  <el-icon><Download /></el-icon>
                  下载结果
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：检测结果和设置 -->
      <el-col :span="8">
        <!-- 检测设置 -->
        <el-card class="settings-card">
          <template #header>检测设置</template>
          <el-form label-position="top" size="small">
            <el-form-item label="置信度阈值">
              <el-slider v-model="settings.confidence" :min="0.05" :max="0.9" :step="0.05" show-input :format-tooltip="v => v.toFixed(2)" />
            </el-form-item>
            <el-form-item label="跳帧数 (性能优化)">
              <el-slider v-model="settings.frameSkip" :min="0" :max="5" :step="1" show-input @change="updateFrameSkip" />
              <div class="setting-hint">值越大性能越好，但检测延迟增加</div>
            </el-form-item>
            <el-form-item label="请求间隔 (ms)">
              <el-slider v-model="settings.interval" :min="50" :max="1000" :step="50" show-input />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 实时检测统计 -->
        <el-card class="stats-card">
          <template #header>检测结果</template>
          
          <div class="stats-overview">
            <div class="stat-item">
              <div class="stat-value">{{ currentStats.total }}</div>
              <div class="stat-label">检测总数</div>
            </div>
            <div class="stat-item normal">
              <div class="stat-value">{{ currentStats.normal }}</div>
              <div class="stat-label">正常行为</div>
            </div>
            <div class="stat-item warning">
              <div class="stat-value">{{ currentStats.warning }}</div>
              <div class="stat-label">预警行为</div>
            </div>
          </div>
          
          <!-- 行为分布 -->
          <div class="behavior-list">
            <div class="section-title">行为分布</div>
            <div v-for="(count, name) in currentStats.behaviors" :key="name" class="behavior-item">
              <span class="behavior-name">{{ name }}</span>
              <el-tag :type="getBehaviorTagType(name)" size="small">{{ count }}</el-tag>
            </div>
          </div>
        </el-card>
        
        <!-- 行为时间统计 -->
        <el-card class="time-stats-card" v-if="isDetecting || timeStats.total_time > 0">
          <template #header>
            <div class="card-header">
              <span>行为时间统计</span>
              <el-button size="small" @click="resetTimeStats(true)" :disabled="isDetecting">重置</el-button>
            </div>
          </template>
          
          <div class="total-time">
            <span class="time-label">检测总时长:</span>
            <span class="time-value">{{ timeStats.total_time_formatted || '0:00' }}</span>
          </div>
          
          <div class="time-list">
            <div v-for="(duration, name) in timeStats.behavior_duration_formatted" :key="name" class="time-item">
              <span class="time-name">{{ name }}</span>
              <span class="time-duration" :class="{ warning: getBehaviorTagType(name) === 'danger' }">
                {{ duration }}
              </span>
            </div>
          </div>
        </el-card>
        
        <!-- 检测目标列表 -->
        <el-card class="detections-card" v-if="currentDetections.length > 0">
          <template #header>
            <div class="card-header">
              <span>检测目标</span>
              <el-tag size="small">{{ currentDetections.length }} 个</el-tag>
            </div>
          </template>
          
          <div class="detection-list">
            <div 
              v-for="(det, index) in currentDetections" 
              :key="index" 
              class="detection-item"
              :class="{ warning: det.behavior_type === 'warning' }"
            >
              <div class="det-header">
                <span class="det-class">{{ det.class_name_cn }}</span>
                <el-tag :type="det.behavior_type === 'warning' ? 'danger' : 'success'" size="small">
                  {{ (det.confidence * 100).toFixed(1) }}%
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- GPU 信息 -->
        <el-card class="gpu-card" v-if="gpuInfo.using_gpu">
          <template #header>
            <div class="card-header">
              <span>GPU 状态</span>
              <el-tag :type="gpuInfo.model_loaded ? 'success' : 'warning'" size="small">
                {{ gpuInfo.model_loaded ? '已加载' : '未加载' }}
              </el-tag>
            </div>
          </template>
          
          <div class="gpu-info">
            <div class="gpu-item">
              <span class="gpu-label">GPU:</span>
              <span class="gpu-value">{{ gpuInfo.gpu_name || 'N/A' }}</span>
            </div>
            <div class="gpu-item">
              <span class="gpu-label">显存:</span>
              <span class="gpu-value">
                {{ gpuInfo.gpu_memory_allocated || '0GB' }} / {{ gpuInfo.gpu_memory_total || '0GB' }}
              </span>
            </div>
            <div class="gpu-item">
              <span class="gpu-label">图像尺寸:</span>
              <span class="gpu-value">{{ gpuInfo.imgsz || 640 }}px</span>
            </div>
            <div class="gpu-item">
              <span class="gpu-label">半精度:</span>
              <el-tag :type="gpuInfo.use_half ? 'success' : 'info'" size="small">
                {{ gpuInfo.use_half ? '启用' : '禁用' }}
              </el-tag>
            </div>
          </div>
          
          <div class="gpu-controls">
            <el-button size="small" @click="refreshGpuInfo" :loading="gpuLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button size="small" @click="showGpuSettings = true">
              <el-icon><Setting /></el-icon>
              设置
            </el-button>
          </div>
        </el-card>
        
        <!-- 行为类别说明 -->
        <el-card class="classes-card">
          <template #header>行为类别</template>
          <div class="class-list">
            <div v-for="cls in behaviorClasses" :key="cls.class_id" class="class-item">
              <span class="class-color" :style="{ background: cls.color }"></span>
              <span class="class-name">{{ cls.cn_name }}</span>
              <el-tag :type="cls.type === 'warning' ? 'danger' : 'success'" size="small">
                {{ cls.type === 'warning' ? '预警' : '正常' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 检测历史记录 -->
    <el-row style="margin-top: 16px;">
      <el-col :span="24">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <span>📋 检测历史记录</span>
              <div class="header-actions">
                <el-button size="small" @click="loadHistory" :loading="historyLoading">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>
          
          <!-- 历史记录表格 -->
          <el-table 
            :data="historyList" 
            v-loading="historyLoading"
            stripe
            style="width: 100%"
            @row-click="showHistoryDetail"
          >
            <el-table-column prop="session_id" label="会话ID" width="80" />
            <el-table-column prop="source_type" label="来源类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getSourceTypeTag(row.source_type)" size="small">
                  {{ getSourceTypeLabel(row.source_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.start_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_detections" label="检测数" width="90" align="center" />
            <el-table-column prop="warning_count" label="预警数" width="90" align="center">
              <template #default="{ row }">
                <span :class="{ 'warning-text': row.warning_count > 0 }">{{ row.warning_count }}</span>
              </template>
            </el-table-column>
            <el-table-column label="行为分布" min-width="200">
              <template #default="{ row }">
                <div class="behavior-tags">
                  <el-tag 
                    v-for="(count, name) in row.behavior_summary" 
                    :key="name"
                    :type="getBehaviorTagType(name)"
                    size="small"
                    style="margin-right: 4px; margin-bottom: 4px;"
                  >
                    {{ name }}: {{ count }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                  {{ row.status === 'completed' ? '已完成' : '进行中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click.stop="showHistoryDetail(row)">
                  详情
                </el-button>
                <el-button type="danger" size="small" link @click.stop="deleteHistoryItem(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination-wrapper" v-if="historyTotal > 0">
            <el-pagination
              v-model:current-page="historyPage"
              v-model:page-size="historyPageSize"
              :total="historyTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadHistory"
              @current-change="loadHistory"
            />
          </div>
          
          <!-- 空状态 -->
          <el-empty v-if="!historyLoading && historyList.length === 0" description="暂无检测记录" />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 历史详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="检测详情" width="700px">
      <div v-loading="detailLoading">
        <div class="detail-header" v-if="historyDetail">
          <div class="detail-info">
            <p><strong>会话ID:</strong> {{ historyDetail.session_id }}</p>
            <p><strong>来源类型:</strong> {{ getSourceTypeLabel(historyDetail.source_type) }}</p>
            <p><strong>开始时间:</strong> {{ formatDateTime(historyDetail.start_time) }}</p>
            <p><strong>结束时间:</strong> {{ formatDateTime(historyDetail.end_time) }}</p>
          </div>
          <div class="detail-stats">
            <div class="stat-box">
              <div class="stat-num">{{ historyDetail.total_count }}</div>
              <div class="stat-label">总检测数</div>
            </div>
            <div class="stat-box normal">
              <div class="stat-num">{{ historyDetail.normal_count }}</div>
              <div class="stat-label">正常行为</div>
            </div>
            <div class="stat-box warning">
              <div class="stat-num">{{ historyDetail.warning_count }}</div>
              <div class="stat-label">预警行为</div>
            </div>
          </div>
        </div>
        
        <!-- 行为统计 -->
        <div class="detail-behavior-summary" v-if="historyDetail">
          <h4>行为统计</h4>
          <div class="behavior-grid">
            <div 
              v-for="(count, name) in historyDetail.behavior_summary" 
              :key="name"
              class="behavior-card"
              :class="{ warning: getBehaviorTagType(name) === 'danger' }"
            >
              <div class="behavior-count">{{ count }}</div>
              <div class="behavior-name">{{ name }}</div>
            </div>
          </div>
        </div>
        
        <!-- 检测列表 -->
        <div class="detail-detections" v-if="historyDetail && historyDetail.detections">
          <h4>检测目标列表 ({{ historyDetail.detections.length }})</h4>
          <el-table :data="historyDetail.detections" max-height="300" size="small">
            <el-table-column prop="class_name" label="行为类型" width="120" />
            <el-table-column prop="confidence" label="置信度" width="100">
              <template #default="{ row }">
                {{ (row.confidence * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="behavior_type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag :type="row.behavior_type === 'warning' ? 'danger' : 'success'" size="small">
                  {{ row.behavior_type === 'warning' ? '预警' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="位置" min-width="150">
              <template #default="{ row }">
                <span class="bbox-text">
                  [{{ row.bbox.map(v => Math.round(v)).join(', ') }}]
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- GPU 设置对话框 -->
    <el-dialog v-model="showGpuSettings" title="GPU 优化设置" width="500px">
      <el-form label-position="top">
        <el-form-item label="推理图像尺寸 (影响 GPU 利用率)">
          <el-slider 
            v-model="gpuSettings.imgsz" 
            :min="320" 
            :max="1920" 
            :step="160" 
            show-input 
            :format-tooltip="v => `${v}px`"
          />
          <div class="setting-hint">更大的尺寸会提高 GPU 利用率，但可能降低速度</div>
        </el-form-item>
        
        <el-form-item label="半精度 (FP16)" v-if="gpuInfo.using_gpu">
          <el-switch 
            v-model="gpuSettings.use_half"
            active-text="启用"
            inactive-text="禁用"
          />
          <div class="setting-hint">启用 FP16 可以提高 GPU 利用率并减少显存使用</div>
        </el-form-item>
        
        <el-form-item label="置信度阈值">
          <el-slider 
            v-model="gpuSettings.confidence_threshold" 
            :min="0.1" 
            :max="0.9" 
            :step="0.05" 
            show-input 
            :format-tooltip="v => v.toFixed(2)"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showGpuSettings = false">取消</el-button>
        <el-button type="primary" @click="updateGpuSettings" :loading="gpuLoading">
          应用设置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, VideoCamera, Camera, RefreshRight, Download, VideoPause, VideoPlay, Loading, Refresh, Setting } from '@element-plus/icons-vue'
import api from '@/api'

// 状态
const cameraActive = ref(false)
const isDetecting = ref(false)
const modelLoaded = ref(false)
const resultImage = ref(null)
const fps = ref(0)
const launchingApp = ref(false)

// 视频处理状态
const videoProcessing = ref(false)
const videoProgress = ref(0)
const videoProgressText = ref('')
const videoResult = ref(null)
const videoStats = reactive({
  currentFrame: 0,
  totalFrames: 0,
  detections: 0,
  warnings: 0
})
let videoAbortController = null

// 引用
const videoRef = ref(null)
const canvasRef = ref(null)
const outputCanvasRef = ref(null)
const videoPreviewRef = ref(null)
const videoCanvasRef = ref(null)
const videoOutputRef = ref(null)
let mediaStream = null
let detectionInterval = null
let frameCount = 0
let lastFpsTime = Date.now()
let videoProcessingActive = false

// 设置
const settings = reactive({
  confidence: 0.45,  // 提高默认置信度以减少误检测
  interval: 200,  // 检测间隔 ms（降低以提高流畅度）
  frameSkip: 2  // 跳帧数（每N帧检测一次）
})

// 当前检测结果
const currentDetections = ref([])
const currentStats = reactive({
  total: 0,
  normal: 0,
  warning: 0,
  behaviors: {}
})

// 时间统计
const timeStats = reactive({
  total_time: 0,
  total_time_formatted: '0:00',
  frame_count: 0,
  behavior_duration: {},
  behavior_duration_formatted: {}
})

// 历史记录
const historyList = ref([])
const historyLoading = ref(false)
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const showDetailDialog = ref(false)
const detailLoading = ref(false)
const historyDetail = ref(null)

// 行为类别
const behaviorClasses = ref([
  { class_id: 0, name: 'handrise', cn_name: '举手', type: 'normal', color: 'rgb(0,255,0)' },
  { class_id: 2, name: 'write', cn_name: '书写', type: 'normal', color: 'rgb(0,180,0)' },
  { class_id: 3, name: 'sleep', cn_name: '睡觉', type: 'warning', color: 'rgb(255,0,0)' },
  { class_id: 4, name: 'stand', cn_name: '站立', type: 'warning', color: 'rgb(128,128,128)' },
  { class_id: 5, name: 'using_electronic_devices', cn_name: '使用电子设备', type: 'warning', color: 'rgb(255,0,255)' },
  { class_id: 6, name: 'talk', cn_name: '交谈', type: 'warning', color: 'rgb(255,165,0)' },
  { class_id: 7, name: 'head_down', cn_name: '低头', type: 'warning', color: 'rgb(255,128,0)' },
])

// 获取行为标签类型
const getBehaviorTagType = (name) => {
  const warningBehaviors = ['睡觉', '站立', '使用电子设备', '交谈', '低头']
  return warningBehaviors.includes(name) ? 'danger' : 'success'
}

// 启动桌面检测应用
const launchDesktopApp = async () => {
  launchingApp.value = true
  try {
    const res = await api.detection.launchDesktopApp()
    if (res.success) {
      ElMessage.success('桌面检测应用已启动，检测结果将自动保存到数据库')
    } else {
      ElMessage.error(res.message || '启动失败')
    }
  } catch (e) {
    console.error('Launch desktop app error:', e)
    ElMessage.error('启动桌面应用失败: ' + (e.message || '网络错误'))
  } finally {
    launchingApp.value = false
  }
}

// GPU 信息
const gpuInfo = reactive({
  using_gpu: false,
  model_loaded: false,
  gpu_name: '',
  gpu_memory_total: '',
  gpu_memory_allocated: '',
  gpu_memory_cached: '',
  imgsz: 640,
  use_half: false,
  device: 'cpu'
})

const gpuLoading = ref(false)
const showGpuSettings = ref(false)

// GPU 设置数据
const gpuSettings = reactive({
  imgsz: 1280,
  use_half: true,
  confidence_threshold: 0.45
})

// 刷新 GPU 信息
const refreshGpuInfo = async () => {
  gpuLoading.value = true
  try {
    const res = await api.detection.getGpuInfo()
    if (res.success) {
      Object.assign(gpuInfo, res.data)
      // 同步设置数据
      gpuSettings.imgsz = res.data.imgsz || 1280
      gpuSettings.use_half = res.data.use_half || false
      gpuSettings.confidence_threshold = res.data.confidence_threshold || 0.45
    }
  } catch (e) {
    console.error('获取 GPU 信息失败:', e)
    ElMessage.error('获取 GPU 信息失败')
  } finally {
    gpuLoading.value = false
  }
}

// 更新 GPU 设置
const updateGpuSettings = async () => {
  gpuLoading.value = true
  try {
    const res = await api.detection.updateSettings(gpuSettings)
    if (res.success) {
      ElMessage.success('设置已更新')
      showGpuSettings.value = false
      // 刷新 GPU 信息
      await refreshGpuInfo()
    } else {
      ElMessage.error('设置更新失败')
    }
  } catch (e) {
    console.error('更新 GPU 设置失败:', e)
    ElMessage.error('设置更新失败')
  } finally {
    gpuLoading.value = false
  }
}

// 开始实时检测
const startRealTimeDetection = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ 
      video: { width: 1280, height: 720 } 
    })
    cameraActive.value = true
    
    // 重置时间统计
    await resetTimeStats()
    
    await nextTick()
    
    const video = videoRef.value
    video.srcObject = mediaStream
    
    // 等待视频加载
    video.onloadedmetadata = () => {
      // 设置canvas尺寸
      const canvas = canvasRef.value
      const outputCanvas = outputCanvasRef.value
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      outputCanvas.width = video.videoWidth
      outputCanvas.height = video.videoHeight
      
      // 开始检测循环
      startDetectionLoop()
    }
    
    ElMessage.success('摄像头已开启，开始实时检测')
  } catch (e) {
    console.error('Camera error:', e)
    ElMessage.error('无法访问摄像头: ' + e.message)
  }
}

// 开始检测循环
const startDetectionLoop = () => {
  isDetecting.value = true
  
  const detectFrame = async () => {
    if (!cameraActive.value || !isDetecting.value) return
    
    const video = videoRef.value
    const canvas = canvasRef.value
    const outputCanvas = outputCanvasRef.value
    
    if (!video || !canvas || !outputCanvas) return
    
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)
    
    // 获取图片数据（降低质量以提高传输速度）
    const base64Image = canvas.toDataURL('image/jpeg', 0.7)
    
    try {
      // 使用快速检测API
      const res = await api.detection.detectFast({
        image: base64Image,
        confidence: settings.confidence,
        skip_detection: false
      })
      
      if (res.success) {
        // 更新检测结果
        currentDetections.value = res.data.detections || []
        currentStats.total = res.data.total_count || 0
        currentStats.normal = res.data.normal_count || 0
        currentStats.warning = res.data.warning_count || 0
        currentStats.behaviors = res.data.behavior_summary || {}
        
        // 更新FPS（从服务端获取）
        if (res.data.fps) {
          fps.value = Math.round(res.data.fps)
        }
        
        // 更新时间统计
        if (res.data.behavior_duration) {
          updateTimeStats(res.data.behavior_duration)
        }
        
        // 在输出canvas上绘制结果
        drawDetectionsOnCanvas(outputCanvas, currentDetections.value)
        
        // 本地FPS计算
        frameCount++
        const now = Date.now()
        if (now - lastFpsTime >= 1000) {
          // 使用服务端FPS或本地计算
          if (!res.data.fps) {
            fps.value = frameCount
          }
          frameCount = 0
          lastFpsTime = now
        }
      }
    } catch (e) {
      console.error('Detection error:', e)
    }
    
    // 继续下一帧
    if (cameraActive.value && isDetecting.value) {
      detectionInterval = setTimeout(detectFrame, settings.interval)
    }
  }
  
  detectFrame()
}

// 在canvas上绘制检测结果
const drawDetectionsOnCanvas = (canvas, detections) => {
  const ctx = canvas.getContext('2d')
  const video = videoRef.value
  
  // 先绘制视频帧
  ctx.drawImage(video, 0, 0)
  
  // 绘制检测框
  for (const det of detections) {
    const [x1, y1, x2, y2] = det.bbox
    
    // 获取颜色
    const cls = behaviorClasses.value.find(c => c.class_id === det.class_id)
    const color = cls ? cls.color : 'rgb(0,255,0)'
    
    // 绘制边界框
    ctx.strokeStyle = color
    ctx.lineWidth = det.behavior_type === 'warning' ? 3 : 2
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
    
    // 绘制标签背景
    const label = `${det.class_name_cn} ${(det.confidence * 100).toFixed(0)}%`
    ctx.font = '16px Microsoft YaHei, sans-serif'
    const textWidth = ctx.measureText(label).width
    
    ctx.fillStyle = color
    ctx.fillRect(x1, y1 - 24, textWidth + 10, 24)
    
    // 绘制标签文字
    ctx.fillStyle = 'white'
    ctx.fillText(label, x1 + 5, y1 - 6)
    
    // 预警标记
    if (det.behavior_type === 'warning') {
      ctx.fillStyle = 'red'
      ctx.beginPath()
      ctx.arc(x2 - 15, y1 + 15, 10, 0, Math.PI * 2)
      ctx.fill()
      ctx.fillStyle = 'white'
      ctx.font = 'bold 14px sans-serif'
      ctx.fillText('!', x2 - 19, y1 + 20)
    }
  }
  
  // 绘制统计信息
  ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
  ctx.fillRect(5, 5, 200, 30)
  ctx.fillStyle = '#00ff00'
  ctx.font = '14px Microsoft YaHei, sans-serif'
  ctx.fillText(`检测: ${detections.length} | 预警: ${detections.filter(d => d.behavior_type === 'warning').length}`, 10, 25)
}

// 停止实时检测
const stopRealTimeDetection = () => {
  isDetecting.value = false
  
  if (detectionInterval) {
    clearTimeout(detectionInterval)
    detectionInterval = null
  }
  
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  
  cameraActive.value = false
  fps.value = 0
  
  ElMessage.info('已停止实时检测')
}

// 截图保存
const captureSnapshot = async () => {
  const outputCanvas = outputCanvasRef.value
  if (!outputCanvas) return
  
  // 保存当前帧到数据库
  const base64Image = canvasRef.value.toDataURL('image/jpeg', 0.9)
  
  try {
    const res = await api.detection.detect({
      image: base64Image,
      confidence: settings.confidence,
      iou: 0.45,
      save_to_db: true
    })
    
    if (res.success) {
      // 下载截图
      const link = document.createElement('a')
      link.href = outputCanvas.toDataURL('image/jpeg', 0.9)
      link.download = `detection_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.jpg`
      link.click()
      
      ElMessage.success('截图已保存')
    }
  } catch (e) {
    console.error('Snapshot error:', e)
    ElMessage.error('保存失败')
  }
}

// 处理文件上传
const handleFileChange = async (uploadFile) => {
  const file = uploadFile.raw || uploadFile
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = async (e) => {
    await detectImage(e.target.result)
  }
  reader.readAsDataURL(file)
}

// 检测单张图片
const detectImage = async (base64Image) => {
  try {
    const res = await api.detection.detect({
      image: base64Image,
      confidence: settings.confidence,
      iou: 0.45,
      save_to_db: true
    })
    
    if (res.success) {
      resultImage.value = res.data.annotated_image
      currentDetections.value = res.data.detections || []
      currentStats.total = res.data.total_count || 0
      currentStats.normal = res.data.normal_count || 0
      currentStats.warning = res.data.warning_count || 0
      currentStats.behaviors = res.data.behavior_summary || {}
      
      ElMessage.success(`检测完成，发现 ${res.data.total_count} 个目标`)
    } else {
      ElMessage.error(res.message || '检测失败')
    }
  } catch (e) {
    console.error('Detection error:', e)
    ElMessage.error('检测失败: ' + (e.message || '网络错误'))
  }
}

// 重置检测
const resetDetection = () => {
  resultImage.value = null
  currentDetections.value = []
  currentStats.total = 0
  currentStats.normal = 0
  currentStats.warning = 0
  currentStats.behaviors = {}
}

// 处理视频上传
const handleVideoChange = async (uploadFile) => {
  const file = uploadFile.raw || uploadFile
  if (!file) return
  
  // 检查文件大小（限制500MB）
  if (file.size > 500 * 1024 * 1024) {
    ElMessage.error('视频文件不能超过500MB')
    return
  }
  
  // 询问用户是否使用 GPU 优化处理
  const useOptimized = await ElMessageBox.confirm(
    '是否使用 GPU 优化处理？优化模式处理速度更快，但可能消耗更多显存。',
    '选择处理模式',
    {
      confirmButtonText: 'GPU 优化处理',
      cancelButtonText: '标准处理',
      type: 'info',
      distinguishCancelAndClose: true
    }
  ).then(() => true).catch((action) => {
    if (action === 'cancel') return false
    throw new Error('用户取消')
  })
  
  if (useOptimized) {
    await handleVideoOptimized(file)
  } else {
    await handleVideoStandard(file)
  }
}

// GPU 优化视频处理
const handleVideoOptimized = async (file) => {
  videoProcessing.value = true
  videoProgress.value = 0
  videoProgressText.value = '正在上传视频...'
  videoResult.value = null
  
  try {
    const formData = new FormData()
    formData.append('video', file)
    formData.append('confidence', settings.confidence)
    formData.append('frame_skip', 3)  // 更积极的跳帧
    formData.append('batch_size', gpuInfo.using_gpu ? 8 : 4)  // 根据 GPU 调整批大小
    
    const startTime = Date.now()
    
    const res = await api.detection.detectVideoOptimized(formData, (progressEvent) => {
      if (progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        videoProgress.value = progress
        videoProgressText.value = `上传进度: ${progress}%`
      }
    })
    
    const processingTime = (Date.now() - startTime) / 1000
    
    if (res.success) {
      videoResult.value = {
        ...res.data,
        processing_time_frontend: processingTime,
        optimization_used: true
      }
      videoProgressText.value = '处理完成！'
      videoProgress.value = 100
      
      ElMessage.success(`GPU 优化处理完成！用时 ${res.data.processing_time}s，平均 ${res.data.avg_fps} FPS`)
    } else {
      throw new Error(res.message || '处理失败')
    }
  } catch (error) {
    console.error('GPU 优化视频处理失败:', error)
    ElMessage.error(`GPU 优化处理失败: ${error.message}`)
  } finally {
    videoProcessing.value = false
  }
}

// 标准视频处理（原有逻辑）
const handleVideoStandard = async (file) => {
  videoProcessing.value = true
  videoProgress.value = 0
  videoProgressText.value = '正在加载视频...'
  videoResult.value = null
  videoProcessingActive = true
  
  // 重置统计
  videoStats.currentFrame = 0
  videoStats.totalFrames = 0
  videoStats.detections = 0
  videoStats.warnings = 0
  
  await nextTick()
  
  // 创建视频URL
  const videoUrl = URL.createObjectURL(file)
  const video = videoPreviewRef.value
  const canvas = videoCanvasRef.value
  const outputCanvas = videoOutputRef.value
  
  video.src = videoUrl
  
  video.onloadedmetadata = async () => {
    const totalFrames = Math.floor(video.duration * 30) // 假设30fps
    videoStats.totalFrames = totalFrames
    
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    outputCanvas.width = video.videoWidth
    outputCanvas.height = video.videoHeight
    
    videoProgressText.value = '开始检测...'
    
    // 开始逐帧检测
    await processVideoFrames(video, canvas, outputCanvas, file.name)
    
    URL.revokeObjectURL(videoUrl)
  }
  
  video.onerror = () => {
    ElMessage.error('无法加载视频文件')
    videoProcessing.value = false
    URL.revokeObjectURL(videoUrl)
  }
}

// 逐帧处理视频
const processVideoFrames = async (video, canvas, outputCanvas, filename) => {
  const ctx = canvas.getContext('2d')
  const outputCtx = outputCanvas.getContext('2d')
  const frameSkip = 5 // 每5帧检测一次
  const duration = video.duration
  const fps = 30
  const totalFrames = Math.floor(duration * fps)
  
  let currentFrame = 0
  let lastDetections = []  // 保存上一次的检测结果
  
  // 基于位置的学生跟踪
  const studentTrackers = new Map()
  const gridSize = 100
  
  const getPositionId = (bbox) => {
    const centerX = (bbox[0] + bbox[2]) / 2
    const centerY = (bbox[1] + bbox[3]) / 2
    const gridX = Math.floor(centerX / gridSize)
    const gridY = Math.floor(centerY / gridSize)
    return `${gridX}_${gridY}`
  }
  
  // 在canvas上绘制检测框（与实时检测一致）
  const drawDetections = (canvas, detections) => {
    const ctx = canvas.getContext('2d')
    
    for (const det of detections) {
      const [x1, y1, x2, y2] = det.bbox
      
      const cls = behaviorClasses.value.find(c => c.class_id === det.class_id)
      const color = cls ? cls.color : 'rgb(0,255,0)'
      
      ctx.strokeStyle = color
      ctx.lineWidth = det.behavior_type === 'warning' ? 3 : 2
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
      
      const label = `${det.class_name_cn} ${(det.confidence * 100).toFixed(0)}%`
      ctx.font = '16px Microsoft YaHei, sans-serif'
      const textWidth = ctx.measureText(label).width
      
      ctx.fillStyle = color
      ctx.fillRect(x1, y1 - 24, textWidth + 10, 24)
      
      ctx.fillStyle = 'white'
      ctx.fillText(label, x1 + 5, y1 - 6)
      
      if (det.behavior_type === 'warning') {
        ctx.fillStyle = 'red'
        ctx.beginPath()
        ctx.arc(x2 - 15, y1 + 15, 10, 0, Math.PI * 2)
        ctx.fill()
        ctx.fillStyle = 'white'
        ctx.font = 'bold 14px sans-serif'
        ctx.fillText('!', x2 - 19, y1 + 20)
      }
    }
    
    // 统计信息
    const warningCount = detections.filter(d => d.behavior_type === 'warning').length
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
    ctx.fillRect(5, 5, 200, 30)
    ctx.fillStyle = '#00ff00'
    ctx.font = '14px Microsoft YaHei, sans-serif'
    ctx.fillText(`检测: ${detections.length} | 预警: ${warningCount}`, 10, 25)
  }
  
  const processFrame = () => {
    return new Promise((resolve) => {
      if (!videoProcessingActive) {
        resolve(false)
        return
      }
      
      const currentTime = currentFrame / fps
      if (currentTime >= duration) {
        resolve(false)
        return
      }
      
      video.currentTime = currentTime
      
      video.onseeked = async () => {
        if (!videoProcessingActive) {
          resolve(false)
          return
        }
        
        // 绘制当前帧到隐藏canvas
        ctx.drawImage(video, 0, 0)
        
        // 每N帧检测一次
        if (currentFrame % frameSkip === 0) {
          const base64Image = canvas.toDataURL('image/jpeg', 0.7)
          
          try {
            const res = await api.detection.detectFast({
              image: base64Image,
              confidence: settings.confidence,
              skip_detection: false
            })
            
            if (res.success && res.data.detections) {
              lastDetections = res.data.detections
              
              // 基于位置跟踪学生行为
              for (const det of res.data.detections) {
                const posId = getPositionId(det.bbox)
                
                if (!studentTrackers.has(posId)) {
                  studentTrackers.set(posId, {
                    behaviors: {},
                    lastSeen: currentFrame
                  })
                }
                
                const tracker = studentTrackers.get(posId)
                tracker.lastSeen = currentFrame
                
                if (!tracker.behaviors[det.class_name_cn]) {
                  tracker.behaviors[det.class_name_cn] = {
                    count: 1,
                    type: det.behavior_type,
                    firstFrame: currentFrame
                  }
                }
              }
              
              updateVideoStats(studentTrackers)
            }
          } catch (e) {
            console.error('Frame detection error:', e)
          }
        }
        
        // 绘制当前帧到输出canvas
        outputCtx.drawImage(video, 0, 0)
        
        // 始终绘制上一次的检测框（保持框持续显示）
        if (lastDetections.length > 0) {
          drawDetections(outputCanvas, lastDetections)
        }
        
        currentFrame++
        videoStats.currentFrame = currentFrame
        videoProgress.value = Math.round((currentFrame / totalFrames) * 100)
        videoProgressText.value = `处理中: ${videoProgress.value}%`
        
        resolve(true)
      }
    })
  }
  
  // 循环处理帧
  let shouldContinue = true
  while (shouldContinue && videoProcessingActive) {
    shouldContinue = await processFrame()
    await new Promise(r => setTimeout(r, 10))
  }
  
  // 完成
  if (videoProcessingActive) {
    videoProgress.value = 100
    videoProgressText.value = '检测完成'
    
    const behaviorSummary = {}
    let totalStudents = studentTrackers.size
    let studentsWithWarning = 0
    
    for (const [posId, tracker] of studentTrackers) {
      let hasWarning = false
      for (const [behavior, info] of Object.entries(tracker.behaviors)) {
        behaviorSummary[behavior] = (behaviorSummary[behavior] || 0) + 1
        if (info.type === 'warning') {
          hasWarning = true
        }
      }
      if (hasWarning) {
        studentsWithWarning++
      }
    }
    
    videoResult.value = {
      total_frames: totalFrames,
      processed_frames: Math.floor(totalFrames / frameSkip),
      total_students: totalStudents,
      students_with_warning: studentsWithWarning,
      behavior_summary: behaviorSummary
    }
    
    ElMessage.success(`视频检测完成，识别到 ${totalStudents} 个学生位置`)
  }
  
  videoProcessing.value = false
  videoProcessingActive = false
}

// 更新视频统计显示
const updateVideoStats = (trackers) => {
  let totalBehaviors = 0
  let warnings = 0
  
  for (const [posId, tracker] of trackers) {
    for (const [behavior, info] of Object.entries(tracker.behaviors)) {
      totalBehaviors++
      if (info.type === 'warning') {
        warnings++
      }
    }
  }
  
  videoStats.detections = trackers.size  // 学生位置数
  videoStats.warnings = warnings  // 预警行为数
}

// 取消视频处理
const cancelVideoProcessing = () => {
  videoProcessingActive = false
  videoProcessing.value = false
  videoProgress.value = 0
  videoProgressText.value = ''
  ElMessage.info('已停止视频检测')
}

// 查看视频检测详情
const viewVideoDetail = () => {
  if (videoResult.value && videoResult.value.session_id) {
    // 可以跳转到历史记录详情页
    ElMessage.info(`检测会话ID: ${videoResult.value.session_id}`)
  }
}

// 重置视频结果
const resetVideoResult = () => {
  videoResult.value = null
  videoProgress.value = 0
  videoProgressText.value = ''
}

// 下载结果
const downloadResult = () => {
  if (!resultImage.value) return
  
  const link = document.createElement('a')
  link.href = resultImage.value
  link.download = `detection_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.jpg`
  link.click()
}

// 加载设置
const loadSettings = async () => {
  try {
    const res = await api.detection.getSettings()
    if (res.success) {
      settings.confidence = res.data.confidence_threshold
      modelLoaded.value = res.data.model_loaded
    }
    
    // 加载跳帧设置
    const frameSkipRes = await api.detection.getFrameSkip()
    if (frameSkipRes.success) {
      settings.frameSkip = frameSkipRes.data.frame_skip
    }
    
    // 加载 GPU 信息
    await refreshGpuInfo()
  } catch (e) {
    console.error('Load settings error:', e)
  }
}

// 更新跳帧设置
const updateFrameSkip = async (value) => {
  try {
    await api.detection.setFrameSkip({ frame_skip: value })
  } catch (e) {
    console.error('Update frame skip error:', e)
  }
}

// 加载行为类别
const loadClasses = async () => {
  try {
    const res = await api.detection.getClasses()
    if (res.success) {
      behaviorClasses.value = res.data
    }
  } catch (e) {
    console.error('Load classes error:', e)
  }
}

// 更新时间统计（从检测结果中）
const updateTimeStats = (behaviorDuration) => {
  // 更新行为时间
  for (const [name, seconds] of Object.entries(behaviorDuration)) {
    timeStats.behavior_duration[name] = seconds
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    timeStats.behavior_duration_formatted[name] = `${minutes}:${secs.toString().padStart(2, '0')}`
  }
  
  // 计算总时间（所有行为时间之和的最大值作为参考）
  const totalSeconds = Math.max(...Object.values(behaviorDuration), 0)
  timeStats.total_time = totalSeconds
  const totalMinutes = Math.floor(totalSeconds / 60)
  const totalSecs = Math.floor(totalSeconds % 60)
  timeStats.total_time_formatted = `${totalMinutes}:${totalSecs.toString().padStart(2, '0')}`
}

// 加载时间统计
const loadTimeStats = async () => {
  try {
    const res = await api.detection.getTimeStatistics()
    if (res.success) {
      timeStats.total_time = res.data.total_time || 0
      timeStats.total_time_formatted = res.data.total_time_formatted || '0:00'
      timeStats.frame_count = res.data.frame_count || 0
      timeStats.behavior_duration = res.data.behavior_duration || {}
      timeStats.behavior_duration_formatted = res.data.behavior_duration_formatted || {}
    }
  } catch (e) {
    console.error('Load time stats error:', e)
  }
}

// 重置时间统计
const resetTimeStats = async (showMessage = false) => {
  try {
    const res = await api.detection.resetTimeStatistics()
    if (res.success) {
      timeStats.total_time = 0
      timeStats.total_time_formatted = '0:00'
      timeStats.frame_count = 0
      timeStats.behavior_duration = {}
      timeStats.behavior_duration_formatted = {}
      if (showMessage) {
        ElMessage.success('时间统计已重置')
      }
    }
  } catch (e) {
    console.error('Reset time stats error:', e)
    if (showMessage) {
      ElMessage.error('重置失败')
    }
  }
}

// ==================== 历史记录功能 ====================

// 加载历史记录
const loadHistory = async () => {
  historyLoading.value = true
  try {
    const res = await api.detection.getHistory({
      page: historyPage.value,
      page_size: historyPageSize.value
    })
    if (res.success) {
      historyList.value = res.data.items || []
      historyTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('Load history error:', e)
    ElMessage.error('加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

// 显示历史详情
const showHistoryDetail = async (row) => {
  showDetailDialog.value = true
  detailLoading.value = true
  historyDetail.value = null
  
  try {
    const res = await api.detection.getDetail(row.session_id)
    if (res.success) {
      historyDetail.value = res.data
    } else {
      ElMessage.error('获取详情失败')
    }
  } catch (e) {
    console.error('Get detail error:', e)
    ElMessage.error('获取详情失败')
  } finally {
    detailLoading.value = false
  }
}

// 删除历史记录
const deleteHistoryItem = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除会话 ${row.session_id} 的检测记录吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    const res = await api.detection.deleteHistory(row.session_id)
    if (res.success) {
      ElMessage.success('删除成功')
      loadHistory()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('Delete history error:', e)
      ElMessage.error('删除失败')
    }
  }
}

// 获取来源类型标签
const getSourceTypeTag = (type) => {
  const typeMap = {
    'image': 'primary',
    'video': 'success',
    'video_optimized': 'success',
    'realtime': 'warning',
    'desktop': 'info'
  }
  return typeMap[type] || 'info'
}

// 获取来源类型标签文字
const getSourceTypeLabel = (type) => {
  const labelMap = {
    'image': '图片检测',
    'video': '视频检测',
    'video_optimized': 'GPU视频',
    'realtime': '实时检测',
    'desktop': '桌面应用'
  }
  return labelMap[type] || type
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadSettings()
  loadClasses()
  loadHistory()  // 加载历史记录
  // 不再自动加载时间统计，等开始检测时再重置
})

onUnmounted(() => {
  stopRealTimeDetection()
})
</script>


<style lang="scss" scoped>
.detection-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-right {
      display: flex;
      align-items: center;
    }
  }
  
  .detection-card {
    min-height: 550px;
    
    .detection-area {
      min-height: 480px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    
    .start-area {
      text-align: center;
      padding: 40px;
      
      .start-icon {
        font-size: 64px;
        color: #409EFF;
        margin-bottom: 20px;
      }
      
      h3 {
        margin: 0 0 10px;
        color: #303133;
      }
      
      p {
        color: #909399;
        margin-bottom: 20px;
      }
      
      .upload-buttons {
        display: flex;
        gap: 16px;
        justify-content: center;
        flex-wrap: wrap;
      }
      
      .upload-btn {
        display: inline-block;
      }
    }
    
    .video-processing-area {
      text-align: center;
      padding: 20px;
      
      .video-preview-container {
        position: relative;
        width: 100%;
        max-width: 800px;
        margin: 0 auto 20px;
        background: #000;
        border-radius: 8px;
        overflow: hidden;
        
        .video-preview {
          display: none;
        }
        
        .video-canvas {
          display: none;
        }
        
        .video-output {
          width: 100%;
          display: block;
        }
      }
      
      .processing-info {
        max-width: 500px;
        margin: 0 auto;
        
        .progress-text {
          margin: 10px 0;
          color: #606266;
        }
        
        .processing-stats {
          display: flex;
          justify-content: center;
          gap: 20px;
          margin-top: 10px;
          
          span {
            color: #909399;
            font-size: 14px;
          }
        }
      }
    }
    
    .video-result-area {
      padding: 20px;
      
      .video-stats {
        text-align: center;
        
        p {
          margin: 5px 0;
          color: #606266;
        }
      }
      
      .video-behavior-summary {
        margin-top: 20px;
        padding: 16px;
        background: #f5f7fa;
        border-radius: 8px;
        
        h4 {
          margin: 0 0 12px;
          color: #303133;
        }
        
        .behavior-stat-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #e4e7ed;
          
          &:last-child {
            border-bottom: none;
          }
        }
      }
    }
    
    .realtime-area {
      width: 100%;
      
      .video-container {
        position: relative;
        width: 100%;
        background: #000;
        border-radius: 8px;
        overflow: hidden;
        
        .camera-video {
          width: 100%;
          display: block;
        }
        
        .detection-canvas {
          display: none;
        }
        
        .output-canvas {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
      }
      
      .camera-controls {
        margin-top: 16px;
        text-align: center;
        display: flex;
        gap: 12px;
        justify-content: center;
      }
    }
    
    .result-area {
      width: 100%;
      text-align: center;
      
      .result-image {
        max-width: 100%;
        max-height: 400px;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      }
      
      .result-controls {
        margin-top: 16px;
        display: flex;
        gap: 12px;
        justify-content: center;
      }
    }
  }
  
  .settings-card {
    margin-bottom: 16px;
    
    :deep(.el-slider) {
      padding-right: 60px;
    }
    
    .setting-hint {
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
    }
  }
  
  .stats-card {
    margin-bottom: 16px;
    
    .stats-overview {
      display: flex;
      justify-content: space-around;
      margin-bottom: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid #eee;
      
      .stat-item {
        text-align: center;
        
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #409EFF;
        }
        
        .stat-label {
          font-size: 12px;
          color: #909399;
          margin-top: 4px;
        }
        
        &.normal .stat-value { color: #67C23A; }
        &.warning .stat-value { color: #F56C6C; }
      }
    }
    
    .behavior-list {
      .section-title {
        font-size: 14px;
        color: #606266;
        margin-bottom: 12px;
        font-weight: 500;
      }
      
      .behavior-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f5f5f5;
        
        &:last-child { border-bottom: none; }
        
        .behavior-name {
          font-size: 13px;
          color: #606266;
        }
      }
    }
  }
  
  .detections-card {
    margin-bottom: 16px;
    max-height: 250px;
    overflow-y: auto;
    
    .detection-list {
      .detection-item {
        padding: 8px 10px;
        margin-bottom: 6px;
        background: #f5f7fa;
        border-radius: 6px;
        border-left: 3px solid #67C23A;
        
        &.warning {
          border-left-color: #F56C6C;
          background: #fef0f0;
        }
        
        .det-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .det-class {
            font-weight: 500;
            color: #303133;
            font-size: 13px;
          }
        }
      }
    }
  }
  
  .time-stats-card {
    margin-bottom: 16px;
    
    .total-time {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid #eee;
      margin-bottom: 12px;
      
      .time-label {
        font-size: 14px;
        color: #606266;
      }
      
      .time-value {
        font-size: 20px;
        font-weight: bold;
        color: #409EFF;
      }
    }
    
    .time-list {
      .time-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px solid #f5f5f5;
        
        &:last-child { border-bottom: none; }
        
        .time-name {
          font-size: 13px;
          color: #606266;
        }
        
        .time-duration {
          font-size: 14px;
          font-weight: 500;
          color: #67C23A;
          
          &.warning {
            color: #F56C6C;
          }
        }
      }
    }
  }
  
  .gpu-card {
    margin-bottom: 16px;
    
    .gpu-info {
      margin-bottom: 16px;
      
      .gpu-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .gpu-label {
          font-weight: 500;
          color: #606266;
          min-width: 80px;
        }
        
        .gpu-value {
          color: #303133;
          font-family: 'Courier New', monospace;
          font-size: 13px;
        }
      }
    }
    
    .gpu-controls {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
    }
  }
  
  .classes-card {
    .class-list {
      .class-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 0;
        border-bottom: 1px solid #f5f5f5;
        
        &:last-child { border-bottom: none; }
        
        .class-color {
          width: 14px;
          height: 14px;
          border-radius: 3px;
        }
        
        .class-name {
          flex: 1;
          font-size: 13px;
          color: #606266;
        }
      }
    }
  }
}

.setting-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

// 历史记录样式
.history-card {
  :deep(.el-card__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      span {
        font-weight: 500;
        font-size: 15px;
      }
      
      .el-button {
        color: white;
        border-color: rgba(255, 255, 255, 0.5);
        
        &:hover {
          background: rgba(255, 255, 255, 0.1);
        }
      }
    }
  }
  
  .behavior-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
  }
  
  .warning-text {
    color: #F56C6C;
    font-weight: bold;
  }
  
  .pagination-wrapper {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}

// 详情对话框样式
.detail-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
  
  .detail-info {
    p {
      margin: 6px 0;
      color: #606266;
      font-size: 14px;
      
      strong {
        color: #303133;
        margin-right: 8px;
      }
    }
  }
  
  .detail-stats {
    display: flex;
    gap: 16px;
    
    .stat-box {
      text-align: center;
      padding: 12px 20px;
      background: #f5f7fa;
      border-radius: 8px;
      min-width: 80px;
      
      .stat-num {
        font-size: 24px;
        font-weight: bold;
        color: #409EFF;
      }
      
      .stat-label {
        font-size: 12px;
        color: #909399;
        margin-top: 4px;
      }
      
      &.normal .stat-num { color: #67C23A; }
      &.warning .stat-num { color: #F56C6C; }
    }
  }
}

.detail-behavior-summary {
  margin-bottom: 20px;
  
  h4 {
    margin: 0 0 12px;
    color: #303133;
    font-size: 14px;
  }
  
  .behavior-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 12px;
    
    .behavior-card {
      text-align: center;
      padding: 12px;
      background: #f0f9eb;
      border-radius: 8px;
      border: 1px solid #e1f3d8;
      
      &.warning {
        background: #fef0f0;
        border-color: #fde2e2;
      }
      
      .behavior-count {
        font-size: 20px;
        font-weight: bold;
        color: #67C23A;
      }
      
      &.warning .behavior-count {
        color: #F56C6C;
      }
      
      .behavior-name {
        font-size: 12px;
        color: #606266;
        margin-top: 4px;
      }
    }
  }
}

.detail-detections {
  h4 {
    margin: 0 0 12px;
    color: #303133;
    font-size: 14px;
  }
  
  .bbox-text {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: #909399;
  }
}
</style>
