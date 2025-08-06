<template>
  <el-dialog
    v-model="dialogVisible"
    title="編輯用戶"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent="handleSubmit"
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <h4 class="section-title">基本信息</h4>
        
        <el-form-item label="用戶名稱" prop="username">
          <el-input
            v-model="form.username"
            placeholder="請輸入用戶名稱"
            :disabled="user?.isSystemUser"
            clearable
            @blur="validateUsername"
          />
        </el-form-item>
        
        <el-form-item label="郵箱地址" prop="email">
          <el-input
            v-model="form.email"
            type="email"
            placeholder="請輸入郵箱地址"
            :disabled="user?.isSystemUser"
            clearable
            @blur="validateEmail"
          />
        </el-form-item>
      </div>
      
      <!-- 個人信息 -->
      <div class="form-section">
        <h4 class="section-title">個人信息</h4>
        
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
      
      <!-- 狀態和權限 -->
      <div class="form-section">
        <h4 class="section-title">狀態和權限</h4>
        
        <el-form-item label="用戶狀態" prop="status">
          <el-radio-group v-model="form.status" :disabled="user?.isSystemUser">
            <el-radio value="active">啟用</el-radio>
            <el-radio value="inactive">停用</el-radio>
            <el-radio value="suspended">暫停</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="角色" prop="roleId">
          <el-select
            v-model="form.roleId"
            placeholder="選擇用戶角色"
            style="width: 100%"
            :disabled="user?.isSystemUser"
          >
            <el-option
              v-for="role in usersStore.roles"
              :key="role.id"
              :label="role.displayName"
              :value="role.id"
            >
              <div class="role-option">
                <span class="role-name">{{ role.displayName }}</span>
                <span class="role-desc">{{ role.description }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </div>
      
      <!-- 密碼重置 -->
      <div class="form-section">
        <h4 class="section-title">密碼設定</h4>
        
        <el-form-item>
          <el-checkbox v-model="resetPassword">
            重置密碼
          </el-checkbox>
        </el-form-item>
        
        <el-form-item v-if="resetPassword" label="新密碼" prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            placeholder="請輸入新密碼"
            show-password
            clearable
          />
        </el-form-item>
        
        <el-form-item v-if="resetPassword" label="確認密碼" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="請再次輸入新密碼"
            show-password
            clearable
          />
        </el-form-item>
      </div>
      
      <!-- 用戶信息 -->
      <div v-if="user" class="user-info-section">
        <h4 class="section-title">用戶信息</h4>
        
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">創建時間：</span>
            <span class="info-value">{{ formatDate(user.createdAt) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">最後更新：</span>
            <span class="info-value">{{ formatDate(user.updatedAt) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">最後登入：</span>
            <span class="info-value">{{ user.lastLoginAt ? formatDate(user.lastLoginAt) : '從未登入' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">用戶類型：</span>
            <span class="info-value">
              {{ user.isSystemUser ? '系統用戶' : '普通用戶' }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- 提示信息 -->
      <div class="form-info">
        <el-icon><InfoFilled /></el-icon>
        <div class="info-content">
          <p v-if="user?.isSystemUser"><strong>系統用戶：</strong></p>
          <ul v-if="user?.isSystemUser">
            <li>系統用戶的基本信息和權限不能修改</li>
            <li>只能修改個人信息如姓名和部門</li>
          </ul>
          <ul v-else>
            <li>修改後的信息將立即生效</li>
            <li>狀態變更會影響用戶的登入權限</li>
            <li>角色變更會影響用戶的功能權限</li>
            <li>如選擇重置密碼，請確保新密碼安全性</li>
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
          更新用戶
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { useUsersStore } from '@/stores/users'
import { userService } from '@/services/user.service'
import type { FormInstance, FormRules } from 'element-plus'
import type { User, UpdateUserRequest, UserStatus } from '@/types/user'

interface Props {
  modelValue: boolean
  user: User | null
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
const resetPassword = ref(false)

const form = ref({
  username: '',
  email: '',
  name: '',
  department: '',
  status: 'active' as UserStatus,
  roleId: '',
  newPassword: '',
  confirmPassword: ''
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
  status: [
    { required: true, message: '請選擇用戶狀態', trigger: 'change' }
  ],
  roleId: [
    { required: true, message: '請選擇用戶角色', trigger: 'change' }
  ],
  newPassword: [
    {
      validator: (rule, value, callback) => {
        if (resetPassword.value) {
          if (!value) {
            callback(new Error('請輸入新密碼'))
          } else if (value.length < 6) {
            callback(new Error('密碼長度至少6位'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    {
      validator: (rule, value, callback) => {
        if (resetPassword.value) {
          if (!value) {
            callback(new Error('請再次輸入新密碼'))
          } else if (value !== form.value.newPassword) {
            callback(new Error('兩次輸入的密碼不一致'))
          } else {
            callback()
          }
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
  if (visible && props.user) {
    loadUserData()
  }
})

// 監聽用戶變化
watch(() => props.user, (user) => {
  if (user && dialogVisible.value) {
    loadUserData()
  }
})

// 監聽重置密碼選項
watch(resetPassword, (value) => {
  if (!value) {
    form.value.newPassword = ''
    form.value.confirmPassword = ''
  }
  // 重新驗證表單
  formRef.value?.clearValidate(['newPassword', 'confirmPassword'])
})

// 加載用戶數據
const loadUserData = () => {
  if (!props.user) return
  
  form.value = {
    username: props.user.username,
    email: props.user.email,
    name: props.user.name || '',
    department: props.user.department || '',
    status: props.user.status,
    roleId: props.user.role.id,
    newPassword: '',
    confirmPassword: ''
  }
  
  resetPassword.value = false
  formRef.value?.clearValidate()
}

// 驗證用戶名唯一性
const validateUsername = async () => {
  if (!form.value.username.trim() || !props.user) return
  
  // 如果用戶名沒有變化，跳過驗證
  if (form.value.username === props.user.username) return
  
  try {
    const result = await userService.validateUsername(form.value.username, props.user.id)
    if (result.isDuplicate) {
      ElMessage.warning('用戶名稱已存在')
    }
  } catch (error) {
    console.error('驗證用戶名失敗:', error)
  }
}

// 驗證郵箱唯一性
const validateEmail = async () => {
  if (!form.value.email.trim() || !props.user) return
  
  // 如果郵箱沒有變化，跳過驗證
  if (form.value.email === props.user.email) return
  
  try {
    const result = await userService.validateEmail(form.value.email, props.user.id)
    if (result.isDuplicate) {
      ElMessage.warning('郵箱地址已存在')
    }
  } catch (error) {
    console.error('驗證郵箱失敗:', error)
  }
}

// 處理提交
const handleSubmit = async () => {
  if (!formRef.value || !props.user) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    // 準備更新數據
    const updateData: UpdateUserRequest = {
      name: form.value.name?.trim() || undefined,
      department: form.value.department?.trim() || undefined
    }
    
    // 非系統用戶可以修改更多信息
    if (!props.user.isSystemUser) {
      updateData.status = form.value.status
      updateData.roleId = form.value.roleId
    }
    
    // 更新用戶基本信息
    await usersStore.updateUser(props.user.id, updateData)
    
    // 如果需要重置密碼
    if (resetPassword.value && form.value.newPassword) {
      await usersStore.resetPassword(props.user.id, form.value.newPassword)
    }
    
    ElMessage.success('用戶更新成功')
    emit('success')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '更新用戶失敗')
  } finally {
    submitting.value = false
  }
}

// 處理關閉
const handleClose = () => {
  if (submitting.value) return
  
  resetPassword.value = false
  emit('update:modelValue', false)
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-TW')
}
</script>

<style scoped>
.form-section {
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

.role-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.role-name {
  font-weight: 500;
  color: #1f2937;
}

.role-desc {
  font-size: 12px;
  color: #6b7280;
}

.user-info-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 80px;
}

.info-value {
  color: #1f2937;
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

:deep(.el-select .el-input) {
  width: 100%;
}
</style>