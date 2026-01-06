<template>
  <PageLayout
    title="系统概览"
    subtitle="智慧教育平台数据中心"
    title-icon="HomeFilled"
    :loading="statsLoading"
    :error="statsError"
    @retry="loadStats"
  >
    <!-- 统计卡片组 -->
    <StatCardGroup 
      :cards="statCards" 
      :columns="4"
      :gutter="20"
      @card-click="handleStatCardClick"
      @card-retry="loadStats"
      class="dashboard__stats"
    />

    <!-- 系统通知区域 -->
    <div v-if="notifications.length > 0" class="dashboard__notifications">
      <el-alert
        v-for="notification in notifications"
        :key="notification.id"
        :title="notification.title"
        :type="notification.type"
        :description="notification.description"
        :closable="notification.closable"
        show-icon
        @close="handleNotificationClose(notification.id)"
      />
    </div>
    
    <el-row :gutter="20" class="dashboard__charts">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>行为趋势分析</span>
              <div class="period-switch">
                <button 
                  :class="['period-btn', { active: chartPeriod === 'week' }]"
                  @click="switchPeriod('week')"
                >本周</button>
                <button 
                  :class="['period-btn', { active: chartPeriod === 'month' }]"
                  @click="switchPeriod('month')"
                >本月</button>
              </div>
            </div>
          </template>
          <LineChart
            :xAxisData="trendChartData.xAxisData"
            :data="trendChartData.data"
            :loading="chartLoading"
            :error="chartError"
            :showArea="true"
            yAxisName="专注度(%)"
            height="260px"
            @retry="loadTrendData"
          />
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="chart-card pie-card">
          <template #header>
            <span>行为分布</span>
          </template>
          <PieChart
            :data="pieChartData"
            :loading="statsLoading"
            height="200px"
            :showLegend="false"
            :radius="['35%', '60%']"
          />
          <div class="pie-legend">
            <div v-for="(item, index) in pieChartData" :key="index" class="legend-item">
              <span class="legend-dot" :style="{ background: item.itemStyle?.color || chartColors[index] }"></span>
              <span class="legend-name">{{ item.name }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 关系图和热力图 -->
    <el-row :gutter="20" class="dashboard__relation">
      <el-col :span="12">
        <el-card class="chart-card relation-card">
          <template #header>
            <span>数据关系图</span>
          </template>
          <RelationGraph
            :nodes="relationGraphData.nodes"
            :links="relationGraphData.links"
            :categories="relationGraphData.categories"
            :loading="relationLoading"
            height="320px"
            :draggable="true"
            :repulsion="120"
          />
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="chart-card heatmap-card">
          <template #header>
            <span>行为时段热力图</span>
          </template>
          <HeatmapChart
            :data="heatmapData.data"
            :xAxisData="heatmapData.xAxisData"
            :yAxisData="heatmapData.yAxisData"
            :loading="heatmapLoading"
            height="320px"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="dashboard__bottom">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>预警行为排名</span>
              <el-button size="small" type="primary" text @click="$router.push('/alert')">
                查看全部
              </el-button>
            </div>
          </template>
          <el-table :data="warningRanking" style="width: 100%">
            <el-table-column prop="behavior_name_cn" label="行为类型" />
            <el-table-column prop="count" label="次数" width="100" />
            <el-table-column prop="percentage" label="占比" width="100">
              <template #default="{ row }">{{ row.percentage }}%</template>
            </el-table-column>
            <el-table-column prop="alert_level" label="预警级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.alert_level)">{{ getLevelText(row.alert_level) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button 
              v-for="action in quickActions"
              :key="action.key"
              :type="action.type"
              :icon="action.icon"
              @click="handleQuickAction(action)"
              class="quick-action-btn"
            >
              {{ action.label }}
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </PageLayout>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import StatCardGroup from '@/components/StatCardGroup.vue'
import PageLayout from '@/components/PageLayout.vue'
import { LineChart, PieChart, RelationGraph, HeatmapChart } from '@/components/charts'
import { behaviorNames, getBehaviorColor } from '@/components/charts'

const router = useRouter()
const chartPeriod = ref('week')
const chartColors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#00D4FF', '#FF6B6B']

const switchPeriod = (period) => {
  chartPeriod.value = period
  loadTrendData()
}

const chartLoading = ref(false)
const chartError = ref('')
const relationLoading = ref(false)
const heatmapLoading = ref(false)
const statsLoading = ref(false)
const statsError = ref('')

const stats = reactive({
  totalSessions: 0,
  totalStudents: 0,
  totalAlerts: 0,
  attentionRate: 0
})

const warningRanking = ref([])
const trendData = ref([])
const behaviorDist = ref({})

const trendChartData = computed(() => ({
  xAxisData: trendData.value.map(d => d.date),
  data: trendData.value.map(d => (d.attention_rate * 100).toFixed(1))
}))

const pieChartData = computed(() => {
  return Object.entries(behaviorDist.value).map(([key, val]) => ({
    name: behaviorNames[key] || key,
    value: val,
    itemStyle: { color: getBehaviorColor(key) }
  }))
})

const relationGraphData = computed(() => {
  const categories = [{ name: '学生' }, { name: '行为' }, { name: '预警' }]
  const nodes = []
  const links = []
  
  const students = ['学生A', '学生B', '学生C', '学生D', '学生E']
  students.forEach((name, i) => {
    nodes.push({ id: `student_${i}`, name, category: 0, value: Math.floor(Math.random() * 20) + 10, symbolSize: 35 })
  })
  
  const behaviors = ['专注', '走神', '睡觉', '交谈', '举手']
  behaviors.forEach((name, i) => {
    nodes.push({ id: `behavior_${i}`, name, category: 1, value: Math.floor(Math.random() * 30) + 5, symbolSize: 28 })
  })
  
  const alerts = ['轻度预警', '中度预警', '严重预警']
  alerts.forEach((name, i) => {
    nodes.push({ id: `alert_${i}`, name, category: 2, value: Math.floor(Math.random() * 15) + 3, symbolSize: 25 })
  })
  
  students.forEach((_, si) => {
    const behaviorCount = Math.floor(Math.random() * 3) + 1
    for (let j = 0; j < behaviorCount; j++) {
      const bi = Math.floor(Math.random() * behaviors.length)
      links.push({ source: `student_${si}`, target: `behavior_${bi}`, value: Math.floor(Math.random() * 10) + 1 })
    }
  })
  
  behaviors.forEach((_, bi) => {
    if (bi > 1) {
      const ai = Math.min(bi - 2, alerts.length - 1)
      links.push({ source: `behavior_${bi}`, target: `alert_${ai}`, value: Math.floor(Math.random() * 5) + 1 })
    }
  })
  
  return { nodes, links, categories }
})

const heatmapData = computed(() => {
  const hours = ['8:00', '9:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00']
  const days = ['周一', '周二', '周三', '周四', '周五']
  const data = []
  days.forEach((_, di) => {
    hours.forEach((_, hi) => {
      data.push([hi, di, Math.floor(Math.random() * 100)])
    })
  })
  return { xAxisData: hours, yAxisData: days, data }
})

const notifications = ref([
  { id: 1, title: '系统维护通知', description: '系统将于今晚22:00-24:00进行维护升级', type: 'warning', closable: true }
])

const quickActions = computed(() => [
  { key: 'detection', label: '开始检测', type: 'primary', icon: 'VideoCamera' },
  { key: 'alert', label: '查看预警', type: 'warning', icon: 'Bell' },
  { key: 'portrait', label: '学业画像', type: 'info', icon: 'DataAnalysis' }
])

const getLevelType = (level) => level >= 3 ? 'danger' : level >= 2 ? 'warning' : 'info'
const getLevelText = (level) => level >= 3 ? '严重' : level >= 2 ? '中度' : '轻度'

const statCards = computed(() => [
  { key: 'sessions', title: '检测会话', value: stats.totalSessions, icon: 'VideoCamera', color: 'primary', clickable: true, loading: statsLoading.value, error: statsError.value },
  { key: 'students', title: '学生人数', value: stats.totalStudents, icon: 'User', color: 'success', clickable: true, loading: statsLoading.value, error: statsError.value },
  { key: 'alerts', title: '预警次数', value: stats.totalAlerts, icon: 'Bell', color: 'warning', clickable: true, loading: statsLoading.value, error: statsError.value },
  { key: 'attention', title: '平均专注度', value: stats.attentionRate, unit: '%', icon: 'TrendCharts', color: 'info', clickable: true, loading: statsLoading.value, error: statsError.value, trend: { direction: 'up', value: 5.2, period: '较上周' } }
])

const handleStatCardClick = ({ card }) => {
  switch (card.key) {
    case 'sessions': router.push('/detection'); break
    case 'students': router.push('/users'); break
    case 'alerts': router.push('/alert'); break
    case 'attention': router.push('/portrait'); break
  }
}

const handleQuickAction = (action) => {
  switch (action.key) {
    case 'detection': router.push('/detection'); break
    case 'alert': router.push('/alert'); break
    case 'portrait': router.push('/portrait'); break
  }
}

const handleNotificationClose = (id) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) notifications.value.splice(index, 1)
}

const loadStats = async () => {
  statsLoading.value = true
  statsError.value = ''
  try {
    const res = await api.portrait.getOverview()
    if (res.success) {
      stats.totalSessions = res.data.total_sessions || 0
      stats.totalStudents = res.data.total_students || 0
      stats.totalAlerts = res.data.warning_count || 0
      stats.attentionRate = ((res.data.avg_attention_rate || 0) * 100).toFixed(1)
      behaviorDist.value = res.data.behavior_distribution || {}
    }
  } catch (e) { 
    console.error('Load stats error:', e)
    statsError.value = '加载失败'
  } finally {
    statsLoading.value = false
  }
}

const loadWarningRanking = async () => {
  try {
    const res = await api.portrait.getWarningRanking()
    if (res.success) warningRanking.value = res.data
  } catch (e) { console.error('Load warning ranking error:', e) }
}

const loadTrendData = async () => {
  chartLoading.value = true
  chartError.value = ''
  try {
    const days = chartPeriod.value === 'week' ? 7 : 30
    const res = await api.portrait.getAttentionTrend({ days })
    if (res.success) trendData.value = res.data
  } catch (e) { 
    console.error('Load trend error:', e)
    chartError.value = '加载失败'
  } finally {
    chartLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadWarningRanking()
  loadTrendData()
})
</script>

<style lang="scss" scoped>
.dashboard__stats { margin-bottom: 20px; }
.dashboard__notifications { margin-bottom: 20px; }
.dashboard__notifications :deep(.el-alert) { margin-bottom: 10px; border-radius: 10px; }
.dashboard__notifications :deep(.el-alert:last-child) { margin-bottom: 0; }
.dashboard__charts { margin-bottom: 20px; }
.dashboard__relation { margin-bottom: 20px; }
.dashboard__bottom { margin-bottom: 20px; }

.chart-card {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: visible !important;
  height: 350px;
}

.pie-card {
  height: 350px !important;
  :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    padding: 12px 16px !important;
    height: calc(100% - 52px);
    overflow: hidden;
  }
}

