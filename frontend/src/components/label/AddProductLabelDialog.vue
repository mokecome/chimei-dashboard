<template>
  <el-dialog
    v-model="dialogVisible"
    title="新增商品標籤"
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
          placeholder="請輸入商品標籤名稱"
          :maxlength="labelsStore.settings.limits.maxProductLabelLength"
          show-word-limit
          clearable
          @keyup.enter="handleSubmit"
        />
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
            商品標籤用於AI分析時識別相關商品，建議使用簡潔明確的關鍵字。
            目前已有 {{ labelsStore.productLabelCount }} 個標籤，上限 {{ labelsStore.settings.limits.maxProductLabels }} 個。
          </span>
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
      max: labelsStore.settings.limits.maxProductLabelLength, 
      message: `標籤名稱長度在 1 到 ${labelsStore.settings.limits.maxProductLabelLength} 個字符`, 
      trigger: 'blur' 
    },
    {
      validator: (rule, value, callback) => {
        if (value && labelsStore.productLabels.some(label => label.name === value.trim())) {
          callback(new Error('標籤名稱已存在'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
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
    description: ''
  }
  formRef.value?.clearValidate()
}

// 處理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    await labelsStore.addProductLabel(
      form.value.name.trim(),
      form.value.description?.trim() || undefined
    )
    
    ElMessage.success('商品標籤新增成功')
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>