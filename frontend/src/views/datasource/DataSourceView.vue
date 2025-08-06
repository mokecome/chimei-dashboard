<template>
  <div class="datasource-page">
    <!-- Page Header -->
    <header class="page-header">
      <div class="header-content">
        <div>
          <div class="breadcrumb">
            <span>Dashboard</span>
            <el-icon><ArrowRight /></el-icon>
            <span>匯入資料</span>
            <el-icon><ArrowRight /></el-icon>
            <span>AI 分析</span>
          </div>
          <h1 class="page-title">分析上傳檔案</h1>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="openUploadModal">
            <el-icon><Upload /></el-icon>
            匯入
          </el-button>
        </div>
      </div>
    </header>

    <!-- Content -->
    <div class="content-section">
      <!-- Toolbar -->
      <div class="toolbar" v-if="selectedItems.length > 0">
        <div class="selected-info">
          已選擇 {{ selectedItems.length }} 項
        </div>
        <div class="toolbar-actions">
          <el-button 
            type="danger" 
            :disabled="selectedItems.length === 0"
            @click="handleBatchDelete"
          >
            <el-icon><Delete /></el-icon>
            刪除
          </el-button>
        </div>
      </div>
      
      <!-- Data Table -->
      <div class="table-container">
        <div class="table-wrapper">
          <table class="data-table">
            <thead class="table-header">
              <tr>
                <th class="table-th checkbox-column">
                  <el-checkbox 
                    v-model="selectAll" 
                    :indeterminate="isIndeterminate"
                    @change="handleSelectAll"
                  >
                    全選
                  </el-checkbox>
                </th>
                <th class="table-th">檔案名稱</th>
                <th class="table-th">上傳時間</th>
                <th class="table-th">狀態</th>
                <th class="table-th">上傳者</th>
                <th class="table-th">檔案格式</th>
                <th class="table-th">詳細內容</th>
              </tr>
            </thead>
            <tbody class="table-body">
              <tr 
                v-for="row in tableData" 
                :key="row.id"
                class="table-row"
                :class="{ 'selected': selectedItems.includes(row.id) }"
              >
                <td class="table-td checkbox-column">
                  <el-checkbox 
                    :model-value="selectedItems.includes(row.id)"
                    @change="(checked) => handleItemSelect(row.id, checked)"
                    @click.stop
                  />
                </td>
                <td class="table-td" @click="handleRowClick(row)">
                  <div class="file-name">{{ row.fileName }}</div>
                </td>
                <td class="table-td" @click="handleRowClick(row)">
                  <div class="upload-time">{{ row.uploadTime }}</div>
                </td>
                <td class="table-td" @click="handleRowClick(row)">
                  <div class="status-operation-content">
                    <!-- 待分析狀態 - 自動開始分析 -->
                    <div v-if="row.rawStatus === 'pending'" class="status-content pending">
                      <span>待分析</span>
                      <el-icon class="pending-icon">
                        <Loading />
                      </el-icon>
                    </div>
                    
                    <!-- 分析中狀態 -->
                    <div v-else-if="row.rawStatus === 'analyzing'" class="status-content analyzing">
                      <span>分析中</span>
                      <el-icon class="analyzing-icon">
                        <Loading />
                      </el-icon>
                    </div>
                    
                    <!-- 分析完成狀態 -->
                    <div v-else-if="row.rawStatus === 'completed'" class="status-content completed">
                      <span>分析完成</span>
                      <el-icon class="completed-icon">
                        <Check />
                      </el-icon>
                    </div>
                    
                    <!-- 分析失敗狀態 - 顯示重新分析按鈕 -->
                    <div v-else-if="row.rawStatus === 'failed'" class="status-operation-failed">
                      <button 
                        class="retry-button"
                        @click.stop="retryAnalysis(row)"
                        :disabled="row.isRetrying"
                      >
                        <el-icon v-if="row.isRetrying" class="analyzing-icon"><Loading /></el-icon>
                        {{ row.isRetrying ? '重試中...' : '重新分析' }}
                      </button>
                    </div>
                    
                    <!-- 文字檔案或其他狀態 -->
                    <div v-else class="status-content">
                      <span>{{ row.status }}</span>
                    </div>
                  </div>
                </td>
                <td class="table-td" @click="handleRowClick(row)">
                  <div>{{ row.uploader }}</div>
                </td>
                <td class="table-td" @click="handleRowClick(row)">
                  <div>{{ row.fileFormat }}</div>
                </td>
                <td class="table-td">
                  <button 
                    :class="row.isViewable ? 'view-button' : 'view-button-disabled'"
                    :disabled="!row.isViewable"
                    @click.stop="viewDetails(row)"
                  >
                    檢視
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- Pagination -->
        <div class="pagination-container" v-if="tableData.length > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalItems"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handleCurrentPageChange"
          />
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <el-dialog
      v-model="uploadModalVisible"
      title="上傳分析檔案"
      width="600px"
      :before-close="closeUploadModal"
      class="upload-modal"
    >
      <div class="upload-content">
        <div 
          class="upload-area" 
          v-if="selectedFiles.length === 0"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragenter="handleDragEnter"
          @dragleave="handleDragLeave"
          :class="{ 'drag-over': isDragOver }"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <p class="upload-text">拖拽檔案到此處或點擊選擇</p>
          <p class="upload-hint">支援 WAV、MP3、TXT 格式</p>
          <input 
            type="file" 
            ref="fileInput"
            class="file-input" 
            accept=".wav,.mp3,.txt"
            multiple
            @change="handleFileSelect"
          />
          <el-button class="select-button" @click="triggerFileSelect">
            選擇檔案
          </el-button>
        </div>
        
        <!-- 已選擇檔案列表 -->
        <div v-else class="selected-files-area">
          <div class="files-header">
            <h4>已選擇檔案 ({{ selectedFiles.length }})</h4>
            <el-button size="small" @click="triggerFileSelect">
              <el-icon><Plus /></el-icon>
              新增檔案
            </el-button>
          </div>
          
          <div class="files-list">
            <div 
              v-for="(file, index) in selectedFiles" 
              :key="file.name"
              class="file-item"
            >
              <div class="file-info">
                <div class="file-icon">
                  <el-icon>
                    <Document v-if="file.name.endsWith('.txt')" />
                    <Microphone v-else />
                  </el-icon>
                </div>
                <div class="file-details">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-size">{{ formatFileSize(file.size) }}</div>
                </div>
              </div>
              
              <div class="file-actions">
                <!-- 簡化為只顯示移除按鈕 -->
              </div>
              
              <el-button 
                type="danger" 
                size="small" 
                :icon="Delete"
                circle
                @click="removeFile(index)"
              />
            </div>
          </div>
          
          <!-- 隱藏的 file input 用於新增檔案 -->
          <input 
            type="file" 
            ref="fileInput"
            class="file-input" 
            accept=".wav,.mp3,.txt"
            multiple
            @change="handleFileSelect"
          />
        </div>
      </div>
      
      <template #footer>
        <div class="modal-footer">
          <el-button @click="closeUploadModal">取消</el-button>
          <el-button 
            type="primary" 
            :disabled="selectedFiles.length === 0"
            @click="handleUpload"
          >
            <el-icon><Upload /></el-icon>
            開始上傳 ({{ selectedFiles.length }})
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowRight,
  Upload,
  UploadFilled,
  Loading,
  Check,
  Download,
  ArrowLeft,
  Clock,
  Plus,
  Document,
  Microphone,
  Delete,
  Close
} from '@element-plus/icons-vue'
import { useDataSourceStore } from '@/stores/datasource'
import { dataSourceService } from '@/services/datasource.service'
import { useRouter } from 'vue-router'

