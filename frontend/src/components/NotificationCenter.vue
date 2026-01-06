<template>
  <div class="notification-center">
    <!-- 通知触发按钮 -->
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
      <el-button 
        :icon="Bell" 
        circle 
        @click="togglePanel"
        class="notification-trigger"
      />
    </el-badge>

    <!-- 通知面板 -->
    <el-drawer
      v-model="panelVisible"
      title="消息中心"
      direction="rtl"
      size="380px"
      :show-close="true"
    >
      <!-- 标签页切换 -->
      <el-tabs v-model="activeTab" class="notification-tabs">
        <el-tab-pane label="全部" name="all">
          <template #label>
            <span>全部</span>
            <el-badge :value="notifications.length" :hidden="notifications.length === 0" class="tab-badge" />
          </template>
        </el-tab-pane>
        <el-tab-pane label="预警" name="alert">
          <template #label>
            <span>预警</span>
            <el-badge :value="alertCount" :hidden="alertCount === 0" class="tab-badge" />
          </template>
        </el-tab-pane>
        <el-tab-pane label="系统" name="system">
          <template #label>
            <span>系统</span>
            <el-badge :value="systemCount" :hidden="systemCount === 0" class="tab-badge" />
          </template>
        </el-tab-pane>
        <el-tab-pane label="协作" name="collaboration">
          <template #label>
            <span>协作</span>
            <el-badge :value="collaborationCount" :hidden="collaborationCount === 0" class="tab-badge" />
          </template>
        </el-tab-pane>
      </el-tabs>

      <!-- 操作栏 -->
      <div class="notification-actions">
        <el-button text size="small" @click="markAllAsRead" :disabled="unreadCount === 0">
          全部已读
        </el-button>
        <el-button text size="small" @click="clearAll" :disabled="filteredNotifications.length === 0">
          清空
        </el-button>
      </div>

      <!-- 通知列表 -->
      <div class="notification-list" v-loading="loading">
        <template v-if="filteredNotifications.length > 0">
          <div
            v-for="notification in filteredNotifications"
            :key="notification.id"
            class="notification-item"
            :class="{ 'is-unread': !notification.read }"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-icon" :class="`notification-icon--${notification.type}`">
              <el-icon>
                <component :is="getNotificationIcon(notification.type)" />
              </el-icon>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-meta">
                <span class="notification-time">{{ formatTime(notification.createdAt) }}</span>
                <el-tag v-if="notification.priority === 'high'" type="danger" size="small">紧急</el-tag>
              </div>
            </div>
            <el-button
              v-if="!notification.read"
              text
              size="small"
              @click.stop="markAsRead(notification.id)"
              class="notification-mark-btn"
            >
              标记已读
            </el-button>
          </div>
        </template>
        <el-empty v-else description="暂无消息" :image-size="80" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Warning, InfoFilled, ChatDotRound, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const panelVisible = ref(false)
const activeTab = ref('all')
const loading = ref(false)

// 通知数据
const notifications = ref([])

// 模拟通知数据
const mockNotifications = [
  {
    id: 1,
    type: 'alert',
    title: '新预警通知',
    message: '学生张三在第3节课出现睡觉行为，已触发预警',
    createdAt: new Date(Date.now() - 5 * 60 * 1000),
    read: false,
    priority: 'high',
    data: { studentId: 1, alertId: 101 }
  },
  {
    id: 2,
    type: 'collaboration',
    title: '教师反馈',
    message: '李老师对学生王五的学习情况进行了反馈',
    createdAt: new Date(Date.now() - 30 * 60 * 1000),
    read: false,
    priority: 'normal',
    data: { teacherId: 2, studentId: 5 }
  },
  {
    id: 3,
    type: 'system',
    title: '系统维护通知',
    message: '系统将于今晚22:00-24:00进行维护升级',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: true,
    priority: 'normal',
    data: {}
  },
  {
    id: 4,
    type: 'alert',
    title: '行为改善提醒',
    message: '学生李四本周专注度提升15%，建议给予鼓励',
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000),
    read: true,
    priority: 'normal',
    data: { studentId: 4 }
  }
]

// 计算属性
const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)
const alertCount = computed(() => notifications.value.filter(n => n.type === 'alert').length)
const systemCount = computed(() => notifications.value.filter(n => n.type === 'system').length)
const collaborationCount = computed(() => notifications.value.filter(n => n.type === 'collaboration').length)

const filteredNotifications = computed(() => {
  if (activeTab.value === 'all') return notifications.value
  return notifications.value.filter(n => n.type === activeTab.value)
})

// 方法
const togglePanel = () => {
  panelVisible.value = !panelVisible.value
}

const getNotificationIcon = (type) => {
  const icons = {
    alert: Warning,
    system: Setting,
    collaboration: ChatDotRound,
    info: InfoFilled
  }
  return icons[type] || InfoFilled
}

const formatTime = (date) => {
  const now = new Date()
  const diff = now - new Date(date)
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return new Date(date).toLocaleDateString()
}

const markAsRead = (id) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.read = true
  }
}

const markAllAsRead = () => {
  notifications.value.forEach(n => n.read = true)
  ElMessage.success('已全部标记为已读')
}

const clearAll = () => {
  if (activeTab.value === 'all') {
    notifications.value = []
  } else {
    notifications.value = notifications.value.filter(n => n.type !== activeTab.value)
  }
  ElMessage.success('已清空')
}

const handleNotificationClick = (notification) => {
  markAsRead(notification.id)
  
  // 根据通知类型跳转
  switch (notification.type) {
    case 'alert':
      if (notification.data?.studentId) {
        router.push(`/portrait?studentId=${notification.data.studentId}`)
      } else {
        router.push('/alert')
      }
      break
    case 'collaboration':
      router.push('/portrait')
      break
    default:
      break
  }
  
  panelVisible.value = false
}

// 加载通知
const loadNotifications = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    notifications.value = [...mockNotifications]
  } finally {
    loading.value = false
  }
}

// 添加新通知
const addNotification = (notification) => {
  notifications.value.unshift({
    id: Date.now(),
    createdAt: new Date(),
    read: false,
    ...notification
  })
}

// 轮询检查新通知
let pollInterval = null
const startPolling = () => {
  pollInterval = setInterval(() => {
    // 实际项目中这里调用API检查新通知
  }, 30000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onMounted(() => {
  loadNotifications()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

// 暴露方法供外部调用
defineExpose({
  addNotification,
  togglePanel
})
</script>

<style lang="scss" scoped>
.notification-center {
  position: relative;
}

.notification-trigger {
  font-size: 18px;
}

.notification-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: var(--spacing-sm);
  }
  
  .tab-badge {
    margin-left: 4px;
  }
}

.notification-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--spacing-sm);
}

.notification-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-base);
  cursor: pointer;
  transition: var(--transition-base);
  
  &:hover {
    background: var(--color-background-hover);
  }
  
  &.is-unread {
    background: var(--color-primary-light);
    
    &:hover {
      background: var(--color-primary-lighter);
    }
  }
  
  & + & {
    margin-top: var(--spacing-xs);
  }
}

.notification-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  &--alert {
    background: var(--color-warning-light);
    color: var(--color-warning);
  }
  
  &--system {
    background: var(--color-info-light);
    color: var(--color-info);
  }
  
  &--collaboration {
    background: var(--color-success-light);
    color: var(--color-success);
  }
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.notification-message {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: 4px;
}

.notification-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
}

.notification-mark-btn {
  flex-shrink: 0;
  font-size: var(--font-size-xs);
}
</style>
