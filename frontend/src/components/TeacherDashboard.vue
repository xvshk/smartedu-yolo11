<template>
  <div class="teacher-dashboard">
    <!-- 教师概览统计 -->
    <StatCardGroup 
      :cards="teacherStatCards" 
      :columns="4"
      :gutter="20"
      @card-click="handleStatClick"
      class="teacher-dashboard__stats"
    />

    <!-- 班级实时状况 -->
    <el-row :gutter="20" class="teacher-dashboard__classes">
      <el-col :span="16">
        <el-card class="class-status-card">
          <template #header>
            <div class="card-header">
              <span>班级实时状况</span>
              <div class="header-actions">
                <el-select v-model="selectedClass" placeholder="选择班级" size="small" @change="loadClassData">
                  <el-option 
                    v-for="cls in teacherClasses" 
                    :key="cls.id" 
                    :label="cls.name" 
                    :value="cls.id" 
                  />
                </el-select>
                <el-button size="small" @click="refreshClassData">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="selectedClassData" class="class-overview">
            <!-- 班级基本信息 -->
            <div class="class-info">
              <div class="info-item">
                <span class="label">班级名称:</span>
                <span class="value">{{ selectedClassData.name }}</span>
              </div>
              <div class="info-item">
                <span class="label">学生人数:</span>
                <span class="value">{{ selectedClassData.totalStudents }}</span>
              </div>
              <div class="info-item">
                <span class="label">在线人数:</span>
                <span class="value online">{{ selectedClassData.onlineStudents }}</span>
              </div>
              <div class="info-item">
                <span class="label">平均专注度:</span>
                <span class="value" :class="getAttentionClass(selectedClassData.averageAttention)">
                  {{ selectedClassData.averageAttention }}%
                </span>
              </div>
            </div>

            <!-- 学生状态列表 -->
            <div class="students-status">
              <div class="status-header">
                <h4>学生状态监控</h4>
                <div class="status-filters">
                  <el-radio-group v-model="statusFilter" size="small" @change="filterStudents">
                    <el-radio-button label="all">全部</el-radio-button>
                    <el-radio-button label="attention">专注度低</el-radio-button>
                    <el-radio-button label="alert">有预警</el-radio-button>
                  </el-radio-group>
                </div>
              </div>

              <div class="students-grid">
                <div 
                  v-for="student in filteredStudents" 
                  :key="student.id"
                  class="student-card"
                  :class="getStudentStatusClass(student)"
                  @click="viewStudentDetail(student)"
                >
                  <div class="student-avatar">
                    <img v-if="student.avatar" :src="student.avatar" :alt="student.name" />
                    <div v-else class="avatar-placeholder">
                      {{ student.name.charAt(0) }}
                    </div>
                  </div>
                  <div class="student-info">
                    <div class="student-name">{{ student.name }}</div>
                    <div class="student-status">
                      <span class="attention-score">专注度: {{ student.attentionScore }}%</span>
                      <el-tag 
                        v-if="student.alertLevel > 0" 
                        :type="getAlertTagType(student.alertLevel)"
                        size="small"
                      >
                        {{ getAlertText(student.alertLevel) }}
                      </el-tag>
                    </div>
                  </div>
                  <div class="student-actions">
                    <el-button 
                      size="small" 
                      circle 
                      @click.stop="quickIntervention(student)"
                      title="快速干预"
                    >
                      <el-icon><Bell /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-else description="请选择班级查看详情" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="intervention-card">
          <template #header>
            <span>实时干预操作</span>
          </template>

          <div class="intervention-panel">
            <div class="quick-actions">
              <h4>快速操作</h4>
              <div class="action-buttons">
                <el-button 
                  v-for="action in quickInterventions" 
                  :key="action.key"
                  :type="action.type"
                  size="small"
                  @click="executeQuickAction(action)"
                  class="action-btn"
                >
                  <el-icon>
                    <component :is="action.icon" />
                  </el-icon>
                  {{ action.label }}
                </el-button>
              </div>
            </div>

            <div class="recent-interventions">
              <h4>最近干预记录</h4>
              <div class="intervention-list">
                <div 
                  v-for="intervention in recentInterventions" 
                  :key="intervention.id"
                  class="intervention-item"
                >
                  <div class="intervention-time">
                    {{ formatTime(intervention.createdAt) }}
                  </div>
                  <div class="intervention-content">
                    <div class="intervention-student">{{ intervention.studentName }}</div>
                    <div class="intervention-action">{{ intervention.action }}</div>
                  </div>
                  <div class="intervention-status">
                    <el-tag :type="intervention.status === 'effective' ? 'success' : 'warning'" size="small">
                      {{ intervention.status === 'effective' ? '有效' : '待观察' }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学生详细分析 -->
    <el-row :gutter="20" class="teacher-dashboard__analysis">
      <el-col :span="12">
        <el-card class="analysis-card">
          <template #header>
            <div class="card-header">
              <span>班级专注度趋势</span>
              <el-radio-group v-model="analysisPeriod" size="small" @change="loadAnalysisData">
                <el-radio-button label="today">今日</el-radio-button>
                <el-radio-button label="week">本周</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="attentionTrendRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="behavior-card">
          <template #header>
            <span>行为分布分析</span>
          </template>
          <div ref="behaviorChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 干预记录和跟踪 -->
    <el-card class="tracking-card">
      <template #header>
        <div class="card-header">
          <span>干预效果跟踪</span>
          <el-button size="small" type="primary" @click="showTrackingDialog = true">
            <el-icon><DataAnalysis /></el-icon>
            详细分析
          </el-button>
        </div>
      </template>

      <el-table :data="interventionTracking" style="width: 100%">
        <el-table-column prop="studentName" label="学生姓名" width="120" />
        <el-table-column prop="interventionType" label="干预类型" width="120" />
        <el-table-column prop="interventionTime" label="干预时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.interventionTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="beforeScore" label="干预前专注度" width="140">
          <template #default="{ row }">
            <span :class="getScoreClass(row.beforeScore)">{{ row.beforeScore }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="afterScore" label="干预后专注度" width="140">
          <template #default="{ row }">
            <span :class="getScoreClass(row.afterScore)">{{ row.afterScore }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="improvement" label="改善程度" width="120">
          <template #default="{ row }">
            <el-tag :type="row.improvement > 0 ? 'success' : 'danger'" size="small">
              {{ row.improvement > 0 ? '+' : '' }}{{ row.improvement }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="effectiveness" label="效果评估" width="120">
          <template #default="{ row }">
            <el-rate 
              v-model="row.effectiveness" 
              :max="5" 
              size="small" 
              disabled 
              show-score
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="viewInterventionDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 干预详情对话框 -->
    <el-dialog v-model="showInterventionDialog" title="干预操作" width="500px">
      <el-form :model="interventionForm" label-width="100px">
        <el-form-item label="学生">
          <span>{{ selectedStudent?.name }}</span>
        </el-form-item>
        <el-form-item label="干预类型">
          <el-select v-model="interventionForm.type" placeholder="选择干预类型">
            <el-option label="提醒专注" value="attention_reminder" />
            <el-option label="课堂提问" value="question" />
            <el-option label="个别指导" value="individual_guidance" />
            <el-option label="座位调整" value="seat_adjustment" />
          </el-select>
        </el-form-item>
        <el-form-item label="干预说明">
          <el-input 
            v-model="interventionForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请描述具体的干预措施"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInterventionDialog = false">取消</el-button>
        <el-button type="primary" @click="submitIntervention">确认干预</el-button>
      </template>
    </el-dialog>

    <!-- 跟踪分析对话框 -->
    <el-dialog v-model="showTrackingDialog" title="干预效果详细分析" width="800px">
      <div class="tracking-analysis">
        <div class="analysis-summary">
          <div class="summary-item">
            <div class="summary-number">{{ trackingSummary.totalInterventions }}</div>
            <div class="summary-label">总干预次数</div>
          </div>
          <div class="summary-item">
            <div class="summary-number">{{ trackingSummary.effectiveRate }}%</div>
            <div class="summary-label">有效率</div>
          </div>
          <div class="summary-item">
            <div class="summary-number">{{ trackingSummary.averageImprovement }}%</div>
            <div class="summary-label">平均改善度</div>
          </div>
        </div>
        <div ref="trackingChartRef" class="tracking-chart"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import StatCardGroup from './StatCardGroup.vue'
import api from '@/api'

// 响应式数据
const loading = ref(false)
const selectedClass = ref(null)
const statusFilter = ref('all')
const analysisPeriod = ref('today')

const teacherStats = ref({
  totalClasses: 0,
  totalStudents: 0,
  activeAlerts: 0,
  interventionCount: 0
})

const teacherClasses = ref([])

const selectedClassData = ref(null)
const classStudents = ref([])

const quickInterventions = ref([
  {
    key: 'attention_reminder',
    label: '专注提醒',
    type: 'warning',
    icon: 'Bell'
  },
  {
    key: 'question',
    label: '课堂提问',
    type: 'primary',
    icon: 'ChatDotRound'
  },
  {
    key: 'individual_guidance',
    label: '个别指导',
    type: 'success',
    icon: 'User'
  }
])

const recentInterventions = ref([
  {
    id: 1,
    studentName: '张三',
    action: '专注提醒',
    createdAt: new Date(Date.now() - 5 * 60 * 1000),
    status: 'effective'
  },
  {
    id: 2,
    studentName: '李四',
    action: '课堂提问',
    createdAt: new Date(Date.now() - 15 * 60 * 1000),
    status: 'pending'
  }
])

const interventionTracking = ref([
  {
    id: 1,
    studentName: '张三',
    interventionType: '专注提醒',
    interventionTime: new Date(Date.now() - 30 * 60 * 1000),
    beforeScore: 65,
    afterScore: 82,
    improvement: 17,
    effectiveness: 4
  },
  {
    id: 2,
    studentName: '李四',
    interventionType: '课堂提问',
    interventionTime: new Date(Date.now() - 60 * 60 * 1000),
    beforeScore: 58,
    afterScore: 75,
    improvement: 17,
    effectiveness: 4
  }
])

const trackingSummary = ref({
  totalInterventions: 25,
  effectiveRate: 78,
  averageImprovement: 15
})

// 对话框状态
const showInterventionDialog = ref(false)
const showTrackingDialog = ref(false)
const selectedStudent = ref(null)
const interventionForm = ref({
  type: '',
  description: ''
})

// 图表引用
const attentionTrendRef = ref(null)
const behaviorChartRef = ref(null)
const trackingChartRef = ref(null)
let attentionChart = null
let behaviorChart = null
let trackingChart = null

// 计算属性
const teacherStatCards = computed(() => [
  {
    key: 'classes',
    title: '管理班级',
    value: teacherStats.value.totalClasses,
    icon: 'School',
    color: 'primary',
    clickable: true
  },
  {
    key: 'students',
    title: '学生总数',
    value: teacherStats.value.totalStudents,
    icon: 'User',
    color: 'success',
    clickable: true
  },
  {
    key: 'alerts',
    title: '活跃预警',
    value: teacherStats.value.activeAlerts,
    icon: 'Warning',
    color: 'danger',
    clickable: true
  },
  {
    key: 'interventions',
    title: '今日干预',
    value: teacherStats.value.interventionCount,
    icon: 'Bell',
    color: 'warning',
    clickable: true,
    trend: {
      direction: 'up',
      value: 12,
      period: '较昨日'
    }
  }
])

const filteredStudents = computed(() => {
  if (!classStudents.value) return []
  
  switch (statusFilter.value) {
    case 'attention':
      return classStudents.value.filter(s => s.attentionScore < 70)
    case 'alert':
      return classStudents.value.filter(s => s.alertLevel > 0)
    default:
      return classStudents.value
  }
})

// 方法
const handleStatClick = ({ card }) => {
  switch (card.key) {
    case 'classes':
      // 查看班级管理
      break
    case 'students':
      // 查看学生列表
      break
    case 'alerts':
      // 查看预警详情
      break
    case 'interventions':
      // 查看干预记录
      break
  }
}

const loadClassData = async () => {
  if (!selectedClass.value) return
  
  try {
    const res = await api.dashboard.getClassStudents(selectedClass.value)
    if (res.success) {
      selectedClassData.value = res.data.classInfo
      classStudents.value = res.data.students || []
    }
  } catch (error) {
    console.error('Load class data error:', error)
  }
}

const refreshClassData = () => {
  loadClassData()
  ElMessage.success('数据已刷新')
}

const filterStudents = () => {
  // 筛选逻辑已在计算属性中实现
}

const viewStudentDetail = (student) => {
  ElMessage.info(`查看学生详情: ${student.name}`)
  // 这里可以跳转到学生详情页面
}

const quickIntervention = (student) => {
  selectedStudent.value = student
  showInterventionDialog.value = true
}

const executeQuickAction = (action) => {
  ElMessage.success(`执行${action.label}操作`)
  // 这里实现具体的快速操作逻辑
}

const submitIntervention = async () => {
  try {
    // 提交干预记录
    ElMessage.success('干预记录已提交')
    showInterventionDialog.value = false
    
    // 重置表单
    interventionForm.value = {
      type: '',
      description: ''
    }
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

const viewInterventionDetail = (row) => {
  ElMessage.info(`查看干预详情: ${row.studentName}`)
}

const loadAnalysisData = () => {
  nextTick(() => {
    renderAttentionChart()
    renderBehaviorChart()
  })
}

// 工具方法
const getAttentionClass = (score) => {
  if (score >= 80) return 'high'
  if (score >= 60) return 'medium'
  return 'low'
}

const getStudentStatusClass = (student) => {
  if (student.alertLevel > 0) return 'has-alert'
  if (student.attentionScore < 70) return 'low-attention'
  return 'normal'
}

const getAlertTagType = (level) => {
  const types = { 1: 'warning', 2: 'warning', 3: 'danger' }
  return types[level] || 'info'
}

const getAlertText = (level) => {
  const texts = { 1: '轻度', 2: '中度', 3: '严重' }
  return texts[level] || '正常'
}

const getScoreClass = (score) => {
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-medium'
  return 'score-low'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

// 图表渲染
const renderAttentionChart = () => {
  if (!attentionTrendRef.value) return
  if (attentionChart) attentionChart.dispose()
  
  attentionChart = echarts.init(attentionTrendRef.value)
  
  // 模拟数据
  const data = Array.from({ length: 24 }, (_, i) => ({
    time: `${i.toString().padStart(2, '0')}:00`,
    attention: Math.floor(Math.random() * 30) + 60
  }))
  
  attentionChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: data.map(d => d.time),
      boundaryGap: false 
    },
    yAxis: { 
      type: 'value', 
      name: '专注度(%)', 
      min: 0, 
      max: 100 
    },
    series: [{
      type: 'line',
      data: data.map(d => d.attention),
      smooth: true,
      areaStyle: { opacity: 0.3 },
      lineStyle: { color: '#409EFF' },
      itemStyle: { color: '#409EFF' }
    }]
  })
}

const renderBehaviorChart = () => {
  if (!behaviorChartRef.value) return
  if (behaviorChart) behaviorChart.dispose()
  
  behaviorChart = echarts.init(behaviorChartRef.value)
  
  const data = [
    { name: '专注听讲', value: 45 },
    { name: '举手发言', value: 15 },
    { name: '低头看书', value: 20 },
    { name: '交谈讨论', value: 10 },
    { name: '其他行为', value: 10 }
  ]
  
  behaviorChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  })
}

const renderTrackingChart = () => {
  if (!trackingChartRef.value) return
  if (trackingChart) trackingChart.dispose()
  
  trackingChart = echarts.init(trackingChartRef.value)
  
  // 干预效果趋势图
  const data = Array.from({ length: 7 }, (_, i) => ({
    date: `1/${i + 1}`,
    effectiveness: Math.floor(Math.random() * 30) + 60
  }))
  
  trackingChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: data.map(d => d.date) 
    },
    yAxis: { 
      type: 'value', 
      name: '有效率(%)', 
      min: 0, 
      max: 100 
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.effectiveness),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 1, color: '#188df0' }
        ])
      }
    }]
  })
}