// Store
const dataSourceStore = useDataSourceStore()

// Router
const router = useRouter()

// State
const uploadModalVisible = ref(false)
const selectedFiles = ref<File[]>([])
const fileInput = ref<HTMLInputElement>()
const isDragOver = ref(false)

// Pagination state
const currentPage = ref(1)
const pageSize = ref(20)
const totalItems = computed(() => dataSourceStore.pagination.total)

// Selection state
const selectedItems = ref<string[]>([])
const selectAll = ref(false)
const isIndeterminate = computed(() => {
  const selectedCount = selectedItems.value.length
  const totalCount = tableData.value.length
  return selectedCount > 0 && selectedCount < totalCount
})

// Convert API data to display format
const tableData = computed(() => {
  return dataSourceStore.items.map(item => {
    
    const statusText = getStatusText(item.status)
    const isAnalyzing = item.status === 'analyzing'
    const isCompleted = item.status === 'completed'
    const isFailed = item.status === 'failed'
    const isPending = item.status === 'pending'
    const isViewable = isCompleted
    
    return {
      id: item.id,
      fileName: item.original_filename || item.fileName,
      uploadTime: formatDateTime(item.created_at || item.uploadTime),
      status: statusText,
      rawStatus: item.status, // 保留原始狀態
      isAnalyzing,
      isCompleted,
      isFailed,
      isPending,
      isViewable,
      isRetrying: false, // 用於控制重試按鈕狀態
      feedbackCategory: item.analysis_result?.feedback_category || null,
      productCategory: item.analysis_result?.product_names?.join('、') || null,
      sentiment: item.analysis_result?.sentiment || null,
      uploader: item.uploader_name || item.uploaderName || '未知',
      fileFormat: '.' + (item.file_format || item.fileType),
      detailTimestamp: formatDateTime(item.updated_at),
      productName: item.analysis_result?.product_names?.join('、') || null,
      feedbackReason: item.analysis_result?.feedback_summary || null,
      transcript: item.analysis_result?.transcript || []
    }
  })
})

