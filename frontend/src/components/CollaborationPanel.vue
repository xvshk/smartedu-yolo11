<template>
  <div class="collaboration-panel">
    <!-- 协作功能入口 -->
    <el-card class="collaboration-card">
      <template #header>
        <div class="card-header">
          <span>协作中心</span>
          <el-tag type="info" size="small">{{ userRole }}</el-tag>
        </div>
      </template>

      <!-- 教师功能 -->
      <template v-if="userRole === 'teacher'">
        <div class="collaboration-section">
          <h4>向管理员报告</h4>
          <el-button type="primary" @click="showReportDialog = true" :icon="Document">
            提交报告
          </el-button>
          <el-button type="warning" @click="showEmergencyDialog = true" :icon="Warning">
            紧急事件
          </el-button>
        </div>
        
        <el-divider />
        
        <div class="collaboration-section">
          <h4>学生求助请求</h4>
          <div v-if="helpRequests.length > 0" class="help-requests">
            <div 
              v-for="request in helpRequests" 
              :key="request.id"
              class="help-request-item"
            >
              <div class="request-info">
                <span class="student-name">{{ request.studentName }}</span>
                <span class="request-type">{{ request.type }}</span>
              </div>
              <div class="request-actions">
                <el-button size="small" type="primary" @click="handleHelpRequest(request)">
                  处理
                </el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无求助请求" :image-size="60" />
        </div>
      </template>

      <!-- 学生功能 -->
      <template v-else-if="userRole === 'student'">
        <div class="collaboration-section">
          <h4>向老师求助</h4>
          <el-button type="primary" @click="showHelpDialog = true" :icon="ChatDotRound">
            发起求助
          </el-button>
          <el-button type="info" @click="showFeedbackDialog = true" :icon="Edit">
            学习反馈
          </el-button>
        </div>
        
        <el-divider />
        
        <div class="collaboration-section">
          <h4>我的求助记录</h4>
          <div v-if="myHelpHistory.length > 0" class="help-history">
            <div 
              v-for="record in myHelpHistory" 
              :key="record.id"
              class="history-item"
            >
              <div class="history-info">
                <span class="history-type">{{ record.type }}</span>
                <el-tag :type="getStatusType(record.status)" size="small">
                  {{ record.status }}
                </el-tag>
              </div>
              <div class="history-time">{{ formatTime(record.createdAt) }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无求助记录" :image-size="60" />
        </div>
      </template>

      <!-- 管理员功能 -->
      <template v-else-if="userRole === 'admin'">
        <div class="collaboration-section">
          <h4>待处理报告</h4>
          <div v-if="pendingReports.length > 0" class="pending-reports">
            <div 
              v-for="report in pendingReports" 
              :key="report.id"
              class="report-item"
              :class="{ 'is-urgent': report.isUrgent }"
            >
              <div class="report-info">
                <span class="reporter-name">{{ report.teacherName }}</span>
                <span class="report-title">{{ report.title }}</span>
                <el-tag v-if="report.isUrgent" type="danger" size="small">紧急</el-tag>
              </div>
              <div class="report-actions">
                <el-button size="small" type="primary" @click="handleReport(report)">
                  查看
                </el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无待处理报告" :image-size="60" />
        </div>
        
        <el-divider />
        
        <div class="collaboration-section">
          <h4>系统公告</h4>
          <el-button type="primary" @click="showAnnouncementDialog = true" :icon="Notification">
            发布公告
          </el-button>
        </div>
      </template>
    </el-card>

    <!-- 教师报告对话框 -->
    <el-dialog v-model="showReportDialog" title="提交报告" width="500px">
      <el-form :model="reportForm" label-width="80px">
        <el-form-item label="报告类型">
          <el-select v-model="reportForm.type" placeholder="选择类型">
            <el-option label="学生行为报告" value="behavior" />
            <el-option label="教学建议" value="suggestion" />
            <el-option label="设备问题" value="equipment" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="reportForm.title" placeholder="请输入报告标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input 
            v-model="reportForm.content" 
            type="textarea" 
            :rows="4"
            placeholder="请详细描述情况"
          />
        </el-form-item>
        <el-form-item label="相关学生">
          <el-select v-model="reportForm.studentIds" multiple placeholder="选择相关学生">
            <el-option 
              v-for="student in studentList" 
              :key="student.id" 
              :label="student.name" 
              :value="student.id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReportDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReport" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>

    <!-- 紧急事件对话框 -->
    <el-dialog v-model="showEmergencyDialog" title="紧急事件报告" width="500px">
      <el-alert type="warning" :closable="false" show-icon class="mb-4">
        紧急事件将立即通知管理员，请确保情况属实
      </el-alert>
      <el-form :model="emergencyForm" label-width="80px">
        <el-form-item label="事件类型">
          <el-select v-model="emergencyForm.type" placeholder="选择类型">
            <el-option label="学生安全问题" value="safety" />
            <el-option label="设备故障" value="equipment" />
            <el-option label="突发状况" value="emergency" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="emergencyForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请简要描述紧急情况"
          />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="emergencyForm.location" placeholder="事件发生位置" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEmergencyDialog = false">取消</el-button>
        <el-button type="danger" @click="submitEmergency" :loading="submitting">立即报告</el-button>
      </template>
    </el-dialog>

    <!-- 学生求助对话框 -->
    <el-dialog v-model="showHelpDialog" title="向老师求助" width="450px">
      <el-form :model="helpForm" label-width="80px">
        <el-form-item label="求助类型">
          <el-select v-model="helpForm.type" placeholder="选择类型">
            <el-option label="学习困难" value="study" />
            <el-option label="课程疑问" value="question" />
            <el-option label="心理咨询" value="mental" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="helpForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请描述您需要帮助的内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showHelpDialog = false">取消</el-button>
        <el-button type="primary" @click="submitHelp" :loading="submitting">发送</el-button>
      </template>
    </el-dialog>

    <!-- 学习反馈对话框 -->
    <el-dialog v-model="showFeedbackDialog" title="学习反馈" width="450px">
      <el-form :model="feedbackForm" label-width="80px">
        <el-form-item label="今日状态">
          <el-rate v-model="feedbackForm.mood" :texts="['很差', '较差', '一般', '较好', '很好']" show-text />
        </el-form-item>
        <el-form-item label="学习感受">
          <el-input 
            v-model="feedbackForm.content" 
            type="textarea" 
            :rows="3"
            placeholder="分享您今天的学习感受"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeedbackDialog = false">取消</el-button>
        <el-button type="primary" @click="submitFeedback" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>

    <!-- 管理员公告对话框 -->
    <el-dialog v-model="showAnnouncementDialog" title="发布公告" width="500px">
      <el-form :model="announcementForm" label-width="80px">
        <el-form-item label="公告标题">
          <el-input v-model="announcementForm.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="公告内容">
          <el-input 
            v-model="announcementForm.content" 
            type="textarea" 
            :rows="4"
            placeholder="请输入公告内容"
          />
        </el-form-item>
        <el-form-item label="接收对象">
          <el-checkbox-group v-model="announcementForm.targets">
            <el-checkbox label="teacher">教师</el-checkbox>
            <el-checkbox label="student">学生</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="announcementForm.priority">
            <el-radio label="normal">普通</el-radio>
            <el-radio label="high">重要</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAnnouncementDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAnnouncement" :loading="submitting">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Document, Warning, ChatDotRound, Edit, Notification } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  userRole: {
    type: String,
    default: 'student',
    validator: (val) => ['student', 'teacher', 'admin'].includes(val)
  }
})

