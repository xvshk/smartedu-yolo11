<template>
  <div class="data-relation" :class="relationClasses">
    <!-- 关联标题 -->
    <div v-if="showTitle" class="data-relation__header">
      <h3 class="data-relation__title">
        <el-icon class="data-relation__title-icon">
          <component :is="titleIcon" />
        </el-icon>
        {{ title }}
        <el-tag v-if="relations.length > 0" size="small" type="info">
          {{ relations.length }}
        </el-tag>
      </h3>
      
      <div v-if="showActions" class="data-relation__actions">
        <el-button 
          v-if="allowRefresh"
          size="small" 
          :loading="loading"
          @click="handleRefresh"
        >
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button 
          v-if="allowViewAll"
          size="small" 
          type="primary" 
          text
          @click="handleViewAll"
        >
          查看全部
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="data-relation__loading">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="data-relation__error">
      <el-alert
        :title="error"
        type="error"
        :closable="false"
        show-icon
      >
        <template #default>
          <el-button size="small" type="primary" @click="handleRetry">
            重试
          </el-button>
        </template>
      </el-alert>
    </div>

    <!-- 空状态 -->
    <div v-else-if="relations.length === 0" class="data-relation__empty">
      <el-empty 
        :description="emptyDescription" 
        :image-size="60"
      />
    </div>

    <!-- 关联列表 -->
    <div v-else class="data-relation__list">
      <div
        v-for="(relation, index) in displayRelations"
        :key="relation.id || index"
        class="data-relation__item"
        :class="getItemClasses(relation)"
        @click="handleItemClick(relation, index)"
      >
        <!-- 关联类型图标 -->
        <div class="data-relation__item-icon" :class="`data-relation__item-icon--${relation.type}`">
          <el-icon>
            <component :is="getTypeIcon(relation.type)" />
          </el-icon>
        </div>

        <!-- 关联内容 -->
        <div class="data-relation__item-content">
          <div class="data-relation__item-header">
            <span class="data-relation__item-title">{{ relation.title }}</span>
            <div class="data-relation__item-meta">
              <el-tag 
                v-if="relation.status" 
                :type="getStatusType(relation.status)" 
                size="small"
              >
                {{ getStatusText(relation.status) }}
              </el-tag>
              <span class="data-relation__item-time">
                {{ formatTime(relation.timestamp) }}
              </span>
            </div>
          </div>
          
          <div v-if="relation.summary" class="data-relation__item-summary">
            {{ relation.summary }}
          </div>
          
          <!-- 额外信息 -->
          <div v-if="relation.extra" class="data-relation__item-extra">
            <component 
              :is="relation.extra.component" 
              v-bind="relation.extra.props"
            />
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="data-relation__item-actions">
          <el-button 
            size="small" 
            type="primary" 
            text
            @click.stop="handleItemClick(relation, index)"
          >
            查看
          </el-button>
          <el-dropdown 
            v-if="relation.actions && relation.actions.length > 0"
            @command="(command) => handleItemAction(relation, command)"
          >
            <el-button size="small" text>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="action in relation.actions"
                  :key="action.key"
                  :command="action.key"
                  :disabled="action.disabled"
                >
                  <el-icon v-if="action.icon">
                    <component :is="action.icon" />
                  </el-icon>
                  {{ action.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 展开/收起按钮 -->
      <div v-if="relations.length > maxDisplay" class="data-relation__expand">
        <el-button 
          type="primary" 
          text 
          @click="toggleExpanded"
        >
          {{ expanded ? '收起' : `展开更多 (${relations.length - maxDisplay})` }}
          <el-icon>
            <component :is="expanded ? 'ArrowUp' : 'ArrowDown'" />
          </el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { 
  Refresh, MoreFilled, ArrowUp, ArrowDown,
  VideoCamera, Bell, User, Document, DataAnalysis
} from '@element-plus/icons-vue'

const props = defineProps({
  // 基础属性
  title: {
    type: String,
    default: '相关数据'
  },
  titleIcon: {
    type: String,
    default: 'DataAnalysis'
  },
  
  // 数据源信息
  sourceType: {
    type: String,
    required: true,
    validator: (value) => ['student', 'class', 'detection', 'alert', 'report'].includes(value)
  },
  sourceId: {
    type: String,
    required: true
  },
  
  // 关联数据
  relations: {
    type: Array,
    default: () => [],
    validator: (relations) => {
      return relations.every(relation => 
        relation.type && relation.id && relation.title
      )
    }
  },
  
  // 显示配置
  maxDisplay: {
    type: Number,
    default: 5
  },
  showTitle: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: true
  },
  allowRefresh: {
    type: Boolean,
    default: true
  },
  allowViewAll: {
    type: Boolean,
    default: true
  },
  
  // 状态
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  
  // 样式
  compact: {
    type: Boolean,
    default: false
  },
  
  // 空状态
  emptyDescription: {
    type: String,
    default: '暂无相关数据'
  }
})

const emit = defineEmits([
  'item-click',
  'item-action', 
  'refresh',
  'view-all',
  'retry'
])

const expanded = ref(false)

// 样式类
const relationClasses = computed(() => ({
  'data-relation--compact': props.compact,
  'data-relation--loading': props.loading
}))

// 显示的关联数据
const displayRelations = computed(() => {
  if (expanded.value || props.relations.length <= props.maxDisplay) {
    return props.relations
  }
  return props.relations.slice(0, props.maxDisplay)
})

// 获取关联类型图标
const getTypeIcon = (type) => {
  const iconMap = {
    detection: 'VideoCamera',
    alert: 'Bell',
    portrait: 'User',
    report: 'Document',
    student: 'User'
  }
  return iconMap[type] || 'Document'
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    normal: 'success',
    warning: 'warning',
    danger: 'danger',
    info: 'info'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    normal: '正常',
    warning: '警告',
    danger: '严重',
    info: '信息'
  }
  return textMap[status] || status
}

