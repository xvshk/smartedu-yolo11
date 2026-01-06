<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <!-- 左侧用户信息卡片 -->
      <el-col :span="8">
        <el-card class="user-card">
          <div class="user-avatar-section">
            <el-avatar :size="100" class="avatar">
              {{ userStore.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <h2 class="username">{{ userStore.username }}</h2>
            <el-tag :type="getRoleType(userStore.role)">{{ getRoleText(userStore.role) }}</el-tag>
          </div>
          <el-divider />
          <div class="user-info-list">
            <div class="info-item">
              <el-icon><Message /></el-icon>
              <span>{{ userInfo.email || '未设置邮箱' }}</span>
            </div>
            <div class="info-item">
              <el-icon><Calendar /></el-icon>
              <span>注册时间：{{ userInfo.created_at || '-' }}</span>
            </div>
            <div class="info-item">
              <el-icon><Clock /></el-icon>
              <span>上次登录：{{ userInfo.last_login || '-' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧编辑表单 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>个人信息</span>
          </template>
          <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="角色">
              <el-input :value="getRoleText(profileForm.role)" disabled />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProfile" :loading="saving">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card style="margin-top: 20px">
          <template #header>
            <span>修改密码</span>
          </template>
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password placeholder="请输入当前密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="changingPwd">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Message, Calendar, Clock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'

const userStore = useUserStore()
const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const saving = ref(false)
const changingPwd = ref(false)

const userInfo = reactive({
  email: '',
  created_at: '',
  last_login: ''
})

const profileForm = reactive({
  username: '',
  role: '',
  email: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const profileRules = {
  email: [{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const getRoleType = (role) => {
  const types = { admin: 'danger', teacher: 'warning', student: 'success', viewer: 'info' }
  return types[role] || 'info'
}

const getRoleText = (role) => {
  const texts = { admin: '管理员', teacher: '教师', student: '学生', viewer: '访客' }
  return texts[role] || role
}

const fetchUserInfo = async () => {
  try {
    const res = await api.auth.getCurrentUser()
    if (res.success) {
      Object.assign(userInfo, res.data)
      profileForm.username = res.data.username
      profileForm.role = res.data.role
      profileForm.email = res.data.email || ''
    }
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

const saveProfile = async () => {
  if (!profileFormRef.value) return
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await api.user.update(userStore.user.user_id, { email: profileForm.email })
      ElMessage.success('保存成功')
      fetchUserInfo()
    } catch (error) {
      ElMessage.error(error.message || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    changingPwd.value = true
    try {
      await api.user.changePassword({
        old_password: passwordForm.oldPassword,
        new_password: passwordForm.newPassword
      })
      ElMessage.success('密码修改成功')
      passwordFormRef.value.resetFields()
    } catch (error) {
      ElMessage.error(error.message || '密码修改失败')
    } finally {
      changingPwd.value = false
    }
  })
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style lang="scss" scoped>
.profile-page {
  .user-card {
    text-align: center;
    
    .user-avatar-section {
      padding: 20px 0;
      
      .avatar {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: #fff;
        font-size: 36px;
      }
      
      .username {
        margin: 15px 0 10px;
        font-size: 20px;
        color: #1a1a1a;
      }
    }
    
    .user-info-list {
      text-align: left;
      
      .info-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 0;
        color: #606266;
        font-size: 14px;
        
        .el-icon {
          color: #909399;
        }
      }
    }
  }
  
  :deep(.el-card) {
    border-radius: 12px;
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  }
}
</style>
