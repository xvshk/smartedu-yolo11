<template>
  <div class="student-portrait-view">
    <el-row :gutter="16" class="overview-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ portrait.student_name }}</div>
          <div class="stat-label">学生姓名</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value highlight">{{ formatPercent(portrait.attention_rate) }}</div>
          <div class="stat-label">个人注意力指数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ formatPercent(portrait.class_avg_attention_rate) }}</div>
          <div class="stat-label">班级平均</div>
        </el-card>
      </el-col>
      <el-col :span="6" v-if="showRank">
        <el-card shadow="hover" class="stat-card" :class="{ 'above-avg': portrait.peer_comparison?.above_average }">
          <div class="stat-value">第{{ portrait.peer_comparison?.student_rank }}名</div>
          <div class="stat-label">班级排名 (共{{ portrait.peer_comparison?.total_students }}人)</div>
        </el-card>
      </el-col>
      <el-col :span="6" v-else>
        <el-card shadow="hover" class="stat-card" :class="{ 'above-avg': portrait.peer_comparison?.above_average }">
          <div class="stat-value">{{ portrait.peer_comparison?.above_average ? '高于平均' : '低于平均' }}</div>
          <div class="stat-label">与班级对比</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>需要改进的方面</template>
          <div class="improvement-areas">
            <el-tag v-for="area in portrait.improvement_areas" :key="area" type="warning" style="margin: 4px">
              {{ area }}
            </el-tag>
            <span v-if="!portrait.improvement_areas?.length" class="no-issues">表现良好，继续保持！</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>改进建议</template>
          <div class="suggestions-list">
            <div v-for="(item, index) in suggestions" :key="index" class="suggestion-item" :class="'priority-' + item.priority">
              <div class="suggestion-header">
                <el-tag :type="item.priority === 0 ? 'success' : 'warning'" size="small">
                  {{ item.behavior_name_cn }}
                </el-tag>
                <span v-if="item.frequency > 0" class="frequency">出现 {{ item.frequency }} 次</span>
              </div>
              <p class="suggestion-text">{{ item.suggestion_text }}</p>
            </div>
            <el-empty v-if="suggestions.length === 0" description="暂无改进建议，表现优秀！" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
defineProps({
  portrait: { type: Object, required: true },
  suggestions: { type: Array, default: () => [] },
  showRank: { type: Boolean, default: true }
})

const formatPercent = (val) => val ? (val * 100).toFixed(1) + '%' : '0%'
</script>

<style lang="scss" scoped>
.student-portrait-view {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.overview-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2) !important;
}

:deep(.stat-card .el-card__body) {
  padding: 24px 16px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #409EFF;
  line-height: 1.2;
  margin-bottom: 8px;
}

.stat-label {
  color: #909399;
  font-size: 13px;
  font-weight: 500;
  margin-top: 8px;
}

.stat-card.warning .stat-value {
  color: #F56C6C;
}

.stat-card.warning::before {
  background: linear-gradient(135deg, #F56C6C 0%, #ff8a8a 100%);
}

.stat-card.above-avg .stat-value {
  color: #67C23A;
}

.stat-card.above-avg::before {
  background: linear-gradient(135deg, #67C23A 0%, #95d475 100%);
}

.highlight {
  color: #67C23A !important;
}

/* 卡片样式 */
:deep(.el-card) {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: hidden;
  height: 100%;
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  font-weight: 600;
  font-size: 15px;
  padding: 14px 20px;
  border-bottom: none !important;
}

:deep(.el-card__body) {
  padding: 20px;
}

.improvement-areas {
  min-height: 80px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
}

.improvement-areas :deep(.el-tag) {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  background: linear-gradient(135deg, #fdf6ec 0%, #fef0e6 100%);
  color: #e6a23c;
  box-shadow: 0 2px 8px rgba(230, 162, 60, 0.15);
  transition: all 0.3s ease;
}

.improvement-areas :deep(.el-tag:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.25);
}

.no-issues {
  color: #67C23A;
  font-size: 15px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e0 100%);
  border-radius: 10px;
  width: 100%;
  justify-content: center;
}

.no-issues::before {
  content: '✓';
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #67C23A;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
}

.suggestions-list {
  max-height: 320px;
  overflow-y: auto;
  padding-right: 4px;
}

.suggestions-list::-webkit-scrollbar {
  width: 6px;
}

.suggestions-list::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 3px;
}

.suggestions-list::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
}

.suggestion-item {
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f5f7fa 100%);
  border-left: 4px solid #909399;
  transition: all 0.3s ease;
}

.suggestion-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.suggestion-item.priority-0 {
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e0 100%);
  border-left-color: #67C23A;
}

.suggestion-item.priority-1 {
  background: linear-gradient(135deg, #fef0f0 0%, #fde8e8 100%);
  border-left-color: #F56C6C;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.suggestion-header :deep(.el-tag) {
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
}

.frequency {
  font-size: 12px;
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.suggestion-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #606266;
}

:deep(.el-empty) {
  padding: 40px 0;
}

:deep(.el-empty__description) {
  color: #67C23A;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 1200px) {
  :deep(.el-col) {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .stat-value {
    font-size: 22px;
  }
  
  .suggestion-item {
    padding: 12px;
  }
}
</style>
