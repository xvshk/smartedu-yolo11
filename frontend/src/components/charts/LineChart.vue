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
  smooth: {
    type: Boolean,
    default: true
  },
  showArea: {
    type: Boolean,
    default: false
  },
  showLegend: {
    type: Boolean,
    default: true
  },
  title: {
    type: String,
    default: ''
  },
  yAxisName: {
    type: String,
    default: ''
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

  return {
    title: props.title ? {
      text: props.title,
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 500 }
    } : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
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
    xAxis: {
      type: 'category',
      data: props.xAxisData,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: props.yAxisName
    },
    color: props.colors,
    series: seriesData.map((item, index) => ({
      name: item.name || `系列${index + 1}`,
      type: 'line',
      data: item.data,
      smooth: props.smooth,
      areaStyle: props.showArea ? {
        opacity: 0.3,
        color: props.colors[index % props.colors.length]
      } : undefined,
      lineStyle: {
        width: 2,
        color: props.colors[index % props.colors.length]
      },
      itemStyle: {
        color: props.colors[index % props.colors.length]
      },
      ...item
    }))
  }
})
</script>
