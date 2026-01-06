// 统一图表组件库
export { default as BaseChart } from './BaseChart.vue'
export { default as LineChart } from './LineChart.vue'
export { default as PieChart } from './PieChart.vue'
export { default as BarChart } from './BarChart.vue'
export { default as FunnelChart } from './FunnelChart.vue'
export { default as RelationGraph } from './RelationGraph.vue'
export { default as HeatmapChart } from './HeatmapChart.vue'

// 图表配色方案
export const chartColors = {
  primary: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399'],
  success: ['#67C23A', '#85CE61', '#A4DA89', '#C2E7B0', '#E1F3D8'],
  warning: ['#E6A23C', '#EEAB4D', '#F5C06E', '#F9D58F', '#FCEAB0'],
  danger: ['#F56C6C', '#F78989', '#F9A7A7', '#FAC5C5', '#FCE3E3'],
  info: ['#909399', '#A6A9AD', '#BCBEC2', '#D3D4D6', '#E9EAEB'],
  gradient: ['#409EFF', '#36D1DC', '#5B86E5', '#667EEA', '#764BA2'],
  behavior: {
    positive: '#67C23A',  // 积极行为
    negative: '#F56C6C',  // 消极行为
    neutral: '#909399'    // 中性行为
  }
}

// 行为类型配色
export const behaviorColors = {
  handrise: '#67C23A',
  read: '#67C23A',
  write: '#67C23A',
  sleep: '#F56C6C',
  stand: '#E6A23C',
  using_electronic_devices: '#F56C6C',
  talk: '#E6A23C'
}

// 获取行为颜色
export const getBehaviorColor = (behavior) => {
  return behaviorColors[behavior] || '#909399'
}

// 行为中文名映射
export const behaviorNames = {
  handrise: '举手',
  read: '阅读',
  write: '书写',
  sleep: '睡觉',
  stand: '站立',
  using_electronic_devices: '使用电子设备',
  talk: '交谈'
}

// 获取行为中文名
export const getBehaviorName = (behavior) => {
  return behaviorNames[behavior] || behavior
}


// 预警级别颜色
export const alertLevelColors = {
  0: '#67C23A',  // 正常 - 绿色
  1: '#909399',  // 轻度 - 灰色
  2: '#E6A23C',  // 中度 - 橙色
  3: '#F56C6C'   // 严重 - 红色
}

// 获取预警级别颜色
export const getAlertLevelColor = (level) => {
  return alertLevelColors[level] || '#909399'
}

// 预警级别名称
export const alertLevelNames = {
  0: '正常',
  1: '轻度预警',
  2: '中度预警',
  3: '严重预警'
}

// 获取预警级别名称
export const getAlertLevelName = (level) => {
  return alertLevelNames[level] || '未知'
}
