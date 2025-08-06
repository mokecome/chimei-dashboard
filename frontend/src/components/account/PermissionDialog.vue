<template>
  <el-dialog
    v-model="dialogVisible"
    title="權限設定"
    width="800px"
    @close="handleClose"
  >
    <!-- 用戶信息 -->
    <div v-if="user" class="user-header">
      <div class="user-info">
        <el-avatar :size="48">
          {{ user.name?.charAt(0) || user.username.charAt(0).toUpperCase() }}
        </el-avatar>
        <div class="user-details">
          <div class="user-name">{{ user.username }}</div>
          <div class="user-meta">
            <span>{{ user.name || '未設定姓名' }}</span>
            <el-tag :type="getRoleTagType(user.role.name)" size="small">
              {{ user.role.displayName }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <div class="permission-summary">
        <div class="summary-item">
          <span class="summary-label">總權限數：</span>
          <span class="summary-value">{{ totalPermissions }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">已啟用：</span>
          <span class="summary-value">{{ enabledPermissions }}</span>
        </div>
      </div>
    </div>

    <!-- 權限設定區域 -->
    <div v-loading="loading" class="permissions-container">
      <!-- 角色基礎權限 -->
      <div class="role-permissions-section">
        <div class="section-header">
          <div class="section-title">
            <el-icon><Crown /></el-icon>
            <span>角色基礎權限</span>
          </div>
          <el-tag :type="getRoleTagType(user?.role.name || '')" size="small">
            {{ user?.role.displayName }}
          </el-tag>
        </div>
        
        <div class="role-description">
          {{ user?.role.description }}
        </div>
        
        <div class="role-permissions-grid">
          <div 
            v-for="module in systemModules" 
            :key="module.id"
            class="module-card"
            :class="{ disabled: !hasRoleAccess(module.id) }"
          >
            <div class="module-header">
              <div class="module-info">
                <el-icon><component :is="getModuleIcon(module.id)" /></el-icon>
                <span class="module-name">{{ module.displayName }}</span>
              </div>
              <el-switch
                :model-value="hasRoleAccess(module.id)"
                disabled
                size="small"
              />
            </div>
            <div class="module-description">{{ module.description }}</div>
          </div>
        </div>
      </div>

      <!-- 自定義權限設定 -->
      <div class="custom-permissions-section">
        <div class="section-header">
          <div class="section-title">
            <el-icon><Setting /></el-icon>
            <span>自定義權限設定</span>
          </div>
          <el-button 
            size="small" 
            @click="resetPermissions"
            :disabled="user?.isSystemUser"
          >
            重置為角色默認
          </el-button>
        </div>
        
        <div class="permissions-grid">
          <div 
            v-for="module in systemModules" 
            :key="module.id"
            class="permission-module"
          >
            <div class="module-title">
              <el-icon><component :is="getModuleIcon(module.id)" /></el-icon>
              <span>{{ module.displayName }}</span>
              <el-switch
                :model-value="isModuleEnabled(module.id)"
                @change="(value) => toggleModule(module.id, value)"
                :disabled="user?.isSystemUser || !hasRoleAccess(module.id)"
                size="small"
              />
            </div>
            
            <div class="module-resources">
              <div 
                v-for="resource in module.resources" 
                :key="resource.id"
                class="resource-group"
              >
                <div class="resource-title">{{ resource.displayName }}</div>
                <div class="resource-actions">
                  <el-checkbox-group
                    :model-value="getResourceActions(module.id, resource.id)"
                    @change="(actions) => updateResourceActions(module.id, resource.id, actions)"
                    :disabled="user?.isSystemUser || !isModuleEnabled(module.id)"
                  >
                    <el-checkbox
                      v-for="action in resource.actions"
                      :key="action"
                      :value="action"
                      size="small"
                    >
                      {{ getActionText(action) }}
                    </el-checkbox>
                  </el-checkbox-group>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系統用戶提示 -->
      <div v-if="user?.isSystemUser" class="system-user-notice">
        <el-icon><WarningFilled /></el-icon>
        <div class="notice-content">
          <p><strong>系統用戶權限說明：</strong></p>
          <p>此用戶為系統內建用戶，權限由系統自動管理，無法手動修改。如需調整權限，請聯繫系統管理員。</p>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="saving"
          :disabled="user?.isSystemUser"
          @click="handleSave"
        >
          保存權限
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Crown, 
  Setting, 
  WarningFilled,
  House,
  TrendCharts,
  Database,
  Tags,
  UserFilled
} from '@element-plus/icons-vue'
import { useUsersStore } from '@/stores/users'
import type { User, Permission, Module, PermissionAction, SystemModule } from '@/types/user'

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
const loading = ref(false)
const saving = ref(false)
const permissions = ref<Permission[]>([])

// 系統模組定義
const systemModules = ref<Module[]>([
  {
    id: 'dashboard',
    name: 'dashboard',
    displayName: '營運總覽',
    description: '查看系統總覽和關鍵指標',
    resources: [
      {
        id: 'overview',
        name: 'overview',
        displayName: '總覽頁面',
        description: '查看總覽頁面',
        actions: ['read']
      },
      {
        id: 'charts',
        name: 'charts',
        displayName: '圖表數據',
        description: '查看和匯出圖表數據',
        actions: ['read', 'create']
      }
    ]
  },
  {
    id: 'analysis',
    name: 'analysis',
    displayName: '深度分析',
    description: '進行數據分析和生成報告',
    resources: [
      {
        id: 'reports',
        name: 'reports',
        displayName: '分析報告',
        description: '查看、創建和管理分析報告',
        actions: ['create', 'read', 'update', 'delete']
      },
      {
        id: 'data',
        name: 'data',
        displayName: '分析數據',
        description: '訪問分析用的原始數據',
        actions: ['read', 'create']
      }
    ]
  },
  {
    id: 'datasource',
    name: 'datasource',
    displayName: '匯入資料',
    description: '管理數據來源和文件上傳',
    resources: [
      {
        id: 'files',
        name: 'files',
        displayName: '文件管理',
        description: '上傳、查看和管理文件',
        actions: ['create', 'read', 'update', 'delete']
      },
      {
        id: 'processing',
        name: 'processing',
        displayName: '數據處理',
        description: '啟動和監控數據處理任務',
        actions: ['create', 'read']
      }
    ]
  },
  {
    id: 'label_setting',
    name: 'label_setting',
    displayName: '分類設定',
    description: '管理標籤和分類設定',
    resources: [
      {
        id: 'labels',
        name: 'labels',
        displayName: '標籤管理',
        description: '創建、編輯和刪除標籤',
        actions: ['create', 'read', 'update', 'delete']
      },
      {
        id: 'categories',
        name: 'categories',
        displayName: '分類管理',
        description: '管理標籤分類',
        actions: ['create', 'read', 'update', 'delete']
      }
    ]
  },
  {
    id: 'account',
    name: 'account',
    displayName: '權限管理',
    description: '管理用戶帳戶和權限',
    resources: [
      {
        id: 'users',
        name: 'users',
        displayName: '用戶管理',
        description: '創建、編輯和刪除用戶',
        actions: ['create', 'read', 'update', 'delete']
      },
      {
        id: 'permissions',
        name: 'permissions',
        displayName: '權限設定',
        description: '管理用戶權限和角色',
        actions: ['read', 'update']
      }
    ]
  }
])

// 計算屬性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const totalPermissions = computed(() => {
  return systemModules.value.reduce((total, module) => {
    return total + module.resources.reduce((moduleTotal, resource) => {
      return moduleTotal + resource.actions.length
    }, 0)
  }, 0)
})

