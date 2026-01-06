import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useNavigationStore = defineStore('navigation', () => {
  // router 和 route 将在 initNavigation 中延迟获取
  let router = null
  let route = null

  // 导航状态
  const currentPath = ref('')
  const breadcrumbs = ref([])
  const pageTitle = ref('')
  const pageContext = ref({}) // 跨页面传递的上下文信息
  const navigationHistory = ref([])
  const maxHistoryLength = 20

  // 页面配置映射
  const pageConfigs = {
    '/': {
      title: '系统概览',
      breadcrumbs: [{ label: '首页', path: '/' }],
      icon: 'HomeFilled'
    },
    '/detection': {
      title: '行为检测',
      breadcrumbs: [
        { label: '首页', path: '/' },
        { label: '行为检测', path: '/detection' }
      ],
      icon: 'VideoCamera'
    },
    '/alert': {
      title: '预警管理',
      breadcrumbs: [
        { label: '首页', path: '/' },
        { label: '预警管理', path: '/alert' }
      ],
      icon: 'Bell'
    },
    '/portrait': {
      title: '学业画像',
      breadcrumbs: [
        { label: '首页', path: '/' },
        { label: '学业画像', path: '/portrait' }
      ],
      icon: 'DataAnalysis'
    },
    '/users': {
      title: '用户管理',
      breadcrumbs: [
        { label: '首页', path: '/' },
        { label: '用户管理', path: '/users' }
      ],
      icon: 'User'
    }
  }

  // 计算属性
  const currentPageConfig = computed(() => {
    return pageConfigs[currentPath.value] || {
      title: '未知页面',
      breadcrumbs: [{ label: '首页', path: '/' }],
      icon: 'Document'
    }
  })

  const canGoBack = computed(() => {
    return navigationHistory.value.length > 1
  })

  const previousPage = computed(() => {
    if (navigationHistory.value.length > 1) {
      return navigationHistory.value[navigationHistory.value.length - 2]
    }
    return null
  })

  // 初始化导航状态
  const initNavigation = (routerInstance, routeInstance) => {
    router = routerInstance
    route = routeInstance
    
    if (route) {
      updateCurrentPage(route.path)
      
      // 监听路由变化
      watch(() => route.path, (newPath) => {
        updateCurrentPage(newPath)
      })
    }
  }

  // 更新当前页面信息
  const updateCurrentPage = (path) => {
    currentPath.value = path
    const config = pageConfigs[path]
    
    if (config) {
      pageTitle.value = config.title
      breadcrumbs.value = [...config.breadcrumbs]
    }
    
    // 更新导航历史
    addToHistory(path)
  }

  // 添加到导航历史
  const addToHistory = (path) => {
    // 避免重复添加相同路径
    if (navigationHistory.value[navigationHistory.value.length - 1]?.path !== path) {
      navigationHistory.value.push({
        path,
        timestamp: Date.now(),
        title: pageConfigs[path]?.title || '未知页面'
      })
      
      // 限制历史记录长度
      if (navigationHistory.value.length > maxHistoryLength) {
        navigationHistory.value.shift()
      }
    }
  }

  // 设置页面上下文
  const setPageContext = (key, value) => {
    pageContext.value[key] = value
  }

  // 获取页面上下文
  const getPageContext = (key) => {
    return pageContext.value[key]
  }

  // 清除页面上下文
  const clearPageContext = (key = null) => {
    if (key) {
      delete pageContext.value[key]
    } else {
      pageContext.value = {}
    }
  }

  // 导航到指定页面并传递上下文
  const navigateWithContext = (path, context = {}) => {
    // 设置上下文
    Object.keys(context).forEach(key => {
      setPageContext(key, context[key])
    })
    
    // 导航
    router.push(path)
  }

  // 返回上一页
  const goBack = () => {
    if (canGoBack.value) {
      const prevPage = previousPage.value
      if (prevPage) {
        // 从历史中移除当前页面
        navigationHistory.value.pop()
        router.push(prevPage.path)
      }
    } else {
      router.push('/')
    }
  }

  // 设置自定义面包屑
  const setBreadcrumbs = (customBreadcrumbs) => {
    breadcrumbs.value = [...customBreadcrumbs]
  }

  // 添加面包屑项
  const addBreadcrumb = (breadcrumb) => {
    breadcrumbs.value.push(breadcrumb)
  }

  // 设置页面标题
  const setPageTitle = (title) => {
    pageTitle.value = title
    // 同时更新浏览器标题
    document.title = `${title} - 智慧教育平台`
  }

  // 获取导航历史
  const getNavigationHistory = () => {
    return [...navigationHistory.value]
  }

  // 清除导航历史
  const clearNavigationHistory = () => {
    navigationHistory.value = []
  }

  // 检查是否来自特定页面
  const isFromPage = (path) => {
    return previousPage.value?.path === path
  }

  // 获取页面间的关联数据传递方法
  const createPageLink = (targetPath, linkData = {}) => {
    return {
      path: targetPath,
      onClick: () => navigateWithContext(targetPath, linkData),
      context: linkData
    }
  }

  return {
    // 状态
    currentPath,
    breadcrumbs,
    pageTitle,
    pageContext,
    navigationHistory,
    
    // 计算属性
    currentPageConfig,
    canGoBack,
    previousPage,
    
    // 方法
    initNavigation,
    updateCurrentPage,
    setPageContext,
    getPageContext,
    clearPageContext,
    navigateWithContext,
    goBack,
    setBreadcrumbs,
    addBreadcrumb,
    setPageTitle,
    getNavigationHistory,
    clearNavigationHistory,
    isFromPage,
    createPageLink
  }
})

// 导航工具函数
export const navigationUtils = {
  // 创建带参数的页面链接
  createStudentLink: (studentId, studentName) => {
    const navStore = useNavigationStore()
    return navStore.createPageLink('/portrait', {
      studentId,
      studentName,
      fromPage: 'users'
    })
  },

  // 创建带预警信息的学生画像链接
  createAlertStudentLink: (alertId, studentId, studentName) => {
    const navStore = useNavigationStore()
    return navStore.createPageLink('/portrait', {
      studentId,
      studentName,
      alertId,
      fromPage: 'alert',
      highlightAlert: true
    })
  },

  // 创建带检测会话的预警链接
  createDetectionAlertLink: (sessionId, detectionData) => {
    const navStore = useNavigationStore()
    return navStore.createPageLink('/alert', {
      sessionId,
      detectionData,
      fromPage: 'detection',
      autoCreateAlert: true
    })
  },

  // 获取返回链接文本
  getBackLinkText: () => {
    const navStore = useNavigationStore()
    const prevPage = navStore.previousPage
    return prevPage ? `返回${prevPage.title}` : '返回首页'
  }
}