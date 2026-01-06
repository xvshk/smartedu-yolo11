<template>
  <div class="dashboard-container">
    <!-- 根据角色显示不同的仪表板 -->
    <AdminDashboard v-if="userRole === 'admin'" />
    <TeacherDashboard v-else-if="userRole === 'teacher'" />
    <StudentDashboard v-else-if="userRole === 'student'" />
    <DefaultDashboard v-else />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import AdminDashboard from '@/components/AdminDashboard.vue'
import TeacherDashboard from '@/components/TeacherDashboard.vue'
import StudentDashboard from '@/components/StudentDashboard.vue'
import DefaultDashboard from '@/components/DefaultDashboard.vue'

const userStore = useUserStore()

// 获取用户角色
const userRole = computed(() => {
  return userStore.role || localStorage.getItem('userRole') || ''
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  width: 100%;
  min-height: 100%;
}
</style>
