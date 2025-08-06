// 标签相关类型定义

export interface ProductLabel {
  id: string
  name: string
  description?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
  createdBy: string
  usage?: number // 使用次数
}

export interface FeedbackLabel {
  id: string
  name: string
  category: string
  description?: string
  isActive: boolean
  isDefault: boolean // 是否为系统预设标签
  createdAt: string
  updatedAt: string
  createdBy: string
  usage?: number // 使用次数
}

export interface LabelCategory {
  id: string
  name: string
  type: 'product' | 'feedback'
  isDefault: boolean
  labels: string[]
}

export interface LabelOperation {
  id: string
  type: 'create' | 'update' | 'delete'
  targetType: 'product' | 'feedback'
  targetId: string
  targetName: string
  oldValue?: string
  newValue?: string
  operatorId: string
  operatorName: string
  timestamp: string
  description?: string
}

export interface LabelSettings {
  productLabels: ProductLabel[]
  feedbackLabels: FeedbackLabel[]
  defaultFeedbackCategories: string[]
  limits: {
    maxProductLabels: number
    maxFeedbackLabels: number
    maxProductLabelLength: number
    maxFeedbackLabelLength: number
  }
}

export interface LabelForm {
  name: string
  category?: string
  description?: string
}

export interface LabelValidation {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

export interface LabelStats {
  totalProductLabels: number
  totalFeedbackLabels: number
  activeProductLabels: number
  activeFeedbackLabels: number
  recentOperations: LabelOperation[]
  topUsedLabels: {
    products: Array<{ name: string, usage: number }>
    feedbacks: Array<{ name: string, usage: number }>
  }
}

export interface BulkLabelOperation {
  type: 'create' | 'delete' | 'activate' | 'deactivate'
  targetType: 'product' | 'feedback'
  items: string[] // 标签名称或ID数组
}

export interface ImportLabelData {
  type: 'product' | 'feedback'
  labels: Array<{
    name: string
    category?: string
    description?: string
  }>
}

export interface ExportLabelOptions {
  includeProduct: boolean
  includeFeedback: boolean
  includeUsage: boolean
  includeOperationHistory: boolean
  format: 'json' | 'csv' | 'xlsx'
}