// Helper functions
const getStatusText = (status: string) => {
  // Map backend status to display text
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
      return '待分析'
  }
}

const formatDateTime = (dateStr: string) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return dateStr
  }
}

const formatSentiment = (sentiment: string) => {
  const sentimentMap: Record<string, string> = {
    'positive': '正面',
    'negative': '負面', 
    'neutral': '中性',
    'POSITIVE': '正面',
    'NEGATIVE': '負面',
    'NEUTRAL': '中性'
  }
  
  if (!sentiment) {
    return 'N/A'
  }
  
  return sentimentMap[sentiment] || sentiment
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
}

// Modal handlers
const openUploadModal = () => {
  uploadModalVisible.value = true
}

const closeUploadModal = () => {
  uploadModalVisible.value = false
  selectedFiles.value = []
  isDragOver.value = false
  
  // 清空 file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const viewDetails = (row: any) => {
  if (!row.isViewable) return
  
  // Navigate to detail page similar to AnalysisView
  router.push({
    name: 'DataSourceDetail',
    params: { id: row.id }
  })
}


// File handling
const triggerFileSelect = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const fileArray = Array.from(target.files)
    validateAndSetFiles(fileArray)
  }
}

// 拖曳處理函數
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
}

const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  // 檢查是否真的離開了拖放區域
  if (!event.currentTarget?.contains(event.relatedTarget as Node)) {
    isDragOver.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    const fileArray = Array.from(files)
    validateAndSetFiles(fileArray)
  }
}

// 驗證並設置檔案
const validateAndSetFiles = (files: File[]) => {
  const allowedTypes = ['.wav', '.mp3', '.txt']
  const validFiles = files.filter(file => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    return allowedTypes.includes(extension)
  })
  
  if (validFiles.length !== files.length) {
    ElMessage.warning(`只支援 ${allowedTypes.join('、')} 格式的檔案`)
  }
  
  if (validFiles.length > 0) {
    selectedFiles.value = validFiles
  }
}

const handleUpload = async () => {
  if (selectedFiles.value.length === 0) return
  
  // 立即關閉上傳對話框
  closeUploadModal()
  
  try {
    if (selectedFiles.value.length === 1) {
      // 單檔案上傳
      const file = selectedFiles.value[0]
      const uploadOptions = {
        autoAnalyze: true,
        notifyOnComplete: true
      }
      
      await dataSourceStore.uploadFile(file, uploadOptions)
      ElMessage.success('檔案上傳成功，正在自動分析中')
      
    } else {
      // 批量上傳
      await uploadMultipleFiles(selectedFiles.value)
    }
    
    // Refresh data to show new files
    await dataSourceStore.fetchDataSourceList(true)
    
    // Start polling to check progress
    dataSourceStore.startPolling()
    
  } catch (error: any) {
    ElMessage.error(error.message || '檔案上傳失敗')
    // 如果上傳失敗，重新打開對話框讓用戶重試
    uploadModalVisible.value = true
  }
}

