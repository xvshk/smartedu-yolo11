import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const permissions = ref([])

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')
  const role = computed(() => user.value?.role || '')

  // 方法
  async function login(credentials) {
    try {
      const response = await api.auth.login(credentials)
      if (response.success) {
        token.value = response.data.access_token
        refreshToken.value = response.data.refresh_token
        user.value = response.data.user
        
        localStorage.setItem('token', token.value)
        localStorage.setItem('refreshToken', refreshToken.value)
        localStorage.setItem('user', JSON.stringify(user.value))
        localStorage.setItem('userRole', user.value.role || '')
        
        // 保存学生ID（如果是学生角色）
        if (user.value.student_id) {
          localStorage.setItem('studentId', user.value.student_id)
        }
        
        return { success: true }
      }
      return { success: false, message: response.message }
    } catch (error) {
      return { success: false, message: error.message || '登录失败' }
    }
  }

  async function logout() {
    try {
      await api.auth.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      token.value = ''
      refreshToken.value = ''
      user.value = null
      permissions.value = []
      
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
      localStorage.removeItem('userRole')
      localStorage.removeItem('studentId')
    }
  }

  async function fetchUserInfo() {
    try {
      const response = await api.auth.getCurrentUser()
      if (response.success) {
        user.value = response.data
        permissions.value = response.data.permissions || []
        localStorage.setItem('user', JSON.stringify(user.value))
      }
    } catch (error) {
      console.error('Fetch user info error:', error)
    }
  }

  function hasPermission(permission) {
    return permissions.value.includes(permission)
  }

  return {
    token,
    refreshToken,
    user,
    permissions,
    isLoggedIn,
    username,
    role,
    login,
    logout,
    fetchUserInfo,
    hasPermission
  }
})
