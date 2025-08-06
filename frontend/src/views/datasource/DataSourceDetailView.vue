<template>
  <div class="datasource-detail-page">
    <!-- 页面头部 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button @click="goBack" class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回資料列表
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
              {{ item?.fileFormat?.toUpperCase() }} 檔案
            </span>
          </div>
        </div>
      </div>
      
    </div>

    <!-- 分析结果卡片 -->
    <div class="content-grid">
      <!-- 反饋分類 -->
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

      <!-- 情緒分析 -->
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

      <!-- 商品分類 -->
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
            {{ item?.feedbackReason || '暫無反饋原因' }}
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
              :disabled="item?.rawStatus !== 'completed'"
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
            <div v-if="!isEditing">
              <div 
                v-for="(line, index) in item?.transcript" 
                :key="index"
                class="transcript-line"
              >
                <div class="speaker-label">{{ line.speaker }}：</div>
                <div class="speaker-text">{{ line.text }}</div>
              </div>
              <div v-if="!item?.transcript?.length" class="no-content">
                暫無逐字稿內容
              </div>
            </div>
            <el-input 
              v-else
              v-model="editContent"
              type="textarea"
              :rows="15"
              resize="vertical"
              placeholder="請輸入逐字稿內容..."
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
import { dataSourceService } from '@/services/datasource.service'
import { useDataSourceStore } from '@/stores/datasource'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()

// Store
const dataSourceStore = useDataSourceStore()

// 状态
const loading = ref(false)
const error = ref('')
const item = ref<any>(null)
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
    error.value = '無效的檔案 ID'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // First, try to find the item in the store
    let storeItem = dataSourceStore.items.find(item => item.id === id)
    
    // If not found in store, load the data from API
    if (!storeItem) {
      await dataSourceStore.fetchDataSourceList()
      storeItem = dataSourceStore.items.find(item => item.id === id)
    }
    
    // Get detailed analysis result from API
    const analysisResult = await dataSourceService.getAnalysisResult(id)
    
    // Map data using store item for consistency with DataSourceView
    item.value = {
      id: id,
      fileName: storeItem?.original_filename || storeItem?.fileName || analysisResult.original_filename || 'Unknown File',
      fileFormat: storeItem?.file_format || analysisResult.file_format || 'unknown',
      productLabels: analysisResult.product_names || [],
      feedbackLabels: parseFeedbackCategories(analysisResult.feedback_category),
      sentiment: analysisResult.sentiment?.toLowerCase() as 'positive' | 'negative' | 'neutral' || 'neutral',
      feedbackReason: analysisResult.feedback_summary || '暫無摘要',
      uploader: storeItem?.uploader_name || analysisResult.uploader_name || 'Unknown',
      uploaderName: storeItem?.uploader_name || analysisResult.uploader_name || 'Unknown',
      uploadTime: storeItem?.created_at || storeItem?.uploadTime || analysisResult.created_at,
      rawStatus: storeItem?.status || analysisResult.status || 'completed',
      transcript: analysisResult.transcript ? 
        analysisResult.transcript.split('\n').filter((line: string) => line.trim()).map((line: string, index: number) => ({
          speaker: index % 2 === 0 ? '客戶' : '客服',
          text: line.trim()
        })) : []
    }
  } catch (err: any) {
    console.error('Failed to fetch data source detail:', err)
    error.value = err.message || '獲取檔案詳情失敗'
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
  if (item.value?.transcript?.length) {
    // 將逐字稿轉換為純文字格式
    editContent.value = item.value.transcript
      .map((line: any) => `${line.speaker}：${line.text}`)
      .join('\n')
    isEditing.value = true
  } else {
    editContent.value = ''
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
    
    // 更新本地狀態 - 將純文字轉換回逐字稿格式
    if (item.value) {
      const lines = editContent.value.split('\n').filter(line => line.trim())
      item.value.transcript = lines.map((line, index) => {
        const colonIndex = line.indexOf('：')
        if (colonIndex > -1) {
          return {
            speaker: line.substring(0, colonIndex),
            text: line.substring(colonIndex + 1)
          }
        } else {
          return {
            speaker: index % 2 === 0 ? '客戶' : '客服',
            text: line
          }
        }
      })
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
  try {
    const date = new Date(dateTime)
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return dateTime
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'pending':
      return '待分析'
    case 'analyzing':
      return '分析中'
    case 'completed':
      return '分析完成'
    case 'failed':
      return '分析失敗'
    default:
      return '未知狀態'
  }
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
    neutral: '中性'
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
.datasource-detail-page {
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

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
  width: fit-content;
}

.status-badge.status-pending {
  background-color: #fef3c7;
  color: #92400e;
}

.status-badge.status-analyzing {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-badge.status-completed {
  background-color: #d1fae5;
  color: #065f46;
}

.status-badge.status-failed {
  background-color: #fee2e2;
  color: #991b1b;
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

.transcript-line {
  margin-bottom: 1rem;
}

.transcript-line:last-child {
  margin-bottom: 0;
}

.speaker-label {
  font-weight: 500;
  font-size: 0.875rem;
  color: #374151;
  margin-bottom: 0.25rem;
}

.speaker-text {
  font-size: 0.875rem;
  color: #1f2937;
}

.no-content {
  color: #9ca3af;
  font-style: italic;
  font-size: 14px;
  text-align: center;
  padding: 20px;
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
  .datasource-detail-page {
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