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
  // 节点数据: [{ id: '1', name: '学生A', category: 0, value: 10 }, ...]
  nodes: {
    type: Array,
    default: () => []
  },
  // 连线数据: [{ source: '1', target: '2', value: 10 }, ...]
  links: {
    type: Array,
    default: () => []
  },
  // 分类: [{ name: '学生' }, { name: '行为' }, { name: '预警' }]
  categories: {
    type: Array,
    default: () => []
  },
  // 样式
  height: {
    type: String,
    default: '400px'
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
  layout: {
    type: String,
    default: 'force',
    validator: (val) => ['force', 'circular'].includes(val)
  },
  draggable: {
    type: Boolean,
    default: true
  },
  showLabel: {
    type: Boolean,
    default: true
  },
  repulsion: {
    type: Number,
    default: 100
  },
  colors: {
    type: Array,
    default: () => ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#00D4FF']
  }
})

defineEmits(['retry', 'click'])

const chartOption = computed(() => {
  if (!props.nodes || props.nodes.length === 0) {
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

  // 处理节点数据
  const processedNodes = props.nodes.map((node, index) => ({
    ...node,
    symbolSize: node.symbolSize || Math.max(20, Math.min(50, (node.value || 10) * 2)),
    itemStyle: {
      color: props.colors[node.category % props.colors.length]
    }
  }))

  // 处理连线数据
  const processedLinks = props.links.map(link => ({
    ...link,
    lineStyle: {
      width: Math.max(1, Math.min(5, (link.value || 1) / 2)),
      curveness: 0.2
    }
  }))

  return {
    title: props.title ? {
      text: props.title,
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 500 }
    } : undefined,
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `${params.name}${params.value ? ': ' + params.value : ''}`
        } else if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}${params.value ? ': ' + params.value : ''}`
        }
        return params.name
      }
    },
    legend: props.categories.length > 0 ? {
      data: props.categories.map(c => c.name),
      bottom: 0,
      type: 'scroll'
    } : undefined,
    color: props.colors,
    animationDuration: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph',
      layout: props.layout,
      data: processedNodes,
      links: processedLinks,
      categories: props.categories,
      roam: true,
      draggable: props.draggable,
      label: {
        show: props.showLabel,
        position: 'right',
        formatter: '{b}'
      },
      labelLayout: {
        hideOverlap: true
      },
      scaleLimit: {
        min: 0.4,
        max: 2
      },
      lineStyle: {
        color: 'source',
        opacity: 0.6
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      force: props.layout === 'force' ? {
        repulsion: props.repulsion,
        gravity: 0.1,
        edgeLength: [50, 150],
        layoutAnimation: true
      } : undefined,
      circular: props.layout === 'circular' ? {
        rotateLabel: true
      } : undefined
    }]
  }
})
</script>