const enabledPermissions = computed(() => {
  return permissions.value.reduce((total, permission) => {
    return total + permission.actions.filter(action => action.allowed).length
  }, 0)
})

// 監聽對話框顯示狀態
watch(dialogVisible, (visible) => {
  if (visible && props.user) {
    loadUserPermissions()
  }
})

// 生命週期
onMounted(() => {
  if (dialogVisible.value && props.user) {
    loadUserPermissions()
  }
})

// 加載用戶權限
const loadUserPermissions = async () => {
  if (!props.user) return
  
  loading.value = true
  
  try {
    // 使用模擬數據
    permissions.value = generateMockPermissions()
    
    // 實際環境中使用：
    // permissions.value = await userService.getUserPermissions(props.user.id)
  } catch (error) {
    ElMessage.error('加載權限失敗')
  } finally {
    loading.value = false
  }
}

// 生成模擬權限數據
const generateMockPermissions = (): Permission[] => {
  if (!props.user) return []
  
  const mockPermissions: Permission[] = []
  
  systemModules.value.forEach(module => {
    module.resources.forEach(resource => {
      const actions: PermissionAction[] = resource.actions.map(action => ({
        action: action as any,
        allowed: hasRoleAccess(module.id) && getDefaultActionPermission(props.user!.role.name, module.id, action)
      }))
      
      mockPermissions.push({
        id: `${module.id}_${resource.id}`,
        module: module.id,
        resource: resource.id,
        actions
      })
    })
  })
  
  return mockPermissions
}

// 獲取默認操作權限
const getDefaultActionPermission = (roleName: string, moduleId: string, action: string): boolean => {
  const rolePermissions: Record<string, Record<string, string[]>> = {
    admin: {
      dashboard: ['read', 'create'],
      analysis: ['create', 'read', 'update', 'delete'],
      datasource: ['create', 'read', 'update', 'delete'],
      label_setting: ['create', 'read', 'update', 'delete'],
      account: ['create', 'read', 'update', 'delete']
    },
    manager: {
      dashboard: ['read', 'create'],
      analysis: ['create', 'read', 'update'],
      datasource: ['create', 'read', 'update'],
      label_setting: ['create', 'read', 'update'],
      account: ['read']
    },
    operator: {
      dashboard: ['read'],
      analysis: ['read'],
      datasource: ['create', 'read'],
      label_setting: ['read'],
      account: []
    },
    viewer: {
      dashboard: ['read'],
      analysis: ['read'],
      datasource: ['read'],
      label_setting: ['read'],
      account: []
    }
  }
  
  return rolePermissions[roleName]?.[moduleId]?.includes(action) || false
}

