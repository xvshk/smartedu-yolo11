<template>
  <div class="stat-card-group" :class="groupClasses">
    <el-row :gutter="gutter" class="stat-card-group__row">
      <el-col 
        v-for="(card, index) in cards" 
        :key="card.key || index"
        :span="getColSpan(index)"
        :xs="getResponsiveSpan('xs', index)"
        :sm="getResponsiveSpan('sm', index)"
        :md="getResponsiveSpan('md', index)"
        :lg="getResponsiveSpan('lg', index)"
        :xl="getResponsiveSpan('xl', index)"
        class="stat-card-group__col"
      >
        <StatCard
          v-bind="card"
          @click="handleCardClick(card, index)"
          @retry="handleCardRetry(card, index)"
        >
          <template v-if="card.extra" #extra>
            <component :is="card.extra" v-bind="card.extraProps" />
          </template>
        </StatCard>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StatCard from './StatCard.vue'
import { useResponsive } from '@/utils/responsive'

const props = defineProps({
  // 卡片数据
  cards: {
    type: Array,
    required: true,
    validator: (cards) => {
      return cards.every(card => card.title && (card.value !== undefined))
    }
  },
  
  // 布局配置
  columns: {
    type: [Number, Object],
    default: 4,
    validator: (value) => {
      if (typeof value === 'number') return value > 0 && value <= 24
      if (typeof value === 'object') {
        return Object.values(value).every(v => v > 0 && v <= 24)
      }
      return false
    }
  },
  
  // 间距配置
  gutter: {
    type: [Number, Object],
    default: 20
  },
  
  // 响应式配置
  responsive: {
    type: Boolean,
    default: true
  },
  
  // 样式类
  className: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['card-click', 'card-retry'])

const { getCurrentBreakpoint } = useResponsive()

// 组样式类
const groupClasses = computed(() => {
  return [
    'stat-card-group',
    props.className,
    {
      'stat-card-group--responsive': props.responsive
    }
  ]
})

// 获取列跨度
const getColSpan = (index) => {
  if (!props.responsive) {
    return typeof props.columns === 'number' 
      ? Math.floor(24 / props.columns)
      : 24 / props.cards.length
  }
  
  // 响应式模式下使用默认值，具体由响应式属性控制
  return 24
}

// 获取响应式跨度
const getResponsiveSpan = (breakpoint, index) => {
  if (!props.responsive) return undefined
  
  const columns = getColumnsForBreakpoint(breakpoint)
  return Math.floor(24 / columns)
}

// 获取断点对应的列数
const getColumnsForBreakpoint = (breakpoint) => {
  if (typeof props.columns === 'number') {
    // 默认响应式规则
    const defaultColumns = {
      xs: Math.min(props.columns, 2), // 移动端最多2列
      sm: Math.min(props.columns, 2), // 小屏最多2列
      md: Math.min(props.columns, 3), // 中屏最多3列
      lg: props.columns,               // 大屏使用设定值
      xl: props.columns                // 超大屏使用设定值
    }
    return defaultColumns[breakpoint] || props.columns
  }
  
  if (typeof props.columns === 'object') {
    return props.columns[breakpoint] || props.columns.default || 4
  }
  
  return 4
}

// 处理卡片点击
const handleCardClick = (card, index) => {
  emit('card-click', { card, index })
}

// 处理卡片重试
const handleCardRetry = (card, index) => {
  emit('card-retry', { card, index })
}
</script>

<style lang="scss" scoped>
.stat-card-group {
  width: 100%;

  &__row {
    margin: 0;
  }

  &__col {
    margin-bottom: var(--spacing-card-gap);
    
    &:last-child {
      margin-bottom: 0;
    }
  }

  // 响应式间距调整
  &--responsive {
    @media (max-width: 767px) {
      .stat-card-group__col {
        margin-bottom: var(--spacing-sm);
      }
    }
  }
}

// 特殊布局样式
.stat-card-group {
  // 紧凑模式
  &--compact {
    .stat-card-group__col {
      margin-bottom: var(--spacing-sm);
    }
  }
  
  // 宽松模式
  &--loose {
    .stat-card-group__col {
      margin-bottom: var(--spacing-xl);
    }
  }
}
</style>