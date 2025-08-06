<template>
  <div class="label-setting-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-content">
        <h1 class="page-title">分類設定</h1>
      </div>
    </header>

    <!-- Content -->
    <div class="label-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <el-icon class="loading-spinner"><Loading /></el-icon>
        載入中...
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <el-icon class="error-icon"><Warning /></el-icon>
        {{ error }}
        <el-button @click="fetchLabels()" type="primary" style="margin-top: 1rem;">
          重新載入
        </el-button>
      </div>
      
      <!-- Content -->
      <div v-else>
        <!-- Product Categories Section -->
        <div class="category-section">
          <div class="section-header">
            <h2 class="section-title">商品分類</h2>
            <div class="section-actions">
              <button 
                class="btn-delete" 
                @click="deleteSelectedTags('product')"
                :disabled="selectedProductTags.length === 0"
              >
                刪除分類 ({{ selectedProductTags.length }})
              </button>
              <button class="btn-cancel" @click="cancelChanges('product')">取消</button>
              <button class="btn-primary" @click="completeChanges('product')">完成</button>
            </div>
          </div>
          
          <div class="tag-container">
            <div 
              v-for="tag in productTags" 
              :key="tag.id"
              :class="['tag-item', { 
                active: tag.is_active, 
                selected: tag.selected,
                'new-tag': newProductTags.some(newTag => newTag.id === tag.id)
              }]"
              @click="toggleTag('product', tag)"
            >
              {{ tag.name }}
              <span v-if="newProductTags.some(newTag => newTag.id === tag.id)" class="new-indicator">(新)</span>
              <span v-if="tag.selected" class="selected-indicator">✓</span>
            </div>
            <div class="tag-item add-tag" @click="addNewTag('product')">
              <el-icon><Plus /></el-icon>新增分類
            </div>
          </div>
        </div>

        <!-- Feedback Categories Section -->
        <div class="category-section">
          <div class="section-header">
            <h2 class="section-title">回饋分類</h2>
            <div class="section-actions">
              <button 
                class="btn-delete" 
                @click="deleteSelectedTags('feedback')"
                :disabled="selectedFeedbackTags.length === 0"
              >
                刪除分類 ({{ selectedFeedbackTags.length }})
              </button>
              <button class="btn-cancel" @click="cancelChanges('feedback')">取消</button>
              <button class="btn-primary" @click="completeChanges('feedback')">完成</button>
            </div>
          </div>
          
          <div class="tag-container">
            <div 
              v-for="tag in feedbackTags" 
              :key="tag.id"
              :class="['tag-item', { 
                active: tag.is_active, 
                selected: tag.selected,
                'new-tag': newFeedbackTags.some(newTag => newTag.id === tag.id)
              }]"
              @click="toggleTag('feedback', tag)"
            >
              {{ tag.name }}
              <span v-if="newFeedbackTags.some(newTag => newTag.id === tag.id)" class="new-indicator">(新)</span>
              <span v-if="tag.selected" class="selected-indicator">✓</span>
            </div>
            <div class="tag-item add-tag" @click="addNewTag('feedback')">
              <el-icon><Plus /></el-icon>新增分類
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Loading, Warning } from '@element-plus/icons-vue'
import { labelsService } from '@/services/labels.service'

interface Label {
  id: number
  name: string
  description?: string
  is_active: boolean
  selected?: boolean  // 新增：選中狀態
  created_at?: string
  updated_at?: string
}

// 響應式數據
const productTags = ref<Label[]>([])
const feedbackTags = ref<Label[]>([])
const loading = ref(false)
const error = ref('')

// 選中狀態管理
const selectedProductTags = ref<number[]>([])
const selectedFeedbackTags = ref<number[]>([])
// 新增的標籤（尚未儲存到資料庫）
const newProductTags = ref<Label[]>([])
const newFeedbackTags = ref<Label[]>([])

// 計算屬性 - 統一管理狀態
const getTagsData = (type: 'product' | 'feedback') => {
  return type === 'product' 
    ? { tags: productTags, selected: selectedProductTags, newTags: newProductTags }
    : { tags: feedbackTags, selected: selectedFeedbackTags, newTags: newFeedbackTags }
}

