import api from './api'
import type { LoginRequest, LoginResponse, RefreshTokenResponse, User } from '@/types/auth'

export const authService = {
  // 用户登录
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await api.post('/auth/login', credentials)
    // 後端返回格式: { message, data: { token, refreshToken, user, ... } }
    return response.data
  },

  // 用户登出
  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  // 刷新 Token
  async refreshToken(): Promise<RefreshTokenResponse> {
    const response = await api.post<RefreshTokenResponse>('/auth/refresh')
    return response.data
  },

  // 获取当前用户信息
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  // 修改密码
  async changePassword(data: {
    current_password: string
    new_password: string
    confirm_password: string
  }): Promise<void> {
    await api.post('/auth/change-password', data)
  }
}