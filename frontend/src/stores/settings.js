import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import api from '@/api'

export const useSettingsStore = defineStore('settings', () => {
  // 默认设置
  const defaultSettings = {
    // 通用设置
    language: 'zh-CN',
    theme: 'light',
    primaryColor: '#2196F3',
    sidebarCollapsed: false,
    enableAnimation: true,
    pageSize: 20,
    // 通知设置
    alertNotification: true,
    alertLevels: ['medium', 'high'],
    browserNotification: true,
    emailNotification: false,
    soundNotification: true,
    notificationVolume: 70,
    notificationFrequency: 'realtime',
    doNotDisturb: false,
    dndStartTime: null,
    dndEndTime: null,
    // 检测设置
    detectionSensitivity: 5,
    confidenceThreshold: 60,
    detectionInterval: 5,
    alertThreshold: 3,
    alertCooldown: 300,
    showBoundingBox: true,
    showConfidence: true,
    showBehaviorLabel: true,
    boundingBoxColor: '#2196F3',
    autoSaveRecords: true,
    saveRawFrames: false,
    // 安全设置
    autoLogoutTime: 30,
    rememberLogin: true,
    enableOperationLog: true,
    logRetentionDays: 90
  }

  // 当前设置
  const settings = ref({ ...defaultSettings })
  
  // 加载设置
  const loadSettings = () => {
    const saved = localStorage.getItem('app_settings')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        settings.value = { ...defaultSettings, ...parsed }
      } catch (e) {
        console.error('加载设置失败', e)
      }
    }
    applyTheme()
  }

  // 保存设置到本地和服务器
  const saveSettings = async () => {
    localStorage.setItem('app_settings', JSON.stringify(settings.value))
    applyTheme()
    
    // 尝试保存到服务器
    try {
      await api.settings.saveUserSettings(settings.value)
    } catch (error) {
      console.error('保存设置到服务器失败', error)
    }
  }

  // 应用主题
  const applyTheme = () => {
    const theme = settings.value.theme
    const primaryColor = settings.value.primaryColor
    
    // 应用主题模式
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
      document.documentElement.setAttribute('data-theme', 'dark')
    } else if (theme === 'light') {
      document.documentElement.classList.remove('dark')
      document.documentElement.setAttribute('data-theme', 'light')
    } else {
      // 跟随系统
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        document.documentElement.classList.add('dark')
        document.documentElement.setAttribute('data-theme', 'dark')
      } else {
        document.documentElement.classList.remove('dark')
        document.documentElement.setAttribute('data-theme', 'light')
      }
    }
    
    // 应用主题色
    document.documentElement.style.setProperty('--primary-color', primaryColor)
    document.documentElement.style.setProperty('--el-color-primary', primaryColor)
  }

  // 重置通用设置
  const resetGeneralSettings = () => {
    settings.value.language = defaultSettings.language
    settings.value.theme = defaultSettings.theme
    settings.value.primaryColor = defaultSettings.primaryColor
    settings.value.sidebarCollapsed = defaultSettings.sidebarCollapsed
    settings.value.enableAnimation = defaultSettings.enableAnimation
    settings.value.pageSize = defaultSettings.pageSize
    applyTheme()
  }

  // 重置检测设置
  const resetDetectionSettings = () => {
    settings.value.detectionSensitivity = defaultSettings.detectionSensitivity
    settings.value.confidenceThreshold = defaultSettings.confidenceThreshold
    settings.value.detectionInterval = defaultSettings.detectionInterval
    settings.value.alertThreshold = defaultSettings.alertThreshold
    settings.value.alertCooldown = defaultSettings.alertCooldown
    settings.value.showBoundingBox = defaultSettings.showBoundingBox
    settings.value.showConfidence = defaultSettings.showConfidence
    settings.value.showBehaviorLabel = defaultSettings.showBehaviorLabel
    settings.value.boundingBoxColor = defaultSettings.boundingBoxColor
    settings.value.autoSaveRecords = defaultSettings.autoSaveRecords
    settings.value.saveRawFrames = defaultSettings.saveRawFrames
  }

  // 监听系统主题变化
  if (typeof window !== 'undefined') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (settings.value.theme === 'auto') {
        applyTheme()
      }
    })
  }

  return {
    settings,
    defaultSettings,
    loadSettings,
    saveSettings,
    applyTheme,
    resetGeneralSettings,
    resetDetectionSettings
  }
})
