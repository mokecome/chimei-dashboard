// 数据来源相关类型定义

export interface AnalysisResult {
  sentiment?: 'positive' | 'negative' | 'neutral'
  feedback_category?: string
  feedback_summary?: string
  product_names?: string[]
  transcript?: string
}

export interface DataSourceItem {
  id: string
  fileName?: string
  filename?: string
  original_filename?: string
  fileType?: 'wav' | 'mp3' | 'txt'
  file_format?: string
  fileSize?: number
  file_size?: number
  uploadTime?: string
  created_at?: string
  updated_at?: string
  uploader?: string
  uploaded_by?: string
  uploaderName?: string
  uploader_name?: string
  status: 'pending' | 'analyzing' | 'completed' | 'failed'
  analysis_result?: AnalysisResult
  analysisResult?: {
    productLabels: string[]
    feedbackLabels: string[]
    sentiment: 'positive' | 'negative' | 'neutral'
    summary: string
    confidence: number
    originalContent?: string
  }
  progress?: number
  errorMessage?: string
}

export interface DataSourceFilter {
  fileName?: string
  fileType?: string
  status?: string
  uploader?: string
  dateRange?: string[]
  keyword?: string
}

export interface SortConfig {
  field: string
  order: 'asc' | 'desc'
}

export interface Pagination {
  page: number
  size: number
  total: number
  pages: number
}

export interface DataSourceListResponse {
  items: DataSourceItem[]
  pagination: Pagination
}

export interface UploadOptions {
  autoAnalyze: boolean
  notifyOnComplete: boolean
}

export interface UploadRequest {
  file: File
  options: UploadOptions
}

export interface BatchOperation {
  type: 'delete' | 'analyze'
  ids: string[]
}

export interface FileAnalysisResult {
  id: string
  fileName: string
  analysisStatus: 'pending' | 'processing' | 'completed' | 'failed'
  result?: {
    transcription?: string
    productLabels: string[]
    feedbackLabels: string[]
    sentiment: 'positive' | 'negative' | 'neutral'
    summary: string
    confidence: number
  }
  createdAt: string
  updatedAt: string
}