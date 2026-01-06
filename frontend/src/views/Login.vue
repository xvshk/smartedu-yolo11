<template>
  <div class="login-page">
    <!-- 左上角品牌 -->
    <div class="brand-logo">SmartEdu</div>
    
    <!-- 主体内容 -->
    <div class="login-content">
      <!-- 左侧插图 -->
      <div class="login-illustration">
        <img src="@/assets/login-left-logo-cae9c116.png" alt="智慧教育" />
      </div>
      
      <!-- 右侧表单 -->
      <div class="login-form-section">
        <div class="login-header">
          <p class="welcome-text">欢迎使用</p>
          <h1 class="platform-title">智慧教育平台</h1>
        </div>
        
        <el-form 
          ref="loginFormRef"
          :model="loginForm" 
          :rules="loginRules"
          class="login-form"
        >
          <el-form-item prop="school">
            <el-input 
              v-model="loginForm.school"
              placeholder="请输入学校名称"
              size="large"
              :prefix-icon="School"
            />
          </el-form-item>
          
          <el-form-item prop="username">
            <el-input 
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-tips">
          <p>登录提示：</p>
          <p>1. 老师账户为职工号，学生的账户为学号</p>
          <p>2. 推荐使用 <el-icon><ChromeFilled /></el-icon> Chrome浏览器进行浏览</p>
        </div>
      </div>
    </div>
    
    <!-- 底部版权 -->
    <div class="login-footer">
      <p>Copyright © 2024 SmartEdu 智慧教育科技</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, School, ChromeFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  school: '河南师范大学',
  username: '',
  password: '',
  remember: true
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 4, message: '密码长度不能少于4位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const result = await userStore.login({
        username: loginForm.username,
        password: loginForm.password,
        school: loginForm.school
      })
      if (result.success) {
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } else {
        ElMessage.error(result.message || '登录失败')
      }
    } catch (error) {
      ElMessage.error(error.message || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>


<style lang="scss" scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(180deg, #e8f4fc 0%, #d4e8f5 100%);
  display: flex;
  flex-direction: column;
  position: relative;
}

.brand-logo {
  position: absolute;
  top: 30px;
  left: 40px;
  font-size: 28px;
  font-weight: bold;
  color: #2196F3;
  letter-spacing: 1px;
}

.login-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 80px;
  gap: 60px;
}

.login-illustration {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 600px;
  
  img {
    width: 100%;
    max-width: 550px;
    height: auto;
    object-fit: contain;
  }
}

.login-form-section {
  width: 420px;
  flex-shrink: 0;
}

.login-header {
  margin-bottom: 35px;
  
  .welcome-text {
    font-size: 16px;
    color: #666;
    margin: 0 0 8px 0;
  }
  
  .platform-title {
    font-size: 32px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0;
    letter-spacing: 1px;
  }
}

.login-form {
  :deep(.el-form-item) {
    margin-bottom: 20px;
  }
  
  :deep(.el-input__wrapper) {
    padding: 4px 15px;
    border-radius: 8px;
    box-shadow: none;
    border: 1px solid #dcdfe6;
    background: #fff;
    
    &:hover {
      border-color: #c0c4cc;
    }
    
    &.is-focus {
      border-color: #2196F3;
    }
  }
  
  :deep(.el-input__inner) {
    height: 38px;
    font-size: 14px;
  }
  
  :deep(.el-checkbox__label) {
    color: #606266;
    font-size: 14px;
  }
  
  :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
    background-color: #2196F3;
    border-color: #2196F3;
  }
  
  :deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
    color: #2196F3;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  background: #2196F3;
  border: none;
  letter-spacing: 8px;
  
  &:hover {
    background: #1976D2;
  }
  
  &:active {
    background: #1565C0;
  }
}

.login-tips {
  margin-top: 25px;
  font-size: 13px;
  color: #909399;
  
  p {
    margin: 6px 0;
    display: flex;
    align-items: center;
    gap: 4px;
    
    &:first-child {
      color: #606266;
      margin-bottom: 8px;
    }
    
    .el-icon {
      color: #4285f4;
      font-size: 14px;
    }
  }
}

.login-footer {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 12px;
  
  p {
    margin: 0;
  }
}

// 响应式
@media (max-width: 992px) {
  .login-content {
    flex-direction: column;
    padding: 40px 20px;
    gap: 40px;
  }
  
  .login-illustration {
    max-width: 400px;
  }
  
  .login-form-section {
    width: 100%;
    max-width: 400px;
  }
}

@media (max-width: 576px) {
  .brand-logo {
    top: 20px;
    left: 20px;
    font-size: 22px;
  }
  
  .login-illustration {
    display: none;
  }
  
  .login-header {
    .platform-title {
      font-size: 26px;
    }
  }
}
</style>
