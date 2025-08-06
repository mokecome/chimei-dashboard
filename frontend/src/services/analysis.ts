/**
 * Analysis Service - 分析服務
 * 用於獲取和管理分析數據
 */
import type { AxiosRequestConfig } from 'axios'
import api from '@/services/api'

// 情緒類型
export enum SentimentType {
  Positive = 'POSITIVE',
  Neutral = 'NEUTRAL',
  Negative = 'NEGATIVE'
}

// 分析響應接口
export interface AnalysisResponse {
  id: string
  file_id: string
  filename?: string
  transcript: string
  sentiment: SentimentType
  feedback_category: string
  feedback_summary: string
  product_names?: string[]
  analysis_time: string
  created_at: string
  upload_time?: string
  uploader_name?: string
}

// 分析過濾參數
export interface AnalysisFilterParams {
  product_names?: string[]
  feedback_categories?: string[]
  sentiments?: SentimentType[]
  uploaders?: string[]
  start_date?: string
  end_date?: string
}

// 分頁參數
export interface PaginationParams {
  page: number
  page_size: number
}

// 分頁響應
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 儀表板數據
export interface DashboardData {
  total_files: number
  total_analyses: number
  sentiment_chart: ChartData
  product_chart: ChartData
  category_chart: ChartData
  trend_chart: ChartData
  feedback_trend_chart: ChartData
}

// 圖表數據
export interface ChartData {
  type: 'pie' | 'bar' | 'line'
  title: string
  data: Array<{
    name: string
    value: number
    date?: string
  }>
}

// 時間維度圖表數據
export interface TimeSeriesData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
  }>
}

// 維度統計數據
export interface DimensionStats {
  dimension1: {
    [key: string]: {
      positive: number
      negative: number
      neutral: number
      total: number
    }
  }
  dimension2: {
    [key: string]: {
      count: number
      percentage: number
    }
  }
}

class AnalysisService {
  /**
   * 獲取分析列表
   */
  async getAnalysisList(
    params: AnalysisFilterParams & PaginationParams
  ): Promise<PaginatedResponse<AnalysisResponse>> {
    const response = await api.get('/data/analysis', { 
      params,
      paramsSerializer: {
        indexes: null // This makes arrays serialize as param=val1&param=val2 instead of param[]=val1&param[]=val2
      }
    })
    return response.data
  }

  /**
   * 獲取儀表板數據
   */
  async getDashboardData(): Promise<DashboardData> {
    const response = await api.get('/data/dashboard')
    return response.data
  }

  /**
   * 獲取分析統計數據
   */
  async getAnalysisStatistics(): Promise<any> {
    const response = await api.get('/analysis/statistics/summary')
    return response.data
  }

  /**
   * 高級搜索
   */
  async advancedSearch(
    filter: AnalysisFilterParams,
    pagination: PaginationParams
  ): Promise<PaginatedResponse<AnalysisResponse>> {
    const response = await api.post('/data/search', {
      ...filter,
      ...pagination
    })
    return response.data
  }

  /**
   * 導出數據
   */
  async exportData(
    format: 'excel' | 'csv',
    filters?: AnalysisFilterParams
  ): Promise<Blob> {
    const response = await api.get('/data/export', {
      params: {
        format,
        ...filters
      },
      responseType: 'blob'
    })
    return response.data
  }