// 獲取標籤數據
const fetchLabels = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // 並行獲取商品標籤和回饋分類
    const [products, feedbacks] = await Promise.all([
      labelsService.getProductLabels(),
      labelsService.getFeedbackLabels()
    ])
    
    productTags.value = products.map(tag => ({
      ...tag,
      is_active: false, // No tags are active by default
      selected: false // 初始未選中
    }))
    feedbackTags.value = feedbacks.map(tag => ({
      ...tag,
      is_active: false, // No tags are active by default
      selected: false // 初始未選中
    }))
  } catch (err: any) {
    error.value = err.message || '獲取標籤數據失敗'
    ElMessage.error('載入標籤數據失敗')
  } finally {
    loading.value = false
  }
}

// Tag management functions
const toggleTag = (type: 'product' | 'feedback', tag: Label) => {
  const { newTags } = getTagsData(type)
  
  // 檢查是否為新增但尚未儲存的標籤
  if (newTags.value.some(newTag => newTag.id === tag.id)) {
    ElMessage.warning('新增的分類需要先完成儲存才能刪除')
    return
  }
  
  // Toggle tag selected state for deletion
  tag.selected = !tag.selected
  
  const selectedArray = type === 'product' ? selectedProductTags : selectedFeedbackTags
  
  if (tag.selected) {
    selectedArray.value.push(tag.id)
  } else {
    const index = selectedArray.value.indexOf(tag.id)
    if (index > -1) {
      selectedArray.value.splice(index, 1)
    }
  }
}

const addNewTag = (type: 'product' | 'feedback') => {
  const tagName = prompt('請輸入新分類名稱：')
  if (!tagName || !tagName.trim()) {
    return
  }

  const trimmedName = tagName.trim()
  const { tags } = getTagsData(type)
  
  // 檢查是否已存在相同名稱的標籤
  if (tags.value.some(tag => tag.name === trimmedName)) {
    ElMessage.warning('此分類名稱已存在')
    return
  }

  // 創建臨時標籤（尚未儲存到資料庫）
  const tempTag: Label = {
    id: Date.now(), // 使用時間戳作為臨時ID
    name: trimmedName,
    is_active: true,
    selected: false
  }

  if (type === 'product') {
    productTags.value.push(tempTag)
    newProductTags.value.push(tempTag)
  } else {
    feedbackTags.value.push(tempTag)
    newFeedbackTags.value.push(tempTag)
  }
  
  ElMessage.info('新分類已加入，點擊完成後儲存')
}

// 刪除選中的標籤（立即更新到資料庫）
const deleteSelectedTags = async (type: 'product' | 'feedback') => {
  const selectedArray = type === 'product' ? selectedProductTags : selectedFeedbackTags
  const tagsArray = type === 'product' ? productTags : feedbackTags
  
  if (selectedArray.value.length === 0) {
    ElMessage.warning('請先選擇要刪除的分類')
    return
  }
  
  try {
    // 立即呼叫 API 刪除
    let result
    if (type === 'product') {
      result = await labelsService.deleteProductLabelsBatch(selectedArray.value)
    } else {
      result = await labelsService.deleteFeedbackLabelsBatch(selectedArray.value)
    }
    
    // 在UI上移除成功刪除的標籤
    tagsArray.value = tagsArray.value.filter(tag => !selectedArray.value.includes(tag.id))
    
    if (result.failed_count > 0) {
      ElMessage.warning(`成功刪除 ${result.deleted_count} 個分類，${result.failed_count} 個刪除失敗`)
    } else {
      ElMessage.success(`成功刪除 ${result.deleted_count} 個分類`)
    }
    
    // 清空選中狀態
    selectedArray.value = []
  } catch (err: any) {
    ElMessage.error(err.message || '刪除失敗')
  }
}

// Unified action handlers
const cancelChanges = (type: 'product' | 'feedback') => {
  const tagsArray = type === 'product' ? productTags : feedbackTags
  const newTagsArray = type === 'product' ? newProductTags : newFeedbackTags
  const selectedArray = type === 'product' ? selectedProductTags : selectedFeedbackTags
  const typeName = type === 'product' ? '商品' : '回饋'
  
  // 移除尚未儲存的新標籤
  if (newTagsArray.value.length > 0) {
    tagsArray.value = tagsArray.value.filter(
      tag => !newTagsArray.value.some(newTag => newTag.id === tag.id)
    )
    newTagsArray.value = []
    ElMessage.info(`已取消新增的${typeName}分類`)
  }
  selectedArray.value = []
}