// 檢查角色是否有模組訪問權限
const hasRoleAccess = (moduleId: string): boolean => {
  if (!props.user) return false
  
  const roleAccess: Record<string, string[]> = {
    admin: ['dashboard', 'analysis', 'datasource', 'label_setting', 'account'],
    manager: ['dashboard', 'analysis', 'datasource', 'label_setting', 'account'],
    operator: ['dashboard', 'analysis', 'datasource', 'label_setting'],
    viewer: ['dashboard', 'analysis', 'datasource', 'label_setting']
  }
  
  return roleAccess[props.user.role.name]?.includes(moduleId) || false
}

// 檢查模組是否啟用
const isModuleEnabled = (moduleId: string): boolean => {
  return permissions.value.some(permission => 
    permission.module === moduleId && 
    permission.actions.some(action => action.allowed)
  )
}

// 切換模組狀態
const toggleModule = (moduleId: string, enabled: boolean) => {
  const module = systemModules.value.find(m => m.id === moduleId)
  if (!module) return
  
  module.resources.forEach(resource => {
    const permission = permissions.value.find(p => 
      p.module === moduleId && p.resource === resource.id
    )
    
    if (permission) {
      permission.actions.forEach(action => {
        action.allowed = enabled && getDefaultActionPermission(props.user!.role.name, moduleId, action.action)
      })
    }
  })
}

// 獲取資源操作權限
const getResourceActions = (moduleId: string, resourceId: string): string[] => {
  const permission = permissions.value.find(p => 
    p.module === moduleId && p.resource === resourceId
  )
  
  return permission?.actions.filter(action => action.allowed).map(action => action.action) || []
}

// 更新資源操作權限
const updateResourceActions = (moduleId: string, resourceId: string, actions: string[]) => {
  const permission = permissions.value.find(p => 
    p.module === moduleId && p.resource === resourceId
  )
  
  if (permission) {
    permission.actions.forEach(action => {
      action.allowed = actions.includes(action.action)
    })
  }
}

// 重置權限
const resetPermissions = () => {
  permissions.value = generateMockPermissions()
  ElMessage.success('權限已重置為角色默認設定')
}

// 保存權限
const handleSave = async () => {
  if (!props.user) return
  
  saving.value = true
  
  try {
    await usersStore.updateUserPermissions(props.user.id, permissions.value)
    
    ElMessage.success('權限保存成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error.message || '保存權限失敗')
  } finally {
    saving.value = false
  }
}

// 處理關閉
const handleClose = () => {
  if (saving.value) return
  
  emit('update:modelValue', false)
}

// 輔助方法
const getRoleTagType = (roleName: string) => {
  const typeMap: Record<string, any> = {
    admin: 'danger',
    manager: 'warning',
    operator: 'primary',
    viewer: 'info'
  }
  return typeMap[roleName] || 'info'
}

const getModuleIcon = (moduleId: string) => {
  const iconMap: Record<string, any> = {
    dashboard: House,
    analysis: TrendCharts,
    datasource: Database,
    label_setting: Tags,
    account: UserFilled
  }
  return iconMap[moduleId] || House
}

const getActionText = (action: string) => {
  const textMap: Record<string, string> = {
    create: '新增',
    read: '查看',
    update: '編輯',
    delete: '刪除'
  }
  return textMap[action] || action
}
</script>

<style scoped>
.user-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  margin-bottom: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #6b7280;
}

.permission-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-label {
  font-size: 14px;
  color: #6b7280;
}

.summary-value {
  font-weight: 600;
  color: #1f2937;
}

.permissions-container {
  min-height: 400px;
}

.role-permissions-section,
.custom-permissions-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.role-description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.role-permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.module-card {
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.module-card.disabled {
  background: #f9fafb;
  opacity: 0.6;
}

.module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.module-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-name {
  font-weight: 500;
  color: #1f2937;
}

.module-description {
  font-size: 13px;
  color: #6b7280;
}

.permissions-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.permission-module {
  padding: 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.module-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.module-resources {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.resource-group {
  padding: 16px;
  background: #f9fafb;
  border-radius: 6px;
}

.resource-title {
  font-weight: 500;
  color: #374151;
  margin-bottom: 12px;
}

.resource-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.system-user-notice {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 8px;
  margin-top: 16px;
}

.system-user-notice .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
  color: #d97706;
}

.notice-content {
  flex: 1;
  font-size: 14px;
  color: #92400e;
  line-height: 1.5;
}

.notice-content p {
  margin: 0 0 8px 0;
}

.notice-content p:last-child {
  margin-bottom: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

:deep(.el-checkbox) {
  margin-right: 0;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .user-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .role-permissions-grid {
    grid-template-columns: 1fr;
  }
  
  .resource-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  :deep(.el-checkbox-group) {
    flex-direction: column;
    gap: 8px;
  }
}
</style>