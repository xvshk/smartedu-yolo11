<template>
  <div class="portrait-page">
    <!-- 老师/管理员视图 -->
    <template v-if="isTeacher">
      <!-- 视图切换和班级筛选 -->
      <div class="filter-bar">
        <el-radio-group v-model="viewMode" class="view-switch">
          <el-radio-button label="class">班级画像</el-radio-button>
          <el-radio-button label="student">学生画像</el-radio-button>
        </el-radio-group>
        
        <div class="class-filter" v-if="viewMode === 'class'">
          <span class="filter-label">班级筛选：</span>
          <el-select v-model="selectedClassId" placeholder="全部班级" clearable style="width: 200px" @change="onClassChange">
            <el-option label="全部班级" :value="null" />
            <el-option
              v-for="c in classList"
              :key="c.class_id"
              :label="c.class_name"
              :value="c.class_id"
            />
          </el-select>
        </div>
      </div>

      <!-- 班级画像视图 -->
      <template v-if="viewMode === 'class'">
        <!-- 概览卡片 -->
        <el-row :gutter="16" class="overview-row">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-value">{{ overview.total_sessions || 0 }}</div>
              <div class="stat-label">检测会话数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-value">{{ overview.total_students || 0 }}</div>
              <div class="stat-label">学生总数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-value highlight">{{ formatPercent(overview.avg_attention_rate) }}</div>
              <div class="stat-label">平均注意力指数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card warning">
              <div class="stat-value">{{ overview.warning_count || 0 }}</div>
              <div class="stat-label">预警行为数</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 图表区域 -->
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card>
              <template #header>行为分布</template>
              <div ref="behaviorChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <div class="chart-header">
                  <span>注意力趋势</span>
                  <el-radio-group v-model="trendDays" size="small" @change="loadAttentionTrend">
                    <el-radio-button :label="7">7天</el-radio-button>
                    <el-radio-button :label="30">30天</el-radio-button>
                  </el-radio-group>
                </div>
              </template>
              <div ref="trendChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 预警排名 -->
        <el-card class="warning-card">
          <template #header>
            <div class="chart-header">
              <span>预警行为排名</span>
              <el-button type="primary" size="small" @click="exportData">导出数据</el-button>
            </div>
          </template>
          <el-table :data="warningRanking" stripe>
            <el-table-column prop="behavior_name_cn" label="行为类型" />
            <el-table-column prop="count" label="次数" />
            <el-table-column prop="percentage" label="占比">
              <template #default="{ row }">{{ row.percentage }}%</template>
            </el-table-column>
            <el-table-column prop="alert_level" label="预警级别">
              <template #default="{ row }">
                <el-tag :type="getAlertType(row.alert_level)">{{ getAlertText(row.alert_level) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>

      <!-- 老师查看学生画像 -->
      <template v-else>
        <el-card v-if="!studentPortrait" class="student-select-card">
          <el-form inline>
            <el-form-item label="选择班级">
              <el-select v-model="studentFilterClassId" placeholder="全部班级" clearable style="width: 180px" @change="onStudentClassChange">
                <el-option label="全部班级" :value="null" />
                <el-option
                  v-for="c in classList"
                  :key="c.class_id"
                  :label="c.class_name"
                  :value="c.class_id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="选择学生">
              <el-select v-model="selectedStudentId" filterable placeholder="请选择学生" style="width: 280px">
                <el-option
                  v-for="s in filteredStudentList"
                  :key="s.student_id"
                  :label="`${s.name} (${s.student_number})`"
                  :value="s.student_id"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadStudentPortrait(selectedStudentId)">查看画像</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        <template v-if="studentPortrait">
          <el-button @click="studentPortrait = null" style="margin-bottom: 16px">返回</el-button>
          <StudentPortraitView :portrait="studentPortrait" :suggestions="suggestions" />
        </template>
      </template>
    </template>

    <!-- 学生视图 - 只能看自己的画像 -->
    <template v-else>
      <el-card class="student-header">
        <h2>我的学业画像</h2>
        <p class="subtitle">查看您的课堂表现和改进建议</p>
      </el-card>
      
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      <template v-else-if="studentPortrait">
        <StudentPortraitView :portrait="studentPortrait" :suggestions="suggestions" :show-rank="false" />
      </template>
      <el-empty v-else :description="loadError || '暂无画像数据'" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { Loading } from '@element-plus/icons-vue'
import StudentPortraitView from '@/components/StudentPortraitView.vue'

const userStore = useUserStore()

// 判断是否是老师/管理员
const isTeacher = computed(() => {
  const role = userStore.user?.role || localStorage.getItem('userRole') || ''
  return ['admin', 'teacher'].includes(role)
})

// 获取当前学生ID（学生登录时）
const currentStudentId = computed(() => {
  return userStore.user?.student_id || localStorage.getItem('studentId')
})

const viewMode = ref('class')
const trendDays = ref(7)
const selectedStudentId = ref(null)
const selectedClassId = ref(null)
const studentFilterClassId = ref(null)
const studentList = ref([])
const classList = ref([])
const loading = ref(false)
const loadError = ref('')

// 数据
const overview = ref({})
const behaviorDist = ref({})
const attentionTrend = ref([])
const warningRanking = ref([])
const studentPortrait = ref(null)
const suggestions = ref([])

// 图表引用
const behaviorChartRef = ref(null)
const trendChartRef = ref(null)
let behaviorChart = null
let trendChart = null

// 行为中文名映射
const behaviorNames = {
  handrise: '举手', read: '阅读', write: '书写',
  sleep: '睡觉', stand: '站立', using_electronic_devices: '使用电子设备', talk: '交谈'
}

// 行为颜色配置
const behaviorColors = {
  handrise: '#67C23A',
  read: '#409EFF', 
  write: '#E6A23C',
  sleep: '#F56C6C',
  stand: '#909399',
  using_electronic_devices: '#E040FB',
  talk: '#FF7043'
}

// 过滤后的学生列表
const filteredStudentList = computed(() => {
  if (!studentFilterClassId.value) return studentList.value
  return studentList.value.filter(s => s.class_id === studentFilterClassId.value)
})

const formatPercent = (val) => val ? (val * 100).toFixed(1) + '%' : '0%'
const getAlertType = (level) => level >= 3 ? 'danger' : level >= 2 ? 'warning' : 'info'
const getAlertText = (level) => level >= 3 ? '高' : level >= 2 ? '中' : '低'

// 渲染行为分布饼图
const renderBehaviorChart = () => {
  if (!behaviorChartRef.value) return
  if (behaviorChart) behaviorChart.dispose()
  behaviorChart = echarts.init(behaviorChartRef.value)
  
  const dist = overview.value.behavior_distribution || {}
  const data = Object.entries(dist).map(([key, val]) => ({
    name: behaviorNames[key] || key,
    value: val,
    itemStyle: { color: behaviorColors[key] || '#909399' }
  })).filter(d => d.value > 0)
  
  // 如果没有数据，显示空状态
  if (data.length === 0) {
    behaviorChart.setOption({
      title: {
        text: '暂无行为数据',
        subtext: '请先进行课堂行为检测',
        left: 'center',
        top: 'center',
        textStyle: { color: '#909399', fontSize: 16 },
        subtextStyle: { color: '#c0c4cc', fontSize: 13 }
      }
    })
    return
  }
  
  behaviorChart.setOption({
    tooltip: { 
      trigger: 'item', 
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#eee',
      borderWidth: 1,
      textStyle: { color: '#333' }
    },
    legend: { 
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 12 }
    },
    series: [{ 
      type: 'pie', 
      radius: ['35%', '65%'], 
      center: ['50%', '45%'],
      data, 
      label: { 
        show: true,
        formatter: '{b}\n{d}%',
        fontSize: 11
      },
      labelLine: {
        length: 10,
        length2: 10
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      }
    }]
  })
}

// 渲染趋势折线图
const renderTrendChart = () => {
  if (!trendChartRef.value) return
  if (trendChart) trendChart.dispose()
  trendChart = echarts.init(trendChartRef.value)
  
  const dates = attentionTrend.value.map(d => d.date)
  const rates = attentionTrend.value.map(d => (d.attention_rate * 100).toFixed(1))
  
  // 如果没有数据，显示空状态
  if (dates.length === 0) {
    trendChart.setOption({
      title: {
        text: '暂无趋势数据',
        subtext: '请先进行课堂行为检测',
        left: 'center',
        top: 'center',
        textStyle: { color: '#909399', fontSize: 16 },
        subtextStyle: { color: '#c0c4cc', fontSize: 13 }
      }
    })
    return
  }
  
  trendChart.setOption({
    tooltip: { 
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#eee',
      borderWidth: 1,
      textStyle: { color: '#333' },
      formatter: (params) => {
        const p = params[0]
        return `${p.axisValue}<br/>注意力指数: <b>${p.value}%</b>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: { 
      type: 'category', 
      data: dates,
      axisLabel: {
        fontSize: 11,
        rotate: dates.length > 10 ? 45 : 0
      }
    },
    yAxis: { 
      type: 'value', 
      name: '注意力(%)', 
      min: 0, 
      max: 100,
      splitLine: {
        lineStyle: { type: 'dashed' }
      }
    },
    series: [{ 
      type: 'line', 
      data: rates, 
      smooth: true, 
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: '#409EFF'
      },
      itemStyle: {
        color: '#409EFF'
      },
      areaStyle: { 
        opacity: 0.2,
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      },
      markLine: {
        silent: true,
        data: [
          { yAxis: 50, lineStyle: { color: '#F56C6C', type: 'dashed' }, label: { formatter: '警戒线 50%' } }
        ]
      }
    }]
  })
}

// 班级切换
const onClassChange = () => {
  loadClassData()
}

// 学生筛选班级切换
const onStudentClassChange = () => {
  selectedStudentId.value = null
}

// 加载班级列表
const loadClassList = async () => {
  try {
    const res = await api.portrait.getClasses()
    if (res.success) classList.value = res.data
  } catch (e) { console.error(e) }
}

// 加载班级数据（老师用）
const loadClassData = async () => {
  try {
    const params = selectedClassId.value ? { class_id: selectedClassId.value } : {}
    const [overviewRes, distRes, rankRes] = await Promise.all([
      api.portrait.getOverview(params),
      api.portrait.getBehaviorDistribution(params),
      api.portrait.getWarningRanking(params)
    ])
    if (overviewRes.success) overview.value = overviewRes.data
    if (distRes.success) behaviorDist.value = distRes.data
    if (rankRes.success) warningRanking.value = rankRes.data
    await loadAttentionTrend()
    nextTick(() => renderBehaviorChart())
  } catch (e) {
    ElMessage.error('加载数据失败')
  }
}

const loadAttentionTrend = async () => {
  try {
    const params = { days: trendDays.value }
    if (selectedClassId.value) params.class_id = selectedClassId.value
    const res = await api.portrait.getAttentionTrend(params)
    if (res.success) {
      attentionTrend.value = res.data
      nextTick(() => renderTrendChart())
    }
  } catch (e) { console.error(e) }
}

// 加载学生列表
const loadStudentList = async () => {
  try {
    const res = await api.portrait.getStudents()
    if (res.success) studentList.value = res.data
  } catch (e) { console.error(e) }
}

// 加载学生画像
const loadStudentPortrait = async (studentId) => {
  if (!studentId) {
    loadError.value = '无法获取学生ID，请重新登录'
    console.error('No studentId provided')
    return
  }
  
  loading.value = true
  loadError.value = ''
  
  try {
    const [portraitRes, suggestRes] = await Promise.all([
      api.portrait.getStudentPortrait(studentId),
      api.portrait.getStudentSuggestions(studentId)
    ])
    
    if (portraitRes.success) {
      studentPortrait.value = portraitRes.data
    } else {
      loadError.value = portraitRes.message || '加载失败'
      ElMessage.error(portraitRes.message || '学生不存在')
    }
    if (suggestRes.success) suggestions.value = suggestRes.data
  } catch (e) {
    console.error('Load student portrait error:', e)
    loadError.value = '加载学生画像失败: ' + (e.message || '网络错误')
    ElMessage.error('加载学生画像失败')
  } finally {
    loading.value = false
  }
}

// 导出数据
const exportData = async () => {
  try {
    const params = selectedClassId.value ? { class_id: selectedClassId.value } : {}
    const res = await api.portrait.exportData(params)
    if (res.success) {
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `portrait_export_${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    }
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

watch(viewMode, (val) => {
  if (val === 'class') nextTick(() => { loadClassData() })
  if (val === 'student') loadStudentList()
})

onMounted(() => {
  if (isTeacher.value) {
    loadClassList()
    loadClassData()
    loadStudentList()
  } else if (currentStudentId.value) {
    loadStudentPortrait(currentStudentId.value)
  } else {
    console.warn('Student ID not found, cannot load portrait')
    ElMessage.warning('无法获取学生ID，请重新登录')
  }
})
</script>

<style lang="scss" scoped>
.portrait-page {
  padding: 4px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.15);
}

.class-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  color: #606266;
  font-size: 14px;
  font-weight: 500;
}

.view-switch {
  margin-bottom: 0;
}

:deep(.view-switch .el-radio-button__inner) {
  border-color: #667eea;
  color: #667eea;
}

:deep(.view-switch .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  box-shadow: -1px 0 0 0 #667eea;
}

.overview-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2) !important;
}

:deep(.stat-card .el-card__body) {
  padding: 24px 16px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #409EFF;
  line-height: 1.2;
  margin-bottom: 8px;
}

.stat-label {
  color: #909399;
  font-size: 13px;
  font-weight: 500;
}

.stat-card.warning .stat-value {
  color: #F56C6C;
}

.stat-card.warning::before {
  background: linear-gradient(135deg, #F56C6C 0%, #ff8a8a 100%);
}

.stat-card.above-avg .stat-value {
  color: #67C23A;
}

.stat-card.above-avg::before {
  background: linear-gradient(135deg, #67C23A 0%, #95d475 100%);
}

.highlight {
  color: #67C23A !important;
}

.student-header {
  margin-bottom: 20px;
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: hidden;
}

.student-header::before {
  content: '';
  display: block;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:deep(.student-header .el-card__body) {
  padding: 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

.student-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.student-header .subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: #667eea;
  font-size: 16px;
}

.loading-container .el-icon {
  margin-right: 12px;
  font-size: 24px;
}

/* 图表卡片样式 */
:deep(.el-card) {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: hidden;
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  font-weight: 600;
  font-size: 15px;
  padding: 14px 20px;
  border-bottom: none !important;
}

:deep(.el-card__body) {
  padding: 16px 20px;
}

.chart-container {
  height: 300px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.chart-header .el-radio-group) {
  display: flex;
  gap: 0;
  border-radius: 6px;
  overflow: hidden;
}

:deep(.chart-header .el-radio-button__inner) {
  padding: 6px 14px;
  font-size: 12px;
  border: none !important;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

:deep(.chart-header .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.95);
  color: #667eea;
  font-weight: 500;
}

.warning-card {
  margin-top: 20px;
}

:deep(.warning-card .el-table) {
  --el-table-border-color: #f0f2f5;
  --el-table-header-bg-color: #f8fafc;
}

:deep(.warning-card .el-table__header th) {
  background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%);
  font-weight: 600;
  color: #303133;
}

:deep(.warning-card .el-table__row:hover > td) {
  background: #f5f7fa;
}

.student-select-card {
  margin-bottom: 20px;
}

:deep(.student-select-card .el-card__body) {
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
}

:deep(.student-select-card .el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.student-select-card .el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
}

:deep(.student-select-card .el-button--primary:hover) {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* 返回按钮样式 */
:deep(.el-button) {
  border-radius: 8px;
}

/* 响应式 */
@media (max-width: 1200px) {
  :deep(.el-col) {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}
</style>