const uploadMultipleFiles = async (files: File[]) => {
  try {
    const response = await dataSourceService.uploadFiles(files, {
      autoAnalyze: true,
      notifyOnComplete: true
    })
    
    const successCount = response.successful_count || 0
    const failedCount = response.failed_count || 0
    
    if (successCount > 0) {
      ElMessage.success(`成功上傳 ${successCount} 個檔案，正在自動分析中`)
    }
    if (failedCount > 0) {
      ElMessage.warning(`${failedCount} 個檔案上傳失敗`)
    }
    
  } catch (error) {
    throw error
  }
}

// Analysis functions
const retryAnalysis = async (row: any) => {
  try {
    console.log('=== RETRY ANALYSIS DEBUG ===')
    console.log('Row before retry:', row)
    console.log('File ID:', row.id)
    console.log('Current status:', row.rawStatus)
    
    // Set retry state
    row.isRetrying = true
    
    await dataSourceStore.retryAnalysis(row.id)
    
    // 立即更新本地狀態為待分析 - 使用 Vue 響應式更新
    const updatedRow = tableData.value.find(item => item.id === row.id)
    if (updatedRow) {
      updatedRow.rawStatus = 'pending'
      updatedRow.status = '待分析'
      updatedRow.isPending = true
      updatedRow.isFailed = false
      updatedRow.isAnalyzing = false
      updatedRow.isCompleted = false
      updatedRow.isViewable = false
      
      console.log('UI: Updated row status to pending')
      console.log('Updated row:', updatedRow)
    }
    
    ElMessage.success('重新分析已開始')
    
    // Start polling to check progress
    dataSourceStore.startPolling()
    
  } catch (error: any) {
    console.error('Retry analysis error:', error)
    console.error('Error response:', error.response)
    console.error('Error message:', error.message)
    
    // Show more detailed error message
    let errorMessage = '重新分析失敗'
    if (error.response?.data?.detail) {
      errorMessage += ': ' + error.response.data.detail
    } else if (error.message) {
      errorMessage += ': ' + error.message
    }
    
    ElMessage.error(errorMessage)
  } finally {
    // Reset retry state
    row.isRetrying = false
  }
}

// Selection handlers
const handleSelectAll = (checked: boolean) => {
  if (checked) {
    selectedItems.value = tableData.value.map(item => item.id)
  } else {
    selectedItems.value = []
  }
  selectAll.value = checked
}

const handleItemSelect = (id: string, checked: boolean) => {
  if (checked) {
    if (!selectedItems.value.includes(id)) {
      selectedItems.value.push(id)
    }
  } else {
    const index = selectedItems.value.indexOf(id)
    if (index > -1) {
      selectedItems.value.splice(index, 1)
    }
  }
  
  // Update selectAll state
  const totalCount = tableData.value.length
  const selectedCount = selectedItems.value.length
  selectAll.value = selectedCount === totalCount
}

// Batch delete handler
const handleBatchDelete = async () => {
  if (selectedItems.value.length === 0) return
  
  try {
    // 確認刪除
    await ElMessageBox.confirm(
      `確定要刪除選中的 ${selectedItems.value.length} 個檔案嗎？此操作無法撤銷。`,
      '確認刪除',
      {
        confirmButtonText: '確定刪除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 執行批量刪除
    await dataSourceService.batchDelete(selectedItems.value)
    
    ElMessage.success(`成功刪除 ${selectedItems.value.length} 個檔案`)
    
    // 清空選擇
    selectedItems.value = []
    selectAll.value = false
    
    // 重新載入數據
    await dataSourceStore.fetchDataSourceList(true)
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '刪除失敗')
    }
  }
}

