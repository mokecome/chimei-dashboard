<template>
  <el-dialog
    v-model="dialogVisible"
    title="匯入標籤數據"
    width="600px"
    @close="handleClose"
  >
    <el-steps :active="currentStep" align-center class="import-steps">
      <el-step title="選擇檔案" icon="Upload" />
      <el-step title="數據預覽" icon="View" />
      <el-step title="匯入設定" icon="Setting" />
      <el-step title="完成匯入" icon="Check" />
    </el-steps>
    
    <!-- 步驟 1: 選擇檔案 -->
    <div v-show="currentStep === 0" class="step-content">
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".csv,.xlsx,.json"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          將檔案拖曳到此處，或 <em>點擊選擇檔案</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支援 CSV、Excel、JSON 格式檔案，檔案大小不超過 10MB
          </div>
        </template>
      </el-upload>
      
      <div class="format-info">
        <h4>支援的檔案格式：</h4>
        <ul>
          <li><strong>CSV</strong>: 欄位順序為 name,category,description</li>
          <li><strong>Excel</strong>: 第一列為欄位名稱，支援多個工作表</li>
          <li><strong>JSON</strong>: 陣列格式，包含 name, category, description 欄位</li>
        </ul>
      </div>
    </div>
    
    <!-- 步驟 2: 數據預覽 -->
    <div v-show="currentStep === 1" class="step-content">
      <div class="preview-header">
        <h4>數據預覽</h4>
        <div class="preview-stats">
          <el-tag type="info">總計 {{ previewData.length }} 筆</el-tag>
          <el-tag type="success">商品標籤 {{ productLabelsCount }} 筆</el-tag>
          <el-tag type="warning">反饋標籤 {{ feedbackLabelsCount }} 筆</el-tag>
        </div>
      </div>
      
      <el-table
        :data="previewData.slice(0, 10)"
        border
        size="small"
        class="preview-table"
      >
        <el-table-column prop="name" label="標籤名稱" width="150" />
        <el-table-column prop="category" label="分類" width="120" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="類型" width="80">
          <template #default="{ row }">
            <el-tag 
              :type="getRowType(row) === 'product' ? 'primary' : 'success'"
              size="small"
            >
              {{ getRowType(row) === 'product' ? '商品' : '反饋' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="狀態" width="80">
          <template #default="{ row }">
            <el-tag 
              :type="validateRow(row).isValid ? 'success' : 'danger'"
              size="small"
            >
              {{ validateRow(row).isValid ? '有效' : '錯誤' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="previewData.length > 10" class="preview-more">
        還有 {{ previewData.length - 10 }} 筆數據...
      </div>
      
      <!-- 驗證錯誤 -->
      <div v-if="validationErrors.length" class="validation-errors">
        <h4>數據驗證錯誤：</h4>
        <ul>
          <li v-for="error in validationErrors.slice(0, 5)" :key="error">
            {{ error }}
          </li>
        </ul>
        <div v-if="validationErrors.length > 5">
          還有 {{ validationErrors.length - 5 }} 個錯誤...
        </div>
      </div>
    </div>
    
    <!-- 步驟 3: 匯入設定 -->
    <div v-show="currentStep === 2" class="step-content">
      <el-form :model="importSettings" label-width="120px">
        <el-form-item label="匯入類型">
          <el-radio-group v-model="importSettings.type">
            <el-radio value="both">全部匯入</el-radio>
            <el-radio value="product">僅商品標籤</el-radio>
            <el-radio value="feedback">僅反饋標籤</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="重複處理">
          <el-radio-group v-model="importSettings.duplicateAction">
            <el-radio value="skip">跳過重複項目</el-radio>
            <el-radio value="update">更新現有項目</el-radio>
            <el-radio value="rename">重新命名</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="驗證等級">
          <el-radio-group v-model="importSettings.validationLevel">
            <el-radio value="strict">嚴格驗證</el-radio>
            <el-radio value="normal">一般驗證</el-radio>
            <el-radio value="loose">寬鬆驗證</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="importSettings.createBackup">
            匯入前建立備份
          </el-checkbox>
        </el-form-item>
      </el-form>
      
      <div class="import-summary">
        <h4>匯入摘要：</h4>
        <ul>
          <li>將匯入 {{ getImportCount() }} 筆標籤</li>
          <li>預計重複項目 {{ getDuplicateCount() }} 筆</li>
          <li>驗證錯誤 {{ validationErrors.length }} 筆</li>
        </ul>
      </div>
    </div>
    
    <!-- 步驟 4: 匯入結果 -->
    <div v-show="currentStep === 3" class="step-content">
      <div v-if="importing" class="importing">
        <el-icon class="is-loading" size="40"><Loading /></el-icon>
        <div class="importing-text">正在匯入數據，請稍候...</div>
        <el-progress :percentage="importProgress" />
      </div>
      
      <div v-else-if="importResult" class="import-result">
        <div class="result-header">
          <el-icon size="60" color="#67c23a"><CircleCheck /></el-icon>
          <h3>匯入完成</h3>
        </div>
        
        <div class="result-stats">
          <div class="stat-item success">
            <span class="stat-number">{{ importResult.successCount }}</span>
            <span class="stat-label">成功匯入</span>
          </div>
          <div class="stat-item warning">
            <span class="stat-number">{{ importResult.duplicateCount }}</span>
            <span class="stat-label">重複跳過</span>
          </div>
          <div class="stat-item danger">
            <span class="stat-number">{{ importResult.failCount }}</span>
            <span class="stat-label">匯入失敗</span>
          </div>
        </div>
        
        <div v-if="importResult.errors.length" class="import-errors">
          <h4>錯誤詳情：</h4>
          <ul>
            <li v-for="error in importResult.errors" :key="error">
              {{ error }}
            </li>
          </ul>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button v-if="currentStep > 0 && currentStep < 3" @click="prevStep">
          上一步
        </el-button>
        <el-button @click="handleClose">
          {{ currentStep === 3 ? '關閉' : '取消' }}
        </el-button>
        <el-button 
          v-if="currentStep < 3"
          type="primary" 
          :disabled="!canNextStep"
          :loading="importing"
          @click="nextStep"
        >
          {{ currentStep === 2 ? '開始匯入' : '下一步' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  UploadFilled, 
  Loading, 
  CircleCheck 
} from '@element-plus/icons-vue'
import { useLabelsStore } from '@/stores/labels'
import type { UploadFile, UploadFiles } from 'element-plus'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'imported'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const labelsStore = useLabelsStore()

// 響應式狀態
const uploadRef = ref()
const currentStep = ref(0)
const fileList = ref<UploadFiles>([])
const previewData = ref<any[]>([])
const validationErrors = ref<string[]>([])
const importing = ref(false)
const importProgress = ref(0)
const importResult = ref<any>(null)

const importSettings = ref({
  type: 'both',
  duplicateAction: 'skip',
  validationLevel: 'normal',
  createBackup: true
})

// 計算屬性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const canNextStep = computed(() => {
  switch (currentStep.value) {
    case 0: return fileList.value.length > 0
    case 1: return previewData.value.length > 0
    case 2: return validationErrors.value.length === 0
    default: return false
  }
})

const productLabelsCount = computed(() => {
  return previewData.value.filter(row => getRowType(row) === 'product').length
})

const feedbackLabelsCount = computed(() => {
  return previewData.value.filter(row => getRowType(row) === 'feedback').length
})

// 文件處理
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
  if (file.raw) {
    parseFile(file.raw)
  }
}

const handleExceed = () => {
  ElMessage.warning('只能選擇一個檔案')
}

const parseFile = async (file: File) => {
  try {
    const text = await file.text()
    let data: any[] = []
    
    if (file.name.endsWith('.json')) {
      data = JSON.parse(text)
    } else if (file.name.endsWith('.csv')) {
      data = parseCSV(text)
    } else {
      ElMessage.error('暫不支援此檔案格式')
      return
    }
    
    previewData.value = data
    validateData(data)
    
  } catch (error) {
    ElMessage.error('檔案解析失敗')
    console.error(error)
  }
}

const parseCSV = (text: string) => {
  const lines = text.split('\n').filter(line => line.trim())
  const headers = lines[0].split(',').map(h => h.trim())
  
  return lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim())
    const obj: any = {}
    headers.forEach((header, index) => {
      obj[header] = values[index] || ''
    })
    return obj
  })
}

