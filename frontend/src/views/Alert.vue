<template>
  <PageLayout
    title="预警管理"
    subtitle="智能行为预警与干预系统"
    title-icon="Bell"
    :actions="pageActions"
  >
    <!-- 顶部统计卡片 -->
    <StatCardGroup 
      :cards="alertStatCards" 
      :columns="4"
      :gutter="20"
      @card-click="handleAlertStatClick"
      class="alert-page__stats"
    />

    <!-- 数据关联组件 -->
    <DataRelation
      v-if="hasDataRelations"
      :relations="dataRelations"
      @relation-click="handleRelationClick"
      class="alert-page__relations"
    />

    <!-- 图表区域 -->
    <el-row :gutter="20" class="alert-page__charts">
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>预警级别分布</span>
          </template>
          <PieChart
            :data="levelChartData"
            :loading="statsLoading"
            :colors="levelColors"
            height="220px"
            :showLabel="true"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>行为类型分布</span>
          </template>
          <BarChart
            :xAxisData="behaviorChartData.xAxisData"
            :data="behaviorChartData.data"
            :loading="statsLoading"
            height="220px"
            :showLabel="true"
            :colors="['#409EFF']"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>预警处理漏斗</span>
          </template>
          <FunnelChart
            :data="funnelChartData"
            :loading="statsLoading"
            height="220px"
            :showConversionRate="true"
            :colors="['#409EFF', '#67C23A', '#E6A23C', '#F56C6C']"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 主内容区 -->
    <el-row :gutter="20">
      <!-- 左侧：预警列表 -->
      <el-col :span="16">
        <el-card class="alert-list-card">
          <template #header>
            <div class="card-header">
              <span>预警列表</span>
              <div class="header-actions">
                <el-button size="small" @click="markAllRead" :disabled="unreadCount === 0">
                  全部已读
                </el-button>
                <el-button size="small" type="primary" @click="openRuleDialog">
                  <el-icon><Setting /></el-icon>
                  规则配置
                </el-button>
              </div>
            </div>
          </template>

          <!-- 筛选条件 -->
          <div class="filter-bar">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              @change="loadAlerts"
            />
            <el-select v-model="filterLevel" placeholder="预警级别" size="small" clearable @change="loadAlerts">
              <el-option label="正常" :value="0" />
              <el-option label="轻度预警" :value="1" />
              <el-option label="中度预警" :value="2" />
              <el-option label="严重预警" :value="3" />
            </el-select>
            <el-select v-model="filterBehavior" placeholder="行为类型" size="small" clearable @change="loadAlerts">
              <el-option label="睡觉" value="睡觉" />
              <el-option label="交谈" value="交谈" />
              <el-option label="使用电子设备" value="使用电子设备" />
              <el-option label="低头" value="低头" />
              <el-option label="站立" value="站立" />
            </el-select>
            <el-button size="small" @click="exportAlerts">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>

          <!-- 预警列表 -->
          <div class="alert-list" v-loading="loading">
            <div 
              v-for="alert in alerts" 
              :key="alert.alert_id" 
              class="alert-item"
              :class="{ unread: !alert.is_read, [`level-${alert.alert_level}`]: true }"
              @click="showAlertDetail(alert)"
            >
              <div class="alert-level-indicator" :class="`level-${alert.alert_level}`"></div>
              <div class="alert-content">
                <div class="alert-header">
                  <span class="behavior-type">{{ alert.behavior_type }}</span>
                  <el-tag :type="getLevelTagType(alert.alert_level)" size="small">
                    {{ getLevelName(alert.alert_level) }}
                  </el-tag>
                </div>
                <div class="alert-info">
                  <span>检测数量: {{ alert.behavior_count }}</span>
                  <span>置信度: {{ (alert.confidence * 100).toFixed(1) }}%</span>
                  <!-- 添加学生信息和跳转链接 -->
                  <span v-if="alert.student_name" class="student-link" @click.stop="navigateToStudent(alert)">
                    学生: {{ alert.student_name }}
                  </span>
                </div>
                <div class="alert-time">
                  {{ formatTime(alert.created_at) }}
                </div>
              </div>
              <div class="alert-actions">
                <el-button 
                  v-if="!alert.is_read" 
                  size="small" 
                  circle 
                  @click.stop="markRead(alert.alert_id)"
                >
                  <el-icon><Check /></el-icon>
                </el-button>
                <!-- 添加快速跳转按钮 -->
                <el-button 
                  size="small" 
                  circle 
                  @click.stop="navigateToStudent(alert)"
                  title="查看学生画像"
                >
                  <el-icon><User /></el-icon>
                </el-button>
              </div>
            </div>

            <el-empty v-if="alerts.length === 0 && !loading" description="暂无预警记录" />
          </div>

          <!-- 分页 -->
          <div class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadAlerts"
              @current-change="loadAlerts"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：预警趋势 -->
      <el-col :span="8">
        <el-card class="chart-card trend-card">
          <template #header>
            <div class="card-header">
              <span>预警趋势</span>
              <el-radio-group v-model="trendPeriod" size="small" @change="loadTrendData">
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <LineChart
            :xAxisData="trendChartData.xAxisData"
            :data="trendChartData.data"
            :loading="trendLoading"
            height="280px"
            :showArea="true"
            yAxisName="预警数"
          />
        </el-card>

        <el-card class="chart-card" style="margin-top: 20px;">
          <template #header>
            <span>时段分布</span>
          </template>
          <BarChart
            :xAxisData="hourlyChartData.xAxisData"
            :data="hourlyChartData.data"
            :loading="statsLoading"
            height="200px"
            :colors="['#67C23A']"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 预警详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="预警详情" width="600px">
      <div v-if="selectedAlert" class="alert-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="预警ID">{{ selectedAlert.alert_id }}</el-descriptions-item>
          <el-descriptions-item label="预警级别">
            <el-tag :type="getLevelTagType(selectedAlert.alert_level)">
              {{ getLevelName(selectedAlert.alert_level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="行为类型">{{ selectedAlert.behavior_type }}</el-descriptions-item>
          <el-descriptions-item label="检测数量">{{ selectedAlert.behavior_count }}</el-descriptions-item>
          <el-descriptions-item label="置信度">{{ (selectedAlert.confidence * 100).toFixed(1) }}%</el-descriptions-item>
          <el-descriptions-item label="预警类型">{{ selectedAlert.alert_type }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ formatTime(selectedAlert.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <div class="suggestions-section" v-if="selectedAlert.suggestions?.length">
          <h4>干预建议</h4>
          <ul>
            <li v-for="(suggestion, index) in selectedAlert.suggestions" :key="index">
              {{ suggestion }}
            </li>
          </ul>
        </div>

        <!-- 添加相关数据链接 -->
        <div class="related-data" v-if="selectedAlert.student_id">
          <h4>相关数据</h4>
          <el-button size="small" @click="navigateToStudent(selectedAlert)">
            <el-icon><User /></el-icon>
            查看学生画像
          </el-button>
          <el-button size="small" @click="navigateToDetection(selectedAlert)">
            <el-icon><VideoCamera /></el-icon>
            查看检测记录
          </el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="recordIntervention">记录干预</el-button>
      </template>
    </el-dialog>

    <!-- 规则配置对话框 -->
    <el-dialog v-model="showRuleDialog" title="预警规则配置" width="800px">
      <div class="rule-config">
        <el-button type="primary" size="small" style="margin-bottom: 15px;" @click="showCreateRuleDialog = true">
          <el-icon><Plus /></el-icon>
          添加规则
        </el-button>
        
        <el-table :data="rules" v-loading="rulesLoading">
          <el-table-column prop="rule_name" label="规则名称" />
          <el-table-column prop="rule_type" label="规则类型" width="100">
            <template #default="{ row }">
              {{ getRuleTypeName(row.rule_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="behavior_type" label="行为类型" width="120" />
          <el-table-column prop="alert_level" label="预警级别" width="100">
            <template #default="{ row }">
              <el-tag :type="getLevelTagType(row.alert_level)" size="small">
                {{ getLevelName(row.alert_level) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="toggleRule(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="editRule(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteRule(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 创建/编辑规则对话框 -->
    <el-dialog v-model="showCreateRuleDialog" :title="editingRule ? '编辑规则' : '创建规则'" width="600px">
      <el-form :model="ruleForm" :rules="ruleFormRules" ref="ruleFormRef" label-width="120px">
        <el-form-item label="规则名称" prop="rule_name">
          <el-input v-model="ruleForm.rule_name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="规则类型" prop="rule_type">
          <el-select v-model="ruleForm.rule_type" placeholder="请选择规则类型">
            <el-option label="频率规则" value="frequency" />
            <el-option label="阈值规则" value="threshold" />
            <el-option label="组合规则" value="combination" />
            <el-option label="持续时间" value="duration" />
          </el-select>
        </el-form-item>
        <el-form-item label="行为类型" prop="behavior_type">
          <el-select v-model="ruleForm.behavior_type" placeholder="请选择行为类型">
            <el-option label="睡觉" value="睡觉" />
            <el-option label="交谈" value="交谈" />
            <el-option label="使用电子设备" value="使用电子设备" />
            <el-option label="低头" value="低头" />
            <el-option label="站立" value="站立" />
          </el-select>
        </el-form-item>
        <el-form-item label="预警级别" prop="alert_level">
          <el-select v-model="ruleForm.alert_level" placeholder="请选择预警级别">
            <el-option label="正常" :value="0" />
            <el-option label="轻度预警" :value="1" />
            <el-option label="中度预警" :value="2" />
            <el-option label="严重预警" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值数量" prop="threshold_count">
          <el-input-number v-model="ruleForm.threshold_count" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="时间窗口(秒)" prop="time_window_seconds">
          <el-input-number v-model="ruleForm.time_window_seconds" :min="10" :max="3600" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="ruleForm.description" type="textarea" placeholder="请输入规则描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule" :loading="saveRuleLoading">
          {{ editingRule ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </PageLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, Download, Check, Plus, User, VideoCamera } from '@element-plus/icons-vue'
import api from '@/api'
import StatCardGroup from '@/components/StatCardGroup.vue'
import PageLayout from '@/components/PageLayout.vue'
import DataRelation from '@/components/DataRelation.vue'
import { PieChart, BarChart, LineChart, FunnelChart, getAlertLevelColor } from '@/components/charts'
import { useNavigationStore, navigationUtils } from '@/stores/navigation'

const navigationStore = useNavigationStore()

// 状态
const loading = ref(false)
const rulesLoading = ref(false)
const statsLoading = ref(false)
const trendLoading = ref(false)
const alerts = ref([])
const rules = ref([])
const statistics = ref({})
const unreadCount = ref(0)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const trendPeriod = ref('week')
const trendData = ref([])

// 筛选条件
const dateRange = ref(null)
const filterLevel = ref(null)
const filterBehavior = ref(null)

// 对话框
const showDetailDialog = ref(false)
const showRuleDialog = ref(false)
const showCreateRuleDialog = ref(false)
const selectedAlert = ref(null)

// 创建规则相关
const editingRule = ref(null)
const saveRuleLoading = ref(false)
const ruleFormRef = ref(null)
const ruleForm = ref({
  rule_name: '',
  rule_type: '',
  behavior_type: '',
  alert_level: 1,
  threshold_count: 1,
  time_window_seconds: 60,
  description: ''
})

const ruleFormRules = {
  rule_name: [
    { required: true, message: '请输入规则名称', trigger: 'blur' }
  ],
  rule_type: [
    { required: true, message: '请选择规则类型', trigger: 'change' }
  ],
  behavior_type: [
    { required: true, message: '请选择行为类型', trigger: 'change' }
  ],
  alert_level: [
    { required: true, message: '请选择预警级别', trigger: 'change' }
  ],
  threshold_count: [
    { required: true, message: '请输入阈值数量', trigger: 'blur' }
  ],
  time_window_seconds: [
    { required: true, message: '请输入时间窗口', trigger: 'blur' }
  ]
}

// 预警级别颜色
const levelColors = ['#67C23A', '#909399', '#E6A23C', '#F56C6C']

// 页面操作按钮
const pageActions = computed(() => [
  {
    label: '导出预警',
    type: 'default',
    icon: 'Download',
    onClick: exportAlerts
  },
  {
    label: '规则配置',
    type: 'primary',
    icon: 'Setting',
    onClick: openRuleDialog
  }
])

// 数据关联
const hasDataRelations = computed(() => {
  const context = navigationStore.getPageContext('fromDetection')
  return !!context
})

const dataRelations = computed(() => {
  const relations = []
  
  // 如果来自检测页面
  const detectionContext = navigationStore.getPageContext('fromDetection')
  if (detectionContext) {
    relations.push({
      type: 'detection',
      title: '检测会话',
      description: `来自检测会话: ${detectionContext.sessionId}`,
      data: detectionContext,
      action: () => navigationStore.navigateWithContext('/detection', { 
        sessionId: detectionContext.sessionId 
      })
    })
  }
  
  // 如果有选中的学生
  const studentContext = navigationStore.getPageContext('selectedStudent')
  if (studentContext) {
    relations.push({
      type: 'student',
      title: '学生画像',
      description: `查看 ${studentContext.name} 的详细画像`,
      data: studentContext,
      action: () => navigationUtils.createAlertStudentLink(
        selectedAlert.value?.alert_id,
        studentContext.id,
        studentContext.name
      ).onClick()
    })
  }
  
  return relations
})

// 级别名称映射
const levelNames = {
  0: '正常',
  1: '轻度预警',
  2: '中度预警',
  3: '严重预警'
}

const ruleTypeNames = {
  frequency: '频率规则',
  threshold: '阈值规则',
  combination: '组合规则',
  duration: '持续时间'
}

// 方法
const getLevelName = (level) => levelNames[level] || '未知'
const getRuleTypeName = (type) => ruleTypeNames[type] || type

// 图表数据计算属性
const levelChartData = computed(() => {
  if (!statistics.value.level_distribution) return []
  return Object.entries(statistics.value.level_distribution).map(([level, count]) => ({
    name: levelNames[level] || `级别${level}`,
    value: count,
    itemStyle: { color: getAlertLevelColor(parseInt(level)) }
  }))
})

const behaviorChartData = computed(() => {
  if (!statistics.value.behavior_distribution) {
    return { xAxisData: [], data: [] }
  }
  const entries = Object.entries(statistics.value.behavior_distribution)
  return {
    xAxisData: entries.map(([name]) => name),
    data: entries.map(([, count]) => count)
  }
})

const funnelChartData = computed(() => {
  const total = statistics.value.total || 0
  const read = total - unreadCount.value
  const processed = Math.floor(read * 0.7) // 模拟处理数据
  const resolved = Math.floor(processed * 0.8) // 模拟解决数据
  
  return [
    { name: '生成预警', value: total },
    { name: '已查看', value: read },
    { name: '已处理', value: processed },
    { name: '已解决', value: resolved }
  ]
})

const trendChartData = computed(() => {
  if (!trendData.value || trendData.value.length === 0) {
    return { xAxisData: [], data: [] }
  }
  return {
    xAxisData: trendData.value.map(d => d.date),
    data: trendData.value.map(d => d.count || 0)
  }
})

const hourlyChartData = computed(() => {
  if (!statistics.value.hourly_distribution) {
    // 生成模拟的时段分布数据
    const hours = ['8时', '9时', '10时', '11时', '14时', '15时', '16时', '17时']
    const data = hours.map(() => Math.floor(Math.random() * 20) + 5)
    return { xAxisData: hours, data }
  }
  const entries = Object.entries(statistics.value.hourly_distribution)
  return {
    xAxisData: entries.map(([hour]) => `${hour}时`),
    data: entries.map(([, count]) => count)
  }
})

// 预警统计卡片配置
const alertStatCards = computed(() => [
  {
    key: 'total',
    title: '总预警数',
    value: statistics.value.total || 0,
    icon: 'Bell',
    color: 'primary',
    clickable: true
  },
  {
    key: 'unread',
    title: '未读预警',
    value: unreadCount.value,
    icon: 'Message',
    color: 'warning',
    clickable: true
  },
  {
    key: 'severe',
    title: '严重预警',
    value: statistics.value.level_distribution?.[3] || 0,
    icon: 'Warning',
    color: 'danger',
    clickable: true
  },
  {
    key: 'trend',
    title: '较上周期',
    value: statistics.value.trend?.change_percent || 0,
    unit: '%',
    icon: 'TrendCharts',
    color: 'info',
    clickable: true,
    trend: statistics.value.trend ? {
      direction: statistics.value.trend.trend === 'up' ? 'up' : 
                statistics.value.trend.trend === 'down' ? 'down' : 'stable',
      value: Math.abs(statistics.value.trend.change_percent || 0)
    } : null
  }
])

// 处理预警统计卡片点击
const handleAlertStatClick = ({ card }) => {
  switch (card.key) {
    case 'total':
      // 显示所有预警
      filterLevel.value = null
      loadAlerts()
      break
    case 'unread':
      // 显示未读预警
      // 可以添加未读筛选逻辑
      break
    case 'severe':
      // 显示严重预警
      filterLevel.value = 3
      loadAlerts()
      break
    case 'trend':
      // 显示趋势详情
      break
  }
}

// 处理数据关联点击
const handleRelationClick = (relation) => {
  if (relation.action) {
    relation.action()
  }
}

// 导航到学生画像
const navigateToStudent = (alert) => {
  if (alert.student_id) {
    const link = navigationUtils.createAlertStudentLink(
      alert.alert_id,
      alert.student_id,
      alert.student_name || '未知学生'
    )
    link.onClick()
  } else {
    ElMessage.warning('该预警没有关联的学生信息')
  }
}

// 导航到检测记录
const navigateToDetection = (alert) => {
  if (alert.session_id) {
    navigationStore.navigateWithContext('/detection', {
      sessionId: alert.session_id,
      fromAlert: true,
      alertId: alert.alert_id
    })
  } else {
    ElMessage.warning('该预警没有关联的检测会话')
  }
}

const getLevelTagType = (level) => {
  const types = { 0: 'success', 1: 'warning', 2: 'warning', 3: 'danger' }
  return types[level] || 'info'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

// 加载预警列表
const loadAlerts = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (dateRange.value) {
      params.start_date = dateRange.value[0].toISOString().split('T')[0]
      params.end_date = dateRange.value[1].toISOString().split('T')[0]
    }
    if (filterLevel.value !== null) {
      params.alert_level = filterLevel.value
    }
    if (filterBehavior.value) {
      params.behavior_type = filterBehavior.value
    }

    console.log('Loading alerts with params:', params)
    const res = await api.alert.getAlerts(params)
    console.log('Alerts response:', res)
    if (res.success) {
      alerts.value = res.data.items
      total.value = res.data.total
      console.log('Loaded alerts:', alerts.value.length)
    } else {
      console.error('API returned success=false:', res)
    }
  } catch (error) {
    console.error('Load alerts error:', error)
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  statsLoading.value = true
  try {
    const res = await api.alert.getStatistics()
    if (res.success) {
      statistics.value = res.data
    }
  } catch (error) {
    console.error('Load statistics error:', error)
  } finally {
    statsLoading.value = false
  }
}

// 加载趋势数据
const loadTrendData = async () => {
  trendLoading.value = true
  try {
    const days = trendPeriod.value === 'week' ? 7 : 30
    const res = await api.alert.getTrend?.({ days }) || { success: false }
    if (res.success) {
      trendData.value = res.data
    } else {
      // 生成模拟趋势数据
      const mockData = []
      const now = new Date()
      for (let i = days - 1; i >= 0; i--) {
        const date = new Date(now)
        date.setDate(date.getDate() - i)
        mockData.push({
          date: `${date.getMonth() + 1}/${date.getDate()}`,
          count: Math.floor(Math.random() * 30) + 10
        })
      }
      trendData.value = mockData
    }
  } catch (error) {
    console.error('Load trend error:', error)
  } finally {
    trendLoading.value = false
  }
}

// 加载未读数量
const loadUnreadCount = async () => {
  try {
    const res = await api.alert.getUnreadAlerts({ limit: 100 })
    if (res.success) {
      unreadCount.value = res.data.count
    }
  } catch (error) {
    console.error('Load unread count error:', error)
  }
}

// 加载规则列表
const loadRules = async () => {
  rulesLoading.value = true
  try {
    console.log('Loading rules...')
    const res = await api.alert.getRules()
    console.log('Rules response:', res)
    if (res.success) {
      rules.value = res.data.items || []
      console.log('Loaded rules:', rules.value)
    } else {
      console.error('API returned success=false:', res)
    }
  } catch (error) {
    console.error('Load rules error:', error)
  } finally {
    rulesLoading.value = false
  }
}

// 标记已读
const markRead = async (alertId) => {
  try {
    await api.alert.markRead(alertId)
    const alert = alerts.value.find(a => a.alert_id === alertId)
    if (alert) alert.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (error) {
    ElMessage.error('标记失败')
  }
}

// 全部已读
const markAllRead = async () => {
  try {
    await api.alert.markAllRead()
    alerts.value.forEach(a => a.is_read = true)
    unreadCount.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 显示预警详情
const showAlertDetail = (alert) => {
  selectedAlert.value = alert
  showDetailDialog.value = true
  if (!alert.is_read) {
    markRead(alert.alert_id)
  }
}

// 导出预警
const exportAlerts = async () => {
  try {
    const params = { format: 'csv' }
    if (dateRange.value) {
      params.start_date = dateRange.value[0].toISOString().split('T')[0]
      params.end_date = dateRange.value[1].toISOString().split('T')[0]
    }
    
    const res = await api.alert.exportAlerts(params)
    
    const blob = new Blob([res], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `alerts_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 切换规则状态
const toggleRule = async (row) => {
  try {
    await api.alert.updateRule(row.rule_id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '规则已启用' : '规则已停用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

// 删除规则
const deleteRule = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该规则吗？', '提示', {
      type: 'warning'
    })
    await api.alert.deleteRule(row.rule_id)
    rules.value = rules.value.filter(r => r.rule_id !== row.rule_id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 编辑规则
const editRule = (row) => {
  editingRule.value = row
  ruleForm.value = {
    rule_name: row.rule_name,
    rule_type: row.rule_type,
    behavior_type: row.behavior_type,
    alert_level: row.alert_level,
    threshold_count: row.threshold_count,
    time_window_seconds: row.time_window_seconds,
    description: row.description || ''
  }
  showCreateRuleDialog.value = true
}

// 保存规则
const saveRule = async () => {
  if (!ruleFormRef.value) return
  
  try {
    await ruleFormRef.value.validate()
    saveRuleLoading.value = true
    
    if (editingRule.value) {
      // 更新规则
      const res = await api.alert.updateRule(editingRule.value.rule_id, ruleForm.value)
      ElMessage.success('规则更新成功')
      
      // 重新加载规则列表
      await loadRules()
    } else {
      // 创建规则
      const res = await api.alert.createRule(ruleForm.value)
      ElMessage.success('规则创建成功')
      
      // 重新加载规则列表
      await loadRules()
    }
    
    showCreateRuleDialog.value = false
    resetRuleForm()
    
  } catch (error) {
    console.error('Save rule error:', error)
    ElMessage.error(error.message || '保存失败')
  } finally {
    saveRuleLoading.value = false
  }
}

// 重置规则表单
const resetRuleForm = () => {
  editingRule.value = null
  ruleForm.value = {
    rule_name: '',
    rule_type: '',
    behavior_type: '',
    alert_level: 1,
    threshold_count: 1,
    time_window_seconds: 60,
    description: ''
  }
  if (ruleFormRef.value) {
    ruleFormRef.value.resetFields()
  }
}

// 记录干预
const recordIntervention = () => {
  ElMessage.info('干预记录功能开发中')
}

// 打开规则对话框
const openRuleDialog = async () => {
  showRuleDialog.value = true
  await loadRules()
}

// 生命周期
onMounted(() => {
  // 检查是否有来自其他页面的上下文
  const detectionContext = navigationStore.getPageContext('fromDetection')
  if (detectionContext && detectionContext.autoCreateAlert) {
    ElMessage.info('检测到异常行为，已自动生成预警')
  }
  
  loadAlerts()
  loadStatistics()
  loadUnreadCount()
  loadRules()
  loadTrendData()
})
</script>

<style lang="scss" scoped>
// 统计卡片区域
.alert-page__stats {
  margin-bottom: 20px;
}

.alert-page__relations {
  margin-bottom: 20px;
}

.alert-page__charts {
  margin-bottom: 20px;
  
  :deep(.el-card) {
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
    overflow: hidden;
    
    .el-card__header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
      color: #fff !important;
      font-weight: 600;
      padding: 14px 20px;
      border-bottom: none !important;
    }
  }
}

// 预警列表卡片 - 使用 :deep 确保样式穿透
.alert-list-card {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: hidden;
}

.alert-list-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  border-radius: 0 !important;
  padding: 16px 20px !important;
  border-bottom: none !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  > span {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
  }
}

.header-actions {
  display: flex;
  gap: 10px;
}

.header-actions :deep(.el-button) {
  background: rgba(255, 255, 255, 0.2) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: #fff !important;
}

.header-actions :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3) !important;
}

.header-actions :deep(.el-button--primary) {
  background: rgba(255, 255, 255, 0.95) !important;
  color: #667eea !important;
  border: none !important;
}

.header-actions :deep(.el-button--primary:hover) {
  background: #fff !important;
}

// 筛选栏
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%);
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

// 预警列表容器
.alert-list {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
  padding: 4px;
}

.alert-list::-webkit-scrollbar {
  width: 6px;
}

.alert-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.alert-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.alert-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

// 预警项目 - 基础样式
.alert-item {
  display: flex;
  align-items: center;
  padding: 16px 18px;
  border-radius: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  border: 1px solid #ebeef5;
  position: relative;
  overflow: hidden;
}

// 左侧装饰条
.alert-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #dcdfe6;
  transition: all 0.3s;
}

.alert-item:hover {
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
  transform: translateX(4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-color: #c0c4cc;
}

.alert-item:hover .alert-actions {
  opacity: 1;
}

// 未读状态
.alert-item.unread {
  background: linear-gradient(135deg, #fff 0%, #e6f4ff 100%);
  border-color: #91caff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.alert-item.unread::before {
  background: linear-gradient(180deg, #409eff 0%, #66b1ff 100%);
  width: 5px;
}

.alert-item.unread .behavior-type {
  color: #1677ff !important;
}

// 未读标记动画点
.alert-item.unread::after {
  content: '';
  position: absolute;
  top: 12px;
  right: 12px;
  width: 10px;
  height: 10px;
  background: #409eff;
  border-radius: 50%;
  animation: pulse 2s infinite;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.6);
}

// 级别3 - 严重预警
.alert-item.level-3::before {
  background: linear-gradient(180deg, #f56c6c 0%, #f89898 100%);
}

.alert-item.level-3.unread {
  background: linear-gradient(135deg, #fff 0%, #ffeded 100%);
  border-color: #ffb3b3;
  box-shadow: 0 2px 12px rgba(245, 108, 108, 0.2);
}

.alert-item.level-3.unread::after {
  background: #f56c6c;
  box-shadow: 0 0 8px rgba(245, 108, 108, 0.6);
}

// 级别2 - 中度预警
.alert-item.level-2::before {
  background: linear-gradient(180deg, #e6a23c 0%, #f0c78a 100%);
}

.alert-item.level-2.unread {
  background: linear-gradient(135deg, #fff 0%, #fff7e6 100%);
  border-color: #ffd591;
  box-shadow: 0 2px 12px rgba(230, 162, 60, 0.2);
}

.alert-item.level-2.unread::after {
  background: #e6a23c;
  box-shadow: 0 0 8px rgba(230, 162, 60, 0.6);
}

// 级别1 - 轻度预警
.alert-item.level-1::before {
  background: linear-gradient(180deg, #909399 0%, #b4b7bd 100%);
}

// 级别0 - 正常
.alert-item.level-0::before {
  background: linear-gradient(180deg, #67c23a 0%, #95d475 100%);
}

.alert-item.level-0.unread {
  background: linear-gradient(135deg, #fff 0%, #f0f9eb 100%);
  border-color: #b7eb8f;
  box-shadow: 0 2px 12px rgba(103, 194, 58, 0.2);
}

.alert-item.level-0.unread::after {
  background: #67c23a;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.6);
}

// 预警级别指示器
.alert-level-indicator {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin-right: 16px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  position: relative;
}

.alert-level-indicator.level-0 {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.alert-level-indicator.level-1 {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
}

.alert-level-indicator.level-2 {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
}

.alert-level-indicator.level-3 {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
  animation: glow 2s ease-in-out infinite;
}

// 预警内容区域
.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.behavior-type {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  transition: color 0.3s;
}

.alert-header :deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  padding: 2px 10px;
}

.alert-info {
  font-size: 13px;
  color: #606266;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  line-height: 1.6;
}

.alert-info > span {
  display: inline-flex;
  align-items: center;
}

.alert-info > span:not(:first-child)::before {
  content: '•';
  margin-right: 8px;
  color: #c0c4cc;
}

.student-link {
  color: #409eff;
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
}

.student-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.alert-time {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.alert-time::before {
  content: '🕐';
  font-size: 12px;
}

// 预警操作按钮
.alert-actions {
  display: flex;
  gap: 8px;
  opacity: 0.6;
  transition: opacity 0.3s;
}

.alert-actions :deep(.el-button) {
  transition: all 0.3s;
}

.alert-actions :deep(.el-button:hover) {
  transform: scale(1.1);
}

// 分页
.pagination {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
}

// 图表卡片
.chart-card {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: hidden;
}

.chart-card :deep(.el-card__header) {
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #f0f2f5;
  padding: 14px 20px;
}

.chart-card.trend-card {
  height: auto;
}

// 预警详情
.alert-detail .suggestions-section {
  margin-top: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.alert-detail .suggestions-section h4 {
  margin-bottom: 12px;
  color: #303133;
  font-size: 15px;
}

.alert-detail .suggestions-section ul {
  padding-left: 20px;
  margin: 0;
}

.alert-detail .suggestions-section li {
  padding: 6px 0;
  color: #606266;
  line-height: 1.6;
}

.alert-detail .related-data {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.alert-detail .related-data h4 {
  margin-bottom: 12px;
  color: #303133;
  font-size: 15px;
}

.alert-detail .related-data .el-button {
  margin-right: 12px;
  margin-bottom: 8px;
}

// 规则配置
.rule-config {
  max-height: 500px;
  overflow-y: auto;
}

// 动画
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.3);
  }
}

@keyframes glow {
  0%, 100% {
    box-shadow: 0 2px 6px rgba(245, 108, 108, 0.4);
  }
  50% {
    box-shadow: 0 2px 12px rgba(245, 108, 108, 0.8);
  }
}

// 响应式适配
@media (max-width: 1200px) {
  .alert-page__charts :deep(.el-col) {
    margin-bottom: 20px;
  }
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    gap: 10px;
  }

  .alert-item {
    padding: 12px 14px;
  }

  .alert-info {
    flex-direction: column;
    gap: 6px;
  }
}
</style>
