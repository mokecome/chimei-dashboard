<template>
  <el-dialog
    v-model="dialogVisible"
    title="新增帳號"
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
      
      <!-- 權限設定 -->
      <div class="form-section">
        <h4 class="section-title">權限設定</h4>
        
        <el-form-item label="角色" prop="roleId">
          <el-select
            v-model="form.roleId"
            placeholder="選擇用戶角色"
            style="width: 100%"
            @change="handleRoleChange"
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
        
        <!-- 複製權限選項 -->
        <el-form-item>
          <el-checkbox v-model="copyFromExisting">
            從現有用戶複製權限設定
          </el-checkbox>
        </el-form-item>
        
        <el-form-item v-if="copyFromExisting" label="複製來源" prop="copyFromUserId">
          <el-select
            v-model="form.copyFromUserId"
            placeholder="選擇要複製權限的用戶"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="`${user.username} (${user.name || ''})`"
              :value="user.id"
            >
              <div class="user-option">
                <span class="user-name">{{ user.username }}</span>
                <span class="user-role">{{ user.role.displayName }}</span>
                <span class="user-desc">{{ user.name || '' }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </div>
      
      <!-- 提示信息 -->
      <div class="form-info">
        <el-icon><InfoFilled /></el-icon>
        <div class="info-content">
          <p><strong>注意事項：</strong></p>
          <ul>
            <li>用戶名稱和郵箱地址必須唯一</li>
            <li>密碼長度至少6位，建議包含數字和字母</li>
            <li>新用戶創建後默認為啟用狀態</li>
            <li>如選擇複製權限，將複製目標用戶的所有權限設定</li>
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
          創建用戶
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
import type { CreateUserRequest, User } from '@/types/user'

interface Props {
  modelValue: boolean
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
const copyFromExisting = ref(false)

const form = ref<CreateUserRequest & { confirmPassword: string }>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  name: '',
  department: '',
  roleId: '',
  copyFromUserId: ''
})

// 計算屬性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const availableUsers = computed(() => 
  usersStore.users.filter(user => !user.isSystemUser)
)

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
  ],
  roleId: [
    { required: true, message: '請選擇用戶角色', trigger: 'change' }
  ],
  copyFromUserId: [
    {
      validator: (rule, value, callback) => {
        if (copyFromExisting.value && !value) {
          callback(new Error('請選擇要複製權限的用戶'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 監聽對話框顯示狀態
watch(dialogVisible, (visible) => {
  if (visible) {
    resetForm()
  }
})

// 監聽複製權限選項
watch(copyFromExisting, (value) => {
  if (!value) {
    form.value.copyFromUserId = ''
  }
  // 重新驗證表單
  formRef.value?.clearValidate('copyFromUserId')
})

// 重置表單
const resetForm = () => {
  form.value = {
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    department: '',
    roleId: '',
    copyFromUserId: ''
  }
  copyFromExisting.value = false
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

// 處理角色變化
const handleRoleChange = (roleId: string) => {
  // 可以根據角色自動設置一些默認權限
  console.log('角色變化:', roleId)
}

// 處理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    // 準備提交數據
    const userData: CreateUserRequest = {
      username: form.value.username.trim(),
      email: form.value.email.trim(),
      password: form.value.password,
      name: form.value.name?.trim() || undefined,
      department: form.value.department?.trim() || undefined,
      roleId: form.value.roleId,
      copyFromUserId: copyFromExisting.value ? form.value.copyFromUserId : undefined
    }
    
    // 創建用戶
    if (copyFromExisting.value && form.value.copyFromUserId) {
      // 複製用戶權限
      const { copyFromUserId, ...createData } = userData
      await usersStore.copyUser(copyFromUserId!, createData)
    } else {
      // 直接創建用戶
      await usersStore.createUser(userData)
    }
    
    ElMessage.success('用戶創建成功')
    emit('success')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '創建用戶失敗')
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

.user-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-weight: 500;
  color: #1f2937;
}

.user-role {
  font-size: 12px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 2px 6px;
  border-radius: 4px;
}

.user-desc {
  font-size: 12px;
  color: #6b7280;
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