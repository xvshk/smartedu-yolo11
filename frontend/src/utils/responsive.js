import { ref, onMounted, onUnmounted } from 'vue'

// 响应式断点配置
export const breakpoints = {
  xs: 480,
  sm: 768,
  md: 1024,
  lg: 1200,
  xl: 1440,
  '2xl': 1920
}

// 当前屏幕尺寸状态
const screenWidth = ref(0)
const screenHeight = ref(0)

// 更新屏幕尺寸
const updateScreenSize = () => {
  screenWidth.value = window.innerWidth
  screenHeight.value = window.innerHeight
}

// 响应式断点 Hook
export const useResponsive = () => {
  onMounted(() => {
    updateScreenSize()
    window.addEventListener('resize', updateScreenSize)
    window.addEventListener('orientationchange', updateScreenSize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateScreenSize)
    window.removeEventListener('orientationchange', updateScreenSize)
  })

  // 检查是否匹配指定断点
  const isBreakpoint = (breakpoint) => {
    return screenWidth.value >= breakpoints[breakpoint]
  }

  // 检查是否在指定断点范围内
  const isBetween = (minBreakpoint, maxBreakpoint) => {
    const minWidth = breakpoints[minBreakpoint] || 0
    const maxWidth = breakpoints[maxBreakpoint] || Infinity
    return screenWidth.value >= minWidth && screenWidth.value < maxWidth
  }

  // 获取当前断点
  const getCurrentBreakpoint = () => {
    const width = screenWidth.value
    if (width >= breakpoints['2xl']) return '2xl'
    if (width >= breakpoints.xl) return 'xl'
    if (width >= breakpoints.lg) return 'lg'
    if (width >= breakpoints.md) return 'md'
    if (width >= breakpoints.sm) return 'sm'
    return 'xs'
  }

  // 响应式状态
  const isXs = () => screenWidth.value < breakpoints.sm
  const isSm = () => isBetween('sm', 'md')
  const isMd = () => isBetween('md', 'lg')
  const isLg = () => isBetween('lg', 'xl')
  const isXl = () => isBetween('xl', '2xl')
  const is2xl = () => screenWidth.value >= breakpoints['2xl']

  // 移动端检测
  const isMobile = () => screenWidth.value < breakpoints.md
  const isTablet = () => isBetween('md', 'lg')
  const isDesktop = () => screenWidth.value >= breakpoints.lg

  // 触摸设备检测
  const isTouchDevice = () => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0
  }

  return {
    screenWidth,
    screenHeight,
    isBreakpoint,
    isBetween,
    getCurrentBreakpoint,
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    is2xl,
    isMobile,
    isTablet,
    isDesktop,
    isTouchDevice
  }
}

// 响应式网格系统
export const useGrid = () => {
  const { getCurrentBreakpoint, isMobile, isTablet } = useResponsive()

  // 获取响应式列数
  const getColumns = (config) => {
    const breakpoint = getCurrentBreakpoint()
    return config[breakpoint] || config.default || 1
  }

  // 获取响应式间距
  const getGutter = (config) => {
    if (typeof config === 'number') return config
    
    const breakpoint = getCurrentBreakpoint()
    return config[breakpoint] || config.default || 16
  }

  // 获取响应式 span
  const getSpan = (config) => {
    if (typeof config === 'number') return config
    
    const breakpoint = getCurrentBreakpoint()
    return config[breakpoint] || config.default || 24
  }

  return {
    getColumns,
    getGutter,
    getSpan
  }
}

// CSS 媒体查询工具
export const mediaQueries = {
  xs: `(max-width: ${breakpoints.sm - 1}px)`,
  sm: `(min-width: ${breakpoints.sm}px) and (max-width: ${breakpoints.md - 1}px)`,
  md: `(min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`,
  lg: `(min-width: ${breakpoints.lg}px) and (max-width: ${breakpoints.xl - 1}px)`,
  xl: `(min-width: ${breakpoints.xl}px) and (max-width: ${breakpoints['2xl'] - 1}px)`,
  '2xl': `(min-width: ${breakpoints['2xl']}px)`,
  
  // 简化版本
  mobile: `(max-width: ${breakpoints.md - 1}px)`,
  tablet: `(min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`,
  desktop: `(min-width: ${breakpoints.lg}px)`,
  
  // 方向查询
  landscape: '(orientation: landscape)',
  portrait: '(orientation: portrait)',
  
  // 高分辨率屏幕
  retina: '(-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi)'
}

// 响应式工具类生成器
export const generateResponsiveClasses = () => {
  const classes = {}
  
  Object.keys(breakpoints).forEach(breakpoint => {
    // 显示/隐藏类
    classes[`hidden-${breakpoint}-up`] = `@media (min-width: ${breakpoints[breakpoint]}px) { display: none !important; }`
    classes[`hidden-${breakpoint}-down`] = `@media (max-width: ${breakpoints[breakpoint] - 1}px) { display: none !important; }`
    classes[`visible-${breakpoint}-up`] = `@media (min-width: ${breakpoints[breakpoint]}px) { display: block !important; }`
    classes[`visible-${breakpoint}-down`] = `@media (max-width: ${breakpoints[breakpoint] - 1}px) { display: block !important; }`
  })
  
  return classes
}

// 响应式字体大小计算
export const getResponsiveFontSize = (baseSize, scaleFactor = 0.8) => {
  const { isMobile, isTablet } = useResponsive()
  
  if (isMobile()) {
    return `${baseSize * scaleFactor}px`
  } else if (isTablet()) {
    return `${baseSize * (scaleFactor + 0.1)}px`
  }
  
  return `${baseSize}px`
}

// 响应式间距计算
export const getResponsiveSpacing = (baseSpacing) => {
  const { isMobile } = useResponsive()
  
  return isMobile() ? Math.max(baseSpacing * 0.75, 8) : baseSpacing
}