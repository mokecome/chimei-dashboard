<template>
  <el-dialog
    v-model="dialogVisible"
    title="匯出標籤數據"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="exportOptions"
      label-width="120px"
    >
      <el-form-item label="匯出範圍">
        <el-checkbox-group v-model="exportTypes">
          <el-checkbox value="product">
            商品標籤 ({{ labelsStore.productLabelCount }} 個)
          </el-checkbox>
          <el-checkbox value="feedback">
            反饋標籤 ({{ labelsStore.feedbackLabelCount }} 個)
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      
      <el-form-item label="匯出格式">
        <el-radio-group v-model="exportOptions.format">
          <el-radio value="json">JSON 格式</el-radio>
          <el-radio value="csv">CSV 格式</el-radio>
          <el-radio value="xlsx">Excel 格式</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="額外選項">
        <el-checkbox-group v-model="extraOptions">
          <el-checkbox value="usage">包含使用統計</el-checkbox>
          <el-checkbox value="operations">包含操作歷史</el-checkbox>
          <el-checkbox value="metadata">包含元數據</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      
      <el-form-item label="檔案命名">
        <el-input
          v-model="fileName"
          placeholder="請輸入檔案名稱"
          :suffix-icon="Edit"
        >
          <template #append>
            .{{ exportOptions.format }}
          </template>
        </el-input>
      </el-form-item>
      
      <!-- 預覽統計 -->
      <el-form-item>
        <div class="export-preview">
          <h4>匯出預覽：</h4>
          <div class="preview-stats">
            <div class="stat-row">
              <span class="stat-label">商品標籤：</span>
              <span class="stat-value">
                {{ exportTypes.includes('product') ? labelsStore.activeProductLabels.length : 0 }} 個
              </span>
            </div>
            <div class="stat-row">
              <span class="stat-label">反饋標籤：</span>
              <span class="stat-value">
                {{ exportTypes.includes('feedback') ? labelsStore.activeFeedbackLabels.length : 0 }} 個
              </span>
            </div>
            <div class="stat-row">
              <span class="stat-label">檔案格式：</span>
              <span class="stat-value">{{ formatNames[exportOptions.format] }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">預估大小：</span>
              <span class="stat-value">{{ estimatedSize }}</span>
            </div>
          </div>
        </div>
      </el-form-item>
    </el-form>
    
    <!-- 格式說明 -->
    <div class="format-description">
      <h4>格式說明：</h4>
      <div v-if="exportOptions.format === 'json'" class="format-info">
        <strong>JSON 格式：</strong>結構化數據，適合程式處理，包含完整的標籤資訊和層級結構。
      </div>
      <div v-else-if="exportOptions.format === 'csv'" class="format-info">
        <strong>CSV 格式：</strong>純文字表格，適合Excel開啟，欄位包含：name, category, description, isActive, usage。
      </div>
      <div v-else-if="exportOptions.format === 'xlsx'" class="format-info">
        <strong>Excel 格式：</strong>多工作表結構，商品標籤和反饋標籤分別存放，包含格式和統計資訊。
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="exporting"
          :disabled="!canExport"
          @click="handleExport"
        >
          <el-icon><Download /></el-icon>
          開始匯出
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Edit } from '@element-plus/icons-vue'
import { useLabelsStore } from '@/stores/labels'
import type { ExportLabelOptions } from '@/types/labels'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const labelsStore = useLabelsStore()

// 響應式狀態
const formRef = ref()
const exporting = ref(false)
const fileName = ref('')

const exportOptions = ref<ExportLabelOptions>({
  includeProduct: true,
  includeFeedback: true,
  includeUsage: false,
  includeOperationHistory: false,
  format: 'json'
})

const exportTypes = ref<string[]>(['product', 'feedback'])
const extraOptions = ref<string[]>([])

// 計算屬性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const canExport = computed(() => {
  return exportTypes.value.length > 0 && fileName.value.trim()
})

const formatNames = {
  json: 'JSON 檔案',
  csv: 'CSV 檔案',
  xlsx: 'Excel 檔案'
}

const estimatedSize = computed(() => {
  const baseSize = exportTypes.value.length * 1024 // 基礎大小
  const itemCount = (exportTypes.value.includes('product') ? labelsStore.productLabelCount : 0) +
                   (exportTypes.value.includes('feedback') ? labelsStore.feedbackLabelCount : 0)
  
  const estimatedBytes = baseSize + (itemCount * 100) // 每個項目約100字節
  
  if (estimatedBytes < 1024) {
    return `${estimatedBytes} B`
  } else if (estimatedBytes < 1024 * 1024) {
    return `${(estimatedBytes / 1024).toFixed(1)} KB`
  } else {
    return `${(estimatedBytes / (1024 * 1024)).toFixed(1)} MB`
  }
})

// 監聽選項變化
watch(exportTypes, (newTypes) => {
  exportOptions.value.includeProduct = newTypes.includes('product')
  exportOptions.value.includeFeedback = newTypes.includes('feedback')
})

watch(extraOptions, (newOptions) => {
  exportOptions.value.includeUsage = newOptions.includes('usage')
  exportOptions.value.includeOperationHistory = newOptions.includes('operations')
})

watch(dialogVisible, (visible) => {
  if (visible) {
    resetForm()
  }
})

// 重置表單
const resetForm = () => {
  exportTypes.value = ['product', 'feedback']
  extraOptions.value = []
  exportOptions.value = {
    includeProduct: true,
    includeFeedback: true,
    includeUsage: false,
    includeOperationHistory: false,
    format: 'json'
  }
  
  // 生成默認檔案名稱
  const now = new Date()
  const dateStr = now.toISOString().split('T')[0]
  fileName.value = `標籤設定_${dateStr}`
}

// 處理匯出
const handleExport = async () => {
  if (!canExport.value) return
  
  exporting.value = true
  
  try {
    await labelsStore.exportLabels({
      ...exportOptions.value,
      fileName: fileName.value
    })
    
    ElMessage.success('標籤數據匯出成功')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '匯出失敗')
  } finally {
    exporting.value = false
  }
}

// 處理關閉
const handleClose = () => {
  if (exporting.value) return
  
  emit('update:visible', false)
}
</script>

<style scoped>
.export-preview {
  padding: 16px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  margin-top: 8px;
}

.export-preview h4 {
  margin: 0 0 12px 0;
  color: #495057;
  font-size: 14px;
}

.preview-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #6c757d;
  font-size: 13px;
}

.stat-value {
  color: #495057;
  font-weight: 500;
  font-size: 13px;
}

.format-description {
  margin-top: 20px;
  padding: 16px;
  background-color: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 6px;
}

.format-description h4 {
  margin: 0 0 8px 0;
  color: #0369a1;
  font-size: 14px;
}

.format-info {
  color: #0369a1;
  font-size: 13px;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>