// 对话框状态
const showReportDialog = ref(false)
const showEmergencyDialog = ref(false)
const showHelpDialog = ref(false)
const showFeedbackDialog = ref(false)
const showAnnouncementDialog = ref(false)
const submitting = ref(false)

// 表单数据
const reportForm = ref({
  type: '',
  title: '',
  content: '',
  studentIds: []
})

const emergencyForm = ref({
  type: '',
  description: '',
  location: ''
})

const helpForm = ref({
  type: '',
  description: ''
})

const feedbackForm = ref({
  mood: 3,
  content: ''
})

const announcementForm = ref({
  title: '',
  content: '',
  targets: ['teacher', 'student'],
  priority: 'normal'
})

// 数据列表
const studentList = ref([
  { id: 1, name: '张三' },
  { id: 2, name: '李四' },
  { id: 3, name: '王五' }
])

const helpRequests = ref([
  { id: 1, studentName: '张三', type: '学习困难', createdAt: new Date() },
  { id: 2, studentName: '李四', type: '课程疑问', createdAt: new Date() }
])

const myHelpHistory = ref([
  { id: 1, type: '学习困难', status: '已处理', createdAt: new Date(Date.now() - 86400000) },
  { id: 2, type: '课程疑问', status: '处理中', createdAt: new Date() }
])

