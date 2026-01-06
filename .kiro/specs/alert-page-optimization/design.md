# Design Document: Alert Page and Dashboard Chart Optimization

## Overview

本设计文档描述预警页面和首页图表优化的技术实现方案。主要目标包括：

1. 修复预警页面和首页的图表显示问题
2. 新增多种数据可视化图表（关系图、漏斗图、热力图等）
3. 美化页面样式和交互体验
4. 优化空状态和错误处理

## Architecture

```mermaid
graph TB
    subgraph Frontend Pages
        Dashboard[Dashboard.vue<br/>首页]
        Alert[Alert.vue<br/>预警页面]
    end
    
    subgraph Chart Components
        BaseChart[BaseChart.vue<br/>基础图表]
        PieChart[PieChart.vue<br/>饼图]
        BarChart[BarChart.vue<br/>柱状图]
        LineChart[LineChart.vue<br/>折线图]
        FunnelChart[FunnelChart.vue<br/>漏斗图 - 新增]
        RelationGraph[RelationGraph.vue<br/>关系图 - 新增]
        HeatmapChart[HeatmapChart.vue<br/>热力图 - 新增]
    end
    
    subgraph Shared Components
        StatCardGroup[StatCardGroup.vue]
        PageLayout[PageLayout.vue]
        EmptyState[EmptyState.vue - 新增]
    end
    
    subgraph Backend API
        AlertAPI[/api/alert]
        PortraitAPI[/api/portrait]
    end
    
    Dashboard --> LineChart
    Dashboard --> PieChart
    Dashboard --> BarChart
    Dashboard --> RelationGraph
    Dashboard --> HeatmapChart
    Dashboard --> StatCardGroup
    
    Alert --> PieChart
    Alert --> BarChart
    Alert --> LineChart
    Alert --> FunnelChart
    Alert --> StatCardGroup
    
    Dashboard --> PortraitAPI
    Alert --> AlertAPI
    
    PieChart --> BaseChart
    BarChart --> BaseChart
    LineChart --> BaseChart
    FunnelChart --> BaseChart
    HeatmapChart --> BaseChart

```

## Components and Interfaces

### 1. FunnelChart Component (新增)

```vue
<!-- frontend/src/components/charts/FunnelChart.vue -->
<template>
  <BaseChart
    :option="chartOption"
    :height="height"
    :width="width"
    :loading="loading"
    :error="error"
    @retry="$emit('retry')"
  />
</template>

<script setup>
const props = defineProps({
  // 数据格式: [{ name: '生成', value: 100 }, { name: '查看', value: 80 }, ...]
  data: { type: Array, default: () => [] },
  height: { type: String, default: '300px' },
  width: { type: String, default: '100%' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  title: { type: String, default: '' },
  showLabel: { type: Boolean, default: true },
  showConversionRate: { type: Boolean, default: true },
  colors: { type: Array, default: () => ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C'] }
})
</script>
```

### 2. RelationGraph Component (新增)

```vue
<!-- frontend/src/components/charts/RelationGraph.vue -->
<template>
  <BaseChart
    :option="chartOption"
    :height="height"
    :width="width"
    :loading="loading"
    :error="error"
    @retry="$emit('retry')"
  />
</template>

<script setup>
const props = defineProps({
  // 节点数据: [{ id: '1', name: '学生A', category: 0 }, ...]
  nodes: { type: Array, default: () => [] },
  // 连线数据: [{ source: '1', target: '2', value: 10 }, ...]
  links: { type: Array, default: () => [] },
  // 分类: [{ name: '学生' }, { name: '行为' }, { name: '预警' }]
  categories: { type: Array, default: () => [] },
  height: { type: String, default: '400px' },
  width: { type: String, default: '100%' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  title: { type: String, default: '' },
  layout: { type: String, default: 'force' }, // force | circular
  draggable: { type: Boolean, default: true }
})
</script>
```

### 3. HeatmapChart Component (新增)

```vue
<!-- frontend/src/components/charts/HeatmapChart.vue -->
<template>
  <BaseChart
    :option="chartOption"
    :height="height"
    :width="width"
    :loading="loading"
    :error="error"
    @retry="$emit('retry')"
  />
</template>

<script setup>
const props = defineProps({
  // 数据格式: [[x, y, value], ...]
  data: { type: Array, default: () => [] },
  // X轴标签
  xAxisData: { type: Array, default: () => [] },
  // Y轴标签
  yAxisData: { type: Array, default: () => [] },
  height: { type: String, default: '300px' },
  width: { type: String, default: '100%' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  title: { type: String, default: '' },
  // 颜色范围
  colorRange: { type: Array, default: () => ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127'] }
})
</script>
```

### 4. EmptyState Component (新增)

