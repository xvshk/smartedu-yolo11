<template>
  <div class="admin-dashboard">
    <!-- 系统概览统计 -->
    <StatCardGroup 
      :cards="adminStatCards" 
      :columns="4"
      :gutter="20"
      @card-click="handleStatClick"
      class="admin-dashboard__stats"
    />

    <!-- 系统状态监控 -->
    <el-row :gutter="20" class="admin-dashboard__monitoring">
      <el-col :span="16">
        <el-card class="system-status-card">
          <template #header>
            <div class="card-header">
              <span>系统状态监控</span>
              <div class="header-actions">
                <el-button size="small" @click="refreshSystemStatus">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
                <el-button size="small" type="primary" @click="showSystemConfig = true">
                  <el-icon><Setting /></el-icon>
                  系统配置
                </el-button>
              </div>
            </div>
          </template>

          <div class="system-metrics">
            <!-- 服务状态 -->
            <div class="metrics-section">
              <h4>服务状态</h4>
              <div class="service-grid">
                <div 
                  v-for="service in systemServices" 
                  :key="service.name"
                  class="service-item"
                  :class="service.status"
                >
                  <div class="service-icon">
                    <el-icon :size="24">
                      <component :is="service.icon" />
                    </el-icon>
                  </div>
                  <div class="service-info">
                    <div class="service-name">{{ service.name }}</div>
                    <div class="service-status">
                      <el-tag :type="getServiceTagType(service.status)" size="small">
                        {{ getServiceStatusText(service.status) }}
                      </el-tag>
                      <span class="service-uptime">运行时间: {{ service.uptime }}</span>
                    </div>
                  </div>
                  <div class="service-actions">
                    <el-button 
                      v-if="service.status !== 'running'" 
                      size="small" 
                      type="success"
                      @click="startService(service)"
                    >
                      启动
                    </el-button>
                    <el-button 
                      v-else 
                      size="small" 
                      type="warning"
                      @click="restartService(service)"
                    >
                      重启
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 性能指标 -->
            <div class="metrics-section">
              <h4>性能指标</h4>
              <div class="performance-grid">
                <div class="performance-item">
                  <div class="performance-label">CPU使用率</div>
                  <div class="performance-value">
                    <el-progress 
                      :percentage="systemMetrics.cpuUsage" 
                      :color="getPerformanceColor(systemMetrics.cpuUsage)"
                      :stroke-width="8"
                    />
                  </div>
                </div>
                <div class="performance-item">
                  <div class="performance-label">内存使用率</div>
                  <div class="performance-value">
                    <el-progress 
                      :percentage="systemMetrics.memoryUsage" 
                      :color="getPerformanceColor(systemMetrics.memoryUsage)"
                      :stroke-width="8"
                    />
                  </div>
                </div>
                <div class="performance-item">
                  <div class="performance-label">磁盘使用率</div>
                  <div class="performance-value">
                    <el-progress 
                      :percentage="systemMetrics.diskUsage" 
                      :color="getPerformanceColor(systemMetrics.diskUsage)"
                      :stroke-width="8"
                    />
                  </div>
                </div>
                <div class="performance-item">
                  <div class="performance-label">网络延迟</div>
                  <div class="performance-value">
                    <span class="latency-value" :class="getLatencyClass(systemMetrics.networkLatency)">
                      {{ systemMetrics.networkLatency }}ms
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="user-management-card">
          <template #header>
            <div class="card-header">
              <span>用户管理</span>
              <el-button size="small" type="primary" @click="showUserDialog = true">
                <el-icon><Plus /></el-icon>
                添加用户
              </el-button>
            </div>
          </template>

          <div class="user-summary">
            <div class="summary-item">
              <div class="summary-number">{{ userStats.totalUsers }}</div>
              <div class="summary-label">总用户数</div>
            </div>
            <div class="summary-item">
              <div class="summary-number">{{ userStats.onlineUsers }}</div>
              <div class="summary-label">在线用户</div>
            </div>
            <div class="summary-item">
              <div class="summary-number">{{ userStats.newUsersToday }}</div>
              <div class="summary-label">今日新增</div>
            </div>
          </div>

          <div class="user-roles">
            <h4>用户角色分布</h4>
            <div class="role-list">
              <div 
                v-for="role in userRoles" 
                :key="role.type"
                class="role-item"
              >
                <div class="role-info">
                  <span class="role-name">{{ role.name }}</span>
                  <span class="role-count">{{ role.count }}人</span>
                </div>
                <div class="role-progress">
                  <el-progress 
                    :percentage="(role.count / userStats.totalUsers * 100)" 
                    :stroke-width="6"
                    :show-text="false"
                    :color="role.color"
                  />
                </div>
              </div>
            </div>
          </div>

          <div class="recent-activities">
            <h4>最近活动</h4>
            <div class="activity-list">
              <div 
                v-for="activity in recentActivities" 
                :key="activity.id"
                class="activity-item"
              >
                <div class="activity-icon">
                  <el-icon>
                    <component :is="activity.icon" />
                  </el-icon>
                </div>
                <div class="activity-content">
                  <div class="activity-text">{{ activity.text }}</div>
                  <div class="activity-time">{{ formatTime(activity.time) }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据统计和报表 -->
    <el-row :gutter="20" class="admin-dashboard__analytics">
      <el-col :span="12">
        <el-card class="usage-analytics-card">
          <template #header>
            <div class="card-header">
              <span>使用情况分析</span>
              <el-radio-group v-model="analyticsPeriod" size="small" @change="loadAnalyticsData">
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
                <el-radio-button label="quarter">本季度</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="usageChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="system-logs-card">
          <template #header>
            <div class="card-header">
              <span>系统日志</span>
              <div class="header-actions">
                <el-select v-model="logLevel" placeholder="日志级别" size="small" @change="loadSystemLogs">
                  <el-option label="全部" value="" />
                  <el-option label="错误" value="error" />
                  <el-option label="警告" value="warning" />
                  <el-option label="信息" value="info" />
                </el-select>
                <el-button size="small" @click="exportLogs">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
              </div>
            </div>
          </template>

          <div class="logs-container">
            <div 
              v-for="log in systemLogs" 
              :key="log.id"
              class="log-item"
              :class="`log-${log.level}`"
            >
              <div class="log-time">{{ formatTime(log.timestamp) }}</div>
              <div class="log-level">
                <el-tag :type="getLogTagType(log.level)" size="small">
                  {{ log.level.toUpperCase() }}
                </el-tag>
              </div>
              <div class="log-message">{{ log.message }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 报表生成 -->
    <el-card class="reports-card">
      <template #header>
        <div class="card-header">
          <span>报表生成</span>
          <el-button size="small" type="primary" @click="showReportDialog = true">
            <el-icon><Document /></el-icon>
            生成报表
          </el-button>
        </div>
      </template>

      <div class="reports-grid">
        <div 
          v-for="report in availableReports" 
          :key="report.type"
          class="report-item"
          @click="generateReport(report)"
        >
          <div class="report-icon">
            <el-icon :size="32">
              <component :is="report.icon" />
            </el-icon>
          </div>
          <div class="report-info">
            <div class="report-title">{{ report.title }}</div>
            <div class="report-desc">{{ report.description }}</div>
            <div class="report-meta">
              <span class="report-format">{{ report.format }}</span>
              <span class="report-size">{{ report.estimatedSize }}</span>
            </div>
          </div>
          <div class="report-actions">
            <el-button size="small" type="primary">生成</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 用户添加对话框 -->
    <el-dialog v-model="showUserDialog" title="添加用户" width="500px">
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="userForm.name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱地址" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="选择用户角色">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="请输入初始密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUserDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUser">确认添加</el-button>
      </template>
    </el-dialog>

    <!-- 系统配置对话框 -->
    <el-dialog v-model="showSystemConfig" title="系统配置" width="800px">
      <el-tabs v-model="configTab">
        <el-tab-pane label="基础配置" name="basic">
          <el-form :model="systemConfig" label-width="120px">
            <el-form-item label="系统名称">
              <el-input v-model="systemConfig.systemName" />
            </el-form-item>
            <el-form-item label="会话超时">
              <el-input-number v-model="systemConfig.sessionTimeout" :min="5" :max="120" />
              <span style="margin-left: 8px;">分钟</span>
            </el-form-item>
            <el-form-item label="最大并发用户">
              <el-input-number v-model="systemConfig.maxConcurrentUsers" :min="10" :max="1000" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="安全配置" name="security">
          <el-form :model="systemConfig" label-width="120px">
            <el-form-item label="密码策略">
              <el-checkbox-group v-model="systemConfig.passwordPolicy">
                <el-checkbox label="requireUppercase">要求大写字母</el-checkbox>
                <el-checkbox label="requireNumbers">要求数字</el-checkbox>
                <el-checkbox label="requireSpecialChars">要求特殊字符</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="最小密码长度">
              <el-input-number v-model="systemConfig.minPasswordLength" :min="6" :max="20" />
            </el-form-item>
            <el-form-item label="登录失败锁定">
              <el-switch v-model="systemConfig.enableLoginLock" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showSystemConfig = false">取消</el-button>
        <el-button type="primary" @click="saveSystemConfig">保存配置</el-button>
      </template>
    </el-dialog>

    <!-- 报表生成对话框 -->
    <el-dialog v-model="showReportDialog" title="生成报表" width="600px">
      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="报表类型">
          <el-select v-model="reportForm.type" placeholder="选择报表类型">
            <el-option 
              v-for="report in availableReports" 
              :key="report.type"
              :label="report.title" 
              :value="report.type" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="reportForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item label="输出格式">
          <el-radio-group v-model="reportForm.format">
            <el-radio label="pdf">PDF</el-radio>
            <el-radio label="excel">Excel</el-radio>
            <el-radio label="csv">CSV</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReportDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReport">生成报表</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import StatCardGroup from './StatCardGroup.vue'
import api from '@/api'

// 响应式数据
const loading = ref(false)
const analyticsPeriod = ref('week')
const logLevel = ref('')
const configTab = ref('basic')

const adminStats = ref({
  totalUsers: 0,
  totalSessions: 0,
  systemUptime: 0,
  storageUsed: 0
})

const systemServices = ref([
  {
    name: 'Web服务器',
    status: 'running',
    uptime: '15天3小时',
    icon: 'Platform'
  },
  {
    name: '数据库',
    status: 'running',
    uptime: '15天3小时',
    icon: 'Coin'
  },
  {
    name: 'AI模型服务',
    status: 'running',
    uptime: '2天5小时',
    icon: 'Monitor'
  },
  {
    name: '文件存储',
    status: 'warning',
    uptime: '15天3小时',
    icon: 'Document'
  }
])

const systemMetrics = ref({
  cpuUsage: 45,
  memoryUsage: 68,
  diskUsage: 72,
  networkLatency: 25
})

const userStats = ref({
  totalUsers: 156,
  onlineUsers: 23,
  newUsersToday: 5
})

const userRoles = ref([
  { type: 'student', name: '学生', count: 120, color: '#409EFF' },
  { type: 'teacher', name: '教师', count: 30, color: '#67C23A' },
  { type: 'admin', name: '管理员', count: 6, color: '#E6A23C' }
])

const recentActivities = ref([
  {
    id: 1,
    text: '用户 张三 登录系统',
    time: new Date(Date.now() - 5 * 60 * 1000),
    icon: 'User'
  },
  {
    id: 2,
    text: '生成了系统使用报表',
    time: new Date(Date.now() - 15 * 60 * 1000),
    icon: 'Document'
  },
  {
    id: 3,
    text: '检测到异常行为预警',
    time: new Date(Date.now() - 30 * 60 * 1000),
    icon: 'Bell'
  }
])

const systemLogs = ref([
  {
    id: 1,
    level: 'info',
    message: '用户登录成功: admin@example.com',
    timestamp: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    id: 2,
    level: 'warning',
    message: '磁盘使用率超过70%',
    timestamp: new Date(Date.now() - 10 * 60 * 1000)
  },
  {
    id: 3,
    level: 'error',
    message: 'AI模型服务连接超时',
    timestamp: new Date(Date.now() - 25 * 60 * 1000)
  }
])

const availableReports = ref([
  {
    type: 'usage',
    title: '系统使用报表',
    description: '用户活跃度、功能使用统计',
    format: 'PDF/Excel',
    estimatedSize: '2.5MB',
    icon: 'DataAnalysis'
  },
  {
    type: 'performance',
    title: '性能监控报表',
    description: '系统性能指标、响应时间分析',
    format: 'PDF/Excel',
    estimatedSize: '1.8MB',
    icon: 'Monitor'
  },
  {
    type: 'security',
    title: '安全审计报表',
    description: '登录记录、权限变更、异常行为',
    format: 'PDF/Excel',
    estimatedSize: '3.2MB',
    icon: 'Lock'
  }
])

// 对话框状态
const showUserDialog = ref(false)
const showSystemConfig = ref(false)
const showReportDialog = ref(false)

// 表单数据
const userForm = ref({
  username: '',
  name: '',
  email: '',
  role: '',
  password: ''
})

const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const systemConfig = ref({
  systemName: '智慧教育平台',
  sessionTimeout: 30,
  maxConcurrentUsers: 200,
  passwordPolicy: ['requireNumbers'],
  minPasswordLength: 8,
  enableLoginLock: true
})

const reportForm = ref({
  type: '',
  dateRange: null,
  format: 'pdf'
})

// 图表引用
const usageChartRef = ref(null)
let usageChart = null

// 计算属性
const adminStatCards = computed(() => [
  {
    key: 'users',
    title: '总用户数',
    value: adminStats.value.totalUsers,
    icon: 'User',
    color: 'primary',
    clickable: true
  },
  {
    key: 'sessions',
    title: '活跃会话',
    value: adminStats.value.totalSessions,
    icon: 'VideoCamera',
    color: 'success',
    clickable: true
  },
  {
    key: 'uptime',
    title: '系统运行时间',
    value: adminStats.value.systemUptime,
    unit: '天',
    icon: 'Monitor',
    color: 'info',
    clickable: true
  },
  {
    key: 'storage',
    title: '存储使用',
    value: adminStats.value.storageUsed,
    unit: 'GB',
    icon: 'Coin',
    color: 'warning',
    clickable: true,
    trend: {
      direction: 'up',
      value: 8.5,
      period: '较上月'
    }
  }
])

// 方法
const handleStatClick = ({ card }) => {
  switch (card.key) {
    case 'users':
      // 跳转到用户管理
      break
    case 'sessions':
      // 查看活跃会话
      break
    case 'uptime':
      // 查看系统状态
      break
    case 'storage':
      // 查看存储详情
      break
  }
}

const refreshSystemStatus = () => {
  loadSystemMetrics()
  ElMessage.success('系统状态已刷新')
}

const getServiceTagType = (status) => {
  const types = {
    running: 'success',
    warning: 'warning',
    error: 'danger',
    stopped: 'info'
  }
  return types[status] || 'info'
}

const getServiceStatusText = (status) => {
  const texts = {
    running: '运行中',
    warning: '警告',
    error: '错误',
    stopped: '已停止'
  }
  return texts[status] || '未知'
}

const getPerformanceColor = (percentage) => {
  if (percentage >= 80) return '#F56C6C'
  if (percentage >= 60) return '#E6A23C'
  return '#67C23A'
}

const getLatencyClass = (latency) => {
  if (latency > 100) return 'latency-high'
  if (latency > 50) return 'latency-medium'
  return 'latency-low'
}

const getLogTagType = (level) => {
  const types = {
    error: 'danger',
    warning: 'warning',
    info: 'info',
    debug: 'success'
  }
  return types[level] || 'info'
}

const startService = (service) => {
  ElMessage.success(`正在启动 ${service.name}`)
  service.status = 'running'
}

const restartService = (service) => {
  ElMessageBox.confirm(`确定要重启 ${service.name} 吗？`, '确认重启', {
    type: 'warning'
  }).then(() => {
    ElMessage.success(`正在重启 ${service.name}`)
  }).catch(() => {})
}

const submitUser = async () => {
  try {
    // 提交用户创建请求
    ElMessage.success('用户创建成功')
    showUserDialog.value = false
    
    // 重置表单
    userForm.value = {
      username: '',
      name: '',
      email: '',
      role: '',
      password: ''
    }
  } catch (error) {
    ElMessage.error('用户创建失败')
  }
}

const saveSystemConfig = async () => {
  try {
    // 保存系统配置
    ElMessage.success('配置保存成功')
    showSystemConfig.value = false
  } catch (error) {
    ElMessage.error('配置保存失败')
  }
}

const generateReport = (report) => {
  reportForm.value.type = report.type
  showReportDialog.value = true
}

const submitReport = async () => {
  try {
    // 生成报表
    ElMessage.success('报表生成中，完成后将通过邮件发送')
    showReportDialog.value = false
    
    // 重置表单
    reportForm.value = {
      type: '',
      dateRange: null,
      format: 'pdf'
    }
  } catch (error) {
    ElMessage.error('报表生成失败')
  }
}

const exportLogs = () => {
  ElMessage.success('日志导出中')
}

const loadAnalyticsData = () => {
  nextTick(() => renderUsageChart())
}

const loadSystemLogs = () => {
  // 根据日志级别筛选日志
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

// 图表渲染
const renderUsageChart = () => {
  if (!usageChartRef.value) return
  if (usageChart) usageChart.dispose()
  
  usageChart = echarts.init(usageChartRef.value)
  
  // 模拟使用情况数据
  const data = Array.from({ length: 7 }, (_, i) => ({
    date: `1/${i + 1}`,
    users: Math.floor(Math.random() * 50) + 20,
    sessions: Math.floor(Math.random() * 100) + 50
  }))
  
  usageChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['活跃用户', '会话数量'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: data.map(d => d.date) 
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '活跃用户',
        type: 'line',
        data: data.map(d => d.users),
        smooth: true,
        lineStyle: { color: '#409EFF' },
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '会话数量',
        type: 'line',
        data: data.map(d => d.sessions),
        smooth: true,
        lineStyle: { color: '#67C23A' },
        itemStyle: { color: '#67C23A' }
      }
    ]
  })
}