const pendingReports = ref([
  { id: 1, teacherName: '李老师', title: '学生行为异常报告', isUrgent: true },
  { id: 2, teacherName: '王老师', title: '教学设备问题', isUrgent: false }
])

// 方法
const getStatusType = (status) => {
  const types = {
    '已处理': 'success',
    '处理中': 'warning',
    '待处理': 'info'
  }
  return types[status] || 'info'
}

const formatTime = (date) => {
  return new Date(date).toLocaleDateString()
}

const submitReport = async () => {
  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('报告已提交')
    showReportDialog.value = false
    reportForm.value = { type: '', title: '', content: '', studentIds: [] }
  } finally {
    submitting.value = false
  }
}

const submitEmergency = async () => {
  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('紧急事件已报告，管理员将尽快处理')
    showEmergencyDialog.value = false
    emergencyForm.value = { type: '', description: '', location: '' }
  } finally {
    submitting.value = false
  }
}

const submitHelp = async () => {
  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('求助已发送，老师会尽快回复')
    showHelpDialog.value = false
    helpForm.value = { type: '', description: '' }
  } finally {
    submitting.value = false
  }
}

const submitFeedback = async () => {
  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('反馈已提交')
    showFeedbackDialog.value = false
    feedbackForm.value = { mood: 3, content: '' }
  } finally {
    submitting.value = false
  }
}

const submitAnnouncement = async () => {
  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('公告已发布')
    showAnnouncementDialog.value = false
    announcementForm.value = { title: '', content: '', targets: ['teacher', 'student'], priority: 'normal' }
  } finally {
    submitting.value = false
  }
}

const handleHelpRequest = (request) => {
  ElMessage.info(`处理 ${request.studentName} 的求助请求`)
}

const handleReport = (report) => {
  ElMessage.info(`查看 ${report.teacherName} 的报告`)
}
</script>

<style lang="scss" scoped>
.collaboration-panel {
  .collaboration-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
  
  .collaboration-section {
    h4 {
      margin: 0 0 var(--spacing-sm) 0;
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
    }
    
    .el-button + .el-button {
      margin-left: var(--spacing-sm);
    }
  }
  
  .help-requests,
  .help-history,
  .pending-reports {
    max-height: 200px;
    overflow-y: auto;
  }
  
  .help-request-item,
  .history-item,
  .report-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm);
    border-radius: var(--border-radius-base);
    background: var(--color-background-secondary);
    
    & + & {
      margin-top: var(--spacing-xs);
    }
    
    &.is-urgent {
      background: var(--color-danger-light);
      border-left: 3px solid var(--color-danger);
    }
  }
  
  .request-info,
  .history-info,
  .report-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }
  
  .student-name,
  .reporter-name {
    font-weight: var(--font-weight-medium);
  }
  
  .request-type,
  .history-type,
  .report-title {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
  
  .history-time {
    font-size: var(--font-size-xs);
    color: var(--color-text-placeholder);
  }
  
  .mb-4 {
    margin-bottom: var(--spacing-base);
  }
}
</style>
