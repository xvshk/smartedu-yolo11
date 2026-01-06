<template>
  <BaseChart
    :option="chartOption"
    :height="height"
    :width="width"
    :loading="loading"
    :error="error"
    @retry="$emit('retry')"
    @click="$emit('click', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'

const props = defineProps({
  // 数据格式: [[x, y, value], ...] 或 [{ x: 0, y: 0, value: 10 }, ...]
  data: {
    type: Array,
    default: () => []
  },
  // X轴标签
  xAxisData: {
    type: Array,
    default: () => []
  },
  // Y轴标签
  yAxisData: {
    type: Array,
    default: () => []
  },
  // 样式
  height: {
    type: String,
    default: '300px'
  },
  width: {
    type: String,
    default: '100%'
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
  // 配置
  title: {
    type: String,
    default: ''
  },
  showLabel: {
    type: Boolean,
    default: false
  },
  showVisualMap: {
    type: Boolean,
    default: true
  },
  // 颜色范围 (从低到高)
  colorRange: {
    type: Array,
    default: () => ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
  },
  // 数值范围
  min: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: null
  }
})

defineEmits(['retry', 'click'])

// 处理数据格式
const processedData = computed(() => {
  if (!props.data || props.data.length === 0) return []
  
  return props.data.map(item => {
    if (Array.isArray(item)) {
      return item
    }
    return [item.x, item.y, item.value]
  })
})

// 计算最大值
const maxValue = computed(() => {
  if (props.max !== null) return props.max
  if (processedData.value.length === 0) return 10
  return Math.max(...processedData.value.map(d => d[2] || 0))
})

const chartOption = computed(() => {
  if (!props.data || props.data.length === 0) {
    return {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#909399',
          fontSize: 14
        }
      }
    }
  }

  return {
    title: props.title ? {
      text: props.title,
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 500 }
    } : undefined,
    tooltip: {
      position: 'top',
      formatter: (params) => {
        const xLabel = props.xAxisData[params.data[0]] || params.data[0]
        const yLabel = props.yAxisData[params.data[1]] || params.data[1]
        return `${yLabel} ${xLabel}: ${params.data[2]}`
      }
    },
    grid: {
      left: '15%',
      right: props.showVisualMap ? '15%' : '5%',
      top: props.title ? '15%' : '10%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.xAxisData,
      splitArea: {
        show: true
      },
      axisLabel: {
        rotate: props.xAxisData.length > 10 ? 45 : 0
      }
    },
    yAxis: {
      type: 'category',
      data: props.yAxisData,
      splitArea: {
        show: true
      }
    },
    visualMap: props.showVisualMap ? {
      min: props.min,
      max: maxValue.value,
      calculable: true,
      orient: 'vertical',
      right: '2%',
      top: 'center',
      inRange: {
        color: props.colorRange
      }
    } : undefined,
    series: [{
      type: 'heatmap',
      data: processedData.value,
      label: {
        show: props.showLabel
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
})
</script>
