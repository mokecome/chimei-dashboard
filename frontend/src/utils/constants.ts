// 用户角色枚举
export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  OPERATOR = 'operator',
  VIEWER = 'viewer'
}

// 权限枚举
export enum Permission {
  // Dashboard
  DASHBOARD_VIEW = 'dashboard:view',
  
  // Analysis
  ANALYSIS_VIEW = 'analysis:view',
  ANALYSIS_EXPORT = 'analysis:export',
  
  // DataSource
  DATASOURCE_VIEW = 'datasource:view',
  DATASOURCE_CREATE = 'datasource:create',
  DATASOURCE_UPDATE = 'datasource:update',
  DATASOURCE_DELETE = 'datasource:delete',
  
  // Labels
  LABELS_VIEW = 'labels:view',
  LABELS_MANAGE = 'labels:manage',
  
  // Account
  ACCOUNT_MANAGE = 'account:manage',
  
  // System
  SYSTEM_SETTINGS = 'system:settings',
  OPERATION_LOGS = 'operation:logs'
}

// 角色权限映射
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  [UserRole.ADMIN]: Object.values(Permission),
  [UserRole.MANAGER]: [
    Permission.DASHBOARD_VIEW,
    Permission.ANALYSIS_VIEW,
    Permission.ANALYSIS_EXPORT,
    Permission.DATASOURCE_VIEW,
    Permission.DATASOURCE_CREATE,
    Permission.DATASOURCE_UPDATE,
    Permission.DATASOURCE_DELETE,
    Permission.LABELS_VIEW,
    Permission.LABELS_MANAGE
  ],
  [UserRole.OPERATOR]: [
    Permission.DASHBOARD_VIEW,
    Permission.ANALYSIS_VIEW,
    Permission.DATASOURCE_VIEW,
    Permission.DATASOURCE_CREATE,
    Permission.DATASOURCE_UPDATE
  ],
  [UserRole.VIEWER]: [
    Permission.DASHBOARD_VIEW,
    Permission.ANALYSIS_VIEW
  ]
}

// 文件类型
export const FILE_TYPES = {
  AUDIO: ['wav', 'mp3'],
  TEXT: ['txt']
}

// 情绪类型
export enum SentimentType {
  POSITIVE = 'positive',
  NEGATIVE = 'negative',
  NEUTRAL = 'neutral'
}

// API 基础配置
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
export const AUTH_TOKEN_KEY = 'auth_token'
export const USER_INFO_KEY = 'user_info'