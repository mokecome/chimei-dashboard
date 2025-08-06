<template>
  <el-dialog
    v-model="visible"
    title="選擇篩選項目"
    width="800px"
    :before-close="handleClose"
    class="filter-selector-dialog"
  >
    <div class="filter-selector">
      <!-- 大類選擇 -->
      <div class="category-list">
        <h3 class="section-title">選擇篩選類別</h3>
        <div class="category-items">
          <div
            v-for="category in categories"
            :key="category.key"
            :class="[
              'category-item',
              { 'selected': selectedCategory === category.key }
            ]"
            @click="selectCategory(category)"
          >
            <div class="category-info">
              <span class="category-label">{{ category.label }}</span>
              <span class="category-count">{{ getCategoryStatus(category) }}</span>
            </div>
            <div class="category-type">
              {{ category.type === 'search' ? '關鍵字搜尋' : '可複選' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 選項選擇 -->
      <div v-if="selectedCategory" class="options-selection">
        <div class="selection-header">
          <h3 class="section-title">
            {{ getCurrentCategoryLabel() }}
            <span class="selection-count">{{ getCategoryStatus(getCurrentCategory()!) }}</span>
          </h3>
          
          <!-- 搜尋框 -->
          <el-input
            v-if="getCurrentCategory()?.searchable"
            v-model="searchQuery"
            placeholder="搜尋..."
            prefix-icon="Search"
            class="search-input"
            clearable
          />
        </div>

        <!-- 摘要搜尋 (特殊處理) -->
        <div v-if="selectedCategory === 'summary_search'" class="summary-search">
          <el-input
            v-model="summaryKeyword"
            :placeholder="filterOptions?.summary_search?.placeholder || '輸入關鍵字搜尋...'"
            class="summary-input"
            clearable
          />
          <p class="summary-hint">輸入關鍵字來搜尋摘要內容</p>
        </div>

        <!-- 多選選項列表 -->
        <div v-else class="options-list">
          <div class="options-grid">
            <el-checkbox-group v-model="selectedOptions">
              <el-checkbox
                v-for="option in filteredOptions"
                :key="option.value"
                :label="option.value"
                class="option-item"
              >
                {{ formatOptionLabel(option) }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
          
          <!-- 快速選擇按鈕 -->
          <div class="quick-actions">
            <el-button size="small" @click="selectAll">全選</el-button>
            <el-button size="small" @click="clearAll">清空</el-button>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleConfirm">確定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  filtersService, 
  FILTER_CATEGORIES,
  type FilterOptions,
  type FilterCategory,
  type FilterOption 
} from '@/services/filters.service'

// Props & Emits
interface Props {
  modelValue: boolean
  currentSelections?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  currentSelections: () => []
})

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', data: { category: string; selections: string[]; keyword?: string }): void
}

const emit = defineEmits<Emits>()

// Reactive data
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const categories = ref(FILTER_CATEGORIES)
const filterOptions = ref<FilterOptions | null>(null)
const selectedCategory = ref<keyof FilterOptions | null>(null)
const selectedOptions = ref<string[]>([])
const summaryKeyword = ref('')
const searchQuery = ref('')
const loading = ref(false)

// Computed
const getCurrentCategory = () => {
  return categories.value.find(cat => cat.key === selectedCategory.value)
}

const getCurrentCategoryLabel = () => {
  return getCurrentCategory()?.label || ''
}

const getCurrentOptions = (): FilterOption[] => {
  if (!filterOptions.value || !selectedCategory.value) return []
  
  const options = filterOptions.value[selectedCategory.value]
  if (Array.isArray(options)) {
    return options as FilterOption[]
  }
  return []
}

const filteredOptions = computed(() => {
  const options = getCurrentOptions()
  return filtersService.searchOptions(options, searchQuery.value)
})

// Methods
const loadFilterOptions = async () => {
  try {
    loading.value = true
    filterOptions.value = await filtersService.getFilterOptions()
  } catch (error) {
    console.error('Failed to load filter options:', error)
    ElMessage.error('載入篩選選項失敗')
  } finally {
    loading.value = false
  }
}

const selectCategory = (category: FilterCategory) => {
  selectedCategory.value = category.key
  selectedOptions.value = []
  summaryKeyword.value = ''
  searchQuery.value = ''
}

const getCategoryStatus = (category: FilterCategory): string => {
  if (!filterOptions.value) return '(0/0)'
  
  if (category.key === 'summary_search') {
    return summaryKeyword.value ? '(1/1)' : '(0/1)'
  }
  
  const options = filterOptions.value[category.key]
  if (Array.isArray(options)) {
    const totalCount = options.length
    const selectedCount = category.key === selectedCategory.value 
      ? selectedOptions.value.length 
      : 0
    return `(${selectedCount}/${totalCount})`
  }
  
  return '(0/0)'
}

const formatOptionLabel = (option: FilterOption): string => {
  const category = getCurrentCategory()
  return category ? filtersService.formatOptionLabel(option, category) : option.label
}

const selectAll = () => {
  selectedOptions.value = getCurrentOptions().map(option => option.value)
}

const clearAll = () => {
  selectedOptions.value = []
}

const handleConfirm = () => {
  if (!selectedCategory.value) {
    ElMessage.warning('請選擇一個篩選類別')
    return
  }

  const category = selectedCategory.value
  let selections: string[] = []
  let keyword: string | undefined

  if (category === 'summary_search') {
    keyword = summaryKeyword.value.trim()
    if (!keyword) {
      ElMessage.warning('請輸入搜尋關鍵字')
      return
    }
  } else {
    selections = [...selectedOptions.value]
    if (selections.length === 0) {
      ElMessage.warning('請至少選擇一個項目')
      return
    }
  }

  emit('confirm', {
    category,
    selections,
    keyword
  })

  visible.value = false
}

const handleClose = () => {
  visible.value = false
}

// Watch for dialog open
watch(visible, (newValue) => {
  if (newValue && !filterOptions.value) {
    loadFilterOptions()
  }
})

// Lifecycle
onMounted(() => {
  if (visible.value) {
    loadFilterOptions()
  }
})
</script>

<style scoped>
.filter-selector-dialog {
  --el-dialog-border-radius: 12px;
}

.filter-selector {
  display: flex;
  gap: 2rem;
  min-height: 500px;
}

.category-list {
  flex: 1;
  border-right: 1px solid #e5e5e5;
  padding-right: 2rem;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 1rem 0;
}

.category-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-item {
  padding: 1rem;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.category-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);
}

.category-item.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.category-label {
  font-weight: 500;
  color: #333;
}

.category-count {
  font-size: 0.875rem;
  color: #666;
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.category-type {
  font-size: 0.8rem;
  color: #888;
}

.options-selection {
  flex: 2;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.selection-count {
  font-size: 0.875rem;
  color: #666;
  font-weight: normal;
}

.search-input {
  width: 200px;
}

.summary-search {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.summary-input {
  width: 100%;
}

.summary-hint {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.options-grid {
  max-height: 350px;
  overflow-y: auto;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  padding: 1rem;
}

.option-item {
  width: 100%;
  margin-bottom: 0.75rem;
}

.option-item:last-child {
  margin-bottom: 0;
}

.quick-actions {
  display: flex;
  gap: 0.5rem;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .filter-selector {
    flex-direction: column;
    gap: 1rem;
  }
  
  .category-list {
    border-right: none;
    border-bottom: 1px solid #e5e5e5;
    padding-right: 0;
    padding-bottom: 1rem;
  }
  
  .selection-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .search-input {
    width: 100%;
  }
}
</style>