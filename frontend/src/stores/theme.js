import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // 主题状态
  const currentTheme = ref('light')
  const systemPreference = ref('light')
  const userPreference = ref(null) // null 表示跟随系统

  // 初始化主题
  const initTheme = () => {
    // 检测系统主题偏好
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemPreference.value = mediaQuery.matches ? 'dark' : 'light'
    
    // 监听系统主题变化
    mediaQuery.addEventListener('change', (e) => {
      systemPreference.value = e.matches ? 'dark' : 'light'
      if (!userPreference.value) {
        applyTheme(systemPreference.value)
      }
    })

    // 从本地存储读取用户偏好
    const stored = localStorage.getItem('theme-preference')
    if (stored && ['light', 'dark', 'auto'].includes(stored)) {
      userPreference.value = stored === 'auto' ? null : stored
    }

    // 应用初始主题
    const initialTheme = userPreference.value || systemPreference.value
    applyTheme(initialTheme)
  }

  // 应用主题
  const applyTheme = (theme) => {
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
    
    // 更新 Element Plus 主题类
    const body = document.body
    body.classList.remove('light-theme', 'dark-theme')
    body.classList.add(`${theme}-theme`)
    
    // 更新 meta 主题色
    updateMetaThemeColor(theme)
  }

  // 更新浏览器主题色
  const updateMetaThemeColor = (theme) => {
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', theme === 'dark' ? '#121212' : '#2196F3')
    }
  }

  // 设置主题
  const setTheme = (theme) => {
    if (theme === 'auto') {
      userPreference.value = null
      localStorage.setItem('theme-preference', 'auto')
      applyTheme(systemPreference.value)
    } else {
      userPreference.value = theme
      localStorage.setItem('theme-preference', theme)
      applyTheme(theme)
    }
  }

  // 切换主题
  const toggleTheme = () => {
    const newTheme = currentTheme.value === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
  }

  // 获取当前主题偏好设置
  const getThemePreference = () => {
    return userPreference.value || 'auto'
  }

  // 监听主题变化，同步到其他组件
  watch(currentTheme, (newTheme) => {
    // 可以在这里添加主题变化的副作用
    console.log(`Theme changed to: ${newTheme}`)
  })

  return {
    currentTheme,
    systemPreference,
    userPreference,
    initTheme,
    setTheme,
    toggleTheme,
    getThemePreference
  }
})

// 主题相关的工具函数
export const themeUtils = {
  // 获取当前主题的 CSS 变量值
  getCSSVariable: (variableName) => {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(variableName)
      .trim()
  },

  // 设置 CSS 变量值
  setCSSVariable: (variableName, value) => {
    document.documentElement.style.setProperty(variableName, value)
  },

  // 检查是否为深色主题
  isDarkTheme: () => {
    return document.documentElement.getAttribute('data-theme') === 'dark'
  },

  // 获取主题适配的颜色
  getThemeColor: (lightColor, darkColor) => {
    return themeUtils.isDarkTheme() ? darkColor : lightColor
  }
}