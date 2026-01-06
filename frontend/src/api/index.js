import axios from 'axios'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        router.push('/login')
      }
      
      return Promise.reject(data || { message: '请求失败' })
    }
    return Promise.reject({ message: '网络错误' })
  }
)

// API模块
const api = {
  // 认证模块
  auth: {
    login: (data) => request.post('/auth/login', data),
    logout: () => request.post('/auth/logout'),
    refresh: () => request.post('/auth/refresh'),
    getCurrentUser: () => request.get('/auth/me')
  },
  
  // 用户管理模块
  user: {
    list: (params) => request.get('/user/list', { params }),
    create: (data) => request.post('/user/create', data),
    update: (id, data) => request.put(`/user/update/${id}`, data),
    delete: (id) => request.delete(`/user/delete/${id}`),
    changePassword: (data) => request.post('/user/change-password', data)
  },
  
  // 系统设置模块
  settings: {
    getUserSettings: () => request.get('/settings/user-settings'),
    saveUserSettings: (data) => request.post('/settings/user-settings', data),
    getSystemInfo: () => request.get('/settings/system-info'),
    exportData: (type) => `/api/settings/export/${type}`,
    cleanupData: (days) => request.post('/settings/cleanup', { days })
  },
  
  // 学生画像模块
  portrait: {
    getOverview: (params) => request.get('/portrait/overview', { params }),
    getBehaviorDistribution: (params) => request.get('/portrait/behavior-distribution', { params }),
    getAttentionTrend: (params) => request.get('/portrait/attention-trend', { params }),
    getWarningRanking: (params) => request.get('/portrait/warning-ranking', { params }),
    getStudents: (params) => request.get('/portrait/students', { params }),
    getClasses: () => request.get('/portrait/classes'),
    getStudentPortrait: (studentId, params) => request.get(`/portrait/student/${studentId}`, { params }),
    getStudentSuggestions: (studentId) => request.get(`/portrait/student/${studentId}/suggestions`),
    exportData: (params) => request.get('/portrait/export', { params })
  },
  
  // 行为检测模块
  detection: {
    detect: (data) => request.post('/detection/detect', data, { timeout: 60000 }),
    detectFast: (data) => request.post('/detection/detect-fast', data, { timeout: 10000 }),
    detectVideo: (formData, onProgress) => request.post('/detection/detect-video', formData, {
      timeout: 600000,
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
    }),
    detectVideoOptimized: (formData, onProgress) => request.post('/detection/detect-video-optimized', formData, {
      timeout: 600000,
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
    }),
    getClasses: () => request.get('/detection/classes'),
    getSettings: () => request.get('/detection/settings'),
    updateSettings: (data) => request.post('/detection/settings', data),
    getFrameSkip: () => request.get('/detection/frame-skip'),
    setFrameSkip: (data) => request.post('/detection/frame-skip', data),
    getGpuInfo: () => request.get('/detection/gpu-info'),
    getHistory: (params) => request.get('/detection/history', { params }),
    getDetail: (sessionId) => request.get(`/detection/history/${sessionId}`),
    deleteHistory: (sessionId) => request.delete(`/detection/history/${sessionId}`),
    getTimeStatistics: () => request.get('/detection/time-statistics'),
    resetTimeStatistics: () => request.post('/detection/time-statistics/reset'),
    // PySide6 桌面应用集成
    launchDesktopApp: () => request.post('/detection/launch-desktop'),
    startSession: (data) => request.post('/detection/session/start', data),
    endSession: (data) => request.post('/detection/session/end', data),
    saveDetection: (data) => request.post('/detection/save', data)
  },
  
  // 智能预警模块
  alert: {
    // 预警列表
    getAlerts: (params) => request.get('/alert/alerts', { params }),
    getAlertDetail: (alertId) => request.get(`/alert/alerts/${alertId}`),
    getUnreadAlerts: (params) => request.get('/alert/alerts/unread', { params }),
    markRead: (alertId) => request.post(`/alert/alerts/${alertId}/read`),
    markAllRead: (sessionId) => request.post('/alert/alerts/read-all', { session_id: sessionId }),
    deleteAlert: (alertId) => request.delete(`/alert/alerts/${alertId}`),
    
    // 统计
    getStatistics: (params) => request.get('/alert/alerts/statistics', { params }),
    exportAlerts: (params) => request.get('/alert/alerts/export', { params, responseType: 'blob' }),
    
    // 规则管理
    getRules: (params) => request.get('/alert/rules', { params }),
    getRuleDetail: (ruleId) => request.get(`/alert/rules/${ruleId}`),
    createRule: (data) => request.post('/alert/rules', data),
    updateRule: (ruleId, data) => request.put(`/alert/rules/${ruleId}`, data),
    deleteRule: (ruleId) => request.delete(`/alert/rules/${ruleId}`),
    
    // 干预建议
    getSuggestions: (alertId) => request.get(`/alert/alerts/${alertId}/suggestions`),
    recordIntervention: (alertId, data) => request.post(`/alert/alerts/${alertId}/interventions`, data),
    updateIntervention: (interventionId, data) => request.put(`/alert/interventions/${interventionId}`, data),
    getInterventionStats: (params) => request.get('/alert/interventions/statistics', { params }),
    
    // 通知偏好
    getNotificationPrefs: () => request.get('/alert/notification-preferences'),
    updateNotificationPrefs: (data) => request.post('/alert/notification-preferences', data)
  },
  
  // 预警通知和学生反馈模块
  notification: {
    // 发送通知（老师/管理员）
    send: (data) => request.post('/notification/send', data),
    sendBatch: (data) => request.post('/notification/send-batch', data),
    getSent: (params) => request.get('/notification/sent', { params }),
    
    // 接收通知（学生）
    getReceived: (params) => request.get('/notification/received', { params }),
    getUnreadCount: () => request.get('/notification/unread-count'),
    getDetail: (notificationId) => request.get(`/notification/${notificationId}`),
    markRead: (notificationId) => request.post(`/notification/${notificationId}/read`),
    markAllRead: () => request.post('/notification/read-all'),
    
    // 学生反馈
    submitFeedback: (notificationId, data) => request.post(`/notification/${notificationId}/feedback`, data),
    getMyFeedbacks: (params) => request.get('/notification/my-feedbacks', { params }),
    
    // 反馈审核（老师/管理员）
    getPendingFeedbacks: (params) => request.get('/notification/feedbacks/pending', { params }),
    getFeedbackDetail: (feedbackId) => request.get(`/notification/feedbacks/${feedbackId}`),
    reviewFeedback: (feedbackId, data) => request.post(`/notification/feedbacks/${feedbackId}/review`, data),
    
    // 模板管理
    getTemplates: (params) => request.get('/notification/templates', { params }),
    createTemplate: (data) => request.post('/notification/templates', data),
    
    // 统计
    getStatistics: (params) => request.get('/notification/statistics', { params })
  },
  
  // Dashboard 模块
  dashboard: {
    // 老师统计
    getTeacherStats: () => request.get('/dashboard/teacher/stats'),
    getTeacherClasses: () => request.get('/dashboard/teacher/classes'),
    getClassStudents: (classId) => request.get(`/dashboard/teacher/class/${classId}/students`),
    
    // 管理员统计
    getAdminStats: () => request.get('/dashboard/admin/stats'),
    
    // 学生统计
    getStudentStats: () => request.get('/dashboard/student/stats')
  },
  
  // 机器学习模块已移除
  // MLflow追踪功能仍可通过直接访问MLflow UI使用
}

export default api
