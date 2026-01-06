import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/global.scss'
import { useThemeStore } from './stores/theme'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// 初始化主题系统
const themeStore = useThemeStore()
themeStore.initTheme()

// 添加主题色 meta 标签
const metaThemeColor = document.createElement('meta')
metaThemeColor.name = 'theme-color'
metaThemeColor.content = '#2196F3'
document.head.appendChild(metaThemeColor)

app.mount('#app')