// 数据加载
const loadAdminStats = async () => {
  try {
    adminStats.value = {
      totalUsers: 156,
      totalSessions: 23,
      systemUptime: 15,
      storageUsed: 128.5
    }
  } catch (error) {
    console.error('Load admin stats error:', error)
  }
}

const loadSystemMetrics = async () => {
  try {
    // 模拟系统指标更新
    systemMetrics.value = {
      cpuUsage: Math.floor(Math.random() * 30) + 30,
      memoryUsage: Math.floor(Math.random() * 40) + 40,
      diskUsage: Math.floor(Math.random() * 20) + 60,
      networkLatency: Math.floor(Math.random() * 50) + 10
    }
  } catch (error) {
    console.error('Load system metrics error:', error)
  }
}

// 定时器引用
let metricsInterval = null

// 生命周期
onMounted(() => {
  loadAdminStats()
  loadSystemMetrics()
  loadAnalyticsData()
  
  // 定时刷新系统指标
  metricsInterval = setInterval(loadSystemMetrics, 30000)
})

onUnmounted(() => {
  if (metricsInterval) {
    clearInterval(metricsInterval)
  }
  usageChart?.dispose()
})
</script>

<style lang="scss" scoped>
.admin-dashboard {
  &__stats {
    margin-bottom: var(--spacing-section-gap);
  }

  &__monitoring {
    margin-bottom: var(--spacing-section-gap);
  }

  &__analytics {
    margin-bottom: var(--spacing-section-gap);
  }

  .system-status-card {
    .system-metrics {
      .metrics-section {
        margin-bottom: var(--spacing-xl);

        &:last-child {
          margin-bottom: 0;
        }

        h4 {
          margin: 0 0 var(--spacing-base) 0;
          color: var(--color-text-primary);
          font-size: var(--font-size-lg);
        }
      }

      .service-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: var(--spacing-base);
      }

      .service-item {
        display: flex;
        align-items: center;
        padding: var(--spacing-base);
        border-radius: var(--border-radius-lg);
        background: var(--color-background-secondary);
        transition: var(--transition-base);

        &.running {
          border-left: 4px solid var(--color-success);
        }

        &.warning {
          border-left: 4px solid var(--color-warning);
        }

        &.error {
          border-left: 4px solid var(--color-danger);
        }

        .service-icon {
          margin-right: var(--spacing-base);
          color: var(--color-primary);
        }

        .service-info {
          flex: 1;

          .service-name {
            font-weight: var(--font-weight-medium);
            color: var(--color-text-primary);
            margin-bottom: var(--spacing-xs);
          }

          .service-status {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);

            .service-uptime {
              font-size: var(--font-size-sm);
              color: var(--color-text-secondary);
            }
          }
        }

        .service-actions {
          margin-left: var(--spacing-base);
        }
      }

      .performance-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--spacing-lg);
      }

      .performance-item {
        .performance-label {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-sm);
        }

        .performance-value {
          .latency-value {
            font-size: var(--font-size-lg);
            font-weight: var(--font-weight-medium);

            &.latency-low {
              color: var(--color-success);
            }

            &.latency-medium {
              color: var(--color-warning);
            }

            &.latency-high {
              color: var(--color-danger);
            }
          }
        }
      }
    }
  }

  .user-management-card {
    .user-summary {
      display: flex;
      justify-content: space-around;
      margin-bottom: var(--spacing-lg);
      padding: var(--spacing-base);
      background: var(--color-background-secondary);
      border-radius: var(--border-radius-lg);

      .summary-item {
        text-align: center;

        .summary-number {
          font-size: var(--font-size-2xl);
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

    .user-roles {
      margin-bottom: var(--spacing-lg);

      h4 {
        margin: 0 0 var(--spacing-base) 0;
        color: var(--color-text-primary);
      }

      .role-list {
        .role-item {
          margin-bottom: var(--spacing-base);

          .role-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-xs);

            .role-name {
              font-weight: var(--font-weight-medium);
              color: var(--color-text-primary);
            }

            .role-count {
              font-size: var(--font-size-sm);
              color: var(--color-text-secondary);
            }
          }
        }
      }
    }

    .recent-activities {
      h4 {
        margin: 0 0 var(--spacing-base) 0;
        color: var(--color-text-primary);
      }

      .activity-list {
        max-height: 200px;
        overflow-y: auto;
      }

      .activity-item {
        display: flex;
        align-items: flex-start;
        padding: var(--spacing-sm);
        border-radius: var(--border-radius-base);
        margin-bottom: var(--spacing-sm);
        background: var(--color-background-primary);

        .activity-icon {
          margin-right: var(--spacing-sm);
          color: var(--color-primary);
        }

        .activity-content {
          flex: 1;

          .activity-text {
            font-size: var(--font-size-sm);
            color: var(--color-text-primary);
            margin-bottom: var(--spacing-xs);
          }

          .activity-time {
            font-size: var(--font-size-xs);
            color: var(--color-text-disabled);
          }
        }
      }
    }
  }

  .usage-analytics-card {
    .chart-container {
      height: 300px;
    }
  }

  .system-logs-card {
    .logs-container {
      max-height: 300px;
      overflow-y: auto;
    }

    .log-item {
      display: flex;
      align-items: center;
      padding: var(--spacing-sm);
      border-radius: var(--border-radius-base);
      margin-bottom: var(--spacing-sm);
      background: var(--color-background-secondary);

      &.log-error {
        border-left: 4px solid var(--color-danger);
      }

      &.log-warning {
        border-left: 4px solid var(--color-warning);
      }

      &.log-info {
        border-left: 4px solid var(--color-info);
      }

      .log-time {
        font-size: var(--font-size-xs);
        color: var(--color-text-disabled);
        margin-right: var(--spacing-sm);
        white-space: nowrap;
      }

      .log-level {
        margin-right: var(--spacing-sm);
      }

      .log-message {
        flex: 1;
        font-size: var(--font-size-sm);
        color: var(--color-text-primary);
      }
    }
  }

  .reports-card {
    .reports-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: var(--spacing-base);
    }

    .report-item {
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

      .report-icon {
        margin-right: var(--spacing-base);
        color: var(--color-primary);
      }

      .report-info {
        flex: 1;

        .report-title {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
          margin-bottom: var(--spacing-xs);
        }

        .report-desc {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-sm);
        }

        .report-meta {
          display: flex;
          gap: var(--spacing-base);

          .report-format,
          .report-size {
            font-size: var(--font-size-xs);
            color: var(--color-text-disabled);
          }
        }
      }

      .report-actions {
        margin-left: var(--spacing-base);
      }
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
  .admin-dashboard {
    .service-grid {
      grid-template-columns: 1fr !important;
    }

    .performance-grid {
      grid-template-columns: 1fr !important;
    }

    .user-summary {
      flex-direction: column !important;
      gap: var(--spacing-base) !important;
    }

    .reports-grid {
      grid-template-columns: 1fr !important;
    }
  }
}
</style>