const completeChanges = async (type: 'product' | 'feedback') => {
  const tagsArray = type === 'product' ? productTags : feedbackTags
  const newTagsArray = type === 'product' ? newProductTags : newFeedbackTags
  const selectedArray = type === 'product' ? selectedProductTags : selectedFeedbackTags
  const typeName = type === 'product' ? '商品' : '回饋'
  
  try {
    let hasChanges = false
    let successCount = 0
    let failCount = 0
    
    // 儲存新增的標籤
    for (const newTag of newTagsArray.value) {
      hasChanges = true
      try {
        let savedLabel
        if (type === 'product') {
          savedLabel = await labelsService.createProductLabel({ 
            name: newTag.name 
          })
        } else {
          savedLabel = await labelsService.createFeedbackLabel({ 
            name: newTag.name,
            category: newTag.name
          })
        }
        
        // 更新臨時ID為真實ID
        const index = tagsArray.value.findIndex(tag => tag.id === newTag.id)
        if (index !== -1) {
          tagsArray.value[index] = {
            ...savedLabel,
            is_active: true,
            selected: false
          }
        }
        successCount++
      } catch (err: any) {
        failCount++
        // 移除失敗的標籤
        tagsArray.value = tagsArray.value.filter(tag => tag.id !== newTag.id)
      }
    }
    
    if (hasChanges) {
      if (failCount > 0) {
        ElMessage.warning(`成功新增 ${successCount} 個分類，${failCount} 個新增失敗`)
      } else {
        ElMessage.success(`成功新增 ${successCount} 個${typeName}分類`)
      }
      newTagsArray.value = []
    } else {
      ElMessage.info('沒有需要儲存的新分類')
    }
    
    selectedArray.value = []
  } catch (err: any) {
    ElMessage.error(err.message || '儲存失敗')
  }
}

// Lifecycle
onMounted(async () => {
  await fetchLabels()
})
</script>

<style scoped>
.label-setting-page {
  min-height: 100vh;
  background-color: #f3f4f6;
  font-family: 'Noto Sans TC', sans-serif;
}

/* Page Header */
.page-header {
  background: white;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 1.5rem 2rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

/* Content */
.label-content {
  padding: 2rem;
}

.category-section {
  background: white;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 32px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.section-actions {
  display: flex;
  gap: 0.75rem;
}

.tag-container {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  min-height: 120px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-content: flex-start;
}

.tag-item {
  background-color: #f3f4f6;
  color: #374151;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.tag-item:hover {
  background-color: #e5e7eb;
  border-color: #d1d5db;
}

.tag-item.active {
  background-color: #3b82f6;
  color: white;
  border-color: #2563eb;
}

.tag-item.selected {
  background-color: #ef4444;
  color: white;
  border-color: #dc2626;
}

.selected-indicator {
  margin-left: 6px;
  font-weight: bold;
}

.new-indicator {
  margin-left: 4px;
  font-size: 12px;
  color: #3b82f6;
  font-weight: normal;
}

.tag-item.new-tag {
  background-color: #dbeafe;
  border-color: #3b82f6;
  border-style: dashed;
}

.tag-item.new-tag:hover {
  background-color: #bfdbfe;
}

.tag-item.new-tag.selected {
  background-color: #ef4444;
  color: white;
  border-style: solid;
}

.tag-item.new-tag.selected .new-indicator {
  color: white;
}

.add-tag {
  background-color: transparent;
  border: 1px dashed #9ca3af;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 4px;
}

.add-tag:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

/* Button styles */
.btn-cancel, .btn-primary, .btn-delete {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
}

.btn-cancel {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-cancel:hover {
  background-color: #e5e7eb;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background-color: #2563eb;
}

.btn-delete {
  background-color: #ef4444;
  color: white;
}

.btn-delete:hover:not(:disabled) {
  background-color: #dc2626;
}

.btn-delete:disabled {
  background-color: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  color: #6b7280;
  font-size: 0.875rem;
  margin: 2rem;
}

.loading-spinner {
  font-size: 2rem;
  margin-bottom: 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #ef4444;
}

/* Responsive design */
@media (max-width: 768px) {
  .label-content {
    padding: 1rem;
  }
  
  .section-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .section-actions {
    justify-content: center;
  }
}
</style>