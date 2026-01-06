<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo">
        <img src="@/assets/logo.svg" alt="Logo" class="logo-img" />
        <span v-show="!isCollapse" class="logo-text">智慧教育平台</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="layout-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        
        <!-- 实时检测 - 仅管理员和教师 -->
        <el-menu-item v-if="isTeacherOrAdmin" index="/detection">
          <el-icon><VideoCamera /></el-icon>
          <template #title>实时检测</template>
        </el-menu-item>
        
        <!-- 精准预警 - 仅管理员和教师 -->
        <el-menu-item v-if="isTeacherOrAdmin" index="/alert">
          <el-icon><Bell /></el-icon>
          <template #title>精准预警</template>
        </el-menu-item>
        
        <!-- 通知反馈 - 所有用户 -->
        <el-menu-item index="/notification">
          <el-icon><Message /></el-icon>
          <template #title>通知反馈</template>
        </el-menu-item>
        
        <el-menu-item index="/portrait">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>学业全景画像</template>
        </el-menu-item>
        
        <!-- 用户管理 - 仅管理员 -->
        <el-menu-item v-if="userStore.role === 'admin'" index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon 
            class="collapse-btn" 
            @click="isCollapse = !isCollapse"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ userStore.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="user-name">{{ userStore.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.role === 'admin'" command="settings">
                  <el-icon><Setting /></el-icon>系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const settingsStore = useSettingsStore()

const isCollapse = ref(false)
let inactivityTimer = null

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')
const isTeacherOrAdmin = computed(() => ['admin', 'teacher'].includes(userStore.role))

// 初始化设置
onMounted(() => {
  try {
    settingsStore.loadSettings()
    isCollapse.value = settingsStore.settings.sidebarCollapsed
    setupInactivityTimer()
  } catch (error) {
    console.error('Layout mounted error:', error)
  }
})

// 设置自动登出计时器
const setupInactivityTimer = () => {
  const autoLogoutTime = settingsStore.settings.autoLogoutTime
  if (autoLogoutTime > 0) {
    resetInactivityTimer()
    document.addEventListener('mousemove', resetInactivityTimer)
    document.addEventListener('keypress', resetInactivityTimer)
    document.addEventListener('click', resetInactivityTimer)
  }
}

const resetInactivityTimer = () => {
  if (inactivityTimer) {
    clearTimeout(inactivityTimer)
  }
  const autoLogoutTime = settingsStore.settings.autoLogoutTime
  if (autoLogoutTime > 0) {
    inactivityTimer = setTimeout(() => {
      handleAutoLogout()
    }, autoLogoutTime * 60 * 1000)
  }
}

const handleAutoLogout = async () => {
  await userStore.logout()
  router.push('/login')
}

onUnmounted(() => {
  if (inactivityTimer) {
    clearTimeout(inactivityTimer)
  }
  document.removeEventListener('mousemove', resetInactivityTimer)
  document.removeEventListener('keypress', resetInactivityTimer)
  document.removeEventListener('click', resetInactivityTimer)
})

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await userStore.logout()
        router.push('/login')
      } catch {
        // 取消退出
      }
      break
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  width: 100%;
  height: 100vh;
}

.layout-aside {
  background: linear-gradient(180deg, #2196F3 0%, #1565C0 100%);
  transition: width 0.3s;
  overflow: hidden;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
    
    .logo-img {
      width: 32px;
      height: 32px;
    }
    
    .logo-text {
      margin-left: 10px;
      font-size: 16px;
      font-weight: bold;
      color: #fff;
      white-space: nowrap;
    }
  }
  
  .layout-menu {
    border-right: none;
    background: transparent;
    
    :deep(.el-menu-item) {
      color: rgba(255, 255, 255, 0.85);
      margin: 4px 8px;
      border-radius: 8px;
      
      &:hover {
        background: rgba(255, 255, 255, 0.15);
        color: #fff;
      }
      
      &.is-active {
        background: rgba(255, 255, 255, 0.25);
        color: #fff;
        font-weight: 500;
      }
    }
  }
}

.layout-header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 15px;
    
    .collapse-btn {
      font-size: 20px;
      cursor: pointer;
      color: #666;
      transition: color 0.3s;
      
      &:hover {
        color: #2196F3;
      }
    }
  }
  
  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 6px 12px;
      border-radius: 20px;
      transition: background 0.3s;
      
      &:hover {
        background: #f5f7fa;
      }
      
      .user-avatar {
        background: #2196F3;
        color: #fff;
      }
      
      .user-name {
        color: #333;
        font-size: 14px;
      }
    }
  }
}

.layout-main {
  background: linear-gradient(180deg, #e8f4fc 0%, #f5f7fa 100%);
  padding: 20px;
  overflow-y: auto;
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
