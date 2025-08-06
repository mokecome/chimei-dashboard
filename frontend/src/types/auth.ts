import { UserRole } from '@/utils/constants'

export interface User {
  id: string  // 改為字符串類型以匹配後端UUID
  username?: string  // 後端沒有username字段，改為可選
  name: string
  email: string
  role: UserRole
  permissions?: string[]  // 後端沒有直接返回permissions，改為可選
  department?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
}

export interface LoginResponse {
  message: string
  data: {
    token: string
    refreshToken: string
    token_type: string
    expires_in: number
    user: User
  }
}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
}