```vue
<!-- frontend/src/components/EmptyState.vue -->
<template>
  <div class="empty-state">
    <el-empty :description="description" :image-size="imageSize">
      <template #image v-if="icon">
        <el-icon :size="60" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </template>
      <template #default v-if="showAction">
        <el-button type="primary" @click="$emit('action')">
          {{ actionText }}
        </el-button>
      </template>
    </el-empty>
  </div>
</template>

<script setup>
defineProps({
  description: { type: String, default: '暂无数据' },
  icon: { type: String, default: '' },
  iconColor: { type: String, default: '#909399' },
  imageSize: { type: Number, default: 100 },
  showAction: { type: Boolean, default: false },
  actionText: { type: String, default: '刷新' }
})
defineEmits(['action'])
</script>
```

## Data Models

### Chart Data Interfaces

```typescript
// 漏斗图数据
interface FunnelData {
  name: string      // 阶段名称
  value: number     // 数值
  rate?: number     // 转化率（可选，自动计算）
}

// 关系图节点
interface GraphNode {
  id: string
  name: string
  category: number  // 分类索引
  value?: number    // 节点大小
  symbolSize?: number
}

// 关系图连线
interface GraphLink {
  source: string    // 源节点ID
  target: string    // 目标节点ID
  value?: number    // 连线权重
}

// 热力图数据点
interface HeatmapPoint {
  x: number | string  // X坐标或标签索引
  y: number | string  // Y坐标或标签索引
  value: number       // 热度值
}

// 预警处理流程数据
interface AlertFunnelData {
  generated: number   // 生成的预警数
  viewed: number      // 已查看数
  handled: number     // 已处理数
  resolved: number    // 已解决数
}

// 关系图数据
interface RelationGraphData {
  nodes: GraphNode[]
  links: GraphLink[]
  categories: { name: string }[]
}
```


## Page Layout Design

### Dashboard Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  统计卡片组 (4列)                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │检测会话  │ │学生人数  │ │预警次数  │ │平均专注度│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────┐ ┌──────────────────────┐       │
│  │ 行为趋势分析 (折线图)      │ │ 行为分布 (饼图)      │       │
│  │ [本周] [本月]              │ │                      │       │
│  │                            │ │                      │       │
│  └────────────────────────────┘ └──────────────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────┐ ┌──────────────────────┐       │
│  │ 预警趋势 (折线图)          │ │ 行为热力图 (新增)    │       │
│  │                            │ │ 按时间段分布         │       │
│  └────────────────────────────┘ └──────────────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────┐ ┌──────────────────────┐       │
│  │ 数据关系图 (新增)          │ │ 快捷操作             │       │
│  │ 学生-行为-预警关联         │ │ [开始检测] [查看预警]│       │
│  └────────────────────────────┘ └──────────────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 预警行为排名 (表格)                                         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Alert Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  统计卡片组 (4列)                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │总预警数  │ │未读预警  │ │严重预警  │ │较上周期  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ ┌──────────────────────┐│
│  │ 预警列表                           │ │ 预警级别分布 (饼图)  ││
│  │ ┌────────────────────────────────┐ │ │                      ││
│  │ │ 筛选条件栏                     │ │ └──────────────────────┘│
│  │ └────────────────────────────────┘ │ ┌──────────────────────┐│
│  │ ┌────────────────────────────────┐ │ │ 行为类型分布 (柱状图)││
│  │ │ 预警项目列表                   │ │ │                      ││
│  │ │ ...                            │ │ └──────────────────────┘│
│  │ └────────────────────────────────┘ │ ┌──────────────────────┐│
│  │ ┌────────────────────────────────┐ │ │ 预警处理漏斗 (新增)  ││
│  │ │ 分页                           │ │ │ 生成→查看→处理→解决  ││
│  │ └────────────────────────────────┘ │ └──────────────────────┘│
│  └────────────────────────────────────┘                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────┐ ┌──────────────────────────┐│
│  │ 预警趋势 (折线图) - 新增       │ │ 时间分布 (柱状图) - 新增││
│  │ 按日期显示预警数量变化         │ │ 按小时显示预警分布      ││
│  └────────────────────────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Chart Fix Strategy

### Problem Analysis

当前图表显示为空的原因：
1. **数据格式不匹配**: API返回的数据格式与图表组件期望的格式不一致
2. **初始化时机问题**: 图表在DOM未完全渲染时初始化
3. **空数据处理缺失**: 没有对空数据进行友好提示

### Fix Approach

1. **Alert.vue 图表修复**:
   - 确保 `updateCharts()` 在数据加载完成后调用
   - 添加数据格式转换逻辑
   - 使用 `nextTick` 确保DOM渲染完成
   - 添加空数据检查和占位显示

