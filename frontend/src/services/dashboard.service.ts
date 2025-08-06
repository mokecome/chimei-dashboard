import api from './api'
import type { 
  DashboardMetrics, 
  ChartData, 
  DashboardFilter, 
  AIInsight 
} from '@/types/dashboard'

export const dashboardService = {
  // 获取仪表板指标数据
  async getMetrics(filters?: DashboardFilter): Promise<any> {
    const response = await api.get<any>('/data/dashboard', {
      params: filters
    })
    return response.data
  },

  // 获取图表数据
  async getChartData(filters?: DashboardFilter): Promise<ChartData[]> {
    const response = await api.get<ChartData[]>('/data/dashboard', {
      params: filters
    })
    return response.data
  },

  // 获取 AI 洞察建议
  async getAIInsights(filters?: DashboardFilter): Promise<AIInsight[]> {
    const response = await api.get<AIInsight[]>('/analysis/insights', {
      params: filters
    })
    return response.data
  },

  // 获取热门商品数据
  async getHotProducts(limit = 10): Promise<any[]> {
    const response = await api.get('/data/dashboard', {
      params: { limit }
    })
    return response.data
  },

  // 获取反馈类别数据
  async getFeedbackCategories(): Promise<any[]> {
    const response = await api.get('/data/dashboard')
    return response.data
  },

  // 获取趋势数据
  async getTrendData(type: string, timeRange?: string): Promise<any[]> {
    const response = await api.get('/data/dashboard', {
      params: { type, timeRange }
    })
    return response.data
  },

  // 导出仪表板报表
  async exportReport(filters?: DashboardFilter): Promise<Blob> {
    const response = await api.post('/data/export', filters, {
      responseType: 'blob'
    })
    return response.data
  }
}