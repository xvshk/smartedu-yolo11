<template>
  <div class="notification-page">
    <!-- 老师/管理员视图 -->
    <template v-if="isTeacherOrAdmin">
      <el-row :gutter="16">
        <!-- 统计卡片 -->
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon sent"><el-icon><Message /></el-icon></div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.sent?.total_sent || 0 }}</div>
                <div class="stat-label">已发送通知</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon read"><el-icon><View /></el-icon></div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.sent?.total_read || 0 }}</div>
                <div class="stat-label">已读通知</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon feedback"><el-icon><ChatDotRound /></el-icon></div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.feedbacks?.total_feedbacks || 0 }}</div>
                <div class="stat-label">收到反馈</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon pending"><el-icon><Clock /></el-icon></div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.feedbacks?.pending_count || 0 }}</div>
                <div class="stat-label">待审核</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 主要内容区 -->
      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="16">
          <!-- 发送通知卡片 -->
          <el-card class="main-card">
            <template #header>
              <div class="card-header">
                <span>📤 发送预警通知</span>
                <el-button type="primary" size="small" @click="showSendDialog = true">
                  <el-icon><Plus /></el-icon> 新建通知
                </el-button>
              </div>
            </template>
            
            <!-- 已发送列表 -->
            <el-table :data="sentList" v-loading="loading" stripe>
              <el-table-column prop="receiver_name" label="接收学生" width="120" />
              <el-table-column prop="title" label="通知标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="notification_type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getTypeTag(row.notification_type)" size="small">
                    {{ getTypeLabel(row.notification_type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="发送时间" width="160">
                <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.is_read ? 'success' : 'info'" size="small">
                    {{ row.is_read ? '已读' : '未读' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="反馈" width="100" align="center">
                <template #default="{ row }">
                  <el-badge 
                    :value="row.pending_feedback_count || 0" 
                    :hidden="!row.pending_feedback_count" 
                    class="feedback-badge"
                  >
                    <el-button size="small" link @click="viewNotificationDetail(row)">
                      {{ row.feedback_count || 0 }} 条
                    </el-button>
                  </el-badge>
                </template>
              </el-table-column>
            </el-table>
            
            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="sentPage"
                :page-size="10"
                :total="sentTotal"
                layout="total, prev, pager, next"
                @current-change="loadSentNotifications"
              />
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <!-- 待审核反馈 -->
          <el-card class="feedback-card">
            <template #header>
              <div class="card-header">
                <span>📝 待审核反馈</span>
                <el-badge :value="pendingCount" :hidden="!pendingCount" />
              </div>
            </template>
            
            <div v-if="pendingFeedbacks.length === 0" class="empty-state">
              <el-empty description="暂无待审核反馈" :image-size="80" />
            </div>
            
            <div v-else class="feedback-list">
              <div 
                v-for="fb in pendingFeedbacks" 
                :key="fb.feedback_id" 
                class="feedback-item"
                @click="showFeedbackDetail(fb)"
              >
                <div class="fb-header">
                  <span class="fb-student">{{ fb.student_name }}</span>
                  <el-tag :type="getFeedbackTypeTag(fb.feedback_type)" size="small">
                    {{ getFeedbackTypeLabel(fb.feedback_type) }}
                  </el-tag>
                </div>
                <div class="fb-title">{{ fb.notification_title }}</div>
                <div class="fb-content">{{ fb.content }}</div>
                <div class="fb-time">{{ formatTime(fb.created_at) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
    
    <!-- 学生视图 -->
    <template v-else>
      <el-row :gutter="16">
        <!-- 未读通知提示 -->
        <el-col :span="24" v-if="unreadCount > 0">
          <el-alert
            :title="`您有 ${unreadCount} 条未读通知`"
            type="warning"
            show-icon
            :closable="false"
            style="margin-bottom: 16px;"
          >
            <template #default>
              <el-button type="primary" size="small" @click="markAllAsRead">全部标为已读</el-button>
            </template>
          </el-alert>
        </el-col>
        
        <!-- 通知列表 -->
        <el-col :span="16">
          <el-card class="main-card">
            <template #header>
              <div class="card-header">
                <span>📬 我的通知</span>
                <el-radio-group v-model="readFilter" size="small" @change="loadReceivedNotifications">
                  <el-radio-button label="">全部</el-radio-button>
                  <el-radio-button label="false">未读</el-radio-button>
                  <el-radio-button label="true">已读</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            
            <div v-if="receivedList.length === 0" class="empty-state">
              <el-empty description="暂无通知" />
            </div>
            
            <div v-else class="notification-list">
              <div 
                v-for="notif in receivedList" 
                :key="notif.notification_id" 
                class="notification-item"
                :class="{ unread: !notif.is_read }"
                @click="viewNotificationDetail(notif)"
              >
                <div class="notif-header">
                  <el-tag :type="getTypeTag(notif.notification_type)" size="small">
                    {{ getTypeLabel(notif.notification_type) }}
                  </el-tag>
                  <el-tag v-if="notif.priority === 'urgent'" type="danger" size="small">紧急</el-tag>
                  <el-tag v-else-if="notif.priority === 'high'" type="warning" size="small">重要</el-tag>
                  <span class="notif-time">{{ formatTime(notif.created_at) }}</span>
                </div>
                <div class="notif-title">{{ notif.title }}</div>
                <div class="notif-sender">来自: {{ notif.sender_name }} ({{ getRoleLabel(notif.sender_role) }})</div>
                <div class="notif-footer">
                  <span v-if="notif.requires_feedback && notif.feedback_count === 0" class="need-feedback">
                    <el-icon><Warning /></el-icon> 需要反馈
                  </span>
                  <span v-else-if="notif.feedback_count > 0" class="has-feedback">
                    <el-icon><Check /></el-icon> 已反馈
                  </span>
                </div>
              </div>
            </div>
            
            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="receivedPage"
                :page-size="10"
                :total="receivedTotal"
                layout="total, prev, pager, next"
                @current-change="loadReceivedNotifications"
              />
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <!-- 我的反馈历史 -->
          <el-card class="feedback-card">
            <template #header>
              <span>📋 我的反馈记录</span>
            </template>
            
            <div v-if="myFeedbacks.length === 0" class="empty-state">
              <el-empty description="暂无反馈记录" :image-size="80" />
            </div>
            
            <div v-else class="feedback-list">
              <div v-for="fb in myFeedbacks" :key="fb.feedback_id" class="feedback-item">
                <div class="fb-header">
                  <el-tag :type="getFeedbackTypeTag(fb.feedback_type)" size="small">
                    {{ getFeedbackTypeLabel(fb.feedback_type) }}
                  </el-tag>
                  <el-tag :type="getStatusTag(fb.status)" size="small">
                    {{ getStatusLabel(fb.status) }}
                  </el-tag>
                </div>
                <div class="fb-title">{{ fb.notification_title }}</div>
                <div class="fb-content">{{ fb.content }}</div>
                <div v-if="fb.reviewer_comment" class="fb-comment">
                  <strong>审核意见:</strong> {{ fb.reviewer_comment }}
                </div>
                <div class="fb-time">{{ formatTime(fb.created_at) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
    
    <!-- 发送通知对话框 -->
    <el-dialog v-model="showSendDialog" title="发送预警通知" width="600px">
      <el-form :model="sendForm" label-width="100px">
        <el-form-item label="选择学生" required>
          <el-select v-model="sendForm.receiver_id" filterable placeholder="请选择学生" style="width: 100%;">
            <el-option 
              v-for="s in studentList" 
              :key="s.user_id" 
              :label="s.username" 
              :value="s.user_id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用模板">
          <el-select v-model="selectedTemplate" placeholder="选择模板快速填充" clearable @change="applyTemplate" style="width: 100%;">
            <el-option 
              v-for="t in templates" 
              :key="t.template_id" 
              :label="t.template_name" 
              :value="t.template_id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="通知类型" required>
          <el-radio-group v-model="sendForm.notification_type">
            <el-radio label="warning">预警</el-radio>
            <el-radio label="reminder">提醒</el-radio>
            <el-radio label="suggestion">建议</el-radio>
            <el-radio label="praise">表扬</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="sendForm.priority">
            <el-radio label="low">低</el-radio>
            <el-radio label="normal">普通</el-radio>
            <el-radio label="high">高</el-radio>
            <el-radio label="urgent">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="通知标题" required>
          <el-input v-model="sendForm.title" placeholder="请输入通知标题" />
        </el-form-item>
        <el-form-item label="通知内容" required>
          <el-input 
            v-model="sendForm.content" 
            type="textarea" 
            :rows="5" 
            placeholder="请输入通知内容"
          />
        </el-form-item>
        <el-form-item label="需要反馈">
          <el-switch v-model="sendForm.requires_feedback" />
          <span style="margin-left: 10px; color: #909399;">开启后学生需要对此通知进行反馈</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSendDialog = false">取消</el-button>
        <el-button type="primary" @click="sendNotification" :loading="sending">发送</el-button>
      </template>
    </el-dialog>
    
    <!-- 通知详情对话框 -->
    <el-dialog v-model="showDetailDialog" :title="detailNotification?.title" width="650px">
      <div v-if="detailNotification" class="detail-content">
        <div class="detail-meta">
          <el-tag :type="getTypeTag(detailNotification.notification_type)" size="small">
            {{ getTypeLabel(detailNotification.notification_type) }}
          </el-tag>
          <span class="meta-item">发送者: {{ detailNotification.sender_name }}</span>
          <span class="meta-item">时间: {{ formatTime(detailNotification.created_at) }}</span>
        </div>
        <div class="detail-body">{{ detailNotification.content }}</div>
        
        <!-- 反馈列表 -->
        <div v-if="detailNotification.feedbacks?.length > 0" class="detail-feedbacks">
          <h4>反馈记录</h4>
          <div v-for="fb in detailNotification.feedbacks" :key="fb.feedback_id" class="detail-feedback-item">
            <div class="dfb-header">
              <span class="dfb-student">{{ fb.student_name }}</span>
              <el-tag :type="getFeedbackTypeTag(fb.feedback_type)" size="small">
                {{ getFeedbackTypeLabel(fb.feedback_type) }}
              </el-tag>
              <el-tag :type="getStatusTag(fb.status)" size="small">
                {{ getStatusLabel(fb.status) }}
              </el-tag>
            </div>
            <div class="dfb-content">{{ fb.content }}</div>
            <div v-if="fb.reviewer_comment" class="dfb-comment">
              <strong>审核意见:</strong> {{ fb.reviewer_comment }}
            </div>
            <div class="dfb-time">{{ formatTime(fb.created_at) }}</div>
            
            <!-- 审核按钮（老师/管理员） -->
            <div v-if="isTeacherOrAdmin && fb.status === 'pending'" class="dfb-actions">
              <el-button size="small" type="success" @click="reviewFeedback(fb.feedback_id, 'accepted')">
                接受
              </el-button>
              <el-button size="small" type="warning" @click="reviewFeedback(fb.feedback_id, 'reviewed')">
                已阅
              </el-button>
              <el-button size="small" type="danger" @click="openRejectDialog(fb.feedback_id)">
                驳回
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 学生提交反馈 -->
        <div v-if="!isTeacherOrAdmin && detailNotification.requires_feedback && !hasFeedback" class="submit-feedback">
          <el-divider>提交反馈</el-divider>
          <el-form :model="feedbackForm" label-width="80px">
            <el-form-item label="反馈类型">
              <el-radio-group v-model="feedbackForm.feedback_type">
                <el-radio label="acknowledge">确认收到</el-radio>
                <el-radio label="explain">情况说明</el-radio>
                <el-radio label="appeal">申诉</el-radio>
                <el-radio label="commit">承诺改进</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="反馈内容">
              <el-input 
                v-model="feedbackForm.content" 
                type="textarea" 
                :rows="4" 
                placeholder="请输入您的反馈内容"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitFeedback" :loading="submitting">提交反馈</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-dialog>
    
    <!-- 驳回对话框 -->
    <el-dialog v-model="showRejectDialogVisible" title="驳回反馈" width="400px">
      <el-input 
        v-model="rejectComment" 
        type="textarea" 
        :rows="3" 
        placeholder="请输入驳回原因"
      />
      <template #footer>
        <el-button @click="showRejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/api'

const userStore = useUserStore()

// 计算属性
const isTeacherOrAdmin = computed(() => {
  const role = userStore.user?.role || ''
  return ['teacher', 'admin'].includes(role)
})

// 状态
const loading = ref(false)
const sending = ref(false)
const submitting = ref(false)

// 统计数据
const stats = ref({})
const unreadCount = ref(0)
const pendingCount = ref(0)

// 列表数据
const sentList = ref([])
const sentPage = ref(1)
const sentTotal = ref(0)

const receivedList = ref([])
const receivedPage = ref(1)
const receivedTotal = ref(0)
const readFilter = ref('')

const pendingFeedbacks = ref([])
const myFeedbacks = ref([])

// 学生列表和模板
const studentList = ref([])
const templates = ref([])
const selectedTemplate = ref(null)

// 对话框
const showSendDialog = ref(false)
const showDetailDialog = ref(false)
const showRejectDialogVisible = ref(false)
const detailNotification = ref(null)
const rejectFeedbackId = ref(null)
const rejectComment = ref('')

// 表单
const sendForm = reactive({
  receiver_id: null,
  title: '',
  content: '',
  notification_type: 'warning',
  priority: 'normal',
  requires_feedback: true
})

const feedbackForm = reactive({
  feedback_type: 'acknowledge',
  content: ''
})

// 计算是否已反馈
const hasFeedback = computed(() => {
  if (!detailNotification.value?.feedbacks) return false
  const userId = userStore.user?.user_id
  return detailNotification.value.feedbacks.some(f => f.student_id === userId)
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    if (isTeacherOrAdmin.value) {
      await Promise.all([
        loadStatistics(),
        loadSentNotifications(),
        loadPendingFeedbacks(),
        loadStudents(),
        loadTemplates()
      ])
    } else {
      await Promise.all([
        loadUnreadCount(),
        loadReceivedNotifications(),
        loadMyFeedbacks()
      ])
    }
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const res = await api.notification.getStatistics({ days: 30 })
    if (res.success) {
      stats.value = res.data
    }
  } catch (e) {
    console.error('Load statistics error:', e)
  }
}

const loadSentNotifications = async () => {
  try {
    const res = await api.notification.getSent({ page: sentPage.value, page_size: 10 })
    if (res.success) {
      sentList.value = res.data.items || []
      sentTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('Load sent notifications error:', e)
  }
}

const loadPendingFeedbacks = async () => {
  try {
    const res = await api.notification.getPendingFeedbacks({ page: 1, page_size: 10 })
    if (res.success) {
      pendingFeedbacks.value = res.data.items || []
      pendingCount.value = res.data.total || 0
    }
  } catch (e) {
    console.error('Load pending feedbacks error:', e)
  }
}

const loadStudents = async () => {
  try {
    const res = await api.user.list({ role: 'student', page_size: 100 })
    if (res.success) {
      studentList.value = res.data.users || []
    }
  } catch (e) {
    console.error('Load students error:', e)
  }
}

const loadTemplates = async () => {
  try {
    const res = await api.notification.getTemplates()
    if (res.success) {
      templates.value = res.data || []
    }
  } catch (e) {
    console.error('Load templates error:', e)
  }
}

const loadUnreadCount = async () => {
  try {
    const res = await api.notification.getUnreadCount()
    if (res.success) {
      unreadCount.value = res.data.count || 0
    }
  } catch (e) {
    console.error('Load unread count error:', e)
  }
}

const loadReceivedNotifications = async () => {
  try {
    const params = { page: receivedPage.value, page_size: 10 }
    if (readFilter.value !== '') {
      params.is_read = readFilter.value
    }
    const res = await api.notification.getReceived(params)
    if (res.success) {
      receivedList.value = res.data.items || []
      receivedTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('Load received notifications error:', e)
  }
}

const loadMyFeedbacks = async () => {
  try {
    const res = await api.notification.getMyFeedbacks({ page: 1, page_size: 10 })
    if (res.success) {
      myFeedbacks.value = res.data.items || []
    }
  } catch (e) {
    console.error('Load my feedbacks error:', e)
  }
}

// 应用模板
const applyTemplate = (templateId) => {
  if (!templateId) return
  const template = templates.value.find(t => t.template_id === templateId)
  if (template) {
    sendForm.title = template.title_template
    sendForm.content = template.content_template
    sendForm.notification_type = template.notification_type
  }
}

// 发送通知
const sendNotification = async () => {
  if (!sendForm.receiver_id || !sendForm.title || !sendForm.content) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  sending.value = true
  try {
    const res = await api.notification.send(sendForm)
    if (res.success) {
      ElMessage.success('通知发送成功')
      showSendDialog.value = false
      resetSendForm()
      loadSentNotifications()
      loadStatistics()
    } else {
      ElMessage.error(res.message || '发送失败')
    }
  } catch (e) {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

const resetSendForm = () => {
  sendForm.receiver_id = null
  sendForm.title = ''
  sendForm.content = ''
  sendForm.notification_type = 'warning'
  sendForm.priority = 'normal'
  sendForm.requires_feedback = true
  selectedTemplate.value = null
}

// 查看通知详情
const viewNotificationDetail = async (notif) => {
  try {
    const res = await api.notification.getDetail(notif.notification_id)
    if (res.success) {
      detailNotification.value = res.data
      showDetailDialog.value = true
      
      // 学生查看时标记为已读
      if (!isTeacherOrAdmin.value && !notif.is_read) {
        await api.notification.markRead(notif.notification_id)
        loadUnreadCount()
        loadReceivedNotifications()
      }
    }
  } catch (e) {
    ElMessage.error('获取详情失败')
  }
}

// 标记全部已读
const markAllAsRead = async () => {
  try {
    await api.notification.markAllRead()
    ElMessage.success('已全部标为已读')
    loadUnreadCount()
    loadReceivedNotifications()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 提交反馈
const submitFeedback = async () => {
  if (!feedbackForm.content) {
    ElMessage.warning('请输入反馈内容')
    return
  }
  
  submitting.value = true
  try {
    const res = await api.notification.submitFeedback(detailNotification.value.notification_id, feedbackForm)
    if (res.success) {
      ElMessage.success('反馈提交成功')
      showDetailDialog.value = false
      feedbackForm.feedback_type = 'acknowledge'
      feedbackForm.content = ''
      loadMyFeedbacks()
    } else {
      ElMessage.error(res.message || '提交失败')
    }
  } catch (e) {
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

// 查看反馈详情
const showFeedbackDetail = async (fb) => {
  try {
    const res = await api.notification.getDetail(fb.notification_id)
    if (res.success) {
      detailNotification.value = res.data
      showDetailDialog.value = true
    }
  } catch (e) {
    ElMessage.error('获取详情失败')
  }
}

// 审核反馈
const reviewFeedback = async (feedbackId, status, comment = '') => {
  try {
    const res = await api.notification.reviewFeedback(feedbackId, { status, comment })
    if (res.success) {
      ElMessage.success('审核完成')
      loadPendingFeedbacks()
      if (detailNotification.value) {
        viewNotificationDetail({ notification_id: detailNotification.value.notification_id })
      }
    }
  } catch (e) {
    ElMessage.error('审核失败')
  }
}

const openRejectDialog = (feedbackId) => {
  rejectFeedbackId.value = feedbackId
  rejectComment.value = ''
  showRejectDialogVisible.value = true
}

const confirmReject = async () => {
  if (!rejectComment.value) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  await reviewFeedback(rejectFeedbackId.value, 'rejected', rejectComment.value)
  showRejectDialogVisible.value = false
}

// 格式化函数
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getTypeTag = (type) => {
  const map = { warning: 'danger', reminder: 'warning', suggestion: 'primary', praise: 'success' }
  return map[type] || 'info'
}

const getTypeLabel = (type) => {
  const map = { warning: '预警', reminder: '提醒', suggestion: '建议', praise: '表扬' }
  return map[type] || type
}

const getFeedbackTypeTag = (type) => {
  const map = { acknowledge: 'info', explain: 'warning', appeal: 'danger', commit: 'success' }
  return map[type] || 'info'
}

const getFeedbackTypeLabel = (type) => {
  const map = { acknowledge: '确认', explain: '说明', appeal: '申诉', commit: '承诺改进' }
  return map[type] || type
}

const getStatusTag = (status) => {
  const map = { pending: 'warning', reviewed: 'info', accepted: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const map = { pending: '待审核', reviewed: '已阅', accepted: '已接受', rejected: '已驳回' }
  return map[status] || status
}

const getRoleLabel = (role) => {
  const map = { admin: '管理员', teacher: '老师', student: '学生' }
  return map[role] || role
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.notification-page {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stat-icon {
        width: 50px;
        height: 50px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: white;
        
        &.sent { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        &.read { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        &.feedback { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        &.pending { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
      }
      
      .stat-info {
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #303133;
        }
        .stat-label {
          font-size: 13px;
          color: #909399;
        }
      }
    }
  }
  
  .main-card {
    :deep(.el-card__header) {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }
    
    .pagination-wrapper {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }
  }
  
  .feedback-card {
    :deep(.el-card__header) {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      color: white;
    }
  }
  
  .empty-state {
    padding: 20px;
    text-align: center;
  }
  
  .notification-list {
    .notification-item {
      padding: 16px;
      border-bottom: 1px solid #eee;
      cursor: pointer;
      transition: background 0.2s;
      
      &:hover { background: #f5f7fa; }
      &.unread { background: #ecf5ff; border-left: 3px solid #409EFF; }
      &:last-child { border-bottom: none; }
      
      .notif-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        
        .notif-time {
          margin-left: auto;
          font-size: 12px;
          color: #909399;
        }
      }
      
      .notif-title {
        font-size: 15px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 4px;
      }
      
      .notif-sender {
        font-size: 13px;
        color: #606266;
      }
      
      .notif-footer {
        margin-top: 8px;
        
        .need-feedback {
          color: #E6A23C;
          font-size: 12px;
        }
        .has-feedback {
          color: #67C23A;
          font-size: 12px;
        }
      }
    }
  }
  
  .feedback-list {
    .feedback-item {
      padding: 12px;
      border-bottom: 1px solid #eee;
      cursor: pointer;
      
      &:hover { background: #f5f7fa; }
      &:last-child { border-bottom: none; }
      
      .fb-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        
        .fb-student {
          font-weight: 500;
          color: #303133;
        }
      }
      
      .fb-title {
        font-size: 13px;
        color: #606266;
        margin-bottom: 4px;
      }
      
      .fb-content {
        font-size: 13px;
        color: #909399;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .fb-comment {
        font-size: 12px;
        color: #409EFF;
        margin-top: 4px;
        padding: 4px 8px;
        background: #ecf5ff;
        border-radius: 4px;
      }
      
      .fb-time {
        font-size: 12px;
        color: #C0C4CC;
        margin-top: 6px;
      }
    }
  }
  
  .detail-content {
    .detail-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid #eee;
      
      .meta-item {
        font-size: 13px;
        color: #909399;
      }
    }
    
    .detail-body {
      font-size: 14px;
      line-height: 1.8;
      color: #606266;
      white-space: pre-wrap;
    }
    
    .detail-feedbacks {
      margin-top: 20px;
      
      h4 {
        margin: 0 0 12px;
        color: #303133;
      }
      
      .detail-feedback-item {
        padding: 12px;
        background: #f5f7fa;
        border-radius: 8px;
        margin-bottom: 12px;
        
        .dfb-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          
          .dfb-student {
            font-weight: 500;
          }
        }
        
        .dfb-content {
          font-size: 14px;
          color: #606266;
          margin-bottom: 8px;
        }
        
        .dfb-comment {
          font-size: 13px;
          color: #409EFF;
          padding: 8px;
          background: #ecf5ff;
          border-radius: 4px;
          margin-bottom: 8px;
        }
        
        .dfb-time {
          font-size: 12px;
          color: #909399;
        }
        
        .dfb-actions {
          margin-top: 12px;
          display: flex;
          gap: 8px;
        }
      }
    }
    
    .submit-feedback {
      margin-top: 20px;
    }
  }
}
</style>