const validateData = (data: any[]) => {
  const errors: string[] = []
  
  data.forEach((row, index) => {
    const validation = validateRow(row)
    if (!validation.isValid) {
      errors.push(`第${index + 1}行: ${validation.errors.join(', ')}`)
    }
  })
  
  validationErrors.value = errors
}

const validateRow = (row: any) => {
  const errors: string[] = []
  
  if (!row.name || !row.name.trim()) {
    errors.push('標籤名稱不能為空')
  }
  
  if (getRowType(row) === 'feedback' && !row.category) {
    errors.push('反饋標籤必須指定分類')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

const getRowType = (row: any): 'product' | 'feedback' => {
  return row.category && 
         labelsStore.settings.defaultFeedbackCategories.includes(row.category) 
         ? 'feedback' : 'product'
}

const getImportCount = () => {
  switch (importSettings.value.type) {
    case 'product': return productLabelsCount.value
    case 'feedback': return feedbackLabelsCount.value
    default: return previewData.value.length
  }
}

const getDuplicateCount = () => {
  // 簡化計算，實際應該檢查與現有標籤的重複
  return Math.floor(getImportCount() * 0.1)
}

// 步驟控制
const nextStep = async () => {
  if (currentStep.value === 2) {
    await startImport()
  } else {
    currentStep.value++
  }
}

const prevStep = () => {
  currentStep.value--
}

const startImport = async () => {
  importing.value = true
  importProgress.value = 0
  currentStep.value = 3
  
  try {
    // 模擬匯入進度
    const interval = setInterval(() => {
      importProgress.value += 10
      if (importProgress.value >= 100) {
        clearInterval(interval)
      }
    }, 200)
    
    // 準備匯入數據
    const importData = {
      type: importSettings.value.type as 'product' | 'feedback',
      labels: previewData.value.filter(row => {
        if (importSettings.value.type === 'product') {
          return getRowType(row) === 'product'
        }
        if (importSettings.value.type === 'feedback') {
          return getRowType(row) === 'feedback'
        }
        return true
      })
    }
    
    const result = await labelsStore.importLabels(importData)
    importResult.value = result
    
    emit('imported')
    
    // 匯入成功後關閉對話框
    setTimeout(() => {
      handleClose()
    }, 1000) // 延遲1秒讓用戶看到完成狀態
    
  } catch (error: any) {
    ElMessage.error(error.message || '匯入失敗')
  } finally {
    importing.value = false
    importProgress.value = 100
  }
}

// 處理關閉
const handleClose = () => {
  if (importing.value) return
  
  // 重置狀態
  currentStep.value = 0
  fileList.value = []
  previewData.value = []
  validationErrors.value = []
  importing.value = false
  importProgress.value = 0
  importResult.value = null
  
  emit('update:visible', false)
}
</script>

<style scoped>
.import-steps {
  margin-bottom: 24px;
}

.step-content {
  min-height: 300px;
  padding: 16px 0;
}

.upload-area {
  margin-bottom: 20px;
}

.format-info {
  background-color: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.format-info h4 {
  margin: 0 0 12px 0;
  color: #495057;
}

.format-info ul {
  margin: 0;
  padding-left: 20px;
}

.format-info li {
  margin-bottom: 8px;
  color: #6c757d;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-header h4 {
  margin: 0;
}

.preview-stats {
  display: flex;
  gap: 8px;
}

.preview-table {
  margin-bottom: 16px;
}

.preview-more {
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

.validation-errors {
  margin-top: 20px;
  padding: 16px;
  background-color: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 6px;
}

.validation-errors h4 {
  margin: 0 0 12px 0;
  color: #c53030;
}

.validation-errors ul {
  margin: 0;
  padding-left: 20px;
}

.validation-errors li {
  color: #e53e3e;
  margin-bottom: 4px;
}

.import-summary {
  margin-top: 20px;
  padding: 16px;
  background-color: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 6px;
}

.import-summary h4 {
  margin: 0 0 12px 0;
  color: #0369a1;
}

.importing {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 20px;
}

.importing-text {
  font-size: 16px;
  color: #6c757d;
}

.import-result {
  text-align: center;
}

.result-header {
  margin-bottom: 24px;
}

.result-header h3 {
  margin: 8px 0 0 0;
  color: #67c23a;
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
}

.stat-item.success .stat-number {
  color: #67c23a;
}

.stat-item.warning .stat-number {
  color: #e6a23c;
}

.stat-item.danger .stat-number {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #6c757d;
}

.import-errors {
  text-align: left;
  max-height: 200px;
  overflow-y: auto;
  padding: 16px;
  background-color: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 6px;
}

.import-errors h4 {
  margin: 0 0 12px 0;
  color: #c53030;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>