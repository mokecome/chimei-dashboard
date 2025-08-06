// 分析項目數據結構
export interface AnalysisItem {
  id: string
  fileName: string
  fileType: 'wav' | 'mp3' | 'txt'
  productLabels: string[]
  feedbackLabels: string[]
  sentiment: 'positive' | 'negative' | 'neutral'
  summary: string
  uploader: string
  uploaderName: string
  uploadTime: string
  confidence: number
  originalContent?: string
  analysisResult?: any
}

// 分析篩選條件
export interface AnalysisFilter {
  productLabels?: string[]      // 商品分類標籤 (最多4個)
  feedbackLabels?: string[]     // 反饋分類標籤 (可複選)
  sentiment?: string            // 評價傾向 (正面、中立、負面)
  uploader?: string            // 上傳者
  dateRange?: [string, string] // 上傳時間範圍
  keyword?: string             // 關鍵字搜索
}

// 分頁參數
export interface Pagination {
  page: number
  size: number
  total: number
  pages: number
}

// 分析列表響應
export interface AnalysisListResponse {
  items: AnalysisItem[]
  pagination: Pagination
}

// 維度分析數據
export interface DimensionAnalysis {
  dimension: string
  items: DimensionItem[]
}

export interface DimensionItem {
  name: string
  value: number
  percentage: number
  color?: string
}

// 圖表維度配置
export interface ChartDimension {
  id: string
  name: string
  type: 'product' | 'feedback' | 'sentiment' | 'time'
  items: string[]
  colors?: string[]
}

// 圖表類型
export type ChartType = 'line' | 'bar' | 'pie' | 'doughnut'

// 圖表配置
export interface AnalysisChartConfig {
  type: ChartType
  dimensions: ChartDimension[]
  timeRange?: string
  data?: any
  options?: any
}

// 導出配置
export interface ExportConfig {
  format: 'xlsx' | 'csv'
  includeColumns: string[]
  fileName?: string
  filters?: AnalysisFilter
}

// 排序配置
export interface SortConfig {
  field: string
  order: 'asc' | 'desc'
}

// 列顯示配置
export interface ColumnConfig {
  field: string
  label: string
  visible: boolean
  width?: number
  sortable?: boolean
}

// 統計數據
export interface AnalysisStats {
  totalCount: number
  sentimentDistribution: {
    positive: number
    negative: number
    neutral: number
  }
  topProducts: Array<{
    name: string
    count: number
  }>
  topFeedbacks: Array<{
    name: string
    count: number
  }>
  uploaderStats: Array<{
    name: string
    count: number
  }>
}