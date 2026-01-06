<template>
  <div class="error-handler" :class="errorClasses">
    <!-- 网络错误 -->
    <template v-if="type === 'network'">
      <div class="error-handler__icon">
        <el-icon :size="iconSize"><WifiOff /></el-icon>
      </div>
      <h3 class="error-handler__title">网络连接失败</h3>
      <p class="error-handler__message">{{ message || '请检查您的网络连接后重试' }}</p>
      <div class="error-handler__actions">
        <el-button type="primary" @click="handleRetry" :loading="retrying">
          重新连接
        </el-button>
      </div>
    </template>

    <!-- 服务器错误 -->
    <template v-else-if="type === 'server'">
      <div class="error-handler__icon error-handler__icon--danger">
        <el-icon :size="iconSize"><Warning /></el-icon>
      </div>
      <h3 class="error-handler__title">服务器错误</h3>
      <p class="error-handler__message">{{ message || '服务器暂时无法响应，请稍后再试' }}</p>
      <div class="error-handler__details" v-if="errorCode">
        <span>错误代码: {{ errorCode }}</span>
      </div>
      <div class="error-handler__actions">
        <el-button type="primary" @click="handleRetry" :loading="retrying">
          重试
        </el-button>
        <el-button @click="handleReport">报告问题</el-button>
      </div>
    </template>

    <!-- 权限错误 -->
    <template v-else-if="type === 'permission'">
      <div class="error-handler__icon error-handler__icon--warning">
        <el-icon :size="iconSize"><Lock /></el-icon>
      </div>
      <h3 class="error-handler__title">访问受限</h3>
      <p class="error-handler__message">{{ message || '您没有权限访问此内容' }}</p>
      <div class="error-handler__actions">
        <el-button type="primary" @click="handleGoBack">返回上一页</el-button>
        <el-button @click="handleGoHome">返回首页</el-button>
      </div>
    </template>

    <!-- 404 错误 -->
    <template v-else-if="type === 'notfound'">
      <div class="error-handler__icon error-handler__icon--info">
        <el-icon :size="iconSize"><Search /></el-icon>
      </div>
      <h3 class="error-handler__title">页面不存在</h3>
      <p class="error-handler__message">{{ message || '您访问的页面不存在或已被移除' }}</p>
      <div class="error-handler__actions">
        <el-button type="primary" @click="handleGoHome">返回首页</el-button>
      </div>
    </template>

    <!-- 数据为空 -->
    <template v-else-if="type === 'empty'">
      <div class="error-handler__icon error-handler__icon--muted">
        <el-icon :size="iconSize"><FolderOpened /></el-icon>
      </div>
      <h3 class="error-handler__title">{{ title || '暂无数据' }}</h3>
      <p class="error-handler__message">{{ message || '当前没有可显示的内容' }}</p>
      <div class="error-handler__actions" v-if="showActions">
        <el-button type="primary" @click="handleCreate" v-if="createText">
          {{ createText }}
        </el-button>
        <el-button @click="handleRefresh">刷新</el-button>
      </div>
    </template>

    <!-- 超时错误 -->
    <template v-else-if="type === 'timeout'">
      <div class="error-handler__icon error-handler__icon--warning">
        <el-icon :size="iconSize"><Timer /></el-icon>
      </div>
      <h3 class="error-handler__title">请求超时</h3>
      <p class="error-handler__message">{{ message || '服务器响应时间过长，请稍后重试' }}</p>
      <div class="error-handler__actions">
        <el-button type="primary" @click="handleRetry" :loading="retrying">
          重试
        </el-button>
      </div>
    </template>

    <!-- 通用错误 -->
    <template v-else>
      <div class="error-handler__icon error-handler__icon--danger">
        <el-icon :size="iconSize"><CircleClose /></el-icon>
      </div>
      <h3 class="error-handler__title">{{ title || '出错了' }}</h3>
      <p class="error-handler__message">{{ message || '发生了一个错误，请稍后重试' }}</p>
      <div class="error-handler__details" v-if="errorDetails">
        <el-collapse>
          <el-collapse-item title="错误详情">
            <pre>{{ errorDetails }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
      <div class="error-handler__actions">
        <el-button type="primary" @click="handleRetry" :loading="retrying">
          重试
        </el-button>
        <el-button @click="handleGoBack">返回</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Warning, Lock, Search, FolderOpened, Timer, CircleClose 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// WifiOff 图标不存在，用自定义
const WifiOff = {
  template: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 18c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm6-6c0 .6-.2 1.1-.6 1.5l-1.4-1.4c.1-.1.1-.1 0-.1-1.1-1.1-2.6-1.7-4-1.7-.3 0-.6 0-.9.1L9.7 9c.7-.2 1.5-.3 2.3-.3 2.1 0 4.1.8 5.6 2.3.3.3.4.6.4 1zM2.1 4.9l2.8 2.8C3.1 8.9 1.8 10.5 1 12.3l1.8.9c.7-1.5 1.8-2.8 3.2-3.8l1.5 1.5c-1.2.8-2.2 1.9-2.9 3.2l1.8.9c.6-1.1 1.4-2 2.4-2.7l1.5 1.5c-.9.5-1.6 1.2-2.2 2l1.8.9c.5-.7 1.1-1.2 1.9-1.6l5.1 5.1 1.4-1.4L3.5 3.5 2.1 4.9z"/></svg>`
}

const props = defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (val) => ['default', 'network', 'server', 'permission', 'notfound', 'empty', 'timeout'].includes(val)
  },
  title: String,
  message: String,
  errorCode: String,
  errorDetails: String,
  size: {
    type: String,
    default: 'default',
    validator: (val) => ['small', 'default', 'large'].includes(val)
  },
  showActions: {
    type: Boolean,
    default: true
  },
  createText: String
})

