// 儀表板指標數據
export interface DashboardMetrics {
  totalFiles: number
  totalAnalyses: number
  positiveRatio: number
  negativeRatio: number
  neutralRatio: number
  todayUploads: number
  weeklyGrowth: number
}

// 圖表數據配置
export interface ChartConfig {
  responsive: boolean
  maintainAspectRatio: boolean
  plugins?: any
  scales?: any
  interaction?: any
  onClick?: (event: any, elements: any[]) => void
}

// 圖表數據項
export interface ChartData {
  id: string
  title: string
  type: 'bar' | 'line' | 'pie' | 'doughnut'
  data: any
  options: ChartConfig
  clickable?: boolean
}

// 熱門商品數據
export interface HotProduct {
  name: string
  count: number
  trend: number // 趨勢百分比
  color?: string
}

// 反饋類別數據
export interface FeedbackCategory {
  name: string
  count: number
  percentage: number
  color?: string
}

// 時間趨勢數據點
export interface TrendDataPoint {
  date: string
  value: number
  label?: string
}

// 時間趨勢數據集
export interface TrendDataset {
  label: string
  data: TrendDataPoint[]
  color: string
  backgroundColor?: string
}

// AI 洞察建議
export interface AIInsight {
  id: string
  type: 'success' | 'warning' | 'info' | 'danger'
  title: string
  content: string
  action?: string
  priority: number
}

// 儀表板過濾條件
export interface DashboardFilter {
  dateRange?: [string, string]
  productLabels?: string[]
  feedbackLabels?: string[]
  sentiment?: string
  uploader?: string
}