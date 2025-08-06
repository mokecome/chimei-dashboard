import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth.service'
import type { User, LoginRequest } from '@/types/auth'
import { AUTH_TOKEN_KEY, USER_INFO_KEY, ROLE_PERMISSIONS } from '@/utils/constants'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem(AUTH_TOKEN_KEY))
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userPermissions = computed(() => {
    if (!user.value) return []
    return ROLE_PERMISSIONS[user.value.role] || []
  })

  // 初始化用户信息
  const initializeAuth = async () => {
    const storedToken = localStorage.getItem(AUTH_TOKEN_KEY)
    const storedUser = localStorage.getItem(USER_INFO_KEY)

    if (storedToken && storedUser) {
      token.value = storedToken
      try {
        user.value = JSON.parse(storedUser)
        // 验证 token 是否有效
        await authService.getCurrentUser()
      } catch (error) {
        // token 无效，清除本地存储
        await logout()
      }
    }
  }

  // 登录
  const login = async (credentials: LoginRequest) => {
    loading.value = true
    try {
      const response = await authService.login(credentials)
      
      // 適配新的響應格式: response.data.token 而不是 response.access_token
      token.value = response.data.token
      user.value = response.data.user
      
      // 存储到本地
      localStorage.setItem(AUTH_TOKEN_KEY, response.data.token)
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(response.data.user))
      
      // 记住用户名
      if (credentials.rememberMe) {
        localStorage.setItem('remembered_username', credentials.username)
      } else {
        localStorage.removeItem('remembered_username')
      }
      
      ElMessage.success('登入成功')
      return response
    } catch (error: any) {
      const message = error.response?.data?.message || '登入失敗'
      ElMessage.error(message)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authService.logout()
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 清除状态和本地存储
      user.value = null
      token.value = null
      localStorage.removeItem(AUTH_TOKEN_KEY)
      localStorage.removeItem(USER_INFO_KEY)
      
      ElMessage.success('已安全登出')
    }
  }

  // 检查权限
  const hasPermission = (permission: string): boolean => {
    return userPermissions.value.includes(permission)
  }

  // 检查角色
  const hasRole = (role: string): boolean => {
    return user.value?.role === role
  }

  // 更新用户信息
  const updateUser = (newUser: User) => {
    user.value = newUser
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(newUser))
  }

  return {
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    isAuthenticated,
    userPermissions,
    initializeAuth,
    login,
    logout,
    hasPermission,
    hasRole,
    updateUser
  }
})