2. **Dashboard.vue 图表修复**:
   - 检查 `pieChartData` 计算属性的数据转换
   - 确保 `trendChartData` 正确处理空数组
   - 添加图表加载状态管理

### Color Scheme

```javascript
// 预警级别颜色
const alertLevelColors = {
  0: '#67C23A',  // 正常 - 绿色
  1: '#909399',  // 轻度 - 灰色
  2: '#E6A23C',  // 中度 - 橙色
  3: '#F56C6C'   // 严重 - 红色
}

// 行为类型颜色
const behaviorColors = {
  '睡觉': '#F56C6C',
  '交谈': '#E6A23C',
  '使用电子设备': '#409EFF',
  '低头': '#909399',
  '站立': '#67C23A',
  '听讲': '#67C23A',
  '举手': '#409EFF',
  '阅读': '#67C23A',
  '书写': '#67C23A'
}

// 渐变色配置
const gradientColors = [
  { offset: 0, color: '#83bff6' },
  { offset: 1, color: '#188df0' }
]
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Alert Chart Data Formatting

*For any* valid statistics response from the API containing level_distribution and behavior_distribution, the data transformation functions SHALL produce arrays with correct format for PieChart and BarChart components (each item having 'name' and 'value' properties).

**Validates: Requirements 1.1, 1.2**

### Property 2: Dashboard Chart Data Formatting

*For any* valid API response containing trend data and behavior distribution, the computed properties SHALL transform the data into correct formats for LineChart (xAxisData array and data array) and PieChart (array of {name, value} objects).

**Validates: Requirements 2.1, 2.2**

### Property 3: Relation Graph Data Structure

*For any* valid relation graph data, all nodes SHALL have required properties (id, name, category), and all links SHALL reference existing node IDs in both source and target properties.

**Validates: Requirements 3.5, 3.6**

### Property 4: Funnel Chart Conversion Rate Calculation

*For any* funnel chart data with sequential stages, the conversion rate between stage N and stage N+1 SHALL equal (stage[N+1].value / stage[N].value * 100) when stage[N].value > 0.

**Validates: Requirements 4.4, 4.5**

### Property 5: Alert Level Color Mapping

*For any* alert level value (0, 1, 2, or 3), the color mapping function SHALL return the corresponding predefined color (green for 0, gray for 1, orange for 2, red for 3).

**Validates: Requirements 5.1**

## Error Handling

### Chart Error States

| Scenario | Handling |
|----------|----------|
| API request fails | Display error message with retry button |
| Empty data returned | Display "暂无数据" placeholder |
| Invalid data format | Log error, display fallback empty state |
| Chart initialization fails | Retry initialization after DOM ready |

### Loading States

| Component | Loading Indicator |
|-----------|-------------------|
| Charts | Skeleton loader or spinner overlay |
| Stat Cards | Pulse animation on value |
| Data Tables | Row skeleton placeholders |

## Testing Strategy

### Unit Tests

1. **Data Transformation Tests**
   - Test alert statistics data formatting
   - Test dashboard data formatting
   - Test funnel conversion rate calculation
   - Test color mapping functions

2. **Component Tests**
   - Test FunnelChart renders with valid data
   - Test RelationGraph renders with nodes and links
   - Test HeatmapChart renders with matrix data
   - Test EmptyState displays correct message

### Property-Based Tests

使用 Vitest 和 fast-check 进行属性测试：

```javascript
import { fc } from '@fast-check/vitest'

// Property 1: Alert chart data formatting
fc.assert(
  fc.property(
    fc.record({
      level_distribution: fc.dictionary(fc.integer({ min: 0, max: 3 }), fc.nat()),
      behavior_distribution: fc.dictionary(fc.string(), fc.nat())
    }),
    (stats) => {
      const pieData = formatLevelDistribution(stats.level_distribution)
      return pieData.every(item => 
        typeof item.name === 'string' && 
        typeof item.value === 'number'
      )
    }
  )
)

// Property 4: Funnel conversion rate
fc.assert(
  fc.property(
    fc.array(fc.record({ name: fc.string(), value: fc.nat() }), { minLength: 2 }),
    (stages) => {
      const withRates = calculateConversionRates(stages)
      return withRates.slice(1).every((stage, i) => {
        if (stages[i].value === 0) return true
        const expectedRate = (stage.value / stages[i].value) * 100
        return Math.abs(stage.rate - expectedRate) < 0.01
      })
    }
  )
)
```

### Integration Tests

1. **Page Load Tests**
   - Verify Dashboard loads all charts
   - Verify Alert page loads all charts
   - Verify charts update on data change

2. **Interaction Tests**
   - Test chart period switching
   - Test stat card click navigation
   - Test filter application

