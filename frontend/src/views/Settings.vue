<template>
  <div class="settings-page">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="menu-card">
          <el-menu :default-active="activeTab" @select="handleSelect">
            <el-menu-item index="general">
              <el-icon><Setting /></el-icon>
              <span>通用设置</span>
            </el-menu-item>
            <el-menu-item index="notification">
              <el-icon><Bell /></el-icon>
              <span>通知设置</span>
            </el-menu-item>
            <el-menu-item index="detection">
              <el-icon><VideoCamera /></el-icon>
              <span>检测设置</span>
            </el-menu-item>
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="data">
              <el-icon><FolderOpened /></el-icon>
              <span>数据管理</span>
            </el-menu-item>
            <el-menu-item index="about">
              <el-icon><InfoFilled /></el-icon>
              <span>关于系统</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <!-- 通用设置 -->
        <el-card v-show="activeTab === 'general'">
          <template #header><span>通用设置</span></template>
          <el-form label-width="140px" class="settings-form">
            <el-form-item label="系统语言">
              <el-select v-model="settingsStore.settings.language" style="width: 240px">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item label="主题模式">
              <el-radio-group v-model="settingsStore.settings.theme" @change="handleThemeChange">
                <el-radio-button label="light">
                  <el-icon><Sunny /></el-icon> 浅色
                </el-radio-button>
                <el-radio-button label="dark">
                  <el-icon><Moon /></el-icon> 深色
                </el-radio-button>
                <el-radio-button label="auto">
                  <el-icon><Monitor /></el-icon> 跟随系统
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="主题色">
              <el-color-picker v-model="settingsStore.settings.primaryColor" :predefine="predefineColors" @change="handleColorChange" />
              <span class="setting-hint">选择系统主题色</span>
            </el-form-item>
            <el-form-item label="侧边栏默认折叠">
              <el-switch v-model="settingsStore.settings.sidebarCollapsed" />
            </el-form-item>
            <el-form-item label="页面切换动画">
              <el-switch v-model="settingsStore.settings.enableAnimation" />
            </el-form-item>
            <el-form-item label="表格每页条数">
              <el-select v-model="settingsStore.settings.pageSize" style="width: 240px">
                <el-option :label="10" :value="10" />
                <el-option :label="20" :value="20" />
                <el-option :label="50" :value="50" />
                <el-option :label="100" :value="100" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
              <el-button @click="resetGeneralSettings">恢复默认</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 通知设置 -->
        <el-card v-show="activeTab === 'notification'">
          <template #header><span>通知设置</span></template>
          <el-form label-width="140px" class="settings-form">
            <el-divider content-position="left">预警通知</el-divider>
            <el-form-item label="启用预警通知">
              <el-switch v-model="settingsStore.settings.alertNotification" />
              <span class="setting-hint">开启后将接收课堂行为预警通知</span>
            </el-form-item>
            <el-form-item label="预警级别筛选">
              <el-checkbox-group v-model="settingsStore.settings.alertLevels">
                <el-checkbox label="low">轻度</el-checkbox>
                <el-checkbox label="medium">中度</el-checkbox>
                <el-checkbox label="high">严重</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-divider content-position="left">通知方式</el-divider>
            <el-form-item label="浏览器通知">
              <el-switch v-model="settingsStore.settings.browserNotification" @change="handleBrowserNotificationChange" />
              <el-button v-if="settingsStore.settings.browserNotification" size="small" @click="testBrowserNotification" style="margin-left: 15px">
                测试通知
              </el-button>
            </el-form-item>
            <el-form-item label="邮件通知">
              <el-switch v-model="settingsStore.settings.emailNotification" />
              <span class="setting-hint">开启后将通过邮件接收重要通知</span>
            </el-form-item>
            <el-form-item label="声音提醒">
              <el-switch v-model="settingsStore.settings.soundNotification" />
            </el-form-item>
            <el-form-item label="通知音量" v-if="settingsStore.settings.soundNotification">
              <el-slider v-model="settingsStore.settings.notificationVolume" :min="0" :max="100" style="width: 240px" />
              <el-button size="small" @click="testSound" style="margin-left: 15px">测试</el-button>
            </el-form-item>
            <el-divider content-position="left">通知频率</el-divider>
            <el-form-item label="汇总方式">
              <el-radio-group v-model="settingsStore.settings.notificationFrequency">
                <el-radio label="realtime">实时通知</el-radio>
                <el-radio label="hourly">每小时汇总</el-radio>
                <el-radio label="daily">每日汇总</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="免打扰时段">
              <el-switch v-model="settingsStore.settings.doNotDisturb" />
            </el-form-item>
            <el-form-item label="免打扰时间" v-if="settingsStore.settings.doNotDisturb">
              <el-time-picker v-model="settingsStore.settings.dndStartTime" placeholder="开始时间" format="HH:mm" style="width: 120px" />
              <span style="margin: 0 10px">至</span>
              <el-time-picker v-model="settingsStore.settings.dndEndTime" placeholder="结束时间" format="HH:mm" style="width: 120px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 检测设置 -->
        <el-card v-show="activeTab === 'detection'">
          <template #header><span>检测设置</span></template>
          <el-form label-width="140px" class="settings-form">
            <el-divider content-position="left">检测参数</el-divider>
            <el-form-item label="检测灵敏度">
              <el-slider v-model="settingsStore.settings.detectionSensitivity" :min="1" :max="10" :marks="sensitivityMarks" style="width: 300px" />
            </el-form-item>
            <el-form-item label="置信度阈值">
              <el-slider v-model="settingsStore.settings.confidenceThreshold" :min="0" :max="100" :format-tooltip="(val) => val + '%'" style="width: 300px" />
              <span class="setting-hint">低于此置信度的检测结果将被忽略</span>
            </el-form-item>
            <el-form-item label="检测间隔">
              <el-input-number v-model="settingsStore.settings.detectionInterval" :min="1" :max="60" />
              <span class="setting-hint">秒，每隔多少秒进行一次检测</span>
            </el-form-item>
            <el-divider content-position="left">预警规则</el-divider>
            <el-form-item label="预警阈值">
              <el-input-number v-model="settingsStore.settings.alertThreshold" :min="1" :max="100" />
              <span class="setting-hint">连续异常行为次数达到此值时触发预警</span>
            </el-form-item>
            <el-form-item label="预警冷却时间">
              <el-input-number v-model="settingsStore.settings.alertCooldown" :min="0" :max="3600" :step="60" />
              <span class="setting-hint">秒，同一学生两次预警的最小间隔</span>
            </el-form-item>
            <el-divider content-position="left">显示选项</el-divider>
            <el-form-item label="显示检测框">
              <el-switch v-model="settingsStore.settings.showBoundingBox" />
            </el-form-item>
            <el-form-item label="显示置信度">
              <el-switch v-model="settingsStore.settings.showConfidence" />
            </el-form-item>
            <el-form-item label="显示行为标签">
              <el-switch v-model="settingsStore.settings.showBehaviorLabel" />
            </el-form-item>
            <el-form-item label="检测框颜色">
              <el-color-picker v-model="settingsStore.settings.boundingBoxColor" />
            </el-form-item>
            <el-divider content-position="left">数据记录</el-divider>
            <el-form-item label="自动保存记录">
              <el-switch v-model="settingsStore.settings.autoSaveRecords" />
            </el-form-item>
            <el-form-item label="保存原始帧">
              <el-switch v-model="settingsStore.settings.saveRawFrames" />
              <span class="setting-hint">保存检测时的原始图像（占用更多存储空间）</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
              <el-button @click="resetDetectionSettings">恢复默认</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 安全设置 -->
        <el-card v-show="activeTab === 'security'">
          <template #header><span>安全设置</span></template>
          <el-form label-width="140px" class="settings-form">
            <el-divider content-position="left">登录安全</el-divider>
            <el-form-item label="自动登出时间">
              <el-select v-model="settingsStore.settings.autoLogoutTime" style="width: 240px">
                <el-option label="从不" :value="0" />
                <el-option label="15分钟" :value="15" />
                <el-option label="30分钟" :value="30" />
                <el-option label="1小时" :value="60" />
                <el-option label="2小时" :value="120" />
              </el-select>
              <span class="setting-hint">无操作后自动登出</span>
            </el-form-item>
            <el-form-item label="记住登录状态">
              <el-switch v-model="settingsStore.settings.rememberLogin" />
            </el-form-item>
            <el-divider content-position="left">操作日志</el-divider>
            <el-form-item label="记录操作日志">
              <el-switch v-model="settingsStore.settings.enableOperationLog" />
            </el-form-item>
            <el-form-item label="日志保留天数">
              <el-input-number v-model="settingsStore.settings.logRetentionDays" :min="7" :max="365" />
              <span class="setting-hint">天</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 数据管理 -->
        <el-card v-show="activeTab === 'data'">
          <template #header><span>数据管理</span></template>
          <el-form label-width="140px" class="settings-form">
            <el-divider content-position="left">数据导出</el-divider>
            <el-form-item label="导出检测记录">
              <el-button @click="exportData('detection')" :loading="exporting.detection">
                <el-icon><Download /></el-icon> 导出 CSV
              </el-button>
              <span class="setting-hint">导出所有检测会话记录</span>
            </el-form-item>
            <el-form-item label="导出预警记录">
              <el-button @click="exportData('alert')" :loading="exporting.alert">
                <el-icon><Download /></el-icon> 导出 CSV
              </el-button>
            </el-form-item>
            <el-form-item label="导出统计报表">
              <el-button @click="exportData('statistics')" :loading="exporting.statistics">
                <el-icon><Download /></el-icon> 导出 CSV
              </el-button>
            </el-form-item>
            <el-divider content-position="left">数据清理</el-divider>
            <el-form-item label="清理历史数据">
              <el-select v-model="cleanupDays" style="width: 200px; margin-right: 15px">
                <el-option label="30天前的数据" :value="30" />
                <el-option label="60天前的数据" :value="60" />
                <el-option label="90天前的数据" :value="90" />
                <el-option label="180天前的数据" :value="180" />
              </el-select>
              <el-button type="danger" @click="cleanupData" :loading="cleaning">
                <el-icon><Delete /></el-icon> 清理数据
              </el-button>
            </el-form-item>
            <el-divider content-position="left">缓存管理</el-divider>
            <el-form-item label="清除本地缓存">
              <el-button @click="clearCache">
                <el-icon><Refresh /></el-icon> 清除缓存
              </el-button>
              <span class="setting-hint">清除浏览器中的本地存储数据</span>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 关于系统 -->
        <el-card v-show="activeTab === 'about'">
          <template #header><span>关于系统</span></template>
          <div class="about-content">
            <div class="system-logo">
              <span class="logo-text">SmartEdu</span>
            </div>
            <h2>智慧教育平台</h2>
            <p class="version">版本 {{ systemInfo.version }}</p>
            <p class="build-info">构建时间：{{ systemInfo.build_time }}</p>
            <el-divider />
            <el-descriptions :column="1" border>
              <el-descriptions-item label="系统名称">智慧教育课堂行为检测系统</el-descriptions-item>
              <el-descriptions-item label="当前版本">v{{ systemInfo.version }}</el-descriptions-item>
              <el-descriptions-item label="前端框架">Vue 3 + Element Plus</el-descriptions-item>
              <el-descriptions-item label="后端框架">Flask + MySQL</el-descriptions-item>
              <el-descriptions-item label="AI引擎">{{ systemInfo.ai_engine }}</el-descriptions-item>
              <el-descriptions-item label="检测会话数">{{ systemInfo.total_sessions }}</el-descriptions-item>
              <el-descriptions-item label="用户总数">{{ systemInfo.total_users }}</el-descriptions-item>
            </el-descriptions>
            <el-divider />
            <div class="info-section">
              <h4>主要功能</h4>
              <el-row :gutter="20">
                <el-col :span="12">
                  <div class="feature-item">
                    <el-icon><VideoCamera /></el-icon>
                    <div>
                      <h5>实时检测</h5>
                      <p>基于AI的课堂行为实时检测</p>
                    </div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="feature-item">
                    <el-icon><Bell /></el-icon>
                    <div>
                      <h5>精准预警</h5>
                      <p>异常行为智能预警提醒</p>
                    </div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="feature-item">
                    <el-icon><DataAnalysis /></el-icon>
                    <div>
                      <h5>学业画像</h5>
                      <p>多维度学生行为分析</p>
                    </div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="feature-item">
                    <el-icon><TrendCharts /></el-icon>
                    <div>
                      <h5>数据统计</h5>
                      <p>可视化数据报表展示</p>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
            <el-divider />
            <div class="info-section">
              <h4>技术支持</h4>
              <p>如有问题请联系：support@smartedu.com</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting, Bell, VideoCamera, InfoFilled, Lock, FolderOpened,
  Sunny, Moon, Monitor, Download, Delete, Refresh, DataAnalysis, TrendCharts
} from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores/settings'
import api from '@/api'

