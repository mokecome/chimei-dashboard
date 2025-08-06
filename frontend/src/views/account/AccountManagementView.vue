<template>
  <div class="account-management-page">
    <!-- Page Header -->
    <header class="page-header">
      <div class="header-content">
        <div>
          <h1 class="page-title">權限管理</h1>
          <p class="page-description">管理使用者帳戶、角色與權限設定</p>
        </div>
        <div class="header-actions">
          <el-button type="danger" @click="createAccount">
            新增帳號
          </el-button>
        </div>
      </div>
    </header>

    <!-- Content -->
    <div class="account-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <el-icon class="loading-spinner"><Loading /></el-icon>
        載入中...
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <el-icon class="error-icon"><Warning /></el-icon>
        {{ error }}
      </div>
      
      <!-- Accounts Section -->
      <div v-else class="account-section">
        <div class="accounts-list">
          <!-- All Users in Single List -->
          <div 
            v-for="account in users" 
            :key="account.id"
            class="account-item"
          >
            <span class="account-name">{{ account.name || account.email }}</span>
            <div class="account-actions">
              <button 
                class="action-button"
                @click="copyAccount(account)"
              >
                複製
              </button>
              <button 
                class="action-button"
                @click="editPermissions(account)"
              >
                權限設定
              </button>
              <button 
                class="action-button"
                @click="deleteAccount(account)"
                :disabled="account.email === 'admin@chimei.com'"
              >
                刪除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userService } from '@/services/user.service'
import type { User } from '@/types/user'
import { Loading, Warning } from '@element-plus/icons-vue'

// 響應式數據
const users = ref<User[]>([])
const loading = ref(false)
const error = ref('')

// No need for role-based grouping since we're showing all users in a single list

// 獲取用戶數據
const fetchUsers = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await userService.getUsers({
      page: 1,
      limit: 100 // 獲取所有用戶
    })
    users.value = response.users
  } catch (err: any) {
    error.value = err.message || '獲取用戶列表失敗'
    ElMessage.error('載入用戶數據失敗')
  } finally {
    loading.value = false
  }
}

// Action handlers
const createAccount = () => {
  ElMessage.info('新增帳號功能')
}

const copyAccount = (account: User) => {
  ElMessage.success(`複製帳號: ${account.name}`)
}

const editPermissions = (account: User) => {
  ElMessage.info(`權限設定: ${account.name}`)
}

const deleteAccount = async (account: User) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除帳號 ${account.name} (${account.email}) 嗎？`,
      '刪除確認',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // Call the delete API
    await userService.deleteUser(account.id)
    
    // Remove the account from the users list
    users.value = users.value.filter(u => u.id !== account.id)
    
    ElMessage.success('帳號已刪除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete account:', error)
      ElMessage.error('刪除帳號失敗')
    }
  }
}

// Lifecycle
onMounted(async () => {
  await fetchUsers()
})
</script>

<style scoped>
.account-management-page {
  min-height: 100vh;
  background-color: #f3f4f6;
  font-family: 'Noto Sans TC', sans-serif;
}

/* Page Header */
.page-header {
  background: white;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.page-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0.25rem 0 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

/* Content */
.account-content {
  padding: 2rem;
}

.account-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.accounts-list {
  padding: 1.5rem;
}

.account-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
  transition: all 0.3s ease;
}

.account-item:last-child {
  border-bottom: none;
}

.account-item:hover {
  background-color: #f9fafb;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  border-radius: 8px;
}

.account-name {
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
}

.account-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-button {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.action-button:hover:not(:disabled) {
  background-color: #fecaca;
  border-color: #dc2626;
}

.action-button:disabled {
  opacity: 0.5;
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
  .account-content {
    padding: 1rem;
  }
  
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .account-item {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }
  
  .account-actions {
    justify-content: center;
  }
}
</style>