// Pagination handlers
const handlePageSizeChange = (newPageSize: number) => {
  pageSize.value = newPageSize
  currentPage.value = 1
  dataSourceStore.setPagination(1, newPageSize)
}

const handleCurrentPageChange = (newPage: number) => {
  currentPage.value = newPage
  dataSourceStore.setPagination(newPage, pageSize.value)
}

// Table handlers
const handleRowClick = (row: any) => {
  // Only handle row click for non-checkbox cells
  // Checkbox cells have their own click handlers
}


// Lifecycle
onMounted(async () => {
  // 同步分頁狀態
  currentPage.value = dataSourceStore.pagination.page
  pageSize.value = dataSourceStore.pagination.size
  
  // 加載真實數據
  try {
    await dataSourceStore.fetchDataSourceList()
    
    // 如果有正在處理的文件，開始輪詢
    if (dataSourceStore.processingCount > 0) {
      dataSourceStore.startPolling()
    } else if (dataSourceStore.failedCount > 0) {
      // 如果沒有正在處理的文件但有失敗的文件，直接啟動自動重試
      dataSourceStore.autoRetryFailedFiles()
    }
    
  } catch (error) {
    console.error('Failed to load data:', error)
    ElMessage.error('載入數據失敗')
  }
})

// Cleanup
onUnmounted(() => {
  // 簡化版本不需要額外清理
})
</script>

<style scoped>
.datasource-page {
  min-height: 100vh;
  background-color: #f3f4f6;
  font-family: 'Noto Sans TC', sans-serif;
}

