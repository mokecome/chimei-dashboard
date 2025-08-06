import type { 
  User, 
  CreateUserRequest, 
  UpdateUserRequest, 
  UserListQuery, 
  UserStats,
  UserOperation,
  PasswordChangeRequest,
  UserRole,
  Module,
  Permission
} from '@/types/user'
import api from './api'

class UserService {
  private baseURL = '/users'

  // 獲取用戶列表
  async getUsers(query: UserListQuery = {}): Promise<{
    users: User[]
    total: number
    page: number
    limit: number
  }> {
    try {
      const params = {
        page: query.page || 1,
        page_size: query.limit || 20,
        ...(query.role && { role: query.role }),
        ...(query.search && { search: query.search }),
        ...(query.active !== undefined && { active_only: query.active })
      }
      
      const response = await api.get(`${this.baseURL}/`, { params })
      
      // 適配後端響應格式
      return {
        users: response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.page_size || 20
      }
    } catch (error) {
      console.error('Failed to fetch users:', error)
      throw error
    }
  }

  // 獲取單個用戶
  async getUser(id: string): Promise<User> {
    try {
      const response = await api.get(`${this.baseURL}/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch user:', error)
      throw error
    }
  }

  // 創建用戶
  async createUser(data: CreateUserRequest): Promise<User> {
    try {
      const response = await api.post(this.baseURL, data)
      return response.data
    } catch (error) {
      console.error('Failed to create user:', error)
      throw error
    }
  }

  // 更新用戶
  async updateUser(id: string, data: UpdateUserRequest): Promise<User> {
    try {
      const response = await api.put(`${this.baseURL}/${id}`, data)
      return response.data
    } catch (error) {
      console.error('Failed to update user:', error)
      throw error
    }
  }

  // 刪除用戶
  async deleteUser(id: string): Promise<void> {
    try {
      await api.delete(`${this.baseURL}/${id}`)
    } catch (error) {
      console.error('Failed to delete user:', error)
      throw error
    }
  }

  // 複製用戶權限
  async copyUser(sourceUserId: string, userData: Omit<CreateUserRequest, 'copyFromUserId'>): Promise<User> {
    try {
      const response = await api.post(`${this.baseURL}/copy`, {
        ...userData,
        copyFromUserId: sourceUserId
      })
      return response.data
    } catch (error) {
      console.error('Failed to copy user:', error)
      throw error
    }
  }

  // 切換用戶狀態
  async toggleUserStatus(id: string, status: 'active' | 'inactive'): Promise<User> {
    try {
      const response = await api.patch(`${this.baseURL}/${id}/status`, { status })
      return response.data
    } catch (error) {
      console.error('Failed to toggle user status:', error)
      throw error
    }
  }

  // 重置用戶密碼
  async resetPassword(id: string, newPassword: string): Promise<void> {
    try {
      await api.post(`${this.baseURL}/${id}/reset-password`, { password: newPassword })
    } catch (error) {
      console.error('Failed to reset password:', error)
      throw error
    }
  }

  // 修改密碼
  async changePassword(id: string, data: PasswordChangeRequest): Promise<void> {
    try {
      await api.post(`${this.baseURL}/${id}/change-password`, data)
    } catch (error) {
      console.error('Failed to change password:', error)
      throw error
    }
  }

  // 獲取用戶統計
  async getUserStats(): Promise<UserStats> {
    try {
      const response = await api.get(`${this.baseURL}/stats`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch user stats:', error)
      throw error
    }
  }

  // 獲取用戶操作記錄
  async getUserOperations(limit: number = 50): Promise<UserOperation[]> {
    try {
      const response = await api.get(`${this.baseURL}/operations`, {
        params: { limit }
      })
      return response.data
    } catch (error) {
      console.error('Failed to fetch user operations:', error)
      throw error
    }
  }

  // 獲取所有角色
  async getRoles(): Promise<UserRole[]> {
    try {
      const response = await api.get('/users/roles')
      return response.data
    } catch (error) {
      console.error('Failed to fetch roles:', error)
      throw error
    }
  }

  // 獲取所有模組
  async getModules(): Promise<Module[]> {
    try {
      const response = await api.get('/users/modules')
      return response.data
    } catch (error) {
      console.error('Failed to fetch modules:', error)
      throw error
    }
  }

  // 獲取用戶權限
  async getUserPermissions(id: string): Promise<Permission[]> {
    try {
      const response = await api.get(`${this.baseURL}/${id}/permissions`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch user permissions:', error)
      throw error
    }
  }

  // 更新用戶權限
  async updateUserPermissions(id: string, permissions: Permission[]): Promise<void> {
    try {
      await api.put(`${this.baseURL}/${id}/permissions`, { permissions })
    } catch (error) {
      console.error('Failed to update user permissions:', error)
      throw error
    }
  }

  // 驗證用戶名唯一性
  async validateUsername(username: string, excludeId?: string): Promise<{
    isValid: boolean
    isDuplicate: boolean
    errors: string[]
  }> {
    try {
      const response = await api.post(`${this.baseURL}/validate-username`, {
        username,
        excludeId
      })
      return response.data
    } catch (error) {
      console.error('Failed to validate username:', error)
      throw error
    }
  }

  // 驗證郵箱唯一性
  async validateEmail(email: string, excludeId?: string): Promise<{
    isValid: boolean
    isDuplicate: boolean
    errors: string[]
  }> {
    try {
      const response = await api.post(`${this.baseURL}/validate-email`, {
        email,
        excludeId
      })
      return response.data
    } catch (error) {
      console.error('Failed to validate email:', error)
      throw error
    }
  }

  // 批量操作
  async bulkOperation(operation: {
    type: 'activate' | 'deactivate' | 'delete'
    userIds: string[]
  }): Promise<{
    successCount: number
    failCount: number
    errors: string[]
  }> {
    try {
      const response = await api.post(`${this.baseURL}/bulk`, operation)
      return response.data
    } catch (error) {
      console.error('Failed to perform bulk operation:', error)
      throw error
    }
  }

  // 匯出用戶數據
  async exportUsers(options: {
    includeInactive?: boolean
    includePermissions?: boolean
    format: 'csv' | 'xlsx' | 'json'
  }): Promise<Blob> {
    try {
      const response = await api.post(`${this.baseURL}/export`, options, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to export users:', error)
      throw error
    }
  }

  // 檢查用戶權限
  async checkPermission(userId: string, module: string, resource: string, action: string): Promise<boolean> {
    try {
      const response = await api.get(`${this.baseURL}/${userId}/check-permission`, {
        params: { module, resource, action }
      })
      return response.data.allowed
    } catch (error) {
      console.error('Failed to check permission:', error)
      return false
    }
  }
}

export const userService = new UserService()