.pie-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px 16px;
  padding: 10px 0;
  margin-top: 8px;
  max-height: 80px;
  overflow-y: auto;
}

.chart-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  font-weight: 600;
  padding: 14px 20px;
  border-bottom: none !important;
  border-radius: 12px 12px 0 0;
}

.chart-card :deep(.el-card__body) {
  padding: 16px;
  height: calc(100% - 52px);
  overflow: visible;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header > span { font-size: 15px; font-weight: 600; }

.period-switch { display: flex; gap: 0; border-radius: 6px; overflow: hidden; }

.period-btn {
  padding: 6px 14px;
  font-size: 12px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  cursor: pointer;
  transition: all 0.3s;
  &:first-child { border-radius: 6px 0 0 6px; }
  &:last-child { border-radius: 0 6px 6px 0; }
  &:hover { background: rgba(255, 255, 255, 0.35); }
  &.active { background: rgba(255, 255, 255, 0.95); color: #667eea; font-weight: 500; }
}

.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #606266; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-name { white-space: nowrap; }
.relation-card, .heatmap-card { height: 400px !important; }

.dashboard__bottom :deep(.el-card) {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: hidden;
}

.dashboard__bottom :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  font-weight: 600;
  padding: 14px 20px;
  border-bottom: none !important;
}

.dashboard__bottom :deep(.el-card__body) { padding: 16px; }

.dashboard__bottom :deep(.el-table) {
  --el-table-border-color: #f0f2f5;
  --el-table-header-bg-color: #f8fafc;
  .el-table__header th { background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%); font-weight: 600; color: #303133; }
  .el-table__row:hover > td { background: #f5f7fa; }
}

.quick-actions { display: flex; gap: 16px; flex-wrap: wrap; padding: 10px 0; }
.quick-actions :deep(.el-button) { flex: 1; min-width: 120px; height: 48px; border-radius: 10px; font-size: 14px; font-weight: 500; transition: all 0.3s; }
.quick-actions :deep(.el-button:hover) { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); }
.quick-actions :deep(.el-button--primary) { background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%); border: none; }
.quick-actions :deep(.el-button--warning) { background: linear-gradient(135deg, #e6a23c 0%, #f0c78a 100%); border: none; }
.quick-actions :deep(.el-button--info) { background: linear-gradient(135deg, #909399 0%, #b4b7bd 100%); border: none; }

@media (max-width: 1200px) {
  .dashboard__charts :deep(.el-col), .dashboard__relation :deep(.el-col), .dashboard__bottom :deep(.el-col) { margin-bottom: 20px; }
}

@media (max-width: 768px) {
  .quick-actions { flex-direction: column; }
  .quick-actions :deep(.el-button) { min-width: 100%; }
  .pie-legend { gap: 8px; }
}
</style>
