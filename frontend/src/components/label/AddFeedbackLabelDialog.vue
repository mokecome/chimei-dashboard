<template>
  <el-dialog
    v-model="dialogVisible"
    title="新增反饋標籤"
    width="480px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="標籤名稱" prop="name">
        <el-input
          v-model="form.name"
          placeholder="請輸入反饋標籤名稱"
          :maxlength="labelsStore.settings.limits.maxFeedbackLabelLength"
          show-word-limit
          clearable
          @keyup.enter="handleSubmit"
        />
      </el-form-item>
      
      <el-form-item label="分類" prop="category">
        <el-select
          v-model="form.category"
          placeholder="選擇標籤分類"
          style="width: 100%"
          clearable
        >
          <el-option
            v-for="category in labelsStore.settings.defaultFeedbackCategories"
            :key="category"
            :label="category"
            :value="category"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          placeholder="請輸入標籤描述（可選）"
          :rows="3"
          maxlength="200"
          show-word-limit
          clearable
        />
      </el-form-item>
      
      <el-form-item>
        <div class="form-info">
          <el-icon><InfoFilled /></el-icon>
          <span>
            反饋標籤用於AI分析客戶反饋的類型和意圖，建議使用具體明確的標籤名稱。
            目前已有 {{ labelsStore.feedbackLabelCount }} 個標籤，上限 {{ labelsStore.settings.limits.maxFeedbackLabels }} 個。
          </span>
        </div>
      </el-form-item>
      
      <!-- 分類預覽 -->
      <el-form-item v-if="form.category">
        <div class="category-preview">
          <div class="preview-title">同分類現有標籤：</div>
          <div class="preview-tags">
            <el-tag
              v-for="label in getCategoryLabels(form.category)"
              :key="label.id"
              size="small"
              :type="label.isActive ? 'primary' : 'info'"
            >
              {{ label.name }}
            </el-tag>
            <span v-if="!getCategoryLabels(form.category).length" class="no-labels">
              暫無標籤
            </span>
          </div>
        </div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="submitting"
          @click="handleSubmit"
        >
          新增標籤
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { useLabelsStore } from '@/stores/labels'
import type { FormInstance, FormRules } from 'element-plus'

interface Props {
  visible: boolean
  defaultCategory?: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'added'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const labelsStore = useLabelsStore()

// 響應式狀態
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = ref({
  name: '',
  category: '',
  description: ''
})

// 計算屬性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 表單驗證規則
const rules: FormRules = {
  name: [
    { required: true, message: '請輸入標籤名稱', trigger: 'blur' },
    { 
      min: 1, 
      max: labelsStore.settings.limits.maxFeedbackLabelLength, 
      message: `標籤名稱長度在 1 到 ${labelsStore.settings.limits.maxFeedbackLabelLength} 個字符`, 
      trigger: 'blur' 
    },
    {
      validator: (rule, value, callback) => {
        if (value && labelsStore.feedbackLabels.some(label => label.name === value.trim())) {
          callback(new Error('標籤名稱已存在'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  category: [
    { required: true, message: '請選擇標籤分類', trigger: 'change' }
  ]
}

// 監聽對話框顯示狀態
watch(dialogVisible, (visible) => {
  if (visible) {
    resetForm()
  }
})

// 重置表單
const resetForm = () => {
  form.value = {
    name: '',
    category: props.defaultCategory || '',
    description: ''
  }
  formRef.value?.clearValidate()
}

// 獲取指定分類的標籤
const getCategoryLabels = (category: string) => {
  return labelsStore.feedbackLabels.filter(label => label.category === category)
}

// 處理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    await labelsStore.addFeedbackLabel(
      form.value.name.trim(),
      form.value.category,
      form.value.description?.trim() || undefined
    )
    
    ElMessage.success('反饋標籤新增成功')
    emit('added')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '新增標籤失敗')
  } finally {
    submitting.value = false
  }
}

// 處理關閉
const handleClose = () => {
  if (submitting.value) return
  
  resetForm()
  emit('update:visible', false)
}
</script>

<style scoped>
.form-info {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background-color: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 6px;
  font-size: 13px;
  color: #0369a1;
  line-height: 1.5;
}

.form-info .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.category-preview {
  width: 100%;
  padding: 12px;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.preview-title {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.no-labels {
  font-size: 12px;
  color: #9ca3af;
  font-style: italic;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>