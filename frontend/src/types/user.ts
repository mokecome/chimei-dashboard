// 用戶相關類型定義

export interface User {
  id: string
  username: string
  email: string
  name?: string
  department?: string
  role: UserRole
  status: UserStatus
  permissions: Permission[]
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
  isSystemUser: boolean // 是否為系統內建用戶（如 admin）
}

export interface UserRole {
  id: string
  name: string
  displayName: string
  description?: string
  level: number // 權限等級，數字越高權限越大
  isSystemRole: boolean
}

export interface Permission {
  id: string
  module: string // 模組名稱
  resource: string // 資源名稱
  actions: PermissionAction[] // 允許的操作
}

export interface PermissionAction {
  action: 'create' | 'read' | 'update' | 'delete'
  allowed: boolean
}

export interface Module {
  id: string
  name: string
  displayName: string
  description?: string
  resources: Resource[]
}

export interface Resource {
  id: string
  name: string
  displayName: string
  description?: string
  actions: string[] // 支援的操作類型
}

export type UserStatus = 'active' | 'inactive' | 'pending' | 'suspended'

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  name?: string
  department?: string
  roleId: string
  permissions?: Permission[]
  copyFromUserId?: string // 複製權限來源用戶ID
}

export interface UpdateUserRequest {
  name?: string
  department?: string
  roleId?: string
  status?: UserStatus
  permissions?: Permission[]
}

export interface UserListQuery {
  page?: number
  limit?: number
  search?: string
  role?: string
  status?: UserStatus
  sortBy?: 'username' | 'email' | 'name' | 'createdAt' | 'lastLoginAt'
  sortOrder?: 'asc' | 'desc'
}

export interface UserStats {
  totalUsers: number
  activeUsers: number
  inactiveUsers: number
  adminUsers: number
  recentLogins: number
  newUsersThisMonth: number
}

export interface PasswordChangeRequest {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export interface UserOperation {
  id: string
  type: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'permission_change'
  targetUserId: string
  targetUsername: string
  operatorId: string
  operatorName: string
  timestamp: string
  description?: string
  details?: Record<string, any>
}

// 系統預設角色
export const SystemRoles = {
  ADMIN: 'admin',
  MANAGER: 'manager', 
  OPERATOR: 'operator',
  VIEWER: 'viewer'
} as const

// 系統模組
export const SystemModules = {
  DASHBOARD: 'dashboard',
  ANALYSIS: 'analysis',
  DATASOURCE: 'datasource',
  LABEL_SETTING: 'label_setting',
  ACCOUNT: 'account'
} as const

// 操作權限
export const Actions = {
  CREATE: 'create',
  READ: 'read',
  UPDATE: 'update',
  DELETE: 'delete'
} as const

export type SystemRole = typeof SystemRoles[keyof typeof SystemRoles]
export type SystemModule = typeof SystemModules[keyof typeof SystemModules]
export type Action = typeof Actions[keyof typeof Actions]