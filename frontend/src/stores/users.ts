import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  User, 
  CreateUserRequest, 
  UpdateUserRequest, 
  UserListQuery, 
  UserStats,
  UserOperation,
  UserRole,
  Module,
  Permission,
  SystemRole
} from '@/types/user'
import { userService } from '@/services/user.service'
import { ElMessage } from 'element-plus'

export const useUsersStore = defineStore('users', () => {
  // 狀態
  const users = ref<User[]>([])
  const roles = ref<UserRole[]>([])
  const modules = ref<Module[]>([])
  const operations = ref<UserOperation[]>([])
  const stats = ref<UserStats | null>(null)
  const loading = ref(false)
  const error = ref('')
  
  // 分頁狀態
  const pagination = ref({
    page: 1,
    limit: 10,
    total: 0
  })

  // 查詢狀態
  const query = ref<UserListQuery>({
    search: '',
    role: '',
    status: undefined,
    sortBy: 'createdAt',
    sortOrder: 'desc'
  })

  // 計算屬性
  const activeUsers = computed(() => 
    users.value.filter(user => user.status === 'active')
  )
  
  const inactiveUsers = computed(() => 
    users.value.filter(user => user.status === 'inactive')
  )
  
  const adminUsers = computed(() => 
    users.value.filter(user => user.role.name === 'admin')
  )

  const systemUsers = computed(() => 
    users.value.filter(user => user.isSystemUser)
  )

  const canDeleteUser = (user: User) => {
    // 系統用戶不能刪除
    if (user.isSystemUser) return false
    // admin 角色不能刪除（除非是其他 admin 用戶）
    if (user.role.name === 'admin') return false
    return true
  }

  const canEditUser = (user: User) => {
    // 系統用戶基本信息不能編輯
    return !user.isSystemUser
  }

  // 獲取用戶列表
  const fetchUsers = async (newQuery?: Partial<UserListQuery>) => {
    loading.value = true
    error.value = ''

    try {
      if (newQuery) {
        Object.assign(query.value, newQuery)
      }

      const queryParams = {
        ...query.value,
        page: pagination.value.page,
        limit: pagination.value.limit
      }

      const response = await userService.getUsers(queryParams)
      
      users.value = response.users
      pagination.value.total = response.total
      pagination.value.page = response.page
      pagination.value.limit = response.limit

    } catch (err: any) {
      error.value = err.message || '獲取用戶列表失敗'
      ElMessage.error('獲取用戶列表失敗')
    } finally {
      loading.value = false
    }
  }

  // 獲取角色列表
  const fetchRoles = async () => {
    try {
      roles.value = await userService.getRoles()
    } catch (err: any) {
      console.error('Failed to fetch roles:', err)
    }
  }

  // 獲取模組列表
  const fetchModules = async () => {
    try {
      modules.value = await userService.getModules()
    } catch (err: any) {
      console.error('Failed to fetch modules:', err)
    }
  }

  // 獲取統計信息
  const fetchStats = async () => {
    try {
      stats.value = await userService.getUserStats()
    } catch (err: any) {
      console.error('Failed to fetch stats:', err)
    }
  }

  // 獲取操作記錄
  const fetchOperations = async (limit = 50) => {
    try {
      operations.value = await userService.getUserOperations(limit)
    } catch (err: any) {
      console.error('Failed to fetch operations:', err)
    }
  }

  // 創建用戶
  const createUser = async (userData: CreateUserRequest) => {
    try {
      const newUser = await userService.createUser(userData)
      users.value.unshift(newUser)
      pagination.value.total += 1
      
      ElMessage.success('用戶創建成功')
      return newUser
    } catch (err: any) {
      ElMessage.error(err.message || '創建用戶失敗')
      throw err
    }
  }

  // 更新用戶
  const updateUser = async (id: string, userData: UpdateUserRequest) => {
    try {
      const updatedUser = await userService.updateUser(id, userData)
      const index = users.value.findIndex(user => user.id === id)
      if (index > -1) {
        users.value[index] = updatedUser
      }
      
      ElMessage.success('用戶更新成功')
      return updatedUser
    } catch (err: any) {
      ElMessage.error(err.message || '更新用戶失敗')
      throw err
    }
  }

  // 刪除用戶
  const deleteUser = async (id: string) => {
    try {
      await userService.deleteUser(id)
      users.value = users.value.filter(user => user.id !== id)
      pagination.value.total -= 1
      
      ElMessage.success('用戶刪除成功')
    } catch (err: any) {
      ElMessage.error(err.message || '刪除用戶失敗')
      throw err
    }
  }

  // 複製用戶
  const copyUser = async (sourceUserId: string, userData: Omit<CreateUserRequest, 'copyFromUserId'>) => {
    try {
      const newUser = await userService.copyUser(sourceUserId, userData)
      users.value.unshift(newUser)
      pagination.value.total += 1
      
      ElMessage.success('用戶複製成功')
      return newUser
    } catch (err: any) {
      ElMessage.error(err.message || '複製用戶失敗')
      throw err
    }
  }

  // 切換用戶狀態
  const toggleUserStatus = async (id: string, status: 'active' | 'inactive') => {
    try {
      const updatedUser = await userService.toggleUserStatus(id, status)
      const index = users.value.findIndex(user => user.id === id)
      if (index > -1) {
        users.value[index] = updatedUser
      }
      
      ElMessage.success(`用戶已${status === 'active' ? '啟用' : '停用'}`)
      return updatedUser
    } catch (err: any) {
      ElMessage.error(err.message || '切換用戶狀態失敗')
      throw err
    }
  }

  // 重置密碼
  const resetPassword = async (id: string, newPassword: string) => {
    try {
      await userService.resetPassword(id, newPassword)
      ElMessage.success('密碼重置成功')
    } catch (err: any) {
      ElMessage.error(err.message || '重置密碼失敗')
      throw err
    }
  }

  // 更新用戶權限
  const updateUserPermissions = async (id: string, permissions: Permission[]) => {
    try {
      await userService.updateUserPermissions(id, permissions)
      
      // 更新本地用戶數據
      const index = users.value.findIndex(user => user.id === id)
      if (index > -1) {
        users.value[index].permissions = permissions
      }
      
      ElMessage.success('權限更新成功')
    } catch (err: any) {
      ElMessage.error(err.message || '更新權限失敗')
      throw err
    }
  }

  // 批量操作
  const bulkOperation = async (operation: {
    type: 'activate' | 'deactivate' | 'delete'
    userIds: string[]
  }) => {
    try {
      const result = await userService.bulkOperation(operation)
      
      // 根據操作類型更新本地狀態
      if (operation.type === 'delete') {
        users.value = users.value.filter(user => !operation.userIds.includes(user.id))
        pagination.value.total -= result.successCount
      } else {
        const newStatus = operation.type === 'activate' ? 'active' : 'inactive'
        users.value.forEach(user => {
          if (operation.userIds.includes(user.id)) {
            user.status = newStatus
          }
        })
      }
      
      ElMessage.success(`批量操作完成：成功 ${result.successCount} 個`)
      return result
    } catch (err: any) {
      ElMessage.error(err.message || '批量操作失敗')
      throw err
    }
  }

  // 搜索用戶
  const searchUsers = (searchTerm: string) => {
    query.value.search = searchTerm
    pagination.value.page = 1
    fetchUsers()
  }

  // 篩選用戶
  const filterUsers = (filters: Partial<UserListQuery>) => {
    Object.assign(query.value, filters)
    pagination.value.page = 1
    fetchUsers()
  }

  // 重置篩選
  const resetFilters = () => {
    query.value = {
      search: '',
      role: '',
      status: undefined,
      sortBy: 'createdAt',
      sortOrder: 'desc'
    }
    pagination.value.page = 1
    fetchUsers()
  }

  // 刷新數據
  const refreshData = () => {
    fetchUsers()
    fetchStats()
    fetchOperations()
  }

  // 獲取模擬數據
  const getMockData = () => {
    // 角色數據
    roles.value = [
      {
        id: '1',
        name: 'admin',
        displayName: '系統管理員',
        description: '擁有所有權限的系統管理員',
        level: 100,
        isSystemRole: true
      },
      {
        id: '2', 
        name: 'manager',
        displayName: '部門主管',
        description: '可管理部門內容和查看所有數據',
        level: 80,
        isSystemRole: true
      },
      {
        id: '3',
        name: 'operator',
        displayName: '操作員',
        description: '可上傳文件和查看分析結果',
        level: 60,
        isSystemRole: true
      },
      {
        id: '4',
        name: 'viewer',
        displayName: '查看者',
        description: '僅可查看數據和報表',
        level: 20,
        isSystemRole: true
      }
    ]

    // 用戶數據
    users.value = [
      {
        id: 'admin',
        username: 'admin',
        email: 'admin@chimei.com',
        name: '系統管理員',
        department: 'IT部門',
        role: roles.value[0],
        status: 'active',
        permissions: [],
        createdAt: '2025-01-01 00:00:00',
        updatedAt: '2025-01-01 00:00:00',
        lastLoginAt: '2025-07-26 10:30:00',
        isSystemUser: true
      },
      {
        id: '2',
        username: 'manager01',
        email: 'manager01@chimei.com',
        name: '張主管',
        department: '品管部',
        role: roles.value[1],
        status: 'active',
        permissions: [],
        createdAt: '2025-01-15 09:00:00',
        updatedAt: '2025-07-25 16:20:00',
        lastLoginAt: '2025-07-25 16:20:00',
        isSystemUser: false
      },
      {
        id: '3',
        username: 'operator01',
        email: 'operator01@chimei.com',
        name: '李操作員',
        department: '客服部',
        role: roles.value[2],
        status: 'active',
        permissions: [],
        createdAt: '2025-02-01 10:30:00',
        updatedAt: '2025-07-24 14:45:00',
        lastLoginAt: '2025-07-24 14:45:00',
        isSystemUser: false
      },
      {
        id: '4',
        username: 'viewer01',
        email: 'viewer01@chimei.com',
        name: '王查看員',
        department: '業務部',
        role: roles.value[3],
        status: 'active',
        permissions: [],
        createdAt: '2025-02-15 14:20:00',
        updatedAt: '2025-07-23 11:10:00',
        lastLoginAt: '2025-07-23 11:10:00',
        isSystemUser: false
      },
      {
        id: '5',
        username: 'test_user',
        email: 'test@chimei.com',
        name: '測試用戶',
        department: '測試部',
        role: roles.value[3],
        status: 'inactive',
        permissions: [],
        createdAt: '2025-03-01 16:00:00',
        updatedAt: '2025-03-01 16:00:00',
        lastLoginAt: undefined,
        isSystemUser: false
      }
    ]

    // 統計數據
    stats.value = {
      totalUsers: users.value.length,
      activeUsers: users.value.filter(u => u.status === 'active').length,
      inactiveUsers: users.value.filter(u => u.status === 'inactive').length,
      adminUsers: users.value.filter(u => u.role.name === 'admin').length,
      recentLogins: 12,
      newUsersThisMonth: 3
    }

    // 操作記錄
    operations.value = [
      {
        id: '1',
        type: 'create',
        targetUserId: '5',
        targetUsername: 'test_user',
        operatorId: 'admin',
        operatorName: '系統管理員',
        timestamp: '2025-07-26 09:15:00',
        description: '創建新用戶'
      },
      {
        id: '2',
        type: 'update',
        targetUserId: '3',
        targetUsername: 'operator01',
        operatorId: 'admin',
        operatorName: '系統管理員',
        timestamp: '2025-07-25 14:30:00',
        description: '更新用戶權限'
      },
      {
        id: '3',
        type: 'login',
        targetUserId: '2',
        targetUsername: 'manager01',
        operatorId: '2',
        operatorName: '張主管',
        timestamp: '2025-07-25 08:45:00',
        description: '用戶登入'
      }
    ]

    // 分頁信息
    pagination.value = {
      page: 1,
      limit: 10,
      total: users.value.length
    }

    loading.value = false
  }

  return {
    // 狀態
    users: readonly(users),
    roles: readonly(roles),
    modules: readonly(modules),
    operations: readonly(operations),
    stats: readonly(stats),
    loading: readonly(loading),
    error: readonly(error),
    pagination: readonly(pagination),
    query: readonly(query),
    
    // 計算屬性
    activeUsers,
    inactiveUsers,
    adminUsers,
    systemUsers,
    canDeleteUser,
    canEditUser,
    
    // 方法
    fetchUsers,
    fetchRoles,
    fetchModules,
    fetchStats,
    fetchOperations,
    createUser,
    updateUser,
    deleteUser,
    copyUser,
    toggleUserStatus,
    resetPassword,
    updateUserPermissions,
    bulkOperation,
    searchUsers,
    filterUsers,
    resetFilters,
    refreshData,
    getMockData
  }
})