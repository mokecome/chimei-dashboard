<template>
  <el-dialog
    v-model="dialogVisible"
    title="複製用戶權限"
    width="600px"
    @close="handleClose"
  >
    <!-- 來源用戶信息 -->
    <div v-if="sourceUser" class="source-user-section">
      <h4 class="section-title">複製來源</h4>
      <div class="source-user-card">
        <div class="user-avatar">
          <el-avatar :size="48">
            {{ sourceUser.name?.charAt(0) || sourceUser.username.charAt(0).toUpperCase() }}
          </el-avatar>
        </div>
        <div class="user-info">
          <div class="user-name">{{ sourceUser.username }}</div>
          <div class="user-details">
            <span class="user-real-name">{{ sourceUser.name || '未設定姓名' }}</span>
            <el-tag :type="getRoleTagType(sourceUser.role.name)" size="small">
              {{ sourceUser.role.displayName }}
            </el-tag>
          </div>
          <div class="user-meta">
            {{ sourceUser.email }} | {{ sourceUser.department || '未設定部門' }}
          </div>
        </div>
      </div>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent="handleSubmit"
    >
      <!-- 新用戶基本信息 -->
      <div class="form-section">
        <h4 class="section-title">新用戶信息</h4>
        
        <el-form-item label="用戶名稱" prop="username">
          <el-input
            v-model="form.username"
            placeholder="請輸入用戶名稱"
            clearable
            @blur="validateUsername"
          />
        </el-form-item>
        
        <el-form-item label="郵箱地址" prop="email">
          <el-input
            v-model="form.email"
            type="email"
            placeholder="請輸入郵箱地址"
            clearable
            @blur="validateEmail"
          />
        </el-form-item>
        
        <el-form-item label="密碼" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="請輸入密碼"
            show-password
            clearable
          />
        </el-form-item>
        
        <el-form-item label="確認密碼" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="請再次輸入密碼"
            show-password
            clearable
          />
        </el-form-item>
      </div>
      
      <!-- 個人信息 -->
      <div class="form-section">
        <h4 class="section-title">個人信息（可選）</h4>
        
        <el-form-item label="姓名" prop="name">
          <el-input
            v-model="form.name"
            placeholder="請輸入姓名"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="部門" prop="department">
          <el-input
            v-model="form.department"
            placeholder="請輸入部門"
            clearable
          />
        </el-form-item>
      </div>
      
      <!-- 權限複製設定 -->
      <div class="permissions-section">
        <h4 class="section-title">權限複製設定</h4>
        
        <div class="permissions-preview">
          <div class="preview-header">
            <el-icon><Key /></el-icon>
            <span>將複製以下權限設定：</span>
          </div>
          
          <div class="permission-items">
            <div class="permission-item">
              <div class="permission-icon role">
                <el-icon><Crown /></el-icon>
              </div>
              <div class="permission-content">
                <div class="permission-title">用戶角色</div>
                <div class="permission-desc">{{ sourceUser?.role.displayName }}</div>
              </div>
            </div>
            
            <div class="permission-item">
              <div class="permission-icon modules">
                <el-icon><Grid /></el-icon>
              </div>
              <div class="permission-content">
                <div class="permission-title">功能模組權限</div>
                <div class="permission-desc">所有已配置的模組訪問權限</div>
              </div>
            </div>
            
            <div class="permission-item">
              <div class="permission-icon data">
                <el-icon><View /></el-icon>
              </div>
              <div class="permission-content">
                <div class="permission-title">數據訪問範圍</div>
                <div class="permission-desc">數據查看和操作權限範圍</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="copy-options">
          <el-checkbox v-model="copyOptions.includeCustomPermissions" checked disabled>
            包含自定義權限設定
          </el-checkbox>
          <el-checkbox v-model="copyOptions.inheritFutureChanges">
            繼承來源用戶的權限變更（實驗性功能）
          </el-checkbox>
        </div>
      </div>
      
      <!-- 提示信息 -->
      <div class="form-info">
        <el-icon><InfoFilled /></el-icon>
        <div class="info-content">
          <p><strong>權限複製說明：</strong></p>
          <ul>
            <li>新用戶將獲得與來源用戶完全相同的角色和權限</li>
            <li>僅複製權限設定，不包含個人數據和操作記錄</li>
            <li>新用戶的帳號、密碼、姓名、部門需要重新設定</li>
            <li>複製後的權限可以單獨調整和修改</li>
            <li>系統用戶的權限無法被複製</li>
          </ul>
        </div>
      </div>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="submitting"
          @click="handleSubmit"
        >
          複製並創建用戶
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  InfoFilled, 
  Key, 
  Crown, 
  Grid, 
  View 
} from '@element-plus/icons-vue'
import { useUsersStore } from '@/stores/users'
import { userService } from '@/services/user.service'
import type { FormInstance, FormRules } from 'element-plus'
import type { User, CreateUserRequest } from '@/types/user'

