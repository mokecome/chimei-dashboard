<template>
  <div class="filter-panel">
    <!-- 筛选器标题 -->
    <div class="filter-header">
      <h3 class="filter-title">篩選條件</h3>
      <div class="filter-actions">
        <el-button size="small" @click="clearAllFilters">
          清除全部
        </el-button>
        <el-button type="primary" size="small" @click="applyFilters">
          套用篩選
        </el-button>
      </div>
    </div>

    <!-- 筛选表单 -->
    <el-form :model="localFilters" label-width="100px" class="filter-form">
      <!-- 商品分类标签 -->
      <el-form-item label="商品分類">
        <el-select
          v-model="localFilters.productLabels"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="請選擇商品分類（最多4個）"
          style="width: 100%"
          :max-collapse-tags="2"
        >
          <el-option
            v-for="label in productLabels"
            :key="label"
            :label="label"
            :value="label"
            :disabled="localFilters.productLabels?.length >= 4 && !localFilters.productLabels.includes(label)"
          />
        </el-select>
      </el-form-item>

      <!-- 反馈分类标签 -->
      <el-form-item label="反饋分類">
        <el-select
          v-model="localFilters.feedbackLabels"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="請選擇反饋分類"
          style="width: 100%"
          :max-collapse-tags="2"
        >
          <el-option
            v-for="label in feedbackLabels"
            :key="label"
            :label="label"
            :value="label"
          />
        </el-select>
      </el-form-item>

      <!-- 评价倾向 -->
      <el-form-item label="評價傾向">
        <el-select
          v-model="localFilters.sentiment"
          placeholder="請選擇評價傾向"
          clearable
          style="width: 100%"
        >
          <el-option label="正面" value="positive" />
          <el-option label="負面" value="negative" />
          <el-option label="中立" value="neutral" />
        </el-select>
      </el-form-item>

      <!-- 上传者 -->
      <el-form-item label="上傳者">
        <el-select
          v-model="localFilters.uploader"
          placeholder="請選擇上傳者"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="user in uploaders"
            :key="user.id"
            :label="user.name"
            :value="user.id"
          />
        </el-select>
      </el-form-item>

      <!-- 时间范围 -->
      <el-form-item label="時間範圍">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="開始時間"
          end-placeholder="結束時間"
          format="YYYY-MM-DD HH:mm"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>

      <!-- 关键字搜索 -->
      <el-form-item label="關鍵字">
        <el-input
          v-model="localFilters.keyword"
          placeholder="搜索檔案名稱或摘要內容"
          clearable
          @keyup.enter="applyFilters"
        />
      </el-form-item>
    </el-form>

    <!-- 当前筛选条件显示 -->
    <div v-if="hasActiveFilters" class="active-filters">
      <div class="active-filters-title">目前篩選條件：</div>
      <div class="active-filters-content">
        <!-- 商品标签 -->
        <el-tag
          v-for="label in localFilters.productLabels"
          :key="`product-${label}`"
          closable
          @close="removeProductLabel(label)"
          class="filter-tag"
        >
          商品: {{ label }}
        </el-tag>

        <!-- 反馈标签 -->
        <el-tag
          v-for="label in localFilters.feedbackLabels"
          :key="`feedback-${label}`"
          type="success"
          closable
          @close="removeFeedbackLabel(label)"
          class="filter-tag"
        >
          反饋: {{ label }}
        </el-tag>

        <!-- 情绪 -->
        <el-tag
          v-if="localFilters.sentiment"
          type="warning"
          closable
          @close="localFilters.sentiment = undefined"
          class="filter-tag"
        >
          情緒: {{ getSentimentLabel(localFilters.sentiment) }}
        </el-tag>

        <!-- 上传者 -->
        <el-tag
          v-if="localFilters.uploader"
          type="info"
          closable
          @close="localFilters.uploader = undefined"
          class="filter-tag"
        >
          上傳者: {{ getUploaderName(localFilters.uploader) }}
        </el-tag>

        <!-- 时间范围 -->
        <el-tag
          v-if="dateRange && dateRange.length === 2"
          type="danger"
          closable
          @close="dateRange = []"
          class="filter-tag"
        >
          時間: {{ formatDateRange(dateRange) }}
        </el-tag>

        <!-- 关键字 -->
        <el-tag
          v-if="localFilters.keyword"
          closable
          @close="localFilters.keyword = undefined"
          class="filter-tag"
        >
          關鍵字: {{ localFilters.keyword }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { AnalysisFilter } from '@/types/analysis'

interface Props {
  filters: AnalysisFilter
  productLabels: string[]
  feedbackLabels: string[]
  uploaders: Array<{ id: string, name: string }>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:filters': [filters: AnalysisFilter]
  'apply': [filters: AnalysisFilter]
}>()

// 本地筛选条件
const localFilters = ref<AnalysisFilter>({ ...props.filters })
const dateRange = ref<string[]>([])

// 计算属性
const hasActiveFilters = computed(() => {
  return !!(
    localFilters.value.productLabels?.length ||
    localFilters.value.feedbackLabels?.length ||
    localFilters.value.sentiment ||
    localFilters.value.uploader ||
    localFilters.value.keyword ||
    dateRange.value.length
  )
})

// 监听props变化
watch(() => props.filters, (newFilters) => {
  localFilters.value = { ...newFilters }
  if (newFilters.dateRange) {
    dateRange.value = [...newFilters.dateRange]
  } else {
    dateRange.value = []
  }
}, { deep: true, immediate: true })

// 监听时间范围变化
watch(dateRange, (newRange) => {
  if (newRange.length === 2) {
    localFilters.value.dateRange = [newRange[0], newRange[1]]
  } else {
    localFilters.value.dateRange = undefined
  }
})

// 应用筛选
const applyFilters = () => {
  const filters = { ...localFilters.value }
  
  // 清理空值
  Object.keys(filters).forEach(key => {
    const value = filters[key as keyof AnalysisFilter]
    if (value === undefined || value === null || 
        (Array.isArray(value) && value.length === 0) ||
        (typeof value === 'string' && value.trim() === '')) {
      delete filters[key as keyof AnalysisFilter]
    }
  })

  emit('update:filters', filters)
  emit('apply', filters)
}

// 清除所有筛选
const clearAllFilters = () => {
  localFilters.value = {}
  dateRange.value = []
  applyFilters()
}

// 移除商品标签
const removeProductLabel = (label: string) => {
  if (localFilters.value.productLabels) {
    localFilters.value.productLabels = localFilters.value.productLabels.filter(l => l !== label)
    if (localFilters.value.productLabels.length === 0) {
      localFilters.value.productLabels = undefined
    }
  }
}

// 移除反馈标签
const removeFeedbackLabel = (label: string) => {
  if (localFilters.value.feedbackLabels) {
    localFilters.value.feedbackLabels = localFilters.value.feedbackLabels.filter(l => l !== label)
    if (localFilters.value.feedbackLabels.length === 0) {
      localFilters.value.feedbackLabels = undefined
    }
  }
}

// 获取情绪标签
const getSentimentLabel = (sentiment: string) => {
  const labels = {
    positive: '正面',
    negative: '負面', 
    neutral: '中立'
  }
  return labels[sentiment as keyof typeof labels] || sentiment
}

// 获取上传者名称
const getUploaderName = (uploaderId: string) => {
  const uploader = props.uploaders.find(u => u.id === uploaderId)
  return uploader?.name || uploaderId
}

// 格式化时间范围
const formatDateRange = (range: string[]) => {
  if (range.length !== 2) return ''
  const start = new Date(range[0]).toLocaleString('zh-TW', { 
    month: 'numeric', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
  const end = new Date(range[1]).toLocaleString('zh-TW', { 
    month: 'numeric', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
  return `${start} - ${end}`
}
</script>

<style scoped>
.filter-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.filter-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.filter-form {
  padding: 20px;
}

.active-filters {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  background: #f9fafb;
}

.active-filters-title {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.active-filters-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tag {
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .filter-actions {
    justify-content: flex-end;
  }
  
  .filter-form {
    padding: 16px;
  }
  
  .active-filters {
    padding: 12px 16px;
  }
}
</style>