// 数据加载
const loadTeacherStats = async () => {
  try {
    // 加载统计数据
    const statsRes = await api.dashboard.getTeacherStats()
    if (statsRes.success) {
      teacherStats.value = {
        totalClasses: statsRes.data.totalClasses || 0,
        totalStudents: statsRes.data.totalStudents || 0,
        activeAlerts: statsRes.data.activeAlerts || 0,
        interventionCount: statsRes.data.detectionCount || 0
      }
    }
    
    // 加载班级列表
    const classesRes = await api.dashboard.getTeacherClasses()
    if (classesRes.success) {
      teacherClasses.value = classesRes.data || []
      // 自动选择第一个班级
      if (teacherClasses.value.length > 0 && !selectedClass.value) {
        selectedClass.value = teacherClasses.value[0].id
        loadClassData()
      }
    }
  } catch (error) {
    console.error('Load teacher stats error:', error)
  }
}

// watch 引用
let unwatch = null

// 生命周期
onMounted(() => {
  loadTeacherStats()
  loadAnalysisData()
  
  // 监听对话框打开事件
  unwatch = watch(showTrackingDialog, (newVal) => {
    if (newVal) {
      nextTick(() => renderTrackingChart())
    }
  })
})

onUnmounted(() => {
  if (unwatch) {
    unwatch()
  }
  attentionChart?.dispose()
  behaviorChart?.dispose()
  trackingChart?.dispose()
})
</script>