const settingsStore = useSettingsStore()
const activeTab = ref('general')
const cleanupDays = ref(30)
const saving = ref(false)
const cleaning = ref(false)
const exporting = reactive({
  detection: false,
  alert: false,
  statistics: false
})

const systemInfo = reactive({
  version: '1.0.0',
  build_time: '2024-01-04',
  total_sessions: 0,
  total_users: 0,
  ai_engine: 'YOLOv11'
})

const predefineColors = ['#2196F3', '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#9C27B0']

const sensitivityMarks = {
  1: '低',
  5: '中',
  10: '高'
}

const handleSelect = (index) => {
  activeTab.value = index
}

// 主题变化处理
const handleThemeChange = () => {
  settingsStore.applyTheme()
}

// 主题色变化处理
const handleColorChange = () => {
  settingsStore.applyTheme()
}

// 保存设置
const saveSettings = async () => {
  saving.value = true
  try {
    await settingsStore.saveSettings()
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

// 重置通用设置
const resetGeneralSettings = () => {
  settingsStore.resetGeneralSettings()
  ElMessage.success('已恢复默认设置')
}

// 重置检测设置
const resetDetectionSettings = () => {
  settingsStore.resetDetectionSettings()
  ElMessage.success('已恢复默认检测设置')
}

// 浏览器通知权限
const handleBrowserNotificationChange = (val) => {
  if (val && 'Notification' in window) {
    Notification.requestPermission().then(permission => {
      if (permission !== 'granted') {
        settingsStore.settings.browserNotification = false
        ElMessage.warning('请允许浏览器通知权限')
      }
    })
  }
}

// 测试浏览器通知
const testBrowserNotification = () => {
  if ('Notification' in window) {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        new Notification('智慧教育平台', {
          body: '这是一条测试通知',
          icon: '/favicon.ico'
        })
      } else {
        ElMessage.warning('请允许浏览器通知权限')
      }
    })
  } else {
    ElMessage.warning('您的浏览器不支持通知功能')
  }
}

