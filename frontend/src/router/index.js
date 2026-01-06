import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页', icon: 'HomeFilled' }
      },
      {
        path: 'detection',
        name: 'Detection',
        component: () => import('@/views/Detection.vue'),
        meta: { title: '实时检测', icon: 'VideoCamera' }
      },
      {
        path: 'alert',
        name: 'Alert',
        component: () => import('@/views/Alert.vue'),
        meta: { title: '精准预警', icon: 'Bell' }
      },
      {
        path: 'notification',
        name: 'Notification',
        component: () => import('@/views/Notification.vue'),
        meta: { title: '通知反馈', icon: 'Message' }
      },
      {
        path: 'portrait',
        name: 'Portrait',
        component: () => import('@/views/Portrait.vue'),
        meta: { title: '学业全景画像', icon: 'DataAnalysis' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理', icon: 'User', permission: 'manage_users' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心', icon: 'User' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const role = userStore.user?.role || localStorage.getItem('userRole') || ''
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/dashboard')
  } else {
    // 角色权限检查
    const teacherOnlyPages = ['/detection', '/alert']
    const adminOnlyPages = ['/users', '/settings']
    
    if (teacherOnlyPages.includes(to.path) && !['admin', 'teacher'].includes(role)) {
      next('/dashboard')
    } else if (adminOnlyPages.includes(to.path) && role !== 'admin') {
      next('/dashboard')
    } else {
      next()
    }
  }
})

export default router
