<template>
  <div class="base-chart-wrapper" :style="{ height: height, width: width }">
    <SkeletonLoader v-if="loading" type="chart" :style="{ height: height }" />
    <ErrorHandler 
      v-else-if="error" 
      type="default" 
      :message="error" 
      size="small"
      @retry="$emit('retry')"
    />
    <div 
      v-show="!loading && !error"
      ref="chartRef" 
      class="base-chart" 
      :style="{ height: height, width: width }"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useThemeStore } from '@/stores/theme'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import ErrorHandler from '@/components/ErrorHandler.vue'

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  height: {
    type: String,
    default: '300px'
  },
  width: {
    type: String,
    default: '100%'
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  autoResize: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['retry', 'click', 'legendselectchanged'])

const themeStore = useThemeStore()
const chartRef = ref(null)
let chartInstance = null

// 获取主题配色
const getThemeColors = () => {
  const isDark = themeStore.isDarkMode
  return {
    backgroundColor: 'transparent',
    textStyle: {
      color: isDark ? '#E5EAF3' : '#303133'
    },
    legend: {
      textStyle: {
        color: isDark ? '#A3A6AD' : '#606266'
      }
    },
    tooltip: {
      backgroundColor: isDark ? '#1D1E1F' : '#FFFFFF',
      borderColor: isDark ? '#4C4D4F' : '#EBEEF5',
      textStyle: {
        color: isDark ? '#E5EAF3' : '#303133'
      }
    },
    xAxis: {
      axisLine: {
        lineStyle: { color: isDark ? '#4C4D4F' : '#DCDFE6' }
      },
      axisLabel: {
        color: isDark ? '#A3A6AD' : '#606266'
      },
      splitLine: {
        lineStyle: { color: isDark ? '#363637' : '#EBEEF5' }
      }
    },
    yAxis: {
      axisLine: {
        lineStyle: { color: isDark ? '#4C4D4F' : '#DCDFE6' }
      },
      axisLabel: {
        color: isDark ? '#A3A6AD' : '#606266'
      },
      splitLine: {
        lineStyle: { color: isDark ? '#363637' : '#EBEEF5' }
      }
    }
  }
}

// 合并主题配置
const mergeThemeOption = (option) => {
  const themeColors = getThemeColors()
  return echarts.util.merge(themeColors, option, true)
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value || props.loading || props.error) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  const mergedOption = mergeThemeOption(props.option)
  chartInstance.setOption(mergedOption)
  
  // 绑定事件
  chartInstance.on('click', (params) => emit('click', params))
  chartInstance.on('legendselectchanged', (params) => emit('legendselectchanged', params))
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || props.loading || props.error) return
  const mergedOption = mergeThemeOption(props.option)
  chartInstance.setOption(mergedOption, true)
}

// 调整大小
const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听配置变化
watch(() => props.option, () => {
  nextTick(updateChart)
}, { deep: true })

// 监听主题变化
watch(() => themeStore.isDarkMode, () => {
  nextTick(updateChart)
})

// 监听加载状态
watch(() => props.loading, (newVal, oldVal) => {
  if (oldVal && !newVal && !props.error) {
    // loading 结束后，更新图表
    nextTick(() => {
      if (chartInstance) {
        updateChart()
        resizeChart()
      } else {
        initChart()
      }
    })
  }
})

// 监听错误状态
watch(() => props.error, (newVal, oldVal) => {
  if (oldVal && !newVal && !props.loading) {
    nextTick(() => {
      if (chartInstance) {
        updateChart()
        resizeChart()
      } else {
        initChart()
      }
    })
  }
})

onMounted(() => {
  nextTick(initChart)
  
  if (props.autoResize) {
    window.addEventListener('resize', resizeChart)
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  
  if (props.autoResize) {
    window.removeEventListener('resize', resizeChart)
  }
})

// 暴露方法
defineExpose({
  resize: resizeChart,
  getInstance: () => chartInstance
})
</script>

<style lang="scss" scoped>
.base-chart-wrapper {
  position: relative;
}

.base-chart {
  position: relative;
  width: 100%;
  height: 100%;
}
</style>