// 测试声音
const testSound = () => {
  const audio = new Audio('/notification.mp3')
  audio.volume = settingsStore.settings.notificationVolume / 100
  audio.play().catch(() => {
    // 如果没有音频文件，使用系统提示音
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)
    
    oscillator.frequency.value = 800
    oscillator.type = 'sine'
    gainNode.gain.value = settingsStore.settings.notificationVolume / 100 * 0.3
    
    oscillator.start()
    setTimeout(() => {
      oscillator.stop()
      ctx.close()
    }, 200)
  })
}

// 导出数据
const exportData = async (type) => {
  exporting[type] = true
  try {
    const token = localStorage.getItem('token')
    const url = api.settings.exportData(type)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = `${url}?token=${token}`
    link.target = '_blank'
    
    // 使用 fetch 下载
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      link.href = downloadUrl
      
      // 从响应头获取文件名
      const contentDisposition = response.headers.get('content-disposition')
      let filename = `${type}_export.csv`
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/)
        if (match) {
          filename = match[1]
        }
      }
      link.download = filename
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
      
      ElMessage.success('导出成功')
    } else {
      throw new Error('导出失败')
    }
  } catch (error) {
    console.error('Export error:', error)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting[type] = false
  }
}

// 清理数据
const cleanupData = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要清理 ${cleanupDays.value} 天前的历史数据吗？此操作不可恢复！`,
      '警告',
      { confirmButtonText: '确定清理', cancelButtonText: '取消', type: 'warning' }
    )
    
    cleaning.value = true
    const res = await api.settings.cleanupData(cleanupDays.value)
    if (res.success) {
      ElMessage.success(res.message || '数据清理完成')
    } else {
      ElMessage.error(res.message || '清理失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '清理失败')
    }
  } finally {
    cleaning.value = false
  }
}

// 清除缓存
const clearCache = () => {
  const settingsBackup = localStorage.getItem('app_settings')
  const tokenBackup = localStorage.getItem('token')
  const userBackup = localStorage.getItem('user')
  
  localStorage.clear()
  sessionStorage.clear()
  
  // 恢复必要数据
  if (settingsBackup) localStorage.setItem('app_settings', settingsBackup)
  if (tokenBackup) localStorage.setItem('token', tokenBackup)
  if (userBackup) localStorage.setItem('user', userBackup)
  
  ElMessage.success('缓存已清除')
}

// 获取系统信息
const fetchSystemInfo = async () => {
  try {
    const res = await api.settings.getSystemInfo()
    if (res.success) {
      Object.assign(systemInfo, res.data)
    }
  } catch (error) {
    console.error('获取系统信息失败', error)
  }
}

onMounted(() => {
  settingsStore.loadSettings()
  fetchSystemInfo()
})
</script>


<style lang="scss" scoped>
.settings-page {
  .menu-card {
    position: sticky;
    top: 20px;
    
    :deep(.el-card__body) {
      padding: 0;
    }
    
    .el-menu {
      border-right: none;
      
      .el-menu-item {
        height: 50px;
        line-height: 50px;
        
        &.is-active {
          background: linear-gradient(90deg, rgba(33, 150, 243, 0.1) 0%, transparent 100%);
          color: var(--primary-color, #2196F3);
          border-right: 3px solid var(--primary-color, #2196F3);
        }
        
        .el-icon {
          margin-right: 8px;
        }
      }
    }
  }
  
  :deep(.el-card) {
    border-radius: 12px;
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
    
    .el-card__header {
      font-weight: 500;
      color: #1a1a1a;
      border-bottom: 1px solid #f0f2f5;
    }
  }
  
  .settings-form {
    max-width: 600px;
    
    :deep(.el-divider__text) {
      color: #909399;
      font-size: 13px;
    }
    
    :deep(.el-form-item__label) {
      color: #606266;
    }
  }
  
  .setting-hint {
    margin-left: 15px;
    color: #909399;
    font-size: 13px;
  }
  
  .about-content {
    text-align: center;
    padding: 20px;
    
    .system-logo {
      margin-bottom: 15px;
      
      .logo-text {
        font-size: 42px;
        font-weight: bold;
        color: var(--primary-color, #2196F3);
        letter-spacing: 2px;
      }
    }
    
    h2 {
      color: #1a1a1a;
      margin-bottom: 10px;
      font-size: 24px;
    }
    
    .version {
      color: #606266;
      font-size: 16px;
      margin-bottom: 5px;
    }
    
    .build-info {
      color: #909399;
      font-size: 13px;
    }
    
    :deep(.el-descriptions) {
      margin: 20px auto;
      max-width: 500px;
    }
    
    .info-section {
      text-align: left;
      margin: 20px 0;
      
      h4 {
        color: #1a1a1a;
        margin-bottom: 15px;
        font-size: 16px;
      }
      
      p {
        color: #606266;
        font-size: 14px;
        line-height: 1.8;
      }
      
      .feature-item {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        padding: 15px;
        background: #f8fafc;
        border-radius: 8px;
        margin-bottom: 15px;
        
        .el-icon {
          font-size: 28px;
          color: var(--primary-color, #2196F3);
          margin-top: 3px;
        }
        
        h5 {
          color: #1a1a1a;
          margin: 0 0 5px 0;
          font-size: 15px;
        }
        
        p {
          color: #909399;
          margin: 0;
          font-size: 13px;
        }
      }
    }
  }
}

// 深色主题支持
:root[data-theme="dark"] {
  .settings-page {
    .menu-card {
      :deep(.el-card) {
        background: #1e1e1e;
      }
      
      .el-menu {
        background: transparent;
        
        .el-menu-item {
          color: #e0e0e0;
          
          &:hover {
            background: rgba(255, 255, 255, 0.1);
          }
        }
      }
    }
    
    :deep(.el-card) {
      background: #1e1e1e;
      
      .el-card__header {
        color: #e0e0e0;
        border-bottom-color: #333;
      }
    }
    
    .about-content {
      h2 {
        color: #e0e0e0;
      }
      
      .info-section {
        h4, h5 {
          color: #e0e0e0;
        }
        
        .feature-item {
          background: #2a2a2a;
        }
      }
    }
  }
}
</style>
