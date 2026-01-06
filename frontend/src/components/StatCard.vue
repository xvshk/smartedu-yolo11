<template>
  <el-card 
    class="stat-card" 
    :class="[
      `stat-card--${color}`,
      { 
        'stat-card--clickable': clickable,
        'stat-card--loading': loading,
        'stat-card--error': error
      }
    ]"
    shadow="hover"
    @click="handleClick"
  >
    <!-- 加载状态 -->
    <div v-if="loading" class="stat-card__loading">
      <el-skeleton animated>
        <template #template>
          <div class="stat-card__content">
            <div class="stat-card__icon">
              <el-skeleton-item variant="circle" style="width: 60px; height: 60px;" />
            </div>
            <div class="stat-card__info">
              <el-skeleton-item variant="text" style="width: 80px; height: 28px;" />
              <el-skeleton-item variant="text" style="width: 60px; height: 14px; margin-top: 8px;" />
            </div>
          </div>
        </template>
      </el-skeleton>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="stat-card__error">
      <div class="stat-card__content">
        <div class="stat-card__icon stat-card__icon--error">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-card__info">
          <div class="stat-card__value">--</div>
          <div class="stat-card__label">{{ title }}</div>
          <div class="stat-card__error-text">{{ error }}</div>
        </div>
      </div>
      <el-button 
        v-if="onRetry" 
        size="small" 
        type="primary" 
        text 
        @click.stop="onRetry"
        class="stat-card__retry"
      >
        重试
      </el-button>
    </div>

    <!-- 正常状态 -->
    <div v-else class="stat-card__content">
      <div class="stat-card__icon" :class="`stat-card__icon--${color}`">
        <el-icon v-if="icon">
          <component :is="icon" />
        </el-icon>
      </div>
      
      <div class="stat-card__info">
        <div class="stat-card__value">
          {{ formattedValue }}
          <span v-if="unit" class="stat-card__unit">{{ unit }}</span>
        </div>
        <div class="stat-card__label">{{ title }}</div>
        
        <!-- 趋势指示器 -->
        <div v-if="trend" class="stat-card__trend" :class="`stat-card__trend--${trend.direction}`">
          <el-icon class="stat-card__trend-icon">
            <Top v-if="trend.direction === 'up'" />
            <Bottom v-if="trend.direction === 'down'" />
            <Minus v-if="trend.direction === 'stable'" />
          </el-icon>
          <span class="stat-card__trend-value">{{ formatTrendValue(trend.value) }}</span>
          <span v-if="trend.period" class="stat-card__trend-period">{{ trend.period }}</span>
        </div>
      </div>

      <!-- 点击指示器 -->
      <div v-if="clickable" class="stat-card__click-indicator">
        <el-icon><ArrowRight /></el-icon>
      </div>
    </div>

    <!-- 额外信息插槽 -->
    <div v-if="$slots.extra" class="stat-card__extra">
      <slot name="extra"></slot>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Warning, Top, Bottom, Minus, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  // 基础属性
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  unit: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  },
  
  // 样式属性
  color: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'warning', 'danger', 'info'].includes(value)
  },
  
  // 趋势属性
  trend: {
    type: Object,
    default: null,
    validator: (value) => {
      if (!value) return true
      return value.direction && ['up', 'down', 'stable'].includes(value.direction)
    }
  },
  
  // 交互属性
  clickable: {
    type: Boolean,
    default: false
  },
  
  // 状态属性
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  
  // 格式化选项
  formatOptions: {
    type: Object,
    default: () => ({
      locale: 'zh-CN',
      notation: 'standard',
      maximumFractionDigits: 1
    })
  }
})

const emit = defineEmits(['click', 'retry'])

// 格式化数值
const formattedValue = computed(() => {
  if (typeof props.value === 'string') return props.value
  
  const num = Number(props.value)
  if (isNaN(num)) return props.value
  
  // 大数值格式化
  if (num >= 1000000) {
    return (num / 1000000).toLocaleString(props.formatOptions.locale, {
      ...props.formatOptions,
      maximumFractionDigits: 1
    }) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toLocaleString(props.formatOptions.locale, {
      ...props.formatOptions,
      maximumFractionDigits: 1
    }) + 'K'
  }
  
  return num.toLocaleString(props.formatOptions.locale, props.formatOptions)
})

