<template>
  <div class="skeleton-loader" :class="skeletonClasses">
    <!-- 卡片骨架 -->
    <template v-if="type === 'card'">
      <div class="skeleton-card" v-for="i in count" :key="i">
        <div class="skeleton-card__header">
          <el-skeleton-item variant="circle" style="width: 40px; height: 40px" />
          <div class="skeleton-card__title">
            <el-skeleton-item variant="text" style="width: 60%" />
            <el-skeleton-item variant="text" style="width: 40%" />
          </div>
        </div>
        <el-skeleton-item variant="text" style="width: 100%" />
        <el-skeleton-item variant="text" style="width: 80%" />
      </div>
    </template>

    <!-- 统计卡片骨架 -->
    <template v-else-if="type === 'stat-card'">
      <el-row :gutter="20">
        <el-col :span="24 / count" v-for="i in count" :key="i">
          <div class="skeleton-stat-card">
            <div class="skeleton-stat-card__icon">
              <el-skeleton-item variant="rect" style="width: 48px; height: 48px; border-radius: 12px" />
            </div>
            <div class="skeleton-stat-card__content">
              <el-skeleton-item variant="text" style="width: 60px; height: 12px" />
              <el-skeleton-item variant="text" style="width: 80px; height: 24px; margin-top: 8px" />
            </div>
          </div>
        </el-col>
      </el-row>
    </template>

    <!-- 表格骨架 -->
    <template v-else-if="type === 'table'">
      <div class="skeleton-table">
        <div class="skeleton-table__header">
          <el-skeleton-item 
            v-for="i in columns" 
            :key="i" 
            variant="text" 
            :style="{ width: `${100 / columns}%` }"
          />
        </div>
        <div class="skeleton-table__row" v-for="i in rows" :key="i">
          <el-skeleton-item 
            v-for="j in columns" 
            :key="j" 
            variant="text" 
            :style="{ width: `${100 / columns - 2}%` }"
          />
        </div>
      </div>
    </template>

    <!-- 图表骨架 -->
    <template v-else-if="type === 'chart'">
      <div class="skeleton-chart">
        <div class="skeleton-chart__header">
          <el-skeleton-item variant="text" style="width: 120px" />
          <el-skeleton-item variant="text" style="width: 80px" />
        </div>
        <div class="skeleton-chart__body">
          <el-skeleton-item variant="rect" style="width: 100%; height: 200px; border-radius: 8px" />
        </div>
      </div>
    </template>

    <!-- 列表骨架 -->
    <template v-else-if="type === 'list'">
      <div class="skeleton-list">
        <div class="skeleton-list__item" v-for="i in rows" :key="i">
          <el-skeleton-item variant="circle" style="width: 32px; height: 32px" />
          <div class="skeleton-list__content">
            <el-skeleton-item variant="text" style="width: 40%" />
            <el-skeleton-item variant="text" style="width: 70%" />
          </div>
        </div>
      </div>
    </template>

    <!-- 画像骨架 -->
    <template v-else-if="type === 'portrait'">
      <div class="skeleton-portrait">
        <div class="skeleton-portrait__header">
          <el-skeleton-item variant="circle" style="width: 80px; height: 80px" />
          <div class="skeleton-portrait__info">
            <el-skeleton-item variant="text" style="width: 120px; height: 20px" />
            <el-skeleton-item variant="text" style="width: 200px" />
            <el-skeleton-item variant="text" style="width: 160px" />
          </div>
        </div>
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="8" v-for="i in 3" :key="i">
            <div class="skeleton-portrait__stat">
              <el-skeleton-item variant="text" style="width: 60px" />
              <el-skeleton-item variant="text" style="width: 80px; height: 24px" />
            </div>
          </el-col>
        </el-row>
      </div>
    </template>

    <!-- 默认骨架 -->
    <template v-else>
      <el-skeleton :rows="rows" animated />
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (val) => ['default', 'card', 'stat-card', 'table', 'chart', 'list', 'portrait'].includes(val)
  },
  count: {
    type: Number,
    default: 4
  },
  rows: {
    type: Number,
    default: 5
  },
  columns: {
    type: Number,
    default: 4
  },
  animated: {
    type: Boolean,
    default: true
  }
})

const skeletonClasses = computed(() => ({
  'skeleton-loader--animated': props.animated
}))
</script>

<style lang="scss" scoped>
.skeleton-loader {
  &--animated {
    :deep(.el-skeleton__item) {
      animation: skeleton-loading 1.4s ease infinite;
    }
  }
}

@keyframes skeleton-loading {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.skeleton-card {
  padding: var(--spacing-base);
  background: var(--color-background-elevated);
  border-radius: var(--border-radius-card);
  margin-bottom: var(--spacing-base);
  
  &__header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
  }
  
  &__title {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
}

.skeleton-stat-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-base);
  padding: var(--spacing-lg);
  background: var(--color-background-elevated);
  border-radius: var(--border-radius-card);
  
  &__content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
}

.skeleton-table {
  background: var(--color-background-elevated);
  border-radius: var(--border-radius-card);
  overflow: hidden;
  
  &__header {
    display: flex;
    gap: var(--spacing-sm);
    padding: var(--spacing-base);
    background: var(--color-background-secondary);
  }
  
  &__row {
    display: flex;
    gap: var(--spacing-sm);
    padding: var(--spacing-base);
    border-bottom: 1px solid var(--color-border-light);
    
    &:last-child {
      border-bottom: none;
    }
  }
}

.skeleton-chart {
  padding: var(--spacing-base);
  background: var(--color-background-elevated);
  border-radius: var(--border-radius-card);
  
  &__header {
    display: flex;
    justify-content: space-between;
    margin-bottom: var(--spacing-base);
  }
  
  &__body {
    min-height: 200px;
  }
}

.skeleton-list {
  &__item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) 0;
    border-bottom: 1px solid var(--color-border-light);
    
    &:last-child {
      border-bottom: none;
    }
  }
  
  &__content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
}

.skeleton-portrait {
  padding: var(--spacing-lg);
  background: var(--color-background-elevated);
  border-radius: var(--border-radius-card);
  
  &__header {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
  }
  
  &__info {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  &__stat {
    text-align: center;
    padding: var(--spacing-base);
    background: var(--color-background-secondary);
    border-radius: var(--border-radius-base);
    
    :deep(.el-skeleton__item) {
      margin: 0 auto;
    }
  }
}
</style>