  /**
   * 獲取維度統計數據
   * @param dimension1Items 維度一項目（如產品）
   * @param dimension2Items 維度二項目（如情緒）
   * @param timePeriod 時間範圍
   */
  async getDimensionStats(
    dimension1Items: string[],
    dimension2Items: string[],
    timePeriod: 'week' | 'month' | 'year'
  ): Promise<DimensionStats> {
    // 計算時間範圍
    const endDate = new Date()
    const startDate = new Date()
    
    switch (timePeriod) {
      case 'week':
        startDate.setDate(startDate.getDate() - 7)
        break
      case 'month':
        startDate.setMonth(startDate.getMonth() - 1)
        break
      case 'year':
        startDate.setFullYear(startDate.getFullYear() - 1)
        break
    }

    // 獲取分析數據
    const params: AnalysisFilterParams = {
      product_names: dimension1Items,
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString()
    }

    const response = await this.getAnalysisList({
      ...params,
      page: 1,
      page_size: 1000 // 獲取足夠多的數據進行統計
    })

    // 處理統計數據
    const stats: DimensionStats = {
      dimension1: {},
      dimension2: {}
    }

    // 初始化維度一統計
    dimension1Items.forEach(item => {
      stats.dimension1[item] = {
        positive: 0,
        negative: 0,
        neutral: 0,
        total: 0
      }
    })

    // 統計數據
    response.items.forEach(analysis => {
      // 統計維度一（產品）
      analysis.product_names?.forEach(product => {
        if (dimension1Items.includes(product)) {
          stats.dimension1[product].total++
          switch (analysis.sentiment) {
            case SentimentType.Positive:
              stats.dimension1[product].positive++
              break
            case SentimentType.Negative:
              stats.dimension1[product].negative++
              break
            case SentimentType.Neutral:
              stats.dimension1[product].neutral++
              break
          }
        }
      })

      // 統計維度二（回饋分類）
      if (analysis.feedback_category) {
        if (!stats.dimension2[analysis.feedback_category]) {
          stats.dimension2[analysis.feedback_category] = { count: 0, percentage: 0 }
        }
        stats.dimension2[analysis.feedback_category].count++
      }
    })

    // 計算百分比
    const totalCount = response.items.length
    Object.keys(stats.dimension2).forEach(category => {
      stats.dimension2[category].percentage = 
        totalCount > 0 ? (stats.dimension2[category].count / totalCount) * 100 : 0
    })

    return stats
  }

  /**
   * 獲取時間序列數據
   * @param dimension1Items 維度一項目（產品）
   * @param dimension2Items 維度二項目（情緒）
   * @param timePeriod 時間範圍
   */
  async getTimeSeriesData(
    dimension1Items: string[] | undefined,
    dimension2Items: string[],
    timePeriod: 'week' | 'month' | 'year'
  ): Promise<TimeSeriesData> {
    console.log('analysisService.getTimeSeriesData called with:', {
      dimension1Items,
      dimension2Items,
      timePeriod
    })
    
    // 將中文情緒轉換為英文
    const sentiments = dimension2Items.map(sentiment => {
      switch(sentiment) {
        case '正面': return 'POSITIVE'
        case '負面': return 'NEGATIVE'
        case '中性': return 'NEUTRAL'
        default: return 'NEUTRAL'
      }
    })

    // 處理產品名稱：如果包含"未分類"，保留它，後端會正確處理
    // 當只有"未分類"時，發送空數組或undefined讓後端返回未分類數據
    let productParams: string[] | undefined = undefined
    
    // 檢查 dimension1Items 是否為 undefined（從 AnalysisView 傳來）
    if (!dimension1Items) {
      console.log('dimension1Items is undefined, setting productParams to undefined')
      productParams = undefined
    } else if (dimension1Items.includes('未分類') && dimension1Items.length === 1) {
      // 只選擇了"未分類"，發送undefined讓後端返回未分類數據
      console.log('Only 未分類 selected, setting productParams to undefined')
      productParams = undefined
    } else if (dimension1Items.includes('未分類') && dimension1Items.length > 1) {
      // 選擇了"未分類"加其他產品，發送完整列表
      console.log('未分類 plus other products selected, using full list')
      productParams = dimension1Items
    } else {
      // 只選擇了具體產品，過濾掉"未分類"
      console.log('Only specific products selected, filtering out 未分類')
      productParams = dimension1Items.filter(item => item !== '未分類')
    }

    console.log('Final API call params:', {
      product_names: productParams,
      sentiments: sentiments,
      time_period: timePeriod
    })
    
    const response = await api.get('/data/time-series', {
      params: {
        product_names: productParams,
        sentiments: sentiments,
        time_period: timePeriod
      },
      paramsSerializer: {
        indexes: null // This makes arrays serialize as param=val1&param=val2 instead of param[]=val1&param[]=val2
      }
    })
    
    return response.data
  }
}

export const analysisService = new AnalysisService()