// 格式化趋势值
const formatTrendValue = (value) => {
  const num = Number(value)
  if (isNaN(num)) return value
  
  const formatted = Math.abs(num).toLocaleString('zh-CN', {
    maximumFractionDigits: 1
  })
  
  return `${formatted}%`
}

// 处理点击事件
const handleClick = () => {
  if (props.clickable && !props.loading && !props.error) {
    emit('click')
  }
}

// 处理重试事件
const onRetry = () => {
  emit('retry')
}
</script>

<style lang="scss" scoped>
.stat-card {
  border: none;
  border-radius: var(--border-radius-card);
  transition: var(--transition-base);
  position: relative;
  overflow: hidden;

  &--clickable {
    cursor: pointer;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-card-hover);
    }
    
    &:active {
      transform: translateY(0);
    }
  }

  &--loading {
    pointer-events: none;
  }

  &--error {
    border-left: 4px solid var(--color-danger);
  }

  :deep(.el-card__body) {
    padding: var(--spacing-lg);
  }

  &__content {
    display: flex;
    align-items: center;
    gap: var(--spacing-base);
    position: relative;
  }

  &__loading {
    .stat-card__content {
      gap: var(--spacing-base);
    }
  }

  &__error {
    .stat-card__content {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-sm);
    }
  }

  &__icon {
    width: 60px;
    height: 60px;
    border-radius: var(--border-radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: white;
    flex-shrink: 0;
    
    &--primary {
      background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
    }
    
    &--success {
      background: linear-gradient(135deg, var(--color-success) 0%, var(--color-success-dark) 100%);
    }
    
    &--warning {
      background: linear-gradient(135deg, var(--color-warning) 0%, var(--color-warning-dark) 100%);
    }
    
    &--danger {
      background: linear-gradient(135deg, var(--color-danger) 0%, var(--color-danger-dark) 100%);
    }
    
    &--info {
      background: linear-gradient(135deg, var(--color-info) 0%, var(--color-info-dark) 100%);
    }

    &--error {
      background: linear-gradient(135deg, var(--color-danger) 0%, var(--color-danger-dark) 100%);
    }
  }

  &__info {
    flex: 1;
    min-width: 0;
  }

  &__value {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    line-height: var(--line-height-tight);
    display: flex;
    align-items: baseline;
    gap: var(--spacing-xs);
  }

  &__unit {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-normal);
    color: var(--color-text-secondary);
  }

  &__label {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-top: var(--spacing-xs);
    line-height: var(--line-height-base);
  }

  &__trend {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    margin-top: var(--spacing-xs);
    font-size: var(--font-size-xs);
    
    &--up {
      color: var(--color-success);
    }
    
    &--down {
      color: var(--color-danger);
    }
    
    &--stable {
      color: var(--color-text-secondary);
    }
  }

  &__trend-icon {
    font-size: var(--font-size-sm);
  }

  &__trend-value {
    font-weight: var(--font-weight-medium);
  }

  &__trend-period {
    color: var(--color-text-disabled);
  }

  &__click-indicator {
    position: absolute;
    top: var(--spacing-sm);
    right: var(--spacing-sm);
    color: var(--color-text-disabled);
    font-size: var(--font-size-sm);
    opacity: 0;
    transition: var(--transition-fast);
  }

  &--clickable:hover &__click-indicator {
    opacity: 1;
  }

  &__error-text {
    font-size: var(--font-size-xs);
    color: var(--color-danger);
    margin-top: var(--spacing-xs);
  }

  &__retry {
    margin-top: var(--spacing-sm);
  }

  &__extra {
    margin-top: var(--spacing-base);
    padding-top: var(--spacing-base);
    border-top: 1px solid var(--color-border-light);
  }
}

// 响应式适配
@media (max-width: 767px) {
  .stat-card {
    &__content {
      gap: var(--spacing-sm);
    }

    &__icon {
      width: 48px;
      height: 48px;
      font-size: 24px;
    }

    &__value {
      font-size: var(--font-size-2xl);
    }

    :deep(.el-card__body) {
      padding: var(--spacing-base);
    }
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .stat-card {
    &--clickable {
      min-height: var(--touch-target-min);
      
      &:hover {
        transform: none;
      }
      
      &:active {
        transform: scale(0.98);
        transition: transform 0.1s ease;
      }
    }
  }
}
</style>