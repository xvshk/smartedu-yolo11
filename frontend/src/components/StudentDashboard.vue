<template>
  <div class="student-dashboard">
    <!-- 个人学习概览 -->
    <StatCardGroup 
      :cards="studentStatCards" 
      :columns="4"
      :gutter="20"
      @card-click="handleStatClick"
      class="student-dashboard__stats"
    />

    <!-- 学习成就和激励 -->
    <el-row :gutter="20" class="student-dashboard__achievements">
      <el-col :span="16">
        <el-card class="achievement-card">
          <template #header>
            <div class="card-header">
              <span>我的成就</span>
              <el-button size="small" type="primary" text @click="viewAllAchievements">
                查看全部
              </el-button>
            </div>
          </template>
          
          <div class="achievement-grid">
            <div 
              v-for="achievement in recentAchievements" 
              :key="achievement.id"
              class="achievement-item"
              :class="{ unlocked: achievement.unlocked }"
            >
              <div class="achievement-icon">
                <el-icon :size="32">
                  <component :is="achievement.icon" />
                </el-icon>
              </div>
              <div class="achievement-info">
                <div class="achievement-title">{{ achievement.title }}</div>
                <div class="achievement-desc">{{ achievement.description }}</div>
                <div v-if="achievement.progress" class="achievement-progress">
                  <el-progress 
                    :percentage="achievement.progress.percentage" 
                    :stroke-width="6"
                    :show-text="false"
                  />
                  <span class="progress-text">
                    {{ achievement.progress.current }}/{{ achievement.progress.total }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="ranking-card">
          <template #header>
            <span>班级排名</span>
          </template>
          
          <div class="ranking-info">
            <div class="my-ranking">
              <div class="ranking-number">{{ studentRanking.myRank || '--' }}</div>
              <div class="ranking-label">我的排名</div>
            </div>
            
            <div class="ranking-details">
              <div class="detail-item">
                <span class="label">专注度排名:</span>
                <span class="value">#{{ studentRanking.attentionRank || '--' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">参与度排名:</span>
                <span class="value">#{{ studentRanking.participationRank || '--' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">班级总人数:</span>
                <span class="value">{{ studentRanking.totalStudents || '--' }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学习趋势和建议 -->
    <el-row :gutter="20" class="student-dashboard__trends">
      <el-col :span="12">
        <el-card class="trend-card">
          <template #header>
            <div class="card-header">
              <span>专注度趋势</span>
              <el-radio-group v-model="trendPeriod" size="small" @change="loadTrendData">
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="suggestions-card">
          <template #header>
            <span>个性化建议</span>
          </template>
          
          <div class="suggestions-list">
            <div 
              v-for="suggestion in personalizedSuggestions" 
              :key="suggestion.id"
              class="suggestion-item"
              :class="`suggestion-${suggestion.type}`"
            >
              <div class="suggestion-icon">
                <el-icon>
                  <component :is="suggestion.icon" />
                </el-icon>
              </div>
              <div class="suggestion-content">
                <div class="suggestion-title">{{ suggestion.title }}</div>
                <div class="suggestion-desc">{{ suggestion.description }}</div>
                <div v-if="suggestion.action" class="suggestion-action">
                  <el-button 
                    size="small" 
                    :type="suggestion.actionType || 'primary'"
                    @click="handleSuggestionAction(suggestion)"
                  >
                    {{ suggestion.actionText }}
                  </el-button>
                </div>
              </div>
            </div>
            
            <el-empty v-if="personalizedSuggestions.length === 0" 
              description="暂无个性化建议" 
              :image-size="80" 
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学习资源推荐 -->
    <el-card class="resources-card">
      <template #header>
        <div class="card-header">
          <span>推荐学习资源</span>
          <el-button size="small" @click="refreshRecommendations">
            <el-icon><Refresh /></el-icon>
            刷新推荐
          </el-button>
        </div>
      </template>
      
      <div class="resources-grid">
        <div 
          v-for="resource in recommendedResources" 
          :key="resource.id"
          class="resource-item"
          @click="openResource(resource)"
        >
          <div class="resource-cover">
            <img v-if="resource.cover" :src="resource.cover" :alt="resource.title" />
            <div v-else class="resource-placeholder">
              <el-icon :size="40">
                <component :is="resource.icon || 'Document'" />
              </el-icon>
            </div>
          </div>
          <div class="resource-info">
            <div class="resource-title">{{ resource.title }}</div>
            <div class="resource-desc">{{ resource.description }}</div>
            <div class="resource-meta">
              <el-tag :type="getResourceTypeTag(resource.type)" size="small">
                {{ resource.typeName }}
              </el-tag>
              <span class="resource-duration">{{ resource.duration }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 在线辅导入口 -->
    <el-card class="tutoring-card">
      <template #header>
        <span>在线辅导</span>
      </template>
      
      <div class="tutoring-content">
        <div class="tutoring-info">
          <h4>需要帮助？</h4>
          <p>我们的老师随时为您提供在线辅导服务，帮助您解决学习中遇到的问题。</p>
          
          <div class="tutoring-stats">
            <div class="stat-item">
              <span class="stat-number">{{ tutoringStats.availableTeachers || 0 }}</span>
              <span class="stat-label">在线老师</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ tutoringStats.averageResponse || '--' }}</span>
              <span class="stat-label">平均响应时间</span>
            </div>
          </div>
        </div>
        
        <div class="tutoring-actions">
          <el-button type="primary" size="large" @click="requestTutoring">
            <el-icon><ChatDotRound /></el-icon>
            申请辅导
          </el-button>
          <el-button @click="viewTutoringHistory">
            查看历史记录
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import StatCardGroup from './StatCardGroup.vue'
import api from '@/api'

// 响应式数据
const loading = ref(false)
const studentStats = ref({
  totalSessions: 0,
  averageAttention: 0,
  participationRate: 0,
  improvementRate: 0
})

const studentRanking = ref({
  myRank: null,
  attentionRank: null,
  participationRank: null,
  totalStudents: null
})

const recentAchievements = ref([
  {
    id: 1,
    title: '专注达人',
    description: '连续7天专注度超过80%',
    icon: 'Target',
    unlocked: true,
    unlockedAt: '2024-01-01'
  },
  {
    id: 2,
    title: '积极参与',
    description: '本周举手发言10次',
    icon: 'Star',
    unlocked: false,
    progress: {
      current: 7,
      total: 10,
      percentage: 70
    }
  },
  {
    id: 3,
    title: '学习之星',
    description: '月度学习时长达到100小时',
    icon: 'Trophy',
    unlocked: false,
    progress: {
      current: 85,
      total: 100,
      percentage: 85
    }
  }
])

const personalizedSuggestions = ref([
  {
    id: 1,
    type: 'attention',
    title: '提升专注度',
    description: '建议在上午时段安排重要学习任务，这是您专注度最高的时间段',
    icon: 'Target',
    action: 'schedule',
    actionText: '制定计划',
    actionType: 'primary'
  },
  {
    id: 2,
    type: 'participation',
    title: '增加课堂参与',
    description: '您的举手发言次数较少，建议多参与课堂讨论',
    icon: 'ChatDotRound',
    action: 'tips',
    actionText: '查看技巧',
    actionType: 'success'
  }
])

const recommendedResources = ref([
  {
    id: 1,
    title: '数学基础强化',
    description: '针对您的薄弱环节定制的数学练习',
    type: 'exercise',
    typeName: '练习题',
    duration: '30分钟',
    icon: 'Edit',
    url: '/resources/math-basic'
  },
  {
    id: 2,
    title: '专注力训练视频',
    description: '科学的专注力提升方法',
    type: 'video',
    typeName: '视频',
    duration: '15分钟',
    icon: 'VideoPlay',
    url: '/resources/focus-training'
  },
  {
    id: 3,
    title: '学习方法指南',
    description: '高效学习方法和技巧分享',
    type: 'article',
    typeName: '文章',
    duration: '10分钟',
    icon: 'Reading',
    url: '/resources/study-methods'
  }
])

const tutoringStats = ref({
  availableTeachers: 3,
  averageResponse: '5分钟'
})

const trendPeriod = ref('week')
const trendChartRef = ref(null)
let trendChart = null

// 计算属性
const studentStatCards = computed(() => [
  {
    key: 'sessions',
    title: '学习会话',
    value: studentStats.value.totalSessions,
    icon: 'VideoCamera',
    color: 'primary',
    clickable: true
  },
  {
    key: 'attention',
    title: '平均专注度',
    value: studentStats.value.averageAttention,
    unit: '%',
    icon: 'Target',
    color: 'success',
    clickable: true,
    trend: {
      direction: 'up',
      value: 3.2,
      period: '较上周'
    }
  },
  {
    key: 'participation',
    title: '参与度',
    value: studentStats.value.participationRate,
    unit: '%',
    icon: 'Star',
    color: 'warning',
    clickable: true
  },
  {
    key: 'improvement',
    title: '进步率',
    value: studentStats.value.improvementRate,
    unit: '%',
    icon: 'TrendCharts',
    color: 'info',
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
    case 'sessions':
      // 查看学习记录
      break
    case 'attention':
      // 查看专注度详情
      break
    case 'participation':
      // 查看参与度详情
      break
    case 'improvement':
      // 查看进步详情
      break
  }
}

const viewAllAchievements = () => {
  ElMessage.info('成就系统开发中')
}

const handleSuggestionAction = (suggestion) => {
  switch (suggestion.action) {
    case 'schedule':
      ElMessage.info('学习计划功能开发中')
      break
    case 'tips':
      ElMessage.info('学习技巧功能开发中')
      break
    default:
      ElMessage.info('功能开发中')
  }
}

const refreshRecommendations = () => {
  ElMessage.success('推荐已刷新')
  loadRecommendations()
}

const openResource = (resource) => {
  ElMessage.info(`打开资源: ${resource.title}`)
  // 这里可以实现资源打开逻辑
}

const getResourceTypeTag = (type) => {
  const typeMap = {
    exercise: 'primary',
    video: 'success',
    article: 'info'
  }
  return typeMap[type] || 'default'
}

const requestTutoring = () => {
  ElMessage.info('在线辅导功能开发中')
}

const viewTutoringHistory = () => {
  ElMessage.info('辅导历史功能开发中')
}

// 数据加载方法
const loadStudentStats = async () => {
  try {
    // 这里调用实际的API
    const mockData = {
      totalSessions: 45,
      averageAttention: 78.5,
      participationRate: 65.2,
      improvementRate: 12.3
    }
    studentStats.value = mockData
  } catch (error) {
    console.error('Load student stats error:', error)
  }
}

const loadRanking = async () => {
  try {
    // 这里调用实际的API
    const mockData = {
      myRank: 8,
      attentionRank: 5,
      participationRank: 12,
      totalStudents: 35
    }
    studentRanking.value = mockData
  } catch (error) {
    console.error('Load ranking error:', error)
  }
}

const loadTrendData = async () => {
  try {
    // 模拟趋势数据
    const mockData = [
      { date: '2024-01-01', attention: 75 },
      { date: '2024-01-02', attention: 78 },
      { date: '2024-01-03', attention: 82 },
      { date: '2024-01-04', attention: 79 },
      { date: '2024-01-05', attention: 85 },
      { date: '2024-01-06', attention: 88 },
      { date: '2024-01-07', attention: 86 }
    ]
    
    nextTick(() => renderTrendChart(mockData))
  } catch (error) {
    console.error('Load trend data error:', error)
  }
}

const loadRecommendations = async () => {
  try {
    // 这里可以调用推荐算法API
    ElMessage.success('推荐内容已更新')
  } catch (error) {
    console.error('Load recommendations error:', error)
  }
}

// 图表渲染
const renderTrendChart = (data) => {
  if (!trendChartRef.value) return
  if (trendChart) trendChart.dispose()
  
  trendChart = echarts.init(trendChartRef.value)
  
  const dates = data.map(d => d.date.split('-').slice(1).join('/'))
  const values = data.map(d => d.attention)
  
  trendChart.setOption({
    tooltip: { 
      trigger: 'axis',
      formatter: '{b}<br/>专注度: {c}%'
    },
    grid: { 
      left: '3%', 
      right: '4%', 
      bottom: '3%', 
      containLabel: true 
    },
    xAxis: { 
      type: 'category', 
      data: dates, 
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
      data: values,
      smooth: true,
      areaStyle: { 
        opacity: 0.3, 
        color: '#67C23A' 
      },
      lineStyle: { 
        color: '#67C23A' 
      },
      itemStyle: { 
        color: '#67C23A' 
      }
    }]
  })
}

// 生命周期
onMounted(() => {
  loadStudentStats()
  loadRanking()
  loadTrendData()
})

onUnmounted(() => {
  trendChart?.dispose()
})
</script>

<style lang="scss" scoped>
.student-dashboard {
  &__stats {
    margin-bottom: var(--spacing-section-gap);
  }

  &__achievements {
    margin-bottom: var(--spacing-section-gap);
  }

  &__trends {
    margin-bottom: var(--spacing-section-gap);
  }

  .achievement-card {
    .achievement-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: var(--spacing-base);
    }

    .achievement-item {
      display: flex;
      align-items: center;
      padding: var(--spacing-base);
      border-radius: var(--border-radius-lg);
      background: var(--color-background-secondary);
      transition: var(--transition-base);

      &.unlocked {
        background: linear-gradient(135deg, #67C23A20, #67C23A10);
        border: 1px solid #67C23A40;
      }

      &:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-card);
      }

      .achievement-icon {
        margin-right: var(--spacing-base);
        color: var(--color-success);
      }

      .achievement-info {
        flex: 1;

        .achievement-title {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
          margin-bottom: var(--spacing-xs);
        }

        .achievement-desc {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-sm);
        }

        .achievement-progress {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);

          .progress-text {
            font-size: var(--font-size-xs);
            color: var(--color-text-secondary);
            white-space: nowrap;
          }
        }
      }
    }
  }

  .ranking-card {
    .ranking-info {
      text-align: center;

      .my-ranking {
        margin-bottom: var(--spacing-lg);

        .ranking-number {
          font-size: var(--font-size-4xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-primary);
          line-height: 1;
        }

        .ranking-label {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-top: var(--spacing-xs);
        }
      }

      .ranking-details {
        .detail-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-sm) 0;
          border-bottom: 1px solid var(--color-border-light);

          &:last-child {
            border-bottom: none;
          }

          .label {
            font-size: var(--font-size-sm);
            color: var(--color-text-secondary);
          }

          .value {
            font-weight: var(--font-weight-medium);
            color: var(--color-text-primary);
          }
        }
      }
    }
  }

  .trend-card {
    .chart-container {
      height: 300px;
    }
  }

  .suggestions-card {
    .suggestions-list {
      max-height: 300px;
      overflow-y: auto;
    }

    .suggestion-item {
      display: flex;
      align-items: flex-start;
      padding: var(--spacing-base);
      border-radius: var(--border-radius-lg);
      margin-bottom: var(--spacing-sm);
      background: var(--color-background-secondary);

      &.suggestion-attention {
        border-left: 4px solid var(--color-primary);
      }

      &.suggestion-participation {
        border-left: 4px solid var(--color-success);
      }

      .suggestion-icon {
        margin-right: var(--spacing-base);
        color: var(--color-primary);
      }

      .suggestion-content {
        flex: 1;

        .suggestion-title {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
          margin-bottom: var(--spacing-xs);
        }

        .suggestion-desc {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-sm);
        }

        .suggestion-action {
          margin-top: var(--spacing-sm);
        }
      }
    }
  }

  .resources-card {
    margin-bottom: var(--spacing-section-gap);

    .resources-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--spacing-base);
    }

    .resource-item {
      display: flex;
      padding: var(--spacing-base);
      border-radius: var(--border-radius-lg);
      background: var(--color-background-secondary);
      cursor: pointer;
      transition: var(--transition-base);

      &:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-card);
      }

      .resource-cover {
        width: 60px;
        height: 60px;
        margin-right: var(--spacing-base);
        border-radius: var(--border-radius-base);
        overflow: hidden;
        background: var(--color-background-primary);
        display: flex;
        align-items: center;
        justify-content: center;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .resource-placeholder {
          color: var(--color-text-secondary);
        }
      }

      .resource-info {
        flex: 1;

        .resource-title {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
          margin-bottom: var(--spacing-xs);
        }

        .resource-desc {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-sm);
        }

        .resource-meta {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);

          .resource-duration {
            font-size: var(--font-size-xs);
            color: var(--color-text-disabled);
          }
        }
      }
    }
  }

  .tutoring-card {
    .tutoring-content {
      display: flex;
      align-items: center;
      gap: var(--spacing-xl);

      @media (max-width: 767px) {
        flex-direction: column;
        text-align: center;
      }

      .tutoring-info {
        flex: 1;

        h4 {
          margin: 0 0 var(--spacing-sm) 0;
          color: var(--color-text-primary);
        }

        p {
          margin: 0 0 var(--spacing-base) 0;
          color: var(--color-text-secondary);
        }

        .tutoring-stats {
          display: flex;
          gap: var(--spacing-xl);

          .stat-item {
            text-align: center;

            .stat-number {
              display: block;
              font-size: var(--font-size-2xl);
              font-weight: var(--font-weight-bold);
              color: var(--color-primary);
            }

            .stat-label {
              font-size: var(--font-size-sm);
              color: var(--color-text-secondary);
            }
          }
        }
      }

      .tutoring-actions {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

// 响应式适配
@media (max-width: 767px) {
  .student-dashboard {
    .achievement-grid {
      grid-template-columns: 1fr !important;
    }

    .resources-grid {
      grid-template-columns: 1fr !important;
    }
  }
}
</style>