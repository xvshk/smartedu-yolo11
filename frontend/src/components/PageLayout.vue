<template>
  <div class="page-layout" :class="layoutClasses">
    <!-- 页面头部 -->
    <div v-if="showHeader" class="page-layout__header">
      <!-- 标题和面包屑区域 -->
      <div class="page-layout__title-section">
        <div v-if="pageBreadcrumb && pageBreadcrumb.length > 0" class="page-layout__breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item 
              v-for="(item, index) in pageBreadcrumb" 
              :key="index"
              :to="item.path"
              :class="{ 'is-active': item.active }"
            >
              {{ item.label }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="page-layout__title-row">
          <h1 class="page-layout__title">
            <el-icon v-if="pageIcon" class="page-layout__title-icon">
              <component :is="pageIcon" />
            </el-icon>
            {{ pageTitle }}
            <el-tag v-if="titleTag" :type="titleTag.type" size="small" class="page-layout__title-tag">
              {{ titleTag.text }}
            </el-tag>
          </h1>
          
          <div v-if="subtitle" class="page-layout__subtitle">
            {{ subtitle }}
          </div>
        </div>
      </div>

      <!-- 操作按钮区域 -->
      <div v-if="actions && actions.length > 0" class="page-layout__actions">
        <el-button
          v-for="(action, index) in actions"
          :key="index"
          :type="action.type || 'default'"
          :size="action.size || 'default'"
          :disabled="action.disabled"
          :loading="action.loading"
          :icon="action.icon"
          @click="handleActionClick(action, index)"
          class="page-layout__action-btn"
        >
          {{ action.label }}
        </el-button>
      </div>
    </div>

    <!-- 筛选器区域 -->
    <div v-if="filters && filters.length > 0" class="page-layout__filters">
      <div class="page-layout__filters-content">
        <template v-for="(filter, index) in filters" :key="index">
          <!-- 日期范围选择器 -->
          <el-date-picker
            v-if="filter.type === 'daterange'"
            v-model="filter.value"
            :type="filter.dateType || 'daterange'"
            :placeholder="filter.placeholder"
            :start-placeholder="filter.startPlaceholder"
            :end-placeholder="filter.endPlaceholder"
            :size="filter.size || 'default'"
            :clearable="filter.clearable !== false"
            @change="handleFilterChange(filter, index)"
            class="page-layout__filter-item"
          />
          
          <!-- 选择器 -->
          <el-select
            v-else-if="filter.type === 'select'"
            v-model="filter.value"
            :placeholder="filter.placeholder"
            :size="filter.size || 'default'"
            :clearable="filter.clearable !== false"
            :multiple="filter.multiple"
            @change="handleFilterChange(filter, index)"
            class="page-layout__filter-item"
          >
            <el-option
              v-for="option in filter.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              :disabled="option.disabled"
            />
          </el-select>
          
          <!-- 输入框 -->
          <el-input
            v-else-if="filter.type === 'input'"
            v-model="filter.value"
            :placeholder="filter.placeholder"
            :size="filter.size || 'default'"
            :clearable="filter.clearable !== false"
            @change="handleFilterChange(filter, index)"
            @keyup.enter="handleFilterSearch"
            class="page-layout__filter-item"
          >
            <template v-if="filter.prepend" #prepend>{{ filter.prepend }}</template>
            <template v-if="filter.append" #append>{{ filter.append }}</template>
          </el-input>
          
          <!-- 自定义筛选器 -->
          <component
            v-else-if="filter.component"
            :is="filter.component"
            v-model="filter.value"
            v-bind="filter.props"
            @change="handleFilterChange(filter, index)"
            class="page-layout__filter-item"
          />
        </template>
        
        <!-- 筛选操作按钮 -->
        <div class="page-layout__filter-actions">
          <el-button 
            type="primary" 
            :loading="searchLoading"
            @click="handleFilterSearch"
          >
            搜索
          </el-button>
          <el-button @click="handleFilterReset">重置</el-button>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="page-layout__content" :class="contentClasses">
      <!-- 加载状态 -->
      <div v-if="loading" class="page-layout__loading">
        <el-skeleton :rows="skeletonRows" animated />
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="page-layout__error">
        <el-result icon="error" :title="errorTitle" :sub-title="error">
          <template #extra>
            <el-button type="primary" @click="handleRetry">重试</el-button>
          </template>
        </el-result>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="empty" class="page-layout__empty">
        <el-empty :description="emptyDescription" :image-size="emptyImageSize">
          <template v-if="emptyActions" #default>
            <el-button
              v-for="(action, index) in emptyActions"
              :key="index"
              :type="action.type || 'primary'"
              @click="handleEmptyActionClick(action, index)"
            >
              {{ action.label }}
            </el-button>
          </template>
        </el-empty>
      </div>
      
      <!-- 正常内容 -->
      <div v-else class="page-layout__main">
        <slot></slot>
      </div>
    </div>

    <!-- 分页区域 -->
    <div v-if="pagination && !loading && !error && !empty" class="page-layout__pagination">
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="pagination.pageSizes || [10, 20, 50, 100]"
        :layout="paginationLayout"
        :background="true"
        @size-change="handlePageSizeChange"
        @current-change="handleCurrentPageChange"
      />
    </div>

    <!-- 浮动操作按钮 -->
    <div v-if="fab" class="page-layout__fab">
      <el-button
        :type="fab.type || 'primary'"
        :size="fab.size || 'large'"
        :icon="fab.icon"
        circle
        @click="handleFabClick"
      >
        {{ fab.label }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useResponsive } from '@/utils/responsive'
import { useNavigationStore } from '@/stores/navigation'

const router = useRouter()
const route = useRoute()
const navigationStore = useNavigationStore()

// 在组件挂载时初始化导航
onMounted(() => {
  navigationStore.initNavigation(router, route)
})

const props = defineProps({
  // 基础属性
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  titleIcon: {
    type: String,
    default: ''
  },
  titleTag: {
    type: Object,
    default: null
  },
  
  // 面包屑导航 - 如果不提供则使用导航store的自动面包屑
  breadcrumb: {
    type: Array,
    default: null
  },
  
  // 操作按钮
  actions: {
    type: Array,
    default: () => []
  },
  
  // 筛选器
  filters: {
    type: Array,
    default: () => []
  },
  
  // 分页
  pagination: {
    type: Object,
    default: null
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
  empty: {
    type: Boolean,
    default: false
  },
  
  // 样式配置
  showHeader: {
    type: Boolean,
    default: true
  },
  contentPadding: {
    type: Boolean,
    default: true
  },
  fullHeight: {
    type: Boolean,
    default: false
  },
  
  // 错误状态配置
  errorTitle: {
    type: String,
    default: '加载失败'
  },
  
  // 空状态配置
  emptyDescription: {
    type: String,
    default: '暂无数据'
  },
  emptyImageSize: {
    type: Number,
    default: 100
  },
  emptyActions: {
    type: Array,
    default: () => []
  },
  
  // 加载状态配置
  skeletonRows: {
    type: Number,
    default: 5
  },
  
  // 浮动操作按钮
  fab: {
    type: Object,
    default: null
  },
  
  // 搜索加载状态
  searchLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'action-click',
  'filter-change', 
  'filter-search', 
  'filter-reset',
  'page-size-change',
  'current-page-change',
  'retry',
  'empty-action-click',
  'fab-click'
])

const { isMobile } = useResponsive()

// 使用导航store的数据或props提供的数据
const pageTitle = computed(() => {
  return props.title || navigationStore.pageTitle
})

const pageBreadcrumb = computed(() => {
  return props.breadcrumb || navigationStore.breadcrumbs
})

const pageIcon = computed(() => {
  return props.titleIcon || navigationStore.currentPageConfig.icon
})

// 布局样式类
const layoutClasses = computed(() => ({
  'page-layout--full-height': props.fullHeight,
  'page-layout--mobile': isMobile()
}))

// 内容区域样式类
const contentClasses = computed(() => ({
  'page-layout__content--no-padding': !props.contentPadding
}))

// 分页布局
const paginationLayout = computed(() => {
  return isMobile() 
    ? 'prev, pager, next'
    : 'total, sizes, prev, pager, next, jumper'
})

// 处理操作按钮点击
const handleActionClick = (action, index) => {
  if (action.onClick) {
    action.onClick()
  } else {
    emit('action-click', { action, index })
  }
}

// 处理筛选器变化
const handleFilterChange = (filter, index) => {
  emit('filter-change', { filter, index })
}

// 处理筛选搜索
const handleFilterSearch = () => {
  emit('filter-search', props.filters)
}

// 处理筛选重置
const handleFilterReset = () => {
  props.filters.forEach(filter => {
    filter.value = filter.multiple ? [] : ''
  })
  emit('filter-reset')
}

// 处理分页大小变化
const handlePageSizeChange = (pageSize) => {
  emit('page-size-change', pageSize)
}

// 处理当前页变化
const handleCurrentPageChange = (currentPage) => {
  emit('current-page-change', currentPage)
}

// 处理重试
const handleRetry = () => {
  emit('retry')
}

// 处理空状态操作
const handleEmptyActionClick = (action, index) => {
  if (action.onClick) {
    action.onClick()
  } else {
    emit('empty-action-click', { action, index })
  }
}

// 处理浮动按钮点击
const handleFabClick = () => {
  if (props.fab.onClick) {
    props.fab.onClick()
  } else {
    emit('fab-click')
  }
}
</script>

<style lang="scss" scoped>
.page-layout {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  
  &--full-height {
    height: 100vh;
  }
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-lg);
    gap: var(--spacing-base);
    
    @media (max-width: 767px) {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }
  }
  
  &__title-section {
    flex: 1;
    min-width: 0;
  }
  
  &__breadcrumb {
    margin-bottom: var(--spacing-sm);
    
    :deep(.el-breadcrumb__item) {
      .el-breadcrumb__inner {
        color: var(--color-text-secondary);
        
        &:hover {
          color: var(--color-primary);
        }
      }
      
      &.is-active .el-breadcrumb__inner {
        color: var(--color-text-primary);
        font-weight: var(--font-weight-medium);
      }
    }
  }
  
  &__title-row {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  &__title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin: 0;
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
    line-height: var(--line-height-tight);
  }
  
  &__title-icon {
    font-size: var(--font-size-xl);
    color: var(--color-primary);
  }
  
  &__title-tag {
    margin-left: var(--spacing-xs);
  }
  
  &__subtitle {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-base);
  }
  
  &__actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    
    @media (max-width: 767px) {
      width: 100%;
      
      .page-layout__action-btn {
        flex: 1;
        min-width: 0;
      }
    }
  }
  
  &__filters {
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-base);
    background: var(--color-background-elevated);
    border-radius: var(--border-radius-lg);
    border: 1px solid var(--color-border-light);
  }
  
  &__filters-content {
    display: flex;
    gap: var(--spacing-base);
    align-items: flex-end;
    flex-wrap: wrap;
  }
  
  &__filter-item {
    min-width: 200px;
    
    @media (max-width: 767px) {
      min-width: 150px;
      flex: 1;
    }
  }
  
  &__filter-actions {
    display: flex;
    gap: var(--spacing-sm);
    
    @media (max-width: 767px) {
      width: 100%;
      
      .el-button {
        flex: 1;
      }
    }
  }
  
  &__content {
    flex: 1;
    padding: var(--spacing-base);
    background: var(--color-background-primary);
    border-radius: var(--border-radius-lg);
    
    &--no-padding {
      padding: 0;
    }
  }
  
  &__loading,
  &__error,
  &__empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 300px;
  }
  
  &__main {
    min-height: 0;
  }
  
  &__pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: var(--spacing-lg);
    
    @media (max-width: 767px) {
      justify-content: center;
    }
  }
  
  &__fab {
    position: fixed;
    bottom: var(--spacing-xl);
    right: var(--spacing-xl);
    z-index: var(--z-index-fixed);
    
    @media (max-width: 767px) {
      bottom: var(--spacing-lg);
      right: var(--spacing-lg);
    }
  }
  
  // 移动端适配
  &--mobile {
    .page-layout__title {
      font-size: var(--font-size-xl);
    }
    
    .page-layout__filters {
      padding: var(--spacing-sm);
    }
    
    .page-layout__content {
      padding: var(--spacing-sm);
    }
  }
}
</style>