const emit = defineEmits(['retry', 'create', 'report'])

const router = useRouter()
const retrying = ref(false)

const iconSize = computed(() => {
  const sizes = { small: 48, default: 64, large: 80 }
  return sizes[props.size]
})

const errorClasses = computed(() => ({
  [`error-handler--${props.size}`]: true
}))

const handleRetry = async () => {
  retrying.value = true
  emit('retry')
  // 模拟重试延迟
  setTimeout(() => {
    retrying.value = false
  }, 1500)
}

const handleGoBack = () => {
  router.back()
}

const handleGoHome = () => {
  router.push('/')
}

const handleRefresh = () => {
  window.location.reload()
}

const handleCreate = () => {
  emit('create')
}

const handleReport = () => {
  emit('report')
  ElMessage.success('问题已报告，我们会尽快处理')
}
</script>

<style lang="scss" scoped>
.error-handler {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  text-align: center;
  min-height: 300px;
  
  &--small {
    padding: var(--spacing-lg);
    min-height: 200px;
  }
  
  &--large {
    padding: var(--spacing-3xl);
    min-height: 400px;
  }
  
  &__icon {
    margin-bottom: var(--spacing-lg);
    color: var(--color-text-placeholder);
    
    &--danger {
      color: var(--color-danger);
    }
    
    &--warning {
      color: var(--color-warning);
    }
    
    &--info {
      color: var(--color-info);
    }
    
    &--muted {
      color: var(--color-text-disabled);
    }
  }
  
  &__title {
    margin: 0 0 var(--spacing-sm) 0;
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
  }
  
  &__message {
    margin: 0 0 var(--spacing-lg) 0;
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
    max-width: 400px;
  }
  
  &__details {
    margin-bottom: var(--spacing-lg);
    font-size: var(--font-size-sm);
    color: var(--color-text-placeholder);
    
    pre {
      text-align: left;
      background: var(--color-background-secondary);
      padding: var(--spacing-sm);
      border-radius: var(--border-radius-base);
      overflow-x: auto;
      max-width: 400px;
    }
  }
  
  &__actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
