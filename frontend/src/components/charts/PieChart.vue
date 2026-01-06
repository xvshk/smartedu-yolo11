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
  // 数据 [{ name: 'xxx', value: 100 }]
  data: {
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
  showLegend: {
    type: Boolean,
    default: true
  },
  legendPosition: {
    type: String,
    default: 'bottom',
    validator: (val) => ['top', 'bottom', 'left', 'right'].includes(val)
  },
  radius: {
    type: [String, Array],
    default: () => ['40%', '70%']
  },
  roseType: {
    type: [Boolean, String],
    default: false
  },
  showLabel: {
    type: Boolean,
    default: false
  },
  colors: {
    type: Array,
    default: () => ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#00D4FF', '#FF6B6B']
  }
})

const emit = defineEmits(['retry', 'click'])

const chartOption = computed(() => {
  const legendConfig = {
    top: { top: 0, left: 'center' },
    bottom: { bottom: 0, left: 'center' },
    left: { left: 0, top: 'center', orient: 'vertical' },
    right: { right: 0, top: 'center', orient: 'vertical' }
  }

  return {
    title: props.title ? {
      text: props.title,
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 500 }
    } : undefined,
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: props.showLegend ? {
      ...legendConfig[props.legendPosition],
      type: 'scroll'
    } : undefined,
    color: props.colors,
    series: [{
      type: 'pie',
      radius: props.radius,
      roseType: props.roseType,
      center: ['50%', '50%'],
      data: props.data.map((item, index) => ({
        ...item,
        itemStyle: item.itemStyle || {
          color: props.colors[index % props.colors.length]
        }
      })),
      label: {
        show: props.showLabel,
        formatter: '{b}: {d}%'
      },
      labelLine: {
        show: props.showLabel
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
})
</script>