/* Page Header */
.page-header {
  background: white;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.breadcrumb {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
  gap: 0.5rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

/* Content Section */
.content-section {
  padding: 2rem;
}

/* Toolbar */
.toolbar {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 1rem 1.5rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.selected-info {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Table Styles */
.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  max-height: calc(100vh - 220px); /* 限制高度，為header和其他元素預留空間 */
  display: flex;
  flex-direction: column;
}

.table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  flex: 1;
  min-height: 0; /* 確保可以收縮 */
}

.data-table {
  width: 100%;
  min-width: 900px; /* 調整最小寬度以適應移除三個欄位後的總和 */
  border-collapse: collapse;
  table-layout: auto; /* 讓表格根據內容自動調整列寬 */
}

.table-header {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10; /* 確保表頭在滾動時保持在上方 */
}

.table-th {
  padding: 0.75rem 1.5rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap; /* 防止表頭文字換行 */
  min-width: fit-content; /* 確保有足夠空間 */
}

/* 針對特定列設置最小寬度 */
.table-th:nth-child(1) { min-width: 80px; }  /* 選擇框 */
.table-th:nth-child(2) { min-width: 200px; } /* 檔案名稱 */
.table-th:nth-child(3) { min-width: 160px; } /* 上傳時間 */
.table-th:nth-child(4) { min-width: 120px; } /* 狀態 */
.table-th:nth-child(5) { min-width: 100px; } /* 上傳者 */
.table-th:nth-child(6) { min-width: 90px; }  /* 檔案格式 */
.table-th:nth-child(7) { min-width: 90px; }  /* 詳細內容 */

.checkbox-column {
  width: 80px;
  text-align: center;
}

.table-body {
  background: white;
}

.table-row {
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
  transition: background-color 0.2s;
}

.table-row:hover {
  background-color: #f9fafb;
}

.table-row.selected {
  background-color: #eff6ff;
}

.table-row.selected:hover {
  background-color: #dbeafe;
}

.table-td {
  padding: 1rem 1.5rem;
  white-space: nowrap;
  vertical-align: middle; /* 垂直居中對齊 */
}

/* 針對特定列設置最小寬度，與表頭對應 */
.table-td:nth-child(1) { min-width: 80px; }  /* 選擇框 */
.table-td:nth-child(2) { min-width: 200px; } /* 檔案名稱 */
.table-td:nth-child(3) { min-width: 160px; } /* 上傳時間 */
.table-td:nth-child(4) { min-width: 120px; } /* 狀態 */
.table-td:nth-child(5) { min-width: 100px; } /* 上傳者 */
.table-td:nth-child(6) { min-width: 90px; }  /* 檔案格式 */
.table-td:nth-child(7) { min-width: 90px; }  /* 詳細內容 */

.file-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
}

.upload-time {
  font-size: 0.875rem;
  color: #1f2937;
}

.status-content {
  font-size: 0.875rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-content.pending {
  color: #f59e0b;
}

.status-content.analyzing {
  color: #3b82f6;
}

.status-content.completed {
  color: #10b981;
}

.status-content.failed {
  color: #ef4444;
}

.pending-icon {
  color: #f59e0b;
  animation: spin 1s linear infinite;
}

.analyzing-icon {
  color: #3b82f6;
  animation: spin 1s linear infinite;
}

.completed-icon {
  color: #10b981;
}

.retry-button {
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.retry-button:hover:not(:disabled) {
  background-color: #dc2626;
}

.retry-button:disabled {
  background-color: #6b7280;
  cursor: not-allowed;
}

.status-operation-failed {
  display: flex;
  align-items: center;
  justify-content: center;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.text-gray-500 {
  color: #6b7280;
}

.view-button {
  color: #3b82f6;
  background: none;
  border: none;
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0;
}

.view-button:hover {
  color: #1d4ed8;
}

.view-button-disabled {
  color: #9ca3af;
  background: none;
  border: none;
  font-size: 0.875rem;
  cursor: not-allowed;
  padding: 0;
}

.analyze-button {
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.analyze-button:hover:not(:disabled) {
  background-color: #059669;
}

.analyze-button:disabled {
  background-color: #6b7280;
  cursor: not-allowed;
}

.status-text {
  font-size: 0.75rem;
  color: #6b7280;
}

.status-operation-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 自定義滾動條樣式 */
.table-wrapper::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.table-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.table-wrapper::-webkit-scrollbar-corner {
  background: #f1f1f1;
}

/* Pagination */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.pagination-container :deep(.el-pagination) {
  --el-pagination-font-size: 14px;
}

/* Upload Modal */
.upload-modal :deep(.el-dialog) {
  border-radius: 1rem;
  overflow: hidden;
}

.upload-content {
  padding: 1rem 0;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  position: relative;
  transition: all 0.3s ease;
  background-color: #fafafa;
}

.upload-area:hover {
  border-color: #3b82f6;
  background-color: #f8faff;
}

.upload-area.drag-over {
  border-color: #10b981;
  background-color: #f0fdf4;
  transform: scale(1.02);
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.15);
}

.upload-icon {
  font-size: 4rem;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.upload-text {
  color: #6b7280;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
  font-weight: 500;
}

.upload-hint {
  color: #9ca3af;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.file-input {
  display: none;
}

.select-button {
  margin-top: 0.5rem;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* 檔案選擇區域樣式 */
.selected-files-area {
  padding: 1rem 0;
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.files-header h4 {
  margin: 0;
  color: #1f2937;
  font-size: 1rem;
  font-weight: 600;
}

.files-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.5rem;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: #f9fafb;
}

.file-item:not(:last-child) {
  border-bottom: 1px solid #f3f4f6;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background-color: #f3f4f6;
  color: #6b7280;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
}

.file-size {
  font-size: 0.75rem;
  color: #6b7280;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Responsive design */
@media (max-width: 1024px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .table-container {
    max-height: calc(100vh - 180px); /* 調整小屏幕高度 */
  }
  
  .data-table {
    min-width: 1100px; /* 小屏幕減少最小寬度，但保持足夠空間 */
  }
}

@media (max-width: 768px) {
  .content-section {
    padding: 1rem;
  }
  
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .table-container {
    max-height: calc(100vh - 160px); /* 手機屏幕進一步調整高度 */
  }
  
  .data-table {
    min-width: 900px; /* 手機屏幕最小寬度，保持足夠空間顯示重要列 */
  }
  
  .table-th,
  .table-td {
    padding: 0.5rem 1rem; /* 減少手機屏幕的padding */
    font-size: 0.8rem; /* 減小字體 */
  }
}
</style>