<template>
  <div class="analysis-detail-page">
    <!-- 页面头部 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button @click="goBack" class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回分析列表
        </el-button>
        <div class="header-info">
          <h1 class="page-title">分析詳細 - {{ item?.fileName }}</h1>
          <div class="header-meta">
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ formatDateTime(item?.uploadTime) }}
            </span>
            <span class="meta-item">
              <el-icon><User /></el-icon>
              {{ item?.uploaderName }}
            </span>
            <span class="meta-item">
              <el-icon><Document /></el-icon>
              {{ item?.fileType?.toUpperCase() }} 檔案
            </span>
          </div>
        </div>
      </div>
      
    </div>

    <!-- 分析结果卡片 -->
    <div class="content-grid">
      <!-- 反馈标签 -->
      <div class="labels-card">
        <div class="card-header">
          <h3>反饋分類</h3>
        </div>
        <div class="card-content">
          <div class="labels-container">
            <el-tag
              v-for="label in item?.feedbackLabels"
              :key="label"
              :type="getFeedbackTagType(label)"
              size="large"
              class="label-tag"
            >
              {{ label }}
            </el-tag>
            <div v-if="!item?.feedbackLabels?.length" class="no-labels">
              暫無反饋分類
            </div>
          </div>
        </div>
      </div>

      <!-- 情绪分析 -->
      <div class="sentiment-card">
        <div class="card-header">
          <h3>評價傾向</h3>
        </div>
        <div class="card-content">
          <div class="sentiment-display">
            <div class="sentiment-icon" :class="getSentimentClass(item?.sentiment)">
              <el-icon size="48">
                <component :is="getSentimentIcon(item?.sentiment)" />
              </el-icon>
            </div>
            <div class="sentiment-text">
              <div class="sentiment-label">{{ getSentimentLabel(item?.sentiment) }}</div>
              <div class="sentiment-desc">{{ getSentimentDescription(item?.sentiment) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 商品标签 -->
      <div class="labels-card">
        <div class="card-header">
          <h3>商品分類</h3>
        </div>
        <div class="card-content">
          <div class="labels-container">
            <el-tag
              v-for="label in item?.productLabels"
              :key="label"
              :type="getProductTagType(label)"
              size="large"
              class="label-tag"
            >
              {{ label }}
            </el-tag>
            <div v-if="!item?.productLabels?.length" class="no-labels">
              暫無商品分類
            </div>
          </div>
        </div>
      </div>

      <!-- 摘要 -->
      <div class="summary-card full-width">
        <div class="card-header">
          <h3>反饋原因</h3>
        </div>
        <div class="card-content">
          <div class="summary-text">
            {{ item?.summary || '暫無反饋原因' }}
          </div>
        </div>
      </div>

      <!-- 原始内容 -->
      <div class="content-card full-width">
        <div class="card-header">
          <h3>逐字稿</h3>
          <div class="content-actions">
            <el-button 
              v-if="!isEditing"
              size="small" 
              @click="startEditing"
            >
              <el-icon><Edit /></el-icon>
              編輯檔案
            </el-button>
            <div v-else class="edit-actions">
              <el-button 
                size="small" 
                @click="saveEdit"
                type="primary"
                :loading="saving"
              >
                <el-icon><Check /></el-icon>
                儲存
              </el-button>
              <el-button 
                size="small" 
                @click="cancelEdit"
              >
                <el-icon><Close /></el-icon>
                取消
              </el-button>
            </div>
          </div>
        </div>
        <div class="card-content">
          <div class="original-content">
            <pre v-if="!isEditing">{{ item?.originalContent || '暫無原始內容' }}</pre>
            <el-input 
              v-else
              v-model="editContent"
              type="textarea"
              :rows="15"
              resize="vertical"
              placeholder="請輸入內容..."
              class="edit-textarea"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" size="40"><Loading /></el-icon>
      <div>載入中...</div>
    </div>

    <!-- 错误状态 -->
    <div v-if="error" class="error-container">
      <el-icon size="40" color="#f56c6c"><Warning /></el-icon>
      <div class="error-message">{{ error }}</div>
      <el-button @click="fetchData">重試</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeft, 
  Clock, 
  User, 
  Document, 
  Edit,
  Loading,
  Warning,
  SuccessFilled,
  CircleCloseFilled,
  InfoFilled,
  Check,
  Close
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { analysisService } from '@/services/analysis.service'
import api from '@/services/api'
import type { AnalysisItem } from '@/types/analysis'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(false)
const error = ref('')
const item = ref<AnalysisItem | null>(null)
const isEditing = ref(false)
const editContent = ref('')
const saving = ref(false)

// Parse feedback categories (handle multiple categories separated by various delimiters)
const parseFeedbackCategories = (feedbackCategory: string | null | undefined): string[] => {
  if (!feedbackCategory) return []
  
  // Split by common delimiters: space, comma, Chinese comma, slash, semicolon
  // Handle the case where categories are like "物流/配送 口味研發"
  const categories = feedbackCategory
    .split(/[\s,，\/;；]+/)
    .map(cat => cat.trim())
    .filter(cat => cat.length > 0 && cat !== '無' && cat !== 'null')
  
  return categories.length > 0 ? categories : []
}

// 获取数据
const fetchData = async () => {
  const id = route.params.id as string
  if (!id) {
    error.value = '無效的分析 ID'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Get analysis data from API - using the correct endpoint for analysis detail
    const response = await api.get(`/analysis/result/${id}`)
    const data = response.data
    
    // Map API response to expected format
    item.value = {
      id: data.file_id, // Use file_id for editing, not analysis id
      analysisId: data.id, // Keep analysis id separately
      fileName: data.filename || 'Unknown',
      fileType: 'wav', // Default file type, could be parsed from filename
      productLabels: data.product_names || [],
      feedbackLabels: parseFeedbackCategories(data.feedback_category),
      sentiment: data.sentiment?.toLowerCase() as 'positive' | 'negative' | 'neutral' || 'neutral',
      summary: data.feedback_summary || '暫無摘要',
      uploader: data.uploader_name || 'Unknown',
      uploaderName: data.uploader_name || 'Unknown',
      uploadTime: data.upload_time || data.created_at,
      confidence: 0.89, // API doesn't return confidence yet, using placeholder
      originalContent: data.transcript || '暫無原始內容'
    }
  } catch (err: any) {
    console.error('Failed to fetch analysis detail:', err)
    error.value = err.message || '獲取分析詳情失敗'
  } finally {
    loading.value = false
  }
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 開始編輯
const startEditing = () => {
  if (item.value?.originalContent) {
    editContent.value = item.value.originalContent
    isEditing.value = true
  }
}

// 取消編輯
const cancelEdit = () => {
  isEditing.value = false
  editContent.value = ''
}

// 儲存編輯
const saveEdit = async () => {
  if (!item.value) return
  
  saving.value = true
  try {
    // 調用API更新transcript
    await api.put(`/analysis/${item.value.id}/transcript`, { 
      transcript: editContent.value 
    })
    
    // 更新本地狀態
    if (item.value) {
      item.value.originalContent = editContent.value
    }
    
    isEditing.value = false
    ElMessage.success('儲存成功')
  } catch (err: any) {
    console.error('Failed to save transcript:', err)
    ElMessage.error('儲存失敗: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}



// 格式化日期时间
const formatDateTime = (dateTime?: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-TW')
}

// 获取情绪样式类
const getSentimentClass = (sentiment?: string) => {
  const classes = {
    positive: 'sentiment-positive',
    negative: 'sentiment-negative',
    neutral: 'sentiment-neutral'
  }
  return classes[sentiment as keyof typeof classes] || 'sentiment-neutral'
}

// 获取情绪图标
const getSentimentIcon = (sentiment?: string) => {
  const icons = {
    positive: SuccessFilled,
    negative: CircleCloseFilled,
    neutral: InfoFilled
  }
  return icons[sentiment as keyof typeof icons] || InfoFilled
}

// 获取情绪标签
const getSentimentLabel = (sentiment?: string) => {
  const labels = {
    positive: '正面',
    negative: '負面',
    neutral: '中立'
  }
  return labels[sentiment as keyof typeof labels] || '未知'
}

// 获取情绪描述
const getSentimentDescription = (sentiment?: string) => {
  const descriptions = {
    positive: '此反饋表達了積極的情緒和滿意度',
    negative: '此反饋表達了消極的情緒和不滿',
    neutral: '此反饋表達了中性的態度'
  }
  return descriptions[sentiment as keyof typeof descriptions] || ''
}

// 获取置信度颜色
const getConfidenceColor = (confidence?: number) => {
  if (!confidence) return '#e5e7eb'
  if (confidence >= 0.8) return '#22c55e'
  if (confidence >= 0.6) return '#eab308'
  return '#ef4444'
}

// 获取商品标签类型
const getProductTagType = (label: string) => {
  const types: { [key: string]: any } = {
    '包子': '',
    '饅頭': 'danger',
    '水餃': 'success',
    '蒸餃': 'warning'
  }
  return types[label] || 'info'
}

// 获取反馈标签类型
const getFeedbackTagType = (label: string) => {
  const types: { [key: string]: any } = {
    '物流/配送': '',
    '口味研發': 'success',
    '活動價惠': 'warning',
    '包裝設計': 'info',
    '客服態度': 'danger'
  }
  return types[label] || ''
}

// 页面挂载时获取数据
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.analysis-detail-page {
  padding: 24px;
  background: #f3f4f6;
  min-height: 100vh;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-button {
  align-self: flex-start;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.header-meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.info-card,
.sentiment-card,
.labels-card,
.summary-card,
.content-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.content-card.full-width,
.summary-card.full-width {
  grid-column: 1 / -1;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.content-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.edit-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.edit-textarea {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
}

.edit-textarea :deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
}

.card-content {
  padding: 24px;
}

.info-grid {
  display: grid;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item span {
  font-size: 14px;
  color: #1f2937;
}

.sentiment-display {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sentiment-icon {
  flex-shrink: 0;
}

.sentiment-icon.sentiment-positive {
  color: #3333FF;
}

.sentiment-icon.sentiment-negative {
  color: #FF7676;
}

.sentiment-icon.sentiment-neutral {
  color: #FFC18F;
}

.sentiment-text {
  flex: 1;
}

.sentiment-label {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.sentiment-desc {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.labels-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.label-tag {
  margin: 0;
}

.no-labels {
  color: #9ca3af;
  font-style: italic;
  font-size: 14px;
}

.summary-text {
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px 16px;
  min-height: 60px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.original-content {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.original-content pre {
  margin: 0;
  font-family: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.error-message {
  font-size: 16px;
  color: #6b7280;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .analysis-detail-page {
    padding: 16px;
  }
  
  .detail-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
    padding: 16px;
  }
  
  .header-actions {
    justify-content: flex-end;
  }
  
  .content-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .header-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .sentiment-display {
    flex-direction: column;
    text-align: center;
  }
}
</style>