interface Props {
  modelValue: boolean
  sourceUser: User | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const usersStore = useUsersStore()

// 響應式狀態
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  name: '',
  department: ''
})

const copyOptions = ref({
  includeCustomPermissions: true,
  inheritFutureChanges: false
})

// 計算屬性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 表單驗證規則
const rules: FormRules = {
  username: [
    { required: true, message: '請輸入用戶名稱', trigger: 'blur' },
    { min: 3, max: 20, message: '用戶名稱長度在 3 到 20 個字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用戶名稱只能包含字母、數字和下劃線', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '請輸入郵箱地址', trigger: 'blur' },
    { type: 'email', message: '請輸入有效的郵箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 6, message: '密碼長度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '請再次輸入密碼', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.value.password) {
          callback(new Error('兩次輸入的密碼不一致'))
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
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    department: ''
  }
  
  copyOptions.value = {
    includeCustomPermissions: true,
    inheritFutureChanges: false
  }
  
  formRef.value?.clearValidate()
}

// 驗證用戶名唯一性
const validateUsername = async () => {
  if (!form.value.username.trim()) return
  
  try {
    const result = await userService.validateUsername(form.value.username)
    if (result.isDuplicate) {
      ElMessage.warning('用戶名稱已存在')
    }
  } catch (error) {
    console.error('驗證用戶名失敗:', error)
  }
}

// 驗證郵箱唯一性
const validateEmail = async () => {
  if (!form.value.email.trim()) return
  
  try {
    const result = await userService.validateEmail(form.value.email)
    if (result.isDuplicate) {
      ElMessage.warning('郵箱地址已存在')
    }
  } catch (error) {
    console.error('驗證郵箱失敗:', error)
  }
}

// 處理提交
const handleSubmit = async () => {
  if (!formRef.value || !props.sourceUser) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    // 準備複製數據
    const userData: Omit<CreateUserRequest, 'copyFromUserId'> = {
      username: form.value.username.trim(),
      email: form.value.email.trim(),
      password: form.value.password,
      name: form.value.name?.trim() || undefined,
      department: form.value.department?.trim() || undefined,
      roleId: props.sourceUser.role.id
    }
    
    // 複製用戶權限
    await usersStore.copyUser(props.sourceUser.id, userData)
    
    ElMessage.success('用戶複製成功')
    emit('success')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '複製用戶失敗')
  } finally {
    submitting.value = false
  }
}

// 處理關閉
const handleClose = () => {
  if (submitting.value) return
  
  resetForm()
  emit('update:modelValue', false)
}

// 獲取角色標籤類型
const getRoleTagType = (roleName: string) => {
  const typeMap: Record<string, any> = {
    admin: 'danger',
    manager: 'warning',
    operator: 'primary',
    viewer: 'info'
  }
  return typeMap[roleName] || 'info'
}
</script>

<style scoped>
.source-user-section {
  margin-bottom: 32px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.source-user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.user-details {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.user-real-name {
  font-size: 14px;
  color: #6b7280;
}

.user-meta {
  font-size: 13px;
  color: #9ca3af;
}

.form-section {
  margin-bottom: 32px;
}

.permissions-section {
  margin-bottom: 24px;
}

.permissions-preview {
  padding: 20px;
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 16px;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-weight: 500;
  color: #374151;
}

.permission-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.permission-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.permission-icon.role {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.permission-icon.modules {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.permission-icon.data {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.permission-content {
  flex: 1;
}

.permission-title {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 2px;
}

.permission-desc {
  font-size: 12px;
  color: #6b7280;
}

.copy-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background-color: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 8px;
  margin-top: 16px;
}

.form-info .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
  color: #0369a1;
}

.info-content {
  flex: 1;
  font-size: 14px;
  color: #0369a1;
  line-height: 1.5;
}

.info-content p {
  margin: 0 0 8px 0;
}

.info-content ul {
  margin: 0;
  padding-left: 20px;
}

.info-content li {
  margin-bottom: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}

:deep(.el-checkbox) {
  margin-bottom: 8px;
}

:deep(.el-checkbox:last-child) {
  margin-bottom: 0;
}
</style>