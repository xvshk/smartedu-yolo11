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
  // 数据
  data: {
    type: Array,
    default: () => []
  },
  xAxisData: {
    type: Array,
    default: () => []
  },
  // 系列配置
  series: {
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
  horizontal: {
    type: Boolean,
    default: false
  },
  showLegend: {
    type: Boolean,
    default: true
  },
  stack: {
    type: Boolean,
    default: false
  },
  barWidth: {
    type: [String, Number],
    default: 'auto'
  },
  yAxisName: {
    type: String,
    default: ''
  },
  showLabel: {
    type: Boolean,
    default: false
  },
  colors: {
    type: Array,
    default: () => ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  }
})

const emit = defineEmits(['retry', 'click'])

const chartOption = computed(() => {
  // 处理简单数据格式
  let seriesData = props.series
  if (props.data.length > 0 && props.series.length === 0) {
    seriesData = [{
      name: '数据',
      data: props.data
    }]
  }

  const categoryAxis = {
    type: 'category',
    data: props.xAxisData
  }

  const valueAxis = {
    type: 'value',
    name: props.yAxisName
  }

  return {
    title: props.title ? {
      text: props.title,
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 500 }
    } : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: props.showLegend && seriesData.length > 1 ? {
      bottom: 0,
      type: 'scroll'
    } : undefined,
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.showLegend && seriesData.length > 1 ? '15%' : '3%',
      top: props.title ? '15%' : '10%',
      containLabel: true
    },
    xAxis: props.horizontal ? valueAxis : categoryAxis,
    yAxis: props.horizontal ? categoryAxis : valueAxis,
    color: props.colors,
    series: seriesData.map((item, index) => ({
      name: item.name || `系列${index + 1}`,
      type: 'bar',
      data: item.data,
      stack: props.stack ? 'total' : undefined,
      barWidth: props.barWidth === 'auto' ? undefined : props.barWidth,
      itemStyle: {
        color: props.colors[index % props.colors.length],
        borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
      },
      label: {
        show: props.showLabel,
        position: props.horizontal ? 'right' : 'top'
      },
      ...item
    }))
  }
})
</script>