<style lang="scss" scoped>
.teacher-dashboard {
  &__stats {
    margin-bottom: var(--spacing-section-gap);
  }

  &__classes {
    margin-bottom: var(--spacing-section-gap);
  }

  &__analysis {
    margin-bottom: var(--spacing-section-gap);
  }

  .class-status-card {
    .class-overview {
      .class-info {
        display: flex;
        gap: var(--spacing-xl);
        margin-bottom: var(--spacing-lg);
        padding: var(--spacing-base);
        background: var(--color-background-secondary);
        border-radius: var(--border-radius-lg);

        .info-item {
          display: flex;
          flex-direction: column;
          align-items: center;

          .label {
            font-size: var(--font-size-sm);
            color: var(--color-text-secondary);
            margin-bottom: var(--spacing-xs);
          }

          .value {
            font-size: var(--font-size-lg);
            font-weight: var(--font-weight-medium);
            color: var(--color-text-primary);

            &.online {
              color: var(--color-success);
            }

            &.high {
              color: var(--color-success);
            }

            &.medium {
              color: var(--color-warning);
            }

            &.low {
              color: var(--color-danger);
            }
          }
        }
      }

      .students-status {
        .status-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-base);

          h4 {
            margin: 0;
            color: var(--color-text-primary);
          }
        }

        .students-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: var(--spacing-base);
          max-height: 400px;
          overflow-y: auto;
        }

        .student-card {
          display: flex;
          align-items: center;
          padding: var(--spacing-base);
          border-radius: var(--border-radius-lg);
          background: var(--color-background-secondary);
          cursor: pointer;
          transition: var(--transition-base);

          &:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-card);
          }

          &.has-alert {
            border-left: 4px solid var(--color-danger);
          }

          &.low-attention {
            border-left: 4px solid var(--color-warning);
          }

          .student-avatar {
            width: 40px;
            height: 40px;
            margin-right: var(--spacing-base);
            border-radius: 50%;
            overflow: hidden;
            background: var(--color-primary);
            display: flex;
            align-items: center;
            justify-content: center;

            img {
              width: 100%;
              height: 100%;
              object-fit: cover;
            }

            .avatar-placeholder {
              color: white;
              font-weight: var(--font-weight-medium);
            }
          }

          .student-info {
            flex: 1;

            .student-name {
              font-weight: var(--font-weight-medium);
              color: var(--color-text-primary);
              margin-bottom: var(--spacing-xs);
            }

            .student-status {
              display: flex;
              align-items: center;
              gap: var(--spacing-sm);

              .attention-score {
                font-size: var(--font-size-sm);
                color: var(--color-text-secondary);
              }
            }
          }

          .student-actions {
            display: flex;
            gap: var(--spacing-xs);
          }
        }
      }
    }
  }

  .intervention-card {
    .intervention-panel {
      .quick-actions {
        margin-bottom: var(--spacing-lg);

        h4 {
          margin: 0 0 var(--spacing-base) 0;
          color: var(--color-text-primary);
        }

        .action-buttons {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);

          .action-btn {
            justify-content: flex-start;
          }
        }
      }

      .recent-interventions {
        h4 {
          margin: 0 0 var(--spacing-base) 0;
          color: var(--color-text-primary);
        }

        .intervention-list {
          max-height: 300px;
          overflow-y: auto;
        }

        .intervention-item {
          display: flex;
          align-items: center;
          padding: var(--spacing-sm);
          border-radius: var(--border-radius-base);
          background: var(--color-background-primary);
          margin-bottom: var(--spacing-sm);

          .intervention-time {
            font-size: var(--font-size-xs);
            color: var(--color-text-disabled);
            margin-right: var(--spacing-sm);
            white-space: nowrap;
          }

          .intervention-content {
            flex: 1;

            .intervention-student {
              font-weight: var(--font-weight-medium);
              color: var(--color-text-primary);
            }

            .intervention-action {
              font-size: var(--font-size-sm);
              color: var(--color-text-secondary);
            }
          }

          .intervention-status {
            margin-left: var(--spacing-sm);
          }
        }
      }
    }
  }

  .analysis-card,
  .behavior-card {
    .chart-container {
      height: 300px;
    }
  }

  .tracking-card {
    .score-high {
      color: var(--color-success);
    }

    .score-medium {
      color: var(--color-warning);
    }

    .score-low {
      color: var(--color-danger);
    }
  }

  .tracking-analysis {
    .analysis-summary {
      display: flex;
      justify-content: space-around;
      margin-bottom: var(--spacing-lg);

      .summary-item {
        text-align: center;

        .summary-number {
          font-size: var(--font-size-3xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-primary);
        }

        .summary-label {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-top: var(--spacing-xs);
        }
      }
    }

    .tracking-chart {
      height: 300px;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: var(--spacing-sm);
    }
  }
}

// 响应式适配
@media (max-width: 767px) {
  .teacher-dashboard {
    .class-info {
      flex-direction: column !important;
      gap: var(--spacing-base) !important;
    }

    .students-grid {
      grid-template-columns: 1fr !important;
    }

    .analysis-summary {
      flex-direction: column !important;
      gap: var(--spacing-base) !important;
    }
  }
}
</style>