// 获取项目样式类
const getItemClasses = (relation) => ({
  'data-relation__item--clickable': true,
  [`data-relation__item--${relation.status}`]: relation.status
})

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  
  // 小于1天
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  
  // 小于7天
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}天前`
  }
  
  // 超过7天显示具体日期
  return date.toLocaleDateString('zh-CN')
}

// 切换展开状态
const toggleExpanded = () => {
  expanded.value = !expanded.value
}

// 处理项目点击
const handleItemClick = (relation, index) => {
  emit('item-click', { relation, index })
}

// 处理项目操作
const handleItemAction = (relation, actionKey) => {
  const action = relation.actions?.find(a => a.key === actionKey)
  if (action) {
    emit('item-action', { relation, action })
  }
}

// 处理刷新
const handleRefresh = () => {
  emit('refresh')
}

// 处理查看全部
const handleViewAll = () => {
  emit('view-all')
}

// 处理重试
const handleRetry = () => {
  emit('retry')
}
</script>

<style lang="scss" scoped>
.data-relation {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-base);
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--color-border-light);
  }
  
  &__title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin: 0;
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-primary);
  }
  
  &__title-icon {
    color: var(--color-primary);
  }
  
  &__actions {
    display: flex;
    gap: var(--spacing-sm);
  }
  
  &__loading,
  &__error,
  &__empty {
    padding: var(--spacing-lg);
  }
  
  &__list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  &__item {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-base);
    padding: var(--spacing-base);
    background: var(--color-background-elevated);
    border: 1px solid var(--color-border-light);
    border-radius: var(--border-radius-base);
    transition: var(--transition-base);
    
    &--clickable {
      cursor: pointer;
      
      &:hover {
        border-color: var(--color-primary);
        box-shadow: var(--shadow-sm);
      }
    }
    
    &--warning {
      border-left: 4px solid var(--color-warning);
    }
    
    &--danger {
      border-left: 4px solid var(--color-danger);
    }
  }
  
  &__item-icon {
    width: 40px;
    height: 40px;
    border-radius: var(--border-radius-base);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--font-size-lg);
    color: white;
    flex-shrink: 0;
    
    &--detection {
      background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
    }
    
    &--alert {
      background: linear-gradient(135deg, var(--color-warning) 0%, var(--color-warning-dark) 100%);
    }
    
    &--portrait,
    &--student {
      background: linear-gradient(135deg, var(--color-success) 0%, var(--color-success-dark) 100%);
    }
    
    &--report {
      background: linear-gradient(135deg, var(--color-info) 0%, var(--color-info-dark) 100%);
    }
  }
  
  &__item-content {
    flex: 1;
    min-width: 0;
  }
  
  &__item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xs);
  }
  
  &__item-title {
    font-weight: var(--font-weight-medium);
    color: var(--color-text-primary);
    line-height: var(--line-height-base);
  }
  
  &__item-meta {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex-shrink: 0;
  }
  
  &__item-time {
    font-size: var(--font-size-xs);
    color: var(--color-text-disabled);
  }
  
  &__item-summary {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-base);
    margin-bottom: var(--spacing-xs);
    
    // 限制显示行数
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  &__item-extra {
    margin-top: var(--spacing-sm);
  }
  
  &__item-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    flex-shrink: 0;
  }
  
  &__expand {
    display: flex;
    justify-content: center;
    padding: var(--spacing-sm);
    border-top: 1px solid var(--color-border-light);
    margin-top: var(--spacing-sm);
  }
  
  // 紧凑模式
  &--compact {
    .data-relation__item {
      padding: var(--spacing-sm);
    }
    
    .data-relation__item-icon {
      width: 32px;
      height: 32px;
      font-size: var(--font-size-base);
    }
    
    .data-relation__item-title {
      font-size: var(--font-size-sm);
    }
  }
}

// 响应式适配
@media (max-width: 767px) {
  .data-relation {
    &__header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }
    
    &__actions {
      justify-content: flex-end;
    }
    
    &__item {
      padding: var(--spacing-sm);
    }
    
    &__item-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-xs);
    }
    
    &__item-meta {
      justify-content: space-between;
    }
    
    &__item-actions {
      margin-top: var(--spacing-xs);
      justify-content: flex-end;
    }
  }
}
</style>