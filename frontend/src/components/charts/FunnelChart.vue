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
  // 数据格式: [{ name: '生成', value: 100 }, { name: '查看', value: 80 }, ...]
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
  showLabel: {
    type: Boolean,
    default: true
  },
  showConversionRate: {
    type: Boolean,
    default: true
  },
  sort: {
    type: String,
    default: 'descending',
    validator: (val) => ['ascending', 'descending', 'none'].includes(val)
  },
  gap: {
    type: Number,
    default: 2
  },
  colors: {
    type: Array,
    default: () => ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  }
})

defineEmits(['retry', 'click'])

// 计算转化率
const dataWithRate = computed(() => {
  if (!props.data || props.data.length === 0) return []
  
  return props.data.map((item, index) => {
    let rate = 100
    if (index > 0 && props.data[index - 1].value > 0) {
      rate = ((item.value / props.data[index - 1].value) * 100).toFixed(1)
    }
    return {
      ...item,
      rate: index === 0 ? 100 : parseFloat(rate)
    }
  })
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
      trigger: 'item',
      formatter: (params) => {
        const item = dataWithRate.value[params.dataIndex]
        let result = `${params.name}: ${params.value}`
        if (props.showConversionRate && params.dataIndex > 0) {
          result += `<br/>转化率: ${item.rate}%`
        }
        return result
      }
    },
    legend: {
      bottom: 0,
      type: 'scroll'
    },
    color: props.colors,
    series: [{
      type: 'funnel',
      left: '10%',
      top: props.title ? 40 : 20,
      bottom: 40,
      width: '80%',
      min: 0,
      max: Math.max(...props.data.map(d => d.value)),
      minSize: '0%',
      maxSize: '100%',
      sort: props.sort,
      gap: props.gap,
      label: {
        show: props.showLabel,
        position: 'inside',
        formatter: (params) => {
          const item = dataWithRate.value[params.dataIndex]
          if (props.showConversionRate && params.dataIndex > 0) {
            return `${params.name}\n${item.rate}%`
          }
          return params.name
        }
      },
      labelLine: {
        length: 10,
        lineStyle: {
          width: 1,
          type: 'solid'
        }
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1
      },
      emphasis: {
        label: {
          fontSize: 14
        }
      },
      data: props.data.map((item, index) => ({
        ...item,
        itemStyle: {
          color: props.colors[index % props.colors.length]
        }
      }))
    }]
  }
})
</script>
